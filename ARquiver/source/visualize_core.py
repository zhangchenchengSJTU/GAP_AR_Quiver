
# ===== Step3.ipynb cell 0 =====
import re
import json
import ast
from pyvis.network import Network
from typing import Union
from pathlib import Path
BASE_DIR = Path.cwd()

# ===== Step3.ipynb cell 1 =====
def parse_dot_string(dot_string):
    nodes = {}
    edges = []
    
    # Determine if we are just parsing simple edges or full nodes
    # Pattern for nodes: ID [label="..."];
    # Support alphanumeric IDs
    # Relaxes regex to handle attributes more flexibly
    node_pattern = re.compile(r'^\s*(\w+)\s*\[.*?label="(.*?)".*?\]\s*;\s*$', re.MULTILINE)
    # Pattern for edges: U -> V [label="..."]; or U -> V;
    edge_pattern = re.compile(r'^\s*(\w+)\s*->\s*(\w+)\s*(?:\[.*?label="(.*?)".*?\])?\s*;\s*$', re.MULTILINE)

    # Parse nodes
    for match in node_pattern.finditer(dot_string):
        nid_str = match.group(1)
        nid = int(nid_str) if nid_str.isdigit() else nid_str
        label = match.group(2)
        nodes[nid] = {'label': label}

    # Parse edges
    for match in edge_pattern.finditer(dot_string):
        u_str = match.group(1)
        v_str = match.group(2)
        u = int(u_str) if u_str.isdigit() else u_str
        v = int(v_str) if v_str.isdigit() else v_str
        label = match.group(3)
        if label:
            edges.append((u, v, label))
        else:
            edges.append((u, v))
            
    return nodes, edges

# Alias: parse_dot_string already handles edge labels
parse_dot_string_with_edge_labels = parse_dot_string

# ===== Step3.ipynb cell 2 =====
def parse_quiver_data(quiver_file):
    # Read file content
    try:
        with open(quiver_file, 'r', encoding='utf-8') as f:
            content = f.read()
            content = re.sub(r"\\\s*\n\s*", "", content)
    except FileNotFoundError:
        return None, None, None, None, None, None, None, None, None, None, None, None, None, None
    # Keep a global reference for translation-quiver extraction
    globals()["input_file"] = quiver_file
    # Extract projective/injective modules using regex
    proj_match = re.search(r"Projective modules found \(Node IDs\): \[(.*?)\]", content)
    inj_match = re.search(r"Injective modules found \(Node IDs\):  \[(.*?)\]", content)
    tors_match = re.search(r"Torsionless modules found \(Node IDs\): \[(.*?)\]", content)
    refl_match = re.search(r"Reflexive modules found \(Node IDs\):  \[(.*?)\]", content)
    gp_match = re.search(r"Gorenstein projective modules found \(Node IDs\): \[(.*?)\]", content)
    gi_match = re.search(r"Gorenstein injective modules found \(Node IDs\):  \[(.*?)\]", content)
    # Extract projective/injective module IDs.
    def parse_id_set(match):
        if not match or not match.group(1):
            return set()
        raw = match.group(1).strip()
        if not raw:
            return set()
        return {int(n) for n in re.split(r"\s*,\s*", raw) if n.strip()}
    proj_ids = parse_id_set(proj_match)
    inj_ids = parse_id_set(inj_match)
    tors_ids = parse_id_set(tors_match)
    refl_ids = parse_id_set(refl_match)
    gp_ids = parse_id_set(gp_match)
    gi_ids = parse_id_set(gi_match)
    globals()["gorenstein_projective_ids"] = gp_ids
    globals()["gorenstein_injective_ids"] = gi_ids
    dot_match = re.search(r"digraph Quiver {([\s\S]*?)}", content)
    if not dot_match:
        return None, None, None, None, None, None, None, None, None, None, None, None, None, None
    dot_content = "digraph Quiver {" + dot_match.group(1) + "}"
    syz_match = re.search(r"digraph SyzygySummand {([\s\S]*?)}", content)
    syz_content = None
    if syz_match:
        syz_content = "digraph SyzygySummand {" + syz_match.group(1) + "}"
    cosyz_match = re.search(r"digraph CosyzygySummand {([\s\S]*?)}", content)
    cosyz_content = None
    if cosyz_match:
        cosyz_content = "digraph CosyzygySummand {" + cosyz_match.group(1) + "}"
    globals()["cosyzygy_content"] = cosyz_content
    rad_match = re.search(r"digraph RadicalSummand {([\s\S]*?)}", content)
    rad_content = None
    if rad_match:
        rad_content = "digraph RadicalSummand {" + rad_match.group(1) + "}"
    globals()["radical_content"] = rad_content
    corad_match = re.search(r"digraph CoradicalSummand {([\s\S]*?)}", content)
    corad_content = None
    if corad_match:
        corad_content = "digraph CoradicalSummand {" + corad_match.group(1) + "}"
    globals()["coradical_content"] = corad_content
    trans_match = re.search(r"digraph\s+TranslationQuiver\s*\{([\s\S]*?)\}", content)
    translation_content = None
    if trans_match:
        translation_content = "digraph TranslationQuiver {" + trans_match.group(1) + "}"
    q_match = re.search(r"digraph Q {([\s\S]*?)}", content)
    q_content = None
    if q_match:
        q_content = "digraph Q {" + q_match.group(1) + "}"
    hom_match = re.search(r"digraph HomDim {([\s\S]*?)}", content)
    hom_content = None
    if hom_match:
        hom_content = "digraph HomDim {" + hom_match.group(1) + "}"
    ext_match = re.search(r"digraph ExtDim {([\s\S]*?)}", content)
    ext_content = None
    if ext_match:
        ext_content = "digraph ExtDim {" + ext_match.group(1) + "}"
    rel_match = re.search(r"rel := ([^;\n]+);", content)
    rel_content = rel_match.group(1).strip() if rel_match else None
    module_data_gap = ""
    module_data_match = re.search(r"IndecomposableModuleData\s*:=\s*(\[[\s\S]*?\]);;", content)
    if module_data_match:
        module_data_gap = "IndecomposableModuleData := " + module_data_match.group(1).strip() + ";;"
    globals()["module_data_gap"] = module_data_gap
    # QuiverStructure (optional)
    structure_matches = re.findall(r"QuiverStructure\s*:=\s*\"(.*?)\"", content)
    quiver_structure = structure_matches[-1] if structure_matches else None
    # PD/ID data
    pdid_map = {}
    pdid_match = re.search(r"PDID\s*:=\s*(\[[\s\S]*?\]);", content)
    if pdid_match:
        try:
            pdid_list = ast.literal_eval(pdid_match.group(1))
            for row in pdid_list:
                if isinstance(row, (list, tuple)) and len(row) >= 3:
                    pdid_map[int(row[0])] = {"pd": int(row[1]), "id": int(row[2])}
        except Exception:
            pdid_map = {}
    top_soc_map = {}
    topsoc_match = re.search(r"TopSoc\s*:=\s*(\[[\s\S]*?\]);", content)
    if topsoc_match:
        try:
            topsoc_list = ast.literal_eval(topsoc_match.group(1))
            for row in topsoc_list:
                if isinstance(row, (list, tuple)) and len(row) >= 3:
                    top_soc_map[int(row[0])] = {"top": list(row[1]), "soc": list(row[2])}
        except Exception:
            top_soc_map = {}
    globals()["top_soc_map"] = top_soc_map
    # Tilting data: parse L/F/T blocks
    def parse_list_line(raw_line: str):
        raw = (raw_line or "").strip()
        if not raw or raw == "0":
            return []
        return [int(n) for n in re.split(r"\s*,\s*", raw) if n.strip()]

    def parse_class_expr(raw_expr: str):
        raw = (raw_expr or "").strip()
        if raw == "0":
            return []
        if raw.startswith("[") and raw.endswith("]"):
            raw = raw[1:-1]
        return parse_list_line(raw)
    
    tilting_data = []
# Old line (fails in Python 3.6):
    # blocks = re.split(r'(?=^L := )', content, flags=re.M)

    # New code (compatible with Python 3.6+):
    # We split ON the delimiter but KEEP it by using a capturing group (...)
    split_result = re.split(r'(^L := )', content, flags=re.M)
    
    # The output is now like: ['', 'L := ', 'content1', 'L := ', 'content2', ...]
    # We need to reconstruct the full blocks.
    blocks = []
    # If the file doesn't start with the delimiter, the first chunk is valid content
    if split_result and split_result[0].strip():
        blocks.append(split_result[0])
        
    # Iterate through the list, taking the delimiter and its following text chunk in pairs
    for i in range(1, len(split_result), 2):
        # The delimiter is at index i, the content is at i+1
        delimiter = split_result[i]
        text_chunk = split_result[i+1] if (i+1) < len(split_result) else ""
        blocks.append(delimiter + text_chunk)
    for block in blocks:
        if not block.strip(): continue
        l_match = re.search(r"^L\s*:=\s*\[(.*?)\]", block, re.M)
        f_match = re.search(r"^F\s*:=\s*\[(.*?)\]", block, re.M)
        t_match = re.search(r"^T\s*:=\s*\[(.*?)\]", block, re.M)
        
        if l_match and f_match and t_match:
            has_split = "Split" in block
            tilting_data.append({
                "L": parse_list_line(l_match.group(1)),
                "F": parse_list_line(f_match.group(1)),
                "T": parse_list_line(t_match.group(1)),
                "split": has_split
            })
            

    torsion_pair_data = []
    torsion_section = ""
    torsion_match = re.search(r"# --- TorsionPairTable --- #[\s\S]*?(?=# --- CotorsionPairTable --- #|PDID :=|$)", content)
    if torsion_match:
        torsion_section = torsion_match.group(0)
    for m in re.finditer(r"^T\s*:=\s*(0|\[[^\]]*\])\s*\|\s*F\s*:=\s*(0|\[[^\]]*\])", torsion_section, flags=re.M | re.S):
        torsion_pair_data.append({
            "T": parse_class_expr(m.group(1)),
            "F": parse_class_expr(m.group(2)),
        })
    if not torsion_pair_data and tilting_data:
        # Older output files do not have a TorsionPairTable; recover the visible
        # torsion-class list from the tilting table instead.
        seen_torsion_pairs = set()
        for item in tilting_data:
            key = (tuple(item.get("T", [])), tuple(item.get("F", [])))
            if key in seen_torsion_pairs:
                continue
            seen_torsion_pairs.add(key)
            torsion_pair_data.append({
                "T": list(item.get("T", [])),
                "F": list(item.get("F", [])),
            })

    def normalized_class_key(values):
        return tuple(sorted(int(v) for v in (values or []) if isinstance(v, int) or str(v).lstrip('-').isdigit()))

    tilting_pair_keys = {
        (normalized_class_key(item.get("T", [])), normalized_class_key(item.get("F", [])))
        for item in tilting_data
    }
    torsion_module_ids = set(int(k) for k in pdid_map.keys())
    for item in tilting_data:
        torsion_module_ids.update(normalized_class_key(item.get("L", [])))
        torsion_module_ids.update(normalized_class_key(item.get("F", [])))
        torsion_module_ids.update(normalized_class_key(item.get("T", [])))
    for item in torsion_pair_data:
        torsion_module_ids.update(normalized_class_key(item.get("T", [])))
        torsion_module_ids.update(normalized_class_key(item.get("F", [])))
    for item in torsion_pair_data:
        t_key = normalized_class_key(item.get("T", []))
        f_key = normalized_class_key(item.get("F", []))
        item["tilting"] = (t_key, f_key) in tilting_pair_keys
        item["split"] = set(t_key).union(f_key) == torsion_module_ids
        item["tagText"] = f"{'tilting' if item['tilting'] else 'non-tilting'} | {'split' if item['split'] else 'non-split'}"

    def injective_dimension_at_most_one(module_id):
        try:
            entry = pdid_map.get(int(module_id), {})
            value = int(entry.get("id", -1))
            return 0 <= value <= 1
        except Exception:
            return False

    torsion_pair_split_by_key = {
        (normalized_class_key(item.get("T", [])), normalized_class_key(item.get("F", []))): bool(item.get("split"))
        for item in torsion_pair_data
    }
    for item in tilting_data:
        t_key = normalized_class_key(item.get("T", []))
        f_key = normalized_class_key(item.get("F", []))
        splitting = all(injective_dimension_at_most_one(mid) for mid in f_key)
        separating = torsion_pair_split_by_key.get((t_key, f_key), set(t_key).union(f_key) == torsion_module_ids)
        item["splitting"] = splitting
        item["separating"] = separating
        item["tags"] = ["splitting" if splitting else "non-splitting", "separating" if separating else "non-separating"]
        item["tagText"] = " | ".join(item["tags"])

    cotorsion_pair_data = []
    cotorsion_section = ""
    cotorsion_match = re.search(r"# --- CotorsionPairTable --- #[\s\S]*?(?=PDID :=|$)", content)
    if cotorsion_match:
        cotorsion_section = cotorsion_match.group(0)
    for m in re.finditer(r"^L\s*:=\s*(0|\[[^\]]*\])\s*\|\s*R\s*:=\s*(0|\[[^\]]*\])\s*\|\s*Hereditary\s*:\s*=\s*(true|false)", cotorsion_section, flags=re.M | re.S | re.I):
        cotorsion_pair_data.append({
            "L": parse_class_expr(m.group(1)),
            "R": parse_class_expr(m.group(2)),
            "hereditary": m.group(3).lower() == "true",
        })

    support_tau_data = []
    support_tau_match = re.search(r"# --- SupportTauTiltingTable --- #[\s\S]*?(?=# --- AlmostSupportTauTiltingTable --- #|PDID :=|$)", content)
    support_tau_section = support_tau_match.group(0) if support_tau_match else ""
    for m in re.finditer(r"^P\s*:=\s*(0|\[[^\]]*\])\s*\|\s*M\s*:=\s*(0|\[[^\]]*\])", support_tau_section, flags=re.M | re.S):
        support_tau_data.append({"P": parse_class_expr(m.group(1)), "M": parse_class_expr(m.group(2))})

    almost_support_tau_data = []
    almost_support_tau_match = re.search(r"# --- AlmostSupportTauTiltingTable --- #[\s\S]*?(?=PDID :=|$)", content)
    almost_support_tau_section = almost_support_tau_match.group(0) if almost_support_tau_match else ""
    for m in re.finditer(r"^P\s*:=\s*(0|\[[^\]]*\])\s*\|\s*M\s*:=\s*(0|\[[^\]]*\])", almost_support_tau_section, flags=re.M | re.S):
        almost_support_tau_data.append({"P": parse_class_expr(m.group(1)), "M": parse_class_expr(m.group(2))})

    def display_class(values):
        return "0" if not values else ",".join(str(v) for v in values)

    for item in tilting_data:
        item["labelText"] = f"L=[{display_class(item.get('L', []))}] | F=[{display_class(item.get('F', []))}] | T=[{display_class(item.get('T', []))}] | {item.get('tagText', '')}"
    for item in torsion_pair_data:
        item["labelText"] = f"T=[{display_class(item.get('T', []))}] | F=[{display_class(item.get('F', []))}] | {item.get('tagText', '')}"
    for item in cotorsion_pair_data:
        item["labelText"] = f"L=[{display_class(item.get('L', []))}] | R=[{display_class(item.get('R', []))}] | {'hereditary' if item.get('hereditary') else 'non-hereditary'}"
    for item in support_tau_data:
        item["labelText"] = f"P=[{display_class(item.get('P', []))}] | M=[{display_class(item.get('M', []))}]"
    for item in almost_support_tau_data:
        item["labelText"] = f"P=[{display_class(item.get('P', []))}] | M=[{display_class(item.get('M', []))}]"

    torsion_pair_buckets = {}
    for tilting_filter in ["all", "tilting", "non-tilting"]:
        for split_filter in ["all", "split", "non-split"]:
            key = f"{tilting_filter}|{split_filter}"
            bucket = []
            for idx, item in enumerate(torsion_pair_data):
                tilting_ok = tilting_filter == "all" or (tilting_filter == "tilting" and item.get("tilting")) or (tilting_filter == "non-tilting" and not item.get("tilting"))
                split_ok = split_filter == "all" or (split_filter == "split" and item.get("split")) or (split_filter == "non-split" and not item.get("split"))
                if tilting_ok and split_ok:
                    bucket.append(idx)
            torsion_pair_buckets[key] = bucket

    globals()["torsion_pair_data"] = torsion_pair_data
    globals()["torsion_pair_buckets"] = torsion_pair_buckets
    globals()["cotorsion_pair_data"] = cotorsion_pair_data
    globals()["support_tau_tilting_data"] = support_tau_data
    globals()["almost_support_tau_tilting_data"] = almost_support_tau_data

    return proj_ids, inj_ids, tors_ids, refl_ids, dot_content, syz_content, translation_content, q_content, rel_content, hom_content, ext_content, tilting_data, quiver_structure, pdid_map

# ===== Step3.ipynb cell 3 =====
def calculate_initial_layout(golden_edges, x_spacing=250, y_spacing=150):
    """
    Return empty layout to let the physics engine place nodes by default.
    When positions are provided, those nodes will be fixed in place.
    """
    return {}

# ===== Step3.ipynb cell 4 =====
def create_and_save_quiver_html(quiver_filepath, output_filename):
    proj_ids, inj_ids, tors_ids, refl_ids, dot_content, syz_content, trans_content, q_dot_content, rel_content, hom_content, ext_content, tilting_data, quiver_structure, pdid_map = parse_quiver_data(quiver_filepath)
    if dot_content is None:
        print(f"Error: quiver file not found or contains no DOT graph: {quiver_filepath}")
        return

    nodes_data, edges_data = parse_dot_string(dot_content)
    syz_edges = []
    syz_nodes_data = None
    if syz_content:
        syz_nodes_data, syz_edges = parse_dot_string(syz_content)
    cosyz_edges = []
    cosyz_content = globals().get("cosyzygy_content")
    if cosyz_content:
        _, cosyz_edges = parse_dot_string(cosyz_content)
    radical_edges = []
    radical_content = globals().get("radical_content")
    if radical_content:
        _, radical_edges = parse_dot_string(radical_content)
    coradical_edges = []
    coradical_content = globals().get("coradical_content")
    if coradical_content:
        _, coradical_edges = parse_dot_string(coradical_content)

    golden_edges = []
    if trans_content:
        _, trans_edges_data = parse_dot_string(trans_content)
        # trans_edges_data usually contains tuples (u, v, label). We just want (u, v).
        golden_edges = [(e[0], e[1]) for e in trans_edges_data]
    
    # Prefer dimension vectors from SyzygySummand labels when available
    dim_map = {}
    if syz_nodes_data:
        for nid, attrs in syz_nodes_data.items():
            lbl = attrs.get('label', '')
            try:
                val = json.loads(lbl)
            except Exception:
                val = None
            if isinstance(val, list):
                dim_map[nid] = val
    
    q_nodes = []
    q_edges = []
    if q_dot_content:
        q_nodes_data, q_edges_data = parse_dot_string_with_edge_labels(q_dot_content)
        # Map "v1" → id=1, "v2" → id=2 etc. so edges (which use numeric IDs) connect correctly
        # Label uses the numeric part only: "v1" → "1"
        for nid, attrs in q_nodes_data.items():
            numeric_id = nid
            if isinstance(nid, str):
                m = re.match(r'^[a-zA-Z]+(\d+)$', nid)
                if m:
                    numeric_id = int(m.group(1))
            q_nodes.append({"id": numeric_id, "label": str(numeric_id)})
        q_edges = q_edges_data
        if len(q_nodes) == 0 and len(q_edges) > 0:
            node_ids = sorted({e[0] for e in q_edges} | {e[1] for e in q_edges})
            q_nodes = [{"id": nid, "label": str(nid)} for nid in node_ids]
    hom_edges = []
    if hom_content:
        _, hom_edges = parse_dot_string_with_edge_labels(hom_content)
    ext_edges = []
    if ext_content:
        _, ext_edges = parse_dot_string_with_edge_labels(ext_content)

