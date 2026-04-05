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


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

COD_CARGO_GERENTE = 150
VALOR_FIXO_AFASTAMENTO = 3_500.0


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
        (c.cod_marca, c.cod_cargo): c.perc_comissao
        for c in tabela_comissao
    }

    # Aplicar overrides de % de comissão para o mês
    for (cod_marca, cod_cargo), perc in overrides.get("perc_override", {}).items():
        indice_comissao[(cod_marca, cod_cargo)] = perc

    # --- Consolidar vendas por matrícula e por loja ---
    vendas_por_matricula: dict[str, float] = {}
    vendas_por_loja: dict[str, float] = {}

    for v in vendas:
        vendas_por_matricula[v.matricula] = vendas_por_matricula.get(v.matricula, 0.0) + v.vlr_venda
        vendas_por_loja[v.cod_loja] = vendas_por_loja.get(v.cod_loja, 0.0) + v.vlr_venda

    # --- Indexar intercorrências por matrícula ---
    intercorr_por_matricula: dict[str, list[Intercorrencia]] = {}
    for ic in intercorrencias:
        intercorr_por_matricula.setdefault(ic.matricula, []).append(ic)

    resultados: list[ResultadoComissionamento] = []

    for func in funcionarios:
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
            continue

        # Ignorar admitidos após o mês de competência
        if func.data_admissao > date(ano, mes, total_dias):
            continue

        eh_gerente = func.cod_cargo == COD_CARGO_GERENTE

        # --- Base de vendas ---
        if eh_gerente:
            base_vendas = vendas_por_loja.get(func.cod_loja, 0.0)
        else:
            base_vendas = vendas_por_matricula.get(func.matricula, 0.0)

        # Bônus sobre base de vendas (ex: bônus por tempo de casa adicionado à base)
        bonus_base_venda = sum(
            ic.valor
            for ic in intercorr_por_matricula.get(func.matricula, [])
            if ic.tipo == "bonus_venda"
        )
        base_vendas += bonus_base_venda

        # --- % de comissão ---
        # Override de marca: ex "aplicar % da marca 20 em todos cargos da marca 10"
        cod_marca_efetivo = overrides.get("marca_override", {}).get(func.cod_marca, func.cod_marca)
        perc = indice_comissao.get((cod_marca_efetivo, func.cod_cargo), 0.0)

        # Acréscimo de % por regra do mês (ex: +0,5% para marca 30)
        perc += overrides.get("perc_adicional", {}).get((func.cod_marca, func.cod_cargo), 0.0)

        # --- Fator proporcional base ---
        fator = 1.0
        bonus = 0.0

        # Proporcional de admissão
        if admitido_no_mes:
            dias_ef = dias_trabalhados_admissao(func.data_admissao, ano, mes)
            fator = min(fator, fator_proporcional(dias_ef, total_dias))

        # Proporcional de demissão
        if demitido_no_mes:
            dias_ef = dias_trabalhados_demissao(func.data_demissao, ano, mes)
            fator = min(fator, fator_proporcional(dias_ef, total_dias))

        # Intercorrências do mês
        for ic in intercorr_por_matricula.get(func.matricula, []):
            if ic.tipo == "ferias" and ic.data_inicio and ic.data_fim:
                fator_f = calcular_fator_ferias(ic.data_inicio, ic.data_fim, ano, mes)
                fator = min(fator, fator_f)

            elif ic.tipo == "licenca_maternidade" and ic.data_inicio:
                fator_l = calcular_fator_licenca_maternidade(ic.data_inicio, ano, mes)
                fator = min(fator, fator_l)

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

            elif ic.tipo == "bonus_fixo":
                bonus += ic.valor

            elif ic.tipo == "admissao_bonus":
                # Bônus para admitidos até determinado dia
                if admitido_no_mes and func.data_admissao.day <= ic.data_inicio.day:
                    bonus += ic.valor

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

        valor_final = valor_comissao_proporcional + bonus

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