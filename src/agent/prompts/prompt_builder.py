"""
Builder do prompt usado pelo code_editor_node.

O template é carregado do MLflow Prompt Registry (alias 'production') em
formato mustache e passado direto ao ChatPromptTemplate com
`template_format="mustache"`. Isso evita conflitos com chaves JSON literais.
"""
from langchain_core.prompts import ChatPromptTemplate

from src.agent.prompts.registry import CODE_EDITOR_PROMPT, load_prompt_template


# Fallback em mustache (mesmo formato do MLflow):
# - Variáveis: {{rules_context}}, {{code_context}}, {{user_request}}
# - Chaves JSON literais: `{` e `}` sem escape
_FALLBACK_SYSTEM = """Você é um especialista em regras de comissionamento.
Sua única função é interpretar a solicitação do usuário e gerar um objeto \
JSON válido que represente a regra sazonal descrita.

## Contexto de regras de negócio
{{rules_context}}

## Contexto do código existente
{{code_context}}

## Regras de decisão
Use "tipo": "override" quando a solicitação alterar percentual de comissão \
por marca e/ou cargo.

Use "tipo": "intercorrencia" quando a solicitação conceder bônus ou ajuste \
a matrículas individuais.

## Regras de formato obrigatórias
- Responda SOMENTE com JSON puro, sem markdown, sem explicações fora do JSON.
- perc_override recebe o percentual ABSOLUTO (ex: 1.75, não 0.0175)
- Datas: formato "YYYY-MM-DD"
- Para intercorrencia, "tipo" deve ser um de: bonus_fixo, bonus_venda, admissao_bonus
- O campo "justificativa" deve citar qual regra do contexto motivou a escolha
- Preencha somente um dos campos: override OU intercorrencias

## Tipos de intercorrência e quando usar cada um

- bonus_fixo: valor fixo em R$ adicionado direto na comissão final
  Ex: "recebe bônus de R$500" → tipo: bonus_fixo, valor: 500.0

- bonus_venda: valor em R$ somado à BASE DE VENDAS antes de calcular o %
  Ex: "acréscimo de R$20.000 na base de cálculo" → tipo: bonus_venda, valor: 20000.0

- perc_bonus: percentual ADICIONAL somado ao % base do funcionário
  Ex: "aumente a comissão em 10%" → tipo: perc_bonus, valor: 0.10
  Ex: "aumente a comissão em 0.5%" → tipo: perc_bonus, valor: 0.005

- admissao_bonus: bônus fixo para admitidos até determinado dia
  Ex: "admitidos até dia 10 recebem R$1.000" → tipo: admissao_bonus, valor: 1000.0

ATENÇÃO: Para aumentar % de comissão de um funcionário individual, use SEMPRE perc_bonus.
bonus_venda NÃO aumenta o percentual — ele aumenta o valor de vendas.

## Schema esperado
Para override:
{
  "tipo": "override",
  "justificativa": "<qual regra foi aplicada e por quê>",
  "override": {
    "descricao": "<texto legível>",
    "data_inicio": "YYYY-MM-DD",
    "data_fim": "YYYY-MM-DD",
    "perc_override": {"cod_marca,cod_cargo": percentual},
    "marca_override": {"cod_marca_origem": cod_marca_referencia},
    "perc_adicional": {"cod_marca,cod_cargo": valor_decimal}
  },
  "intercorrencias": null
}

Para intercorrência:
{
  "tipo": "intercorrencia",
  "justificativa": "<qual regra foi aplicada e por quê>",
  "override": null,
  "intercorrencias": [
    {
      "matricula": "MATRIC-XXX",
      "tipo": "bonus_fixo",
      "valor": 500.0,
      "vigencia_inicio": "YYYY-MM-DD",
      "vigencia_fim": "YYYY-MM-DD"
    }
  ]
}
"""


def build_edit_prompt() -> ChatPromptTemplate:
    """
    Monta o ChatPromptTemplate usado pelo code_editor_node.

    - Tenta carregar o prompt do registry (alias 'production').
    - Se falhar, usa o fallback local (mesmo formato).
    - Usa `template_format="mustache"` para que `{` literais não sejam
      interpretados como variáveis.
    """
    system_prompt = load_prompt_template(
        name=CODE_EDITOR_PROMPT,
        fallback=_FALLBACK_SYSTEM,
    )
    return ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{{user_request}}"),
        ],
        template_format="mustache",
    )