# ===== Step3.ipynb cell 5 =====
def create_and_save_quiver_html(quiver_filepath, output_filename):
    proj_ids, inj_ids, tors_ids, refl_ids, dot_content, syz_content, trans_content, q_dot_content, rel_content, hom_content, ext_content, tilting_data, quiver_structure, pdid_map = parse_quiver_data(quiver_filepath)
    if dot_content is None:
        print(f"Error: quiver file not found or contains no DOT graph: {quiver_filepath}")
        return

    nodes_data, edges_data = parse_dot_string(dot_content)
    syz_edges = []
    syz_nodes_data = None
    if syz_content:
        syz_nodes_data, syz_edges = parse_dot_string(syz_content)
    cosyz_edges = []
    cosyz_content = globals().get("cosyzygy_content")
    if cosyz_content:
        _, cosyz_edges = parse_dot_string(cosyz_content)
    radical_edges = []
    radical_content = globals().get("radical_content")
    if radical_content:
        _, radical_edges = parse_dot_string(radical_content)
    coradical_edges = []
    coradical_content = globals().get("coradical_content")
    if coradical_content:
        _, coradical_edges = parse_dot_string(coradical_content)

    golden_edges = []
    if trans_content:
        _, trans_edges_data = parse_dot_string(trans_content)
        # trans_edges_data usually contains tuples (u, v, label). We just want (u, v).
        golden_edges = [(e[0], e[1]) for e in trans_edges_data]
    
    # Prefer dimension vectors from SyzygySummand labels when available
    dim_map = {}
    if syz_nodes_data:
        for nid, attrs in syz_nodes_data.items():
            lbl = attrs.get('label', '')
            try:
                val = json.loads(lbl)
            except Exception:
                val = None
            if isinstance(val, list):
                dim_map[nid] = val
    
    q_nodes = []
    q_edges = []
    if q_dot_content:
        q_nodes_data, q_edges_data = parse_dot_string_with_edge_labels(q_dot_content)
        # Map "v1" -> id=1, "v2" -> id=2 etc. so edges (which use numeric IDs) connect correctly
        # Label uses the numeric part only: "v1" -> "1"
        for nid, attrs in q_nodes_data.items():
            numeric_id = nid
            if isinstance(nid, str):
                m = re.match(r'^[a-zA-Z]+(\d+)$', nid)
                if m:
                    numeric_id = int(m.group(1))
            q_nodes.append({"id": numeric_id, "label": str(numeric_id)})
        q_edges = q_edges_data
        if len(q_nodes) == 0 and len(q_edges) > 0:
            node_ids = sorted({e[0] for e in q_edges} | {e[1] for e in q_edges})
            q_nodes = [{"id": nid, "label": str(nid)} for nid in node_ids]
    hom_edges = []
    if hom_content:
        _, hom_edges = parse_dot_string_with_edge_labels(hom_content)
    ext_edges = []
    if ext_content:
        _, ext_edges = parse_dot_string_with_edge_labels(ext_content)

    for node_id, attrs in nodes_data.items():
        if node_id in dim_map:
            nodes_data[node_id]['dim'] = dim_map[node_id]
            continue
        try:
            nodes_data[node_id]['dim'] = json.loads(attrs['label'])
        except (json.JSONDecodeError, TypeError) as e:
            # Fallback for "pd=0, id=3"
            lbl = attrs.get('label', '')
            m = re.search(r'pd=(-?\d+|∞),\s*id=(-?\d+|∞)', lbl)
            if m:
                nodes_data[node_id]['dim'] = {'pd': m.group(1), 'id': m.group(2)}
            else:
                print(f"Invalid JSON label for node {node_id}: {attrs.get('label')}\nReason: {e}")
                return
            
    # Draw with the default engine, then add grid snapping and straight-edge behavior through JS.
    net = Network(height='calc(100vh - 16px)', width='100vw', directed=True, notebook=False)
    # Note: find_golden_edges removed in favor of trans_content parsing above
    # golden_edges is already set
    node_positions = calculate_initial_layout(golden_edges)

    # Filter out zero-dimension nodes (the zero module)
    def is_zero_dim(dim):
        if isinstance(dim, list):
            return all(v == 0 for v in dim)
        return False

    zero_node_ids = {nid for nid, attrs in nodes_data.items() if is_zero_dim(attrs.get('dim'))}
    if zero_node_ids:
        print(f"ℹ️ Excluding zero-dimension nodes: {sorted(zero_node_ids)}")

    proj_and_inj = proj_ids.intersection(inj_ids)
    for node_id, attrs in nodes_data.items():
        if node_id in zero_node_ids:
            continue
        border_color = 'gray'
        if node_id in proj_and_inj:
            border_color = 'purple'
        elif node_id in proj_ids:
            border_color = 'blue'
        elif node_id in inj_ids:
            border_color = 'red'
        
        pos_args = {}
        if node_id in node_positions:
            pos_args = {'x': node_positions[node_id]['x'], 'y': node_positions[node_id]['y'], 'physics': False}
        label_display = format_dim_vector(nodes_data[node_id]['dim'], quiver_structure)
        net.add_node(node_id, label=label_display, shape='ellipse',
                     color={'border': border_color, 'background': 'white', 'highlight': {'border': border_color, 'background': '#D2E5FF'}},
                     font={'color': 'black', 'face': 'monospace', 'size': 14, 'bold': True, 'vadjust': 0, 'align': 'center'}, title=str(node_id),
                     borderWidth=3, borderWidthSelected=5,
                     **pos_args)

    # Filter out edges that reference zero-dimension nodes, then collapse exact duplicates for display.
    # GAP may return multiple irreducible maps with the same source/target; drawing them as identical
    # overlapping vis edges makes the HTML look like accidental duplicates.  We keep the multiplicity
    # as an edge label/title instead.
    filtered_edges = [e for e in edges_data if e[0] not in zero_node_ids and e[1] not in zero_node_ids]
    edge_counts = {}
    for e in filtered_edges:
        key = tuple(e)
        edge_counts[key] = edge_counts.get(key, 0) + 1
    collapsed_edges = sorted(edge_counts.items(), key=lambda item: (item[0][0], item[0][1], item[0][2] if len(item[0]) > 2 else ""))
    if any(count > 1 for _, count in collapsed_edges):
        dup_summary = [((key[0], key[1]), count) for key, count in collapsed_edges if count > 1]
        print(f"ℹ️ Collapsing duplicate AR edges for display: {dup_summary}")
    for key, count in collapsed_edges:
        u = key[0]
        v = key[1]
        base_label = key[2] if len(key) > 2 else ""
        display_label = base_label or ""
        if count > 1:
            display_label = f"{display_label} ×{count}" if display_label else f"×{count}"
        edge_kwargs = {}
        if display_label:
            edge_kwargs["label"] = display_label
            edge_kwargs["font"] = {"align": "top", "size": 12, "color": "#444"}
        if count > 1:
            edge_kwargs["title"] = f"Multiplicity {count}"
        net.add_edge(u, v, **edge_kwargs)
    # Also filter golden/syz edges referencing zero nodes
    golden_edges = [(u, v) for u, v in golden_edges if u not in zero_node_ids and v not in zero_node_ids]
    syz_edges = [e for e in syz_edges if e[0] not in zero_node_ids and e[1] not in zero_node_ids]
    # NOTE: We DO NOT add golden edges natively here.
    # We will inject them via JS exactly like Syzygy edges.
    # This ensures they appear/disappear cleanly on toggle.

    html_content = net.generate_html(notebook=False)
    viewport_css = """
        <style type="text/css">
          html, body {
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
            overflow: hidden;
          }
          body > .card {
            width: 100vw !important;
            height: 100vh !important;
            border: 0 !important;
          }
          #mynetwork {
            width: 100vw !important;
            height: 100vh !important;
            border: 0 !important;
            float: none !important;
            padding: 0 !important;
            box-sizing: border-box !important;
          }
        </style>
    """
    html_content = html_content.replace('</head>', viewport_css + '</head>')
    
    golden_edges_js_string = json.dumps(golden_edges)
    tors_ids_js = json.dumps(sorted(list(tors_ids)))
    refl_ids_js = json.dumps(sorted(list(refl_ids)))
    gp_ids_js = json.dumps(sorted(list(globals().get("gorenstein_projective_ids", set()))))
    gi_ids_js = json.dumps(sorted(list(globals().get("gorenstein_injective_ids", set()))))
    zero_ids_js = json.dumps(sorted(list(zero_node_ids)))
    syz_edges_js = json.dumps(syz_edges)
    cosyz_edges_js = json.dumps(cosyz_edges)
    radical_edges_js = json.dumps(radical_edges)
    coradical_edges_js = json.dumps(coradical_edges)
    q_nodes_js = json.dumps(q_nodes)
    q_edges_js = json.dumps(q_edges)
    q_rel_js = json.dumps(rel_content or "")
    module_data_gap_js = json.dumps(globals().get("module_data_gap", ""))
    hom_edges_js = json.dumps(hom_edges)
    ext_edges_js = json.dumps(ext_edges)
    tilting_js = json.dumps(tilting_data or [])
    torsion_pairs_js = json.dumps(globals().get("torsion_pair_data", []))
    torsion_pair_buckets_js = json.dumps(globals().get("torsion_pair_buckets", {}))
    cotorsion_pairs_js = json.dumps(globals().get("cotorsion_pair_data", []))
    support_tau_js = json.dumps(globals().get("support_tau_tilting_data", []))
    almost_support_tau_js = json.dumps(globals().get("almost_support_tau_tilting_data", []))
    pdid_js = json.dumps(pdid_map or {})
    top_soc_js = json.dumps(globals().get("top_soc_map", {}))
    q_structure_js = json.dumps(quiver_structure or "")
    txt_path = Path(quiver_filepath).with_suffix('.txt')
    original_quiver_text = ""
    if txt_path.exists():
        original_quiver_text = txt_path.read_text(encoding='utf-8', errors='replace')
    original_quiver_text_js = json.dumps(original_quiver_text)
    original_quiver_filename_js = json.dumps(txt_path.name)

    # ------------------- JAVASCRIPT MODIFICATION START -------------------
    js_injection = """
    <script type="text/javascript">
      const gridSize = 100;
      const goldenEdges = {{GOLDEN_EDGES}};
      const torsionlessIds = {{TORS_IDS}};
      const reflexiveIds = {{REFL_IDS}};
      const gorensteinProjectiveIds = {{GP_IDS}};
      const gorensteinInjectiveIds = {{GI_IDS}};
      const zeroObjectIds = {{ZERO_OBJECT_IDS}};
      const syzygyEdges = {{SYZ_EDGES}};
      const cosyzygyEdges = {{COSYZ_EDGES}};
      const radicalEdges = {{RAD_EDGES}};
      const coradicalEdges = {{CORAD_EDGES}};
      const quiverNodes = {{Q_NODES}};
      const quiverEdges = {{Q_EDGES}};
      const quiverRel = {{Q_REL}};
      const indecomposableModuleDataGap = {{MODULE_DATA_GAP}};
      const homEdges = {{HOM_EDGES}};
      const extEdges = {{EXT_EDGES}};
      const tiltingData = {{TILTING_DATA}};
      const torsionPairData = {{TORSION_PAIR_DATA}};
      const torsionPairBuckets = {{TORSION_PAIR_BUCKETS}};
      const cotorsionPairData = {{COTORSION_PAIR_DATA}};
      const supportTauTiltingData = {{SUPPORT_TAU_TILTING_DATA}};
      const almostSupportTauTiltingData = {{ALMOST_SUPPORT_TAU_TILTING_DATA}};
      const pdidMap = {{PDID_MAP}};
      const topSocMap = {{TOP_SOC_MAP}};
      const quiverStructure = {{Q_STRUCTURE}};
      const originalQuiverText = {{ORIGINAL_QUIVER_TEXT}};
      const originalQuiverFilename = {{ORIGINAL_QUIVER_FILENAME}};
      const goldenEdgeSet = new Set(goldenEdges.map(e => `${e[0]}->${e[1]}`));
      var options = {
        "edges": {
          // Selection only thickens the edge and uses green highlighting.
          "selectionWidth": 2,
          "color": { "color": "#000000", "highlight": "#00aa00", "hover": "#00aa00", "inherit": true },
          // Keep all edges straight; keyboard controls can adjust curvature.
          "smooth": { "enabled": false }
        },
        "interaction": { "multiselect": true },
        "physics": { "enabled": true }
      };
      network.setOptions(options);

      // After physics stabilization, snap all nodes to grid and disable physics
      network.once('stabilizationIterationsDone', function() {
        const allNodeIds = network.body.data.nodes.getIds();
        allNodeIds.forEach(id => snapNode(id));
        network.setOptions({ physics: { enabled: false } });
        snapshot();
      });

      (function hideManipulationPanel() {
        const style = document.createElement('style');
        style.textContent = '.vis-manipulation { display: none !important; }';
        document.head.appendChild(style);
      })();

      (function addTiltingButtonStyles() {
        const style = document.createElement('style');
        style.textContent = `
          .tilting-btn-active {
            background: #ffe9a6 !important;
            font-weight: 700 !important;
          }
        `;
        document.head.appendChild(style);
      })();

      function renderInlineMath(element, tex) {
        if (!element) return;
        element.textContent = String(tex || '');
        element.classList.add('ar-math-label');
      }

      function parseEdgeColor(choice) {
        const c = (choice || 'black').toLowerCase().replace(/\\s+/g, '');
        if (c === 'gold' || c === 'g') {
          return { color: 'gold', width: 3 };
        }
        if (c === 'lightgold' || c === 'lg') {
          return { color: '#ffe9a6', width: 3 };
        }
        if (c === 'pink' || c === 'p') {
          return { color: 'pink', width: 2 };
        }
        if (c === 'lightgray' || c === 'lightgrey') {
          return { color: '#cccccc', width: 1 };
        }
        return { color: '#000000', width: 1 };
      }

      function assignMultiEdgeCurves(netObj) {
        if (!netObj) return;
        const allEdges = netObj.body.data.edges.get().filter(e => !e.hidden);
        const unordered = new Map();
        allEdges.forEach(e => {
          const a = Number(e.from);
          const b = Number(e.to);
          if (!Number.isFinite(a) || !Number.isFinite(b)) return;
          const key = Math.min(a, b) + '-' + Math.max(a, b);
          if (!unordered.has(key)) unordered.set(key, []);
          unordered.get(key).push(e);
        });
        const updates = [];
        unordered.forEach(edges => {
          const directed = new Map();
          edges.forEach(e => {
            const key = `${e.from}->${e.to}`;
            if (!directed.has(key)) directed.set(key, []);
            directed.get(key).push(e);
          });
          directed.forEach(group => group.sort((a, b) => String(a.id).localeCompare(String(b.id))));
          const hasReverse = directed.size > 1;
          directed.forEach(group => {
            const n = group.length;
            const step = 0.16;
            group.forEach((edge, i) => {
              let curvature;
              if (hasReverse) {
                curvature = 0.18 + (i - (n - 1) / 2) * step;
              } else {
                curvature = (i - (n - 1) / 2) * 0.2;
              }
              if (Math.abs(curvature) < 0.01) {
                updates.push({ id: edge.id, smooth: false });
              } else {
                updates.push({
                  id: edge.id,
                  smooth: {
                    enabled: true,
                    type: curvature > 0 ? 'curvedCW' : 'curvedCCW',
                    roundness: Math.abs(curvature)
                  }
                });
              }
            });
          });
        });
        if (updates.length) netObj.body.data.edges.update(updates);
      }

      function rememberEdgeCurve(edge) {
        if (!edge || edge.id === undefined || edge.id === null) return;
        if (edge.smooth && typeof edge.smooth === 'object') {
          edgeCurveMemory.set(String(edge.id), { ...edge.smooth });
        } else if (edge.smooth === false) {
          edgeCurveMemory.set(String(edge.id), false);
        }
      }

      function curveForEdgeId(id) {
        const key = String(id);
        return edgeCurveMemory.has(key) ? edgeCurveMemory.get(key) : false;
      }

      function rememberExistingEdgesByPrefix(prefix) {
        network.body.data.edges.get({
          filter: (edge) => edge.id && String(edge.id).startsWith(prefix)
        }).forEach(rememberEdgeCurve);
      }

      function addLabeledEdges(prefix, edges, color, width) {
        const toAdd = edges.map((e, i) => {
          const id = `${prefix}_${i}`;
          const label = (e[2] || '').toString();
          return {
            id: id,
            from: e[0],
            to: e[1],
            label: label && label !== '0' ? label : undefined,
            color: color,
            width: width,
            arrows: 'to',
            dashes: false,
            smooth: curveForEdgeId(id)
          };
        });
        network.body.data.edges.add(toAdd);
      }

      function addPlainEdges(prefix, edges, color, width) {
        const toAdd = edges.map((e, i) => {
          const id = `${prefix}_${i}`;
          return {
            id: id,
            from: e[0],
            to: e[1],
            color: color,
            width: width,
            arrows: 'to',
            dashes: false,
            smooth: curveForEdgeId(id)
          };
        });
        network.body.data.edges.add(toAdd);
      }

      function removeEdgesByPrefix(prefix) {
        const existingEdges = network.body.data.edges.get({
          filter: (edge) => edge.id && String(edge.id).startsWith(prefix)
        });
        existingEdges.forEach(rememberEdgeCurve);
        const existing = existingEdges.map(e => e.id);
        if (existing.length) network.body.data.edges.remove(existing);
      }

      // --- Buttons (right) ---
      let editMode = false;
      let miniQuiver = null;
      let miniContainer = null;
      let showLabels = false;
      let showBorders = true;
      let showPd = false;
      let showId = false;
      let showTop = false;
      let showSoc = false;
      let idLabelLayer = null;
      let pdLabelLayer = null;
      let idValueLabelLayer = null;
      let topLabelLayer = null;
      let socLabelLayer = null;
      const idLabelMap = new Map();
      const pdLabelMap = new Map();
      const idValueLabelMap = new Map();
      const topLabelMap = new Map();
      const socLabelMap = new Map();
      const floatingLabelOffsets = {
        pd: { x: 0, y: 0 },
        id: { x: 0, y: 0 },
        top: { x: 0, y: 0 },
        soc: { x: 0, y: 0 }
      };
      let floatingLabelDrag = null;
      const customTexLabels = new Map();
      let nodeLabelMode = 'dimension';
      const nodeLabelButtons = new Map();
      const edgeCurveMemory = new Map();
      const baseNodeStyles = new Map();
      let tiltingHighlighted = new Set();
      let calculatorHighlighted = new Set();
      function toBaseStyle(n) {
        return {
          id: n.id,
          label: n.label,
          title: n.title,
          color: n.color,
          shape: n.shape || 'ellipse',
          borderWidth: n.borderWidth,
          borderWidthSelected: n.borderWidthSelected,
          shapeProperties: n.shapeProperties,
          font: n.font,
          shadow: n.shadow || { enabled: false }
        };
      }
      function normalizeId(id) {
        const n = Number(id);
        return Number.isFinite(n) ? n : null;
      }
      function getExistingNode(id) {
        const n = normalizeId(id);
        if (n === null) return null;
        return network.body.data.nodes.get(n);
      }
      (function cacheBaseNodeStyles() {
        network.body.data.nodes.get().forEach(n => {
          baseNodeStyles.set(n.id, toBaseStyle(n));
        });
      })();
      (function addRightButtons() {
        ['arControlPanel','arTopMenu','arFolderPanel','arListDrawer','calculatorPanel','arTexExportModal','arDisplayCodeModal','arColorLegend','arQuiverTikzModal','quiverMiniContainer'].forEach(id => {
          const el = document.getElementById(id);
          if (el && el.parentNode) el.parentNode.removeChild(el);
        });
        const container = document.createElement('div');
        container.id = 'arControlPanel';
        container.style.position = 'absolute';
        container.style.top = '10px';
        container.style.right = '10px';
        container.style.zIndex = '999';
        container.style.display = 'flex';
        container.style.flexDirection = 'column';
        container.style.gap = '6px';
        container.innerHTML = `
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px;">
            <button id="torsBtn" style="padding:4px 8px;">Torsionless (${torsionlessIds.length})</button>
            <button id="reflBtn" style="padding:4px 8px;">Reflexive (${reflexiveIds.length})</button>
            <button id="gpBtn" style="padding:4px 8px;">GProj (${gorensteinProjectiveIds.length})</button>
            <button id="giBtn" style="padding:4px 8px;">GInj (${gorensteinInjectiveIds.length})</button>
          </div>
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:4px;">
            <label style="font-size:12px; background: rgba(255,255,255,0.8); padding:4px 8px; border-radius:4px;">
              <input id="syzToggle" type="checkbox" /> Syzygy
            </label>
            <label style="font-size:12px; background: rgba(255,255,255,0.8); padding:4px 8px; border-radius:4px;">
              <input id="cosyzToggle" type="checkbox" /> Cosyzygy
            </label>
            <label style="font-size:12px; background: rgba(255,255,255,0.8); padding:4px 8px; border-radius:4px;">
              <input id="radToggle" type="checkbox" /> Radical
            </label>
            <label style="font-size:12px; background: rgba(255,255,255,0.8); padding:4px 8px; border-radius:4px;">
              <input id="coradToggle" type="checkbox" /> Coradical
            </label>
            <label style="font-size:12px; background: rgba(255,255,255,0.8); padding:4px 8px; border-radius:4px;">
              <input id="homToggle" type="checkbox" /> HomDim
            </label>
            <label style="font-size:12px; background: rgba(255,255,255,0.8); padding:4px 8px; border-radius:4px;">
              <input id="extToggle" type="checkbox" /> ExtDim
            </label>
            <label style="font-size:12px; background: rgba(255,255,255,0.8); padding:4px 8px; border-radius:4px;">
              <input id="irrToggle" type="checkbox" checked /> Irr
            </label>
            <label style="font-size:12px; background: rgba(255,255,255,0.8); padding:4px 8px; border-radius:4px;">
              <input id="trToggle" type="checkbox" checked /> tau
            </label>
            <label style="font-size:12px; background: rgba(255,255,255,0.8); padding:4px 8px; border-radius:4px;">
              <input id="quiverToggle" type="checkbox" /> Quiver
            </label>
            <label style="font-size:12px; background: rgba(255,255,255,0.8); padding:4px 8px; border-radius:4px;">
              <input id="tiltingToggle" type="checkbox" /> Tilting
            </label>
            <label style="font-size:12px; background: rgba(255,255,255,0.8); padding:4px 8px; border-radius:4px;">
              <input id="torsionPairToggle" type="checkbox" /> TorsionCls
            </label>
            <label style="font-size:12px; background: rgba(255,255,255,0.8); padding:4px 8px; border-radius:4px;">
              <input id="cotorsionPairToggle" type="checkbox" /> CotorsionCls
            </label>
            <label style="font-size:12px; background: rgba(255,255,255,0.8); padding:4px 8px; border-radius:4px;">
              <input id="supportTauToggle" type="checkbox" /> sTauTilt
            </label>
            <label style="font-size:12px; background: rgba(255,255,255,0.8); padding:4px 8px; border-radius:4px;">
              <input id="almostSupportTauToggle" type="checkbox" /> almost sTauTilt
            </label>
            <label style="font-size:12px; background: rgba(255,255,255,0.8); padding:4px 8px; border-radius:4px;">
              <input id="pdToggle" type="checkbox" /> PD
            </label>
            <label style="font-size:12px; background: rgba(255,255,255,0.8); padding:4px 8px; border-radius:4px;">
              <input id="idToggle" type="checkbox" /> ID
            </label>
            <label style="font-size:12px; background: rgba(255,255,255,0.8); padding:4px 8px; border-radius:4px;">
              <input id="topToggle" type="checkbox" /> Top
            </label>
            <label style="font-size:12px; background: rgba(255,255,255,0.8); padding:4px 8px; border-radius:4px;">
              <input id="socToggle" type="checkbox" /> Soc
            </label>
            <label style="font-size:12px; background: rgba(255,255,255,0.8); padding:4px 8px; border-radius:4px;">
              <input id="borderToggle" type="checkbox" checked /> Border
            </label>
          </div>
          <div id="tiltingList" style="display:none; background: rgba(255,255,255,0.9); padding:6px; border-radius:6px; overflow:auto; font-size:12px;"></div>
          <div id="torsionPairList" style="display:none; background: rgba(255,255,255,0.9); padding:6px; border-radius:6px; overflow:auto; font-size:12px;"></div>
          <div id="cotorsionPairList" style="display:none; background: rgba(255,255,255,0.9); padding:6px; border-radius:6px; overflow:auto; font-size:12px;"></div>
          <div id="supportTauList" style="display:none; background: rgba(255,255,255,0.9); padding:6px; border-radius:6px; overflow:auto; font-size:12px;"></div>
          <div id="almostSupportTauList" style="display:none; background: rgba(255,255,255,0.9); padding:6px; border-radius:6px; overflow:auto; font-size:12px;"></div>
        `;
        document.body.appendChild(container);
        container.style.display = 'none';
        let menuBar = null;
        let drawer = null;
        let drawerTitle = null;
        let drawerBody = null;
        let drawerListId = null;
        let drawerToggleId = null;
        let uiVisible = true;
        let drawerVisibleBeforeHide = false;
        const activeModuleClasses = new Map();

        function activeModuleIds() {
          const ids = new Set();
          activeModuleClasses.forEach(entry => {
            (entry.ids || []).forEach(id => ids.add(Number(id)));
          });
          return ids;
        }

        function redrawActiveModuleClasses() {
          const allNodes = network.body.data.nodes.get();
          allNodes.forEach(n => restoreNodeBase(n.id));
          activeModuleClasses.forEach(entry => {
            const idSet = new Set((entry.ids || []).map(Number));
            const updates = network.body.data.nodes.get().filter(n => idSet.has(Number(n.id))).map(n => ({
              id: n.id,
              color: { border: entry.color, background: '#fff7cc', highlight: { border: entry.color, background: '#ffe680' } },
              borderWidth: showBorders ? 5 : 0,
              borderWidthSelected: showBorders ? 6 : 0
            }));
            if (updates.length) network.body.data.nodes.update(updates);
          });
          const ids = Array.from(activeModuleIds());
          if (ids.length) network.selectNodes(ids);
          else network.unselectAll();
        }

        function toggleModuleClass(btnId, ids, color) {
          const btn = document.getElementById(btnId);
          const idsArray = (ids || []).map(Number).filter(x => !Number.isNaN(x));
          if (!idsArray.length) {
            alert('Not found');
            return false;
          }
          if (activeModuleClasses.has(btnId)) {
            activeModuleClasses.delete(btnId);
            if (btn) btn.classList.remove('ar-control-active');
          } else {
            activeModuleClasses.set(btnId, { ids: idsArray, color: color });
            if (btn) btn.classList.add('ar-control-active');
          }
          redrawActiveModuleClasses();
          return true;
        }
        document.getElementById('torsBtn').addEventListener('click', () => toggleModuleClass('torsBtn', torsionlessIds, '#0ea5e9'));
        document.getElementById('reflBtn').addEventListener('click', () => toggleModuleClass('reflBtn', reflexiveIds, '#8b5cf6'));
        document.getElementById('gpBtn').addEventListener('click', () => toggleModuleClass('gpBtn', gorensteinProjectiveIds, '#16a34a'));
        document.getElementById('giBtn').addEventListener('click', () => toggleModuleClass('giBtn', gorensteinInjectiveIds, '#dc2626'));
        document.getElementById('syzToggle').addEventListener('change', (e) => {
          const checked = e.target.checked;
          const existing = network.body.data.edges.get({
            filter: (edge) => edge.id && String(edge.id).startsWith('syz_')
          }).map(e => e.id);
          if (checked) {
            const toAdd = syzygyEdges.map((e, i) => ({
              id: `syz_${i}` ,
              from: e[0],
              to: e[1],
              color: 'pink',
              width: 2,
              arrows: 'to',
              dashes: false,
              smooth: curveForEdgeId(`syz_${i}`)
            }));
            network.body.data.edges.add(toAdd);
          } else {
            rememberExistingEdgesByPrefix('syz_');
            if (existing.length) network.body.data.edges.remove(existing);
          }
        });
        document.getElementById('cosyzToggle').addEventListener('change', (e) => {
          const checked = e.target.checked;
          const existing = network.body.data.edges.get({
            filter: (edge) => edge.id && String(edge.id).startsWith('cosyz_')
          }).map(e => e.id);
          if (checked) {
            const toAdd = cosyzygyEdges.map((e, i) => ({
              id: `cosyz_${i}`,
              from: e[0],
              to: e[1],
              color: '#22c55e',
              width: 2,
              arrows: 'to',
              dashes: false,
              smooth: curveForEdgeId(`cosyz_${i}`)
            }));
            network.body.data.edges.add(toAdd);
          } else {
            rememberExistingEdgesByPrefix('cosyz_');
            if (existing.length) network.body.data.edges.remove(existing);
          }
        });
        document.getElementById('radToggle').addEventListener('change', (e) => {
          const checked = e.target.checked;
          if (checked) addPlainEdges('rad', radicalEdges, '#0ea5e9', 2);
          else removeEdgesByPrefix('rad');
        });
        document.getElementById('coradToggle').addEventListener('change', (e) => {
          const checked = e.target.checked;
          if (checked) addPlainEdges('corad', coradicalEdges, '#a855f7', 2);
          else removeEdgesByPrefix('corad');
        });
        document.getElementById('homToggle').addEventListener('change', (e) => {
          const checked = e.target.checked;
          if (checked) {
            addLabeledEdges('hom', homEdges, '#8b5a2b', 1);
          } else {
            removeEdgesByPrefix('hom');
          }
        });
        document.getElementById('extToggle').addEventListener('change', (e) => {
          const checked = e.target.checked;
          if (checked) {
            addLabeledEdges('ext', extEdges, 'red', 1);
          } else {
            removeEdgesByPrefix('ext');
          }
        });
        document.getElementById('irrToggle').addEventListener('change', (e) => {
          const checked = e.target.checked;
          toggleEdges((edge) => isIrreducibleEdge(edge), checked);
        });
        document.getElementById('trToggle').addEventListener('change', (e) => {
          const checked = e.target.checked;
          if (checked) {
            const toAdd = goldenEdges.map((e, i) => ({
              id: `tr_${i}`,
              from: e[0],
              to: e[1],
              color: 'gold',
              width: 3,
              arrows: 'to',
              dashes: false,
              smooth: curveForEdgeId(`tr_${i}`)
            }));
            network.body.data.edges.add(toAdd);
          } else {
            removeEdgesByPrefix('tr');
          }
        });
        // Initialize tau edges manually on load since checked=true
        if (document.getElementById('trToggle').checked && goldenEdges.length > 0) {
           const toAdd = goldenEdges.map((e, i) => ({
              id: `tr_${i}`,
              from: e[0],
              to: e[1],
              color: 'gold',
              width: 3,
              arrows: 'to',
              dashes: false,
              smooth: curveForEdgeId(`tr_${i}`)
           }));
           network.body.data.edges.add(toAdd);
        }
        
        document.getElementById('quiverToggle').addEventListener('change', (e) => {
          toggleMiniQuiver(e.target.checked);
        });
        document.getElementById('tiltingToggle').addEventListener('change', (e) => {
          const checked = e.target.checked;
          const listEl = document.getElementById('tiltingList');
          if (!checked) {
            listEl.style.display = 'none';
            resetTiltingStyles();
            clearActiveTilting();
            return;
          }
          if (!tiltingData || tiltingData.length === 0) {
            alert('No tilting data found.');
            listEl.style.display = 'none';
            return;
          }
          listEl.style.display = 'block';
          renderTiltingList();
        });
        function clearPairListHighlight() {
          const hadPairHighlight = pairHighlighted && pairHighlighted.size > 0;
          resetPairStyles();
          if (hadPairHighlight) {
            resetTiltingStyles();
            clearActiveTilting();
          }
        }
        document.getElementById('torsionPairToggle').addEventListener('change', (e) => {
          const el = document.getElementById('torsionPairList');
          if (!el) return;
          el.style.display = e.target.checked ? 'block' : 'none';
          if (e.target.checked) {
            renderTorsionClassListLikeCotorsion('torsionPairList');
          } else {
            clearPairListHighlight();
          }
        });
        document.getElementById('cotorsionPairToggle').addEventListener('change', (e) => {
          const el = document.getElementById('cotorsionPairList');
          if (!el) return;
          el.style.display = e.target.checked ? 'block' : 'none';
          if (e.target.checked) {
            renderPairList('cotorsionPairList', cotorsionPairData, 'L', 'R', 'Cotorsion pairs', item => `<td style="border:1px solid #ddd; padding:3px;">${item.hereditary ? 'hereditary' : 'non-hereditary'}</td>`, { kind: 'cotorsion' });
          } else {
            clearPairListHighlight();
          }
        });
        document.getElementById('supportTauToggle').addEventListener('change', (e) => {
          const el = document.getElementById('supportTauList');
          if (!el) return;
          el.style.display = e.target.checked ? 'block' : 'none';
          if (e.target.checked) {
            renderSupportTauList('supportTauList', supportTauTiltingData, 'Support tau-tilting modules');
          } else {
            clearPairListHighlight();
          }
        });
        document.getElementById('almostSupportTauToggle').addEventListener('change', (e) => {
          const el = document.getElementById('almostSupportTauList');
          if (!el) return;
          el.style.display = e.target.checked ? 'block' : 'none';
          if (e.target.checked) {
            renderSupportTauList('almostSupportTauList', almostSupportTauTiltingData, 'Almost support tau-tilting modules');
          } else {
            clearPairListHighlight();
          }
        });
        document.getElementById('pdToggle').addEventListener('change', (e) => {
          togglePdLabels(e.target.checked);
        });
        document.getElementById('idToggle').addEventListener('change', (e) => {
          toggleIdValueLabels(e.target.checked);
        });
        document.getElementById('topToggle').addEventListener('change', (e) => {
          toggleTopLabels(e.target.checked);
        });
        document.getElementById('socToggle').addEventListener('change', (e) => {
          toggleSocLabels(e.target.checked);
        });
        document.getElementById('borderToggle').addEventListener('change', (e) => {
          showBorders = e.target.checked;
          toggleNodeBorders(showBorders);
        });

        function dispatchChange(el) {
          if (!el) return;
          el.dispatchEvent(new Event('change', { bubbles: true }));
        }

        function toggleCheckbox(id) {
          const el = document.getElementById(id);
          if (!el) return;
          el.checked = !el.checked;
          dispatchChange(el);
        }

        function setCheckbox(id, checked) {
          const el = document.getElementById(id);
          if (!el) return;
          if (el.checked !== checked) {
            el.checked = checked;
            dispatchChange(el);
          } else if (checked) {
            dispatchChange(el);
          }
        }

        function clickControl(id) {
          const el = document.getElementById(id);
          if (el) el.click();
        }

        function clearButtonListActive(containerId) {
          const el = document.getElementById(containerId);
          if (!el) return;
          el.querySelectorAll('button[data-row]').forEach(btn => btn.classList.remove('tilting-btn-active'));
        }

        function clearListMenuActive() {
          if (!folderPanel) return;
          folderPanel.querySelectorAll('button[data-list]').forEach(btn => btn.classList.remove('ar-control-active'));
        }

        function closeListDrawer(clearColors) {
          if (drawer) drawer.style.display = 'none';
          if (drawerToggleId) setCheckbox(drawerToggleId, false);
          if (drawerListId) clearButtonListActive(drawerListId);
          clearListMenuActive();
          if (clearColors) clearListColoring();
          drawerListId = null;
          drawerToggleId = null;
        }

        function drawerSwatch(color, label) {
          return '<span title="' + label + '" style="display:inline-block;width:0.85em;height:0.85em;vertical-align:-0.08em;margin:0 0.2em;border:1px solid #64748b;border-radius:2px;background:' + color + ';"></span>';
        }

        function drawerTitleHtml(listId, title) {
          const meta = {
            torsionPairList: [['T', '#ffe1c7'], ['F', '#d9f2d9']],
            cotorsionPairList: [['left', '#93c5fd'], ['right', '#fca5a5']],
            tiltingList: [['L', '#b5b5b5'], ['T', '#ffe1c7'], ['F', '#d9f2d9']],
            supportTauList: [['P', '#dbeafe'], ['M', '#b5b5b5']],
            almostSupportTauList: [['P', '#dbeafe'], ['M', '#b5b5b5']]
          };
          const items = meta[listId];
          if (!items) return title;
          return title + ' <span style="font-weight:400;color:#475569;font-size:11px;">(' + items.map(item => item[0] + ' ' + drawerSwatch(item[1], item[0])).join(', ') + ')</span>';
        }

        function showListInDrawer(toggleId, listId, title) {
          ensureDrawer();
          if (drawer && drawer.style.display === 'block' && drawerToggleId === toggleId && drawerListId === listId) {
            closeListDrawer(true);
            return false;
          }
          if (drawerListId && drawerListId !== listId) clearButtonListActive(drawerListId);
          if (drawerToggleId && drawerToggleId !== toggleId) setCheckbox(drawerToggleId, false);
          clearListMenuActive();
          setCheckbox(toggleId, true);
          const listEl = document.getElementById(listId);
          if (!listEl) return false;
          while (drawerBody.firstChild) {
            container.appendChild(drawerBody.firstChild);
          }
          drawerToggleId = toggleId;
          drawerListId = listId;
          drawerTitle.innerHTML = drawerTitleHtml(listId, title);
          drawerBody.appendChild(listEl);
          listEl.style.display = 'block';
          drawer.style.display = 'block';
          if (listId === 'tiltingList' && typeof renderTiltingList === 'function') {
            renderTiltingList();
          }
          if (listId === 'torsionPairList' && typeof renderTorsionClassListLikeCotorsion === 'function') {
            renderTorsionClassListLikeCotorsion(listId);
          }
          if (listId === 'cotorsionPairList' && typeof renderPairList === 'function') {
            renderPairList('cotorsionPairList', cotorsionPairData, 'L', 'R', 'Cotorsion pairs', item => `<td style="border:1px solid #ddd; padding:3px;">${item.hereditary ? 'hereditary' : 'non-hereditary'}</td>`, { kind: 'cotorsion' });
          }
          if (listId === 'supportTauList' && typeof renderSupportTauList === 'function') {
            renderSupportTauList('supportTauList', supportTauTiltingData, 'Support tau-tilting modules');
          }
          if (listId === 'almostSupportTauList' && typeof renderSupportTauList === 'function') {
            renderSupportTauList('almostSupportTauList', almostSupportTauTiltingData, 'Almost support tau-tilting modules');
          }
          resizeDrawerContent();
          return true;
        }

        function clearAllNodeHighlights() {
          splitPairHighlights = new Map();
          pairHighlighted = new Set();
          tiltingHighlighted = new Set();
          calculatorHighlighted = new Set();
          if (typeof activeModuleClasses !== 'undefined') activeModuleClasses.clear();
          ['torsBtn','reflBtn','gpBtn','giBtn'].forEach(id => {
            const btn = document.getElementById(id);
            if (btn) btn.classList.remove('ar-control-active');
          });
          if (folderPanel) {
            folderPanel.querySelectorAll('button[data-click="torsBtn"],button[data-click="reflBtn"],button[data-click="gpBtn"],button[data-click="giBtn"]').forEach(btn => btn.classList.remove('ar-control-active'));
          }
          network.body.data.nodes.getIds().forEach(id => restoreNodeBase(id));
          network.unselectAll();
          network.redraw();
        }

        function clearListColoring() {
          clearAllNodeHighlights();
          clearActiveTilting();
          ['tiltingList','torsionPairList','cotorsionPairList','supportTauList','almostSupportTauList'].forEach(clearButtonListActive);
          clearListMenuActive();
          ['tiltingToggle','torsionPairToggle','cotorsionPairToggle','supportTauToggle','almostSupportTauToggle'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.checked = false;
          });
        }

        function addMenuStyles() {
          const style = document.createElement('style');
          style.textContent = `
            #arTopMenu {
              position: fixed;
              top: 0;
              left: 0;
              right: 0;
              height: 34px;
              display: flex;
              align-items: center;
              gap: 8px;
              padding: 0 10px;
              background: rgba(15,23,42,0.94);
              color: #f8fafc;
              z-index: 20001;
              font-family: system-ui,-apple-system,Segoe UI,sans-serif;
              font-size: 13px;
              box-shadow: 0 2px 10px rgba(15,23,42,0.25);
            }
            #arTopMenu button {
              border: 0;
              border-radius: 5px;
              background: rgba(255,255,255,0.12);
              color: #f8fafc;
              padding: 5px 9px;
              cursor: pointer;
              font: inherit;
            }
            #arTopMenu button:hover { background: rgba(255,255,255,0.22); }
            #arTopMenu button.ar-top-active { background:#dbeafe; color:#1d4ed8; font-weight:700; }
            #arTopMenu .ar-title { font-weight: 650; margin-right: 8px; }
            #arTopMenu .ar-spacer { flex: 1; }
            #arFolderPanel {
              position: fixed;
              top: 42px;
              left: 10px;
              width: 310px;
              max-height: calc(100vh - 54px);
              overflow: auto;
              background: rgba(255,255,255,0.97);
              border: 1px solid #cbd5e1;
              border-radius: 9px;
              box-shadow: 0 12px 32px rgba(15,23,42,0.22);
              z-index: 20000;
              font-family: system-ui,-apple-system,Segoe UI,sans-serif;
              font-size: 13px;
              display: block;
            }
            #arFolderPanel .ar-panel-head {
              position: sticky;
              top: 0;
              z-index: 2;
              display: flex;
              align-items: center;
              justify-content: space-between;
              padding: 8px 10px;
              border-bottom: 1px solid #e5e7eb;
              background: #f8fafc;
              border-radius: 9px 9px 0 0;
              font-weight: 650;
            }
            #arFolderPanel .ar-panel-close { border: 0; background: transparent; font-size: 18px; cursor: pointer; }
            #arFolderPanel details { border-bottom: 1px solid #eef2f7; }
            #arFolderPanel summary {
              cursor: pointer;
              padding: 8px 10px;
              font-weight: 600;
              color: #0f172a;
              user-select: none;
            }
            #arFolderPanel .ar-folder-body { padding: 4px 8px 9px 18px; display: grid; gap: 4px; }
            #arFolderPanel button {
              text-align: left;
              border: 0;
              background: transparent;
              padding: 5px 7px;
              border-radius: 5px;
              cursor: pointer;
              font: inherit;
            }
            #arFolderPanel button:hover { background: #eff6ff; }
            #arFolderPanel button.ar-control-active { background:#dbeafe; color:#1d4ed8; font-weight:700; box-shadow: inset 3px 0 0 #2563eb; }
            #arGapCodePanel .ar-panel-head {
              display:flex;
              align-items:center;
              justify-content:space-between;
              padding:8px 10px;
              border-bottom:1px solid #e5e7eb;
              background:#f8fafc;
              border-radius:9px 9px 0 0;
              font-weight:650;
              cursor:move;
            }
            .ar-soft-close {
              border:1px solid #cbd5e1;
              background:#ffffff;
              color:#334155;
              border-radius:999px;
              padding:3px 10px;
              font:inherit;
              font-size:12px;
              cursor:pointer;
            }
            .ar-soft-close:hover { background:#eff6ff; color:#1d4ed8; border-color:#93c5fd; }
            .ar-math-label { font-family: serif; }
            #arListDrawer {
              position: fixed;
              top: 42px;
              right: 10px;
              width: 390px;
              height: auto;
              min-width: 260px;
              min-height: 160px;
              max-width: 96vw;
              max-height: 96vh;
              overflow: auto;
              background: rgba(255,255,255,0.97);
              border: 1px solid #cbd5e1;
              border-radius: 9px;
              box-shadow: 0 12px 32px rgba(15,23,42,0.22);
              z-index: 20000;
              display: none;
            }
            #arListDrawer .ar-panel-head {
              display: flex;
              align-items: center;
              justify-content: space-between;
              padding: 8px 10px;
              border-bottom: 1px solid #e5e7eb;
              background: #f8fafc;
              border-radius: 9px 9px 0 0;
              font-weight: 650;
              font-family: system-ui,-apple-system,Segoe UI,sans-serif;
              font-size: 13px;
              cursor: move;
            }
            #arListDrawer .ar-panel-close { border: 0; background: transparent; font-size: 18px; cursor: pointer; }
            .ar-list-resize-handle { position:absolute; background:transparent; z-index:2; }
            .ar-list-resize-handle:hover { background:rgba(37,99,235,0.18); }
            .ar-list-resize-left { left:0; top:8px; bottom:8px; width:7px; cursor:ew-resize; }
            .ar-list-resize-right { right:0; top:8px; bottom:8px; width:7px; cursor:ew-resize; }
            .ar-list-resize-top { left:8px; right:8px; top:0; height:7px; cursor:ns-resize; }
            .ar-list-resize-bottom { left:8px; right:8px; bottom:0; height:7px; cursor:ns-resize; }
            .ar-list-resize-nw { left:0; top:0; width:9px; height:9px; cursor:nwse-resize; }
            .ar-list-resize-ne { right:0; top:0; width:9px; height:9px; cursor:nesw-resize; }
            .ar-list-resize-sw { left:0; bottom:0; width:9px; height:9px; cursor:nesw-resize; }
            .ar-list-resize-se { right:0; bottom:0; width:9px; height:9px; cursor:nwse-resize; }
            .ar-window-resize-handle { position:absolute; background:transparent; z-index:3; }
            .ar-window-resize-handle:hover { background:rgba(37,99,235,0.18); }
            .ar-window-resize-left { left:0; top:8px; bottom:8px; width:7px; cursor:ew-resize; }
            .ar-window-resize-right { right:0; top:8px; bottom:8px; width:7px; cursor:ew-resize; }
            .ar-window-resize-top { left:8px; right:8px; top:0; height:7px; cursor:ns-resize; }
            .ar-window-resize-bottom { left:8px; right:8px; bottom:0; height:7px; cursor:ns-resize; }
            .ar-window-resize-nw { left:0; top:0; width:9px; height:9px; cursor:nwse-resize; }
            .ar-window-resize-ne { right:0; top:0; width:9px; height:9px; cursor:nesw-resize; }
            .ar-window-resize-sw { left:0; bottom:0; width:9px; height:9px; cursor:nesw-resize; }
            .ar-window-resize-se { right:0; bottom:0; width:9px; height:9px; cursor:nwse-resize; }
            #arListDrawerBody { padding: 8px; }
            #tiltingList, #torsionPairList, #cotorsionPairList, #supportTauList, #almostSupportTauList { min-width: 240px; max-width: 100%; }
            .ar-record-row { display:block; width:100%; text-align:left; margin:2px 0; padding:4px 6px; border:1px solid #dbeafe; border-radius:4px; background:#fff; font-family:monospace; font-size:11px; cursor:pointer; }
            .ar-record-row:hover { background:#eff6ff; }
          `;
          document.head.appendChild(style);
        }

        function addWindowResizeHandles(el) {
          if (!el || el.dataset.arResizable === 'true') return;
          el.dataset.arResizable = 'true';
          const classSuffix = {
            'left': 'left',
            'right': 'right',
            'top': 'top',
            'bottom': 'bottom',
            'top left': 'nw',
            'top right': 'ne',
            'bottom left': 'sw',
            'bottom right': 'se'
          };
          ['left','right','top','bottom','top left','top right','bottom left','bottom right'].forEach(dir => {
            const handle = document.createElement('div');
            handle.className = 'ar-window-resize-handle ar-window-resize-' + classSuffix[dir];
            handle.dataset.resize = dir;
            el.appendChild(handle);
          });
        }

        function makeFloatingWindow(el, handle, options = {}) {
          if (!el || el.dataset.arFloatingWindow === 'true') return;
          el.dataset.arFloatingWindow = 'true';
          const minWidth = Number(options.minWidth || 260);
          const minHeight = Number(options.minHeight || 160);
          const onResize = typeof options.onResize === 'function' ? options.onResize : null;
          if (getComputedStyle(el).position === 'static') el.style.position = 'fixed';
          addWindowResizeHandles(el);
          let drag = null;
          let resize = null;
          const startDrag = (event) => {
            if (event.target.closest('button,input,select,textarea,.ar-window-resize-handle,.ar-list-resize-handle')) return;
            const rect = el.getBoundingClientRect();
            el.style.left = rect.left + 'px';
            el.style.top = rect.top + 'px';
            el.style.right = 'auto';
            el.style.bottom = 'auto';
            el.style.width = rect.width + 'px';
            el.style.height = rect.height + 'px';
            drag = { x: event.clientX, y: event.clientY, left: rect.left, top: rect.top };
            event.preventDefault();
          };
          (handle || el).addEventListener('mousedown', startDrag);
          el.querySelectorAll('.ar-window-resize-handle').forEach(handleEl => {
            handleEl.addEventListener('mousedown', (event) => {
              const rect = el.getBoundingClientRect();
              el.style.left = rect.left + 'px';
              el.style.top = rect.top + 'px';
              el.style.right = 'auto';
              el.style.bottom = 'auto';
              el.style.width = rect.width + 'px';
              el.style.height = rect.height + 'px';
              resize = { dirs: handleEl.dataset.resize.split(' '), x: event.clientX, y: event.clientY, left: rect.left, top: rect.top, width: rect.width, height: rect.height };
              event.preventDefault();
              event.stopPropagation();
            });
          });
          document.addEventListener('mousemove', (event) => {
            if (drag) {
              const width = el.offsetWidth || minWidth;
              const height = el.offsetHeight || minHeight;
              const left = Math.max(0, Math.min(window.innerWidth - Math.min(60, width), drag.left + event.clientX - drag.x));
              const top = Math.max(0, Math.min(window.innerHeight - Math.min(40, height), drag.top + event.clientY - drag.y));
              el.style.left = Math.min(left, Math.max(0, window.innerWidth - width - 4)) + 'px';
              el.style.top = Math.min(top, Math.max(0, window.innerHeight - height - 4)) + 'px';
            }
            if (resize) {
              let left = resize.left;
              let top = resize.top;
              let width = resize.width;
              let height = resize.height;
              const dx = event.clientX - resize.x;
              const dy = event.clientY - resize.y;
              if (resize.dirs.includes('right')) width = resize.width + dx;
              if (resize.dirs.includes('bottom')) height = resize.height + dy;
              if (resize.dirs.includes('left')) { width = resize.width - dx; left = resize.left + dx; }
              if (resize.dirs.includes('top')) { height = resize.height - dy; top = resize.top + dy; }
              if (width < minWidth) { if (resize.dirs.includes('left')) left -= minWidth - width; width = minWidth; }
              if (height < minHeight) { if (resize.dirs.includes('top')) top -= minHeight - height; height = minHeight; }
              left = Math.max(0, left);
              top = Math.max(0, top);
              width = Math.min(width, window.innerWidth - left - 4);
              height = Math.min(height, window.innerHeight - top - 4);
              el.style.left = left + 'px';
              el.style.top = top + 'px';
              el.style.width = width + 'px';
              el.style.height = height + 'px';
              if (onResize) onResize(el, width, height);
            }
          });
          document.addEventListener('mouseup', () => { drag = null; resize = null; });
        }

        function resizeDrawerContent() {
          if (!drawer || !drawerBody) return;
          const rect = drawer.getBoundingClientRect();
          const head = drawer.querySelector('.ar-panel-head');
          const headHeight = head ? head.offsetHeight : 0;
          const bodyHeight = Math.max(80, rect.height - headHeight - 2);
          drawerBody.style.height = bodyHeight + 'px';
          drawerBody.style.overflow = 'auto';
          if (drawerListId) {
            const listEl = document.getElementById(drawerListId);
            if (listEl) {
              listEl.style.maxHeight = Math.max(60, bodyHeight - 16) + 'px';
              listEl.style.height = Math.max(60, bodyHeight - 16) + 'px';
              listEl.style.overflow = 'auto';
            }
          }
        }

        function ensureDrawer() {
          if (drawer) return;
          drawer = document.createElement('div');
          drawer.id = 'arListDrawer';
          drawer.innerHTML = '<div class="ar-list-resize-handle ar-list-resize-left" data-resize="left"></div><div class="ar-list-resize-handle ar-list-resize-right" data-resize="right"></div><div class="ar-list-resize-handle ar-list-resize-top" data-resize="top"></div><div class="ar-list-resize-handle ar-list-resize-bottom" data-resize="bottom"></div><div class="ar-list-resize-handle ar-list-resize-nw" data-resize="top left"></div><div class="ar-list-resize-handle ar-list-resize-ne" data-resize="top right"></div><div class="ar-list-resize-handle ar-list-resize-sw" data-resize="bottom left"></div><div class="ar-list-resize-handle ar-list-resize-se" data-resize="bottom right"></div><div class="ar-panel-head"><strong id="arDrawerTitle"></strong><button id="arDrawerClose" class="ar-panel-close">×</button></div><div id="arListDrawerBody"></div>';
          document.body.appendChild(drawer);
          drawerTitle = drawer.querySelector('#arDrawerTitle');
          drawerBody = drawer.querySelector('#arListDrawerBody');
          drawer.querySelector('#arDrawerClose').addEventListener('click', () => {
            closeListDrawer(true);
          });
          const drawerHead = drawer.querySelector('.ar-panel-head');
          let drawerDrag = null;
          drawerHead.addEventListener('mousedown', (event) => {
            if (event.target.closest('button')) return;
            const rect = drawer.getBoundingClientRect();
            drawer.style.left = rect.left + 'px';
            drawer.style.top = rect.top + 'px';
            drawer.style.right = 'auto';
            drawer.style.bottom = 'auto';
            drawer.style.width = rect.width + 'px';
            drawer.style.height = rect.height + 'px';
            drawerDrag = { x: event.clientX, y: event.clientY, left: rect.left, top: rect.top };
            event.preventDefault();
          });
          let drawerResize = null;
          drawer.querySelectorAll('.ar-list-resize-handle').forEach(handle => {
            handle.addEventListener('mousedown', (event) => {
              const rect = drawer.getBoundingClientRect();
              drawer.style.left = rect.left + 'px';
              drawer.style.top = rect.top + 'px';
              drawer.style.right = 'auto';
              drawer.style.bottom = 'auto';
              drawer.style.width = rect.width + 'px';
              drawer.style.height = rect.height + 'px';
              drawerResize = { dirs: handle.dataset.resize.split(' '), x: event.clientX, y: event.clientY, left: rect.left, top: rect.top, width: rect.width, height: rect.height };
              event.preventDefault();
              event.stopPropagation();
            });
          });
          document.addEventListener('mousemove', (event) => {
            if (drawerDrag) {
              drawer.style.left = Math.max(0, Math.min(window.innerWidth - 60, drawerDrag.left + event.clientX - drawerDrag.x)) + 'px';
              drawer.style.top = Math.max(0, Math.min(window.innerHeight - 40, drawerDrag.top + event.clientY - drawerDrag.y)) + 'px';
            }
            if (drawerResize) {
              let left = drawerResize.left;
              let top = drawerResize.top;
              let width = drawerResize.width;
              let height = drawerResize.height;
              const dx = event.clientX - drawerResize.x;
              const dy = event.clientY - drawerResize.y;
              if (drawerResize.dirs.includes('right')) width = drawerResize.width + dx;
              if (drawerResize.dirs.includes('bottom')) height = drawerResize.height + dy;
              if (drawerResize.dirs.includes('left')) { width = drawerResize.width - dx; left = drawerResize.left + dx; }
              if (drawerResize.dirs.includes('top')) { height = drawerResize.height - dy; top = drawerResize.top + dy; }
              if (width < 260) { if (drawerResize.dirs.includes('left')) left -= 260 - width; width = 260; }
              if (height < 160) { if (drawerResize.dirs.includes('top')) top -= 160 - height; height = 160; }
              width = Math.min(width, window.innerWidth - left - 4);
              height = Math.min(height, window.innerHeight - top - 4);
              drawer.style.left = Math.max(0, left) + 'px';
              drawer.style.top = Math.max(0, top) + 'px';
              drawer.style.width = width + 'px';
              drawer.style.height = height + 'px';
              resizeDrawerContent();
            }
          });
          document.addEventListener('mouseup', () => { drawerDrag = null; drawerResize = null; });
        }

        let calculatorPanel = null;
        function allModuleIds() {
          const ids = new Set();
          const add = (value) => {
            const n = Number(value);
            if (Number.isFinite(n)) ids.add(n);
          };
          if (pdidMap && typeof pdidMap === 'object') Object.keys(pdidMap).forEach(add);
          (tiltingData || []).forEach(item => {
            (item.L || []).forEach(add);
            (item.F || []).forEach(add);
            (item.T || []).forEach(add);
          });
          (torsionPairData || []).forEach(item => {
            (item.T || []).forEach(add);
            (item.F || []).forEach(add);
          });
          if (ids.size === 0 && network && network.body && network.body.data && network.body.data.nodes && typeof network.body.data.nodes.getIds === 'function') {
            network.body.data.nodes.getIds().forEach(add);
          }
          return Array.from(ids).sort((a, b) => a - b);
        }
        function calcAllIds() {
          return allModuleIds();
        }
        function calcParseSet(text) {
          const all = calcAllIds();
          const raw = String(text || '').trim();
          if (!raw) return [];
          if (raw.toLowerCase() === 'all' || raw === '*') return all;
          return Array.from(new Set((raw.match(/-?\\d+/g) || []).map(Number).filter(x => all.includes(x)))).sort((a, b) => a - b);
        }
        function calcFormatSet(ids) {
          const arr = Array.from(new Set((ids || []).map(Number).filter(Number.isFinite))).sort((a, b) => a - b);
          return arr.length ? arr.join(' ') : '∅';
        }
        function calcNonzero(edges, a, b) {
          return (edges || []).some(e => Number(e[0]) === Number(a) && Number(e[1]) === Number(b) && String(e[2] == null ? '1' : e[2]) !== '0');
        }
        function calcDim(edges, a, b) {
          const e = (edges || []).find(e => Number(e[0]) === Number(a) && Number(e[1]) === Number(b));
          return e ? String(e[2] == null ? '1' : e[2]) : '0';
        }
        function calcPairs(edges, left, right) {
          const L = new Set(left.map(Number));
          const R = new Set(right.map(Number));
          return (edges || []).filter(e => L.has(Number(e[0])) && R.has(Number(e[1])) && String(e[2] == null ? '1' : e[2]) !== '0')
            .map(e => `${e[0]}→${e[1]}:${e[2] == null ? 1 : e[2]}`);
        }
        function calcImage(edges, input) {
          const S = new Set(input.map(Number));
          return (edges || []).filter(e => S.has(Number(e[0]))).map(e => Number(e[1]));
        }
        function calcImageWithMultiplicity(edges, input) {
          const out = [];
          (input || []).forEach(x => {
            (edges || []).forEach(e => {
              if (Number(e[0]) === Number(x)) out.push(Number(e[1]));
            });
          });
          return out;
        }
        function calcRelationFromEdges(edges) {
          const rel = new Map();
          (edges || []).forEach(e => {
            const from = Number(e[0]);
            const to = Number(e[1]);
            if (!Number.isFinite(from) || !Number.isFinite(to)) return;
            if (!rel.has(from)) rel.set(from, new Map());
            const row = rel.get(from);
            row.set(to, (row.get(to) || 0n) + 1n);
          });
          return rel;
        }
        function calcApplyRelationToVector(vec, rel) {
          const out = new Map();
          vec.forEach((count, from) => {
            const row = rel.get(from);
            if (!row) return;
            row.forEach((mult, to) => out.set(to, (out.get(to) || 0n) + count * mult));
          });
          return out;
        }
        function calcComposeRelations(left, right) {
          const out = new Map();
          left.forEach((row, from) => {
            row.forEach((leftMult, mid) => {
              const rightRow = right.get(mid);
              if (!rightRow) return;
              if (!out.has(from)) out.set(from, new Map());
              const outRow = out.get(from);
              rightRow.forEach((rightMult, to) => outRow.set(to, (outRow.get(to) || 0n) + leftMult * rightMult));
            });
          });
          return out;
        }
        function calcVectorToIdList(vec) {
          const out = [];
          vec.forEach((count, id) => {
            if (count > 0n) out.push(id);
          });
          return out.sort((a, b) => a - b);
        }
        function calcIteratedImageMap(edges, input, steps) {
          let n = Number(steps);
          if (!Number.isInteger(n) || n < 0) throw new Error('n must be a nonnegative integer.');
          let vec = new Map();
          (input || []).map(Number).filter(Number.isFinite).forEach(id => vec.set(id, (vec.get(id) || 0n) + 1n));
          let rel = calcRelationFromEdges(edges);
          while (n > 0) {
            if (n % 2 === 1) vec = calcApplyRelationToVector(vec, rel);
            n = Math.floor(n / 2);
            if (n > 0) rel = calcComposeRelations(rel, rel);
            if (vec.size === 0) break;
          }
          return vec;
        }
        function calcIteratedImage(edges, input, steps) {
          return calcVectorToIdList(calcIteratedImageMap(edges, input, steps));
        }
        function calcIteratedSyzygy(input, steps) {
          return calcIteratedImage(syzygyEdges, input, steps);
        }
        function calcFormatMultiset(ids) {
          const counts = new Map();
          if (ids instanceof Map) {
            ids.forEach((count, id) => {
              const big = typeof count === 'bigint' ? count : BigInt(count || 0);
              if (big > 0n) counts.set(Number(id), big);
            });
          } else {
            (ids || []).map(Number).filter(Number.isFinite).forEach(id => counts.set(id, (counts.get(id) || 0n) + 1n));
          }
          const parts = Array.from(counts.keys()).sort((a, b) => a - b).map(id => counts.get(id) > 1n ? `${id}^${counts.get(id).toString()}` : String(id));
          return parts.length ? parts.join(' + ') : '∅';
        }
        function calcExtKDimValue(k, a, b) {
          if (k === 0) return BigInt(calcDimValue(homEdges, a, b));
          if (k === 1) return BigInt(calcDimValue(extEdges, a, b));
          const syz = calcIteratedImageMap(syzygyEdges, [a], k - 1);
          let total = 0n;
          syz.forEach((count, s) => { total += count * BigInt(calcDimValue(extEdges, s, b)); });
          return total;
        }
        function calcExtKDimSum(k, left, right) {
          let total = 0n;
          left.forEach(a => right.forEach(b => { total += calcExtKDimValue(k, a, b); }));
          return total.toString();
        }
        function calcParseK() {
          const value = Number(document.getElementById('calcK').value || '0');
          if (!Number.isInteger(value) || value < 0) throw new Error('k must be a nonnegative integer.');
          return value;
        }
        function calcRightExtKPerp(k, input) {
          const all = calcAllIds();
          return all.filter(x => input.every(a => calcExtKDimValue(k, a, x) === 0n));
        }
        function calcLeftExtKPerp(k, input) {
          const all = calcAllIds();
          return all.filter(x => input.every(b => calcExtKDimValue(k, x, b) === 0n));
        }
        function calcRightPerp(edges, input) {
          const all = calcAllIds();
          return all.filter(x => input.every(a => !calcNonzero(edges, a, x)));
        }
        function calcLeftPerp(edges, input) {
          const all = calcAllIds();
          return all.filter(x => input.every(a => !calcNonzero(edges, x, a)));
        }
        function calcDimValue(edges, a, b) {
          const e = (edges || []).find(e => Number(e[0]) === Number(a) && Number(e[1]) === Number(b));
          const raw = e ? String(e[2] == null ? '1' : e[2]) : '0';
          const n = Number(raw);
          return Number.isFinite(n) ? n : 0;
        }
        function calcDimSum(edges, left, right) {
          let total = 0;
          left.forEach(a => right.forEach(b => { total += calcDimValue(edges, a, b); }));
          return String(total);
        }
        function calcSingleIndecomposable(text, fieldName) {
          const values = calcParseSet(text);
          if (values.length !== 1) {
            throw new Error(fieldName + ' must contain exactly one indecomposable module label.');
          }
          return values[0];
        }
        function calcRunOperation() {
          const op = document.getElementById('calcOp').value;
          let output = '';
          let highlightA = [];
          let highlightB = [];
          let highlightOutput = [];
          try {
            if (op === 'ExtK') {
              const k = calcParseK();
              const A = calcParseSet(document.getElementById('calcA').value);
              const B = calcParseSet(document.getElementById('calcB').value);
              highlightA = A;
              highlightB = B;
              output = calcExtKDimSum(k, A, B);
            } else if (op === 'Syzygy') {
              const k = calcParseK();
              const a = calcSingleIndecomposable(document.getElementById('calcA').value, 'A');
              highlightA = [a];
              const result = calcIteratedImageMap(syzygyEdges, [a], k);
              highlightOutput = calcVectorToIdList(result);
              output = calcFormatMultiset(result);
            } else if (op === 'Cosyzygy') {
              const k = calcParseK();
              const a = calcSingleIndecomposable(document.getElementById('calcA').value, 'A');
              highlightA = [a];
              const result = calcIteratedImageMap(cosyzygyEdges, [a], k);
              highlightOutput = calcVectorToIdList(result);
              output = calcFormatMultiset(result);
            } else if (op === 'Radical') {
              const k = calcParseK();
              const a = calcSingleIndecomposable(document.getElementById('calcA').value, 'A');
              highlightA = [a];
              const result = calcIteratedImageMap(radicalEdges, [a], k);
              highlightOutput = calcVectorToIdList(result);
              output = calcFormatMultiset(result);
            } else if (op === 'Coradical') {
              const k = calcParseK();
              const a = calcSingleIndecomposable(document.getElementById('calcA').value, 'A');
              highlightA = [a];
              const result = calcIteratedImageMap(coradicalEdges, [a], k);
              highlightOutput = calcVectorToIdList(result);
              output = calcFormatMultiset(result);
            } else if (op === 'ExtKperp') {
              const k = calcParseK();
              const A = calcParseSet(document.getElementById('calcA').value);
              highlightA = A;
              highlightOutput = calcRightExtKPerp(k, A);
              output = calcFormatSet(highlightOutput);
            } else if (op === 'perpExtK') {
              const k = calcParseK();
              const B = calcParseSet(document.getElementById('calcB').value);
              highlightB = B;
              highlightOutput = calcLeftExtKPerp(k, B);
              output = calcFormatSet(highlightOutput);
            }
            applyCalculatorHighlights(highlightA, highlightB, highlightOutput);
          } catch (err) {
            clearCalculatorHighlight();
            output = err && err.message ? err.message : String(err);
          }
          document.getElementById('calcOutput').textContent = output;
        }
        function gapQuote(value) {
          return String(value == null ? '' : value).split(String.fromCharCode(92)).join(String.fromCharCode(92) + String.fromCharCode(92)).split('"').join(String.fromCharCode(92) + '"');
        }
        function gapArrowName(value, index) {
          const raw = String(value == null || value === '' ? 'a' + index : value).trim();
          const clean = raw.replace(/[^A-Za-z0-9_]/g, '_');
          if (/^[A-Za-z_][A-Za-z0-9_]*$/.test(clean)) return clean;
          return 'a' + index;
        }
        function calcSourceStem() {
          const name = (window.location.pathname.split('/').pop() || 'untitled.html').replace(/\\.(html|log|txt)$/i, '');
          return name || 'untitled';
        }
        function calcGapScript() {
          const source = calcSourceStem();
          const nodes = (quiverNodes || []).map(n => Number(n.id)).filter(Number.isFinite);
          const edgeNodes = (quiverEdges || []).flatMap(e => [Number(e[0]), Number(e[1])]).filter(Number.isFinite);
          const maxNode = nodes.length ? Math.max.apply(null, nodes) : (edgeNodes.length ? Math.max.apply(null, edgeNodes) : calcAllIds().length);
          const nVerts = Number.isFinite(maxNode) && maxNode > 0 ? maxNode : calcAllIds().length;
          const arrows = (quiverEdges || []).map((e, i) => {
            const name = gapArrowName(e[2], i + 1);
            return '[' + Number(e[0]) + ', ' + Number(e[1]) + ', "' + gapQuote(name) + '"]';
          });
          const relText = quiverRel && String(quiverRel).trim() ? String(quiverRel).trim() : '[]';
          const moduleDataText = indecomposableModuleDataGap && String(indecomposableModuleDataGap).trim() ? String(indecomposableModuleDataGap).trim() : '';
          const hasModuleData = moduleDataText.length > 0;
          const nl = String.fromCharCode(10);
          return [
            '# GAP/QPA script generated by AR Quiver',
            '# Source: ' + source,
            '#',
            '# Paste this code directly into a GAP cell, or save it as ' + source + '_run_with_gap.g and run it with GAP.',
            '#',
            '# Available objects after running:',
            '#   Q, kQ, rel, A, M, P, I, S',
            '',
            'LoadPackage("QPA");;',
            '',
            'Q := Quiver(' + nVerts + ', [',
            arrows.map((a, i) => '  ' + a + (i + 1 < arrows.length ? ',' : '')).join(nl),
            ']);;',
            '',
            'kQ := PathAlgebra(Rationals, Q);;',
            'AssignGeneratorVariables(kQ);;',
            '',
            '# Relations are evaluated after AssignGeneratorVariables, so arrow names can be used directly.',
            'rel := ' + relText + ';;',
            'A := kQ / rel;;',
            '',
            'P := IndecProjectiveModules(A);;',
            'I := IndecInjectiveModules(A);;',
            'S := SimpleModules(A);;',
            '',
            hasModuleData ? '# Indecomposable modules reconstructed from AR-quiver log data.' : '# No serialized module data found in this log.',
            hasModuleData ? moduleDataText : 'IndecomposableModuleData := [];;',
            hasModuleData ? 'M := List(IndecomposableModuleData, r -> RightModuleOverPathAlgebra(A, r.dim, r.maps));;' : 'M := [];;',
            '',
            'Print("Generated objects ready.");;',
            'Print("Q: original quiver");;',
            'Print("kQ: path algebra over Rationals");;',
            'Print("A: bound quiver algebra kQ / rel");;',
            'Print("Projectives P[1]..P[");; Print(Length(P));; Print("]");;',
            'Print("Injectives I[1]..I[");; Print(Length(I));; Print("]");;',
            'Print("Simples S[1]..S[");; Print(Length(S));; Print("]");;',
            'Print("Indecomposables M[1]..M[");; Print(Length(M));; Print("]");;',
            ''
          ].join(nl);
        }
        function calcRunWithGap() {
          const out = document.getElementById('calcOutput');
          const source = calcSourceStem();
          const script = calcGapScript();
          const filename = source + '_run_with_gap.g';
          out.innerHTML = '';
          appendGapCodeBox(out, script, filename, 'Generated GAP/QPA code for Q, kQ, A, M[i], P[i], I[i], S[i].');
        }
        function genGapCodeSnippet() {
          const nl = String.fromCharCode(10);
          return [
            '# Exact gen(X) computation for the indecomposables M[1],...,M[n].',
            '# First run the generated-quiver code so that A and M are defined.',
            '# Usage: GenOf([1,2,5]);',
            '',
            'TraceInclusionDimension := function(trace_inc)',
            '    if trace_inc = fail then return 0; fi;',
            '    return Dimension(Source(trace_inc));',
            'end;;',
            '',
            'ComputeTraceInclusionTable := function(verts)',
            '    local trace_inc, trace_dim, i, j, traceCall;',
            '    trace_inc := [];; trace_dim := [];;',
            '    for i in [1..Length(verts)] do',
            '        trace_inc[i] := [];; trace_dim[i] := [];;',
            '        for j in [1..Length(verts)] do',
            '            traceCall := CALL_WITH_CATCH(TraceOfModule, [verts[i], verts[j]]);',
            '            if traceCall[1] = true then',
            '                trace_inc[i][j] := traceCall[2];',
            '                trace_dim[i][j] := TraceInclusionDimension(traceCall[2]);',
            '            else',
            '                trace_inc[i][j] := fail;',
            '                trace_dim[i][j] := 0;',
            '            fi;',
            '        od;',
            '    od;',
            '    return rec(inc := trace_inc, dim := trace_dim);',
            'end;;',
            '',
            'TraceFullGenerates := function(verts, trace_table, src_idx, target_idx)',
            '    return trace_table.dim[src_idx][target_idx] = Dimension(verts[target_idx]);',
            'end;;',
            '',
            'QuotientClosureFromTrace := function(verts, trace_table, source_set)',
            '    local closure, changed, src_idx, target_idx;',
            '    closure := ShallowCopy(source_set);; Sort(closure);;',
            '    changed := true;;',
            '    while changed do',
            '        changed := false;;',
            '        for src_idx in ShallowCopy(closure) do',
            '            for target_idx in [1..Length(verts)] do',
            '                if not (target_idx in closure) and TraceFullGenerates(verts, trace_table, src_idx, target_idx) then',
            '                    AddSet(closure, target_idx);;',
            '                    changed := true;;',
            '                fi;',
            '            od;',
            '        od;',
            '    od;',
            '    return closure;',
            'end;;',
            '',
            'MinimalTraceSources := function(verts, trace_table, source_set)',
            '    local minimal, src_idx, other_idx, redundant;',
            '    minimal := [];;',
            '    for src_idx in source_set do',
            '        redundant := false;;',
            '        for other_idx in source_set do',
            '            if other_idx <> src_idx and TraceFullGenerates(verts, trace_table, other_idx, src_idx) then',
            '                redundant := true;; break;',
            '            fi;',
            '        od;',
            '        if not redundant then AddSet(minimal, src_idx); fi;',
            '    od;',
            '    return minimal;',
            'end;;',
            '',
            'IsGeneratedBySetFromTrace := function(verts, trace_table, source_set, target_idx)',
            '    local M0, target_dim, src_idx, reduced_sources, nonzero_traces, total_trace_dim, sum_inc, sumCall, inc;',
            '    M0 := verts[target_idx];;',
            '    target_dim := Dimension(M0);;',
            '    if target_dim = 0 then return true; fi;',
            '    if Length(source_set) = 0 then return false; fi;',
            '    reduced_sources := MinimalTraceSources(verts, trace_table, source_set);;',
            '    nonzero_traces := [];; total_trace_dim := 0;;',
            '    for src_idx in reduced_sources do',
            '        if trace_table.dim[src_idx][target_idx] = target_dim then return true; fi;',
            '        if trace_table.dim[src_idx][target_idx] > 0 and trace_table.inc[src_idx][target_idx] <> fail then',
            '            total_trace_dim := total_trace_dim + trace_table.dim[src_idx][target_idx];;',
            '            Add(nonzero_traces, trace_table.inc[src_idx][target_idx]);;',
            '        fi;',
            '    od;',
            '    if total_trace_dim < target_dim or Length(nonzero_traces) = 0 then return false; fi;',
            '    sum_inc := nonzero_traces[1];;',
            '    if Dimension(Source(sum_inc)) = target_dim then return true; fi;',
            '    if Length(nonzero_traces) >= 2 then',
            '        for src_idx in [2..Length(nonzero_traces)] do',
            '            inc := nonzero_traces[src_idx];;',
            '            sumCall := CALL_WITH_CATCH(SumOfSubmodules, [sum_inc, inc]);',
            '            if sumCall[1] = true then',
            '                sum_inc := sumCall[2][1];;',
            '                if Dimension(Source(sum_inc)) = target_dim then return true; fi;',
            '            fi;',
            '        od;',
            '    fi;',
            '    return Dimension(Source(sum_inc)) = target_dim;',
            'end;;',
            '',
            'GenClosureFromTrace := function(verts, trace_table, source_set)',
            '    local closure, quotient_closed, idx;',
            '    quotient_closed := QuotientClosureFromTrace(verts, trace_table, source_set);;',
            '    closure := ShallowCopy(quotient_closed);;',
            '    for idx in [1..Length(verts)] do',
            '        if not (idx in closure) and IsGeneratedBySetFromTrace(verts, trace_table, quotient_closed, idx) then',
            '            Add(closure, idx);;',
            '        fi;',
            '    od;',
            '    closure := QuotientClosureFromTrace(verts, trace_table, closure);;',
            '    Sort(closure);;',
            '    return closure;',
            'end;;',
            '',
            'trace_table_for_gen := ComputeTraceInclusionTable(M);;',
            'GenOf := function(X)',
            '    return GenClosureFromTrace(M, trace_table_for_gen, X);',
            'end;;',
            '',
            '# Example:',
            'GenOf([1]);'
          ].join(nl);
        }
        function cogenGapCodeSnippet() {
          const nl = String.fromCharCode(10);
          return [
            '# Cogen(X) helper skeleton.',
            '# First run the generated-quiver code so that A and M are defined.',
            '# In many QPA setups this can be computed by applying the gen(-) code to dual modules.',
            '# Adjust the dual functor name if your QPA installation uses a different one.',
            '',
            '# 1. Paste/run the find gen(-) code first.',
            '# 2. Define a dual list, for example one of the following may work depending on QPA version:',
            '# DM := List(M, D);;',
            '# DM := List(M, DualOfModule);;',
            '# DM := List(M, DualModule);;',
            '',
            '# Then compute gen on the dual side and translate indices back:',
            '# trace_table_for_cogen := ComputeTraceInclusionTable(DM);;',
            '# CogenOf := function(X)',
            '#     return GenClosureFromTrace(DM, trace_table_for_cogen, X);',
            '# end;;',
            '# CogenOf([1]);'
          ].join(nl);
        }
        function extensionClosureGapCodeSnippet() {
          return String.raw`# Extension closure of a class of modules by an Ext^1 middle-term table.
# First run the generated-quiver code so that A and M are defined.
# Usage:
#   table := ComputeExtMiddleTermTable(M);;
#   ExtensionClosureFromTable([1,2,5], table);
#
# Convention:
#   table[sub][quot] stores middle terms of short exact sequences
#       0 -> M[sub] -> E -> M[quot] -> 0.
#   Each middle term is stored by the labels of its indecomposable summands.
#
# Over a finite field this enumerates all Ext^1 classes and is exact.
# Over an infinite field such as Rationals, Ext^1 has infinitely many linear
# combinations; this snippet computes the split extension plus the chosen
# ExtOverAlgebra basis representatives. Use finite fields for a complete table.

ModuleLabelInList := function(verts, N)
    local i;
    for i in [1..Length(verts)] do
        if IsomorphicModules(N, verts[i]) then return i; fi;
    od;
    return fail;
end;;

SnippetFindNontrivialIdempotent := function(N)
    local HomNN, nn, m, n, i, j, f, e, imgDim;
    if Dimension(N) = 0 then return false; fi;
    HomNN := HomOverAlgebra(N, N);
    nn := Length(HomNN);
    if nn <= 1 then return false; fi;
    m := Maximum(DimensionVector(N));
    if m <= 0 then return false; fi;
    n := Int(Ceil(Log2(1.0 * m)));
    for i in [1..nn] do
        f := HomNN[i];
        e := f;
        for j in [1..n] do
            e := e * e;
        od;
        imgDim := Dimension(Image(e));
        if imgDim <> 0 and imgDim <> Dimension(N) then
            return e;
        fi;
    od;
    return false;
end;;

SnippetDecomposeToProjections := function(N)
    local e, id, eK, U, K, pU, pK, projsU, projsK, projs, p;
    if Dimension(N) = 0 then return [];; fi;
    e := SnippetFindNontrivialIdempotent(N);
    if e = false then return [IdentityMapping(N)]; fi;
    id := IdentityMapping(N);
    eK := id - e;
    U := Image(e);
    K := Image(eK);
    pU := ImageProjection(e);
    pK := ImageProjection(eK);
    projsU := SnippetDecomposeToProjections(U);
    projsK := SnippetDecomposeToProjections(K);
    projs := [];;
    for p in projsU do Add(projs, pU * p); od;
    for p in projsK do Add(projs, pK * p); od;
    return projs;
end;;

IndecomposableLabelsOfModule := function(verts, N)
    local projections, labels, pr, piece, label;
    if Dimension(N) = 0 then return [];; fi;
    projections := SnippetDecomposeToProjections(N);
    labels := [];;
    for pr in projections do
        piece := Range(pr);
        label := ModuleLabelInList(verts, piece);
        if label = fail then
            Error("Could not identify an indecomposable summand in M.");
        fi;
        Add(labels, label);
    od;
    Sort(labels);;
    return labels;
end;;

DirectSumForClass := function(verts, class)
    if Length(class) = 0 then
        Error("DirectSumForClass needs a non-empty class.");
    fi;
    if Length(class) = 1 then
        return verts[class[1]];
    fi;
    return DirectSumOfQPAModules(List(class, i -> verts[i]));
end;;

LinearCombinationOfMaps := function(zero_map, basis_maps, coeffs)
    local h, i;
    h := zero_map;
    for i in [1..Length(basis_maps)] do
        if coeffs[i] <> Zero(LeftActingDomain(Source(zero_map))) then
            h := h + coeffs[i] * basis_maps[i];
        fi;
    od;
    return h;
end;;

MiddleLabelsFromExtClass := function(verts, sub_module, quot_module, class_map)
    local extData, syzInc, po, inc, middle;
    extData := ExtOverAlgebra(quot_module, sub_module);
    syzInc := extData[1];
    po := PushOut(syzInc, class_map);
    if po = fail then Error("PushOut failed while constructing the extension."); fi;
    inc := po[1];
    middle := Range(inc);
    return IndecomposableLabelsOfModule(verts, middle);
end;;

MiddleTermLabelsForPair := function(verts, sub_idx, quot_idx)
    local K, sub_module, quot_module, extData, syzInc, basisMaps, zeroMap, coeffTuples, tuple, labels, allLabels, h, i;
    K := LeftActingDomain(verts[1]);
    sub_module := verts[sub_idx];
    quot_module := verts[quot_idx];
    extData := ExtOverAlgebra(quot_module, sub_module);
    syzInc := extData[1];
    basisMaps := extData[2];
    allLabels := [ [sub_idx, quot_idx] ];;
    if Length(basisMaps) = 0 then return allLabels; fi;
    zeroMap := ZeroMapping(Source(syzInc), sub_module);
    if IsFinite(K) then
        coeffTuples := Tuples(Elements(K), Length(basisMaps));
    else
        Print("Warning: base field is not finite; using only Ext basis representatives for pair ", sub_idx, " -> E -> ", quot_idx, ".\n");
        coeffTuples := [];;
        for i in [1..Length(basisMaps)] do
            tuple := List([1..Length(basisMaps)], j -> Zero(K));
            tuple[i] := One(K);
            Add(coeffTuples, tuple);
        od;
    fi;
    for tuple in coeffTuples do
        if ForAll(tuple, c -> c = Zero(K)) then
            continue;
        fi;
        h := LinearCombinationOfMaps(zeroMap, basisMaps, tuple);
        labels := MiddleLabelsFromExtClass(verts, sub_module, quot_module, h);
        AddSet(allLabels, labels);
    od;
    return allLabels;
end;;

ComputeExtMiddleTermTable := function(verts)
    local table, sub_idx, quot_idx;
    table := [];;
    for sub_idx in [1..Length(verts)] do
        table[sub_idx] := [];;
        for quot_idx in [1..Length(verts)] do
            table[sub_idx][quot_idx] := MiddleTermLabelsForPair(verts, sub_idx, quot_idx);
        od;
    od;
    return table;
end;;

ExtensionClosureFromTable := function(X, table)
    local closure, changed, sub_idx, quot_idx, middleLists, labels, label;
    closure := ShallowCopy(X);; Sort(closure);;
    changed := true;;
    while changed do
        changed := false;;
        for sub_idx in ShallowCopy(closure) do
            for quot_idx in ShallowCopy(closure) do
                middleLists := table[sub_idx][quot_idx];
                for labels in middleLists do
                    for label in labels do
                        if not (label in closure) then
                            AddSet(closure, label);;
                            changed := true;;
                        fi;
                    od;
                od;
            od;
        od;
    od;
    Sort(closure);;
    return closure;
end;;

ExtensionClosureOf := function(X)
    return ExtensionClosureFromTable(X, ComputeExtMiddleTermTable(M));
end;;

# Example:
# table := ComputeExtMiddleTermTable(M);;
# ExtensionClosureFromTable([1], table);`;
        }
        function extBasisGapCodeSnippet() {
          return String.raw`# Ext^1 basis for two classes of indecomposable modules.
# First run the generated-quiver code so that A and M are defined.
# Usage:
#   ExtBasisSequencesForClasses([1,2], [3,4]);
#   PrintExtBasisSequencesForClasses([1,2], [3,4]);
#
# Convention:
#   ExtBasisSequencesForClasses(sub_class, quotient_class)
# computes basis representatives of
#   Ext^1( direct_sum(quotient_class), direct_sum(sub_class) ),
# equivalently short exact sequences
#   0 -> direct_sum(sub_class) -> E -> direct_sum(quotient_class) -> 0.

ModuleLabelInList := function(verts, N)
    local i;
    for i in [1..Length(verts)] do
        if IsomorphicModules(N, verts[i]) then return i; fi;
    od;
    return fail;
end;;

SnippetFindNontrivialIdempotent := function(N)
    local HomNN, nn, m, n, i, j, f, e, imgDim;
    if Dimension(N) = 0 then return false; fi;
    HomNN := HomOverAlgebra(N, N);
    nn := Length(HomNN);
    if nn <= 1 then return false; fi;
    m := Maximum(DimensionVector(N));
    if m <= 0 then return false; fi;
    n := Int(Ceil(Log2(1.0 * m)));
    for i in [1..nn] do
        f := HomNN[i];
        e := f;
        for j in [1..n] do e := e * e; od;
        imgDim := Dimension(Image(e));
        if imgDim <> 0 and imgDim <> Dimension(N) then return e; fi;
    od;
    return false;
end;;

SnippetDecomposeToProjections := function(N)
    local e, id, eK, U, K, pU, pK, projsU, projsK, projs, p;
    if Dimension(N) = 0 then return [];; fi;
    e := SnippetFindNontrivialIdempotent(N);
    if e = false then return [IdentityMapping(N)]; fi;
    id := IdentityMapping(N);
    eK := id - e;
    U := Image(e);
    K := Image(eK);
    pU := ImageProjection(e);
    pK := ImageProjection(eK);
    projsU := SnippetDecomposeToProjections(U);
    projsK := SnippetDecomposeToProjections(K);
    projs := [];;
    for p in projsU do Add(projs, pU * p); od;
    for p in projsK do Add(projs, pK * p); od;
    return projs;
end;;

IndecomposableLabelsOfModule := function(verts, N)
    local projections, labels, pr, piece, label;
    if Dimension(N) = 0 then return [];; fi;
    projections := SnippetDecomposeToProjections(N);
    labels := [];;
    for pr in projections do
        piece := Range(pr);
        label := ModuleLabelInList(verts, piece);
        if label = fail then Error("Could not identify an indecomposable summand in M."); fi;
        Add(labels, label);
    od;
    Sort(labels);;
    return labels;
end;;

DirectSumForClass := function(verts, class)
    if Length(class) = 0 then
        Error("DirectSumForClass needs a non-empty class.");
    fi;
    if Length(class) = 1 then
        return verts[class[1]];
    fi;
    return DirectSumOfQPAModules(List(class, i -> verts[i]));
end;;

ExtBasisSequencesForClasses := function(sub_class, quotient_class)
    local sub_module, quotient_module, extData, syzInc, basisMaps, seqs, h, po, inc, middle, q;
    sub_module := DirectSumForClass(M, sub_class);
    quotient_module := DirectSumForClass(M, quotient_class);
    extData := ExtOverAlgebra(quotient_module, sub_module);
    syzInc := extData[1];
    basisMaps := extData[2];
    seqs := [];;
    for h in basisMaps do
        po := PushOut(syzInc, h);
        if po = fail then Error("PushOut failed while constructing an Ext representative."); fi;
        inc := po[1];
        middle := Range(inc);
        q := CoKernelProjection(inc);
        Add(seqs, rec(
            sub_class := sub_class,
            quotient_class := quotient_class,
            submodule := sub_module,
            quotient := quotient_module,
            inclusion := inc,
            middle := middle,
            middle_labels := IndecomposableLabelsOfModule(M, middle),
            quotient_projection := q
        ));
    od;
    return seqs;
end;;

PrintExtBasisSequencesForClasses := function(sub_class, quotient_class)
    local seqs, i;
    seqs := ExtBasisSequencesForClasses(sub_class, quotient_class);
    Print("dim Ext^1(⊕", quotient_class, ", ⊕", sub_class, ") = ", Length(seqs), "\n");
    for i in [1..Length(seqs)] do
        Print(i, ": 0 -> ⊕", sub_class, " -> E -> ⊕", quotient_class, " -> 0,  E indec labels = ", seqs[i].middle_labels, "\n");
    od;
    return seqs;
end;;

# Example:
# PrintExtBasisSequencesForClasses([1], [2]);`;
        }
        function usefulGapCode(kind) {
          if (kind === 'generate') return calcGapScript();
          if (kind === 'gen') return calcGapScript() + String.fromCharCode(10) + genGapCodeSnippet();
          if (kind === 'cogen') return calcGapScript() + String.fromCharCode(10) + cogenGapCodeSnippet();
          if (kind === 'extclosure') return calcGapScript() + String.fromCharCode(10) + extensionClosureGapCodeSnippet();
          if (kind === 'extbasis') return calcGapScript() + String.fromCharCode(10) + extBasisGapCodeSnippet();
          return calcGapScript();
        }
        function hideUsefulGapCode() {
          const panel = document.getElementById('arGapCodePanel');
          if (panel) {
            panel.style.display = 'none';
            panel.removeAttribute('data-gap-kind');
          }
          if (typeof refreshFolderControlStates === 'function') refreshFolderControlStates();
        }
        function showUsefulGapCode(kind) {
          const source = calcSourceStem();
          let panel = document.getElementById('arGapCodePanel');
          if (panel && panel.style.display !== 'none' && panel.getAttribute('data-gap-kind') === kind) {
            hideUsefulGapCode();
            return;
          }
          if (!panel) {
            panel = document.createElement('div');
            panel.id = 'arGapCodePanel';
            panel.style.position = 'fixed';
            panel.style.right = '22px';
            panel.style.top = '88px';
            panel.style.width = '520px';
            panel.style.maxWidth = 'calc(100vw - 44px)';
            panel.style.background = 'rgba(255,255,255,0.98)';
            panel.style.border = '1px solid #cbd5e1';
            panel.style.borderRadius = '10px';
            panel.style.boxShadow = '0 12px 32px rgba(15,23,42,0.24)';
            panel.style.zIndex = '20004';
            panel.style.fontFamily = 'system-ui,-apple-system,Segoe UI,sans-serif';
            panel.style.fontSize = '13px';
            panel.innerHTML = '<div class="ar-panel-head"><span>Useful GAP code</span><button class="ar-soft-close" data-gap-close="1" title="Close GAP code panel">Close</button></div><div id="arGapCodeBody" style="padding:10px;"></div>';
            document.body.appendChild(panel);
            makeFloatingWindow(panel, panel.querySelector('.ar-panel-head'), { minWidth: 360, minHeight: 260 });
            panel.addEventListener('click', (e) => {
              if (e.target && e.target.getAttribute('data-gap-close')) hideUsefulGapCode();
            });
          }
          panel.style.display = 'block';
          panel.setAttribute('data-gap-kind', kind);
          const script = usefulGapCode(kind);
          const names = { generate: 'generate_this_quiver', gen: 'find_gen', cogen: 'find_cogen', extclosure: 'extension_closure', extbasis: 'ext_basis_sequences' };
          const body = panel.querySelector('#arGapCodeBody');
          appendGapCodeBox(body, script, source + '_' + (names[kind] || 'gap_code') + '.g', 'Click copy or edit the GAP code below.');
          if (typeof refreshFolderControlStates === 'function') refreshFolderControlStates();
        }
        function appendGapCodeBox(out, script, filename, caption) {
          out.innerHTML = '';
          const textarea = document.createElement('textarea');
          textarea.value = script;
          textarea.style.width = '100%';
          textarea.style.height = '180px';
          textarea.style.boxSizing = 'border-box';
          textarea.style.fontFamily = 'monospace';
          textarea.style.fontSize = '12px';
          const buttons = document.createElement('div');
          buttons.style.display = 'flex';
          buttons.style.gap = '8px';
          buttons.style.marginBottom = '6px';
          const copyBtn = document.createElement('button');
          copyBtn.textContent = 'Copy GAP code';
          copyBtn.addEventListener('click', async () => {
            textarea.focus();
            textarea.select();
            try {
              await navigator.clipboard.writeText(script);
              copyBtn.textContent = 'Copied';
            } catch (e) {
              document.execCommand('copy');
              copyBtn.textContent = 'Copied';
            }
          });
          const downloadBtn = document.createElement('button');
          downloadBtn.textContent = 'Download .g';
          downloadBtn.addEventListener('click', () => {
            const blob = new Blob([script], { type: 'text/plain;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
          });
          buttons.appendChild(copyBtn);
          buttons.appendChild(downloadBtn);
          out.appendChild(document.createTextNode(caption || 'Generated GAP/QPA code.'));
          out.appendChild(document.createElement('br'));
          out.appendChild(buttons);
          out.appendChild(textarea);
        }
        function setCalculatorControlActive(active) {
          if (!folderPanel) return;
          const btn = folderPanel.querySelector('button[data-action="calculator"]');
          if (btn) btn.classList.toggle('ar-control-active', !!active);
        }

        function hideCalculator() {
          if (calculatorPanel) calculatorPanel.style.display = 'none';
          clearCalculatorHighlight();
          setCalculatorControlActive(false);
        }

        function isCalculatorVisible() {
          return !!(calculatorPanel && calculatorPanel.style.display !== 'none');
        }

        function showCalculator() {
          if (!calculatorPanel) {
            calculatorPanel = document.createElement('div');
            calculatorPanel.id = 'arCalculatorPanel';
            calculatorPanel.style.position = 'fixed';
            calculatorPanel.style.right = '18px';
            calculatorPanel.style.bottom = '18px';
            calculatorPanel.style.width = '390px';
            calculatorPanel.style.background = 'rgba(255,255,255,0.98)';
            calculatorPanel.style.border = '1px solid #cbd5e1';
            calculatorPanel.style.borderRadius = '10px';
            calculatorPanel.style.boxShadow = '0 12px 32px rgba(15,23,42,0.24)';
            calculatorPanel.style.zIndex = '20002';
            calculatorPanel.style.fontFamily = 'system-ui,-apple-system,Segoe UI,sans-serif';
            calculatorPanel.style.fontSize = '13px';
            calculatorPanel.innerHTML = `
              <div style="display:flex; align-items:center; justify-content:space-between; padding:8px 10px; border-bottom:1px solid #e5e7eb; background:#f8fafc; border-radius:10px 10px 0 0; font-weight:650;">
                <span>Calculator</span><button id="calcClose" style="border:0; background:transparent; font-size:18px; cursor:pointer;">×</button>
              </div>
              <div style="padding:10px; display:grid; gap:8px;">
                <label>Function <select id="calcOp" style="width:100%;"><option value="ExtK">dim Ext^k(A,B)</option><option value="ExtKperp">ker Ext^k(A,-)</option><option value="perpExtK">ker Ext^k(-,B)</option><option value="Syzygy">Ω^n(A)</option><option value="Cosyzygy">Σ^n(A)</option><option value="Radical">Rad^n(A)</option><option value="Coradical">Corad^n(A)</option></select></label>
                <label id="calcKLabel">k / n <input id="calcK" style="width:100%; box-sizing:border-box;" value="0" /></label>
                <label id="calcALabel">A labels <span title="calculator color for A" style="display:inline-block;width:0.85em;height:0.85em;vertical-align:-0.08em;margin-left:0.2em;border:1px solid #64748b;border-radius:2px;background:#bfdbfe;"></span><input id="calcA" style="width:100%; box-sizing:border-box;" placeholder="e.g. 1 2 5 or all" /></label>
                <label id="calcBLabel">B labels <span title="calculator color for B" style="display:inline-block;width:0.85em;height:0.85em;vertical-align:-0.08em;margin-left:0.2em;border:1px solid #64748b;border-radius:2px;background:#fde68a;"></span><input id="calcB" style="width:100%; box-sizing:border-box;" placeholder="e.g. 1 2 5 or all" /></label>
                <div id="calcHint" style="color:#475569; font-size:12px;"></div>
                <div style="display:flex; gap:8px;">
                  <button id="calcRun" style="flex:1; padding:6px 10px; border:1px solid #2563eb; background:#dbeafe; color:#1d4ed8; border-radius:6px; cursor:pointer; font-weight:650;">Run</button>
                  <button id="calcRunGap" style="flex:1; padding:6px 10px; border:1px solid #16a34a; background:#dcfce7; color:#166534; border-radius:6px; cursor:pointer; font-weight:650;">Run with GAP</button>
                </div>
                <div style="color:#475569; font-size:12px;">Inputs/outputs use node label numbers. Empty input means ∅; type all or * for all modules. Calculator coloring uses at most two internal split-fill colors and does not change borders. Run with GAP shows copyable GAP/QPA code and can download a .g file.</div>
                <div style="font-weight:600; font-size:12px;">Result <span title="calculator color for result set" style="display:inline-block;width:0.85em;height:0.85em;vertical-align:-0.08em;margin-left:0.2em;border:1px solid #64748b;border-radius:2px;background:#bbf7d0;"></span></div>
                <pre id="calcOutput" style="min-height:48px; max-height:180px; overflow:auto; white-space:pre-wrap; margin:0; padding:8px; background:#f8fafc; border:1px solid #e5e7eb; border-radius:6px;"></pre>
              </div>`;
            document.body.appendChild(calculatorPanel);
            const calculatorHead = calculatorPanel.firstElementChild;
            if (calculatorHead) calculatorHead.style.cursor = 'move';
            makeFloatingWindow(calculatorPanel, calculatorHead, {
              minWidth: 300,
              minHeight: 260,
              onResize: (panel, width, height) => {
                const out = panel.querySelector('#calcOutput');
                if (out) out.style.maxHeight = Math.max(80, height - 270) + 'px';
              }
            });
            const updateCalculatorFields = () => {
              const op = calculatorPanel.querySelector('#calcOp').value;
              const aLabel = calculatorPanel.querySelector('#calcALabel');
              const bLabel = calculatorPanel.querySelector('#calcBLabel');
              const kLabel = calculatorPanel.querySelector('#calcKLabel');
              const hint = calculatorPanel.querySelector('#calcHint');
              const usesA = ['ExtK','ExtKperp','Syzygy','Cosyzygy','Radical','Coradical'].includes(op);
              const usesB = ['ExtK','perpExtK'].includes(op);
              const usesK = ['ExtK','ExtKperp','perpExtK','Syzygy','Cosyzygy','Radical','Coradical'].includes(op);
              aLabel.style.display = usesA ? 'block' : 'none';
              bLabel.style.display = usesB ? 'block' : 'none';
              kLabel.style.display = usesK ? 'block' : 'none';
              if (op === 'ExtK') hint.textContent = 'Computes Sum dim Ext^k(A_i, B_j); k=0 is Hom, k=1 is Ext^1, k>=2 uses syzygy and Ext^1 data.';
              else if (op === 'ExtKperp') hint.textContent = 'Input A only; returns modules X with Ext^k(A_i, X)=0 for all A_i.';
              else if (op === 'perpExtK') hint.textContent = 'Input B only; returns modules X with Ext^k(X, B_j)=0 for all B_j.';
              else if (op === 'Syzygy') hint.textContent = 'Input exactly one indecomposable module label in A; returns Ω^n(A), computed by fast powering the syzygy quiver. Multiplicities are shown as powers.';
              else if (op === 'Cosyzygy') hint.textContent = 'Input exactly one indecomposable module label in A; returns Σ^n(A), computed by fast powering the cosyzygy quiver. Multiplicities are shown as powers.';
              else if (op === 'Radical') hint.textContent = 'Input exactly one indecomposable module label in A; returns Rad^n(A), computed by fast powering the radical quiver. Multiplicities are shown as powers.';
              else if (op === 'Coradical') hint.textContent = 'Input exactly one indecomposable module label in A; returns Corad^n(A), computed by fast powering the coradical quiver. Multiplicities are shown as powers.';
              else hint.textContent = 'Inputs/outputs use node label numbers.';
            };
            calculatorPanel.querySelector('#calcOp').addEventListener('change', () => {
              updateCalculatorFields();
              calcRunOperation();
            });
            ['calcA','calcB','calcK'].forEach(id => {
              const el = calculatorPanel.querySelector('#' + id);
              if (el) el.addEventListener('input', calcRunOperation);
            });
            updateCalculatorFields();
            calculatorPanel.querySelector('#calcClose').addEventListener('click', hideCalculator);
            calculatorPanel.querySelector('#calcRun').addEventListener('click', calcRunOperation);
            calculatorPanel.querySelector('#calcRunGap').addEventListener('click', calcRunWithGap);
          }
          calculatorPanel.style.display = 'block';
          setCalculatorControlActive(true);
        }

        function toggleCalculator() {
          if (isCalculatorVisible()) hideCalculator();
          else showCalculator();
        }

        let folderPanel = null;
        function refreshFolderControlStates() {
          if (!folderPanel) return;
          folderPanel.querySelectorAll('button[data-toggle]').forEach(btn => {
            const id = btn.getAttribute('data-toggle');
            const el = document.getElementById(id);
            btn.classList.toggle('ar-control-active', !!(el && el.checked));
          });
          folderPanel.querySelectorAll('button[data-click]').forEach(btn => {
            const id = btn.getAttribute('data-click');
            btn.classList.toggle('ar-control-active', activeModuleClasses.has(id));
          });
          const gapPanel = document.getElementById('arGapCodePanel');
          const activeGapKind = gapPanel && gapPanel.style.display !== 'none' ? gapPanel.getAttribute('data-gap-kind') : null;
          folderPanel.querySelectorAll('button[data-gap-code]').forEach(btn => {
            btn.classList.toggle('ar-control-active', !!activeGapKind && btn.getAttribute('data-gap-code') === activeGapKind);
          });
        }

        function createFolderPanel() {
          if (folderPanel) return;
          folderPanel = document.createElement('div');
          folderPanel.id = 'arFolderPanel';
          folderPanel.innerHTML = `
            <div class="ar-panel-head"><span>Controls</span><button class="ar-panel-close" data-action="close-panel">×</button></div>
            <details open><summary>View</summary><div class="ar-folder-body">
              <button data-toggle="pdToggle">PD</button>
              <button data-toggle="idToggle">ID</button>
              <button data-toggle="topToggle">Top</button>
              <button data-toggle="socToggle">Soc</button>
              <button data-toggle="borderToggle">Borders</button>
            </div></details>
            <details open><summary>Quivers</summary><div class="ar-folder-body">
              <button data-toggle="irrToggle">AR irreducible arrows</button>
              <button data-toggle="trToggle">Translation quiver τ</button>
              <button data-toggle="syzToggle">Syzygy quiver</button>
              <button data-toggle="cosyzToggle">Cosyzygy quiver</button>
              <button data-toggle="radToggle">Radical quiver</button>
              <button data-toggle="coradToggle">Coradical quiver</button>
              <button data-toggle="homToggle">Hom dimension quiver</button>
              <button data-toggle="extToggle">Ext dimension quiver</button>
              <button data-toggle="quiverToggle">Original quiver Q</button>
            </div></details>
            <details><summary>Modules</summary><div class="ar-folder-body">
              <button data-click="torsBtn">Torsionless (${torsionlessIds.length})</button>
              <button data-click="reflBtn">Reflexive (${reflexiveIds.length})</button>
              <button data-click="gpBtn">Gorenstein projective (${gorensteinProjectiveIds.length})</button>
              <button data-click="giBtn">Gorenstein injective (${gorensteinInjectiveIds.length})</button>
            </div></details>
            <details><summary>Classes</summary><div class="ar-folder-body">
              <button data-list="torsionPairToggle|torsionPairList|Torsion classes">Torsion classes</button>
              <button data-list="cotorsionPairToggle|cotorsionPairList|Cotorsion classes">Cotorsion classes</button>
            </div></details>
            <details><summary>Tilting</summary><div class="ar-folder-body">
              <button data-list="tiltingToggle|tiltingList|Tilting modules">Tilting modules</button>
              <button data-list="supportTauToggle|supportTauList|Support τ-tilting modules">Support τ-tilting</button>
              <button data-list="almostSupportTauToggle|almostSupportTauList|Almost support τ-tilting modules">Almost support τ-tilting</button>
            </div></details>
            <details><summary>GAP codes</summary><div class="ar-folder-body">
              <button data-gap-code="generate">Generate this quiver</button>
              <button data-gap-code="gen">Find gen(-)</button>
              <button data-gap-code="cogen">Find cogen(-)</button>
              <button data-gap-code="extclosure">Extension closure</button>
              <button data-gap-code="extbasis">Ext basis sequences</button>
            </div></details>
            <details><summary>Tools</summary><div class="ar-folder-body">
              <button data-action="calculator">Calculator</button>
              <button data-action="export-tex">Export AR quiver to TeX</button>
              <button data-action="display-code">Display code</button>
              <button data-action="legend">Color legend</button>
            </div></details>
          `;
          document.body.appendChild(folderPanel);
          makeFloatingWindow(folderPanel, folderPanel.querySelector('.ar-panel-head'), { minWidth: 220, minHeight: 180 });
          folderPanel.addEventListener('click', handleMenuAction);
          refreshFolderControlStates();
        }

        function texBackslash() {
          return String.fromCharCode(92);
        }

        function escapeTeXText(value) {
          const slash = texBackslash();
          const specials = '{}_$%&#' + slash;
          const text = String(value == null ? '' : value);
          let out = '';
          for (let i = 0; i < text.length; i += 1) {
            const ch = text.charAt(i);
            if (specials.indexOf(ch) >= 0) out += slash + ch;
            else if (ch === '^') out += slash + 'textasciicircum{}';
            else if (ch === '~') out += slash + 'textasciitilde{}';
            else out += ch;
          }
          return out;
        }

        function splitWords(row) {
          return String(row).trim().split(' ').map(x => x.trim()).filter(x => x.length > 0);
        }

        function labelToSmallMatrix(label) {
          const slash = texBackslash();
          const raw = String(label == null ? '' : label).trim();
          if (!raw) return '{}';
          let rows = raw.split(String.fromCharCode(10)).map(r => r.trim()).filter(r => r.length > 0);
          if (rows.length === 1 && rows[0].charAt(0) === '[' && rows[0].charAt(rows[0].length - 1) === ']') {
            rows = [rows[0].substring(1, rows[0].length - 1).split(',').map(x => x.trim()).join(' ')];
          }
          const texRows = rows.map(row => {
            let cells = splitWords(row);
            if (cells.length === 0) cells = ['0'];
            return cells.map(escapeTeXText).join(' & ');
          });
          return '{' + slash + 'begin{smallmatrix}' + texRows.join(' ' + slash + slash + ' ') + slash + 'end{smallmatrix}}';
        }

        function clusterCoordinate(values, gap) {
          const sorted = values.slice().sort((a, b) => a - b);
          const centers = [];
          sorted.forEach(v => {
            if (!centers.length || Math.abs(v - centers[centers.length - 1]) > gap) {
              centers.push(v);
            } else {
              const last = centers.length - 1;
              centers[last] = (centers[last] + v) / 2;
            }
          });
          return centers;
        }

        function nearestIndex(values, value) {
          let best = 0;
          let bestDist = Infinity;
          values.forEach((v, i) => {
            const d = Math.abs(v - value);
            if (d < bestDist) {
              best = i;
              bestDist = d;
            }
          });
          return best;
        }

        function xyDirection(fromCell, toCell) {
          const dr = toCell.row - fromCell.row;
          const dc = toCell.col - fromCell.col;
          if (dr === 0 && dc === 0) return '@(ul,ur)[]';
          let dir = '';
          if (dr > 0) dir += 'd'.repeat(dr);
          if (dr < 0) dir += 'u'.repeat(-dr);
          if (dc > 0) dir += 'r'.repeat(dc);
          if (dc < 0) dir += 'l'.repeat(-dc);
          return '[' + dir + ']';
        }

        function isVisibleEdgeForExport(edge) {
          return !edge.hidden && (isBlackEdge(edge) || isTranslationEdge(edge) || String(edge.id || '').startsWith('tr_'));
        }
        function nodeExportLabel(id, fallbackLabel) {
          const custom = customTexLabels.get(id) || customTexLabels.get(String(id));
          if (custom) return '{' + custom + '}';
          return labelToSmallMatrix(fallbackLabel);
        }

        function xyCurvePart(edge) {
          if (!edge || !edge.smooth || typeof edge.smooth !== 'object' || !edge.smooth.enabled) return '';
          const roundness = Number(edge.smooth.roundness || 0);
          if (!Number.isFinite(roundness) || roundness <= 0.005) return '';
          const amount = Math.max(0.25, Math.min(5, roundness * 3)).toFixed(2).replace(/\\.00$/, '').replace(/0$/, '');
          const type = edge.smooth.type || 'curvedCW';
          return type === 'curvedCCW' ? '@/_' + amount + 'pc/' : '@/^' + amount + 'pc/';
        }

        function xyArrow(edge, dir) {
          const slash = texBackslash();
          if (dir.indexOf('@(') === 0) {
            return (isTranslationEdge(edge) || String(edge.id || '').startsWith('tr_')) ? slash + 'ar@{-->}' + dir : slash + 'ar' + dir;
          }
          const curve = xyCurvePart(edge);
          const dashed = (isTranslationEdge(edge) || String(edge.id || '').startsWith('tr_')) ? '@{-->}' : '';
          return slash + 'ar' + curve + dashed + dir;
        }


        function exportCurrentARQuiverToXyMatrix() {
          const slash = texBackslash();
          const nodeIds = network.body.data.nodes.getIds().map(Number).filter(n => Number.isFinite(n));
          const positions = network.getPositions(nodeIds);
          const visibleNodeIds = nodeIds.filter(id => positions[id]);
          if (!visibleNodeIds.length) {
            alert('No nodes to export.');
            return '';
          }
          const xs = clusterCoordinate(visibleNodeIds.map(id => positions[id].x), Math.max(40, gridSize * 0.55));
          const ys = clusterCoordinate(visibleNodeIds.map(id => positions[id].y), Math.max(40, gridSize * 0.55));
          const cellById = new Map();
          const matrix = [];
          ys.forEach(() => matrix.push(xs.map(() => '')));
          visibleNodeIds.forEach(id => {
            const node = network.body.data.nodes.get(id);
            const row = nearestIndex(ys, positions[id].y);
            const col = nearestIndex(xs, positions[id].x);
            cellById.set(id, { row, col });
            const label = nodeExportLabel(id, node && node.label ? node.label : id);
            if (matrix[row][col]) matrix[row][col] += slash + '; ' + label;
            else matrix[row][col] = label;
          });
          const arrowsBySource = new Map();
          const edges = network.body.data.edges.get().filter(isVisibleEdgeForExport);
          edges.forEach(edge => {
            const from = Number(edge.from);
            const to = Number(edge.to);
            if (!cellById.has(from) || !cellById.has(to)) return;
            const fromCell = cellById.get(from);
            const toCell = cellById.get(to);
            const dir = xyDirection(fromCell, toCell);
            const arrow = xyArrow(edge, dir);
            const key = fromCell.row + ',' + fromCell.col;
            if (!arrowsBySource.has(key)) arrowsBySource.set(key, []);
            arrowsBySource.get(key).push(arrow);
          });
          for (let r = 0; r < matrix.length; r += 1) {
            for (let c = 0; c < matrix[r].length; c += 1) {
              const key = r + ',' + c;
              if (!matrix[r][c]) matrix[r][c] = '{}';
              if (arrowsBySource.has(key)) matrix[r][c] += ' ' + arrowsBySource.get(key).join(' ');
            }
          }
          const body = matrix.map(row => row.join(' & ')).join(' ' + slash + slash + String.fromCharCode(10));
          return slash + '[' + String.fromCharCode(10) + slash + 'xymatrix{' + String.fromCharCode(10) + body + String.fromCharCode(10) + '}' + String.fromCharCode(10) + slash + ']';
        }

        function exportCurrentARQuiverToTikZ() {
          const slash = texBackslash();
          const nodeIds = network.body.data.nodes.getIds().map(Number).filter(Number.isFinite).sort((a, b) => a - b);
          const positions = network.getPositions(nodeIds);
          const visibleNodeIds = nodeIds.filter(id => positions[id]);
          if (!visibleNodeIds.length) {
            alert('No nodes to export.');
            return '';
          }
          const xs = visibleNodeIds.map(id => positions[id].x);
          const ys = visibleNodeIds.map(id => positions[id].y);
          const minX = Math.min.apply(null, xs);
          const minY = Math.min.apply(null, ys);
          const coord = (value) => {
            const text = (Math.round(value * 100) / 100).toFixed(2).replace(/\\.00$/, '').replace(/(\\.\\d)0$/, '$1');
            return text === '-0' ? '0' : text;
          };
          const nodeName = (id) => 'M' + String(id).replace(/[^A-Za-z0-9]/g, '_');
          const lines = [];
          lines.push('% Requires: ' + slash + 'usepackage{tikz,amsmath}');
          lines.push(slash + '[');
          lines.push(slash + 'begin{tikzpicture}[>=stealth, every node/.style={inner sep=2pt}]');
          visibleNodeIds.forEach(id => {
            const node = network.body.data.nodes.get(id);
            const x = (positions[id].x - minX) / gridSize;
            const y = -(positions[id].y - minY) / gridSize;
            const label = nodeExportLabel(id, node && node.label ? node.label : id);
            lines.push('  ' + slash + 'node (' + nodeName(id) + ') at (' + coord(x) + ',' + coord(y) + ') {$' + label + '$};');
          });
          network.body.data.edges.get().filter(isVisibleEdgeForExport).forEach(edge => {
            const from = Number(edge.from);
            const to = Number(edge.to);
            if (!positions[from] || !positions[to]) return;
            const opts = ['->'];
            if (isTranslationEdge(edge) || String(edge.id || '').startsWith('tr_')) opts.push('dashed');
            if (isDimmedEdge(edge)) opts.push('gray');
            let path = '--';
            if (from === to) {
              path = 'to[loop above]';
            } else if (edge.smooth && typeof edge.smooth === 'object' && edge.smooth.enabled) {
              const roundness = Math.abs(Number(edge.smooth.roundness || 0));
              if (roundness > 0.005) {
                const angle = Math.max(8, Math.min(80, Math.round(roundness * 60)));
                const bend = (edge.smooth.type || 'curvedCW') === 'curvedCCW' ? 'bend left=' : 'bend right=';
                path = 'to[' + bend + angle + ']';
              }
            }
            if (path === '--') lines.push('  ' + slash + 'draw[' + opts.join(',') + '] (' + nodeName(from) + ') -- (' + nodeName(to) + ');');
            else lines.push('  ' + slash + 'draw[' + opts.join(',') + '] (' + nodeName(from) + ') ' + path + ' (' + nodeName(to) + ');');
          });
          lines.push(slash + 'end{tikzpicture}');
          lines.push(slash + ']');
          return lines.join(String.fromCharCode(10));
        }

        let texExportMode = 'xy';

        function setTexExportMode(mode) {
          texExportMode = mode === 'tikz' ? 'tikz' : 'xy';
          const modal = document.getElementById('arTexExportModal');
          if (!modal) return;
          const output = texExportMode === 'tikz' ? exportCurrentARQuiverToTikZ() : exportCurrentARQuiverToXyMatrix();
          const ta = modal.querySelector('#arTexOutput');
          if (ta) ta.value = output;
          const title = modal.querySelector('#arTexExportTitle');
          if (title) title.textContent = texExportMode === 'tikz' ? 'Export AR quiver to TeX / TikZ' : 'Export AR quiver to TeX / xymatrix';
          modal.querySelectorAll('button[data-tex-mode]').forEach(btn => {
            const active = btn.getAttribute('data-tex-mode') === texExportMode;
            btn.style.background = active ? '#dbeafe' : '';
            btn.style.fontWeight = active ? '700' : '';
          });
        }

        function showTexExport(mode) {
          let modal = document.getElementById('arTexExportModal');
          if (!modal) {
            modal = document.createElement('div');
            modal.id = 'arTexExportModal';
            modal.style.position = 'fixed';
            modal.style.left = '50%';
            modal.style.top = '50%';
            modal.style.transform = 'translate(-50%, -50%)';
            modal.style.width = '760px';
            modal.style.maxWidth = '92vw';
            modal.style.height = '520px';
            modal.style.maxHeight = '86vh';
            modal.style.background = 'white';
            modal.style.border = '1px solid #94a3b8';
            modal.style.borderRadius = '10px';
            modal.style.boxShadow = '0 18px 48px rgba(15,23,42,0.35)';
            modal.style.zIndex = '30000';
            modal.style.display = 'none';
            modal.innerHTML = '<div style="display:flex;align-items:center;justify-content:space-between;padding:9px 12px;border-bottom:1px solid #e5e7eb;background:#f8fafc;border-radius:10px 10px 0 0;font-family:system-ui,-apple-system,Segoe UI,sans-serif;font-size:13px;"><strong id="arTexExportTitle">Export AR quiver to TeX / xymatrix</strong><button id="arTexClose" style="border:0;background:transparent;font-size:20px;cursor:pointer;">×</button></div><div style="display:flex;gap:8px;padding:8px 10px;border-bottom:1px solid #e5e7eb;background:#fff;"><button data-tex-mode="xy">xymatrix</button><button data-tex-mode="tikz">TikZ</button></div><textarea id="arTexOutput" style="box-sizing:border-box;width:100%;height:360px;border:0;border-bottom:1px solid #e5e7eb;padding:10px;font-family:monospace;font-size:12px;white-space:pre;"></textarea><div style="display:flex;gap:8px;justify-content:flex-end;padding:9px 12px;"><button id="arTexCopy">Copy</button><button id="arTexDownload">Download .tex</button></div>';
            document.body.appendChild(modal);
            modal.querySelector('#arTexClose').addEventListener('click', () => { modal.style.display = 'none'; });
            modal.querySelectorAll('button[data-tex-mode]').forEach(btn => {
              btn.addEventListener('click', () => setTexExportMode(btn.getAttribute('data-tex-mode')));
            });
            modal.querySelector('#arTexCopy').addEventListener('click', () => {
              const ta = modal.querySelector('#arTexOutput');
              ta.focus();
              ta.select();
              document.execCommand('copy');
            });
            modal.querySelector('#arTexDownload').addEventListener('click', () => {
              const ta = modal.querySelector('#arTexOutput');
              const blob = new Blob([ta.value], { type: 'text/x-tex;charset=utf-8' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = texExportMode === 'tikz' ? 'ar-quiver-tikz.tex' : 'ar-quiver-xymatrix.tex';
              document.body.appendChild(a);
              a.click();
              document.body.removeChild(a);
              URL.revokeObjectURL(url);
            });
          }
          setTexExportMode(mode);
          modal.style.display = 'block';
        }

        const displayCodeAlphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_';
        const displayCodeZero = 32;
        const displayCurveStep = 0.1;

        function encodeDisplaySigned(value) {
          const n = Math.round(Number(value));
          const idx = n + displayCodeZero;
          if (!Number.isInteger(n) || idx < 0 || idx >= displayCodeAlphabet.length) throw new Error('Display offset out of range: ' + value);
          return displayCodeAlphabet.charAt(idx);
        }

        function decodeDisplaySigned(ch) {
          const idx = displayCodeAlphabet.indexOf(ch);
          if (idx < 0) throw new Error('Invalid display code character: ' + ch);
          return idx - displayCodeZero;
        }

        function encodeDisplayUnsigned2(value) {
          const n = Math.round(Number(value));
          if (!Number.isInteger(n) || n < 0 || n >= 4096) throw new Error('Display index out of range: ' + value);
          return displayCodeAlphabet.charAt(Math.floor(n / 64)) + displayCodeAlphabet.charAt(n % 64);
        }

        function decodeDisplayUnsigned2(text, offset) {
          const hi = displayCodeAlphabet.indexOf(text.charAt(offset));
          const lo = displayCodeAlphabet.indexOf(text.charAt(offset + 1));
          if (hi < 0 || lo < 0) throw new Error('Invalid display index at character ' + offset);
          return hi * 64 + lo;
        }

        function curveStepFromSmooth(smooth) {
          if (!smooth || typeof smooth !== 'object' || !smooth.enabled) return 0;
          const round = Number(smooth.roundness || 0);
          if (!Number.isFinite(round) || round <= 0.005) return 0;
          const signed = (smooth.type || 'curvedCW') === 'curvedCCW' ? -round : round;
          return Math.round(signed / displayCurveStep);
        }

        function smoothFromCurveStep(step) {
          if (!step) return false;
          return {
            enabled: true,
            type: step < 0 ? 'curvedCCW' : 'curvedCW',
            roundness: Math.abs(step) * displayCurveStep
          };
        }

        function exportDisplayCodeText() {
          const ids = network.body.data.nodes.getIds().map(Number).filter(Number.isFinite).sort((a, b) => a - b);
          if (!ids.length) return 'ARQ2..';
          const positions = network.getPositions(ids);
          const anchor = positions[ids[0]];
          if (!anchor) throw new Error('Cannot read anchor node position.');
          let nodePart = '';
          ids.slice(1).forEach(id => {
            const p = positions[id];
            if (!p) throw new Error('Cannot read node position: ' + id);
            nodePart += encodeDisplaySigned((p.x - anchor.x) / gridSize) + encodeDisplaySigned((p.y - anchor.y) / gridSize);
          });
          let curvePart = '';
          let dimPart = '';
          network.body.data.edges.get().forEach((edge, index) => {
            const step = curveStepFromSmooth(edge.smooth);
            if (step) curvePart += encodeDisplayUnsigned2(index) + encodeDisplaySigned(step);
            if (isDimmableAREdge(edge) && isDimmedEdge(edge)) dimPart += encodeDisplayUnsigned2(index);
          });
          return 'ARQ3.' + nodePart + '.' + curvePart + '.' + dimPart;
        }

        function normalizeDisplayCodeInput(text) {
          const raw = String(text || '').trim();
          const direct = raw.match(/ARQ[23]\\.[0-9A-Za-z\\-_]*\\.[0-9A-Za-z\\-_]*(?:\\.[0-9A-Za-z\\-_]*)?/);
          if (direct) return direct[0];
          return raw.replace(/[`\\s]/g, '');
        }

        function applyDisplayCodeText(text) {
          const raw = normalizeDisplayCodeInput(text);
          try {
            const version = raw.startsWith('ARQ3.') ? 3 : (raw.startsWith('ARQ2.') ? 2 : 0);
            if (!version) throw new Error('Display code must start with ARQ2 or ARQ3.');
            const parts = raw.slice(5).split('.');
            if (version === 2 && parts.length !== 2) throw new Error('ARQ2 display code must have node and curve sections.');
            if (version === 3 && parts.length !== 3) throw new Error('ARQ3 display code must have node, curve, and dimmed-arrow sections.');
            const nodePart = parts[0];
            const curvePart = parts[1];
            const dimPart = version === 3 ? parts[2] : '';
            const ids = network.body.data.nodes.getIds().map(Number).filter(Number.isFinite).sort((a, b) => a - b);
            if (nodePart.length % 2 !== 0) throw new Error('Node section length mismatch.');
            if (curvePart.length % 3 !== 0) throw new Error('Curve section length mismatch.');
            if (dimPart.length % 2 !== 0) throw new Error('Dimmed-arrow section length mismatch.');
            const positions = network.getPositions(ids);
            const anchor = ids.length ? positions[ids[0]] : null;
            if (anchor) {
              const nodePairs = Math.min(ids.length - 1, nodePart.length / 2);
              for (let i = 1; i <= nodePairs; i += 1) {
                const off = (i - 1) * 2;
                const dx = decodeDisplaySigned(nodePart.charAt(off));
                const dy = decodeDisplaySigned(nodePart.charAt(off + 1));
                network.moveNode(ids[i], anchor.x + dx * gridSize, anchor.y + dy * gridSize);
              }
            }
            edgeCurveMemory.clear();
            const edges = network.body.data.edges.get();
            const updates = edges
              .filter(edge => edge.id !== undefined && edge.id !== null)
              .map(edge => ({ id: edge.id, smooth: false }));
            for (let i = 0; i < curvePart.length; i += 3) {
              const index = decodeDisplayUnsigned2(curvePart, i);
              const step = decodeDisplaySigned(curvePart.charAt(i + 2));
              if (index < 0 || index >= edges.length) continue;
              const edge = edges[index];
              if (edge.id === undefined || edge.id === null) continue;
              const smooth = smoothFromCurveStep(step);
              edgeCurveMemory.set(String(edge.id), smooth);
              updates.push({ id: edge.id, smooth });
            }
            edges.forEach(edge => {
              if (!isDimmableAREdge(edge) || edge.id === undefined || edge.id === null) return;
              if (String(edge.id || '').startsWith('tr_') || isGoldenEdge(edge)) {
                updates.push({ id: edge.id, color: { color: 'gold' } });
              } else {
                updates.push({ id: edge.id, color: { color: '#000000' } });
              }
            });
            for (let i = 0; i < dimPart.length; i += 2) {
              const index = decodeDisplayUnsigned2(dimPart, i);
              if (index < 0 || index >= edges.length) continue;
              const edge = edges[index];
              if (!isDimmableAREdge(edge) || edge.id === undefined || edge.id === null) continue;
              const dimmedColor = (String(edge.id || '').startsWith('tr_') || isGoldenEdge(edge)) ? '#ffe9a6' : '#cccccc';
              updates.push({ id: edge.id, color: { color: dimmedColor } });
            }
            if (updates.length) network.body.data.edges.update(updates);
            network.redraw();
            if (typeof updateAllFloatingLabels === 'function') updateAllFloatingLabels();
            snapshot();
            return true;
          } catch (err) {
            alert('Invalid display code: ' + (err && err.message ? err.message : String(err)));
            return false;
          }
        }

        function showDisplayCodeModal() {
          let modal = document.getElementById('arDisplayCodeModal');
          if (!modal) {
            modal = document.createElement('div');
            modal.id = 'arDisplayCodeModal';
            modal.style.position = 'fixed';
            modal.style.left = '50%';
            modal.style.top = '50%';
            modal.style.transform = 'translate(-50%, -50%)';
            modal.style.width = '760px';
            modal.style.maxWidth = '92vw';
            modal.style.height = '520px';
            modal.style.maxHeight = '86vh';
            modal.style.background = 'white';
            modal.style.border = '1px solid #94a3b8';
            modal.style.borderRadius = '10px';
            modal.style.boxShadow = '0 18px 48px rgba(15,23,42,0.35)';
            modal.style.zIndex = '30000';
            modal.style.display = 'none';
            modal.innerHTML = '<div style="display:flex;align-items:center;justify-content:space-between;padding:9px 12px;border-bottom:1px solid #e5e7eb;background:#f8fafc;border-radius:10px 10px 0 0;font-family:system-ui,-apple-system,Segoe UI,sans-serif;font-size:13px;"><strong>Display code: compact node positions, arrow curves, and dimmed arrows</strong><button id="arDisplayCodeClose" style="border:0;background:transparent;font-size:20px;cursor:pointer;">×</button></div><textarea id="arDisplayCodeText" style="box-sizing:border-box;width:100%;height:400px;border:0;border-bottom:1px solid #e5e7eb;padding:10px;font-family:monospace;font-size:12px;white-space:pre-wrap;word-break:break-all;"></textarea><div style="display:flex;gap:8px;justify-content:flex-end;padding:9px 12px;"><button id="arDisplayCodeRefresh">Refresh from current display</button><button id="arDisplayCodeApply">Apply code</button><button id="arDisplayCodeCopy">Copy</button><button id="arDisplayCodeDownload">Download .txt</button></div>';
            document.body.appendChild(modal);
            modal.querySelector('#arDisplayCodeClose').addEventListener('click', () => { modal.style.display = 'none'; });
            modal.querySelector('#arDisplayCodeRefresh').addEventListener('click', () => { modal.querySelector('#arDisplayCodeText').value = exportDisplayCodeText(); });
            modal.querySelector('#arDisplayCodeApply').addEventListener('click', () => {
              if (applyDisplayCodeText(modal.querySelector('#arDisplayCodeText').value)) alert('Display code applied.');
            });
            modal.querySelector('#arDisplayCodeCopy').addEventListener('click', () => {
              const ta = modal.querySelector('#arDisplayCodeText');
              ta.focus();
              ta.select();
              document.execCommand('copy');
            });
            modal.querySelector('#arDisplayCodeDownload').addEventListener('click', () => {
              const ta = modal.querySelector('#arDisplayCodeText');
              const blob = new Blob([ta.value], { type: 'text/plain;charset=utf-8' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = 'ar-quiver-display-code.txt';
              document.body.appendChild(a);
              a.click();
              document.body.removeChild(a);
              URL.revokeObjectURL(url);
            });
          }
          modal.querySelector('#arDisplayCodeText').value = exportDisplayCodeText();
          modal.style.display = 'block';
        }

        function showColorLegend() {
          let modal = document.getElementById('arColorLegendModal');
          if (!modal) {
            const row = (label, color, note, borderColor) => '<div style="display:flex;align-items:center;gap:6px;margin:2px 0;"><span style="display:inline-block;width:0.95em;height:0.95em;border:2px solid ' + (borderColor || '#64748b') + ';border-radius:2px;background:' + color + ';"></span><span><strong>' + label + '</strong>' + (note ? ' — ' + note : '') + '</span></div>';
            const section = (title, rows) => '<section style="margin:8px 0;"><div style="font-weight:700;color:#0f172a;margin-bottom:3px;">' + title + '</div>' + rows.join('') + '</section>';
            modal = document.createElement('div');
            modal.id = 'arColorLegendModal';
            modal.style.position = 'fixed';
            modal.style.left = '50%';
            modal.style.top = '50%';
            modal.style.transform = 'translate(-50%, -50%)';
            modal.style.width = '460px';
            modal.style.maxWidth = '92vw';
            modal.style.maxHeight = '86vh';
            modal.style.overflow = 'auto';
            modal.style.background = 'white';
            modal.style.border = '1px solid #94a3b8';
            modal.style.borderRadius = '10px';
            modal.style.boxShadow = '0 18px 48px rgba(15,23,42,0.35)';
            modal.style.zIndex = '30000';
            modal.style.display = 'none';
            modal.style.fontFamily = 'system-ui,-apple-system,Segoe UI,sans-serif';
            modal.style.fontSize = '13px';
            modal.innerHTML = '<div style="position:sticky;top:0;z-index:1;display:flex;align-items:center;justify-content:space-between;padding:9px 12px;border-bottom:1px solid #e5e7eb;background:#f8fafc;border-radius:10px 10px 0 0;"><strong>Color legend</strong><button id="arLegendClose" style="border:0;background:transparent;font-size:20px;cursor:pointer;">×</button></div>' +
              '<div style="padding:10px 12px;">' +
              section('Node borders', [
                row('blue', 'white', 'projective', 'blue'),
                row('red', 'white', 'injective', 'red'),
                row('purple', 'white', 'projective-injective', 'purple')
              ]) +
              section('Module class highlights', [
                row('cyan', '#fff7cc', 'torsionless module', '#0ea5e9'),
                row('purple', '#fff7cc', 'reflexive module', '#8b5cf6'),
                row('green', '#fff7cc', 'Gorenstein projective module', '#16a34a'),
                row('red', '#fff7cc', 'Gorenstein injective module', '#dc2626')
              ]) +
              section('Edges', [
                row('black', 'black', 'AR irreducible arrow'),
                row('gold', 'gold', 'τM ← M'),
                row('pink', 'pink', 'M → N if N is a summand of ΩM'),
                row('green', '#22c55e', 'M → N if N is a summand of ΣM'),
                row('cyan', '#0ea5e9', 'M → N if N is a summand of Rad(M)'),
                row('purple', '#a855f7', 'M → N if N is a summand of Corad(M)'),
                row('brown', '#8b5a2b', 'M → N if dim Hom(M,N) = k'),
                row('red', 'red', 'M → N if dim Ext¹(M,N) = k'),
                row('light gray', '#d1d5db', 'dimmed irreducible arrow')
              ]) +
              section('(co)torsion and (tau) tilting', [
                row('T', '#ffe1c7', 'torsion class'),
                row('F', '#d9f2d9', 'torsion-free class'),
                row('L', '#b5b5b5', 'tilting module L'),
                row('left', '#93c5fd', 'cotorsion left class'),
                row('right', '#fca5a5', 'cotorsion right class'),
                row('P', '#dbeafe', 'support τ-tilting projective part'),
                row('M', '#b5b5b5', 'support τ-tilting module part')
              ]) +
              section('calculator', [
                row('A', '#bfdbfe', 'input A'),
                row('B', '#fde68a', 'input B'),
                row('result', '#bbf7d0', 'output class')
              ]) +
              section('floating labels', [
                row('pd', 'rgba(219,234,254,0.96)', 'projective dimension'),
                row('id', 'rgba(224,242,254,0.96)', 'injective dimension'),
                row('top', 'rgba(240,253,244,0.96)', 'top'),
                row('soc', 'rgba(255,247,237,0.96)', 'socle')
              ]) + '</div>';
            document.body.appendChild(modal);
            const head = modal.firstElementChild;
            if (head) {
              head.style.cursor = 'move';
              head.addEventListener('mousedown', (event) => {
                if (event.target.closest('button')) return;
                const rect = modal.getBoundingClientRect();
                modal.style.left = rect.left + 'px';
                modal.style.top = rect.top + 'px';
                modal.style.transform = 'none';
                const startX = event.clientX;
                const startY = event.clientY;
                const startLeft = rect.left;
                const startTop = rect.top;
                const onMove = (moveEvent) => {
                  modal.style.left = Math.max(0, Math.min(window.innerWidth - 60, startLeft + moveEvent.clientX - startX)) + 'px';
                  modal.style.top = Math.max(0, Math.min(window.innerHeight - 40, startTop + moveEvent.clientY - startY)) + 'px';
                };
                const onUp = () => {
                  document.removeEventListener('mousemove', onMove);
                  document.removeEventListener('mouseup', onUp);
                };
                document.addEventListener('mousemove', onMove);
                document.addEventListener('mouseup', onUp);
              });
            }
            modal.querySelector('#arLegendClose').addEventListener('click', () => { modal.style.display = 'none'; });
          }
          modal.style.display = 'block';
        }

        function handleMenuAction(event) {
          const btn = event.target.closest('button');
          if (!btn) return;
          const toggleId = btn.getAttribute('data-toggle');
          const clickId = btn.getAttribute('data-click');
          const listSpec = btn.getAttribute('data-list');
          const gapCodeKind = btn.getAttribute('data-gap-code');
          const action = btn.getAttribute('data-action');
          if (gapCodeKind) {
            showUsefulGapCode(gapCodeKind);
            refreshFolderControlStates();
            return;
          }
          if (toggleId) {
            if (toggleId === 'quiverToggle') {
              const el = document.getElementById(toggleId);
              const show = !(miniContainer && miniContainer.style.display === 'block');
              if (el) el.checked = show;
              toggleMiniQuiver(show);
              btn.classList.toggle('ar-control-active', show);
            } else {
              toggleCheckbox(toggleId);
              const toggleEl = document.getElementById(toggleId);
              btn.classList.toggle('ar-control-active', !!(toggleEl && toggleEl.checked));
            }
          }
          if (!toggleId && !clickId && !listSpec && action && action !== 'calculator') {
            btn.classList.add('ar-control-active');
            setTimeout(() => btn.classList.remove('ar-control-active'), 350);
          }
          if (clickId) {
            clickControl(clickId);
            if (['torsBtn','reflBtn','gpBtn','giBtn'].includes(clickId) && typeof activeModuleClasses !== 'undefined') {
              btn.classList.toggle('ar-control-active', activeModuleClasses.has(clickId));
            }
          }
          if (listSpec) {
            const parts = listSpec.split('|');
            const opened = showListInDrawer(parts[0], parts[1], parts[2]);
            clearListMenuActive();
            if (opened) btn.classList.add('ar-control-active');
          }
          if (action === 'close-panel') folderPanel.style.display = 'none';
          if (action === 'fit') network.fit({ animation: true });
          if (action === 'toggle-ui') toggleMenuUi();
          if (action === 'clear-colors') clearListColoring();
          if (action === 'undo' && typeof undo === 'function') undo();
          if (action === 'redo' && typeof redo === 'function') redo();
          if (action === 'calculator') toggleCalculator();
          if (action === 'export-tex') showTexExport('xy');
          if (action === 'display-code') showDisplayCodeModal();
          if (action === 'legend') showColorLegend();
        }

        function translateTexToken(token) {
          const greek = {
            alpha: 'α', beta: 'β', gamma: 'γ', delta: 'δ', epsilon: 'ε', varepsilon: 'ε', zeta: 'ζ', eta: 'η', theta: 'θ', vartheta: 'ϑ', iota: 'ι', kappa: 'κ', lambda: 'λ', mu: 'μ', nu: 'ν', xi: 'ξ', pi: 'π', varpi: 'ϖ', rho: 'ρ', varrho: 'ϱ', sigma: 'σ', varsigma: 'ς', tau: 'τ', upsilon: 'υ', phi: 'φ', varphi: 'ϕ', chi: 'χ', psi: 'ψ', omega: 'ω',
            Gamma: 'Γ', Delta: 'Δ', Theta: 'Θ', Lambda: 'Λ', Xi: 'Ξ', Pi: 'Π', Sigma: 'Σ', Upsilon: 'Υ', Phi: 'Φ', Psi: 'Ψ', Omega: 'Ω',
            ell: 'ℓ', infty: '∞', emptyset: '∅', varnothing: '∅'
          };
          const bs = String.fromCharCode(92);
          let text = String(token || '');
          Object.keys(greek).sort((a, b) => b.length - a.length).forEach(name => {
            text = text.split(bs + name).join(greek[name]);
          });
          return text.replace(/[{}]/g, '');
        }

        function texScript(text, mode) {
          const sub = { '0':'₀','1':'₁','2':'₂','3':'₃','4':'₄','5':'₅','6':'₆','7':'₇','8':'₈','9':'₉','+':'₊','-':'₋','=':'₌','(':'₍',')':'₎','a':'ₐ','e':'ₑ','h':'ₕ','i':'ᵢ','j':'ⱼ','k':'ₖ','l':'ₗ','m':'ₘ','n':'ₙ','o':'ₒ','p':'ₚ','r':'ᵣ','s':'ₛ','t':'ₜ','u':'ᵤ','v':'ᵥ','x':'ₓ' };
          const sup = { '0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹','+':'⁺','-':'⁻','=':'⁼','(':'⁽',')':'⁾','a':'ᵃ','b':'ᵇ','c':'ᶜ','d':'ᵈ','e':'ᵉ','f':'ᶠ','g':'ᵍ','h':'ʰ','i':'ⁱ','j':'ʲ','k':'ᵏ','l':'ˡ','m':'ᵐ','n':'ⁿ','o':'ᵒ','p':'ᵖ','r':'ʳ','s':'ˢ','t':'ᵗ','u':'ᵘ','v':'ᵛ','w':'ʷ','x':'ˣ','y':'ʸ','z':'ᶻ' };
          const map = mode === 'sub' ? sub : sup;
          return translateTexToken(text).split('').map(ch => map[ch] || ch).join('');
        }

        function stripTexCommandWithBraces(text, commandName) {
          const prefix = String.fromCharCode(92) + commandName + '{';
          let out = String(text || '');
          let idx = out.indexOf(prefix);
          while (idx !== -1) {
            const start = idx + prefix.length;
            const end = out.indexOf('}', start);
            if (end === -1) break;
            out = out.slice(0, idx) + out.slice(start, end) + out.slice(end + 1);
            idx = out.indexOf(prefix, idx + 1);
          }
          return out;
        }

        function latexToCanvasLabel(tex) {
          let out = String(tex == null ? '' : tex).trim();
          out = out.replace(/^\\$+|\\$+$/g, '');
          out = stripTexCommandWithBraces(out, 'text');
          out = stripTexCommandWithBraces(out, 'mathrm');
          out = stripTexCommandWithBraces(out, 'operatorname');
          out = out.replace(/_\\{([^}]*)\\}/g, (_, body) => texScript(body, 'sub'));
          out = out.replace(/\\^\\{([^}]*)\\}/g, (_, body) => texScript(body, 'sup'));
          out = out.replace(/_([A-Za-z0-9+=-])/g, (_, body) => texScript(body, 'sub'));
          out = out.replace(/\\^([A-Za-z0-9+=-])/g, (_, body) => texScript(body, 'sup'));
          out = translateTexToken(out);
          out = out.split(String.fromCharCode(92)).join('');
          return out;
        }

        function nodeCircleLabel(id) {
          const base = baseNodeStyles.get(id) || baseNodeStyles.get(String(id)) || baseNodeStyles.get(Number(id));
          if (nodeLabelMode === 'label') return String(id);
          if (nodeLabelMode === 'custom') {
            const custom = customTexLabels.get(id) || customTexLabels.get(String(id)) || customTexLabels.get(Number(id));
            return custom ? latexToCanvasLabel(custom) : (base ? base.label : String(id));
          }
          return base ? base.label : String(id);
        }

        function applyNodeLabelMode(mode) {
          nodeLabelMode = mode;
          const updates = network.body.data.nodes.get().map(n => {
            const base = baseNodeStyles.get(n.id) || toBaseStyle(n);
            if (!baseNodeStyles.has(n.id)) baseNodeStyles.set(n.id, base);
            const label = nodeCircleLabel(n.id);
            return { id: n.id, label: label, title: String(n.id) };
          });
          if (updates.length) network.body.data.nodes.update(updates);
          nodeLabelButtons.forEach((button, key) => button.classList.toggle('ar-top-active', key === nodeLabelMode));
          network.redraw();
        }

        function refreshCustomNodeLabelMode(focusedNodeId) {
          applyNodeLabelMode('dimension');
          setTimeout(() => {
            nodeLabelMode = 'custom';
            const updates = network.body.data.nodes.get().map(n => ({
              id: n.id,
              label: nodeCircleLabel(n.id),
              title: String(n.id)
            }));
            if (updates.length) network.body.data.nodes.update(updates);
            if (focusedNodeId !== undefined && focusedNodeId !== null) {
              network.body.data.nodes.update({
                id: focusedNodeId,
                label: nodeCircleLabel(focusedNodeId),
                title: String(focusedNodeId)
              });
            }
            nodeLabelButtons.forEach((button, key) => button.classList.toggle('ar-top-active', key === nodeLabelMode));
            network.redraw();
          }, 20);
        }
        window.refreshCustomNodeLabelMode = refreshCustomNodeLabelMode;

        function createMenuBar() {
          addMenuStyles();
          createFolderPanel();
          menuBar = document.createElement('div');
          menuBar.id = 'arTopMenu';
          menuBar.innerHTML = '<span class="ar-title">AR Quiver</span><button data-action="toggle-panel">Controls</button><button data-action="fit">Fit graph</button><button data-action="undo">Ctrl+Z</button><button data-action="redo">Ctrl+Y</button><button data-action="clear-colors">Clear colors</button><button data-label-mode="dimension">show dimension vector</button><button data-label-mode="label">show label</button><button data-label-mode="custom">show custom label</button><span class="ar-spacer"></span><span>Ctrl+L hide/show UI</span>';
          document.body.appendChild(menuBar);
          menuBar.querySelectorAll('button[data-label-mode]').forEach(button => {
            nodeLabelButtons.set(button.getAttribute('data-label-mode'), button);
          });
          applyNodeLabelMode(nodeLabelMode);
          menuBar.addEventListener('click', (event) => {
            const btn = event.target.closest('button');
            if (!btn) return;
            const labelMode = btn.getAttribute('data-label-mode');
            if (labelMode) {
              applyNodeLabelMode(labelMode);
              return;
            }
            const action = btn.getAttribute('data-action');
            if (action === 'toggle-panel') {
              folderPanel.style.display = folderPanel.style.display === 'block' ? 'none' : 'block';
            }
            if (action === 'fit') network.fit({ animation: true });
            if (action === 'undo' && typeof undo === 'function') undo();
            if (action === 'redo' && typeof redo === 'function') redo();
            if (action === 'clear-colors') clearListColoring();
          });
        }

        function toggleMenuUi() {
          uiVisible = !uiVisible;
          if (!uiVisible) {
            drawerVisibleBeforeHide = !!(drawer && drawer.style.display !== 'none');
            if (menuBar) menuBar.style.display = 'none';
            if (folderPanel) folderPanel.style.display = 'none';
            if (drawer) drawer.style.display = 'none';
            return;
          }
          if (menuBar) menuBar.style.display = 'flex';
          if (folderPanel) folderPanel.style.display = 'block';
          if (drawer && drawerVisibleBeforeHide) drawer.style.display = 'block';
        }

        createMenuBar();
        document.addEventListener('keydown', (event) => {
          const key = (event.key || '').toLowerCase();
          if ((event.ctrlKey || event.metaKey) && key === 'l') {
            event.preventDefault();
            event.stopPropagation();
            toggleMenuUi();
          }
        }, true);
      })();

      let pairHighlighted = new Set();
      let splitPairHighlights = new Map();

      network.on('afterDrawing', function(ctx) {
        if (!splitPairHighlights || splitPairHighlights.size === 0) return;
        splitPairHighlights.forEach((parts, rawId) => {
          const id = Number(rawId);
          const pos = network.getPositions([id])[id];
          const node = network.body.nodes[id];
          if (!pos || !node) return;
          const box = (node.shape && node.shape.boundingBox) || node.boundingBox || null;
          let left, right, top, bottom, cx, cy, w, h;
          if (box && Number.isFinite(box.left) && Number.isFinite(box.right) && Number.isFinite(box.top) && Number.isFinite(box.bottom)) {
            left = box.left;
            right = box.right;
            top = box.top;
            bottom = box.bottom;
            cx = (left + right) / 2;
            cy = (top + bottom) / 2;
            w = Math.max(1, right - left);
            h = Math.max(1, bottom - top);
          } else {
            const dataNode = network.body.data.nodes.get(id) || {};
            const fontFace = dataNode.font && dataNode.font.face ? dataNode.font.face : 'arial';
            const fontSize = dataNode.font && dataNode.font.size ? Number(dataNode.font.size) : 14;
            ctx.font = `${fontSize}px ${fontFace}`;
            const labelLines = String(dataNode.label == null ? id : dataNode.label).split(String.fromCharCode(10));
            const measuredLabelWidth = Math.max.apply(null, labelLines.map(line => ctx.measureText(line).width).concat([0])) + 36;
            const nodeWidth = Number(node.width || 0);
            const shapeWidth = Number(node.shape && node.shape.width ? node.shape.width : 0);
            w = Math.max(42, measuredLabelWidth, nodeWidth, shapeWidth, 46);
            h = Math.max(30, Number(node.height || 0), (node.shape && node.shape.height) ? node.shape.height : 32);
            cx = pos.x;
            cy = pos.y;
            left = cx - w / 2;
            right = cx + w / 2;
            top = cy - h / 2;
            bottom = cy + h / 2;
          }
          parts.forEach(part => {
            ctx.save();
            ctx.globalAlpha = 0.55;
            ctx.beginPath();
            if (part.part === 'left') {
              ctx.rect(left, top, w / 2, h);
            } else if (part.part === 'right') {
              ctx.rect((left + right) / 2, top, w / 2, h);
            } else if (part.part === 'top') {
              ctx.rect(left, top, w, h / 2);
            } else if (part.part === 'bottom') {
              ctx.rect(left, (top + bottom) / 2, w, h / 2);
            }
            ctx.clip();
            ctx.beginPath();
            ctx.ellipse(cx, cy, w / 2, h / 2, 0, 0, 2 * Math.PI);
            ctx.fillStyle = part.color;
            ctx.fill();
            ctx.restore();
          });
        });
      });

      const zeroNodeIdCache = new Set((zeroObjectIds || []).map(Number));
      const tiltingPairIndex = (() => {
        const index = new Map();
        (tiltingData || []).forEach((t, i) => {
          index.set(`${sortedKey(t.T)}|${sortedKey(t.F)}`, { index: i, item: t });
        });
        return index;
      })();

      function zeroNodeIds() {
        return zeroNodeIdCache;
      }

      function sortedKey(arr) {
        return (arr || []).map(Number).filter(n => Number.isFinite(n) && !zeroNodeIdCache.has(n)).sort((a, b) => a - b).join(',');
      }

      function findTiltingForTorsionPair(item) {
        return tiltingPairIndex.get(`${sortedKey(item.T)}|${sortedKey(item.F)}`) || null;
      }

      function resetPairStyles() {
        pairHighlighted.forEach(id => restoreNodeBase(id));
        pairHighlighted = new Set();
        splitPairHighlights = new Map();
        network.unselectAll();
        network.redraw();
      }

      function addSplitFill(ids, part, colorHex, nextSet) {
        (ids || []).forEach(raw => {
          const id = Number(raw);
          if (!Number.isFinite(id) || !getExistingNode(id)) return;
          const key = String(id);
          const parts = splitPairHighlights.get(key) || [];
          parts.push({ part, color: colorHex });
          splitPairHighlights.set(key, parts);
          nextSet.add(id);
        });
      }

      function applyFullFill(ids, colorHex, nextSet) {
        (ids || []).forEach(raw => {
          const id = Number(raw);
          const node = getExistingNode(id);
          if (!Number.isFinite(id) || !node) return;
          let base = baseNodeStyles.get(node.id);
          if (!base) {
            base = toBaseStyle(node);
            baseNodeStyles.set(node.id, base);
          }
          const baseColor = base.color;
          let colorObj;
          if (typeof baseColor === 'string') {
            colorObj = { border: baseColor, background: colorHex };
          } else {
            colorObj = { ...(baseColor || {}), background: colorHex };
          }
          network.body.data.nodes.update({ id: node.id, color: colorObj });
          nextSet.add(node.id);
        });
      }

      function applyTiltingTorsionPairHighlight(tiltingItem) {
        resetTiltingStyles();
        resetPairStyles();
        const nextSet = new Set();
        const L = new Set((tiltingItem.L || []).map(Number).filter(Number.isFinite));
        const T = (tiltingItem.T || []).map(Number).filter(id => Number.isFinite(id) && !L.has(id));
        const F = (tiltingItem.F || []).map(Number).filter(id => Number.isFinite(id) && !L.has(id));
        applyFullFill([...L], arColors.tiltingL, nextSet);
        applyFullFill(T, arColors.torsionT, nextSet);
        applyFullFill(F, arColors.torsionF, nextSet);
        tiltingHighlighted = nextSet;
        pairHighlighted = nextSet;
        network.unselectAll();
        network.redraw();
      }

      function applyTorsionPairHighlight(item) {
        resetTiltingStyles();
        resetPairStyles();
        const nextSet = new Set();
        applyFullFill(item.T || [], arColors.torsionT, nextSet);
        applyFullFill(item.F || [], arColors.torsionF, nextSet);
        pairHighlighted = nextSet;
        network.unselectAll();
        network.redraw();
      }

      function applyCotorsionPairHighlight(item) {
        resetTiltingStyles();
        resetPairStyles();
        const nextSet = new Set();
        addSplitFill(item.L || [], 'top', arColors.cotorsionL, nextSet);
        addSplitFill(item.R || [], 'bottom', arColors.cotorsionR, nextSet);
        pairHighlighted = nextSet;
        network.unselectAll();
        network.redraw();
      }

      function applySupportTauHighlight(item) {
        resetTiltingStyles();
        resetPairStyles();
        const nextSet = new Set();
        applyFullFill(item.P || [], arColors.supportP, nextSet);
        applyFullFill(item.M || [], arColors.supportM, nextSet);
        pairHighlighted = nextSet;
        network.unselectAll();
        network.redraw();
      }

      const arColors = {
        torsionT: '#ffe1c7',
        torsionF: '#d9f2d9',
        tiltingL: '#b5b5b5',
        cotorsionL: '#93c5fd',
        cotorsionR: '#fca5a5',
        supportP: '#dbeafe',
        supportM: '#b5b5b5',
        calcA: '#bfdbfe',
        calcB: '#fde68a',
        calcResult: '#bbf7d0'
      };

      function colorSwatch(color, label) {
        const title = label ? ` title="${label}"` : '';
        return `<span${title} style="display:inline-block;width:0.85em;height:0.85em;vertical-align:-0.08em;margin:0 0.2em;border:1px solid #64748b;border-radius:2px;background:${color};"></span>`;
      }

      function colorKey(label, color) {
        return `${label} ${colorSwatch(color, label)}`;
      }

      function titleWithColorKeys(title, entries) {
        return `${title} <span style="font-weight:400;color:#475569;font-size:11px;">(${entries.map(entry => colorKey(entry[0], entry[1])).join(', ')})</span>`;
      }

      function displayClassList(arr) {
        return (!arr || arr.length === 0) ? '0' : arr.join(',');
      }

      const listStates = new Map();
      const pairListFilters = {
        torsionTilting: 'all',
        torsionSplit: 'all',
        cotorsionHereditary: 'all',
        tiltingSplitting: 'all',
        tiltingSeparating: 'all'
      };

      function setPairFilter(key, value) {
        pairListFilters[key] = value;
      }

      function tiltingSplittingFlag(item) {
        if (item && Object.prototype.hasOwnProperty.call(item, 'splitting')) return !!item.splitting;
        return tiltingIsSplit(item);
      }

      function tiltingSeparatingFlag(item) {
        if (item && Object.prototype.hasOwnProperty.call(item, 'separating')) return !!item.separating;
        return tiltingIsSeparating(item);
      }

      function filterTiltingRows(data) {
        return (data || []).filter(item => {
          const splitting = tiltingSplittingFlag(item);
          const separating = tiltingSeparatingFlag(item);
          const splittingOk = pairListFilters.tiltingSplitting === 'all' || (pairListFilters.tiltingSplitting === 'splitting' ? splitting : !splitting);
          const separatingOk = pairListFilters.tiltingSeparating === 'all' || (pairListFilters.tiltingSeparating === 'separating' ? separating : !separating);
          return splittingOk && separatingOk;
        });
      }

      function installTiltingFilterButtons(containerId) {
        const el = document.getElementById(containerId);
        if (!el) return;
        const row = document.createElement('div');
        row.style.display = 'flex';
        row.style.flexWrap = 'wrap';
        row.style.gap = '4px';
        row.style.margin = '0 0 6px 0';
        [
          { key: 'tiltingSplitting', vals: ['all','splitting','non-splitting'] },
          { key: 'tiltingSeparating', vals: ['all','separating','non-separating'] }
        ].forEach(group => {
          group.vals.forEach(val => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.textContent = val;
            btn.style.fontSize = '11px';
            btn.style.padding = '2px 6px';
            btn.style.border = '1px solid ' + (pairListFilters[group.key] === val ? '#0f766e' : '#ccc');
            btn.style.borderRadius = '4px';
            btn.style.background = pairListFilters[group.key] === val ? '#ccfbf1' : '#fff';
            btn.addEventListener('click', () => { pairListFilters[group.key] = val; renderTiltingList(); });
            row.appendChild(btn);
          });
        });
        el.prepend(row);
      }

      const listModuleIdCache = (() => {
        const ids = new Set();
        const add = (value) => {
          const n = Number(value);
          if (Number.isFinite(n)) ids.add(n);
        };
        if (typeof pdidMap !== 'undefined' && pdidMap && typeof pdidMap === 'object') Object.keys(pdidMap).forEach(add);
        if (typeof tiltingData !== 'undefined') {
          (tiltingData || []).forEach(item => {
            (item.L || []).forEach(add);
            (item.F || []).forEach(add);
            (item.T || []).forEach(add);
          });
        }
        if (typeof torsionPairData !== 'undefined') {
          (torsionPairData || []).forEach(item => {
            (item.T || []).forEach(add);
            (item.F || []).forEach(add);
          });
        }
        return Array.from(ids).sort((a, b) => a - b);
      })();
      const listModuleIdSet = new Set(listModuleIdCache);
      const torsionSplitCache = new WeakMap();
      const tiltingTagCache = new WeakMap();

      function listAllModuleIds() {
        return listModuleIdCache;
      }

      function isSplitTorsionPair(item) {
        if (!item || typeof item !== 'object') return false;
        if (torsionSplitCache.has(item)) return torsionSplitCache.get(item);
        const union = new Set([...(item.T || []), ...(item.F || [])].map(Number).filter(Number.isFinite));
        let split = union.size === listModuleIdSet.size;
        if (split) {
          for (const id of listModuleIdSet) {
            if (!union.has(id)) { split = false; break; }
          }
        }
        torsionSplitCache.set(item, split);
        return split;
      }

      function tiltingIsSeparating(item) {
        return isSplitTorsionPair(item || {});
      }

      function injectiveDimensionAtMostOne(id) {
        const key = Number(id);
        if (!Number.isFinite(key)) return false;
        const entry = pdidMap && (pdidMap[key] || pdidMap[String(key)]);
        if (!entry) return false;
        const value = Number(entry.id);
        return Number.isFinite(value) && value >= 0 && value <= 1;
      }

      function tiltingIsSplit(item) {
        return (item && item.F ? item.F : []).map(Number).filter(Number.isFinite).every(injectiveDimensionAtMostOne);
      }

      function tiltingTags(item) {
        if (item && typeof item === 'object' && tiltingTagCache.has(item)) return tiltingTagCache.get(item);
        const tags = [tiltingIsSplit(item) ? 'splitting' : 'non-splitting', tiltingIsSeparating(item) ? 'separating' : 'non-separating'];
        if (item && typeof item === 'object') tiltingTagCache.set(item, tags);
        return tags;
      }

      function isSplitPair(item) {
        if (item && (Object.prototype.hasOwnProperty.call(item, 'T') || Object.prototype.hasOwnProperty.call(item, 'F'))) {
          return isSplitTorsionPair(item);
        }
        const union = new Set([...(item.L || []), ...(item.R || [])].map(Number).filter(Number.isFinite));
        if (union.size !== listModuleIdSet.size) return false;
        for (const id of listModuleIdSet) if (!union.has(id)) return false;
        return true;
      }

      function filterPairRows(data, kind) {
        let rows = data || [];
        if (kind === 'torsion') {
          rows = rows.filter(item => {
            const hasTilting = Object.prototype.hasOwnProperty.call(item, 'tilting') ? !!item.tilting : !!findTiltingForTorsionPair(item);
            const split = Object.prototype.hasOwnProperty.call(item, 'split') ? !!item.split : isSplitPair(item);
            const tiltingOk = pairListFilters.torsionTilting === 'all' || (pairListFilters.torsionTilting === 'tilting' ? hasTilting : !hasTilting);
            const splitOk = pairListFilters.torsionSplit === 'all' || (pairListFilters.torsionSplit === 'split' ? split : !split);
            return tiltingOk && splitOk;
          });
        } else if (kind === 'cotorsion') {
          rows = rows.filter(item => pairListFilters.cotorsionHereditary === 'all' || (pairListFilters.cotorsionHereditary === 'hereditary' ? !!item.hereditary : !item.hereditary));
        }
        return rows;
      }

      function installPairFilterButtons(containerId, kind, rerender) {
        const el = document.getElementById(containerId);
        if (!el) return;
        const row = document.createElement('div');
        row.style.display = 'flex';
        row.style.flexWrap = 'wrap';
        row.style.gap = '4px';
        row.style.margin = '0 0 6px 0';
        const groups = kind === 'torsion'
          ? [{ key: 'torsionTilting', vals: ['all','tilting','non-tilting'] }, { key: 'torsionSplit', vals: ['all','split','non-split'] }]
          : [{ key: 'cotorsionHereditary', vals: ['all','hereditary','non-hereditary'] }];
        groups.forEach(group => {
          group.vals.forEach(val => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.textContent = val;
            btn.style.fontSize = '11px';
            btn.style.padding = '2px 6px';
            btn.style.border = '1px solid ' + (pairListFilters[group.key] === val ? '#0f766e' : '#ccc');
            btn.style.borderRadius = '4px';
            btn.style.background = pairListFilters[group.key] === val ? '#ccfbf1' : '#fff';
            btn.addEventListener('click', () => { setPairFilter(group.key, val); rerender(); });
            row.appendChild(btn);
          });
        });
        el.prepend(row);
      }

      function listLexCompare(a, b) {
        const aa = (a || []).map(Number);
        const bb = (b || []).map(Number);
        const n = Math.min(aa.length, bb.length);
        for (let i = 0; i < n; i += 1) {
          if (aa[i] !== bb[i]) return aa[i] - bb[i];
        }
        return aa.length - bb.length;
      }

      function compareByColumn(a, b, key, mode) {
        const av = a.item[key] || [];
        const bv = b.item[key] || [];
        if (mode === 'lenlex' && av.length !== bv.length) return av.length - bv.length;
        const c = listLexCompare(av, bv);
        if (c !== 0) return c;
        return a.originalIndex - b.originalIndex;
      }

      function ensureListState(containerId, defaultKey) {
        if (!listStates.has(containerId)) {
          listStates.set(containerId, { sortKey: defaultKey, sortMode: 'lex', selectedIndex: 0, rows: [] });
        }
        return listStates.get(containerId);
      }

      function activateButtonListRow(containerId, displayIndex) {
        const state = listStates.get(containerId);
        if (!state || !state.rows.length) return;
        const bounded = Math.max(0, Math.min(displayIndex, state.rows.length - 1));
        state.selectedIndex = bounded;
        const el = document.getElementById(containerId);
        if (!el) return;
        el.querySelectorAll('button[data-row]').forEach((btn) => {
          const active = Number(btn.getAttribute('data-row')) === bounded;
          btn.classList.toggle('tilting-btn-active', active);
          if (active) btn.focus({ preventScroll: true });
        });
        state.apply(state.rows[bounded].item);
      }

      function renderButtonRecordList(containerId, data, title, columns, applyFn, formatExtra) {
        const el = document.getElementById(containerId);
        if (!el) return;
        if (!data || data.length === 0) {
          el.innerHTML = `<b>${title}</b><br/><span style="color:#666;">No data.</span>`;
          return;
        }
        const state = ensureListState(containerId, columns[0].key);
        state.apply = applyFn;
        let rows = data.map((item, originalIndex) => ({ item, originalIndex }));
        rows.sort((a, b) => compareByColumn(a, b, state.sortKey, state.sortMode));
        state.rows = rows;
        if (state.selectedIndex >= rows.length) state.selectedIndex = rows.length - 1;

        const modeText = state.sortMode === 'lex' ? 'lex' : 'length+lex';
        const headerButtons = columns.map(col => {
          const active = state.sortKey === col.key;
          return `<button type="button" data-sort-key="${col.key}" style="font-size:11px; margin-right:4px; padding:2px 6px; border:1px solid ${active ? '#0f766e' : '#ccc'}; border-radius:4px; background:${active ? '#ccfbf1' : '#fff'}; cursor:pointer;">${col.label}${active ? ` (${modeText})` : ''}</button>`;
        }).join('');
        const items = rows.map((row, idx) => {
          const body = row.item.labelText || columns.map(col => `${col.label}=[${displayClassList(row.item[col.key] || [])}]`).join(' | ');
          const extra = row.item.labelText ? '' : (formatExtra ? formatExtra(row.item) : '');
          return `<button type="button" data-row="${idx}" class="ar-record-row">${idx + 1}. ${body}${extra}</button>`;
        }).join('');
        el.innerHTML = `<b>${title}</b><div style="margin:4px 0;">${headerButtons}</div><div role="listbox">${items}</div>`;
        el.onclick = (event) => {
          const sortBtn = event.target.closest('button[data-sort-key]');
          if (sortBtn && el.contains(sortBtn)) {
            const key = sortBtn.getAttribute('data-sort-key');
            if (state.sortKey === key) state.sortMode = state.sortMode === 'lex' ? 'lenlex' : 'lex';
            else { state.sortKey = key; state.sortMode = 'lex'; }
            state.selectedIndex = 0;
            renderButtonRecordList(containerId, data, title, columns, applyFn, formatExtra);
            return;
          }
          const rowBtn = event.target.closest('button[data-row]');
          if (rowBtn && el.contains(rowBtn)) activateButtonListRow(containerId, Number(rowBtn.getAttribute('data-row')));
        };
        el.onkeydown = (event) => {
          if (event.key === 'ArrowDown') { event.preventDefault(); activateButtonListRow(containerId, state.selectedIndex + 1); }
          if (event.key === 'ArrowUp') { event.preventDefault(); activateButtonListRow(containerId, state.selectedIndex - 1); }
        };
      }

      function renderSupportTauList(containerId, data, title) {
        renderButtonRecordList(
          containerId,
          data,
          title,
          [{ key: 'P', label: 'P' }, { key: 'M', label: 'M' }],
          applySupportTauHighlight
        );
      }

      function renderTorsionClassListLikeCotorsion(containerId) {
        const el = document.getElementById(containerId);
        if (!el) return;
        try {
          const safeList = (arr) => (!arr || arr.length === 0) ? '0' : arr.join(',');
          const safeHasTilting = (item) => {
            if (item && Object.prototype.hasOwnProperty.call(item, 'tilting')) return !!item.tilting;
            try { return !!findTiltingForTorsionPair(item); } catch (err) { return false; }
          };
          const safeIsSplit = (item) => {
            if (item && Object.prototype.hasOwnProperty.call(item, 'split')) return !!item.split;
            try { return isSplitPair(item); } catch (err) { return false; }
          };
          const bucketKey = `${pairListFilters.torsionTilting}|${pairListFilters.torsionSplit}`;
          const bucket = torsionPairBuckets && torsionPairBuckets[bucketKey];
          let rows = Array.isArray(bucket)
            ? bucket.map(idx => {
                const item = torsionPairData[idx];
                return item ? { item, hasTilting: !!item.tilting, split: !!item.split } : null;
              }).filter(Boolean)
            : (torsionPairData || []).map(item => ({
                item,
                hasTilting: safeHasTilting(item),
                split: safeIsSplit(item)
              })).filter(row => {
                const tiltingOk = pairListFilters.torsionTilting === 'all' || (pairListFilters.torsionTilting === 'tilting' ? row.hasTilting : !row.hasTilting);
                const splitOk = pairListFilters.torsionSplit === 'all' || (pairListFilters.torsionSplit === 'split' ? row.split : !row.split);
                return tiltingOk && splitOk;
              });

          el.innerHTML = '';
          const title = document.createElement('div');
          title.innerHTML = '<b>Torsion pairs</b>';
          el.appendChild(title);

          const filterRow = document.createElement('div');
          filterRow.style.display = 'flex';
          filterRow.style.flexWrap = 'wrap';
          filterRow.style.gap = '4px';
          filterRow.style.margin = '6px 0';
          [
            { key: 'torsionTilting', vals: ['all','tilting','non-tilting'] },
            { key: 'torsionSplit', vals: ['all','split','non-split'] }
          ].forEach(group => {
            group.vals.forEach(val => {
              const btn = document.createElement('button');
              btn.type = 'button';
              btn.textContent = val;
              btn.style.fontSize = '11px';
              btn.style.padding = '2px 6px';
              btn.style.border = '1px solid ' + (pairListFilters[group.key] === val ? '#0f766e' : '#ccc');
              btn.style.borderRadius = '4px';
              btn.style.background = pairListFilters[group.key] === val ? '#ccfbf1' : '#fff';
              btn.addEventListener('click', () => {
                pairListFilters[group.key] = val;
                renderTorsionClassListLikeCotorsion(containerId);
              });
              filterRow.appendChild(btn);
            });
          });
          el.appendChild(filterRow);

          if (!rows.length) {
            const empty = document.createElement('div');
            empty.style.color = '#666';
            empty.textContent = 'No torsion pairs after filters.';
            el.appendChild(empty);
            if (typeof resizeDrawerContent === 'function') resizeDrawerContent();
            return;
          }

          rows.sort((a, b) => {
            const la = (a.item.T || []).length;
            const lb = (b.item.T || []).length;
            if (la !== lb) return la - lb;
            return safeList(a.item.T).localeCompare(safeList(b.item.T), undefined, { numeric: true });
          });

          const listBox = document.createElement('div');
          listBox.setAttribute('role', 'listbox');
          rows.forEach((row, idx) => {
            const item = row.item;
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.dataset.row = String(idx);
            btn.className = 'ar-record-row';
            btn.textContent = `${idx + 1}. ${item.labelText || (`T=[${safeList(item.T || [])}] | F=[${safeList(item.F || [])}] | ${item.tagText || ((row.hasTilting ? 'tilting' : 'non-tilting') + ' | ' + (row.split ? 'split' : 'non-split'))}`)}`;
            listBox.appendChild(btn);
          });
          listBox.addEventListener('click', (event) => {
            const btn = event.target.closest('button[data-row]');
            if (!btn || !listBox.contains(btn)) return;
            const row = rows[Number(btn.dataset.row)];
            if (!row) return;
            el.querySelectorAll('button[data-row]').forEach(b => b.classList.remove('tilting-btn-active'));
            btn.classList.add('tilting-btn-active');
            applyTorsionPairHighlight(row.item);
          });
          el.appendChild(listBox);
          if (typeof resizeDrawerContent === 'function') resizeDrawerContent();
        } catch (err) {
          el.innerHTML = '<b>Torsion pairs</b><pre style="white-space:pre-wrap;color:#b91c1c;background:#fee2e2;border:1px solid #fecaca;border-radius:6px;padding:8px;">Torsion render error: ' + (err && err.message ? err.message : String(err)) + '</pre>';
        }
      }

      function renderPairList(containerId, data, leftKey, rightKey, title, extraRenderer, options = {}) {
        const isTorsion = options.kind === 'torsion';
        const isCotorsion = options.kind === 'cotorsion';
        const filteredData = filterPairRows(data, isTorsion ? 'torsion' : (isCotorsion ? 'cotorsion' : ''));
        const rerender = () => renderPairList(containerId, data, leftKey, rightKey, title, extraRenderer, options);
        const applyFn = (item) => {
          if (isTorsion) {
            applyTorsionPairHighlight(item);
          } else {
            applyCotorsionPairHighlight(item);
          }
        };
        const formatExtra = (item) => {
          if (isTorsion) {
            if (item && Object.prototype.hasOwnProperty.call(item, 'tagText')) return ' | ' + item.tagText;
            const tags = [];
            tags.push(Object.prototype.hasOwnProperty.call(item, 'tilting') ? (item.tilting ? 'tilting' : 'non-tilting') : (findTiltingForTorsionPair(item) ? 'tilting' : 'non-tilting'));
            tags.push(Object.prototype.hasOwnProperty.call(item, 'split') ? (item.split ? 'split' : 'non-split') : (isSplitTorsionPair(item) ? 'split' : 'non-split'));
            return ' | ' + tags.join(' | ');
          }
          if (extraRenderer) return ` | ${item.hereditary ? 'hereditary' : 'non-hereditary'}`;
          return '';
        };
        renderButtonRecordList(containerId, filteredData, title, [{ key: leftKey, label: leftKey }, { key: rightKey, label: rightKey }], applyFn, formatExtra);
        if (isTorsion) installPairFilterButtons(containerId, 'torsion', rerender);
        if (isCotorsion) installPairFilterButtons(containerId, 'cotorsion', rerender);
        if (typeof resizeDrawerContent === 'function') resizeDrawerContent();
      }

      function tiltingExtraText(item) {
        if (item && Object.prototype.hasOwnProperty.call(item, 'tagText')) return ' | ' + item.tagText;
        if (item && Array.isArray(item.tags)) return ' | ' + item.tags.join(' | ');
        try {
          return ' | ' + tiltingTags(item).join(' | ');
        } catch (err) {
          const msg = err && err.message ? err.message : String(err);
          return ' | tag-error: ' + msg;
        }
      }

      function renderTiltingListFallback(el, err) {
        if (!el) return;
        const data = filterTiltingRows(tiltingData || []);
        const errorHtml = err ? `<pre style="white-space:pre-wrap;color:#b91c1c;background:#fee2e2;border:1px solid #fecaca;border-radius:6px;padding:8px;margin:0 0 6px 0;">Tilting render fallback: ${String(err && err.message ? err.message : err)}</pre>` : '';
        const items = data.map((item, idx) => {
          const L = displayClassList(item.L || []);
          const F = displayClassList(item.F || []);
          const T = displayClassList(item.T || []);
          const extra = tiltingExtraText(item);
          return `<button type="button" data-row="${idx}" class="ar-record-row">${idx + 1}. L=[${L}] | F=[${F}] | T=[${T}]${extra}</button>`;
        }).join('');
        el.innerHTML = `<b>Tilting modules</b><div style="margin:4px 0;color:#64748b;">${data.length} records</div>${errorHtml}<div role="listbox">${items || '<span style="color:#666;">No tilting data.</span>'}</div>`;
        installTiltingFilterButtons('tiltingList');
        el.querySelectorAll('button[data-row]').forEach(btn => {
          btn.addEventListener('click', () => {
            const idx = Number(btn.getAttribute('data-row'));
            const item = data[idx];
            if (!item) return;
            el.querySelectorAll('button[data-row]').forEach(b => b.classList.remove('tilting-btn-active'));
            btn.classList.add('tilting-btn-active');
            resetPairStyles();
            applyTiltingHighlight(item);
            setActiveTilting(idx);
          });
        });
      }

      function renderTiltingList() {
        const el = document.getElementById('tiltingList');
        try {
          const data = filterTiltingRows(tiltingData);
          renderButtonRecordList('tiltingList', data, 'Tilting modules', [
            { key: 'L', label: 'L' },
            { key: 'F', label: 'F' },
            { key: 'T', label: 'T' }
          ], (item) => {
            resetPairStyles();
            applyTiltingHighlight(item);
            const idx = tiltingData.indexOf(item);
            setActiveTilting(idx);
          }, tiltingExtraText);
          installTiltingFilterButtons('tiltingList');
          if (el && !el.querySelector('button[data-row]') && data && data.length) {
            throw new Error('tiltingData is nonempty but no tilting row was rendered');
          }
        } catch (err) {
          renderTiltingListFallback(el, err);
        }
      }

      function setActiveTilting(idx) {
        const listEl = document.getElementById('tiltingList');
        const buttons = listEl.querySelectorAll('button[data-row]');
        buttons.forEach((b) => {
          const row = Number(b.getAttribute('data-row'));
          const state = listStates.get('tiltingList');
          const item = state && state.rows[row] ? state.rows[row].item : null;
          const originalIndex = item ? tiltingData.indexOf(item) : row;
          b.classList.toggle('tilting-btn-active', originalIndex === idx);
        });
      }

      function clearActiveTilting() {
        const listEl = document.getElementById('tiltingList');
        const buttons = listEl.querySelectorAll('button[data-row]');
        buttons.forEach((b) => b.classList.remove('tilting-btn-active'));
      }

      function getActiveTiltingIndex() {
        const listEl = document.getElementById('tiltingList');
        const buttons = listEl.querySelectorAll('button[data-row]');
        for (let i = 0; i < buttons.length; i++) {
          if (buttons[i].classList.contains('tilting-btn-active')) return Number(buttons[i].getAttribute('data-row'));
        }
        return -1;
      }

      function selectTiltingByIndex(nextIdx) {
        const listEl = document.getElementById('tiltingList');
        const buttons = listEl.querySelectorAll('button[data-row]');
        if (!buttons.length) return;
        let idx = nextIdx;
        if (idx < 0) idx = 0;
        if (idx >= buttons.length) idx = buttons.length - 1;
        buttons[idx].click();
        buttons[idx].scrollIntoView({ block: 'nearest' });
      }

      function ensureIdLabelLayer() {
        if (idLabelLayer) return;
        idLabelLayer = document.createElement('div');
        idLabelLayer.style.position = 'absolute';
        idLabelLayer.style.left = '0';
        idLabelLayer.style.top = '0';
        idLabelLayer.style.width = '100%';
        idLabelLayer.style.height = '100%';
        idLabelLayer.style.pointerEvents = 'none';
        idLabelLayer.style.zIndex = '997';
        network.body.container.appendChild(idLabelLayer);
      }

      function ensureFloatingLabelLayer(name, zIndex) {
        const prop = name + 'Layer';
        if (window[prop]) return window[prop];
        const layer = document.createElement('div');
        layer.style.position = 'absolute';
        layer.style.left = '0';
        layer.style.top = '0';
        layer.style.width = '100%';
        layer.style.height = '100%';
        layer.style.pointerEvents = 'none';
        layer.style.zIndex = String(zIndex);
        network.body.container.appendChild(layer);
        window[prop] = layer;
        return layer;
      }

      function makeLabelElement(layer, color, border, background, kind) {
        const el = document.createElement('div');
        el.dataset.labelKind = kind || '';
        el.style.position = 'absolute';
        el.style.fontSize = '12px';
        el.style.color = color;
        el.style.fontFamily = 'monospace';
        el.style.fontWeight = 'normal';
        el.style.transform = 'translate(-50%, 0)';
        el.style.background = background;
        el.style.border = '1px solid ' + border;
        el.style.borderRadius = '4px';
        el.style.padding = '1px 4px';
        el.style.boxShadow = '0 1px 2px rgba(0,0,0,0.1)';
        el.style.whiteSpace = 'pre';
        el.style.cursor = 'move';
        el.style.userSelect = 'none';
        el.style.pointerEvents = 'auto';
        el.addEventListener('mousedown', startFloatingLabelDrag);
        layer.appendChild(el);
        return el;
      }

      function startFloatingLabelDrag(event) {
        const kind = event.currentTarget && event.currentTarget.dataset ? event.currentTarget.dataset.labelKind : '';
        if (!kind || !floatingLabelOffsets[kind]) return;
        event.preventDefault();
        event.stopPropagation();
        floatingLabelDrag = {
          kind,
          startClientX: event.clientX,
          startClientY: event.clientY,
          startOffsetX: floatingLabelOffsets[kind].x,
          startOffsetY: floatingLabelOffsets[kind].y
        };
        document.body.style.cursor = 'move';
        window.addEventListener('mousemove', moveFloatingLabelDrag);
        window.addEventListener('mouseup', stopFloatingLabelDrag, { once: true });
      }

      function moveFloatingLabelDrag(event) {
        if (!floatingLabelDrag) return;
        const kind = floatingLabelDrag.kind;
        floatingLabelOffsets[kind].x = floatingLabelDrag.startOffsetX + event.clientX - floatingLabelDrag.startClientX;
        floatingLabelOffsets[kind].y = floatingLabelDrag.startOffsetY + event.clientY - floatingLabelDrag.startClientY;
        refreshFloatingLabelsByKind(kind);
      }

      function stopFloatingLabelDrag() {
        floatingLabelDrag = null;
        document.body.style.cursor = '';
        window.removeEventListener('mousemove', moveFloatingLabelDrag);
      }

      function refreshFloatingLabelsByKind(kind) {
        if (kind === 'pd' && showPd) updatePdLabels();
        if (kind === 'id' && showId) updateIdValueLabels();
        if (kind === 'top' && showTop) updateTopLabels();
        if (kind === 'soc' && showSoc) updateSocLabels();
      }

      function updateScalarLabels(visible, layer, labelMap, getText, yOffset, color, border, background, kind) {
        if (!visible || !layer) return;
        const positions = network.getPositions();
        Object.keys(positions).forEach(idStr => {
          const id = Number(idStr);
          if (!Number.isFinite(id)) return;
          const text = getText(id);
          if (text === null || text === undefined || text === '') return;
          const node = network.body.nodes[id];
          if (!node) return;
          let el = labelMap.get(id);
          if (!el) {
            el = makeLabelElement(layer, color, border, background, kind);
            labelMap.set(id, el);
          }
          el.textContent = text;
          const dom = network.canvasToDOM(positions[id]);
          const offset = floatingLabelOffsets[kind] || { x: 0, y: 0 };
          el.style.left = `${dom.x + offset.x}px`;
          el.style.top = `${dom.y + yOffset(node) + offset.y}px`;
        });
      }

      function ensurePdLabelLayer() {
        pdLabelLayer = pdLabelLayer || ensureFloatingLabelLayer('pdLabel', 998);
      }
      function ensureIdValueLabelLayer() {
        idValueLabelLayer = idValueLabelLayer || ensureFloatingLabelLayer('idValueLabel', 998);
      }
      function ensureTopLabelLayer() {
        topLabelLayer = topLabelLayer || ensureFloatingLabelLayer('topLabel', 999);
      }
      function ensureSocLabelLayer() {
        socLabelLayer = socLabelLayer || ensureFloatingLabelLayer('socLabel', 999);
      }

      function pdidEntry(id) {
        return pdidMap && (pdidMap[id] || pdidMap[String(id)]);
      }
      function topSocEntry(id) {
        return topSocMap && (topSocMap[id] || topSocMap[String(id)]);
      }

      function formatHomologicalDimension(value) {
        return Number(value) === -1 ? '∞' : String(value);
      }

      function updatePdLabels() {
        updateScalarLabels(showPd, pdLabelLayer, pdLabelMap, id => {
          const e = pdidEntry(id); return e ? `pd=${formatHomologicalDimension(e.pd)}` : null;
        }, node => -((node.shape && node.shape.height) ? (node.shape.height / 2 + 42) : 46), '#1f4a7a', '#9eb6d3', 'rgba(219,234,254,0.96)', 'pd');
      }
      function updateIdValueLabels() {
        updateScalarLabels(showId, idValueLabelLayer, idValueLabelMap, id => {
          const e = pdidEntry(id); return e ? `id=${formatHomologicalDimension(e.id)}` : null;
        }, node => -((node.shape && node.shape.height) ? (node.shape.height / 2 + 24) : 28), '#1f4a7a', '#9eb6d3', 'rgba(224,242,254,0.96)', 'id');
      }
      function updateTopLabels() {
        updateScalarLabels(showTop, topLabelLayer, topLabelMap, id => {
          const e = topSocEntry(id); return e ? `Top=${formatSimpleList(e.top)}` : null;
        }, node => ((node.shape && node.shape.height) ? (node.shape.height / 2 + 28) : 34), '#14532d', '#86efac', 'rgba(240,253,244,0.96)', 'top');
      }
      function updateSocLabels() {
        updateScalarLabels(showSoc, socLabelLayer, socLabelMap, id => {
          const e = topSocEntry(id); return e ? `Soc=${formatSimpleList(e.soc)}` : null;
        }, node => ((node.shape && node.shape.height) ? (node.shape.height / 2 + 46) : 52), '#7c2d12', '#fdba74', 'rgba(255,247,237,0.96)', 'soc');
      }

      function togglePdLabels(visible) {
        showPd = visible;
        ensurePdLabelLayer();
        pdLabelLayer.style.display = visible ? 'block' : 'none';
        updatePdLabels();
      }
      function toggleIdValueLabels(visible) {
        showId = visible;
        ensureIdValueLabelLayer();
        idValueLabelLayer.style.display = visible ? 'block' : 'none';
        updateIdValueLabels();
      }
      function toggleTopLabels(visible) {
        showTop = visible;
        ensureTopLabelLayer();
        topLabelLayer.style.display = visible ? 'block' : 'none';
        updateTopLabels();
      }
      function toggleSocLabels(visible) {
        showSoc = visible;
        ensureSocLabelLayer();
        socLabelLayer.style.display = visible ? 'block' : 'none';
        updateSocLabels();
      }

      function showIdLabels() {
        ensureIdLabelLayer();
        idLabelLayer.style.display = 'block';
        updateIdLabels();
      }

      function hideIdLabels() {
        if (idLabelLayer) idLabelLayer.style.display = 'none';
      }

      function ensureTopSocLabelLayer() {}

      function toSuperscript(value) {
        const map = { '0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹','+':'⁺','-':'⁻' };
        return String(value).split('').map(ch => map[ch] || ch).join('');
      }

      function formatSimpleList(arr) {
        if (!arr || arr.length === 0) return '0';
        const counts = new Map();
        const order = [];
        arr.forEach(x => {
          const key = String(x);
          if (!counts.has(key)) order.push(key);
          counts.set(key, (counts.get(key) || 0) + 1);
        });
        return order.map(key => key + (counts.get(key) > 1 ? toSuperscript(counts.get(key)) : '')).join('');
      }

      function updateTopSocLabels() {}
      function showTopSocLabels() {}
      function hideTopSocLabels() {}

      function toggleNodeBorders(visible) {
        const nodes = network.body.data.nodes.get();
        const updates = nodes.map(n => {
          let base = baseNodeStyles.get(n.id);
          if (!base) {
            base = toBaseStyle(n);
            baseNodeStyles.set(n.id, base);
          }
          return { id: n.id, borderWidth: visible ? (base.borderWidth || 3) : 0, borderWidthSelected: visible ? (base.borderWidthSelected || 5) : 0 };
        });
        if (updates.length) network.body.data.nodes.update(updates);
      }

      function restoreNodeBase(id) {
        const node = getExistingNode(id);
        if (!node) return;
        let base = baseNodeStyles.get(node.id);
        if (!base) {
          base = toBaseStyle(node);
          baseNodeStyles.set(node.id, base);
        }
        let colorObj;
        if (typeof base.color === 'string') {
          colorObj = { border: base.color, background: 'white' };
        } else {
          colorObj = { ...(base.color || {}), background: (base.color && base.color.background) || 'white' };
        }
        network.body.data.nodes.update({
          id: node.id,
          color: colorObj,
          borderWidth: showBorders ? (base.borderWidth || 3) : 0,
          borderWidthSelected: showBorders ? (base.borderWidthSelected || 5) : 0,
          shadow: { enabled: false }
        });
      }

      function clearCalculatorHighlight() {
        splitPairHighlights.forEach((parts, key) => {
          const kept = (parts || []).filter(part => part.source !== 'calculator');
          if (kept.length) splitPairHighlights.set(key, kept);
          else splitPairHighlights.delete(key);
        });
        calculatorHighlighted = new Set();
        network.redraw();
      }

      function addCalculatorSplitFill(ids, part, colorHex) {
        (ids || []).forEach(rawId => {
          const id = Number(rawId);
          if (!Number.isFinite(id) || !getExistingNode(id)) return;
          const key = String(id);
          const parts = splitPairHighlights.get(key) || [];
          parts.push({ part, color: colorHex, source: 'calculator' });
          splitPairHighlights.set(key, parts);
          calculatorHighlighted.add(id);
        });
      }

      function applyCalculatorHighlights(inputA, inputB, outputIds) {
        clearCalculatorHighlight();
        const hasA = (inputA || []).length > 0;
        const hasB = (inputB || []).length > 0;
        const hasOutput = (outputIds || []).length > 0;
        if (hasA && hasB) {
          addCalculatorSplitFill(inputA, 'top', arColors.calcA);
          addCalculatorSplitFill(inputB, 'bottom', arColors.calcB);
        } else if (hasA && hasOutput) {
          addCalculatorSplitFill(inputA, 'top', arColors.calcA);
          addCalculatorSplitFill(outputIds, 'bottom', arColors.calcResult);
        } else if (hasB && hasOutput) {
          addCalculatorSplitFill(inputB, 'top', arColors.calcB);
          addCalculatorSplitFill(outputIds, 'bottom', arColors.calcResult);
        } else if (hasA) {
          addCalculatorSplitFill(inputA, 'top', arColors.calcA);
        } else if (hasB) {
          addCalculatorSplitFill(inputB, 'top', arColors.calcB);
        } else if (hasOutput) {
          addCalculatorSplitFill(outputIds, 'bottom', arColors.calcResult);
        }
        network.redraw();
      }

      function resetTiltingStyles() {
        tiltingHighlighted.forEach(id => restoreNodeBase(id));
        tiltingHighlighted = new Set();
      }

      function applyTiltingHighlight(item) {
        resetPairStyles();
        const toIdSet = (arr) => new Set((arr || []).map(n => Number(n)).filter(n => Number.isFinite(n)));
        const L = toIdSet(item.L);
        const F = toIdSet(item.F);
        const T = toIdSet(item.T);
        L.forEach(id => {
          F.delete(id);
          T.delete(id);
        });

        const newHighlighted = new Set([...L, ...F, ...T]);
        tiltingHighlighted.forEach(id => {
          if (!newHighlighted.has(id)) {
            restoreNodeBase(id);
          }
        });

        const applyFill = (id, colorHex) => {
          const node = getExistingNode(id);
          if (!node) return;
          let base = baseNodeStyles.get(node.id);
          if (!base) {
            base = toBaseStyle(node);
            baseNodeStyles.set(node.id, base);
          }
          const baseColor = base.color;
          let colorObj;
          if (typeof baseColor === 'string') {
            colorObj = { border: baseColor, background: colorHex };
          } else {
            colorObj = { ...(baseColor || {}), background: colorHex };
          }
          network.body.data.nodes.update({ id: node.id, color: colorObj });
        };

        L.forEach(id => applyFill(id, arColors.tiltingL));
        F.forEach(id => applyFill(id, arColors.torsionF));
        T.forEach(id => applyFill(id, arColors.torsionT));
        tiltingHighlighted = newHighlighted;
      }

      // --- Format quiver node label using QuiverStructure layout ---
      function formatQuiverNodeLabel(vertexId) {
        // Use the quiverStructure to produce a layout like the dimension vector display
        // e.g. QuiverStructure = "[1-2]" means vertices 1 and 2 side by side
        if (!quiverStructure) return 'v' + vertexId;
        let s = quiverStructure.trim();
        if (s.startsWith('[') && s.endsWith(']')) s = s.slice(1, -1);
        const rows = s.split(';');
        const rendered = [];
        for (const row of rows) {
          let cells = [];
          for (const ch of row) {
            if (/\\d/.test(ch)) {
              const idx = parseInt(ch);
              if (idx === vertexId) {
                cells.push('*');
              } else {
                cells.push(' ');
              }
            } else if (ch === '-' || ch === ' ') {
              cells.push(' ');
            } else {
              cells.push(' ');
            }
          }
          rendered.push(cells.join(' '));
        }
        // For single-row structures like "1-2", show e.g. "v1" but positioned
        // Actually show the vertex name directly - matching main canvas style
        return 'v' + vertexId;
      }

      function quiverTikzCode() {
        const nl = String.fromCharCode(10);
        const nodes = (quiverNodes || []).map(n => Number(n.id)).filter(Number.isFinite).sort((a, b) => a - b);
        const nodeSet = new Set(nodes);
        (quiverEdges || []).forEach(e => {
          const a = Number(e[0]);
          const b = Number(e[1]);
          if (Number.isFinite(a)) nodeSet.add(a);
          if (Number.isFinite(b)) nodeSet.add(b);
        });
        const allNodes = Array.from(nodeSet).sort((a, b) => a - b);
        const pos = {};
        if (quiverStructure) {
          let s = quiverStructure.trim();
          if (s.startsWith('[') && s.endsWith(']')) s = s.slice(1, -1);
          s.split(';').forEach((row, r) => {
            let c = 0;
            for (let i = 0; i < row.length; i += 1) {
              if (/\\d/.test(row[i])) pos[Number(row[i])] = [r, c];
              c += 1;
            }
          });
        }
        allNodes.forEach((id, i) => { if (!pos[id]) pos[id] = [0, i * 2]; });
        const rows = [];
        const maxR = Math.max.apply(null, Object.values(pos).map(p => p[0]).concat([0]));
        const maxC = Math.max.apply(null, Object.values(pos).map(p => p[1]).concat([0]));
        for (let r = 0; r <= maxR; r += 1) {
          const cells = [];
          for (let c = 0; c <= maxC; c += 1) {
            const found = allNodes.find(id => pos[id][0] === r && pos[id][1] === c);
            cells.push(found ? String(found) : '{}');
          }
          rows.push(cells.join(' & '));
        }
        const cellById = new Map(allNodes.map(id => [id, pos[id]]));
        const arrows = (quiverEdges || []).map(e => {
          const from = Number(e[0]);
          const to = Number(e[1]);
          if (!cellById.has(from) || !cellById.has(to)) return '';
          const a = cellById.get(from);
          const b = cellById.get(to);
          const dr = b[0] - a[0];
          const dc = b[1] - a[1];
          let dir = '';
          if (dr > 0) dir += 'd'.repeat(dr);
          if (dr < 0) dir += 'u'.repeat(-dr);
          if (dc > 0) dir += 'r'.repeat(dc);
          if (dc < 0) dir += 'l'.repeat(-dc);
          if (!dir) dir = 'loop right';
          const label = e[2] ? ', "' + String(e[2]).replace(/"/g, '\\"') + '"' : '';
          return '\\arrow[' + dir + label + ']';
        }).filter(Boolean);
        return '\\begin{tikzcd}' + nl + rows.join(' \\\\' + nl) + nl + arrows.join(nl) + nl + '\\end{tikzcd}';
      }

      function showQuiverTikz() {
        let modal = document.getElementById('arQuiverTikzModal');
        if (!modal) {
          modal = document.createElement('div');
          modal.id = 'arQuiverTikzModal';
          modal.style.position = 'fixed';
          modal.style.left = '50%';
          modal.style.top = '50%';
          modal.style.transform = 'translate(-50%, -50%)';
          modal.style.width = '620px';
          modal.style.maxWidth = '92vw';
          modal.style.height = '420px';
          modal.style.maxHeight = '86vh';
          modal.style.background = 'white';
          modal.style.border = '1px solid #94a3b8';
          modal.style.borderRadius = '10px';
          modal.style.boxShadow = '0 18px 48px rgba(15,23,42,0.35)';
          modal.style.zIndex = '30000';
          modal.style.display = 'none';
          modal.innerHTML = '<div style="display:flex;align-items:center;justify-content:space-between;padding:9px 12px;border-bottom:1px solid #e5e7eb;background:#f8fafc;border-radius:10px 10px 0 0;font-family:system-ui,-apple-system,Segoe UI,sans-serif;font-size:13px;"><strong id="arTikzTitle">Original quiver source</strong><button id="arTikzClose" style="border:0;background:transparent;font-size:20px;cursor:pointer;">×</button></div><div style="padding:8px 10px;color:#475569;font-size:12px;font-family:system-ui,-apple-system,Segoe UI,sans-serif;">The first line of this file contains a q.uiver.app URL.</div><textarea id="arTikzOutput" style="box-sizing:border-box;width:100%;height:336px;border:0;border-top:1px solid #e5e7eb;padding:10px;font-family:monospace;font-size:12px;white-space:pre;"></textarea>';
          document.body.appendChild(modal);
          const head = modal.firstElementChild;
          if (head) head.style.cursor = 'move';
          makeDraggable(modal, head);
          modal.querySelector('#arTikzClose').addEventListener('click', () => { modal.style.display = 'none'; });
        }
        const title = modal.querySelector('#arTikzTitle');
        if (title) title.textContent = 'Original quiver source: ' + (originalQuiverFilename || 'quiver.txt');
        modal.querySelector('#arTikzOutput').value = originalQuiverText || quiverTikzCode();
        modal.style.display = 'block';
      }

      function originalQuiverUrl() {
        const text = String(originalQuiverText || '').replace(/\\r/g, '');
        const marker = 'https://q.uiver.app/';
        const start = text.indexOf(marker);
        if (start < 0) return '';
        const rest = text.slice(start);
        return (rest.split(/\\s/)[0] || '').trim();
      }

      function parseQuiverAppData() {
        const url = originalQuiverUrl();
        const marker = '#q=';
        const idx = url.indexOf(marker);
        if (idx < 0) return null;
        let encoded = url.slice(idx + marker.length).trim();
        encoded = encoded.replace(/-/g, '+').replace(/_/g, '/');
        while (encoded.length % 4) encoded += '=';
        try {
          const raw = JSON.parse(atob(encoded));
          const count = Number(raw[1] || 0);
          if (!count || raw.length < 2 + count) return null;
          const nodes = raw.slice(2, 2 + count).map((row, i) => ({
            id: i,
            x: Number(row[0] || 0),
            y: Number(row[1] || 0),
            label: String(row[2] == null ? i + 1 : row[2])
          }));
          const arrows = raw.slice(2 + count).filter(row => Array.isArray(row) && row.length >= 3).map(row => ({
            from: Number(row[0]),
            to: Number(row[1]),
            label: String(row[2] == null ? '' : row[2]),
            options: row.find(x => x && typeof x === 'object') || {}
          }));
          return { nodes, arrows };
        } catch (err) {
          return null;
        }
      }

      function renderOriginalQuiverSvg(target) {
        const data = parseQuiverAppData();
        if (!target || !data || !data.nodes.length) return false;
        const scale = 90;
        const pad = 52;
        const xs = data.nodes.map(n => n.x * scale);
        const ys = data.nodes.map(n => n.y * scale);
        const minX = Math.min.apply(null, xs);
        const minY = Math.min.apply(null, ys);
        const maxX = Math.max.apply(null, xs);
        const maxY = Math.max.apply(null, ys);
        const width = Math.max(260, maxX - minX + pad * 2);
        const height = Math.max(160, maxY - minY + pad * 2);
        const pos = new Map();
        data.nodes.forEach(n => pos.set(n.id, { x: n.x * scale - minX + pad, y: n.y * scale - minY + pad, label: n.label }));
        const esc = s => String(s == null ? '' : s).replace(/[&<>\"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[ch]));
        const edgeSvg = data.arrows.map((a, i) => {
          const p = pos.get(a.from);
          const q = pos.get(a.to);
          if (!p || !q) return '';
          if (a.from === a.to) {
            const r = 22;
            const x = p.x;
            const y = p.y;
            return `<path d="M ${x - 10} ${y - 16} C ${x - 48} ${y - 54}, ${x + 48} ${y - 54}, ${x + 10} ${y - 16}" fill="none" stroke="#334155" stroke-width="1.8" marker-end="url(#arrow)"/><text x="${x}" y="${y - 48}" text-anchor="middle" font-family="monospace" font-size="12">${esc(a.label)}</text>`;
          }
          const dx = q.x - p.x;
          const dy = q.y - p.y;
          const len = Math.max(1, Math.hypot(dx, dy));
          const sx = p.x + dx / len * 22;
          const sy = p.y + dy / len * 22;
          const tx = q.x - dx / len * 22;
          const ty = q.y - dy / len * 22;
          const off = Number(a.options && a.options.offset ? a.options.offset : 0);
          const nx = -dy / len * off * 7;
          const ny = dx / len * off * 7;
          const mx = (sx + tx) / 2 + nx;
          const my = (sy + ty) / 2 + ny;
          const path = off ? `M ${sx} ${sy} Q ${mx} ${my} ${tx} ${ty}` : `M ${sx} ${sy} L ${tx} ${ty}`;
          return `<path d="${path}" fill="none" stroke="#334155" stroke-width="1.8" marker-end="url(#arrow)"/><text x="${mx}" y="${my - 6}" text-anchor="middle" font-family="monospace" font-size="12" fill="#111827">${esc(a.label)}</text>`;
        }).join('');
        const nodeSvg = data.nodes.map(n => {
          const p = pos.get(n.id);
          const isRel = /rel/i.test(n.label);
          if (isRel) return `<rect x="${p.x - 38}" y="${p.y - 15}" width="76" height="30" rx="5" fill="#f8fafc" stroke="#94a3b8"/><text x="${p.x}" y="${p.y + 4}" text-anchor="middle" font-family="monospace" font-size="11">${esc(n.label)}</text>`;
          return `<circle cx="${p.x}" cy="${p.y}" r="19" fill="white" stroke="#64748b" stroke-width="1.8"/><text x="${p.x}" y="${p.y + 5}" text-anchor="middle" font-family="monospace" font-weight="700" font-size="14">${esc(n.label)}</text>`;
        }).join('');
        target.innerHTML = `<svg viewBox="0 0 ${width} ${height}" width="100%" height="100%" style="display:block;background:white;"><defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#334155"/></marker></defs>${edgeSvg}${nodeSvg}</svg>`;
        return true;
      }

      function ensureMiniQuiver() {
        if (miniContainer) return;
        miniContainer = document.createElement('div');
        miniContainer.id = 'quiverMiniContainer';
        miniContainer.style.position = 'fixed';
        miniContainer.style.bottom = '10px';
        miniContainer.style.right = '10px';
        miniContainer.style.width = '360px';
        miniContainer.style.background = 'rgba(255,255,255,0.95)';
        miniContainer.style.border = '1px solid #ccc';
        miniContainer.style.padding = '6px';
        miniContainer.style.borderRadius = '6px';
        miniContainer.style.zIndex = '20000';
        miniContainer.style.boxSizing = 'border-box';
        miniContainer.innerHTML = `
          <div id="quiverMiniHeader" style="font-size:12px; margin-bottom:4px; cursor:move; font-weight:600; user-select:none; display:flex; align-items:center; justify-content:space-between; gap:8px;"><span>Quiver Q</span><span style="display:flex;gap:6px;align-items:center;"><button id="quiverOpenBtn" type="button" style="border:0;background:transparent;color:#2563eb;text-decoration:underline;cursor:pointer;font:inherit;font-weight:600;padding:0;">Open in q.uiver</button><button id="quiverTikzBtn" type="button" style="border:0;background:transparent;color:#2563eb;text-decoration:underline;cursor:pointer;font:inherit;font-weight:600;padding:0;">see ${originalQuiverFilename || 'quiver.txt'}</button></span></div>
          <div id="quiverMini" style="width:100%; height:220px; border:1px solid #ddd; background:white; box-sizing:border-box;"></div>
          <div id="quiverRel" style="margin-top:6px; font-size:12px; font-family:monospace; white-space:pre-wrap;"></div>
        `;
        document.body.appendChild(miniContainer);
        makeDraggable(miniContainer, miniContainer.querySelector('#quiverMiniHeader'));
        const relBox = miniContainer.querySelector('#quiverRel');
        const tikzBtn = miniContainer.querySelector('#quiverTikzBtn');
        const openBtn = miniContainer.querySelector('#quiverOpenBtn');
        if (openBtn) {
          openBtn.addEventListener('mousedown', (event) => { event.stopPropagation(); });
          openBtn.addEventListener('click', (event) => {
            event.preventDefault();
            event.stopPropagation();
            const url = originalQuiverUrl();
            if (url) window.open(url, '_blank', 'noopener,noreferrer');
            else alert('No q.uiver.app URL found in ' + (originalQuiverFilename || 'quiver.txt'));
          });
        }
        if (tikzBtn) {
          tikzBtn.addEventListener('mousedown', (event) => { event.stopPropagation(); });
          tikzBtn.addEventListener('click', (event) => { event.preventDefault(); event.stopPropagation(); showQuiverTikz(); });
        }
        relBox.textContent = quiverRel ? `rel := ${quiverRel}` : 'rel := []';
        const mini = miniContainer.querySelector('#quiverMini');
        if (!quiverNodes || quiverNodes.length === 0) {
          miniContainer.querySelector('#quiverMini').textContent = 'No Q data.';
          return;
        }

        // Layout nodes using QuiverStructure
        let layoutPositions = {};
        if (quiverStructure) {
          let s = quiverStructure.trim();
          if (s.startsWith('[') && s.endsWith(']')) s = s.slice(1, -1);
          const rows = s.split(';');
          rows.forEach((row, rowIdx) => {
            let colIdx = 0;
            for (let i = 0; i < row.length; i++) {
              if (/\\d/.test(row[i])) {
                const nid = parseInt(row[i]);
                layoutPositions[nid] = { x: colIdx * 100, y: rowIdx * 100 };
                colIdx++;
              } else {
                colIdx++;
              }
            }
          });
        }

        const nodes = new vis.DataSet(quiverNodes.map(n => {
          const pos = layoutPositions[n.id] || {};
          return {
            id: n.id,
            label: String(n.label),
            shape: 'ellipse',
            font: { face: 'monospace', size: 14, bold: true, color: 'black', vadjust: 0, align: 'center' },
            color: { border: 'gray', background: 'white' },
            borderWidth: 2,
            ...(pos.x !== undefined ? { x: pos.x, y: pos.y } : {})
          };
        }));
        const edges = new vis.DataSet(quiverEdges.map((e, i) => ({
          id: `q_${i}` ,
          from: e[0],
          to: e[1],
          label: e[2] || '',
          arrows: 'to',
          font: { align: 'horizontal', size: 12, face: 'monospace', color: '#333', vadjust: 0 },
          smooth: false
        })));
        miniQuiver = new vis.Network(miniContainer.querySelector('#quiverMini'), { nodes, edges }, {
          physics: false,
          interaction: { dragNodes: true, zoomView: true, dragView: true },
          edges: { arrows: { to: true }, font: { align: 'horizontal' }, smooth: false }
        });
        setTimeout(() => {
          if (miniQuiver) {
            miniQuiver.redraw();
            miniQuiver.fit({ animation: false });
          }
        }, 0);
      }

      function makeDraggable(container, handle) {
        let isDown = false;
        let offsetX = 0;
        let offsetY = 0;
        handle.addEventListener('mousedown', (e) => {
          isDown = true;
          const rect = container.getBoundingClientRect();
          offsetX = e.clientX - rect.left;
          offsetY = e.clientY - rect.top;
          e.preventDefault();
        });
        document.addEventListener('mousemove', (e) => {
          if (!isDown) return;
          container.style.left = `${e.clientX - offsetX}px`;
          container.style.top = `${e.clientY - offsetY}px`;
          container.style.right = 'auto';
          container.style.bottom = 'auto';
        });
        document.addEventListener('mouseup', () => {
          isDown = false;
        });
      }

      function toggleMiniQuiver(show) {
        if (show) {
          ensureMiniQuiver();
          if (miniContainer) miniContainer.style.display = 'block';
        } else {
          if (miniContainer) miniContainer.style.display = 'none';
        }
      }

      function updateEdgeCurvature(netObj, delta) {
        if (!netObj) return;
        const selectedEdges = netObj.getSelectedEdges();
        if (selectedEdges.length > 0) {
          snapshot();
          selectedEdges.forEach(id => {
            const edge = netObj.body.data.edges.get(id);
            let round = 0;
            let type = 'curvedCW';
            if (edge.smooth && typeof edge.smooth === 'object') {
              round = edge.smooth.roundness || 0;
              type = edge.smooth.type || 'curvedCW';
            }
            let signed = (type === 'curvedCCW') ? -round : round;
            let next = Math.max(-1, Math.min(1, signed + delta));
            let nextType = next < 0 ? 'curvedCCW' : 'curvedCW';
            let nextRound = Math.abs(next);
            const nextSmooth = { enabled: true, type: nextType, roundness: nextRound };
            edgeCurveMemory.set(String(id), nextSmooth);
            netObj.body.data.edges.update({ id, smooth: nextSmooth });
          });
        }
      }

      // --- Undo / Redo (with positions) ---
      const undoStack = [];
      const redoStack = [];
      let isRestoring = false;
      function snapshot() {
        if (isRestoring) return;
        const positions = network.getPositions();
        const nodes = network.body.data.nodes.get().map(n => {
          const pos = positions[n.id];
          if (pos) {
            return { ...n, x: pos.x, y: pos.y };
          }
          return n;
        });
        const edges = network.body.data.edges.get();
        undoStack.push({ nodes, edges });
        redoStack.length = 0;
      }
      function restore(state) {
        if (!state) return;
        isRestoring = true;
        network.body.data.nodes.clear();
        network.body.data.edges.clear();
        network.body.data.nodes.add(state.nodes);
        network.body.data.edges.add(state.edges);
        state.nodes.forEach(n => {
          if (typeof n.x === 'number' && typeof n.y === 'number') {
            network.moveNode(n.id, n.x, n.y);
          }
        });
        isRestoring = false;
      }
      function undo() {
        if (undoStack.length === 0) return;
        const current = { nodes: network.body.data.nodes.get(), edges: network.body.data.edges.get() };
        const prev = undoStack.pop();
        redoStack.push(current);
        restore(prev);
      }
      function redo() {
        if (redoStack.length === 0) return;
        const current = { nodes: network.body.data.nodes.get(), edges: network.body.data.edges.get() };
        const next = redoStack.pop();
        undoStack.push(current);
        restore(next);
      }
      document.addEventListener('keydown', function(e) {
        const listEl = document.getElementById('tiltingList');
        const tiltingVisible = listEl && listEl.style.display !== 'none';
        if (tiltingVisible && (e.key === 'ArrowUp' || e.key === 'ArrowDown')) {
          e.preventDefault();
          const dir = (e.key === 'ArrowUp') ? -1 : 1;
          const idx = getActiveTiltingIndex();
          selectTiltingByIndex(idx + dir);
          return;
        }
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z') {
          e.preventDefault();
          undo();
        } else if ((e.ctrlKey || e.metaKey) && (e.key.toLowerCase() === 'y' || (e.shiftKey && e.key.toLowerCase() === 'z'))) {
          e.preventDefault();
          redo();
        } else if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
          const delta = (e.key === 'ArrowRight') ? 0.1 : -0.1;
          updateEdgeCurvature(network, delta);
          updateEdgeCurvature(miniQuiver, delta);
        }
      });
      // initial snapshot
      snapshot();

      function snapNode(nodeId) {
        const position = network.getPositions([nodeId]);
        const x = position[nodeId].x, y = position[nodeId].y;
        const snappedX = Math.round(x / gridSize) * gridSize;
        const snappedY = Math.round(y / gridSize) * gridSize;
        network.moveNode(nodeId, snappedX, snappedY);
      }

      function getEdgeColor(edge) {
        if (edge.color && typeof edge.color === 'object' && edge.color.color) {
          return edge.color.color;
        }
        if (typeof edge.color === 'string') {
          return edge.color;
        }
        return '#000000';
      }

      function isGoldenEdge(edge) {
        return goldenEdgeSet.has(`${edge.from}->${edge.to}`);
      }

      function isDimmedEdge(edge) {
        const c = getEdgeColor(edge);
        return c === '#cccccc' || c === 'lightgray' || c === 'lightgrey' || c === '#ffe9a6';
      }

      function isBlackEdge(edge) {
        const c = getEdgeColor(edge);
        return c === '#000000' || c === 'black' || c === '#cccccc' || c === 'lightgray' || c === 'lightgrey';
      }

      function isIrreducibleEdge(edge) {
        if (!edge) return false;
        const id = edge.id === undefined || edge.id === null ? '' : String(edge.id);
        return !/^(tr|syz|cosyz|rad|corad|hom|ext)_/.test(id);
      }

      function isDimmableAREdge(edge) {
        return isIrreducibleEdge(edge) || String(edge.id || '').startsWith('tr_') || isGoldenEdge(edge);
      }

      function isTranslationEdge(edge) {
        const c = getEdgeColor(edge);
        return isGoldenEdge(edge) || c === '#ffd700' || c === '#ffe9a6' || c === 'gold';
      }

      function isOrangeEdge(edge) {
        const c = getEdgeColor(edge);
        return isGoldenEdge(edge) || c === '#ffd700' || c === '#ffe9a6' || c === 'gold' || c === 'orange' || c === '#ffa500';
      }

      function toggleEdges(predicate, visible) {
        const edges = network.body.data.edges.get();
        const updates = edges.filter(predicate).map(e => ({ id: e.id, hidden: !visible }));
        if (updates.length) network.body.data.edges.update(updates);
      }

      function getComponentNodes(startNodeId, edges) {
        const adj = new Map();
        edges.forEach(e => {
          if (!adj.has(e.from)) adj.set(e.from, new Set());
          if (!adj.has(e.to)) adj.set(e.to, new Set());
          adj.get(e.from).add(e.to);
          adj.get(e.to).add(e.from);
        });
        const visited = new Set();
        const stack = [startNodeId];
        visited.add(startNodeId);
        while (stack.length) {
          const n = stack.pop();
          const nbrs = adj.get(n) || new Set();
          nbrs.forEach(m => {
            if (!visited.has(m)) {
              visited.add(m);
              stack.push(m);
            }
          });
        }
        return visited;
      }

      function hasDirectedCycle(nodesSet, edges) {
        const adj = new Map();
        nodesSet.forEach(n => adj.set(n, []));
        edges.forEach(e => {
          if (nodesSet.has(e.from) && nodesSet.has(e.to)) {
            adj.get(e.from).push(e.to);
          }
        });
        const WHITE = 0, GRAY = 1, BLACK = 2;
        const color = new Map();
        nodesSet.forEach(n => color.set(n, WHITE));
        let found = false;
        function dfs(u) {
          if (found) return;
          color.set(u, GRAY);
          for (const v of adj.get(u)) {
            const c = color.get(v);
            if (c === GRAY) {
              found = true;
              return;
            }
            if (c === WHITE) dfs(v);
          }
          color.set(u, BLACK);
        }
        for (const n of nodesSet) {
          if (color.get(n) === WHITE) dfs(n);
          if (found) break;
        }
        return found;
      }

      function adjustIncomingEdgePosition(a, b, edges, requireOrange) {
        // Find incoming edge c -> b (prefer orange edges)
        let candidate = null;
        let foundOrange = null;
        for (const e of edges) {
          if (e.to === b) {
            if (!candidate) candidate = e;
            if (isOrangeEdge(e)) {
              foundOrange = e;
              break;
            }
          }
        }
        const chosen = requireOrange ? foundOrange : (foundOrange || candidate);
        if (!chosen || chosen.from === a) return null;
        const c = chosen.from;
        const posA = network.getPositions([a])[a];
        const posB = network.getPositions([b])[b];
        if (!posA || !posB) return null;
        const newCx = 2 * posB.x - posA.x;
        const newCy = 2 * posB.y - posA.y;
        network.moveNode(c, newCx, newCy);
        return { a: b, b: c };
      }

      function handleLongPressOnOrangeEdge(edge) {
        const edges = network.body.data.edges.get();
        const component = getComponentNodes(edge.from, edges);
        const hasCycle = hasDirectedCycle(component, edges);
        let a = edge.to;
        let b = edge.from;
        if (hasCycle) {
          adjustIncomingEdgePosition(a, b, edges, true);
          return;
        }
        // No directed cycle: recurse along chain until no incoming edge
        const visited = new Set();
        while (true) {
          const key = `${a}->${b}`;
          if (visited.has(key)) break;
          visited.add(key);
          const step = adjustIncomingEdgePosition(a, b, edges, true);
          if (!step) break;
          a = step.a;
          b = step.b;
        }
      }

      network.on("dragStart", function (params) {
        if (params.nodes.length > 0) {
          snapshot();
        }
      });
      network.on("dragEnd", function (params) {
        if (params.nodes.length > 0) {
          snapNode(params.nodes[0]);
          if (showLabels) updateIdLabels();
          if (showPd) updatePdLabels();
          if (showId) updateIdValueLabels();
          if (showTop) updateTopLabels();
          if (showSoc) updateSocLabels();
        }
      });

      network.on('afterDrawing', function() {
        if (showLabels) updateIdLabels();
        if (showPd) updatePdLabels();
        if (showId) updateIdValueLabels();
        if (showTop) updateTopLabels();
        if (showSoc) updateSocLabels();
      });

      network.on('hold', function(p) {
        if (p.edges.length > 0) {
          const edge_id = p.edges[0];
          const edge = network.body.data.edges.get(edge_id);
          if (edge && isOrangeEdge(edge)) {
            snapshot();
            handleLongPressOnOrangeEdge(edge);
            network.unselectAll();
          }
        }
      });

      network.on('doubleClick', function(p) {
        if (p.nodes.length > 0) {
          const nodeId = p.nodes[0];
          const n_id = Number(nodeId);
          const labelKey = Number.isFinite(n_id) ? n_id : nodeId;
          const current = customTexLabels.get(labelKey) || customTexLabels.get(String(nodeId)) || '';
          const releaseNodeInteractionState = () => {
            network.unselectAll();
            if (network.body && network.body.nodes && network.body.nodes[nodeId]) {
              network.body.nodes[nodeId].selected = false;
            }
            if (network.selectionHandler && typeof network.selectionHandler.unselectAll === 'function') {
              network.selectionHandler.unselectAll();
            }
            if (network.interactionHandler) {
              network.interactionHandler.dragging = false;
              network.interactionHandler.drag = {};
            }
            if (network.canvas && network.canvas.frame && typeof network.canvas.frame.blur === 'function') {
              network.canvas.frame.blur();
            }
            network.setOptions({ interaction: { dragNodes: true } });
            network.redraw();
          };
          network.setOptions({ interaction: { dragNodes: false } });
          releaseNodeInteractionState();
          setTimeout(() => {
            const input = prompt('Custom TeX label for node ' + String(nodeId), current);
            if (input === null) {
              releaseNodeInteractionState();
              setTimeout(releaseNodeInteractionState, 0);
              setTimeout(releaseNodeInteractionState, 80);
              return;
            }
            const value = input.trim();
            if (value) {
              customTexLabels.set(labelKey, value);
              customTexLabels.set(String(nodeId), value);
            } else {
              customTexLabels.delete(labelKey);
              customTexLabels.delete(String(nodeId));
            }
            releaseNodeInteractionState();
            if (typeof window.refreshCustomNodeLabelMode === 'function') {
              window.refreshCustomNodeLabelMode(nodeId);
            } else {
              console.error('refreshCustomNodeLabelMode is not available');
            }
            setTimeout(releaseNodeInteractionState, 0);
            setTimeout(releaseNodeInteractionState, 80);
          }, 0);
          return;
        }
        if (p.edges.length > 0) {
          const edge_id = p.edges[0];
          const edge = network.body.data.edges.get(edge_id);
          if (!edge || !isDimmableAREdge(edge)) return;
          const blackColor = '#000000';
          const lightGray = '#cccccc';
          const goldColor = '#ffd700';
          const lightGold = '#ffe9a6';
          const currentColor = getEdgeColor(edge);
          const isGold = String(edge.id || '').startsWith('tr_') || isGoldenEdge(edge) || currentColor === goldColor || currentColor === lightGold || currentColor === 'gold';
          let newColor = currentColor;
          if (isGold) {
            newColor = (currentColor === lightGold) ? goldColor : lightGold;
          } else {
            newColor = (currentColor === lightGray) ? blackColor : lightGray;
          }
          snapshot();
          network.body.data.edges.update({ id: edge_id, color: { color: newColor } });
        }
      });

      // defaults
      applyNodeLabelMode('dimension');
      togglePdLabels(false);
      toggleIdValueLabels(false);
      toggleTopLabels(false);
      toggleSocLabels(false);
      toggleNodeBorders(true);
    </script>
    """
    js_injection = js_injection.replace("{{GOLDEN_EDGES}}", golden_edges_js_string)
    js_injection = js_injection.replace("{{TORS_IDS}}", tors_ids_js)
    js_injection = js_injection.replace("{{REFL_IDS}}", refl_ids_js)
    js_injection = js_injection.replace("{{GP_IDS}}", gp_ids_js)
    js_injection = js_injection.replace("{{GI_IDS}}", gi_ids_js)
    js_injection = js_injection.replace("{{ZERO_OBJECT_IDS}}", zero_ids_js)
    js_injection = js_injection.replace("{{SYZ_EDGES}}", syz_edges_js)
    js_injection = js_injection.replace("{{COSYZ_EDGES}}", cosyz_edges_js)
    js_injection = js_injection.replace("{{RAD_EDGES}}", radical_edges_js)
    js_injection = js_injection.replace("{{CORAD_EDGES}}", coradical_edges_js)
    js_injection = js_injection.replace("{{Q_NODES}}", q_nodes_js)
    js_injection = js_injection.replace("{{Q_EDGES}}", q_edges_js)
    js_injection = js_injection.replace("{{Q_REL}}", q_rel_js)
    js_injection = js_injection.replace("{{MODULE_DATA_GAP}}", module_data_gap_js)
    js_injection = js_injection.replace("{{HOM_EDGES}}", hom_edges_js)
    js_injection = js_injection.replace("{{EXT_EDGES}}", ext_edges_js)
    js_injection = js_injection.replace("{{TILTING_DATA}}", tilting_js)
    js_injection = js_injection.replace("{{TORSION_PAIR_DATA}}", torsion_pairs_js)
    js_injection = js_injection.replace("{{TORSION_PAIR_BUCKETS}}", torsion_pair_buckets_js)
    js_injection = js_injection.replace("{{COTORSION_PAIR_DATA}}", cotorsion_pairs_js)
    js_injection = js_injection.replace("{{SUPPORT_TAU_TILTING_DATA}}", support_tau_js)
    js_injection = js_injection.replace("{{ALMOST_SUPPORT_TAU_TILTING_DATA}}", almost_support_tau_js)
    js_injection = js_injection.replace("{{PDID_MAP}}", pdid_js)
    js_injection = js_injection.replace("{{TOP_SOC_MAP}}", top_soc_js)
    js_injection = js_injection.replace("{{Q_STRUCTURE}}", q_structure_js)
    js_injection = js_injection.replace("{{ORIGINAL_QUIVER_TEXT}}", original_quiver_text_js)
    js_injection = js_injection.replace("{{ORIGINAL_QUIVER_FILENAME}}", original_quiver_filename_js)

    # ------------------- JAVASCRIPT MODIFICATION END -------------------
    final_html = html_content.replace('</body>', js_injection + '</body>')
    
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(final_html)
        print(f"Success: interactive graph saved to: '{output_filename}'")
    except Exception as e:
        print(f"Error writing file: {e}")

