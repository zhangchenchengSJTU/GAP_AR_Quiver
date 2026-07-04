import os
import selectors
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source"

EXCLUDED_PREFIXES = ("quiver_",)
EXCLUDED_NAMES = {"Step1.txt", "name.txt"}
DEFAULT_GAP_TIMEOUT_SEC = int(os.environ.get("ARQUIVER_GAP_TIMEOUT_SEC", "900"))


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


def run_gap_streaming(script_path: Path, timeout_sec: int = DEFAULT_GAP_TIMEOUT_SEC) -> None:
    proc = subprocess.Popen(
        ["gap", "-q", "--quitonbreak", str(script_path)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1,
    )
    assert proc.stdout is not None
    selector = selectors.DefaultSelector()
    selector.register(proc.stdout, selectors.EVENT_READ)
    deadline = time.monotonic() + timeout_sec
    timed_out = False
    while proc.poll() is None:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            timed_out = True
            proc.kill()
            break
        for key, _ in selector.select(timeout=min(1.0, remaining)):
            line = key.fileobj.readline()
            if line:
                print(line, end="", flush=True)
    for line in proc.stdout:
        print(line, end="", flush=True)
    selector.close()
    return_code = proc.wait()
    if timed_out:
        raise TimeoutError(f"GAP computation exceeded {timeout_sec} seconds for {script_path}")
    if return_code != 0:
        raise subprocess.CalledProcessError(return_code, ["gap", "-q", "--quitonbreak", str(script_path)])


def compute_one(txt_path: Path) -> None:
    stem = txt_path.stem
    log_path = ROOT / f"{stem}.log"
    wrapper = f'''
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
