"""
Integração com o MLflow Prompt Registry.
 
Responsabilidades:
- Registrar novas versões dos prompts do agente.
- Carregar a versão ativa (via alias) no momento da execução.
- Fornecer fallback silencioso para a string local caso o registry falhe,
  garantindo que o agente continue funcionando mesmo sem o MLflow no ar.
"""

from __future__ import annotations

import logging 

import mlflow

logger = logging.getLogger(__name__)

# Nomes dos prompts registrados no MLflow
AGENT_SYSTEM_PROMPT = "agent-system-prompt"
CODE_EDITOR_PROMPT = "code-editor-prompt"

# Alias utilizado para identificar o prompt em produção
PRODUCTION_ALIAS = "production"

def register_prompt_version(
    name: str,
    template: str,
    commit_message: str,
    tags: dict[str, str] | None = None,
) -> int:
    """
    Registra uma nova versão do prompt e retorna o número da versão criada.
 
    `template` deve usar sintaxe `{{variavel}}` (double-brace) — que é o padrão
    do MLflow Prompt Registry. Para uso com LangChain, converta depois com
    `.to_single_brace_format()`.
    """
    prompt = mlflow.genai.register_prompt(
        name=name,
        template=template,
        commit_message=commit_message,
        tags=tags or {},
    )     
    
    logger.info(f"Registrado prompt '{name}' versão {prompt.version} com commit: {commit_message}")
    return prompt.version


def promote_to_production(name: str, version: int) -> None:
    """Move o alias `production` para a versão indicada."""
    mlflow.genai.set_prompt_alias(
        name=name,
        alias=PRODUCTION_ALIAS,
        version=version
    )
    logger.info(f"Promovido prompt '{name}' versão {version} para produção (alias='{PRODUCTION_ALIAS}')")



def load_prompt_template(
    name: str,
    alias: str = PRODUCTION_ALIAS,
    fallback: str | None = None,
) -> str:
    """
    Carrega o template de um prompt no formato single-brace (compatível com LangChain).
 
    Se a carga falhar (registry indisponível, prompt inexistente etc.) e um
    `fallback` for fornecido, retorna o fallback. Caso contrário, propaga a exceção.
    """
    uri = f"prompts:/{name}@{alias}"
    try:
        prompt = mlflow.genai.load_prompt(uri)
        return prompt.to_single_brace_format()
    except Exception as exc:
        if fallback is not None:
            logger.warning(
                "Falha ao carregar prompt '%s' (%s). Usando fallback local.",
                uri, exc,
            )
            return fallback
        raise