# ===== Step3.ipynb cell 6 =====
def _inject_tilting_graph_js(html: str) -> str:

    return html

    marker = "/* TILTING_GRAPH_INJECT */"

    if marker in html:

        return html

    js = r"""

    <script type=\"text/javascript\">

    /* TILTING_GRAPH_INJECT */

    (function() {

      let tiltingGraphContainer = null;

      let tiltingGraphNetwork = null;

      let tiltingDataLocal = [];



      function diffByOne(a, b) {

        if (!a || !b || a.size !== b.size) return false;

        let diff = 0;

        for (const x of a) if (!b.has(x)) diff++;

        for (const x of b) if (!a.has(x)) diff++;

        return diff === 2;

      }



      function makeDraggable(container, handle) {

        let isDown = false;

        let offsetX = 0;

        let offsetY = 0;

        handle.addEventListener('mousedown', (e) => {

          isDown = true;

          const rect = container.getBoundingClientRect();

          offsetX = e.clientX - rect.left;

          offsetY = e.clientY - rect.top;

          e.preventDefault();

        });

        document.addEventListener('mousemove', (e) => {

          if (!isDown) return;

          container.style.left = `${e.clientX - offsetX}px`;

          container.style.top = `${e.clientY - offsetY}px`;

          container.style.right = 'auto';

          container.style.bottom = 'auto';

        });

        document.addEventListener('mouseup', () => { isDown = false; });

      }



      function ensureTiltingGraphContainer() {

        if (tiltingGraphContainer) return tiltingGraphContainer;

        tiltingGraphContainer = document.createElement('div');

        tiltingGraphContainer.id = 'tiltingGraphContainer';

        tiltingGraphContainer.style.position = 'absolute';

        tiltingGraphContainer.style.bottom = '10px';

        tiltingGraphContainer.style.left = '10px';

        tiltingGraphContainer.style.width = '360px';

        tiltingGraphContainer.style.background = 'rgba(255,255,255,0.95)';

        tiltingGraphContainer.style.border = '1px solid #ccc';

        tiltingGraphContainer.style.padding = '6px';

        tiltingGraphContainer.style.borderRadius = '6px';

        tiltingGraphContainer.style.zIndex = '998';

        tiltingGraphContainer.innerHTML = `

          <div id=\"tiltingGraphHeader\" style=\"font-size:12px; margin-bottom:4px; cursor:move; font-weight:600;\">Tilting L</div>

          <div id=\"tiltingGraph\" style=\"width:340px; height:220px; border:1px solid #ddd; background:white;\"></div>

          <div id=\"tiltingDetails\" style=\"margin-top:6px; font-size:12px; font-family:monospace; white-space:pre-wrap;\"></div>

        `;

        document.body.appendChild(tiltingGraphContainer);

        makeDraggable(tiltingGraphContainer, tiltingGraphContainer.querySelector('#tiltingGraphHeader'));

        return tiltingGraphContainer;

      }



      function showTiltingDetails(idx) {

        const detail = document.getElementById('tiltingDetails');

        if (!detail || !tiltingDataLocal || !tiltingDataLocal.length) return;

        const item = tiltingDataLocal[idx];

        if (!item) return;

        const L = (item.L || []).join(', ');

        const F = (item.F || []).join(', ');

        const T = (item.T || []).join(', ');

        const tags = (typeof tiltingTags === 'function') ? tiltingTags(item).join(', ') : '';

        detail.innerHTML = `L${idx + 1}: [${L}]<br>F: [${F}]<br>T: [${T}]<br>${tags}`;

      }



      function selectTiltingNode(idx) {

        if (!tiltingDataLocal || !tiltingDataLocal.length) return;

        const clamped = Math.max(0, Math.min(idx, tiltingDataLocal.length - 1));

        if (tiltingGraphNetwork) {

          tiltingGraphNetwork.selectNodes([clamped]);

          tiltingGraphNetwork.focus(clamped, { scale: 1.0 });

        }

        showTiltingDetails(clamped);

        if (window.applyTiltingHighlight) window.applyTiltingHighlight(tiltingDataLocal[clamped]);

      }



      function buildTiltingGraph() {

        tiltingDataLocal = (window.tiltingData || (typeof tiltingData !== 'undefined' ? tiltingData : [])) || [];

        if (!tiltingDataLocal.length) return;



        const listEl = document.getElementById('tiltingList');

        if (listEl) listEl.style.display = 'none';



        const container = ensureTiltingGraphContainer();

        container.style.display = 'block';

        const graphDiv = container.querySelector('#tiltingGraph');

        graphDiv.innerHTML = '';



        const nodes = [];

        const edges = [];

        const sets = tiltingDataLocal.map(item => new Set((item.L || []).map(Number)));

        for (let i = 0; i < tiltingDataLocal.length; i++) {

          nodes.push({ id: i, label: `L${i + 1}` });

        }

        for (let i = 0; i < sets.length; i++) {

          for (let j = i + 1; j < sets.length; j++) {

            if (diffByOne(sets[i], sets[j])) {

              edges.push({ from: i, to: j });

            }

          }

        }



        const data = {

          nodes: new vis.DataSet(nodes),

          edges: new vis.DataSet(edges)

        };

        const options = {

          physics: { enabled: true },

          interaction: { dragNodes: true, dragView: true, zoomView: true },

          edges: { smooth: false },

          nodes: { shape: 'dot', size: 12, font: { size: 12 } }

        };

        tiltingGraphNetwork = new vis.Network(graphDiv, data, options);

        tiltingGraphNetwork.on('click', function(params) {

          if (params.nodes.length > 0) {

            selectTiltingNode(params.nodes[0]);

          }

        });

        selectTiltingNode(0);

      }



      function hookToggleHide() {

        const toggle = document.getElementById('tiltingToggle');

        if (!toggle || toggle.__tiltingGraphHooked) return;

        toggle.__tiltingGraphHooked = true;

        toggle.addEventListener('change', (e) => {

          if (!e.target.checked && tiltingGraphContainer) {

            tiltingGraphContainer.style.display = 'none';

          }

        });

      }



      // Override tilting UI hooks

      window.renderTiltingList = function() {

        buildTiltingGraph();

        hookToggleHide();

      };

      window.setActiveTilting = function(idx) {

        selectTiltingNode(idx);

      };

      window.getActiveTiltingIndex = function() {

        if (tiltingGraphNetwork) {

          const sel = tiltingGraphNetwork.getSelectedNodes();

          return sel.length ? sel[0] : -1;

        }

        return -1;

      };

      window.selectTiltingByIndex = function(idx) {

        selectTiltingNode(idx);

      };



      // Hover tooltips are disabled.

    })();

    </script>

    """

    return html.replace("</body>", js + "</body>")



