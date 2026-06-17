
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
    # 读取文件内容
    try:
        with open(quiver_file, 'r', encoding='utf-8') as f:
            content = f.read()
            content = re.sub(r"\\\s*\n\s*", "", content)
    except FileNotFoundError:
        return None, None, None, None, None, None, None, None, None, None, None, None, None, None
    # Keep a global reference for translation-quiver extraction
    globals()["input_file"] = quiver_file
    # 使用正则表达式提取投射/内射模
    proj_match = re.search(r"Projective modules found \(Node IDs\): \[(.*?)\]", content)
    inj_match = re.search(r"Injective modules found \(Node IDs\):  \[(.*?)\]", content)
    tors_match = re.search(r"Torsionless modules found \(Node IDs\): \[(.*?)\]", content)
    refl_match = re.search(r"Reflexive modules found \(Node IDs\):  \[(.*?)\]", content)
    gp_match = re.search(r"Gorenstein projective modules found \(Node IDs\): \[(.*?)\]", content)
    gi_match = re.search(r"Gorenstein injective modules found \(Node IDs\):  \[(.*?)\]", content)
    # 提取投射模/内射模 ID.
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
        l_match = re.search(r"^L := \[(.*?)\]", block, re.M)
        f_match = re.search(r"^F := \[(.*?)\]", block, re.M)
        t_match = re.search(r"^T := \[(.*?)\]", block, re.M)
        
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
    for m in re.finditer(r"^T :=\s*(0|\[[^\]]*\])\s*\|\s*F :=\s*(0|\[[^\]]*\])", torsion_section, flags=re.M | re.S):
        torsion_pair_data.append({
            "T": parse_class_expr(m.group(1)),
            "F": parse_class_expr(m.group(2)),
        })

    cotorsion_pair_data = []
    cotorsion_section = ""
    cotorsion_match = re.search(r"# --- CotorsionPairTable --- #[\s\S]*?(?=PDID :=|$)", content)
    if cotorsion_match:
        cotorsion_section = cotorsion_match.group(0)
    for m in re.finditer(r"^L :=\s*(0|\[[^\]]*\])\s*\|\s*R :=\s*(0|\[[^\]]*\])\s*\|\s*Hereditary\s*:\s*=\s*(true|false)", cotorsion_section, flags=re.M | re.S | re.I):
        cotorsion_pair_data.append({
            "L": parse_class_expr(m.group(1)),
            "R": parse_class_expr(m.group(2)),
            "hereditary": m.group(3).lower() == "true",
        })

    support_tau_data = []
    support_tau_match = re.search(r"# --- SupportTauTiltingTable --- #[\s\S]*?(?=# --- AlmostSupportTauTiltingTable --- #|PDID :=|$)", content)
    support_tau_section = support_tau_match.group(0) if support_tau_match else ""
    for m in re.finditer(r"^P :=\s*(0|\[[^\]]*\])\s*\|\s*M :=\s*(0|\[[^\]]*\])", support_tau_section, flags=re.M | re.S):
        support_tau_data.append({"P": parse_class_expr(m.group(1)), "M": parse_class_expr(m.group(2))})

    almost_support_tau_data = []
    almost_support_tau_match = re.search(r"# --- AlmostSupportTauTiltingTable --- #[\s\S]*?(?=PDID :=|$)", content)
    almost_support_tau_section = almost_support_tau_match.group(0) if almost_support_tau_match else ""
    for m in re.finditer(r"^P :=\s*(0|\[[^\]]*\])\s*\|\s*M :=\s*(0|\[[^\]]*\])", almost_support_tau_section, flags=re.M | re.S):
        almost_support_tau_data.append({"P": parse_class_expr(m.group(1)), "M": parse_class_expr(m.group(2))})

    globals()["torsion_pair_data"] = torsion_pair_data
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
        print(f"❌ 未找到 quiver 文件或其中不含 dot 图：{quiver_filepath}")
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
        print(f"❌ 未找到 quiver 文件或其中不含 dot 图：{quiver_filepath}")
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
                print(f"❌ 节点 {node_id} 的 label 不是合法 JSON：{attrs.get('label')}\n原因：{e}")
                return
            
    # 使用默认引擎绘制 + 增加格点吸附/直线边(通过 JS 设置)
    net = Network(height='750px', width='100%', directed=True, notebook=False)
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
                     font={'color': 'black', 'face': 'monospace', 'size': 14, 'bold': True, 'vadjust': 0, 'align': 'center'}, title=f"Node {node_id}<br>{label_display}",
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
    
    golden_edges_js_string = json.dumps(golden_edges)
    tors_ids_js = json.dumps(sorted(list(tors_ids)))
    refl_ids_js = json.dumps(sorted(list(refl_ids)))
    gp_ids_js = json.dumps(sorted(list(globals().get("gorenstein_projective_ids", set()))))
    gi_ids_js = json.dumps(sorted(list(globals().get("gorenstein_injective_ids", set()))))
    zero_ids_js = json.dumps(sorted(list(zero_node_ids)))
    syz_edges_js = json.dumps(syz_edges)
    cosyz_edges_js = json.dumps(cosyz_edges)
    q_nodes_js = json.dumps(q_nodes)
    q_edges_js = json.dumps(q_edges)
    q_rel_js = json.dumps(rel_content or "")
    hom_edges_js = json.dumps(hom_edges)
    ext_edges_js = json.dumps(ext_edges)
    tilting_js = json.dumps(tilting_data or [])
    torsion_pairs_js = json.dumps(globals().get("torsion_pair_data", []))
    cotorsion_pairs_js = json.dumps(globals().get("cotorsion_pair_data", []))
    support_tau_js = json.dumps(globals().get("support_tau_tilting_data", []))
    almost_support_tau_js = json.dumps(globals().get("almost_support_tau_tilting_data", []))
    pdid_js = json.dumps(pdid_map or {})
    top_soc_js = json.dumps(globals().get("top_soc_map", {}))
    q_structure_js = json.dumps(quiver_structure or "")

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
      const quiverNodes = {{Q_NODES}};
      const quiverEdges = {{Q_EDGES}};
      const quiverRel = {{Q_REL}};
      const homEdges = {{HOM_EDGES}};
      const extEdges = {{EXT_EDGES}};
      const tiltingData = {{TILTING_DATA}};
      const torsionPairData = {{TORSION_PAIR_DATA}};
      const cotorsionPairData = {{COTORSION_PAIR_DATA}};
      const supportTauTiltingData = {{SUPPORT_TAU_TILTING_DATA}};
      const almostSupportTauTiltingData = {{ALMOST_SUPPORT_TAU_TILTING_DATA}};
      const pdidMap = {{PDID_MAP}};
      const topSocMap = {{TOP_SOC_MAP}};
      const quiverStructure = {{Q_STRUCTURE}};
      const goldenEdgeSet = new Set(goldenEdges.map(e => `${e[0]}->${e[1]}`));
      var options = {
        "edges": {
          // (1) 选中只加粗，不改变颜色；改为绿色细边框高亮
          "selectionWidth": 2,
          "color": { "color": "#000000", "highlight": "#00aa00", "hover": "#00aa00", "inherit": true },
          // (2) 所有边为直线（可被键盘调弧度）
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

      (function ensureMathJax() {
        if (window.MathJax || document.getElementById('mathjax-script')) return;
        window.MathJax = { tex: { inlineMath: [['$', '$']] }, svg: { fontCache: 'global' } };
        const script = document.createElement('script');
        script.id = 'mathjax-script';
        script.async = true;
        script.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js';
        document.head.appendChild(script);
      })();

      function typesetMath(element) {
        if (window.MathJax && window.MathJax.typesetPromise) {
          window.MathJax.typesetPromise(element ? [element] : undefined).catch(() => {});
          return;
        }
        if (element) {
          element.__mathjaxRetries = (element.__mathjaxRetries || 0) + 1;
          if (element.__mathjaxRetries <= 20) {
            setTimeout(() => typesetMath(element), 250);
          }
        }
      }

      function renderInlineMath(element, tex) {
        if (!element) return;
        element.textContent = '$' + tex + '$';
        element.classList.add('ar-math-label');
        typesetMath(element);
      }

      function parseEdgeColor(choice) {
        const c = (choice || 'black').toLowerCase().replace(/\s+/g, '');
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
      const customTexLabels = new Map();
      let nodeLabelMode = 'dimension';
      const nodeLabelButtons = new Map();
      const edgeCurveMemory = new Map();
      let hoverTip = null;
      let hoverNodeId = null;
      const baseNodeStyles = new Map();
      let tiltingHighlighted = new Set();
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
            <button id="torsBtn" style="padding:4px 8px;">Torsionless</button>
            <button id="reflBtn" style="padding:4px 8px;">Reflexive</button>
            <button id="gpBtn" style="padding:4px 8px;">GProj</button>
            <button id="giBtn" style="padding:4px 8px;">GInj</button>
          </div>
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:4px;">
            <label style="font-size:12px; background: rgba(255,255,255,0.8); padding:4px 8px; border-radius:4px;">
              <input id="syzToggle" type="checkbox" /> Syzygy
            </label>
            <label style="font-size:12px; background: rgba(255,255,255,0.8); padding:4px 8px; border-radius:4px;">
              <input id="cosyzToggle" type="checkbox" /> Cosyzygy
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
          <div id="tiltingList" style="display:none; background: rgba(255,255,255,0.9); padding:6px; border-radius:6px; max-height:240px; overflow:auto; font-size:12px;"></div>
          <div id="torsionPairList" style="display:none; background: rgba(255,255,255,0.9); padding:6px; border-radius:6px; max-height:260px; overflow:auto; font-size:12px;"></div>
          <div id="cotorsionPairList" style="display:none; background: rgba(255,255,255,0.9); padding:6px; border-radius:6px; max-height:260px; overflow:auto; font-size:12px;"></div>
          <div id="supportTauList" style="display:none; background: rgba(255,255,255,0.9); padding:6px; border-radius:6px; max-height:260px; overflow:auto; font-size:12px;"></div>
          <div id="almostSupportTauList" style="display:none; background: rgba(255,255,255,0.9); padding:6px; border-radius:6px; max-height:260px; overflow:auto; font-size:12px;"></div>
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
            alert('不存在');
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
          const selected = Array.from(activeModuleIds());
          if (selected.length === 1) network.focus(selected[0], { scale: 1.2, animation: true });
          else if (selected.length > 1) network.fit({ nodes: selected, animation: true });
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
          toggleEdges((edge) => isBlackEdge(edge), checked);
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
            renderPairList('torsionPairList', torsionPairData, 'T', 'F', 'Torsion pairs', null, { kind: 'torsion' });
          } else {
            clearPairListHighlight();
          }
        });
        document.getElementById('cotorsionPairToggle').addEventListener('change', (e) => {
          const el = document.getElementById('cotorsionPairList');
          if (!el) return;
          el.style.display = e.target.checked ? 'block' : 'none';
          if (e.target.checked) {
            renderPairList('cotorsionPairList', cotorsionPairData, 'L', 'R', 'Cotorsion pairs', item => `<td style="border:1px solid #ddd; padding:3px;">${item.hereditary ? 'hereditary' : 'non-hereditary'}</td>`);
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

        function showListInDrawer(toggleId, listId, title) {
          ensureDrawer();
          setCheckbox(toggleId, true);
          const listEl = document.getElementById(listId);
          if (!listEl) return;
          while (drawerBody.firstChild) {
            container.appendChild(drawerBody.firstChild);
          }
          drawerToggleId = toggleId;
          drawerListId = listId;
          drawerTitle.textContent = title;
          drawerBody.appendChild(listEl);
          listEl.style.display = 'block';
          drawer.style.display = 'block';
          typesetMath(drawerBody);
        }

        function clearAllNodeHighlights() {
          splitPairHighlights = new Map();
          pairHighlighted = new Set();
          tiltingHighlighted = new Set();
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
            .ar-math-label { font-family: serif; }
            #arListDrawer {
              position: fixed;
              top: 42px;
              right: 10px;
              width: 390px;
              min-width: 260px;
              max-width: 90vw;
              max-height: calc(100vh - 54px);
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
            }
            #arListDrawer .ar-panel-close { border: 0; background: transparent; font-size: 18px; cursor: pointer; }
            #arListDrawerResizeHandle { position:absolute; left:0; top:0; bottom:0; width:7px; cursor:ew-resize; background:transparent; }
            #arListDrawerResizeHandle:hover { background:rgba(37,99,235,0.18); }
            #arListDrawerBody { padding: 8px; }
            #tiltingList, #torsionPairList, #cotorsionPairList, #supportTauList, #almostSupportTauList { min-width: 240px; max-width: 100%; }
            .ar-record-row { display:block; width:100%; text-align:left; margin:2px 0; padding:4px 6px; border:1px solid #dbeafe; border-radius:4px; background:#fff; font-family:monospace; font-size:11px; cursor:pointer; }
            .ar-record-row:hover { background:#eff6ff; }
          `;
          document.head.appendChild(style);
        }

        function ensureDrawer() {
          if (drawer) return;
          drawer = document.createElement('div');
          drawer.id = 'arListDrawer';
          drawer.innerHTML = '<div id="arListDrawerResizeHandle"></div><div class="ar-panel-head"><strong id="arDrawerTitle"></strong><button id="arDrawerClose" class="ar-panel-close">×</button></div><div id="arListDrawerBody"></div>';
          document.body.appendChild(drawer);
          drawerTitle = drawer.querySelector('#arDrawerTitle');
          drawerBody = drawer.querySelector('#arListDrawerBody');
          drawer.querySelector('#arDrawerClose').addEventListener('click', () => {
            closeListDrawer(true);
          });
          const resizeHandle = drawer.querySelector('#arListDrawerResizeHandle');
          let resizingDrawer = false;
          resizeHandle.addEventListener('mousedown', (event) => {
            resizingDrawer = true;
            event.preventDefault();
            event.stopPropagation();
          });
          document.addEventListener('mousemove', (event) => {
            if (!resizingDrawer) return;
            const right = window.innerWidth - drawer.getBoundingClientRect().right;
            const nextWidth = Math.max(260, Math.min(window.innerWidth * 0.9, window.innerWidth - event.clientX - right));
            drawer.style.width = nextWidth + 'px';
          });
          document.addEventListener('mouseup', () => { resizingDrawer = false; });
        }

        let calculatorPanel = null;
        function calcAllIds() {
          return network.body.data.nodes.getIds().map(Number).filter(Number.isFinite).sort((a, b) => a - b);
        }
        function calcParseSet(text) {
          const all = calcAllIds();
          const raw = String(text || '').trim();
          if (!raw || raw.toLowerCase() === 'all' || raw === '*') return all;
          return Array.from(new Set((raw.match(/-?\d+/g) || []).map(Number).filter(x => all.includes(x)))).sort((a, b) => a - b);
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
        function calcRightPerp(edges, input) {
          const all = calcAllIds();
          return all.filter(x => input.every(a => !calcNonzero(edges, a, x)));
        }
        function calcLeftPerp(edges, input) {
          const all = calcAllIds();
          return all.filter(x => input.every(a => !calcNonzero(edges, x, a)));
        }
        function calcRunOperation() {
          const op = document.getElementById('calcOp').value;
          const A = calcParseSet(document.getElementById('calcA').value);
          const B = calcParseSet(document.getElementById('calcB').value);
          const extI = Number(document.getElementById('calcI').value || '1');
          let output = '';
          if (op === 'Hom') output = calcPairs(homEdges, A, B).join(', ') || '0';
          else if (op === 'Ext') output = extI === 1 ? (calcPairs(extEdges, A, B).join(', ') || '0') : 'Only Ext^1 data is available in this HTML.';
          else if (op === 'Syzygy') output = calcFormatSet(calcImage(syzygyEdges, A));
          else if (op === 'Cosyzygy') output = calcFormatSet(calcImage(cosyzygyEdges, A));
          else if (op === 'Homperp') output = calcFormatSet(calcRightPerp(homEdges, A));
          else if (op === 'perpHom') output = calcFormatSet(calcLeftPerp(homEdges, A));
          else if (op === 'Extperp') output = calcFormatSet(calcRightPerp(extEdges, A));
          else if (op === 'perpExt') output = calcFormatSet(calcLeftPerp(extEdges, A));
          else if (op === 'Gen') output = calcFormatSet(calcRightPerp(homEdges, []).filter(x => A.some(a => calcNonzero(homEdges, a, x))));
          else if (op === 'Cog') output = calcFormatSet(calcRightPerp(homEdges, []).filter(x => A.some(a => calcNonzero(homEdges, x, a))));
          else if (op === 'Extension') output = (calcPairs(extEdges, A, B).join(', ') || 'No nonzero Ext^1 pairs in current data.');
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
          const name = (window.location.pathname.split('/').pop() || 'untitled.html').replace(/\.(html|log|txt)$/i, '');
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
          const nl = String.fromCharCode(10);
          return [
            '# GAP/QPA script generated by AR Quiver',
            '# Source: ' + source,
            '#',
            '# Usage:',
            '#   Copy this file into GAP, or save it as ' + source + '_run_with_gap.g and run:',
            '#     gap -q ' + source + '_run_with_gap.g',
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
            'TryAllIndecomposableModules := function(A)',
            '  if IsBoundGlobal("IndecModules") then return IndecModules(A); fi;',
            '  if IsBoundGlobal("IndecomposableModules") then return IndecomposableModules(A); fi;',
            '  if IsBoundGlobal("IndecModulesOfAlgebra") then return IndecModulesOfAlgebra(A); fi;',
            '  if IsBoundGlobal("IndecomposableModulesOfAlgebra") then return IndecomposableModulesOfAlgebra(A); fi;',
            '  return fail;',
            'end;;',
            '',
            'M := TryAllIndecomposableModules(A);;',
            '',
            'Print("\\nGenerated objects ready.\\n");',
            'Print("Q: original quiver\\n");',
            'Print("kQ: path algebra over Rationals\\n");',
            'Print("A: bound quiver algebra kQ / rel\\n");',
            'Print("Projectives P[1]..P[", Length(P), "]\\n");',
            'Print("Injectives I[1]..I[", Length(I), "]\\n");',
            'Print("Simples S[1]..S[", Length(S), "]\\n");',
            'if M = fail then',
            '  Print("M: all indecomposable modules could not be enumerated by the available QPA commands.\\n");',
            'else',
            '  Print("Indecomposables M[1]..M[", Length(M), "]\\n");',
            'fi;',
            ''
          ].join(nl);
        }
        function calcRunWithGap() {
          const out = document.getElementById('calcOutput');
          const source = calcSourceStem();
          const script = calcGapScript();
          const filename = source + '_run_with_gap.g';
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
          out.appendChild(document.createTextNode('Generated GAP/QPA code for Q, kQ, A, M[i], P[i], I[i], S[i].'));
          out.appendChild(document.createElement('br'));
          out.appendChild(buttons);
          out.appendChild(textarea);
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
                <label>Function <select id="calcOp" style="width:100%;"><option>Hom</option><option>Ext</option><option>Syzygy</option><option>Cosyzygy</option><option>Homperp</option><option>perpHom</option><option value="Extperp">Extperp / Extprep</option><option value="perpExt">perpExt / prepExt</option><option>Gen</option><option>Cog</option><option>Extension</option></select></label>
                <label>A labels <input id="calcA" style="width:100%; box-sizing:border-box;" placeholder="e.g. 1 2 5 or all" /></label>
                <label>B labels <input id="calcB" style="width:100%; box-sizing:border-box;" placeholder="for Hom/Ext/Extension" /></label>
                <label>i for Ext^i <input id="calcI" style="width:100%; box-sizing:border-box;" value="1" /></label>
                <div style="display:flex; gap:8px;">
                  <button id="calcRun" style="flex:1; padding:6px 10px; border:1px solid #2563eb; background:#dbeafe; color:#1d4ed8; border-radius:6px; cursor:pointer; font-weight:650;">Run</button>
                  <button id="calcRunGap" style="flex:1; padding:6px 10px; border:1px solid #16a34a; background:#dcfce7; color:#166534; border-radius:6px; cursor:pointer; font-weight:650;">Run with GAP</button>
                </div>
                <div style="color:#475569; font-size:12px;">Inputs/outputs use node label numbers. Run with GAP shows copyable GAP/QPA code and can download a .g file.</div>
                <pre id="calcOutput" style="min-height:48px; max-height:180px; overflow:auto; white-space:pre-wrap; margin:0; padding:8px; background:#f8fafc; border:1px solid #e5e7eb; border-radius:6px;"></pre>
              </div>`;
            document.body.appendChild(calculatorPanel);
            calculatorPanel.querySelector('#calcClose').addEventListener('click', () => { calculatorPanel.style.display = 'none'; });
            calculatorPanel.querySelector('#calcRun').addEventListener('click', calcRunOperation);
            calculatorPanel.querySelector('#calcRunGap').addEventListener('click', calcRunWithGap);
          }
          calculatorPanel.style.display = 'block';
        }

        let folderPanel = null;
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
              <button data-toggle="homToggle">Hom dimension quiver</button>
              <button data-toggle="extToggle">Ext dimension quiver</button>
              <button data-toggle="quiverToggle">Original quiver Q</button>
            </div></details>
            <details><summary>Modules</summary><div class="ar-folder-body">
              <button data-click="torsBtn">Torsionless</button>
              <button data-click="reflBtn">Reflexive</button>
              <button data-click="gpBtn">Gorenstein projective</button>
              <button data-click="giBtn">Gorenstein injective</button>
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
            <details><summary>Tools</summary><div class="ar-folder-body">
              <button data-action="fit">Fit graph</button>
              <button data-action="undo">Undo Ctrl+Z</button>
              <button data-action="redo">Redo Ctrl+Y</button>
              <button data-action="calculator">Calculator</button>
              <button data-action="export-tex">Export AR quiver to TeX</button>
              <button data-action="legend">Color legend</button>
            </div></details>
          `;
          document.body.appendChild(folderPanel);
          folderPanel.addEventListener('click', handleMenuAction);
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
          const amount = Math.max(0.25, Math.min(5, roundness * 3)).toFixed(2).replace(/\.00$/, '').replace(/0$/, '');
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

        function showTexExport(tex) {
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
            modal.innerHTML = '<div style="display:flex;align-items:center;justify-content:space-between;padding:9px 12px;border-bottom:1px solid #e5e7eb;background:#f8fafc;border-radius:10px 10px 0 0;font-family:system-ui,-apple-system,Segoe UI,sans-serif;font-size:13px;"><strong>Export AR quiver to TeX / xymatrix</strong><button id="arTexClose" style="border:0;background:transparent;font-size:20px;cursor:pointer;">×</button></div><textarea id="arTexOutput" style="box-sizing:border-box;width:100%;height:400px;border:0;border-bottom:1px solid #e5e7eb;padding:10px;font-family:monospace;font-size:12px;white-space:pre;"></textarea><div style="display:flex;gap:8px;justify-content:flex-end;padding:9px 12px;"><button id="arTexCopy">Copy</button><button id="arTexDownload">Download .tex</button></div>';
            document.body.appendChild(modal);
            modal.querySelector('#arTexClose').addEventListener('click', () => { modal.style.display = 'none'; });
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
              a.download = 'ar-quiver-xymatrix.tex';
              document.body.appendChild(a);
              a.click();
              document.body.removeChild(a);
              URL.revokeObjectURL(url);
            });
          }
          modal.querySelector('#arTexOutput').value = tex;
          modal.style.display = 'block';
        }

        function handleMenuAction(event) {
          const btn = event.target.closest('button');
          if (!btn) return;
          const toggleId = btn.getAttribute('data-toggle');
          const clickId = btn.getAttribute('data-click');
          const listSpec = btn.getAttribute('data-list');
          const action = btn.getAttribute('data-action');
          if (toggleId) {
            toggleCheckbox(toggleId);
            const toggleEl = document.getElementById(toggleId);
            btn.classList.toggle('ar-control-active', !!(toggleEl && toggleEl.checked));
          }
          if (!toggleId && !clickId && !listSpec && action) {
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
            showListInDrawer(parts[0], parts[1], parts[2]);
            btn.classList.add('ar-control-active');
          }
          if (action === 'close-panel') folderPanel.style.display = 'none';
          if (action === 'fit') network.fit({ animation: true });
          if (action === 'toggle-ui') toggleMenuUi();
          if (action === 'clear-colors') clearListColoring();
          if (action === 'undo' && typeof undo === 'function') undo();
          if (action === 'redo' && typeof redo === 'function') redo();
          if (action === 'calculator') showCalculator();
          if (action === 'export-tex') showTexExport(exportCurrentARQuiverToXyMatrix());
          if (action === 'legend') alert(['Legend:', 'blue border = projective', 'red border = injective', 'purple border = projective-injective', 'gold edge = τ', 'pink edge = syzygy', 'green edge = cosyzygy', 'orange fill = torsion class', 'green fill = torsion-free class', 'gray fill = tilting L'].join('\\n'));
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
          out = out.replace(/^\$+|\$+$/g, '');
          out = stripTexCommandWithBraces(out, 'text');
          out = stripTexCommandWithBraces(out, 'mathrm');
          out = stripTexCommandWithBraces(out, 'operatorname');
          out = out.replace(/_\{([^}]*)\}/g, (_, body) => texScript(body, 'sub'));
          out = out.replace(/\^\{([^}]*)\}/g, (_, body) => texScript(body, 'sup'));
          out = out.replace(/_([A-Za-z0-9+\-=])/g, (_, body) => texScript(body, 'sub'));
          out = out.replace(/\^([A-Za-z0-9+\-=])/g, (_, body) => texScript(body, 'sup'));
          out = translateTexToken(out);
          out = out.split(String.fromCharCode(92)).join('');
          return out;
        }

        function nodeCircleLabel(id) {
          const base = baseNodeStyles.get(id) || baseNodeStyles.get(Number(id));
          if (nodeLabelMode === 'label') return String(id);
          if (nodeLabelMode === 'custom') {
            const custom = customTexLabels.get(id) || customTexLabels.get(Number(id));
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
            return { id: n.id, label: label, title: `Node ${n.id}<br>${label}` };
          });
          if (updates.length) network.body.data.nodes.update(updates);
          nodeLabelButtons.forEach((button, key) => button.classList.toggle('ar-top-active', key === nodeLabelMode));
          network.redraw();
        }

        function createMenuBar() {
          addMenuStyles();
          createFolderPanel();
          menuBar = document.createElement('div');
          menuBar.id = 'arTopMenu';
          menuBar.innerHTML = '<span class="ar-title">AR Quiver</span><button data-action="toggle-panel">Controls</button><button data-action="fit">Fit</button><button data-action="clear-colors">Clear colors</button><button data-label-mode="dimension">show dimension vector</button><button data-label-mode="label">show label</button><button data-label-mode="custom">show custom label</button><span class="ar-spacer"></span><span>Ctrl+L hide/show UI</span>';
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
          const w = Math.max(42, (node.shape && node.shape.width) ? node.shape.width : 46);
          const h = Math.max(30, (node.shape && node.shape.height) ? node.shape.height : 32);
          parts.forEach(part => {
            ctx.save();
            ctx.globalAlpha = 0.55;
            ctx.beginPath();
            if (part.part === 'left') {
              ctx.rect(pos.x - w / 2, pos.y - h / 2, w / 2, h);
            } else if (part.part === 'right') {
              ctx.rect(pos.x, pos.y - h / 2, w / 2, h);
            } else if (part.part === 'top') {
              ctx.rect(pos.x - w / 2, pos.y - h / 2, w, h / 2);
            } else if (part.part === 'bottom') {
              ctx.rect(pos.x - w / 2, pos.y, w, h / 2);
            }
            ctx.clip();
            ctx.beginPath();
            ctx.ellipse(pos.x, pos.y, w / 2, h / 2, 0, 0, 2 * Math.PI);
            ctx.fillStyle = part.color;
            ctx.fill();
            ctx.restore();
          });
        });
      });

      function zeroNodeIds() {
        return new Set((zeroObjectIds || []).map(Number));
      }

      function sortedKey(arr) {
        const zeros = zeroNodeIds();
        return (arr || []).map(Number).filter(n => Number.isFinite(n) && !zeros.has(n)).sort((a, b) => a - b).join(',');
      }

      function findTiltingForTorsionPair(item) {
        const keyT = sortedKey(item.T);
        const keyF = sortedKey(item.F);
        for (let i = 0; i < tiltingData.length; i += 1) {
          const t = tiltingData[i] || {};
          if (sortedKey(t.T) === keyT && sortedKey(t.F) === keyF) {
            return { index: i, item: t };
          }
        }
        return null;
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
        applyFullFill([...L], '#b5b5b5', nextSet);
        applyFullFill(T, '#ffe1c7', nextSet);
        applyFullFill(F, '#d9f2d9', nextSet);
        tiltingHighlighted = nextSet;
        pairHighlighted = nextSet;
        network.unselectAll();
        network.redraw();
      }

      function applyTorsionPairHighlight(item) {
        resetTiltingStyles();
        resetPairStyles();
        const nextSet = new Set();
        applyFullFill(item.T || [], '#ffe1c7', nextSet);
        applyFullFill(item.F || [], '#d9f2d9', nextSet);
        pairHighlighted = nextSet;
        network.unselectAll();
        network.redraw();
      }

      function applyCotorsionPairHighlight(item) {
        resetTiltingStyles();
        resetPairStyles();
        const nextSet = new Set();
        addSplitFill(item.L || [], 'top', '#93c5fd', nextSet);
        addSplitFill(item.R || [], 'bottom', '#fca5a5', nextSet);
        pairHighlighted = nextSet;
        network.unselectAll();
        network.redraw();
      }

      function applySupportTauHighlight(item) {
        resetTiltingStyles();
        resetPairStyles();
        const nextSet = new Set();
        applyFullFill(item.P || [], '#dbeafe', nextSet);
        applyFullFill(item.M || [], '#d1d5db', nextSet);
        pairHighlighted = nextSet;
        network.unselectAll();
        network.redraw();
      }

      function displayClassList(arr) {
        return (!arr || arr.length === 0) ? '0' : arr.join(',');
      }

      const listStates = new Map();

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
        el.querySelectorAll('button[data-row]').forEach((btn, idx) => {
          const active = idx === bounded;
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

        const modeText = state.sortMode === 'lex' ? '字典序' : '数量+字典序';
        const headerButtons = columns.map(col => {
          const active = state.sortKey === col.key;
          return `<button type="button" data-sort-key="${col.key}" style="font-size:11px; margin-right:4px; padding:2px 6px; border:1px solid ${active ? '#0f766e' : '#ccc'}; border-radius:4px; background:${active ? '#ccfbf1' : '#fff'}; cursor:pointer;">${col.label}${active ? ` (${modeText})` : ''}</button>`;
        }).join('');
        const items = rows.map((row, idx) => {
          const body = columns.map(col => `${col.label}=[${displayClassList(row.item[col.key] || [])}]`).join(' | ');
          const extra = formatExtra ? formatExtra(row.item) : '';
          return `<button type="button" data-row="${idx}" class="ar-record-row">${idx + 1}. ${body}${extra}</button>`;
        }).join('');
        el.innerHTML = `<b>${title}</b><div style="margin:4px 0;">${headerButtons}</div><div role="listbox">${items}</div>`;
        typesetMath(el);
        el.querySelectorAll('button[data-sort-key]').forEach(btn => btn.addEventListener('click', () => {
          const key = btn.getAttribute('data-sort-key');
          if (state.sortKey === key) state.sortMode = state.sortMode === 'lex' ? 'lenlex' : 'lex';
          else { state.sortKey = key; state.sortMode = 'lex'; }
          state.selectedIndex = 0;
          renderButtonRecordList(containerId, data, title, columns, applyFn, formatExtra);
        }));
        el.querySelectorAll('button[data-row]').forEach(btn => {
          btn.addEventListener('click', () => activateButtonListRow(containerId, Number(btn.getAttribute('data-row'))));
          btn.addEventListener('keydown', (event) => {
            if (event.key === 'ArrowDown') { event.preventDefault(); activateButtonListRow(containerId, state.selectedIndex + 1); }
            if (event.key === 'ArrowUp') { event.preventDefault(); activateButtonListRow(containerId, state.selectedIndex - 1); }
          });
        });
      }

      function renderSupportTauList(containerId, data, title) {
        renderButtonRecordList(containerId, data, title, [{ key: 'P', label: 'P' }, { key: 'M', label: 'M' }], applySupportTauHighlight);
      }

      function renderPairList(containerId, data, leftKey, rightKey, title, extraRenderer, options = {}) {
        const isTorsion = options.kind === 'torsion';
        const applyFn = (item) => {
          if (isTorsion) {
            const tilting = findTiltingForTorsionPair(item);
            if (tilting) {
              applyTiltingTorsionPairHighlight(tilting.item);
              setActiveTilting(tilting.index);
              const tl = document.getElementById('tiltingList');
              const tt = document.getElementById('tiltingToggle');
              if (tl) tl.style.display = 'block';
              if (tt) tt.checked = true;
            } else {
              applyTorsionPairHighlight(item);
            }
          } else {
            applyCotorsionPairHighlight(item);
          }
        };
        const formatExtra = (item) => {
          if (isTorsion) {
            const tilting = findTiltingForTorsionPair(item);
            return tilting ? ` | Tilting=yes L=[${displayClassList(tilting.item.L || [])}]` : ' | Tilting=no';
          }
          if (extraRenderer) return ` | ${item.hereditary ? 'hereditary' : 'non-hereditary'}`;
          return '';
        };
        renderButtonRecordList(containerId, data, title, [{ key: leftKey, label: leftKey }, { key: rightKey, label: rightKey }], applyFn, formatExtra);
      }

      function renderTiltingList() {
        renderButtonRecordList('tiltingList', tiltingData, 'Tilting modules', [
          { key: 'L', label: 'L' },
          { key: 'F', label: 'F' },
          { key: 'T', label: 'T' }
        ], (item) => {
          resetPairStyles();
          applyTiltingHighlight(item);
          const idx = tiltingData.indexOf(item);
          setActiveTilting(idx);
        });
      }

      function setActiveTilting(idx) {
        const listEl = document.getElementById('tiltingList');
        const buttons = listEl.querySelectorAll('button[data-row]');
        buttons.forEach((b) => {
          const row = Number(b.getAttribute('data-row'));
          const state = listStates.get('tiltingList');
          const originalIndex = state && state.rows[row] ? state.rows[row].originalIndex : row;
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
        const buttons = listEl.querySelectorAll('button');
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

      function makeLabelElement(layer, color, border, background) {
        const el = document.createElement('div');
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
        layer.appendChild(el);
        return el;
      }

      function updateScalarLabels(visible, layer, labelMap, getText, yOffset, color, border, background) {
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
            el = makeLabelElement(layer, color, border, background);
            labelMap.set(id, el);
          }
          el.textContent = text;
          const dom = network.canvasToDOM(positions[id]);
          el.style.left = `${dom.x}px`;
          el.style.top = `${dom.y + yOffset(node)}px`;
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
        }, node => -((node.shape && node.shape.height) ? (node.shape.height / 2 + 42) : 46), '#1f4a7a', '#9eb6d3', 'rgba(255,255,255,0.95)');
      }
      function updateIdValueLabels() {
        updateScalarLabels(showId, idValueLabelLayer, idValueLabelMap, id => {
          const e = pdidEntry(id); return e ? `id=${formatHomologicalDimension(e.id)}` : null;
        }, node => -((node.shape && node.shape.height) ? (node.shape.height / 2 + 24) : 28), '#1f4a7a', '#9eb6d3', 'rgba(255,255,255,0.95)');
      }
      function updateTopLabels() {
        updateScalarLabels(showTop, topLabelLayer, topLabelMap, id => {
          const e = topSocEntry(id); return e ? `Top=${formatSimpleList(e.top)}` : null;
        }, node => ((node.shape && node.shape.height) ? (node.shape.height / 2 + 28) : 34), '#14532d', '#86efac', 'rgba(240,253,244,0.96)');
      }
      function updateSocLabels() {
        updateScalarLabels(showSoc, socLabelLayer, socLabelMap, id => {
          const e = topSocEntry(id); return e ? `Soc=${formatSimpleList(e.soc)}` : null;
        }, node => ((node.shape && node.shape.height) ? (node.shape.height / 2 + 46) : 52), '#14532d', '#86efac', 'rgba(240,253,244,0.96)');
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

        L.forEach(id => applyFill(id, '#b5b5b5'));
        F.forEach(id => applyFill(id, '#d9f2d9'));
        T.forEach(id => applyFill(id, '#ffe1c7'));
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
            if (/\d/.test(ch)) {
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

      function ensureMiniQuiver() {
        if (miniContainer) return;
        miniContainer = document.createElement('div');
        miniContainer.id = 'quiverMiniContainer';
        miniContainer.style.position = 'absolute';
        miniContainer.style.bottom = '10px';
        miniContainer.style.right = '10px';
        miniContainer.style.width = '360px';
        miniContainer.style.background = 'rgba(255,255,255,0.95)';
        miniContainer.style.border = '1px solid #ccc';
        miniContainer.style.padding = '6px';
        miniContainer.style.borderRadius = '6px';
        miniContainer.style.zIndex = '998';
        miniContainer.innerHTML = `
          <div id="quiverMiniHeader" style="font-size:12px; margin-bottom:4px; cursor:move; font-weight:600;">Quiver Q</div>
          <div id="quiverMini" style="width:340px; height:220px; border:1px solid #ddd; background:white;"></div>
          <div id="quiverRel" style="margin-top:6px; font-size:12px; font-family:monospace; white-space:pre-wrap;"></div>
        `;
        document.body.appendChild(miniContainer);
        makeDraggable(miniContainer, miniContainer.querySelector('#quiverMiniHeader'));
        const relBox = miniContainer.querySelector('#quiverRel');
        relBox.textContent = quiverRel ? `rel := ${quiverRel}` : 'rel := []';
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
              if (/\d/.test(row[i])) {
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

      function isBlackEdge(edge) {
        const c = getEdgeColor(edge);
        return c === '#000000' || c === 'black';
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
        if (hoverNodeId !== null) updateHoverTip();
      });

      network.on('hoverNode', function(p) {
        showHoverTip(p.node);
      });
      network.on('blurNode', function() {
        hideHoverTip();
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
          const n_id = Number(p.nodes[0]);
          const current = customTexLabels.get(n_id) || '';
          const wasShowingCustomLabel = nodeLabelMode === 'custom';
          network.setOptions({ interaction: { dragNodes: false } });
          network.unselectAll();
          const input = prompt('Custom TeX label for node ' + n_id, current);
          const releaseNodeAfterPrompt = () => {
            network.unselectAll();
            if (network.body && network.body.nodes && network.body.nodes[n_id]) {
              network.body.nodes[n_id].selected = false;
            }
            network.setOptions({ interaction: { dragNodes: true } });
            network.redraw();
          };
          if (input === null) {
            releaseNodeAfterPrompt();
            setTimeout(releaseNodeAfterPrompt, 0);
            setTimeout(releaseNodeAfterPrompt, 80);
            return;
          }
          const value = input.trim();
          if (value) customTexLabels.set(n_id, value);
          else customTexLabels.delete(n_id);
          const refreshByClickingLabelButtons = () => {
            const labelButton = nodeLabelButtons.get('label');
            const customButton = nodeLabelButtons.get('custom');
            if (labelButton && customButton) {
              labelButton.click();
              setTimeout(() => customButton.click(), 0);
            } else {
              applyNodeLabelMode('label');
              applyNodeLabelMode('custom');
            }
          };
          if (wasShowingCustomLabel) {
            refreshByClickingLabelButtons();
          }
          releaseNodeAfterPrompt();
          setTimeout(releaseNodeAfterPrompt, 0);
          setTimeout(releaseNodeAfterPrompt, 80);
          return;
        }
        if (p.edges.length > 0) {
          const edge_id = p.edges[0];
          const edge = network.body.data.edges.get(edge_id);
          const blackColor = '#000000';
          const lightGray = '#cccccc';
          const goldColor = '#ffd700';
          const lightGold = '#ffe9a6';
          const currentColor = getEdgeColor(edge);
          const isGold = isGoldenEdge(edge) || currentColor === goldColor || currentColor === lightGold || currentColor === 'gold';
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
    js_injection = js_injection.replace("{{Q_NODES}}", q_nodes_js)
    js_injection = js_injection.replace("{{Q_EDGES}}", q_edges_js)
    js_injection = js_injection.replace("{{Q_REL}}", q_rel_js)
    js_injection = js_injection.replace("{{HOM_EDGES}}", hom_edges_js)
    js_injection = js_injection.replace("{{EXT_EDGES}}", ext_edges_js)
    js_injection = js_injection.replace("{{TILTING_DATA}}", tilting_js)
    js_injection = js_injection.replace("{{TORSION_PAIR_DATA}}", torsion_pairs_js)
    js_injection = js_injection.replace("{{COTORSION_PAIR_DATA}}", cotorsion_pairs_js)
    js_injection = js_injection.replace("{{SUPPORT_TAU_TILTING_DATA}}", support_tau_js)
    js_injection = js_injection.replace("{{ALMOST_SUPPORT_TAU_TILTING_DATA}}", almost_support_tau_js)
    js_injection = js_injection.replace("{{PDID_MAP}}", pdid_js)
    js_injection = js_injection.replace("{{TOP_SOC_MAP}}", top_soc_js)
    js_injection = js_injection.replace("{{Q_STRUCTURE}}", q_structure_js)

    # ------------------- JAVASCRIPT MODIFICATION END -------------------
    final_html = html_content.replace('</body>', js_injection + '</body>')
    
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(final_html)
        print(f"✅ 操作成功！已将交互式图形保存到文件: '{output_filename}'")
    except Exception as e:
        print(f"❌ 写入文件时出错: {e}")

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

        detail.innerHTML = `L${idx + 1}: [${L}]<br>F: [${F}]<br>T: [${T}]`;

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



      // Disable hover pd/id tooltip

      window.showHoverTip = function() {};

      window.hideHoverTip = function() {};

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

        print("✅ 已使用统一列表式 tilting 布局")

    except Exception as e:

        print(f"❌ 注入 tilting L 图形失败: {e}")


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
        container.style.background = 'rgba(255,255,255,0.95)';
        container.style.border = '1px solid #ccc';
        container.style.padding = '6px';
        container.style.borderRadius = '6px';
        container.style.zIndex = '9999';
        container.style.boxShadow = '0 2px 10px rgba(0,0,0,0.15)';

        container.innerHTML = `
          <div id=\"tiltingGraphHeader\" style=\"font-size:12px; margin-bottom:4px; cursor:move; font-weight:600;\">Tilting</div>
          <div id=\"tiltingGraph\" style=\"width:360px; height:240px; border:1px solid #ddd; background:white;\"></div>
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
          detail.innerHTML = `L: [${L}]<br>F: [${F}]<br>T: [${T}]`;
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
              const isSplit = !!data[i].split;
              const isSelected = (i == idx);
              
              const finalBg = isSplit ? '#ffcccc' : '#ccf2ff';
              const finalBorder = isSplit ? '#ff0000' : '#00ccff';

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



