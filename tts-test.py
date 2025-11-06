#!/usr/bin/env python3
"""
gTTS CLI — Simple, resilient Text-to-Speech with retries and Rich output.

Features
- Read text from --text, --file, or STDIN.
- Language (-l), TLD (--tld), slow mode (--slow).
- Retries with exponential backoff on transient HTTP errors (e.g., 429).
- Clean console output with Rich.

Usage examples
  python gtts_cli.py --text "Hola Daiego" -l es -o hola.mp3
  python gtts_cli.py --file input.txt -l es --tld es -o salida.mp3
  echo "texto por stdin" | python gtts_cli.py -l es -o out.mp3
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import argparse
import time

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.traceback import install as rich_traceback

from gtts import gTTS

console = Console()
rich_traceback(show_locals=False)


@dataclass
class TTSConfig:
    text: str
    lang: str = "es"
    tld: str = "es"
    slow: bool = False
    output: Path = Path("output.mp3")
    retries: int = 3
    backoff_base: float = 1.0  # seconds
    confirm_overwrite: bool = False


def read_text_arg(args: argparse.Namespace) -> str:
    if args.text:
        return args.text
    if args.file:
        p = Path(args.file)
        return p.read_text(encoding="utf-8")
    # Fallback: STDIN
    if not console.is_terminal:
        return console.file.read()
    console.print(
        Panel.fit(
            "[bold]Waiting for STDIN...[/bold]\n"
            "Tip: echo 'hola' | python gtts_cli.py -l es -o hola.mp3",
            title="Input",
        )
    )
    return console.file.read()


def synthesize(cfg: TTSConfig) -> None:
    if cfg.output.exists():
        if cfg.confirm_overwrite and not Confirm.ask(
            f"[yellow]File {cfg.output} exists. Overwrite?[/yellow]"
        ):
            console.print("[red]Aborted by user.[/red]")
            return

    attempt = 0
    last_exc: Optional[Exception] = None

    with console.status("[bold green]Synthesizing speech...[/bold green]"):
        while attempt <= cfg.retries:
            try:
                tts = gTTS(text=cfg.text, lang=cfg.lang, tld=cfg.tld, slow=cfg.slow)
                cfg.output.parent.mkdir(parents=True, exist_ok=True)
                tts.save(str(cfg.output))
                break
            except Exception as e:
                last_exc = e
                if attempt == cfg.retries:
                    raise
                sleep_s = cfg.backoff_base * (2**attempt)
                console.log(
                    f"[yellow]Retry {attempt+1}/{cfg.retries} after error: "
                    f"{type(e).__name__}: {e} — sleeping {sleep_s:.1f}s[/yellow]"
                )
                time.sleep(sleep_s)
                attempt += 1

    console.print(
        Panel.fit(
            f"[bold]Saved:[/bold] {cfg.output}\n"
            f"[bold]Lang:[/bold] {cfg.lang}  •  [bold]TLD:[/bold] {cfg.tld}  •  "
            f"[bold]Slow:[/bold] {cfg.slow}",
            title="gTTS Done",
            border_style="green",
        )
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gtts-cli",
        description="Minimal gTTS CLI with retries and Rich output.",
    )
    src = p.add_mutually_exclusive_group()
    src.add_argument("--text", type=str, help="Inline text to synthesize.")
    src.add_argument("--file", type=str, help="UTF-8 text file to synthesize.")
    p.add_argument("-l", "--lang", default="es", help="Language code (default: es).")
    p.add_argument("--tld", default="com", help="Google TLD (e.g., es, com, co.uk).")
    p.add_argument("--slow", action="store_true", help="Use slow speaking rate.")
    p.add_argument(
        "-o", "--output", default="output.mp3", help="Output MP3 path (default: output.mp3)."
    )
    p.add_argument("--retries", type=int, default=3, help="Retries on failure (default: 3).")
    p.add_argument(
        "--backoff-base",
        type=float,
        default=1.0,
        help="Exponential backoff base seconds (default: 1.0).",
    )
    p.add_argument(
        "--yes",
        action="store_true",
        help="Overwrite output without confirmation.",
    )
    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    text = read_text_arg(args).strip()
    if not text:
        console.print("[red]No input text provided.[/red]")
        raise SystemExit(2)

    cfg = TTSConfig(
        text=text,
        lang=args.lang,
        tld=args.tld,
        slow=args.slow,
        output=Path(args.output),
        retries=args.retries,
        backoff_base=args.backoff_base,
        confirm_overwrite=(not args.yes),
    )

    console.print(
        Panel.fit(
            f"[bold]Chars:[/bold] {len(cfg.text)}  •  [bold]Lang:[/bold] {cfg.lang}  •  "
            f"[bold]TLD:[/bold] {cfg.tld}  •  [bold]Slow:[/bold] {cfg.slow}",
            title="gTTS",
            border_style="cyan",
        )
    )
    synthesize(cfg)


if __name__ == "__main__":
    main()