def create_and_save_quiver_html_with_tilting_graph(quiver_filepath, output_filename):

    create_and_save_quiver_html(quiver_filepath, output_filename)

    try:

        with open(output_filename, 'r', encoding='utf-8') as f:

            html = f.read()

        html = _inject_tilting_graph_js(html)

        with open(output_filename, 'w', encoding='utf-8') as f:

            f.write(html)

        print("Success: unified list-style tilting layout enabled")

    except Exception as e:

        print(f"Error injecting tilting L graph: {e}")


# ===== Step3.ipynb cell 7 =====
def _inject_tau_toggle_html(html: str) -> str:
    marker = "/* TAU_TOGGLE_INJECT */"
    if marker in html:
        return html

    js = r"""
    <script type=\"text/javascript\">
    /* TAU_TOGGLE_INJECT */
    (function() {
      function getGoldenEdges() {
        if (typeof goldenEdges !== 'undefined' && Array.isArray(goldenEdges)) {
          return goldenEdges;
        }
        return [];
      }

      function removeTranslationEdges() {
        if (!window.network || !window.network.body || !window.network.body.data) return;
        const existing = window.network.body.data.edges.get({
          filter: (edge) => edge.id && String(edge.id).startsWith('tr_')
        }).map(e => e.id);
        if (existing.length) window.network.body.data.edges.remove(existing);
      }

      function addTranslationEdges() {
        if (!window.network || !window.network.body || !window.network.body.data) return;
        const edges = getGoldenEdges();
        if (!edges.length) return;
        removeTranslationEdges();
        const toAdd = edges.map((e, i) => ({
          id: `tr_${i}`,
          from: e[0],
          to: e[1],
          color: 'gold',
          width: 3,
          arrows: 'to',
          dashes: false
        }));
        window.network.body.data.edges.add(toAdd);
      }

      function syncTranslationEdges(visible) {
        if (visible) {
          addTranslationEdges();
        } else {
          removeTranslationEdges();
        }
      }

      function init() {
        const t = document.getElementById('trToggle');
        if (!t) return;
        t.addEventListener('change', (e) => {
          syncTranslationEdges(e.target.checked);
        });
        syncTranslationEdges(t.checked);
      }

      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
      } else {
        init();
      }
    })();
    </script>
    """

    if "</body>" in html:
        return html.replace("</body>", js + "</body>")
    return html + js


