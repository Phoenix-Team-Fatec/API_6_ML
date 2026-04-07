from langchain_core.messages import HumanMessage
from src.agent.graph.builder import build_graph
import json
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich import print as rprint
from dotenv import load_dotenv

load_dotenv()

console = Console()
graph = build_graph()


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
            conteudo = (msg.content or "")[:300]  # limita para não poluir
            if len(msg.content or "") > 1000:
                conteudo += "..."
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

    result = graph.invoke({
        "messages": [HumanMessage(content=(
            "Somente para este mês, o % de comissionamento da marca 20 "
            "será aplicada em todos os cargos da marca 10"
        ))],
        "user_request": (
            "Somente para este mês, o % de comissionamento da marca 20 "
            "será aplicada em todos os cargos da marca 10"
        ),
        "rules_context": "",
        "code_context": "",
        "raw_output": "",
        "validated_output": None,
        "review_errors": [],
        "iterations": 0,
    })

    format_json(result)
    return result


if __name__ == "__main__":
    main()