"""
base_algorithm.py
Algoritmo base de cálculo de comissionamento mensal.
Este arquivo é gerenciado pela IA — não edite manualmente.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from src.agent.models.outputs import IntercorrenciaSazonal, OverridesMensais

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

COD_CARGO_GERENTE = 150
VALOR_FIXO_AFASTAMENTO = 3_500.0

DEBUG_COMISSIONAMENTO = False


def print_debug(mensagem: str = "") -> None:
    if DEBUG_COMISSIONAMENTO:
        print(mensagem)


# ---------------------------------------------------------------------------
# Estruturas de dados
# ---------------------------------------------------------------------------


@dataclass
class Funcionario:
    matricula: str
    cod_marca: int
    descr_marca: str
    cod_loja: str
    descr_loja: str
    data_admissao: date
    data_demissao: Optional[date]
    cod_cargo: int
    descr_cargo: str


@dataclass
class Venda:
    matricula: str
    cod_marca: int
    cod_loja: str
    vlr_venda: float


@dataclass
class ComissionamentoBase:
    cod_marca: int
    cod_cargo: int
    perc_comissao: float  # ex: 0.05 para 5%


@dataclass
class Intercorrencia:
    """Representa qualquer evento especial que afeta o comissionamento."""

    matricula: str
    tipo: str  # 'afastamento', 'ferias', 'bonus_fixo', 'bonus_venda', 'admissao_bonus'
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    valor: float = 0.0


@dataclass
class ResultadoComissionamento:
    matricula: str
    cod_loja: str
    cod_marca: int
    base_vendas: float
    perc_comissao: float
    valor_comissao_bruto: float
    ajuste_proporcional: float  # fator entre 0 e 1
    bonus: float
    valor_final: float


# ---------------------------------------------------------------------------
# Helpers de data
# ---------------------------------------------------------------------------


def dias_no_mes(ano: int, mes: int) -> int:
    return calendar.monthrange(ano, mes)[1]


def dias_trabalhados_admissao(data_admissao: date, ano: int, mes: int) -> int:
    """Dias efetivamente trabalhados quando admitido no mês de competência."""
    total = dias_no_mes(ano, mes)
    return total - data_admissao.day + 1


def dias_trabalhados_demissao(data_demissao: date, ano: int, mes: int) -> int:
    """Dias efetivamente trabalhados quando demitido no mês de competência."""
    return data_demissao.day


def fator_proporcional(dias_efetivos: int, total_dias: int) -> float:
    return dias_efetivos / total_dias


# ---------------------------------------------------------------------------
# Regras de afastamento
# ---------------------------------------------------------------------------


def calcular_ajuste_afastamento(
    vlr_base: float,
    dias_afastamento: int,
    dias_trabalhados: int,
    total_dias: int,
) -> float:
    """
    Retorna o valor adicional de comissionamento referente ao período de
    afastamento (atestado médico), respeitando as regras:
      - < 15 dias: proporcional aos dias afastados OU R$3.500 (o maior)
      - >= 15 dias: proporcional a 15 dias OU R$3.500 (o maior)
    """
    if dias_afastamento < 15:
        # base de calculo = venda_mes / dias_trabalhados * dias_afastados
        if dias_trabalhados == 0:
            base_afastamento = 0.0
        else:
            base_afastamento = (vlr_base / dias_trabalhados) * dias_afastamento
    else:
        # limite de 15 dias independente de quantos dias afastou
        if dias_trabalhados == 0:
            base_afastamento = 0.0
        else:
            base_afastamento = (vlr_base / dias_trabalhados) * 15

    return max(base_afastamento, VALOR_FIXO_AFASTAMENTO)


# ---------------------------------------------------------------------------
# Regras de férias
# ---------------------------------------------------------------------------


def calcular_fator_ferias(
    data_inicio_ferias: date,
    data_fim_ferias: date,
    ano: int,
    mes: int,
) -> float:
    """
    Funcionários em férias não recebem comissionamento nos dias de gozo.
    Retorna o fator (0-1) dos dias que dão direito a comissão no mês.
    """
    total_dias = dias_no_mes(ano, mes)
    primeiro_dia = date(ano, mes, 1)
    ultimo_dia = date(ano, mes, total_dias)

    inicio_efetivo = max(data_inicio_ferias, primeiro_dia)
    fim_efetivo = min(data_fim_ferias, ultimo_dia)

    if fim_efetivo < inicio_efetivo:
        return 1.0  # férias fora do mês — sem impacto

    dias_ferias_no_mes = (fim_efetivo - inicio_efetivo).days + 1
    dias_com_direito = total_dias - dias_ferias_no_mes
    return fator_proporcional(dias_com_direito, total_dias)


# ---------------------------------------------------------------------------
# Licença maternidade
# ---------------------------------------------------------------------------


def calcular_fator_licenca_maternidade(
    data_inicio_licenca: date,
    ano: int,
    mes: int,
) -> float:
    """
    Licença maternidade: sem comissionamento a partir da data de início.
    """
    total_dias = dias_no_mes(ano, mes)
    primeiro_dia = date(ano, mes, 1)

    if data_inicio_licenca > date(ano, mes, total_dias):
        return 1.0  # licença começa depois do mês — sem impacto

    if data_inicio_licenca <= primeiro_dia:
        return 0.0  # mês inteiro em licença

    dias_trabalhados = (data_inicio_licenca - primeiro_dia).days
    return fator_proporcional(dias_trabalhados, total_dias)


# ---------------------------------------------------------------------------
# Engine principal
# ---------------------------------------------------------------------------


def calcular_comissionamento(
    funcionarios: list[Funcionario],
    vendas: list[Venda],
    tabela_comissao: list[ComissionamentoBase],
    intercorrencias: list[Intercorrencia],
    ano: int,
    mes: int,
    overrides: Optional[dict] = None,
) -> list[ResultadoComissionamento]:
    """
    Calcula o comissionamento de todos os funcionários para o mês/ano
    informado, aplicando todas as regras gerais e intercorrências.

    overrides: dict opcional para regras temporárias do mês (ex: % especial
               por marca/cargo, bônus de período, etc.)
    """
    if overrides is None:
        overrides = {}

    total_dias = dias_no_mes(ano, mes)
    data_competencia = date(ano, mes, 1)

    # --- Indexar tabela de comissão ---
    indice_comissao: dict[tuple[int, int], float] = {
        (c.cod_marca, c.cod_cargo): c.perc_comissao for c in tabela_comissao
    }

    # Aplicar overrides de % de comissão para o mês
    for (cod_marca, cod_cargo), perc in overrides.get("perc_override", {}).items():
        indice_comissao[(cod_marca, cod_cargo)] = perc

    # --- Consolidar vendas por matrícula e por loja ---
    vendas_por_matricula: dict[str, float] = {}
    vendas_por_loja: dict[str, float] = {}

    for v in vendas:
        vendas_por_matricula[v.matricula] = (
            vendas_por_matricula.get(v.matricula, 0.0) + v.vlr_venda
        )
        vendas_por_loja[v.cod_loja] = vendas_por_loja.get(v.cod_loja, 0.0) + v.vlr_venda

    print_debug("")
    print_debug("========== VENDAS CONSOLIDADAS ==========")
    print_debug(f"Vendas por matrícula: {vendas_por_matricula}")
    print_debug(f"Vendas por loja: {vendas_por_loja}")

    # --- Indexar intercorrências por matrícula ---
    intercorr_por_matricula: dict[str, list[Intercorrencia]] = {}
    for ic in intercorrencias:
        intercorr_por_matricula.setdefault(ic.matricula, []).append(ic)

    resultados: list[ResultadoComissionamento] = []

    for func in funcionarios:
        print_debug("")
        print_debug("==========================================")
        print_debug(f"INICIANDO CÁLCULO DA MATRÍCULA: {func.matricula}")
        print_debug(f"Funcionário: cargo={func.cod_cargo} - {func.descr_cargo}")
        print_debug(f"Loja: {func.cod_loja} - {func.descr_loja}")
        print_debug(f"Marca: {func.cod_marca} - {func.descr_marca}")
        print_debug(f"Admissão: {func.data_admissao}")
        print_debug(f"Demissão: {func.data_demissao}")
        # Verificar se funcionário estava ativo no mês
        admitido_no_mes = (
            func.data_admissao.year == ano and func.data_admissao.month == mes
        )
        demitido_no_mes = (
            func.data_demissao is not None
            and func.data_demissao.year == ano
            and func.data_demissao.month == mes
        )

        # Ignorar funcionários demitidos antes do mês de competência
        if func.data_demissao is not None and func.data_demissao < data_competencia:
            print_debug("Funcionário ignorado: demitido antes do mês de competência.")
            continue

        # Ignorar admitidos após o mês de competência
        if func.data_admissao > date(ano, mes, total_dias):
            print_debug("Funcionário ignorado: admitido após o mês de competência.")
            continue

        eh_gerente = func.cod_cargo == COD_CARGO_GERENTE

        # --- Base de vendas ---
        if eh_gerente:
            base_vendas = vendas_por_loja.get(func.cod_loja, 0.0)
            print_debug("Funcionário é gerente.")
            print_debug(
                f"Base de vendas usada: total da loja {func.cod_loja} = R$ {base_vendas:,.2f}"
            )
        else:
            base_vendas = vendas_por_matricula.get(func.matricula, 0.0)
            print_debug("Funcionário não é gerente.")
            print_debug(
                f"Base de vendas usada: vendas da matrícula {func.matricula} = R$ {base_vendas:,.2f}"
            )

        # Bônus sobre base de vendas (ex: bônus por tempo de casa adicionado à base)
        bonus_base_venda = sum(
            ic.valor
            for ic in intercorr_por_matricula.get(func.matricula, [])
            if ic.tipo == "bonus_venda"
        )

        if bonus_base_venda:
            print_debug(
                f"Bônus adicionado à base de vendas: R$ {bonus_base_venda:,.2f}"
            )

        print_debug(f"Base final para cálculo da comissão: R$ {base_vendas:,.2f}")

        base_vendas += bonus_base_venda

        # --- % de comissão ---
        # Override de marca: ex "aplicar % da marca 20 em todos cargos da marca 10"
        cod_marca_efetivo = overrides.get("marca_override", {}).get(
            func.cod_marca, func.cod_marca
        )
        perc = indice_comissao.get((cod_marca_efetivo, func.cod_cargo), 0.0)

        print_debug(f"Marca efetiva para busca de comissão: {cod_marca_efetivo}")
        print_debug(f"Percentual base encontrado: {perc * 100:.2f}%")

        # Acréscimo de % por regra do mês (ex: +0,5% para marca 30)
        perc += overrides.get("perc_adicional", {}).get(
            (func.cod_marca, func.cod_cargo), 0.0
        )
        print_debug(f"Percentual final após adicionais: {perc * 100:.2f}%")

        # --- Fator proporcional base ---
        fator = 1.0
        bonus = 0.0

        # Proporcional de admissão
        if admitido_no_mes:
            dias_ef = dias_trabalhados_admissao(func.data_admissao, ano, mes)
            fator_admissao = fator_proporcional(dias_ef, total_dias)
            fator = min(fator, fator_proporcional(dias_ef, total_dias))

            print_debug("Aplicando proporcional de admissão.")
            print_debug(f"Dias trabalhados desde admissão: {dias_ef} de {total_dias}")
            print_debug(f"Fator de admissão: {fator_admissao:.4f}")

        # Proporcional de demissão
        if demitido_no_mes:
            dias_ef = dias_trabalhados_demissao(func.data_demissao, ano, mes)
            fator_demissao = fator_proporcional(dias_ef, total_dias)
            fator = min(fator, fator_proporcional(dias_ef, total_dias))

            print_debug("Aplicando proporcional de demissão.")
            print_debug(f"Dias trabalhados até demissão: {dias_ef} de {total_dias}")
            print_debug(f"Fator de demissão: {fator_demissao:.4f}")

        # Intercorrências do mês
        for ic in intercorr_por_matricula.get(func.matricula, []):
            print_debug("")
            print_debug(f"Intercorrência encontrada: {ic.tipo}")
            print_debug(
                f"Início: {ic.data_inicio} | Fim: {ic.data_fim} | Valor: R$ {ic.valor:,.2f}"
            )

            if ic.tipo == "ferias" and ic.data_inicio and ic.data_fim:
                fator_f = calcular_fator_ferias(ic.data_inicio, ic.data_fim, ano, mes)
                fator = min(fator, fator_f)

                print_debug("Aplicando regra de férias.")
                print_debug(f"Fator de férias: {fator_f:.4f}")
                print_debug(f"Fator proporcional acumulado: {fator:.4f}")

            elif ic.tipo == "licenca_maternidade" and ic.data_inicio:
                fator_l = calcular_fator_licenca_maternidade(ic.data_inicio, ano, mes)
                fator = min(fator, fator_l)

                print_debug("Aplicando regra de licença maternidade.")
                print_debug(f"Fator de licença maternidade: {fator_l:.4f}")
                print_debug(f"Fator proporcional acumulado: {fator:.4f}")

            elif ic.tipo == "afastamento" and ic.data_inicio and ic.data_fim:
                # Calcular dias de afastamento no mês
                primeiro_dia_mes = date(ano, mes, 1)
                ultimo_dia_mes = date(ano, mes, total_dias)
                inicio_ef = max(ic.data_inicio, primeiro_dia_mes)
                fim_ef = min(ic.data_fim, ultimo_dia_mes)

                if fim_ef >= inicio_ef:
                    dias_afastamento = (fim_ef - inicio_ef).days + 1
                    dias_trabalhados_no_mes = total_dias - dias_afastamento
                    ajuste = calcular_ajuste_afastamento(
                        vlr_base=base_vendas,
                        dias_afastamento=dias_afastamento,
                        dias_trabalhados=dias_trabalhados_no_mes,
                        total_dias=total_dias,
                    )
                    # O valor de afastamento já é o adicional — não reduz o fator geral
                    bonus += ajuste

                    print_debug("Aplicando regra de afastamento.")
                    print_debug(f"Dias de afastamento no mês: {dias_afastamento}")
                    print_debug(f"Dias trabalhados no mês: {dias_trabalhados_no_mes}")
                    print_debug(f"Ajuste de afastamento calculado: R$ {ajuste:,.2f}")
                    print_debug(f"Bônus acumulado: R$ {bonus:,.2f}")

            elif ic.tipo == "bonus_fixo":
                bonus += ic.valor

                print_debug("Aplicando bônus fixo.")
                print_debug(f"Valor do bônus fixo: R$ {ic.valor:,.2f}")
                print_debug(f"Bônus acumulado: R$ {bonus:,.2f}")

            elif ic.tipo == "perc_bonus":
                perc += ic.valor

                print_debug("Aplicando bônus percentual.")
                print_debug(f"Percentual adicional: {ic.valor * 100:.2f}%")
                print_debug(f"Percentual acumulado: {perc * 100:.2f}%")

            elif ic.tipo == "admissao_bonus":
                # Bônus para admitidos até determinado dia
                if admitido_no_mes and func.data_admissao.day <= ic.data_inicio.day:
                    bonus += ic.valor

                    print_debug("Aplicando bônus de admissão.")
                    print_debug(f"Valor do bônus de admissão: R$ {ic.valor:,.2f}")
                    print_debug(f"Bônus acumulado: R$ {bonus:,.2f}")

        # --- Comissão base ---
        valor_comissao_bruto = base_vendas * perc
        valor_comissao_proporcional = valor_comissao_bruto * fator

        # --- Bônus de meta por faixa (ex: dezembro) ---
        bonus_faixa = _calcular_bonus_faixa(
            eh_gerente=eh_gerente,
            cod_marca=func.cod_marca,
            base_vendas=base_vendas,
            overrides=overrides,
        )
        bonus += bonus_faixa

        if bonus_faixa:
            print_debug("Aplicando bônus por faixa.")
            print_debug(f"Bônus por faixa calculado: R$ {bonus_faixa:,.2f}")
            print_debug(f"Bônus total acumulado: R$ {bonus:,.2f}")

        valor_final = valor_comissao_proporcional + bonus

        print_debug("")
        print_debug("---------- RESUMO DO CÁLCULO ----------")
        print_debug(f"Base de vendas: R$ {base_vendas:,.2f}")
        print_debug(f"Percentual de comissão: {perc * 100:.2f}%")
        print_debug(f"Comissão bruta = R$ {base_vendas:,.2f} x {perc * 100:.2f}% = R$ {valor_comissao_bruto:,.2f}")
        print_debug(f"Fator proporcional aplicado: {fator:.4f}")
        print_debug(f"Comissão proporcional = R$ {valor_comissao_bruto:,.2f} x {fator:.4f} = R$ {valor_comissao_proporcional:,.2f}")
        print_debug(f"Bônus total: R$ {bonus:,.2f}")
        print_debug(f"VALOR FINAL = R$ {valor_final:,.2f}")
        print_debug("----------------------------------------")

        resultados.append(
            ResultadoComissionamento(
                matricula=func.matricula,
                cod_loja=func.cod_loja,
                cod_marca=func.cod_marca,
                base_vendas=base_vendas,
                perc_comissao=perc,
                valor_comissao_bruto=valor_comissao_bruto,
                ajuste_proporcional=fator,
                bonus=bonus,
                valor_final=valor_final,
            )
        )

    return resultados


# ---------------------------------------------------------------------------
# Bônus por faixa de venda (regra de dezembro e similares)
# ---------------------------------------------------------------------------


def _calcular_bonus_faixa(
    eh_gerente: bool,
    cod_marca: int,
    base_vendas: float,
    overrides: dict,
) -> float:
    """
    Aplica bônus por faixa de venda conforme regras do mês (overrides).
    Espera chave 'bonus_faixa_funcionario' e 'bonus_faixa_gerente' no overrides.
    Cada entry é: {'marcas': [10,20], 'faixas': [(min, max, valor), ...]}
    """
    bonus = 0.0

    if not eh_gerente:
        regra = overrides.get("bonus_faixa_funcionario")
        if regra and cod_marca in regra.get("marcas", []):
            bonus += _faixa(base_vendas, regra["faixas"])
    else:
        regra = overrides.get("bonus_faixa_gerente")
        if regra and cod_marca in regra.get("marcas", []):
            bonus += _faixa(base_vendas, regra["faixas"])

    return bonus


def _faixa(valor: float, faixas: list[tuple[float, float, float]]) -> float:
    """
    faixas: lista de (min_inclusive, max_inclusive, bonus)
            use float('inf') para sem limite superior
    """
    for minimo, maximo, bonus in faixas:
        if minimo <= valor <= maximo:
            return bonus
    return 0.0


def carregar_overrides_do_mes(
    regras_mongo: list[dict],
    ano: int,
    mes: int,
) -> dict:
    """
    Recebe lista de documentos do MongoDB,
    filtra os vigentes no mês e combina em um único dict de overrides.
    """
    overrides_combinados: dict = {
        "perc_override": {},
        "marca_override": {},
        "perc_adicional": {},
    }

    for doc in regras_mongo:
        if doc.get("tipo") != "override":
            continue

        regra = OverridesMensais(**doc["override"])

        if not regra.esta_vigente(ano, mes):
            continue

        parsed = regra.to_dict()
        overrides_combinados["perc_override"].update(parsed["perc_override"])
        overrides_combinados["marca_override"].update(parsed["marca_override"])
        overrides_combinados["perc_adicional"].update(parsed["perc_adicional"])

    return overrides_combinados


def carregar_intercorrencias_do_mes(
    regras_mongo: list[dict],
    ano: int,
    mes: int,
) -> list:
    """
    Filtra intercorrências vigentes e converte para objetos Intercorrencia.
    """

    resultado = []
    for doc in regras_mongo:
        if doc.get("tipo") != "intercorrencia":
            continue
        for ic in doc.get("intercorrencias", []):
            sazonal = IntercorrenciaSazonal(**ic)
            if sazonal.esta_vigente(ano, mes):
                resultado.append(
                    Intercorrencia(
                        matricula=sazonal.matricula,
                        tipo=sazonal.tipo,
                        data_inicio=sazonal.vigencia_inicio,
                        data_fim=sazonal.vigencia_fim,
                        valor=sazonal.valor,
                    )
                )
    return resultado


if __name__ == "__main__":
    DEBUG_COMISSIONAMENTO = True

    output_ia = {
        "tipo": "intercorrencia",
        "override": None,
        "intercorrencias": [
            {
                "matricula": "MATRIC-10",
                "tipo": "bonus_venda",
                "valor": 3500,
                "vigencia_inicio": "2025-01-01",
                "vigencia_fim": "2025-12-31",
            },
            {
                "matricula": "MATRIC-10",
                "tipo": "bonus_venda",
                "valor": 4000,
                "vigencia_inicio": "2025-01-01",
                "vigencia_fim": "2025-12-31",
            },
            {
                "matricula": "MATRIC-10",
                "tipo": "bonus_venda",
                "valor": 4500,
                "vigencia_inicio": "2025-01-01",
                "vigencia_fim": "2025-12-31",
            },
            {
                "matricula": "MATRIC-20",
                "tipo": "bonus_venda",
                "valor": 3500,
                "vigencia_inicio": "2025-01-01",
                "vigencia_fim": "2025-12-31",
            },
            {
                "matricula": "MATRIC-20",
                "tipo": "bonus_venda",
                "valor": 4000,
                "vigencia_inicio": "2025-01-01",
                "vigencia_fim": "2025-12-31",
            },
            {
                "matricula": "MATRIC-20",
                "tipo": "bonus_venda",
                "valor": 4500,
                "vigencia_inicio": "2025-01-01",
                "vigencia_fim": "2025-12-31",
            },
        ],
        "justificativa": "Regra de bônus por faixa de venda individual foi aplicada para marcas 10 e 20, com base no valor total de vendas superior a R$40 mil, conforme especificado no contexto de regras de comissionamento.",
    }

    funcionarios = [
        Funcionario(
            matricula="MATRIC-227",
            cod_marca=10,
            descr_marca="Marca 10",
            cod_loja="LOJA-1",
            descr_loja="Loja 1",
            data_admissao=date(2020, 1, 1),
            data_demissao=None,
            cod_cargo=300,
            descr_cargo="Vendedor Loja",
        )
    ]

    vendas = [
        Venda(
            matricula="MATRIC-227", cod_marca=10, cod_loja="LOJA-1", vlr_venda=25361.90
        )
    ]

    tabela_comissao = [
        ComissionamentoBase(cod_marca=10, cod_cargo=300, perc_comissao=0.025)  # 2.5%
    ]

    # --- Converter intercorrências do output da IA ---
    intercorrencias = carregar_intercorrencias_do_mes(
        regras_mongo=[output_ia],
        ano=2024,
        mes=12,
    )

    resultados = calcular_comissionamento(
        funcionarios=funcionarios,
        vendas=vendas,
        tabela_comissao=tabela_comissao,
        intercorrencias=intercorrencias,
        ano=2024,
        mes=12,
    )

    for r in resultados:
        print(f"""
Matrícula:       {r.matricula}
Base de vendas:  R$ {r.base_vendas:,.2f}
% Comissão:      {r.perc_comissao * 100:.2f}%
Comissão bruta:  R$ {r.valor_comissao_bruto:,.2f}
Bônus:           R$ {r.bonus:,.2f}
VALOR FINAL:     R$ {r.valor_final:,.2f}
        """)