def patch_tau_toggle_file(html_path: str) -> None:
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()
        html = _inject_tau_toggle_html(html)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print("✅ Injected tau-toggle translation edges.")
    except Exception as e:
        print(f"❌ Failed to inject tau-toggle: {e}")

# ===== Step3.ipynb cell 8 =====
def format_dim_vector(dim_list, quiver_structure: Union[str, None]):
    # Special labels like pd/id
    if isinstance(dim_list, dict) and 'pd' in dim_list and 'id' in dim_list:
        
        def _pdid_val(x):
            return '∞' if x == -1 or x == '-1' else str(x)
        return f"pd={_pdid_val(dim_list['pd'])}, id={_pdid_val(dim_list['id'])}"
    if isinstance(dim_list, str):
        return dim_list
    if not dim_list:
        return ""

    # Use QuiverStructure layout if provided
    if quiver_structure:
        s = quiver_structure.strip()
        if s.startswith('[') and s.endswith(']'):
            s = s[1:-1]
        rows = s.split(';')
        width = max(len(str(x)) for x in dim_list)
        rendered_rows = []
        for row in rows:
            cells = []
            for ch in row:
                if ch.isdigit():
                    idx = int(ch) - 1
                    if 0 <= idx < len(dim_list):
                        cells.append(str(dim_list[idx]).rjust(width))
                    else:
                        cells.append('?' * width)
                elif ch in {'-', ' '}:
                    cells.append(' ' * width)
                else:
                    cells.append(str(ch).rjust(width))
            rendered_rows.append(' '.join(cells))
        return '\n'.join(rendered_rows)

    # Fallback: compact list
    return ''.join(str(dim_list).split())

