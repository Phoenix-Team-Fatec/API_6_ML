"""
Helpers de tracing manual.
 
Usamos spans manuais apenas nos pontos cegos do autolog:
- etapas internas do review_node (parse, schema, regras)
- guardrail do agent_node
- heurísticas do _limpar_json
"""

from contextlib import contextmanager
from typing import Any, Iterator

import mlflow

@contextmanager
def trace_block(name: str, **attributes: Any) -> Iterator[Any]:
    """
    Abre um span manual dentro do trace atual.
 
    Uso:
        with trace_block("parse_json", raw_length=len(raw)) as span:
            data = json.loads(raw)
            span.set_attribute("parsed_keys", list(data.keys()))
 
    - Cria um span filho do span ativo (ex.: o nó do LangGraph).
    - Atributos passados no kwargs são registrados já na abertura.
    - Exceções dentro do bloco são capturadas no span automaticamente.
    """
    with mlflow.start_span(name=name) as span:
        for key, value in attributes.items():
            span.set_attribute(key, value)
        yield span