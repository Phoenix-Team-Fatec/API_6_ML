"""
Extração de uso de tokens de respostas de LLM.

LangChain expõe tokens em `response.usage_metadata` quando o provider
retorna essa informação. Provedores como Groq, OpenAI, Anthropic e Google
GenAI populam normalmente. Modelos locais (Ollama, HF transformers) podem
não preencher.

O helper retorna (0, 0) silenciosamente quando não há metadados, evitando
quebrar o fluxo.
"""
from __future__ import annotations

from typing import Any


def extract_tokens(response: Any) -> tuple[int, int]:
    """
    Extrai (input_tokens, output_tokens) de uma resposta do LangChain.

    Aceita qualquer objeto que possa ter `usage_metadata`. Se o atributo
    não existir ou estiver vazio, retorna (0, 0).
    """
    metadata = getattr(response, "usage_metadata", None) or {}
    input_tokens = int(metadata.get("input_tokens", 0) or 0)
    output_tokens = int(metadata.get("output_tokens", 0) or 0)
    return input_tokens, output_tokens