# ===== Step3.ipynb cell 9 =====
from pathlib import Path

def locate_project_dir(prefer: Union[Path, None] = None) -> Path:
    """Try to locate the ARquiver project directory at runtime.

    Strategy:
    - Prefer an explicit path if given.
    - Try cwd and some common locations under $HOME.
    - Validate candidates by checking for project markers.
    """

    def is_project_dir(p: Path) -> bool:
        if not p or not p.exists() or not p.is_dir():
            return False
        # project markers
        if (p / "PythonPlot.ipynb").exists():
            return True
        if (p / "DrawARquiver.ipynb").exists():
            return True
        if (p / "lib").exists() and (p / "lib").is_dir():
            return True
        return False

    candidates: list[Path] = []
    if prefer is not None:
        candidates.append(prefer)

    cwd = Path.cwd()
    home = Path.home()

    # common candidates
    candidates.extend([
        cwd,
        cwd / "ARquiver",
        cwd / "GapDocs" / "ARquiver",
        home / "GapDocs" / "ARquiver",
        home / "ARquiver",
    ])

    # also try scanning a couple of well-known parent folders (cheap, non-recursive)
    for parent in [cwd, home, home / "GapDocs"]:
        if parent.exists() and parent.is_dir():
            candidates.append(parent / "ARquiver")

    seen: set[Path] = set()
    for p in candidates:
        p = p.expanduser().resolve()
        if p in seen:
            continue
        seen.add(p)
        if is_project_dir(p):
            return p

    raise FileNotFoundError(
        "Cannot locate ARquiver project directory. "
        "Tried cwd and common $HOME locations; please set BASE_DIR manually."
    )


