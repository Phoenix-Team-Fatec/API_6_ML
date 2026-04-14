from __future__ import annotations
import calendar
from datetime import date
from typing import Literal, Optional, Union
from pydantic import BaseModel, Field, model_validator


class OverridesMensais(BaseModel):
    """Regra sazonal de percentual de comissão por marca/cargo."""

    descricao: str = Field(
        description="Descrição legível da regra, ex: '% marca 10 cargo 300 → 1.75 (abril/2025)'"
    )
    data_inicio: date = Field(
        description="Primeiro dia de vigência da regra"
    )
    data_fim: date = Field(
        description="Último dia de vigência da regra (inclusive)"
    )
    perc_override: dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Percentual fixo por (cod_marca, cod_cargo). "
            "Chave no formato 'cod_marca,cod_cargo', ex: '10,300'. "
            "Valor é o percentual absoluto, ex: 1.75"
        ),
    )
    marca_override: dict[str, int] = Field(
        default_factory=dict,
        description=(
            "Redireciona o % de uma marca para outra. "
            "Chave = cod_marca de origem (str), valor = cod_marca de referência (int). "
            "Ex: {'10': 20} → marca 10 usa o % da marca 20"
        ),
    )
    perc_adicional: dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Acréscimo de % sobre o percentual base. "
            "Chave no formato 'cod_marca,cod_cargo'. "
            "Valor é somado ao percentual existente."
        ),
    )

    @model_validator(mode="after")
    def validar_periodo(self) -> OverridesMensais:
        if self.data_fim < self.data_inicio:
            raise ValueError(
                f"data_fim ({self.data_fim}) não pode ser anterior a data_inicio ({self.data_inicio})"
            )
        return self

    @model_validator(mode="after")
    def validar_preenchimento(self) -> OverridesMensais:
        if not any([self.perc_override, self.marca_override, self.perc_adicional]):
            raise ValueError(
                "Ao menos um campo de override deve ser preenchido "
                "(perc_override, marca_override ou perc_adicional)"
            )
        return self
    
    
    @model_validator(mode="after")
    def validar_marca_override(self) -> OverridesMensais:
        # Coerce valores string para int silenciosamente
        self.marca_override = {
            k: int(v) for k, v in self.marca_override.items()
        }
        return self

    def esta_vigente(self, ano: int, mes: int) -> bool:
        data_competencia = date(ano, mes, 1)
        return self.data_inicio <= data_competencia <= self.data_fim

    def to_dict(self) -> dict:
        """Converte para o formato esperado por calcular_comissionamento()."""
        def parse_key(k: str) -> tuple[int, int]:
            marca, cargo = k.split(",")
            return int(marca.strip()), int(cargo.strip())

        return {
            "perc_override": {
                parse_key(k): v for k, v in self.perc_override.items()
            },
            "marca_override": {
                int(k): v for k, v in self.marca_override.items()
            },
            "perc_adicional": {
                parse_key(k): v for k, v in self.perc_adicional.items()
            },
        }


class IntercorrenciaSazonal(BaseModel):
    """Bônus ou ajuste sazonal vinculado a matrículas individuais."""

    matricula: str = Field(description="Matrícula do funcionário")
    tipo: Literal["bonus_fixo", "bonus_venda", "admissao_bonus"] = Field(
        description="Tipo da intercorrência conforme calcular_comissionamento()"
    )
    valor: float = Field(description="Valor em reais ou percentual conforme o tipo")
    vigencia_inicio: date = Field(description="Início da vigência")
    vigencia_fim: date = Field(description="Fim da vigência (inclusive)")

    @model_validator(mode="after")
    def validar_periodo(self) -> IntercorrenciaSazonal:
        if self.vigencia_fim < self.vigencia_inicio:
            raise ValueError(
                f"vigencia_fim ({self.vigencia_fim}) não pode ser anterior "
                f"a vigencia_inicio ({self.vigencia_inicio})"
            )
        return self

    def esta_vigente(self, ano: int, mes: int) -> bool:
        primeiro_dia_mes = date(ano, mes, 1)
        ultimo_dia_mes = date(ano, mes, calendar.monthrange(ano, mes)[1])
        return self.vigencia_inicio <= ultimo_dia_mes and self.vigencia_fim >= primeiro_dia_mes

class RespostaAgente(BaseModel):
    """
    Contrato de saída do code_editor.
    Exatamente um dos campos deve ser preenchido por resposta.
    """

    tipo: Literal["override", "intercorrencia"] = Field(
        description=(
            "'override' para regras de percentual por marca/cargo. "
            "'intercorrencia' para bônus ou ajustes por matrícula individual."
        )
    )
    override: Optional[OverridesMensais] = Field(
        default=None,
        description="Preenchido quando tipo='override'"
    )
    intercorrencias: Optional[list[IntercorrenciaSazonal]] = Field(
        default=None,
        description="Preenchido quando tipo='intercorrencia'"
    )
    justificativa: str = Field(
        description=(
            "Explicação de qual regra de negócio foi aplicada e "
            "por que este tipo de objeto foi escolhido."
        )
    )

    @model_validator(mode="after")
    def validar_consistencia(self) -> RespostaAgente:
        if self.tipo == "override" and self.override is None:
            raise ValueError("tipo='override' exige o campo 'override' preenchido")
        if self.tipo == "intercorrencia" and not self.intercorrencias:
            raise ValueError(
                "tipo='intercorrencia' exige ao menos um item em 'intercorrencias'"
            )
        return self