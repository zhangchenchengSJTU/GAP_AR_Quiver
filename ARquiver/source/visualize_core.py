
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
    # Tilting data: parse L/F/T blocks
    def parse_list_line(raw_line: str):
        raw = (raw_line or "").strip()
        if not raw:
            return []
        return [int(n) for n in re.split(r"\s*,\s*", raw) if n.strip()]
    
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
    for m in re.finditer(r"^T := \[([^\]]*)\]\s*\|\s*F := \[([^\]]*)\]", content, flags=re.M):
        torsion_pair_data.append({
            "T": parse_list_line(m.group(1)),
            "F": parse_list_line(m.group(2)),
        })

    cotorsion_pair_data = []
    for m in re.finditer(r"^L := \[([^\]]*)\]\s*\|\s*R :=\s*\[([^\]]*)\]\s*\|\s*Hereditary :=\s*(true|false)", content, flags=re.M | re.I):
        cotorsion_pair_data.append({
            "L": parse_list_line(m.group(1)),
            "R": parse_list_line(m.group(2)),
            "hereditary": m.group(3).lower() == "true",
        })

    globals()["torsion_pair_data"] = torsion_pair_data
    globals()["cotorsion_pair_data"] = cotorsion_pair_data

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
            m = re.search(r'pd=(\d+),\s*id=(\d+)', lbl)
            if m:
                nodes_data[node_id]['dim'] = {'pd': int(m.group(1)), 'id': int(m.group(2))}
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

    # Filter out edges that reference zero-dimension nodes
    filtered_edges = [e for e in edges_data if e[0] not in zero_node_ids and e[1] not in zero_node_ids]
    net.add_edges(filtered_edges)
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
    syz_edges_js = json.dumps(syz_edges)
    q_nodes_js = json.dumps(q_nodes)
    q_edges_js = json.dumps(q_edges)
    q_rel_js = json.dumps(rel_content or "")
    hom_edges_js = json.dumps(hom_edges)
    ext_edges_js = json.dumps(ext_edges)
    tilting_js = json.dumps(tilting_data or [])
    torsion_pairs_js = json.dumps(globals().get("torsion_pair_data", []))
    cotorsion_pairs_js = json.dumps(globals().get("cotorsion_pair_data", []))
    pdid_js = json.dumps(pdid_map or {})
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
      const syzygyEdges = {{SYZ_EDGES}};
      const quiverNodes = {{Q_NODES}};
      const quiverEdges = {{Q_EDGES}};
      const quiverRel = {{Q_REL}};
      const homEdges = {{HOM_EDGES}};
      const extEdges = {{EXT_EDGES}};
      const tiltingData = {{TILTING_DATA}};
      const torsionPairData = {{TORSION_PAIR_DATA}};
      const cotorsionPairData = {{COTORSION_PAIR_DATA}};
      const pdidMap = {{PDID_MAP}};
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
        const pairMap = {};
        allEdges.forEach(e => {
          const a = (typeof e.from === 'number') ? e.from : parseInt(e.from);
          const b = (typeof e.to === 'number') ? e.to : parseInt(e.to);
          const key = Math.min(a, b) + '-' + Math.max(a, b);
          if (!pairMap[key]) pairMap[key] = [];
          pairMap[key].push(e.id);
        });
        const updates = [];
        Object.values(pairMap).forEach(ids => {
          if (ids.length <= 1) return;
          const n = ids.length;
          const step = 0.2;
          ids.forEach((id, i) => {
            const curvature = (i - (n - 1) / 2) * step;
            if (Math.abs(curvature) < 0.01) {
              updates.push({ id, smooth: false });
            } else {
              updates.push({
                id,
                smooth: {
                  enabled: true,
                  type: curvature > 0 ? 'curvedCW' : 'curvedCCW',
                  roundness: Math.abs(curvature)
                }
              });
            }
          });
        });
        if (updates.length) netObj.body.data.edges.update(updates);
      }

      function addLabeledEdges(prefix, edges, color, width) {
        const toAdd = edges.map((e, i) => {
          const label = (e[2] || '').toString();
          return {
            id: `${prefix}_${i}`,
            from: e[0],
            to: e[1],
            label: label && label !== '0' ? label : undefined,
            color: color,
            width: width,
            arrows: 'to',
            dashes: false
          };
        });
        network.body.data.edges.add(toAdd);
      }

      function removeEdgesByPrefix(prefix) {
        const existing = network.body.data.edges.get({
          filter: (edge) => edge.id && String(edge.id).startsWith(prefix)
        }).map(e => e.id);
        if (existing.length) network.body.data.edges.remove(existing);
      }

      // --- Buttons (right) ---
      let editMode = false;
      let miniQuiver = null;
      let miniContainer = null;
      let showLabels = false;
      let showBorders = true;
      let showPdid = false;
      let idLabelLayer = null;
      let pdidLabelLayer = null;
      const idLabelMap = new Map();
      const pdidLabelMap = new Map();
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
              <input id="showLabelToggle" type="checkbox" /> Label
            </label>
            <label style="font-size:12px; background: rgba(255,255,255,0.8); padding:4px 8px; border-radius:4px;">
              <input id="pdidToggle" type="checkbox" /> PDID
            </label>
            <label style="font-size:12px; background: rgba(255,255,255,0.8); padding:4px 8px; border-radius:4px;">
              <input id="borderToggle" type="checkbox" checked /> Border
            </label>
          </div>
          <div id="tiltingList" style="display:none; background: rgba(255,255,255,0.9); padding:6px; border-radius:6px; max-height:240px; overflow:auto; font-size:12px;"></div>
          <div id="torsionPairList" style="display:none; background: rgba(255,255,255,0.9); padding:6px; border-radius:6px; max-height:260px; overflow:auto; font-size:12px;"></div>
          <div id="cotorsionPairList" style="display:none; background: rgba(255,255,255,0.9); padding:6px; border-radius:6px; max-height:260px; overflow:auto; font-size:12px;"></div>
        `;
        document.body.appendChild(container);
        function emphasizeNodeSet(ids, color) {
          const idsArray = (ids || []).map(Number).filter(x => !Number.isNaN(x));
          if (!idsArray.length) return false;
          const allNodes = network.body.data.nodes.get();
          const idSet = new Set(idsArray);
          const updates = allNodes.map(n => {
            const base = baseNodeStyles.get(n.id) || {};
            if (idSet.has(Number(n.id))) {
              return { id: n.id, color: { border: color, background: '#fff7cc', highlight: { border: color, background: '#ffe680' } }, borderWidth: 5 };
            }
            return { id: n.id, color: base.color || n.color, borderWidth: base.borderWidth || n.borderWidth || 1 };
          });
          network.body.data.nodes.update(updates);
          network.selectNodes(idsArray);
          if (idsArray.length === 1) network.focus(idsArray[0], { scale: 1.2, animation: true });
          else network.fit({ nodes: idsArray, animation: true });
          return true;
        }
        document.getElementById('torsBtn').addEventListener('click', () => {
          if (!emphasizeNodeSet(torsionlessIds, '#0ea5e9')) alert('No torsionless modules found.');
        });
        document.getElementById('reflBtn').addEventListener('click', () => {
          if (!emphasizeNodeSet(reflexiveIds, '#8b5cf6')) alert('No reflexive modules found.');
        });
        document.getElementById('gpBtn').addEventListener('click', () => {
          if (!emphasizeNodeSet(gorensteinProjectiveIds, '#16a34a')) alert('No Gorenstein projective modules found.');
        });
        document.getElementById('giBtn').addEventListener('click', () => {
          if (!emphasizeNodeSet(gorensteinInjectiveIds, '#dc2626')) alert('No Gorenstein injective modules found.');
        });
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
              dashes: false
            }));
            network.body.data.edges.add(toAdd);
          } else {
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
              dashes: false
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
              dashes: false
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
        document.getElementById('torsionPairToggle').addEventListener('change', (e) => {
          const el = document.getElementById('torsionPairList');
          if (!el) return;
          el.style.display = e.target.checked ? 'block' : 'none';
          if (e.target.checked) renderPairList('torsionPairList', torsionPairData, 'T', 'F', 'Torsion pairs');
        });
        document.getElementById('cotorsionPairToggle').addEventListener('change', (e) => {
          const el = document.getElementById('cotorsionPairList');
          if (!el) return;
          el.style.display = e.target.checked ? 'block' : 'none';
          if (e.target.checked) renderPairList('cotorsionPairList', cotorsionPairData, 'L', 'R', 'Cotorsion pairs', item => `<td style="border:1px solid #ddd; padding:3px;">${item.hereditary ? 'hereditary' : 'non-hereditary'}</td>`);
        });
        document.getElementById('showLabelToggle').addEventListener('change', (e) => {
          showLabels = e.target.checked;
          toggleShowLabels(showLabels);
        });
        document.getElementById('pdidToggle').addEventListener('change', (e) => {
          showPdid = e.target.checked;
          togglePdidLabels(showPdid);
        });
        document.getElementById('borderToggle').addEventListener('change', (e) => {
          showBorders = e.target.checked;
          toggleNodeBorders(showBorders);
        });
      })();

      function renderPairList(containerId, data, leftKey, rightKey, title, extraRenderer) {
        const el = document.getElementById(containerId);
        if (!el) return;
        if (!data || data.length === 0) {
          el.innerHTML = `<b>${title}</b><br/><span style="color:#666;">No data.</span>`;
          return;
        }
        const rows = data.map((item, idx) => {
          const left = item[leftKey] || [];
          const right = item[rightKey] || [];
          const extra = extraRenderer ? extraRenderer(item) : '';
          return `<tr>
            <td style="border:1px solid #ddd; padding:3px;">${idx + 1}</td>
            <td style="border:1px solid #ddd; padding:3px; cursor:pointer;" data-left="${left.join(',')}">${left.join(', ')}</td>
            <td style="border:1px solid #ddd; padding:3px; cursor:pointer;" data-right="${right.join(',')}">${right.join(', ')}</td>
            ${extra}
          </tr>`;
        }).join('');
        el.innerHTML = `<b>${title}</b><table style="border-collapse:collapse; width:100%; margin-top:4px; font-family:monospace; font-size:11px;">
          <thead><tr><th>#</th><th>${leftKey}</th><th>${rightKey}</th>${extraRenderer ? '<th>Info</th>' : ''}</tr></thead>
          <tbody>${rows}</tbody></table>`;
        el.querySelectorAll('[data-left]').forEach(cell => cell.addEventListener('click', () => {
          const ids = cell.getAttribute('data-left').split(',').filter(Boolean).map(Number);
          emphasizeNodeSet(ids, '#f59e0b');
        }));
        el.querySelectorAll('[data-right]').forEach(cell => cell.addEventListener('click', () => {
          const ids = cell.getAttribute('data-right').split(',').filter(Boolean).map(Number);
          emphasizeNodeSet(ids, '#10b981');
        }));
      }

      function renderTiltingList() {
        const listEl = document.getElementById('tiltingList');
        listEl.innerHTML = '';
        tiltingData.forEach((item, idx) => {
          const btn = document.createElement('button');
          btn.style.display = 'block';
          btn.style.width = '100%';
          btn.style.margin = '2px 0';
          btn.textContent = `L${idx + 1}: [${(item.L || []).join(', ')}]`;
          btn.addEventListener('click', () => {
            applyTiltingHighlight(item);
            setActiveTilting(idx);
          });
          listEl.appendChild(btn);
        });
      }

      function setActiveTilting(idx) {
        const listEl = document.getElementById('tiltingList');
        const buttons = listEl.querySelectorAll('button');
        buttons.forEach((b, i) => {
          if (i === idx) {
            b.classList.add('tilting-btn-active');
          } else {
            b.classList.remove('tilting-btn-active');
          }
        });
      }

      function clearActiveTilting() {
        const listEl = document.getElementById('tiltingList');
        const buttons = listEl.querySelectorAll('button');
        buttons.forEach((b) => b.classList.remove('tilting-btn-active'));
      }

      function getActiveTiltingIndex() {
        const listEl = document.getElementById('tiltingList');
        const buttons = listEl.querySelectorAll('button');
        for (let i = 0; i < buttons.length; i++) {
          if (buttons[i].classList.contains('tilting-btn-active')) return i;
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

      function ensurePdidLabelLayer() {
        if (pdidLabelLayer) return;
        pdidLabelLayer = document.createElement('div');
        pdidLabelLayer.style.position = 'absolute';
        pdidLabelLayer.style.left = '0';
        pdidLabelLayer.style.top = '0';
        pdidLabelLayer.style.width = '100%';
        pdidLabelLayer.style.height = '100%';
        pdidLabelLayer.style.pointerEvents = 'none';
        pdidLabelLayer.style.zIndex = '998';
        network.body.container.appendChild(pdidLabelLayer);
      }

      function updateIdLabels() {
        if (!showLabels || !idLabelLayer) return;
        const positions = network.getPositions();
        Object.keys(positions).forEach(idStr => {
          const id = Number(idStr);
          if (!Number.isFinite(id)) return;
          const node = network.body.nodes[id];
          if (!node) return;
          let el = idLabelMap.get(id);
          if (!el) {
            el = document.createElement('div');
            el.style.position = 'absolute';
            el.style.fontSize = '12px';
            el.style.color = '#5b3a1e';
            el.style.fontFamily = 'monospace';
            el.style.fontWeight = 'normal';
            el.style.transform = 'translate(-50%, 0)';
            el.style.background = 'rgba(255,255,255,0.95)';
            el.style.border = '1px solid #c8b08b';
            el.style.borderRadius = '4px';
            el.style.padding = '1px 4px';
            el.style.boxShadow = '0 1px 2px rgba(0,0,0,0.1)';
            el.textContent = String(id);
            idLabelLayer.appendChild(el);
            idLabelMap.set(id, el);
          }
          const dom = network.canvasToDOM(positions[id]);
          const offset = (node.shape && node.shape.height) ? (node.shape.height / 2 + 8) : 18;
          el.style.left = `${dom.x}px`;
          el.style.top = `${dom.y + offset}px`;
        });
      }

      function updatePdidLabels() {
        if (!showPdid || !pdidLabelLayer) return;
        const positions = network.getPositions();
        Object.keys(positions).forEach(idStr => {
          const id = Number(idStr);
          if (!Number.isFinite(id)) return;
          const entry = (pdidMap && (pdidMap[id] || pdidMap[String(id)]));
          if (!entry) return;
          const node = network.body.nodes[id];
          if (!node) return;
          let el = pdidLabelMap.get(id);
          if (!el) {
            el = document.createElement('div');
            el.style.position = 'absolute';
            el.style.fontSize = '12px';
            el.style.color = '#1f4a7a';
            el.style.fontFamily = 'monospace';
            el.style.fontWeight = 'normal';
            el.style.transform = 'translate(-50%, 0)';
            el.style.background = 'rgba(255,255,255,0.95)';
            el.style.border = '1px solid #9eb6d3';
            el.style.borderRadius = '4px';
            el.style.padding = '1px 4px';
            el.style.boxShadow = '0 1px 2px rgba(0,0,0,0.1)';
            el.style.whiteSpace = 'pre';
            el.textContent = `pd = ${entry.pd}\nid = ${entry.id}`;
            pdidLabelLayer.appendChild(el);
            pdidLabelMap.set(id, el);
          }
          const dom = network.canvasToDOM(positions[id]);
          const offset = (node.shape && node.shape.height) ? (node.shape.height / 2 + 26) : 30;
          el.style.left = `${dom.x}px`;
          el.style.top = `${dom.y - offset}px`;
        });
      }

      function showIdLabels() {
        ensureIdLabelLayer();
        idLabelLayer.style.display = 'block';
        updateIdLabels();
      }

      function showPdidLabels() {
        ensurePdidLabelLayer();
        pdidLabelLayer.style.display = 'block';
        updatePdidLabels();
      }

      function hideIdLabels() {
        if (idLabelLayer) idLabelLayer.style.display = 'none';
      }

      function hidePdidLabels() {
        if (pdidLabelLayer) pdidLabelLayer.style.display = 'none';
      }

      function ensureHoverTip() {
        if (hoverTip) return;
        hoverTip = document.createElement('div');
        hoverTip.style.position = 'absolute';
        hoverTip.style.pointerEvents = 'none';
        hoverTip.style.background = 'rgba(255,255,255,0.95)';
        hoverTip.style.border = '1px solid #c8b08b';
        hoverTip.style.borderRadius = '4px';
        hoverTip.style.padding = '2px 6px';
        hoverTip.style.fontSize = '12px';
        hoverTip.style.fontFamily = 'monospace';
        hoverTip.style.color = '#000';
        hoverTip.style.zIndex = '996';
        hoverTip.style.display = 'none';
        network.body.container.appendChild(hoverTip);
      }

      function updateHoverTip() {
        if (!hoverTip || hoverNodeId === null) return;
        const pos = network.getPositions([hoverNodeId])[hoverNodeId];
        const node = network.body.nodes[hoverNodeId];
        if (!pos || !node) return;
        const dom = network.canvasToDOM(pos);
        const offset = (node.shape && node.shape.height) ? (node.shape.height / 2 + 18) : 28;
        hoverTip.style.left = `${dom.x}px`;
        hoverTip.style.top = `${dom.y - offset}px`;
      }

      function showHoverTip(id) {
        const entry = (pdidMap && (pdidMap[id] || pdidMap[String(id)]));
        if (!entry) return;
        ensureHoverTip();
        hoverNodeId = id;
        hoverTip.textContent = `pd=${entry.pd}, id=${entry.id}`;
        hoverTip.style.display = 'block';
        updateHoverTip();
      }

      function hideHoverTip() {
        if (!hoverTip) return;
        hoverNodeId = null;
        hoverTip.style.display = 'none';
      }

      function toggleShowLabels(visible) {
        showLabels = visible;
        if (showLabels) {
          showIdLabels();
        } else {
          hideIdLabels();
        }
      }

      function togglePdidLabels(visible) {
        showPdid = visible;
        if (showPdid) {
          showPdidLabels();
        } else {
          hidePdidLabels();
        }
      }

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
          shadow: { enabled: false }
        });
      }

      function resetTiltingStyles() {
        tiltingHighlighted.forEach(id => restoreNodeBase(id));
        tiltingHighlighted = new Set();
      }

      function applyTiltingHighlight(item) {
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
        setTimeout(() => assignMultiEdgeCurves(miniQuiver), 50);
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
            netObj.body.data.edges.update({ id, smooth: { enabled: true, type: nextType, roundness: nextRound } });
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
        } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'l') {
          e.preventDefault();
          const lightGray = '#cccccc';
          const lightGold = '#ffe9a6';
          const edges = network.body.data.edges.get();
          const toRemove = edges.filter(e => {
            const c = getEdgeColor(e);
            return c === lightGray || c === lightGold;
          }).map(e => e.id);
          if (toRemove.length) {
            snapshot();
            network.body.data.edges.remove(toRemove);
          }
        } else if (e.key === 'Delete' || e.key === 'Backspace') {
          snapshot();
          network.deleteSelected();
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
          if (showPdid) updatePdidLabels();
        }
      });

      network.on('afterDrawing', function() {
        if (showLabels) updateIdLabels();
        if (showPdid) updatePdidLabels();
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
        if (editMode) {
          if (p.nodes.length > 0) {
            const n_id = p.nodes[0];
            const node = network.body.data.nodes.get(n_id);
            const newLabel = prompt('New node label', node.label);
            if (newLabel !== null) {
              const currentBorder = (node.color && node.color.border) ? node.color.border : 'gray';
              const colorInput = (prompt('Border color (red/blue/purple/green/gray)', currentBorder) || currentBorder).toLowerCase();
              const allowed = ['red','blue','purple','green','gray'];
              const border = allowed.includes(colorInput) ? colorInput : currentBorder;
              snapshot();
              const newColor = { border: border, background: 'white', highlight: { border: border, background: '#D2E5FF' } };
              network.body.data.nodes.update({
                id: n_id,
                label: newLabel,
                title: `Node ${n_id}<br>${newLabel}`,
                color: newColor,
                borderWidth: showBorders ? 3 : 0,
                borderWidthSelected: showBorders ? 5 : 0,
                font: { color: 'black', face: 'monospace', size: 14, bold: true, vadjust: 0, align: 'center' }
              });
              const updated = network.body.data.nodes.get(n_id);
              if (updated) {
                baseNodeStyles.set(n_id, toBaseStyle({ ...updated, label: newLabel }));
              }
            }
          } else if (p.edges.length > 0) {
            const e_id = p.edges[0];
            const edge = network.body.data.edges.get(e_id);
            const newLabel = prompt('New edge label', edge.label || '');
            if (newLabel !== null) {
              snapshot();
              network.body.data.edges.update({ id: e_id, label: newLabel });
            }
          }
          return;
        }
        if (p.nodes.length > 0) {
          snapshot();
          const n_id = p.nodes[0];
          const n_pos = network.getPositions([n_id])[n_id];
          const o_node = network.body.data.nodes.get(n_id);
          const new_id = 'copy_' + n_id + '_' + Date.now();
          network.body.data.nodes.add({ id: new_id, label: o_node.label, shape: 'ellipse', color: o_node.color, font: {color: 'black', face: 'monospace', size: 14, bold: true, vadjust: 0, align: 'center'}, x: n_pos.x + 50, y: n_pos.y + 50, title: `Copy of ${o_node.id}`, borderWidth: showBorders ? 3 : 0, borderWidthSelected: showBorders ? 5 : 0});
          network.getConnectedEdges(n_id).forEach(function(e_id) {
            const edge = network.body.data.edges.get(e_id);
            network.body.data.edges.add({
              from: (edge.from === n_id) ? new_id : edge.from,
              to: (edge.to === n_id) ? new_id : edge.to,
              arrows: 'to',
              color: edge.color || '#000000',
              width: edge.width || 1
            });
          });
        } else if (p.edges.length > 0) {
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
              if (currentColor === lightGold) {
                  newColor = goldColor;
              } else {
                  newColor = lightGold;
              }
          } else {
              if (currentColor === lightGray) {
                  newColor = blackColor;
              } else {
                  newColor = lightGray;
              }
          }
          snapshot();
          network.body.data.edges.update({ id: edge_id, color: { color: newColor } });
        }
      });

      // Auto-reassign multi-edge curves when any edge toggle changes
      ['syzToggle','homToggle','extToggle','irrToggle','trToggle'].forEach(tid => {
        const el = document.getElementById(tid);
        if (el) el.addEventListener('change', () => {
          setTimeout(() => assignMultiEdgeCurves(network), 50);
        });
      });
      assignMultiEdgeCurves(network);

      // defaults
      toggleShowLabels(false);
      togglePdidLabels(false);
      toggleNodeBorders(true);
    </script>
    """
    js_injection = js_injection.replace("{{GOLDEN_EDGES}}", golden_edges_js_string)
    js_injection = js_injection.replace("{{TORS_IDS}}", tors_ids_js)
    js_injection = js_injection.replace("{{REFL_IDS}}", refl_ids_js)
    js_injection = js_injection.replace("{{GP_IDS}}", gp_ids_js)
    js_injection = js_injection.replace("{{GI_IDS}}", gi_ids_js)
    js_injection = js_injection.replace("{{SYZ_EDGES}}", syz_edges_js)
    js_injection = js_injection.replace("{{Q_NODES}}", q_nodes_js)
    js_injection = js_injection.replace("{{Q_EDGES}}", q_edges_js)
    js_injection = js_injection.replace("{{Q_REL}}", q_rel_js)
    js_injection = js_injection.replace("{{HOM_EDGES}}", hom_edges_js)
    js_injection = js_injection.replace("{{EXT_EDGES}}", ext_edges_js)
    js_injection = js_injection.replace("{{TILTING_DATA}}", tilting_js)
    js_injection = js_injection.replace("{{TORSION_PAIR_DATA}}", torsion_pairs_js)
    js_injection = js_injection.replace("{{COTORSION_PAIR_DATA}}", cotorsion_pairs_js)
    js_injection = js_injection.replace("{{PDID_MAP}}", pdid_js)
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

        print("✅ 已注入 tilting L 图形与 PDID 悬停禁用")

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
        return f"pd={dim_list['pd']}, id={dim_list['id']}"
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


try:
    with open(output_file, 'r', encoding='utf-8') as f:
        html = f.read()

    html = _inject_tilting_graph_fallback(html)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print("✅ 已追加 tilting 图形 fallback hook")
except Exception as e:
    print(f"❌ 追加 tilting fallback 失败: {e}")


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


try:
    with open(output_file, 'r', encoding='utf-8') as f:
        html = f.read()

    html = _inject_tilting_graph_override(html)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print("✅ 已注入 tilting 图形覆盖逻辑")
except Exception as e:
    print(f"❌ 注入 tilting 图形覆盖失败: {e}")


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
try:
    if 'output_file' not in locals():
         output_file = 'quiver_Q.html'

    # Ensure we use the correct file
    print(f"DEBUG: Auto-Injection target: {output_file}")

    with open(output_file, 'r', encoding='utf-8') as f:
        html = f.read()

    html = _inject_tilting_window_like_quiver(html)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ AUTO-INJECTED V20 Tilting & Quiver Windows into: {output_file}")
except Exception as e:
    print(f"❌ Injection Failed: {e}")

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

try:
    if 'output_file' not in locals():
        output_file = 'quiver_Q.html'
    with open(output_file, 'r', encoding='utf-8') as f:
        html = f.read()
    new_html = _greekize_text(html)
    if new_html != html:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(new_html)
        print("✅ Greek letter conversion applied to output HTML")
    else:
        print("ℹ️ No Greek letter replacements needed")
except Exception as e:
    print(f"❌ Greek letter conversion failed: {e}")

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

try:
    if 'output_file' not in locals():
        output_file = 'quiver_Q.html'
    with open(output_file, 'r', encoding='utf-8') as f:
        html = f.read()
    html = _inject_relation_formatter(html)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ Relation display formatted as requested")
except Exception as e:
    print(f"❌ Relation formatter injection failed: {e}")