# ===== Step3.ipynb cell 11 =====
def _inject_tilting_graph_fallback(html: str) -> str:
    if not html.lstrip().lower().startswith("<!doctype html>"):
        html = "<!DOCTYPE html>\n" + html

    marker = "/* TILTING_GRAPH_FALLBACK */"
    if marker in html:
        return html

    js = r"""
    <script type=\"text/javascript\">
    /* TILTING_GRAPH_FALLBACK */
    (function() {
      function ensureStyle() {
        if (document.getElementById('tiltingGraphStyle')) return;
        const style = document.createElement('style');
        style.id = 'tiltingGraphStyle';
        style.textContent = `
          #tiltingGraphContainer {
            position: fixed !important;
            left: 10px !important;
            bottom: 10px !important;
            z-index: 9999 !important;
            box-shadow: 0 2px 10px rgba(0,0,0,0.15);
          }
        `;
        document.head.appendChild(style);
      }

      function forceShowContainer() {
        const c = document.getElementById('tiltingGraphContainer');
        if (!c) return;
        c.style.display = 'block';
        c.style.position = 'fixed';
        c.style.zIndex = '9999';
      }

      function buildIfChecked() {
        ensureStyle();
        const toggle = document.getElementById('tiltingToggle');
        if (!toggle) return;
        if (toggle.checked && typeof window.renderTiltingList === 'function') {
          window.renderTiltingList();
          setTimeout(forceShowContainer, 0);
        }
      }

      function onChange(e) {
        ensureStyle();
        if (e.target.checked) {
          if (typeof window.renderTiltingList === 'function') {
            window.renderTiltingList();
            setTimeout(forceShowContainer, 0);
          }
        } else {
          const c = document.getElementById('tiltingGraphContainer');
          if (c) c.style.display = 'none';
        }
      }

      const toggle = document.getElementById('tiltingToggle');
      if (toggle) {
        ensureStyle();
        toggle.addEventListener('change', onChange);
        setTimeout(buildIfChecked, 0);
        setTimeout(buildIfChecked, 300);
      } else {
        window.addEventListener('load', function() {
          const t = document.getElementById('tiltingToggle');
          if (!t) return;
          ensureStyle();
          t.addEventListener('change', onChange);
          setTimeout(buildIfChecked, 0);
          setTimeout(buildIfChecked, 300);
        });
      }
    })();
    </script>
    """

    if "</body>" in html:
        return html.replace("</body>", js + "\n</body>")
    return html + js






