import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source"

EXCLUDED_PREFIXES = ("quiver_",)
EXCLUDED_NAMES = {"Step1.txt", "name.txt"}


def input_files():
    for path in sorted(ROOT.glob("*.txt")):
        if path.name in EXCLUDED_NAMES:
            continue
        if path.name.startswith(EXCLUDED_PREFIXES):
            continue
        yield path


def needs_compute(txt_path: Path) -> bool:
    stem = txt_path.stem
    return not (ROOT / f"{stem}.log").exists()


def run_gap_streaming(script_path: Path) -> None:
    proc = subprocess.Popen(
        ["gap", "-q", str(script_path)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        print(line, end="", flush=True)
    return_code = proc.wait()
    if return_code != 0:
        raise subprocess.CalledProcessError(return_code, ["gap", "-q", str(script_path)])


def compute_one(txt_path: Path) -> None:
    stem = txt_path.stem
    log_path = ROOT / f"{stem}.log"
    wrapper = f'''
OnBreak := QUIT;;
input_txt_path := "{txt_path.as_posix()}";;
output_log_path := "{log_path.as_posix()}";;
Read("{(SOURCE / 'Step2Core.g').as_posix()}");;
RunARQuiverComputation();;
QUIT;
'''
    with tempfile.NamedTemporaryFile("w", suffix=".g", delete=False) as tmp:
        tmp.write(wrapper)
        tmp_path = Path(tmp.name)
    try:
        print(f"[compute] {txt_path.name} -> {log_path.name}", flush=True)
        run_gap_streaming(tmp_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def main() -> None:
    targets = [p for p in input_files() if needs_compute(p)]
    if not targets:
        print("No pending .txt inputs need computation.", flush=True)
        return
    for txt_path in targets:
        compute_one(txt_path)


if __name__ == "__main__":
    main()
