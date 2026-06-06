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

    @model_validator(mode="before")
    @classmethod
    def normalizar_mapas_vazios(cls, data):
        if isinstance(data, dict):
            for field in ("perc_override", "marca_override", "perc_adicional"):
                if data.get(field) is None:
                    data[field] = {}
        return data

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
    def validar_formato_chaves(self) -> OverridesMensais:
        for field_name, mapping in [
            ("perc_override", self.perc_override),
            ("perc_adicional", self.perc_adicional),
        ]:
            for key in mapping:
                parts = key.split(",")
                if len(parts) != 2:
                    raise ValueError(
                        f"{field_name}['{key}']: chave deve estar no formato "
                        f"'cod_marca,cod_cargo' (ex: '10,300'). "
                        f"Para regras por matrícula ou loja use tipo 'rate_override'."
                    )
                try:
                    int(parts[0].strip())
                    int(parts[1].strip())
                except ValueError:
                    raise ValueError(
                        f"{field_name}['{key}']: ambas as partes devem ser inteiros, "
                        f"ex: '10,300'."
                    )
        return self

    @model_validator(mode="after")
    def normalizar_percentuais_decimais(self) -> OverridesMensais:
        self.perc_override = {
            key: value * 100 if 0 < value < 0.1 else value
            for key, value in self.perc_override.items()
        }
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
    tipo: Literal["bonus_fixo", "bonus_venda", "admissao_bonus", "perc_bonus"] = Field(
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


class EscopoRegra(BaseModel):
    """Escopo explicito para uma regra de percentual de comissao."""

    matricula: Optional[str] = None
    cod_loja: Optional[int] = None
    cod_marca: Optional[int] = None
    cod_cargo: Optional[int] = None

    @model_validator(mode="after")
    def validar_preenchimento(self) -> EscopoRegra:
        has_matricula = self.matricula is not None and self.matricula.strip() != ""
        if not any([has_matricula, self.cod_loja is not None, self.cod_marca is not None, self.cod_cargo is not None]):
            raise ValueError("Ao menos um campo de escopo deve ser preenchido")
        return self


class EfeitoRegra(BaseModel):
    """Efeito percentual aplicado quando o escopo da regra corresponde."""

    tipo: Literal["percentual_absoluto", "percentual_adicional"]
    valor: float

    @model_validator(mode="after")
    def validar_valor(self) -> EfeitoRegra:
        if self.valor <= 0:
            raise ValueError("valor deve ser positivo")
        return self


class RegraComissaoEscopada(BaseModel):
    """Regra sazonal de percentual com escopo flexivel."""

    descricao: str
    vigencia_inicio: date
    vigencia_fim: date
    escopo: EscopoRegra
    efeito: EfeitoRegra

    @model_validator(mode="after")
    def validar_periodo(self) -> RegraComissaoEscopada:
        if self.vigencia_fim < self.vigencia_inicio:
            raise ValueError(
                f"vigencia_fim ({self.vigencia_fim}) nao pode ser anterior "
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

    tipo: Literal["override", "intercorrencia", "rate_override"] = Field(
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
    rate_overrides: Optional[list[RegraComissaoEscopada]] = Field(
        default=None,
        description="Preenchido quando tipo='rate_override'"
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
        if self.tipo == "rate_override" and not self.rate_overrides:
            raise ValueError(
                "tipo='rate_override' exige ao menos um item em 'rate_overrides'"
            )
        return self


# ---------------------------------------------------------------------------
# Auditoria e Rastreamento de Cálculos
# ---------------------------------------------------------------------------

from datetime import datetime


class EtapaCalculo(BaseModel):
    """Representa uma etapa do cálculo de comissão com rastreamento completo"""
    
    numero: int = Field(description="Número sequencial da etapa")
    secao: str = Field(
        description="Seção do cálculo: Consolidação, Percentual, Proporcional, Intercorrências, Comissão"
    )
    descricao: str = Field(description="Descrição legível da etapa")
    entrada: dict = Field(description="Valores que entraram nesta etapa")
    saida: dict = Field(description="Resultado desta etapa")
    logica_aplicada: str = Field(description="Resumo da lógica aplicada")
    condicao: Optional[str] = Field(
        default=None,
        description="Condição que ativou esta etapa, ex: 'admitido no mês', 'em férias'"
    )
    timestamp: datetime = Field(default_factory=datetime.now, description="Momento da execução")
    
    def model_dump(self, **kwargs) -> dict:
        """Serializa com timestamp em ISO format"""
        data = super().model_dump(**kwargs)
        data["timestamp"] = self.timestamp.isoformat()
        return data


class ResultadoComissionamentoDetalhado(BaseModel):
    """Resultado do cálculo de comissão com rastreamento de etapas"""
    
    # Dados base (compatível com ResultadoComissionamento)
    matricula: str = Field(description="Matrícula do funcionário")
    cod_loja: str = Field(description="Código da loja")
    cod_marca: int = Field(description="Código da marca")
    base_vendas: float = Field(description="Base de vendas utilizada")
    perc_comissao: float = Field(description="Percentual de comissão aplicado")
    valor_comissao_bruto: float = Field(description="Comissão antes de ajustes")
    ajuste_proporcional: float = Field(description="Fator de proporcionalidade (0-1)")
    bonus: float = Field(description="Bônus totais")
    valor_final: float = Field(description="Valor final de comissão")
    
    # NOVO: Rastreamento de etapas
    etapas: list[EtapaCalculo] = Field(
        default_factory=list,
        description="Lista de todas as etapas do cálculo"
    )
    
    def model_dump(self, **kwargs) -> dict:
        """Serializa resultado com etapas"""
        data = super().model_dump(**kwargs)
        return data
    
    def para_dict_com_auditoria(self) -> dict:
        """Retorna estrutura amigável para frontend com resultado e auditoria separados"""
        return {
            "matricula": self.matricula,
            "resultado_final": {
                "base_vendas": self.base_vendas,
                "perc_comissao": self.perc_comissao,
                "valor_comissao_bruto": self.valor_comissao_bruto,
                "ajuste_proporcional": self.ajuste_proporcional,
                "bonus": self.bonus,
                "valor_final": self.valor_final,
                "cod_loja": self.cod_loja,
                "cod_marca": self.cod_marca,
            },
            "auditoria": {
                "total_etapas": len(self.etapas),
                "etapas": [e.model_dump() for e in self.etapas]
            }
        }