# ===== Step3.ipynb cell 12 =====
def _inject_tilting_graph_override(html: str) -> str:
    marker = "/* TILTING_GRAPH_OVERRIDE */"
    if marker in html:
        return html

    js = r"""
    <script type=\"text/javascript\">
    /* TILTING_GRAPH_OVERRIDE */
    (function() {
      function ensureTiltingWindow() {
        let container = document.getElementById('tiltingGraphContainer');
        if (container) return container;

        container = document.createElement('div');
        container.id = 'tiltingGraphContainer';
        container.style.position = 'fixed';
        container.style.left = '10px';
        container.style.bottom = '10px';
        container.style.width = '380px';
        container.style.minWidth = '280px';
        container.style.minHeight = '220px';
        container.style.background = 'rgba(255,255,255,0.95)';
        container.style.border = '1px solid #ccc';
        container.style.padding = '6px';
        container.style.borderRadius = '6px';
        container.style.zIndex = '9999';
        container.style.boxShadow = '0 2px 10px rgba(0,0,0,0.15)';

        container.innerHTML = `
          <div class=\"tilting-resize-handle tilting-resize-left\" data-resize=\"left\" style=\"position:absolute; left:0; top:8px; bottom:8px; width:7px; cursor:ew-resize; z-index:2;\"></div>
          <div class=\"tilting-resize-handle tilting-resize-right\" data-resize=\"right\" style=\"position:absolute; right:0; top:8px; bottom:8px; width:7px; cursor:ew-resize; z-index:2;\"></div>
          <div class=\"tilting-resize-handle tilting-resize-top\" data-resize=\"top\" style=\"position:absolute; left:8px; right:8px; top:0; height:7px; cursor:ns-resize; z-index:2;\"></div>
          <div class=\"tilting-resize-handle tilting-resize-bottom\" data-resize=\"bottom\" style=\"position:absolute; left:8px; right:8px; bottom:0; height:7px; cursor:ns-resize; z-index:2;\"></div>
          <div class=\"tilting-resize-handle tilting-resize-nw\" data-resize=\"top left\" style=\"position:absolute; left:0; top:0; width:9px; height:9px; cursor:nwse-resize; z-index:2;\"></div>
          <div class=\"tilting-resize-handle tilting-resize-ne\" data-resize=\"top right\" style=\"position:absolute; right:0; top:0; width:9px; height:9px; cursor:nesw-resize; z-index:2;\"></div>
          <div class=\"tilting-resize-handle tilting-resize-sw\" data-resize=\"bottom left\" style=\"position:absolute; left:0; bottom:0; width:9px; height:9px; cursor:nesw-resize; z-index:2;\"></div>
          <div class=\"tilting-resize-handle tilting-resize-se\" data-resize=\"bottom right\" style=\"position:absolute; right:0; bottom:0; width:9px; height:9px; cursor:nwse-resize; z-index:2;\"></div>
          <div id=\"tiltingGraphHeader\" style=\"font-size:12px; margin-bottom:4px; cursor:move; font-weight:600; user-select:none;\">Tilting</div>
          <div id=\"tiltingGraph\" style=\"width:100%; height:240px; border:1px solid #ddd; background:white; box-sizing:border-box;\"></div>
          <div id=\"tiltingDetails\" style=\"margin-top:6px; font-size:12px; font-family:monospace; white-space:pre-wrap;\"></div>
        `;

        document.body.appendChild(container);

        const header = container.querySelector('#tiltingGraphHeader');
        let isDown = false;
        let offsetX = 0;
        let offsetY = 0;
        header.addEventListener('mousedown', (e) => {
          isDown = true;
          const rect = container.getBoundingClientRect();
          offsetX = e.clientX - rect.left;
          offsetY = e.clientY - rect.top;
          container.style.left = rect.left + 'px';
          container.style.top = rect.top + 'px';
          container.style.right = 'auto';
          container.style.bottom = 'auto';
          container.style.width = rect.width + 'px';
          container.style.height = rect.height + 'px';
          e.preventDefault();
        });

        let resizing = null;
        container.querySelectorAll('.tilting-resize-handle').forEach((handle) => {
          handle.addEventListener('mousedown', (e) => {
            const rect = container.getBoundingClientRect();
            container.style.left = rect.left + 'px';
            container.style.top = rect.top + 'px';
            container.style.right = 'auto';
            container.style.bottom = 'auto';
            container.style.width = rect.width + 'px';
            container.style.height = rect.height + 'px';
            resizing = { dirs: handle.dataset.resize.split(' '), x: e.clientX, y: e.clientY, left: rect.left, top: rect.top, width: rect.width, height: rect.height };
            e.preventDefault();
            e.stopPropagation();
          });
        });

        document.addEventListener('mousemove', (e) => {
          if (isDown) {
            const width = container.offsetWidth || 380;
            const height = container.offsetHeight || 300;
            container.style.left = Math.max(0, Math.min(window.innerWidth - 60, e.clientX - offsetX)) + 'px';
            container.style.top = Math.max(0, Math.min(window.innerHeight - 40, e.clientY - offsetY)) + 'px';
            if (Number.parseFloat(container.style.left) + width > window.innerWidth) container.style.left = Math.max(0, window.innerWidth - width - 4) + 'px';
            if (Number.parseFloat(container.style.top) + height > window.innerHeight) container.style.top = Math.max(0, window.innerHeight - height - 4) + 'px';
          }
          if (resizing) {
            let left = resizing.left;
            let top = resizing.top;
            let width = resizing.width;
            let height = resizing.height;
            const dx = e.clientX - resizing.x;
            const dy = e.clientY - resizing.y;
            if (resizing.dirs.includes('right')) width = resizing.width + dx;
            if (resizing.dirs.includes('bottom')) height = resizing.height + dy;
            if (resizing.dirs.includes('left')) { width = resizing.width - dx; left = resizing.left + dx; }
            if (resizing.dirs.includes('top')) { height = resizing.height - dy; top = resizing.top + dy; }
            if (width < 280) { if (resizing.dirs.includes('left')) left -= 280 - width; width = 280; }
            if (height < 220) { if (resizing.dirs.includes('top')) top -= 220 - height; height = 220; }
            left = Math.max(0, left);
            top = Math.max(0, top);
            width = Math.min(width, window.innerWidth - left - 4);
            height = Math.min(height, window.innerHeight - top - 4);
            container.style.left = left + 'px';
            container.style.top = top + 'px';
            container.style.width = width + 'px';
            container.style.height = height + 'px';
            const graph = container.querySelector('#tiltingGraph');
            if (graph) graph.style.height = Math.max(120, height - 84) + 'px';
            if (window.__tiltingGraphNetwork) window.__tiltingGraphNetwork.redraw();
          }
        });
        document.addEventListener('mouseup', () => { isDown = false; resizing = null; });

        return container;
      }

      function intersectionSize(a, b) {
        const setB = new Set((b || []).map(Number));
        let count = 0;
        (a || []).forEach((x) => { if (setB.has(Number(x))) count++; });
        return count;
      }

      function buildTiltingGraphOverride() {
        const data = (window.tiltingData || (typeof tiltingData !== 'undefined' ? tiltingData : [])) || [];
        if (!data.length) return;

        const listEl = document.getElementById('tiltingList');
        if (listEl) listEl.style.display = 'none';

        const container = ensureTiltingWindow();
        container.style.display = 'block';
        const graphDiv = container.querySelector('#tiltingGraph');
        graphDiv.innerHTML = '';

        const nodes = [];
        const edges = [];

        for (let i = 0; i < data.length; i++) {
          const L = (data[i].L || []).map(Number);
          nodes.push({ id: i, label: `[${L.join(',')}]` });
        }

        for (let i = 0; i < data.length; i++) {
          const Li = data[i].L || [];
          for (let j = i + 1; j < data.length; j++) {
            const Lj = data[j].L || [];
            if (intersectionSize(Li, Lj) === 4) {
              edges.push({ from: i, to: j });
            }
          }
        }

        const visData = {
          nodes: new vis.DataSet(nodes),
          edges: new vis.DataSet(edges)
        };
        const options = {
          physics: { enabled: true },
          interaction: { dragNodes: true, dragView: true, zoomView: true, multiselect: false },
          edges: { smooth: false },
          nodes: { shape: 'dot', size: 12, font: { size: 12 } }
        };

        const network = new vis.Network(graphDiv, visData, options);

        function showDetails(idx) {
          const detail = container.querySelector('#tiltingDetails');
          if (!detail) return;
          const item = data[idx];
          if (!item) return;
          const L = (item.L || []).join(', ');
          const F = (item.F || []).join(', ');
          const T = (item.T || []).join(', ');
          const tags = (typeof tiltingTags === 'function') ? tiltingTags(item).join(', ') : '';
          detail.innerHTML = `L: [${L}]<br>F: [${F}]<br>T: [${T}]<br>${tags}`;
        }

        function selectSingle(idx) {
          network.unselectAll();
          network.selectNodes([idx], false);
          showDetails(idx);
        }

        network.on('click', function(params) {
          if (params.nodes && params.nodes.length > 0) {
            selectSingle(params.nodes[0]);
          }
        });

        selectSingle(0);
        window.__tiltingGraphNetwork = network;
        window.__tiltingGraphSelect = selectSingle;
      }

      window.renderTiltingList = function() {
        buildTiltingGraphOverride();
      };
      window.setActiveTilting = function(idx) {
        if (window.__tiltingGraphSelect) window.__tiltingGraphSelect(idx);
      };
      window.getActiveTiltingIndex = function() {
        const n = window.__tiltingGraphNetwork;
        if (!n) return -1;
        const sel = n.getSelectedNodes();
        return sel.length ? sel[0] : -1;
      };
      window.selectTiltingByIndex = function(idx) {
        if (window.__tiltingGraphSelect) window.__tiltingGraphSelect(idx);
      };

      const toggle = document.getElementById('tiltingToggle');
      if (toggle) {
        toggle.addEventListener('change', (e) => {
          if (e.target.checked) {
            buildTiltingGraphOverride();
          } else {
            const c = document.getElementById('tiltingGraphContainer');
            if (c) c.style.display = 'none';
          }
        });
      }
    })();
    </script>
    """

    if "</body>" in html:
        return html.replace("</body>", js + "\n</body>")
    return html + js






# ===== Step3.ipynb cell 13 =====
def _inject_tilting_window_like_quiver(html: str) -> str:
    print("DEBUG: Loading V20 Injection Function with Double-Toggle Sync...")
    import os
    import re
    
    # --- 1. Python Side: Analyze QuiverStructure & PDID ---
    quiver_structure = ""
    pdid_data_str = "[]"
    targets = []
    
    g_input_file = globals().get('input_file')
    g_input_name = globals().get('input_name')
    if g_input_file and os.path.exists(g_input_file): targets.append(g_input_file)
    if g_input_name and os.path.exists(g_input_name): targets.append(g_input_name)
    
    candidates = [f for f in os.listdir('.') if f.endswith('.txt') and 'quiver' in f.lower()]
    candidates.sort(key=lambda x: 0 if '_Q' in x else 1)
    targets.extend(candidates)
    
    for fname in targets:
        try:
            with open(fname, 'r', encoding='utf-8') as f: content = f.read()
            qs = re.search(r'QuiverStructure\s*:=\s*"([^"]+)"', content)
            pd = re.search(r'PDID\s*:=\s*(\[\s*[\s\S]*?\]);', content)
            if qs: quiver_structure = qs.group(1)
            if pd: pdid_data_str = re.sub(r'\s+', ' ', pd.group(1))
            if qs or pd: break
        except: continue

    # --- 2. JavaScript Template ---
    js_template = r"""
    <script>
    (function(){
      console.log("Tilting View Sync Logic Initialized");
      
      const QUIVER_STRUCT = "__QUIVER_STRUCTURE_PLACEHOLDER__";
      const PDID_DATA = __PDID_DATA_PLACEHOLDER__;
      
      // -- Helper: Draggable --
      function makeDraggable(el, handle) {
        let isDown=false, offX=0, offY=0;
        handle.addEventListener('mousedown', (e) => {
          isDown = true;
          const rect = el.getBoundingClientRect();
          offX = e.clientX - rect.left;
          offY = e.clientY - rect.top;
          e.preventDefault();
        });
        document.addEventListener('mousemove', (e) => {
          if (!isDown) return;
          el.style.left = (e.clientX - offX) + 'px';
          el.style.top = (e.clientY - offY) + 'px';
          el.style.right = 'auto';
          el.style.bottom = 'auto';
        });
        document.addEventListener('mouseup', () => isDown = false);
      }
      
      function intersect(a,b){
          const s = new Set(b);
          return a.filter(x => s.has(x)).length;
      }

      // --- 1. Tilting Mini Graph ---
      function buildTiltingMiniGraph() {
        if(document.getElementById('tiltingMiniContainer')) return;
        const data = (window.tiltingData || (typeof tiltingData!=='undefined'?tiltingData:[])) || [];
        if(!data.length) return;

        const c = document.createElement('div');
        c.id = 'tiltingMiniContainer';
        c.style.cssText = 'position:fixed;bottom:10px;left:10px;width:350px;height:350px;background:rgba(255,255,255,0.98);border:1px solid #aaa;box-shadow:0 0 10px rgba(0,0,0,0.2);z-index:9999;display:block;';
        c.innerHTML = `
          <div id="tmHead" style="background:#eee;padding:6px;cursor:move;font-weight:bold;font-size:12px;display:flex;justify-content:space-between;border-bottom:1px solid #ccc;">
            <span>Tilting (L-Graph)</span>
            <span onclick="this.parentNode.parentNode.style.display='none'" style="cursor:pointer;padding:0 5px;">×</span>
          </div>
          <div id="tmBody" style="width:100%;height:310px"></div>
        `;
        document.body.appendChild(c);
        makeDraggable(c, c.querySelector('#tmHead'));

        // Prepare Nodes with Selection Colors
        const nodes = data.map((item, i) => {
            const isSplit = !!item.split;
            
            // Define Standard and Highlight (Selected) Colors
            const baseColor = isSplit ? '#ffcccc' : '#ccf2ff';
            const baseBorder = isSplit ? '#ff0000' : '#00ccff';
            
            // Selected state
            const highColor = isSplit ? '#ff9999' : '#99d6ff';
            const highBorder = '#000000'; // Black border for selection
            
            return { 
              id: i, 
              label: String(i+1), 
              shape: 'circle', 
              margin: 10,
              borderWidth: 1,
              borderWidthSelected: 3, // Thicker border when selected
              color: { 
                  background: baseColor, 
                  border: baseBorder,
                  highlight: {
                      background: highColor,
                      border: highBorder
                  }
              }
            };
        });

        const edges = [];
        for(let i=0; i<data.length; i++) {
           for(let j=i+1; j<data.length; j++) {
               const Li = (data[i].L||[]).map(Number);
               const Lj = (data[j].L||[]).map(Number);
               if(intersect(Li, Lj) === 4) edges.push({from:i, to:j});
           }
        }

        const visData = { nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) };
        const opts = {
           interaction: { dragNodes: true, zoomView: true, selectConnectedEdges: false },
           physics: { enabled: false },
           edges: { 
               smooth: false, 
               width: 1,
               color: { color: 'black', highlight: 'black', hover: 'black', inherit: false },
               chosen: false // DISABLE Edge Selection Visuals
           }
        };

        const net = new vis.Network(c.querySelector('#tmBody'), visData, opts);
        
        // Grid Snap (40px)
        net.on("dragEnd", function (params) {
            if (params.nodes.length) {
                const updates = params.nodes.map(id => {
                    const pos = net.getPositions([id])[id];
                    return { id: id, x: Math.round(pos.x / 40) * 40, y: Math.round(pos.y / 40) * 40 };
                });
                visData.nodes.update(updates);
            }
        });

        // Click Graph -> Select List
        net.on('click', function(p){
            if(p.nodes.length){
                const idx = p.nodes[0];
                // Sync select from Graph click
                if(window.selectTiltingByIndex) {
                    window.__syncingFromGraph = true;
                    try { window.selectTiltingByIndex(idx); } catch(e){}
                    window.__syncingFromGraph = false;
                }
            }
        });
        
        window.__tiltingMiniNet = net;
    }
      
      // --- 2. Quiver Mini Graph ---
      function buildMiniQuiver() {
        if(document.getElementById('quiverMiniContainer')) return;
        const c = document.createElement('div');
        c.id = 'quiverMiniContainer';
        c.style.cssText = 'position:fixed;bottom:10px;right:10px;width:360px;height:280px;background:rgba(255,255,255,0.95);border:1px solid #ccc;border-radius:6px;z-index:9999;display:block;';
        c.innerHTML = '<div id="qmHead" style="background:#eee;padding:6px;cursor:move;font-weight:bold;font-size:12px;display:flex;justify-content:space-between;border-bottom:1px solid #ccc;border-radius:6px 6px 0 0;"><span>Quiver Q</span><span onclick="this.parentNode.parentNode.style.display=\'none\'" style="cursor:pointer;padding:0 5px;">×</span></div><div id="qmBody" style="width:100%;height:220px;background:white;"></div><div id="qmRel" style="padding:4px 6px;font-size:12px;font-family:monospace;white-space:pre-wrap;"></div>';
        document.body.appendChild(c);
        makeDraggable(c, c.querySelector('#qmHead'));

        // Show relations
        const relBox = c.querySelector('#qmRel');
        try { if(typeof quiverRel!=='undefined' && quiverRel) relBox.textContent = 'rel := ' + quiverRel; else relBox.textContent = 'rel := []'; } catch(e){ relBox.textContent = 'rel := []'; }
        
        let qNodes=[], qEdges=[];
        try { if(typeof quiverNodes!=='undefined') qNodes=quiverNodes; if(typeof quiverEdges!=='undefined') qEdges=quiverEdges; } catch(e){}
        if(qNodes.length === 0) return;
        
        // Layout nodes using QuiverStructure
        let s = QUIVER_STRUCT;
        if(s.startsWith('[')) s = s.slice(1);
        if(s.endsWith(']')) s = s.slice(0,-1);
        const rows = s.split(';');
        const nodeMap = new Map();
        qNodes.forEach(n => nodeMap.set(n.id, n));
        rows.forEach((r, y) => {
            let x = 0;
            for(let i=0; i<r.length; i++) {
                if(/\d/.test(r[i])) { 
                    const nid = parseInt(r[i]); 
                    const n = nodeMap.get(nid); 
                    if(n){ n.x=x*100; n.y=y*100; }
                    x++; 
                } else { x++; }
            }
        });
        
        const data = {
            nodes: new vis.DataSet(qNodes.map(n => ({
                id: n.id,
                label: String(n.label),
                x: n.x,
                y: n.y,
                shape: 'ellipse',
                font: { face: 'monospace', size: 14, bold: true, color: 'black', vadjust: 0, align: 'center' },
                color: { border: 'gray', background: 'white' },
                borderWidth: 2
            }))),
            edges: new vis.DataSet(qEdges.map((e,i) => ({
                id: 'q'+i,
                from: e[0],
                to: e[1],
                label: e[2] || '',
                arrows: 'to',
                font: { align: 'horizontal', size: 12, face: 'monospace', color: '#333', vadjust: 0 },
                smooth: false
            })))
        };
        const qmNet = new vis.Network(c.querySelector('#qmBody'), data, {
            physics: false,
            interaction: { dragNodes: true, zoomView: true, dragView: true },
            edges: { arrows: { to: true }, font: { align: 'horizontal' }, smooth: false }
        });
        if (typeof assignMultiEdgeCurves === 'function') setTimeout(() => assignMultiEdgeCurves(qmNet), 50);
      }

      // --- Togglers Hooks ---
      function hookTogglers() {
          const qToggle = document.getElementById('quiverToggle');
          if(qToggle) {
              qToggle.addEventListener('change', e => {
                  const c = document.getElementById('quiverMiniContainer');
                  if(e.target.checked) { if(!c) buildMiniQuiver(); else c.style.display = 'block'; }
                  else if(c) { c.style.display = 'none'; }
              });
              if(qToggle.checked) buildMiniQuiver();
          }

          // (1) Hook: Tilting toggle controls both List and Mini Graph
          const tToggle = document.getElementById('tiltingToggle');
          if(tToggle) {
              tToggle.addEventListener('change', e => {
                  const c = document.getElementById('tiltingMiniContainer');
                  const l = document.getElementById('tiltingList');
                  
                  if(e.target.checked) {
                      // SHOW Both
                      if(!c) buildTiltingMiniGraph();
                      else c.style.display = 'block';
                      if(l) l.style.display = 'block';
                      rebindListClicks();
                  } else {
                      // HIDE Both
                      if(c) c.style.display = 'none';
                      if(l) l.style.display = 'none';
                  }
              });
              
              // Initial State Check
              const list = document.getElementById('tiltingList');
              if(tToggle.checked) {
                 buildTiltingMiniGraph();
                 if(list) list.style.display = 'block';
                 rebindListClicks();
              } else {
                 if(list) list.style.display = 'none';
                 const c = document.getElementById('tiltingMiniContainer');
                 if(c) c.style.display = 'none';
              }
          }
      }

      // --- Interaction Sync ---
      
      // Update Selection Styler
      function updateTiltingSelectionStyles(idx) {
          const data = window.tiltingData || [];
          const listBtn = document.querySelectorAll('#tiltingList button');
          
          listBtn.forEach((btn, i) => {
              if(!data[i]) return;
              const item = data[i];
              const isSplit = (typeof tiltingIsSplit === 'function') ? tiltingIsSplit(item) : !!item.split;
              const isSeparating = (typeof tiltingIsSeparating === 'function') ? tiltingIsSeparating(item) : !!item.split;
              const isSelected = (i == idx);
              
              const finalBg = isSplit ? '#ffcccc' : (isSeparating ? '#e9d5ff' : '#ccf2ff');
              const finalBorder = isSplit ? '#ff0000' : (isSeparating ? '#7e22ce' : '#00ccff');

              btn.style.setProperty('background-color', finalBg, 'important');
              btn.style.setProperty('border', '1px solid ' + finalBorder, 'important');
              btn.style.setProperty('color', 'black', 'important');
              
              if(isSelected) {
                  btn.style.setProperty('border', '3px solid black', 'important');
                  btn.style.setProperty('font-weight', 'bold', 'important');
              } else {
                  btn.style.setProperty('font-weight', 'normal', 'important');
              }
          });
      }

      // DIRECT CLICK BINDING
      function rebindListClicks() {
          const list = document.getElementById('tiltingList');
          if(!list) return;
          if(list.dataset.hasDirectSync) return;
          
          list.addEventListener('click', function(e) {
              const btn = e.target.closest('button');
              if(!btn) return;
              
              const allBtns = Array.from(list.querySelectorAll('button'));
              const idx = allBtns.indexOf(btn);
              
              if(idx !== -1) {
                  // FORCE Graph Selection
                  if(window.__tiltingMiniNet) {
                      window.__tiltingMiniNet.selectNodes([idx]);
                  }
                  updateTiltingSelectionStyles(idx);
              }
          }, true);
          
          list.dataset.hasDirectSync = "true";
      }

      // Proxy selectTiltingByIndex as backup
      if(!window.__selectProxyInstalledV6) {
          const origSelectIdx = window.selectTiltingByIndex;
          window.selectTiltingByIndex = function(idx) {
              if(origSelectIdx) origSelectIdx(idx);
              
              // Sync to Graph
              if(!window.__syncingFromGraph && window.__tiltingMiniNet) {
                  // Unselect edges first to be clean?
                  // selectNodes automatically deselects others unless configured otherwise
                  window.__tiltingMiniNet.selectNodes([parseInt(idx)]);
              }
              
              updateTiltingSelectionStyles(idx);
              
              const listBtn = document.querySelectorAll('#tiltingList button');
              if(listBtn[idx]) listBtn[idx].scrollIntoView({block:'center', behavior:'smooth'});
          };
          window.__selectProxyInstalledV6 = true;
      }

      // Hook into renderTiltingList
      if(!window.__renderProxyInstalledV6) {
          const origRenderList = window.renderTiltingList;
          window.renderTiltingList = function() {
              if(origRenderList) origRenderList();
              setTimeout(rebindListClicks, 100);
              
              let currentIdx = -1;
              if(typeof getActiveTiltingIndex === 'function') currentIdx = getActiveTiltingIndex();
              if(currentIdx === undefined) currentIdx = -1;
              
              setTimeout(() => {
                  updateTiltingSelectionStyles(currentIdx);
                  if(currentIdx !== -1 && window.__tiltingMiniNet) {
                      window.__tiltingMiniNet.selectNodes([parseInt(currentIdx)]);
                  }
              }, 150);
          };
          window.__renderProxyInstalledV6 = true;
      }

      // --- Keyboard ---
      if(!window.__keyListenerInstalledV6) {
          document.addEventListener('keydown', e => {
              if(e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                  const delta = (e.key === 'ArrowRight') ? 0.1 : -0.1;
                  if(window.__tiltingMiniNet && window.updateEdgeCurvature && window.__tiltingMiniNet.getSelectedEdges().length > 0) {
                      window.updateEdgeCurvature(window.__tiltingMiniNet, delta);
                  }
              }
              if(['ArrowUp','ArrowDown'].includes(e.key)) {
                 const list = document.getElementById('tiltingList');
                 if(list && list.style.display !== 'none' && e.target.tagName !== 'INPUT') e.preventDefault();
              }
          });
          window.__keyListenerInstalledV6 = true;
      }

      hookTogglers();
      setTimeout(() => {
          if(window.renderTiltingList) window.renderTiltingList();
          rebindListClicks();
      }, 500);

    })();
    </script>
    """

    js = js_template.replace("__QUIVER_STRUCTURE_PLACEHOLDER__", quiver_structure) \
                     .replace("__PDID_DATA_PLACEHOLDER__", pdid_data_str)

    if "</body>" in html:
        return html.replace("</body>", js + "\n</body>")
    return html + js

# ===== Step3.ipynb cell 14 =====



# ===== Step3.ipynb cell 15 =====
def _greekize_text(value: str) -> str:
    if not value:
        return value
    mapping = {
        # lowercase
        "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε",
        "zeta": "ζ", "eta": "η", "theta": "θ", "iota": "ι", "kappa": "κ",
        "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ", "omicron": "ο",
        "pi": "π", "rho": "ρ", "sigma": "σ", "tau": "τ", "upsilon": "υ",
        "phi": "φ", "chi": "χ", "psi": "ψ", "omega": "ω",
        # capitalized
        "Alpha": "Α", "Beta": "Β", "Gamma": "Γ", "Delta": "Δ", "Epsilon": "Ε",
        "Zeta": "Ζ", "Eta": "Η", "Theta": "Θ", "Iota": "Ι", "Kappa": "Κ",
        "Lambda": "Λ", "Mu": "Μ", "Nu": "Ν", "Xi": "Ξ", "Omicron": "Ο",
        "Pi": "Π", "Rho": "Ρ", "Sigma": "Σ", "Tau": "Τ", "Upsilon": "Υ",
        "Phi": "Φ", "Chi": "Χ", "Psi": "Ψ", "Omega": "Ω",
    }
    for key, val in mapping.items():
        value = re.sub(rf"\b{key}\b", val, value)
    return value




# ===== Step3.ipynb cell 16 =====
def _inject_relation_formatter(html: str) -> str:
    marker = "/* RELATION_FORMATTER_INJECT */"
    if marker in html:
        return html
    helper_js = r"""
      /* RELATION_FORMATTER_INJECT */
      function formatRelation(rel) {
        const map = {
          alpha: 'α', beta: 'β', gamma: 'γ', delta: 'δ', epsilon: 'ε',
          zeta: 'ζ', eta: 'η', theta: 'θ', iota: 'ι', kappa: 'κ',
          lambda: 'λ', mu: 'μ', nu: 'ν', xi: 'ξ', omicron: 'ο',
          pi: 'π', rho: 'ρ', sigma: 'σ', tau: 'τ', upsilon: 'υ',
          phi: 'φ', chi: 'χ', psi: 'ψ', omega: 'ω',
          Alpha: 'Α', Beta: 'Β', Gamma: 'Γ', Delta: 'Δ', Epsilon: 'Ε',
          Zeta: 'Ζ', Eta: 'Η', Theta: 'Θ', Iota: 'Ι', Kappa: 'Κ',
          Lambda: 'Λ', Mu: 'Μ', Nu: 'Ν', Xi: 'Ξ', Omicron: 'Ο',
          Pi: 'Π', Rho: 'Ρ', Sigma: 'Σ', Tau: 'Τ', Upsilon: 'Υ',
          Phi: 'Φ', Chi: 'Χ', Psi: 'Ψ', Omega: 'Ω'
        };
        const names = ['alpha','beta','gamma','delta','epsilon','zeta','eta','theta','iota','kappa','lambda','mu','nu','xi','omicron','pi','rho','sigma','tau','upsilon','phi','chi','psi','omega'];
        const namesSorted = names.slice().sort((a, b) => b.length - a.length);
        function parseConcat(word) {
          const lower = word.toLowerCase();
          let i = 0;
          const parts = [];
          while (i < lower.length) {
            let matched = null;
            for (const name of namesSorted) {
              if (lower.startsWith(name, i)) {
                matched = name;
                break;
              }
            }
            if (!matched) return null;
            parts.push(matched);
            i += matched.length;
          }
          return parts;
        }
        function toGreekWord(word) {
          return word.replace(/[A-Za-z]+/g, (m) => map[m] || map[m.toLowerCase()] || m);
        }
        function formatToken(token) {
          const raw = (token || '').trim();
          if (!raw) return '';
          const starParts = raw.split('*').map(s => s.trim()).filter(Boolean);
          const mapped = starParts.map(part => {
            const parsed = parseConcat(part);
            if (parsed) {
              return parsed.map(p => map[p] || p).join('·');
            }
            return toGreekWord(part);
          });
          return mapped.join('·');
        }
        if (!rel) return 'relation = ()';
        let raw = String(rel).trim();
        if (raw.startsWith('[') && raw.endsWith(']')) raw = raw.slice(1, -1);
        if (!raw) return 'relation = ()';
        const items = raw.split(',').map(s => s.trim()).filter(Boolean).map(formatToken);
        return `relation = (${items.join(', ')})`;
      }
    """
    needle = "      function ensureMiniQuiver() {"
    if needle in html:
        html = html.replace(needle, helper_js + "\n" + needle, 1)
    old = "        relBox.textContent = quiverRel ? `rel := ${quiverRel}` : 'rel := []';"
    new = "        relBox.textContent = formatRelation(quiverRel);"
    if old in html:
        html = html.replace(old, new, 1)
    return html



