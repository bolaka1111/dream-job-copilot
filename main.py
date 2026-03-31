"""Dream Job Copilot – CLI entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.traceback import install as install_rich_traceback

install_rich_traceback(show_locals=False)
console = Console()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dream-job-copilot",
        description="🚀 Agentic AI pipeline that finds and applies to your dream job.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --resume resume.pdf
  python main.py --resume resume.docx --non-interactive
  python main.py --resume resume.pdf --output-dir ./my-applications
        """,
    )
    parser.add_argument(
        "--resume",
        required=True,
        metavar="PATH",
        help="Path to your resume file (.pdf or .docx)",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        default=False,
        help="Skip interactive feedback prompts (accept all recommendations)",
    )
    parser.add_argument(
        "--output-dir",
        metavar="DIR",
        default=None,
        help="Directory to save enhanced resumes and application logs (default: ./output)",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    resume_path = Path(args.resume)
    if not resume_path.exists():
        console.print(f"[bold red]Error:[/bold red] Resume file not found: {args.resume}")
        sys.exit(1)

    console.print(
        Panel(
            "[bold cyan]Dream Job Copilot[/bold cyan]\n"
            "Your AI-powered career agent – parsing, searching, and applying for you.",
            expand=False,
        )
    )

    # Lazy import so missing deps give a cleaner error
    try:
        from src.pipeline.copilot_pipeline import run_pipeline
    except ImportError as exc:
        console.print(
            f"[bold red]Import error:[/bold red] {exc}\n"
            "Run [bold]pip install -r requirements.txt[/bold] to install dependencies."
        )
        sys.exit(1)

    try:
        final_state = run_pipeline(
            resume_path=str(resume_path),
            interactive=not args.non_interactive,
            output_dir=args.output_dir,
        )
    except ValueError as exc:
        # Config/API key errors surface as ValueError
        console.print(f"[bold red]Configuration error:[/bold red] {exc}")
        console.print(
            "Tip: Copy [bold].env.example[/bold] to [bold].env[/bold] "
            "and fill in your API keys."
        )
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/yellow]")
        sys.exit(0)
    except Exception as exc:
        console.print_exception()
        sys.exit(1)

    errors = final_state.get("errors") or []
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
