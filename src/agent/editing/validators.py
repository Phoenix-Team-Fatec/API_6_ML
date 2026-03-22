import ast
import re
from pathlib import Path


def sanitize_code(code: str) -> str:
    """Remove markdown fences, tags </think> e texto antes do código."""
    # Remove blocos </think> que o qwen3 adiciona
    code = re.sub(r"</?think>.*?</think>", "", code, flags=re.DOTALL)
    code = re.sub(r"</?think>", "", code)

    # Remove code fences ```python ... ``` ou ``` ... ```
    code = re.sub(r"^```[a-zA-Z]*\n", "", code.strip(), flags=re.MULTILINE)
    code = re.sub(r"```$", "", code.strip(), flags=re.MULTILINE)

    # Remove qualquer linha antes da primeira que começa com import, from, class, def ou #
    lines = code.splitlines()
    for i, line in enumerate(lines):
        if re.match(r"^(import |from |class |def |#|\"\"\"|''')", line):
            code = "\n".join(lines[i:])
            break

    return code.strip()


def validate_python_code(code: str) -> str:
    """Valida sintaxe e retorna o código limpo."""
    clean = sanitize_code(code)
    
    
    ast.parse(clean)
    return clean


def validate_target_file_exists(target_file: str) -> None:
    if not Path(target_file).exists():
        raise FileNotFoundError(f"Arquivo alvo não encontrado: {target_file}")