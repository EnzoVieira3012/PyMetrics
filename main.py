"""PyMetrics CLI entry point: interactive menu."""

import sys
from typing import Any

from cli.commands import cmd_dev_analysis, cmd_export, cmd_repo_analysis
from core.errors import GithubClientError
from core.github_client import GithubClient
from core.logging_setup import setup_logging

MENU = """
PyMetrics — Análise de performance GitHub
=========================================
1. Analisar repositório
2. Analisar desenvolvedor
3. Exportar relatório (última análise)
4. Sair
"""


def main() -> None:
    """Run the interactive menu loop."""
    setup_logging("INFO")
    last_metrics: dict[str, Any] | None = None
    try:
        client = GithubClient()
    except GithubClientError as exc:
        print(f"Erro ao iniciar: {exc}")
        print("Configure o GITHUB_TOKEN no .env e tente novamente.")
        sys.exit(1)

    while True:
        print(MENU)
        try:
            choice = input("Escolha uma opção [1-4]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAté logo!")
            break

        if choice == "1":
            try:
                last_metrics = cmd_repo_analysis(client)
            except GithubClientError as exc:
                print(f"Erro: {exc}")
        elif choice == "2":
            try:
                last_metrics = cmd_dev_analysis(client)
            except GithubClientError as exc:
                print(f"Erro: {exc}")
        elif choice == "3":
            last_metrics = cmd_export(last_metrics)
        elif choice == "4":
            print("Até logo!")
            break
        else:
            print("Opção inválida. Escolha 1 a 4.")


if __name__ == "__main__":
    main()
