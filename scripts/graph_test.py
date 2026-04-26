from langchain_core.messages import HumanMessage
from src.agent.graph.builder import build_graph
import json
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich import print as rprint
from dotenv import load_dotenv
from src.agent.observability.setup import setup_observability

load_dotenv()
setup_observability()

console = Console()
graph = build_graph(provider='google-genai')


def format_json(data) -> None:
    """Exibe o resultado do grafo formatado no terminal."""

    # --- Erros de validação ---
    errors = data.get("review_errors", [])
    if errors:
        console.print(Panel(
            "\n".join(f"[red]• {e}[/red]" for e in errors),
            title="[bold red]Erros de validação[/bold red]",
            border_style="red",
        ))

    # --- Output validado ---
    validated = data.get("validated_output")
    if validated:
        json_str = json.dumps(validated, indent=2, ensure_ascii=False, default=str)
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
        console.print(Panel(
            syntax,
            title="[bold green]Objeto gerado[/bold green]",
            border_style="green",
        ))

    # --- Raw output do modelo ---
    raw = data.get("raw_output", "")
    if raw:
        syntax = Syntax(raw, "json", theme="monokai", line_numbers=True)
        console.print(Panel(
            syntax,
            title="[bold yellow]Raw output do modelo[/bold yellow]",
            border_style="yellow",
        ))

    # --- Resumo das mensagens trocadas ---
    messages = data.get("messages", [])
    if messages:
        table = Table(title="Mensagens do grafo", show_lines=True)
        table.add_column("Tipo", style="cyan", width=20)
        table.add_column("Conteúdo", style="white")

        for msg in messages:
            tipo = type(msg).__name__
            content = msg.content if hasattr(msg, "content") else msg
            if isinstance(content, (dict, list)):
                conteudo = json.dumps(content, ensure_ascii=False, default=str)
            else:
                conteudo = str(content or "")
            if len(conteudo) > 1000:
                conteudo = conteudo[:300] + "..."
            table.add_row(tipo, conteudo)

        console.print(table)

    # --- Iterações utilizadas ---
    iterations = data.get("iteration", 0)
    console.print(f"\n[dim]Iterações utilizadas: {iterations}[/dim]")


def main():
    console.print(Panel(
        "[bold]Iniciando agente de comissionamento...[/bold]",
        border_style="blue"
    ))

    result = graph({
        "messages": [HumanMessage(content=(
            "Os funcionários abaixo receberam um bônus ﬁxo de R$20.000 por" 
            "tempo de casa a ser acrescido na sua respectiva base de calculo de"
            "vendas para efeito de comissionamento:"
            'i. MATRIC-227'
            'ii. MATRIC-139'
            'iii. MATRIC-400'
            'iv. MATRIC-122'
            'v. MATRIC-387'
            'vi. MATRIC-78'
            'vii. MATRIC-10'
            'viii. MATRIC-356'
            'ix. MATRIC-405'
        ))],
        "user_request": (
            "Os funcionários abaixo receberam um bônus ﬁxo de R$20.000 por" 
            "tempo de casa a ser acrescido na sua respectiva base de calculo de"
            "vendas para efeito de comissionamento:"
            'i. MATRIC-227'
            'ii. MATRIC-139'
            'iii. MATRIC-400'
            'iv. MATRIC-122'
            'v. MATRIC-387'
            'vi. MATRIC-78'
            'vii. MATRIC-10'
            'viii. MATRIC-356'
            'ix. MATRIC-405'
        ),
        "rules_context": "",
        "code_context": "",
        "raw_output": "",
        "validated_output": None,
        "review_errors": [],
        "iteration": 0,
    })

    format_json(result)
    return result


if __name__ == "__main__":
    main()