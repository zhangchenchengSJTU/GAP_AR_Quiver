import json
import mimetypes
import subprocess
import sys
import tempfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source"
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))

from compute_all import compute_one  # noqa: E402
from render_all import render_one  # noqa: E402
from visualize_core import parse_dot_string, parse_dot_string_with_edge_labels, parse_quiver_data  # noqa: E402


def parse_ids(value, all_ids):
    text = " ".join(map(str, value)) if isinstance(value, list) else str(value or "")
    text = text.strip()
    if not text or text.lower() in {"all", "*"}:
        return sorted(all_ids)
    ids = []
    for part in text.replace(",", " ").split():
        try:
            n = int(part)
        except ValueError:
            continue
        if n in all_ids and n not in ids:
            ids.append(n)
    return sorted(ids)


def ensure_computed_and_rendered(stem, force=False):
    txt_path = ROOT / f"{stem}.txt"
    log_path = ROOT / f"{stem}.log"
    html_path = ROOT / f"{stem}.html"
    if not txt_path.exists():
        raise FileNotFoundError(f"No input file {txt_path.name}")
    if force or not log_path.exists():
        compute_one(txt_path)
    if force or not html_path.exists():
        render_one(log_path)
    return log_path, html_path


def load_edges(stem):
    log_path, _ = ensure_computed_and_rendered(stem)
    parsed = parse_quiver_data(str(log_path))
    dot_content = parsed[4]
    syz_content = parsed[5]
    hom_content = parsed[9]
    ext_content = parsed[10]
    if dot_content is None:
        raise ValueError(f"Could not parse quiver data from {log_path.name}")
    nodes, _ = parse_dot_string(dot_content)
    all_ids = {int(x) for x in nodes if isinstance(x, int) or str(x).isdigit()}
    syz_edges = []
    if syz_content:
        _, syz_edges = parse_dot_string(syz_content)
    cosyz_edges = []
    cosyz_content = getattr(sys.modules.get("visualize_core"), "cosyzygy_content", None)
    if cosyz_content:
        _, cosyz_edges = parse_dot_string(cosyz_content)
    hom_edges = []
    if hom_content:
        _, hom_edges = parse_dot_string_with_edge_labels(hom_content)
    ext_edges = []
    if ext_content:
        _, ext_edges = parse_dot_string_with_edge_labels(ext_content)
    return sorted(all_ids), hom_edges, ext_edges, syz_edges, cosyz_edges


def edge_dim(edge):
    return str(edge[2] if len(edge) >= 3 and edge[2] is not None else "1")


def nonzero(edges, a, b):
    return any(int(e[0]) == int(a) and int(e[1]) == int(b) and edge_dim(e) != "0" for e in edges)


def pairs(edges, left, right):
    lset = set(left)
    rset = set(right)
    out = []
    for e in edges:
        a, b = int(e[0]), int(e[1])
        if a in lset and b in rset and edge_dim(e) != "0":
            out.append(f"{a}→{b}:{edge_dim(e)}")
    return out


def image(edges, input_ids):
    s = set(input_ids)
    return sorted({int(e[1]) for e in edges if int(e[0]) in s})


def right_perp(all_ids, edges, input_ids):
    return [x for x in all_ids if all(not nonzero(edges, a, x) for a in input_ids)]


def left_perp(all_ids, edges, input_ids):
    return [x for x in all_ids if all(not nonzero(edges, x, a) for a in input_ids)]


def fmt_set(ids):
    ids = sorted({int(x) for x in ids})
    return " ".join(map(str, ids)) if ids else "∅"


def calculate(payload):
    stem = str(payload.get("source") or "untitled").replace(".html", "").replace(".log", "").replace(".txt", "")
    op = str(payload.get("operation") or "Hom")
    ext_i = int(payload.get("i") or 1)
    all_ids, hom_edges, ext_edges, syz_edges, cosyz_edges = load_edges(stem)
    a_ids = parse_ids(payload.get("A", ""), set(all_ids))
    b_ids = parse_ids(payload.get("B", ""), set(all_ids))
    if op == "Hom":
        return ", ".join(pairs(hom_edges, a_ids, b_ids)) or "0"
    if op == "Ext":
        return (", ".join(pairs(ext_edges, a_ids, b_ids)) or "0") if ext_i == 1 else "Only Ext^1 data is available."
    if op == "Syzygy":
        return fmt_set(image(syz_edges, a_ids))
    if op == "Cosyzygy":
        return fmt_set(image(cosyz_edges, a_ids))
    if op == "Homperp":
        return fmt_set(right_perp(all_ids, hom_edges, a_ids))
    if op == "perpHom":
        return fmt_set(left_perp(all_ids, hom_edges, a_ids))
    if op in {"Extperp", "Extprep"}:
        return fmt_set(right_perp(all_ids, ext_edges, a_ids))
    if op in {"perpExt", "prepExt"}:
        return fmt_set(left_perp(all_ids, ext_edges, a_ids))
    if op == "Gen":
        return fmt_set([x for x in all_ids if any(nonzero(hom_edges, a, x) for a in a_ids)])
    if op == "Cog":
        return fmt_set([x for x in all_ids if any(nonzero(hom_edges, x, a) for a in a_ids)])
    if op == "Extension":
        return ", ".join(pairs(ext_edges, a_ids, b_ids)) or "No nonzero Ext^1 pairs in current data."
    raise ValueError(f"Unknown operation: {op}")


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class Handler(BaseHTTPRequestHandler):
    def send_common_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_common_headers()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_common_headers()
        self.end_headers()

    def read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        return json.loads(raw or "{}")

    def do_POST(self):
        try:
            if self.path == "/api/gap/calc":
                payload = self.read_json()
                self.send_json({"ok": True, "output": calculate(payload)})
                return
            if self.path == "/api/gap/recompute":
                payload = self.read_json()
                stem = str(payload.get("source") or "untitled").replace(".txt", "")
                log_path, html_path = ensure_computed_and_rendered(stem, force=True)
                self.send_json({"ok": True, "log": log_path.name, "html": html_path.name})
                return
            self.send_json({"ok": False, "error": "unknown endpoint"}, 404)
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, 500)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.send_json({"ok": True})
            return
        rel = parsed.path.lstrip("/") or "untitled.html"
        rel = rel.split("?", 1)[0]
        target = (ROOT / rel).resolve()
        if not str(target).startswith(str(ROOT.resolve())) or not target.is_file():
            self.send_error(404)
            return
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_common_headers()
        self.end_headers()
        self.wfile.write(data)


def main():
    host = "0.0.0.0"
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Serving {ROOT} on http://{host}:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
