from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from visualize_core import create_and_save_quiver_html_with_tilting_graph  # noqa: E402


def log_files():
    for path in sorted(ROOT.glob("*.log")):
        yield path


def needs_render(log_path: Path) -> bool:
    return not (ROOT / f"{log_path.stem}.html").exists()


def render_one(log_path: Path) -> None:
    html_path = ROOT / f"{log_path.stem}.html"
    print(f"[render] {log_path.name} -> {html_path.name}")
    create_and_save_quiver_html_with_tilting_graph(str(log_path), str(html_path))


def main() -> None:
    targets = [p for p in log_files() if needs_render(p)]
    if not targets:
        print("No pending .log files need rendering.")
        return
    for log_path in targets:
        render_one(log_path)


if __name__ == "__main__":
    main()
