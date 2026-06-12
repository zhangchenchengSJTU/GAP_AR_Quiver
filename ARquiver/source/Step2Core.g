# ARquiver Step2 core computation script.
# This file is generated from the cleaned Step2 workflow and is intended
# to be loaded from GAP/Jupyter with: Read("Step2Core.g");;

# ===== Step2.ipynb cell 0 =====
LoadPackage("QPA");;
compute_tilting := true;;
ar_strategy := "hybrid";;
V := [];;

# ===== Step2.ipynb cell 1 =====
# Decompose a module into projections onto indecomposable summands.
FindNontrivialIdempotent := function(M)
    local HomMM, mm, m, n, i, f, e, imgDim;

    # --- Step 1: Handle trivial cases ---
    if Dimension(M) = 0 then
        return false;
    fi;

    HomMM := HomOverAlgebra(M, M);
    mm := Length(HomMM);

    # If End(M) is 0 or 1-dimensional, M must be indecomposable.
    if mm <= 1 then
        return false;
    fi;

    # --- Step 2: Set up parameters for the power-up algorithm ---
    # We need an exponent large enough for the power-up to converge.
    # The maximum of the dimension vector is a safe and standard upper bound
    # for the nilpotency index of the Jacobson radical of the endomorphism algebra.
    m := Maximum(DimensionVector(M));
    n := Int(Ceil(Log2(1.0 * m)));

    # --- Step 3: Find a non-trivial idempotent with a single loop ---
    # This is the core improvement. We iterate through the basis elements of Hom(M,M)
    # only once. If the module is decomposable, its endomorphism algebra is not
    # local, and this process is guaranteed to find a non-trivial idempotent.
    for i in [1..mm] do
        f := HomMM[i];

        # The standard "power-up" algorithm: The sequence f, f^2, f^4, f^8, ...
        # is guaranteed to converge to an idempotent element.
        e := f;
        for i in [1..n] do
            e := e * e;
        od;

        # Check if the resulting idempotent is non-trivial (i.e., not 0 or 1).
        # For idempotents, image dimension 0 means zero map; full dimension means identity.
        imgDim := Dimension(Image(e));
        if imgDim <> 0 and imgDim <> Dimension(M) then
            # Success! Return the idempotent immediately.
            return e;
        fi;
    od;

    # If the loop completes, no non-trivial idempotent was found from the basis
    # elements, meaning the module is indecomposable.
    return false;
end;


# Return split epimorphisms M -> summands.
DecomposeToProjections := function(M)
  local e, id, eK, U, K, pU, pK, projsU, projsK, projs, p;

  if Dimension(M) = 0 then
    return [];
  fi;

  e := FindNontrivialIdempotent(M);
  if e = false then
    return [ IdentityMapping(M) ];
  fi;

  id := IdentityMapping(M);
  eK := id - e;
  U := Image(e);
  K := Image(eK);
  pU := ImageProjection(e);
  pK := ImageProjection(eK);

  projsU := DecomposeToProjections(U);
  projsK := DecomposeToProjections(K);

  projs := [];
  for p in projsU do
    Add(projs, pU * p);
  od;
  for p in projsK do
    Add(projs, pK * p);
  od;

  return projs;
end;

# Return split monomorphisms summands -> M.
DecomposeToInjections := function(M)
  local e, id, eK, U, K, iU, iK, injsU, injsK, injs, p;

  if Dimension(M) = 0 then
    return [];
  fi;

  e := FindNontrivialIdempotent(M);
  if e = false then
    return [ IdentityMapping(M) ];
  fi;

  id := IdentityMapping(M);
  eK := id - e;
  U := Image(e);
  K := Image(eK);
  iU := ImageInclusion(e);
  iK := ImageInclusion(eK);

  injsU := DecomposeToInjections(U);
  injsK := DecomposeToInjections(K);

  injs := [];
  for p in injsU do
    Add(injs, p * iU);
  od;
  for p in injsK do
    Add(injs, p * iK);
  od;

  return injs;
end;

# ===== Step2.ipynb cell 2 =====
# Compute P and I first!
I := [];;

IrrFrom := function(M)
    local p, fList, f, q, h, K, summands, L, lenf, injs, valid_dims, inj;
    # If M is injective (or isomorphic to an injective), use the socle inclusion to define the unique map h.
    for inj in I do
        if IsomorphicModules(M, inj) then
            h := CoKernelProjection(SocleOfModuleInclusion(inj));
            K := Range(h);
            L := DecomposeToProjections(K);
            summands := List(L, l -> h * l);
            return summands;
        fi;
    od;
    p := CoKernelProjection(InjectiveEnvelope(M));
    fList := HomOverAlgebra(TrD(M), Range(p));
    lenf := Length(fList);
    for f in fList do
        q := PullBack(p, f);
        # Compute kernel and its summands for dimension checks (skip if any summand has forbidden dimension)
        h := KernelInclusion(q[1]);
        K := Range(h);
        injs := DecomposeToInjections(K);
        valid_dims := ForAll(injs, i -> (Dimension(Source(i)) <> Dimension(TrD(M)) and Dimension(Source(i)) <> Dimension(M)));
        if lenf = 1 or (valid_dims and IsRightMinimal(q[1])) then
            L := DecomposeToProjections(K);
            summands := List(L, l -> h * l);
            return summands;
        fi;
    od;
    # If no suitable f found, return empty list.
    return [];
end;

# ===== Step2.ipynb cell 3 =====
# Compute P and I first!
IrrFromGuess := function(M)
    local p, fList, f, q, h, K, summands, L, lenf, injs, valid_dims, inj;
    # If M is injective (or isomorphic to an injective), use the socle inclusion to define the unique map h.
    for inj in I do
        if IsomorphicModules(M, inj) then
            h := CoKernelProjection(SocleOfModuleInclusion(inj));
            K := Range(h);
            L := DecomposeToProjections(K);
            summands := List(L, l -> h * l);
            return summands;
        fi;
    od;
    p := CoKernelProjection(InjectiveEnvelope(M));
    fList := HomOverAlgebra(TrD(M), Range(p));
    lenf := Length(fList);
    for f in fList do
        q := PullBack(p, f);
        # Compute kernel and its summands for dimension checks (skip if any summand has forbidden dimension)
        h := KernelInclusion(q[1]);
        K := Range(h);
        injs := DecomposeToInjections(K);
        valid_dims := ForAll(injs, i -> (Dimension(Source(i)) <> Dimension(TrD(M)) and Dimension(Source(i)) <> Dimension(M)));
        # Take the first q whose kernel summands pass the dimension checks (no RightMinimal verification)
        if lenf = 1 or valid_dims then
            L := DecomposeToProjections(K);
            summands := List(L, l -> h * l);
            return summands;
        fi;
    od;
    # If no suitable f found, return empty list.
    return [];
end;

# ===== Source input config =====
if not IsBoundGlobal("input_txt_path") then
    input_txt_path := "Step1.txt";;
fi;
if not IsBoundGlobal("output_log_path") then
    output_log_path := fail;;
fi;

step1_path := input_txt_path;;
if not IsReadableFile(step1_path) then
    Error("Input txt file not found: ", step1_path);
fi;

Print("Reading config from: ", step1_path, "\n");
input_stream := InputTextFile(step1_path);;
file_content := ReadAll(input_stream);;
CloseStream(input_stream);;

file_lines := SplitString(file_content, "\n");;

# Init vars
n_verts := 0;;
Q_arrows := [];;
rel_list := [];;
qs_rows := [];;
curr_mode := "none";;

# Defaults
run_depth := 4;;
output_name := "Q";;
# Whether to use the guess-mode (use IrrFromGuess)
guess := false;;

if PositionSublist(file_content, "\\begin{tikzcd}") <> fail then
    parser_candidates := [
        "source/Step1Parser.g",
        "Step1Parser.g",
        "ARquiver/source/Step1Parser.g",
        "ARquiver/Step1Parser.g",
        "/home/czhang/GapDocs/ARquiver/source/Step1Parser.g"
    ];;
    parser_path := fail;;
    for path in parser_candidates do
        if IsReadableFile(path) then
            parser_path := path;;
            break;;
        fi;
    od;
    if parser_path = fail then
        Error("Step1Parser.g not found! Checked: ", parser_candidates);
    fi;
    Read(parser_path);;
else
    for line_raw in file_lines do
        line := Filtered(line_raw, c -> c <> '\r');;
        toks := Filtered(SplitString(line, " \t"), x -> Length(x) > 0);;
    
        if Length(toks) = 0 then continue; fi;
    
        head_raw := toks[1];;
        if head_raw[Length(head_raw)] = ':' then
            head_clean := head_raw{[1..Length(head_raw)-1]};;
        else
            head_clean := head_raw;;
        fi;
        head_lower := LowercaseString(head_clean);;
    
        if head_lower = "vertices" then
            nums := [];;
            start_idx := 2;;
            for i in [start_idx..Length(toks)] do
                val := Int(toks[i]);;
                if val <> fail then Add(nums, val); fi;
            od;
            if Length(nums) > 0 then n_verts := Maximum(nums); fi;
            curr_mode := "none";;
        
        elif head_lower = "edges" then
            curr_mode := "edges";;
        
        elif head_lower = "relations" or head_lower = "rel" then
            curr_mode := "relations";;
        
        elif head_lower = "style" then
            curr_mode := "style";;
            if Length(toks) > 1 then
                 row_content := JoinStringsWithSeparator(toks{[2..Length(toks)]}, "");;
                 Add(qs_rows, row_content);;
            fi;
        
        elif head_lower = "depth" then
            if Length(toks) >= 2 then
                val := Int(toks[2]);;
                if val <> fail then run_depth := val; fi;
            fi;
            curr_mode := "none";;

        elif head_lower = "name" or head_lower = "file" then
            if Length(toks) >= 2 then
                output_name := toks[2];;
            fi;
            curr_mode := "none";;

        elif head_lower = "guess" then
            if Length(toks) >= 2 then
                if UppercaseString(toks[2]) = "T" then
                    guess := true;
                else
                    guess := false;
                fi;
            fi;
            curr_mode := "none";;
        
        else
            if curr_mode = "edges" then
                if Length(toks) >= 3 then
                    s := Int(toks[1]);;
                    t := Int(toks[2]);;
                    lbl := toks[3];;
                    if s <> fail and t <> fail then
                        Add(Q_arrows, [s, t, lbl]);;
                        if s > n_verts then n_verts := s; fi;
                        if t > n_verts then n_verts := t; fi;
                    fi;
                fi;
            elif curr_mode = "relations" then
                raw_expr := JoinStringsWithSeparator(toks, "*");
                raw_expr := ReplacedString(raw_expr, "*-*", "-");
                raw_expr := ReplacedString(raw_expr, "*+*", "+");
                Add(rel_list, raw_expr);
            elif curr_mode = "style" then
                 row_content := JoinStringsWithSeparator(toks, "");;
                 Add(qs_rows, row_content);;
            fi;
        fi;
    od;

fi;

if n_verts = 0 then
    Error("Failed to parse Vertices or Edges. n_verts is 0.");
fi;

Q := Quiver(n_verts, Q_arrows);;
if Length(rel_list) > 0 then
    rel_input_str := Concatenation("[", JoinStringsWithSeparator(rel_list, ","), "]");;
else
    rel_input_str := "[]";;
fi;

if Length(qs_rows) > 0 then
    QuiverStructure := Concatenation("[", JoinStringsWithSeparator(qs_rows, ";"), "]");;
else
    QuiverStructure := "[]";;
fi;

Print("Loaded config:\n");
Print("  Vertices: ", n_verts, "\n");
Print("  Depth:    ", run_depth, "\n");
Print("  File:     ", output_name, "\n");
Print("  Style:    ", QuiverStructure, "\n");
Print("  Guess:    ", guess, "\n");

# ===== Step2.ipynb cell 5 =====
kQ := PathAlgebra(Rationals, Q);;
AssignGeneratorVariables(kQ);;
rel := EvalString(rel_input_str);;
A := kQ/rel;;

# ===== Step2.ipynb cell 6 =====
P := IndecProjectiveModules(A);;
I := IndecInjectiveModules(A);;
S := SimpleModules(A);;

# ===== Step2.ipynb cell 7 =====
# 递归 Irreducible 态射
# Load necessary packages (run this once per session)
LoadPackage("digraphs");;

# =================================================================
#  基础辅助函数
# =================================================================

PositionIsomorphic := function(list, module)
    local i;
    for i in [1..Length(list)] do
        if IsomorphicModules(list[i], module) then return i; fi;
    od;
    return fail;
end;;

IsIsomorphicToAny := function(module, list)
    local item, isoCall;
    for item in list do
        if IsIdenticalObj(item, fail) then
            continue;
        fi;
        if IsInt(item) and item = 0 then
            continue;
        fi;
        isoCall := CALL_WITH_CATCH(IsomorphicModules, [module, item]);
        if isoCall[1] = true and isoCall[2] = true then return true; fi;
    od;
    return false;
end;;

WriteQuiverAndRelations := function(fname, Q, rel)
    local v, a, s, t, lbl, rel_str, getArrows, getVertices, arrows_list, vertices_list, nv, nvCall,
        arrows_fallback, max_v;

    if not IsBound(Q) then
        return;
    fi;

    getVertices := fail;
    if IsBoundGlobal("VerticesOfQuiver") then
        getVertices := ValueGlobal("VerticesOfQuiver");
    elif IsBoundGlobal("Vertices") then
        getVertices := ValueGlobal("Vertices");
    fi;

    getArrows := fail;
    if IsBoundGlobal("ArrowsOfQuiver") then
        getArrows := ValueGlobal("ArrowsOfQuiver");
    elif IsBoundGlobal("Arrows") then
        getArrows := ValueGlobal("Arrows");
    fi;

    AppendTo(fname, "\n# --- Quiver Q --- #\n");
    AppendTo(fname, "digraph Q {\n");
    vertices_list := [];
    if getVertices <> fail then
        vertices_list := getVertices(Q);
    else
        nvCall := CALL_WITH_CATCH(NumberOfVertices, [Q]);
        if nvCall[1] = true then
            nv := nvCall[2];
            if IsInt(nv) and nv > 0 then
                vertices_list := [1..nv];
            fi;
        fi;
    fi;
    if Length(vertices_list) = 0 and IsBoundGlobal("Q_arrows") and IsList(Q_arrows) then
        max_v := 0;
        for a in Q_arrows do
            if IsList(a) and Length(a) >= 2 then
                if a[1] > max_v then max_v := a[1]; fi;
                if a[2] > max_v then max_v := a[2]; fi;
            fi;
        od;
        if max_v > 0 then
            vertices_list := [1..max_v];
        fi;
    fi;
    for v in vertices_list do
        AppendTo(fname, "  ", String(v), " [label=\"", String(v), "\"];\n");
    od;

    arrows_fallback := [];
    if IsBoundGlobal("Q_arrows") and IsList(Q_arrows) then
        arrows_fallback := Q_arrows;
    elif getArrows <> fail then
        arrows_list := getArrows(Q);
        if IsList(arrows_list) then
            arrows_fallback := arrows_list;
        fi;
    fi;

    for a in arrows_fallback do
        if IsList(a) and Length(a) >= 2 then
            s := a[1];
            t := a[2];
            lbl := "";
            if Length(a) >= 3 then
                lbl := String(a[3]);
            else
                lbl := String(a);
            fi;
            AppendTo(fname, "  ", String(s), " -> ", String(t), " [label=\"", lbl, "\"];\n");
        fi;
    od;
    AppendTo(fname, "}\n");

    AppendTo(fname, "\n# --- Relations --- #\n");
    if IsBoundGlobal("rel_input_str") then
        rel_str := rel_input_str;
    elif IsBound(rel) then
        rel_str := String(rel);
    else
        rel_str := "[]";
    fi;
    AppendTo(fname, "rel := ", rel_str, ";\n");

    if IsBound(QuiverStructure) then
        AppendTo(fname, "QuiverStructure := \"", QuiverStructure, "\";\n");
    fi;
end;;

# ===== Step2.ipynb cell 8 =====
# Proj/Injective dimensions (write PDID to txt)
ComputeProjInjDims := function(verts, maxN)
    local idx, M, n, pd, id, pdCall, idCall, result;
    result := [];
    for idx in [1..Length(verts)] do
        M := verts[idx];
        pd := -1;
        id := -1;
        for n in [0..maxN] do
            pdCall := CALL_WITH_CATCH(ProjDimensionOfModule, [M, n]);
            if pdCall[1] = true and pdCall[2] <> false then
                pd := n;
                break;
            fi;
        od;
        for n in [0..maxN] do
            idCall := CALL_WITH_CATCH(InjDimensionOfModule, [M, n]);
            if idCall[1] = true and idCall[2] <> false then
                id := n;
                break;
            fi;
        od;
        Add(result, [idx, pd, id]);
    od;
    return result;
end;;

WriteProjInjDims := function(fname, verts, maxN)
    local pdid;
    pdid := ComputeProjInjDims(verts, maxN);
    AppendTo(fname, "PDID := ", pdid, ";\n");
end;;

WriteProjInjDimsFromCache := function(fname, pdid)
    AppendTo(fname, "PDID := ", pdid, ";\n");
end;;

# ===== Step2.ipynb cell 9 =====
# 画 irreducible morphism 的 diagram

DrawIrreducibleDiagram := function(A, N, arg)
    local
        # --- Input and module data ---
        fname, outDir, P, I, SI, V,
        # --- BFS core ---
        queue, verts, edges, depthMap, dead, outAdj,
        X0, Y, f, depth, irr, irrCall, current,
        uX, uY, newDepth,
        # --- Output ---
        out, e, u, v, i, label_str,
        projective_node_ids, injective_node_ids, p_mod, i_mod, pos,
        pdid_map,
        # --- Helper functions ---
        AddVertex, AddEdge, Enqueue, ProcessDeaths;

    # --- 1. I/O setup ---
    # Use current working directory so Binder/Jupyter can write output
    outDir := Directory(".");
    if IsBoundGlobal("output_log_path") and output_log_path <> fail then
        fname := output_log_path;
    elif Length(arg) = 0 then
        fname := Filename(outDir, "quiver_labeled.log");
    else
        fname := Filename(outDir, Concatenation(arg, ".log"));
    fi;

    P := IndecProjectiveModules(A);;
    I := IndecInjectiveModules(A);;
    SI := Filtered(I, X -> Dimension(X) = 1);;

    # --- 2. Init data structures ---
    queue := [];
    verts := [];
    edges := [];      # list of [u, v] integer-ID pairs; multiplicity by repetition
    depthMap := [];
    dead := [];
    outAdj := [];      # outAdj[u] = list of target vertex IDs (multiplicity by repetition)

    # --- Helper: add module to verts if absent, return its ID ---
    AddVertex := function(M)
        local posM;
        posM := PositionIsomorphic(verts, M);
        if posM = fail then
            Add(verts, M);
            posM := Length(verts);
        fi;
        return posM;
    end;

    # --- Helper: add permanent directed edge u -> v ---
    AddEdge := function(uS, uT)
        Add(edges, [uS, uT]);
        if not IsBound(outAdj[uS]) then outAdj[uS] := []; fi;
        Add(outAdj[uS], uT);
    end;

    # --- Helper: enqueue vertex at given depth (skip if beyond limit or dead) ---
    Enqueue := function(uV, d)
        if d >= N then return; fi;
        if IsBound(dead[uV]) and dead[uV] = true then return; fi;
        if not IsBound(depthMap[uV]) or d < depthMap[uV] then
            depthMap[uV] := d;
            Add(queue, rec(id := uV, depth := d));
        fi;
    end;

    # =========================================================================
    # ProcessDeaths: Cascading AR mesh relation
    #
    # The almost split sequence STARTING at M (M not injective):
    #   0 -> M -> E -> TrD(M) -> 0
    #
    # The middle term E = direct sum N_i^{m_i}. By AR theory:
    #   - IrrFrom(M) consists of maps M -> N_i (multiplicity m_i)
    #   - The same N_i map to TrD(M) with the same multiplicities m_i
    #
    # For each dead M with TrD(M) non-zero and not dead:
    #   Step 1: For each edge M->N (mult k) with no existing edge N->TrD(M),
    #           add k temporary arrows N -> TrD(M).
    #   Step 2: For each non-dead N with temp arrows, check using the
    #           AR sequence starting at N:  0 -> N -> F -> TrD(N) -> 0
    #             sum dim(all outgoing from N) = dim(N) + dim(TrD(N))
    #           If satisfied, promote temp arrows, kill N, and cascade from N.
    #
    # Depth control: stop cascading when targets reach the depth limit N.
    # =========================================================================
    ProcessDeaths := function(frontier)
        local nextFrontier, uM, M, trdCall, TrDM, uTrDM,
              succDistinct, uN, multMN, touched,
              temp_by_source, sum_dim, trdNCall, TrDN,
              ta, j, baseDepth;

        while Length(frontier) > 0 do
            temp_by_source := [];  # sparse list: temp_by_source[uN] = [[uTarget, mult], ...]
            touched := [];         # vertex IDs that received temp arrows

            # --- Step 1: Create temporary arrows N -> TrD(M) ---
            for uM in frontier do
                M := verts[uM];
                trdCall := CALL_WITH_CATCH(TrD, [M]);
                if trdCall[1] <> true then continue; fi;
                TrDM := trdCall[2];
                if IsInt(TrDM) or TrDM = 0 then continue; fi;

                uTrDM := AddVertex(TrDM);
                if IsBound(dead[uTrDM]) and dead[uTrDM] = true then continue; fi;

                # Edges from M
                if not IsBound(outAdj[uM]) then continue; fi;
                succDistinct := Set(outAdj[uM]);

                for uN in succDistinct do
                    # Skip dead vertices
                    if IsBound(dead[uN]) and dead[uN] = true then continue; fi;

                    multMN := Number(outAdj[uM], x -> x = uN);
                    if multMN = 0 then continue; fi;

                    # Skip if permanent edge N -> TrD(M) already exists
                    if IsBound(outAdj[uN]) and Number(outAdj[uN], x -> x = uTrDM) > 0 then
                        continue;
                    fi;

                    if not IsBound(temp_by_source[uN]) then
                        temp_by_source[uN] := [];
                    fi;
                    Add(temp_by_source[uN], [uTrDM, multMN]);
                    if not (uN in touched) then Add(touched, uN); fi;
                od;
            od;

            if Length(touched) = 0 then break; fi;

            # --- Step 2: Check AR dim formula and promote ---
            nextFrontier := [];
            for uN in touched do
                if IsBound(dead[uN]) and dead[uN] = true then continue; fi;
                if not IsBound(temp_by_source[uN]) then continue; fi;

                # Sum dim of temp arrow targets (with multiplicity)
                sum_dim := 0;
                for ta in temp_by_source[uN] do
                    sum_dim := sum_dim + ta[2] * Dimension(verts[ta[1]]);
                od;

                # Add dim of existing permanent outgoing edges from N
                if IsBound(outAdj[uN]) then
                    for j in outAdj[uN] do
                        sum_dim := sum_dim + Dimension(verts[j]);
                    od;
                fi;

                # Compute TrD(N) for the almost split sequence starting at N:
                #   0 -> N -> (middle term) -> TrD(N) -> 0
                #   dim(middle term) = dim(N) + dim(TrD(N))
                trdNCall := CALL_WITH_CATCH(TrD, [verts[uN]]);
                if trdNCall[1] <> true then continue; fi;
                TrDN := trdNCall[2];
                if IsInt(TrDN) or TrDN = 0 then continue; fi;

                # Check: sum dim(all outgoing targets of N) = dim(N) + dim(TrD(N))
                if sum_dim = Dimension(verts[uN]) + Dimension(TrDN) then
                    # Compute depth for targets
                    if IsBound(depthMap[uN]) then
                        baseDepth := depthMap[uN] + 1;
                    else
                        baseDepth := 1;
                    fi;

                    # Promote all temp arrows from N to permanent edges
                    for ta in temp_by_source[uN] do
                        for j in [1..ta[2]] do
                            AddEdge(uN, ta[1]);
                        od;
                        Enqueue(ta[1], baseDepth);
                    od;

                    # Kill N: all IrrFrom(N) are now determined
                    dead[uN] := true;

                    # Only cascade further if targets are within depth limit
                    if baseDepth < N then
                        Add(nextFrontier, uN);
                    fi;
                fi;
            od;

            frontier := nextFrontier;
        od;
    end;

    # --- 2.1 Init queue: start from indec projectives ---
    for X0 in P do
        uX := AddVertex(X0);
        Enqueue(uX, 0);
    od;

    # --- 3. BFS main loop ---
    while Length(queue) > 0 do
        current := queue[1];
        Remove(queue, 1);

        uX := current.id;
        depth := current.depth;

        # Skip if already dead (e.g. killed by cascade)
        if IsBound(dead[uX]) and dead[uX] = true then continue; fi;

        X0 := verts[uX];

        # Boundary: depth limit or simple injective
        if depth >= N or IsIsomorphicToAny(X0, SI) then
            dead[uX] := true;
            continue;
        fi;

        # Compute IrrFrom(X0)
        if IsBoundGlobal("guess") and ValueGlobal("guess") = true then
            irrCall := CALL_WITH_CATCH(IrrFromGuess, [X0]);
        else
            irrCall := CALL_WITH_CATCH(IrrFrom, [X0]);
        fi;

        if irrCall[1] = false then
            dead[uX] := true;
            continue;
        fi;
        irr := irrCall[2];
        if not IsList(irr) or Length(irr) = 0 then
            dead[uX] := true;
            continue;
        fi;

        # Record IrrFrom edges and enqueue targets
        for f in irr do
            if not IsBound(f) then continue; fi;
            Y := Range(f);
            uY := AddVertex(Y);
            AddEdge(uX, uY);
            Enqueue(uY, depth + 1);
        od;

        # Mark X0 as dead (IrrFrom fully computed)
        dead[uX] := true;

        # Cascade mesh relation from this death
        ProcessDeaths([uX]);

        Print("Found ",Length(verts)," vertices and ",Length(edges)," edges so far (just processed vertex ", uX, " at depth ", depth, ")\n");
    od;

    # --- 4. Output TXT file ---
    out := OutputTextFile(fname, false);
    PrintTo(out, "digraph Quiver {\n");

    # Compute pd/id for node labels
    pdid_map := [];
    for e in ComputeProjInjDims(verts, 6) do
        if IsList(e) and Length(e) >= 3 then
            pdid_map[e[1]] := e;
        fi;
    od;

    for i in [1..Length(verts)] do
        label_str := String(DimensionVector(verts[i]));
        if IsBound(pdid_map[i]) and IsList(pdid_map[i]) and Length(pdid_map[i]) >= 3 then
            label_str := Concatenation("pd=", String(pdid_map[i][2]), ", id=", String(pdid_map[i][3]));
        fi;
        PrintTo(out, "  ", String(i), " [label=\"", label_str, "\"];");
        PrintTo(out, "\n");
    od;

    # Print edges (multiplicity preserved by repeated lines)
    for e in edges do
        u := e[1]; v := e[2];
        PrintTo(out, "  ", String(u), " -> ", String(v), ";\n");
    od;

    # --- 5. Analysis footer ---
    projective_node_ids := [];
    for p_mod in P do
        pos := PositionIsomorphic(verts, p_mod);
        if pos <> fail then Add(projective_node_ids, pos); fi;
    od;

    injective_node_ids := [];
    for i_mod in I do
        pos := PositionIsomorphic(verts, i_mod);
        if pos <> fail then Add(injective_node_ids, pos); fi;
    od;

    Sort(projective_node_ids);
    Sort(injective_node_ids);
    PrintTo(out, "}\n");

    PrintTo(out, "\n# --- AR-Quiver Analysis --- #\n");
    PrintTo(out, "Projective modules found (Node IDs): ", projective_node_ids, "\n");
    PrintTo(out, "Injective modules found (Node IDs):  ", injective_node_ids, "\n");
    CloseStream(out);;

    V := verts;;
    return rec(
        fname := fname,
        verts := verts,
        projective_node_ids := projective_node_ids,
        injective_node_ids := injective_node_ids,
        P := P
    );
end;

DrawIrreducibleDiagramHybrid := function(A, N, arg)
    local fname, outDir, P, I, SI, queue, verts, edges, depthMap, outAdj,
        expanded, pendingMeshEdges, meshSeen, irr_call_count, mesh_added_count,
        X0, Y, f, current, uX, uY, depth, irr, irrCall, out, e, u, v, i,
        label_str, projective_node_ids, injective_node_ids, p_mod, i_mod, pos,
        pdid_map, AddVertex, AddEdge, Enqueue, EdgeKey, AddMeshFromEdge,
        CloseMesh, ExpandByIrr;

    outDir := Directory(".");
    if IsBoundGlobal("output_log_path") and output_log_path <> fail then
        fname := output_log_path;
    elif Length(arg) = 0 then
        fname := Filename(outDir, "quiver_labeled.log");
    else
        fname := Filename(outDir, Concatenation(arg, ".log"));
    fi;

    P := IndecProjectiveModules(A);;
    I := IndecInjectiveModules(A);;
    SI := Filtered(I, X -> Dimension(X) = 1);;

    queue := [];
    verts := [];
    edges := [];
    depthMap := [];
    outAdj := [];
    expanded := [];
    pendingMeshEdges := [];
    meshSeen := [];
    irr_call_count := 0;
    mesh_added_count := 0;

    AddVertex := function(M)
        local posM;
        posM := PositionIsomorphic(verts, M);
        if posM = fail then
            Add(verts, M);
            posM := Length(verts);
        fi;
        return posM;
    end;

    EdgeKey := function(uS, uT)
        return Concatenation(String(uS), "->", String(uT));
    end;

    AddEdge := function(uS, uT)
        Add(edges, [uS, uT]);
        if not IsBound(outAdj[uS]) then outAdj[uS] := []; fi;
        Add(outAdj[uS], uT);
        Add(pendingMeshEdges, [uS, uT]);
    end;

    Enqueue := function(uV, d)
        if d > N then return; fi;
        if not IsBound(depthMap[uV]) or d < depthMap[uV] then
            depthMap[uV] := d;
            if d < N then
                Add(queue, rec(id := uV, depth := d));
            fi;
        fi;
    end;

    AddMeshFromEdge := function(uS, uT)
        local key, trdCall, trdM, uTrd, newDepth;
        key := EdgeKey(uS, uT);
        if key in meshSeen then
            return false;
        fi;
        Add(meshSeen, key);

        trdCall := CALL_WITH_CATCH(TrD, [verts[uS]]);
        if trdCall[1] <> true then
            return false;
        fi;
        trdM := trdCall[2];
        if IsInt(trdM) or trdM = 0 then
            return false;
        fi;

        uTrd := AddVertex(trdM);
        if IsBound(outAdj[uT]) and Number(outAdj[uT], x -> x = uTrd) > 0 then
            return false;
        fi;

        if IsBound(depthMap[uT]) then
            newDepth := depthMap[uT] + 1;
        elif IsBound(depthMap[uS]) then
            newDepth := depthMap[uS] + 2;
        else
            newDepth := N + 1;
        fi;
        if newDepth > N then
            return false;
        fi;

        AddEdge(uT, uTrd);
        Enqueue(uTrd, newDepth);
        mesh_added_count := mesh_added_count + 1;
        return true;
    end;

    CloseMesh := function()
        local edge;
        while Length(pendingMeshEdges) > 0 do
            edge := pendingMeshEdges[1];
            Remove(pendingMeshEdges, 1);
            AddMeshFromEdge(edge[1], edge[2]);
        od;
    end;

    ExpandByIrr := function(uV, d)
        local M, irrCallLocal, irrLocal, fLocal, YLocal, uYLocal;
        if IsBound(expanded[uV]) and expanded[uV] = true then
            return;
        fi;
        M := verts[uV];
        if d >= N or IsIsomorphicToAny(M, SI) then
            expanded[uV] := true;
            return;
        fi;
        if IsBoundGlobal("guess") and ValueGlobal("guess") = true then
            irrCallLocal := CALL_WITH_CATCH(IrrFromGuess, [M]);
        else
            irrCallLocal := CALL_WITH_CATCH(IrrFrom, [M]);
        fi;
        irr_call_count := irr_call_count + 1;
        if irrCallLocal[1] = false then
            expanded[uV] := true;
            return;
        fi;
        irrLocal := irrCallLocal[2];
        if not IsList(irrLocal) then
            expanded[uV] := true;
            return;
        fi;
        for fLocal in irrLocal do
            if not IsBound(fLocal) then continue; fi;
            YLocal := Range(fLocal);
            uYLocal := AddVertex(YLocal);
            AddEdge(uV, uYLocal);
            Enqueue(uYLocal, d + 1);
        od;
        expanded[uV] := true;
    end;

    for X0 in P do
        uX := AddVertex(X0);
        Enqueue(uX, 0);
    od;

    while Length(queue) > 0 do
        current := queue[1];
        Remove(queue, 1);
        uX := current.id;
        depth := current.depth;
        if IsBound(expanded[uX]) and expanded[uX] = true then
            CloseMesh();
            continue;
        fi;
        ExpandByIrr(uX, depth);
        CloseMesh();
        Print("Hybrid AR: ", Length(verts), " vertices, ", Length(edges), " edges, IrrFrom calls=", irr_call_count,
              ", mesh edges=", mesh_added_count, " (processed vertex ", uX, " at depth ", depth, ")\n");
    od;

    out := OutputTextFile(fname, false);
    PrintTo(out, "digraph Quiver {\n");

    pdid_map := [];
    for e in ComputeProjInjDims(verts, 6) do
        if IsList(e) and Length(e) >= 3 then
            pdid_map[e[1]] := e;
        fi;
    od;

    for i in [1..Length(verts)] do
        label_str := String(DimensionVector(verts[i]));
        if IsBound(pdid_map[i]) and IsList(pdid_map[i]) and Length(pdid_map[i]) >= 3 then
            label_str := Concatenation("pd=", String(pdid_map[i][2]), ", id=", String(pdid_map[i][3]));
        fi;
        PrintTo(out, "  ", String(i), " [label=\"", label_str, "\"];\n");
    od;

    for e in edges do
        u := e[1];
        v := e[2];
        PrintTo(out, "  ", String(u), " -> ", String(v), ";\n");
    od;

    projective_node_ids := [];
    for p_mod in P do
        pos := PositionIsomorphic(verts, p_mod);
        if pos <> fail then Add(projective_node_ids, pos); fi;
    od;

    injective_node_ids := [];
    for i_mod in I do
        pos := PositionIsomorphic(verts, i_mod);
        if pos <> fail then Add(injective_node_ids, pos); fi;
    od;

    Sort(projective_node_ids);
    Sort(injective_node_ids);
    PrintTo(out, "}\n");
    PrintTo(out, "\n# --- AR-Quiver Analysis --- #\n");
    PrintTo(out, "Projective modules found (Node IDs): ", projective_node_ids, "\n");
    PrintTo(out, "Injective modules found (Node IDs):  ", injective_node_ids, "\n");
    PrintTo(out, "AR strategy: hybrid\n");
    PrintTo(out, "IrrFrom calls: ", irr_call_count, "\n");
    PrintTo(out, "Mesh edges added: ", mesh_added_count, "\n");
    CloseStream(out);;

    V := verts;;
    return rec(
        fname := fname,
        verts := verts,
        projective_node_ids := projective_node_ids,
        injective_node_ids := injective_node_ids,
        P := P
    );
end;

# ===== Step2.ipynb cell 10 =====
# 找 syzygy diagram

WriteSyzygySummand := function(fname, verts, projective_node_ids)
    local nonproj_node_ids, source_node_ids, target_node_ids, label_str, idx, Nidx, syzCall, M, dsCall;

    nonproj_node_ids := Filtered([1..Length(verts)], k -> not (k in projective_node_ids));
    source_node_ids := [1..Length(verts)];
    target_node_ids := nonproj_node_ids;

    AppendTo(fname,"\n\ndigraph SyzygySummand {\n");
    for idx in Set(Concatenation(source_node_ids, target_node_ids)) do
        label_str := String(DimensionVector(verts[idx]));
        AppendTo(fname,"  ", String(idx), " [label=\"", label_str, "\"];\n");
    od;

    for Nidx in target_node_ids do
        syzCall := CALL_WITH_CATCH(1stSyzygy, [verts[Nidx]]);
        if syzCall[1] <> true then
            continue;
        fi;
        if IsInt(syzCall[2]) and syzCall[2] = 0 then
            continue;
        fi;

        for idx in source_node_ids do
            M := verts[idx];
            dsCall := CALL_WITH_CATCH(IsDirectSummand, [M, syzCall[2]]);
            if dsCall[1] = true and dsCall[2] = true then
                AppendTo(fname,"  ", String(idx), " -> ", String(Nidx), ";\n");
            fi;
        od;
    od;

    AppendTo(fname,"}\n");
end;;

# ===== Step2.ipynb cell 11 =====
# 找 torsionless/reflexive 对象

CollectTorsionlessReflexive := function(verts, projective_node_ids, P)
    local torsionless_node_ids, reflexive_node_ids, M, idx, phiCall, phi, injCall, isoCall;

    torsionless_node_ids := [];
    reflexive_node_ids := [];

    for idx in [1..Length(verts)] do
        M := verts[idx];
        if M in P then
            continue;
        fi;
        phiCall := CALL_WITH_CATCH(FromIdentityToDoubleStarHomomorphism, [M]);
        if phiCall[1] <> true then
            continue;
        fi;
        phi := phiCall[2];
        injCall := CALL_WITH_CATCH(IsInjective, [phi]);
        if injCall[1] = true and injCall[2] = true then
            Add(torsionless_node_ids, idx);
            isoCall := CALL_WITH_CATCH(IsIsomorphism, [phi]);
            if isoCall[1] = true and isoCall[2] = true then
                Add(reflexive_node_ids, idx);
            fi;
        fi;
    od;

    # Exclude projective vertices from torsionless/reflexive lists
    torsionless_node_ids := Filtered(torsionless_node_ids, k -> not (k in projective_node_ids));
    reflexive_node_ids := Filtered(reflexive_node_ids, k -> not (k in projective_node_ids));

    Sort(torsionless_node_ids);
    Sort(reflexive_node_ids);

    return [torsionless_node_ids, reflexive_node_ids];
end;;

WriteTorsionlessReflexive := function(fname, torsionless_node_ids, reflexive_node_ids)
    AppendTo(fname,"Torsionless modules found (Node IDs): ", torsionless_node_ids, "\n");
    AppendTo(fname,"Reflexive modules found (Node IDs):  ", reflexive_node_ids, "\n");
end;;

# ===== Cached Hom/Ext/tau computations =====
HomObjectDimension := function(homObj)
    local lenCall;
    if IsInt(homObj) and homObj = 0 then
        return 0;
    fi;
    lenCall := CALL_WITH_CATCH(Length, [homObj]);
    if lenCall[1] = true then
        return lenCall[2];
    fi;
    return 0;
end;;

Ext1ObjectDimension := function(extObj)
    local ext1, lenCall;
    if IsList(extObj) and Length(extObj) >= 2 then
        ext1 := extObj[2];
    else
        ext1 := 0;
    fi;
    if IsInt(ext1) and ext1 = 0 then
        return 0;
    fi;
    lenCall := CALL_WITH_CATCH(Length, [ext1]);
    if lenCall[1] = true then
        return lenCall[2];
    fi;
    return 0;
end;;

ComputeDimensionVectors := function(verts)
    return List(verts, DimensionVector);
end;;

ComputeHomDimMatrix := function(verts)
    local hom_dim, i, j, homCall;
    hom_dim := [];
    for i in [1..Length(verts)] do
        hom_dim[i] := [];
        for j in [1..Length(verts)] do
            homCall := CALL_WITH_CATCH(HomOverAlgebra, [verts[i], verts[j]]);
            if homCall[1] = true then
                hom_dim[i][j] := HomObjectDimension(homCall[2]);
            else
                hom_dim[i][j] := 0;
            fi;
        od;
    od;
    return hom_dim;
end;;

ComputeExtDimMatrix := function(verts)
    local ext_dim, i, j, extCall;
    ext_dim := [];
    for i in [1..Length(verts)] do
        ext_dim[i] := [];
        for j in [1..Length(verts)] do
            extCall := CALL_WITH_CATCH(ExtOverAlgebra, [verts[i], verts[j]]);
            if extCall[1] = true then
                ext_dim[i][j] := Ext1ObjectDimension(extCall[2]);
            else
                ext_dim[i][j] := 0;
            fi;
        od;
    od;
    return ext_dim;
end;;

ComputeTauMap := function(verts)
    local tau_map, idx, dtrCall, dtrM, posN;
    tau_map := [];
    for idx in [1..Length(verts)] do
        tau_map[idx] := fail;
        dtrCall := CALL_WITH_CATCH(DTr, [verts[idx]]);
        if dtrCall[1] <> true then
            continue;
        fi;
        dtrM := dtrCall[2];
        if IsInt(dtrM) and dtrM = 0 then
            continue;
        fi;
        posN := PositionIsomorphic(verts, dtrM);
        if posN <> fail then
            tau_map[idx] := posN;
        fi;
    od;
    return tau_map;
end;;

WriteHomDimQuiver := function(fname, verts, dim_vectors, hom_dim)
    local i, j, label_str, n;
    AppendTo(fname, "\n\ndigraph HomDim {\n");
    for i in [1..Length(verts)] do
        label_str := String(dim_vectors[i]);
        AppendTo(fname, "  ", String(i), " [label=\"", label_str, "\"];\n");
    od;
    for i in [1..Length(verts)] do
        for j in [1..Length(verts)] do
            n := hom_dim[i][j];
            if n > 0 then
                AppendTo(fname, "  ", String(i), " -> ", String(j), " [label=\"", String(n), "\"];\n");
            fi;
        od;
    od;
    AppendTo(fname, "}\n");
end;;

WriteExtDimQuiver := function(fname, verts, dim_vectors, ext_dim)
    local i, j, label_str, n;
    AppendTo(fname, "\n\ndigraph ExtDim {\n");
    for i in [1..Length(verts)] do
        label_str := String(dim_vectors[i]);
        AppendTo(fname, "  ", String(i), " [label=\"", label_str, "\"];\n");
    od;
    for i in [1..Length(verts)] do
        for j in [1..Length(verts)] do
            n := ext_dim[i][j];
            if n > 0 then
                AppendTo(fname, "  ", String(i), " -> ", String(j), " [label=\"", String(n), "\"];\n");
            fi;
        od;
    od;
    AppendTo(fname, "}\n");
end;;

ComputeSyzygyEdges := function(verts, projective_node_ids)
    local nonproj_node_ids, source_node_ids, target_node_ids, Nidx, syzCall, M, dsCall, idx, edges;
    edges := [];
    nonproj_node_ids := Filtered([1..Length(verts)], k -> not (k in projective_node_ids));
    source_node_ids := [1..Length(verts)];
    target_node_ids := nonproj_node_ids;
    for Nidx in target_node_ids do
        syzCall := CALL_WITH_CATCH(1stSyzygy, [verts[Nidx]]);
        if syzCall[1] <> true then
            continue;
        fi;
        if IsInt(syzCall[2]) and syzCall[2] = 0 then
            continue;
        fi;
        for idx in source_node_ids do
            M := verts[idx];
            dsCall := CALL_WITH_CATCH(IsDirectSummand, [M, syzCall[2]]);
            if dsCall[1] = true and dsCall[2] = true then
                Add(edges, [idx, Nidx]);
            fi;
        od;
    od;
    return edges;
end;;


LexLessList := function(a, b)
    local i, m;
    m := Minimum(Length(a), Length(b));
    for i in [1..m] do
        if a[i] < b[i] then return true; fi;
        if a[i] > b[i] then return false; fi;
    od;
    return Length(a) < Length(b);
end;;

LexKeyOfPair := function(left, right)
    return [left, right];
end;;

SortRecordsByLeftRight := function(records)
    SortBy(records, r -> [r.left, r.right]);
end;;

ExtEdgesFromMatrix := function(ext_dim)
    local edges, i, j;
    edges := [];
    for i in [1..Length(ext_dim)] do
        for j in [1..Length(ext_dim[i])] do
            if ext_dim[i][j] > 0 then
                Add(edges, [i, j]);
            fi;
        od;
    od;
    return edges;
end;;

FindTiltingObjects := function(fname, verts, projective_node_ids, hom_dim, ext_dim)
    local syzEdges, extEdges, PT, adj, edge, u, v, nodes, solutions, current, i, n, reqSize,
        backtrack, result_lines, annCall, annList, deg, idx, canUse, other,
        nextHasNonProj, nextAnnInter, nextAnnOk, L_sorted, F_list, T_list,
        idxX, idxY, okHom, ft_union;

    syzEdges := ComputeSyzygyEdges(verts, projective_node_ids);
    extEdges := ExtEdgesFromMatrix(ext_dim);

    PT := ShallowCopy(projective_node_ids);
    for edge in syzEdges do
        u := edge[1];
        v := edge[2];
        if u in projective_node_ids and not (v in PT) then
            Add(PT, v);
        fi;
        if v in projective_node_ids and not (u in PT) then
            Add(PT, u);
        fi;
    od;
    Sort(PT);

    adj := [];
    for i in [1..Length(verts)] do
        adj[i] := [];
    od;
    for edge in extEdges do
        u := edge[1];
        v := edge[2];
        if not (v in adj[u]) then Add(adj[u], v); fi;
        if not (u in adj[v]) then Add(adj[v], u); fi;
    od;

    deg := [];
    for i in PT do
        deg[i] := Length(adj[i]);
    od;
    nodes := ShallowCopy(PT);
    SortBy(nodes, i -> -deg[i]);
    n := Length(nodes);
    reqSize := n_verts;

    solutions := [];
    current := [];

    backtrack := function(pos, hasNonProj, annInter, annOk)
        local idx, canUse, other, nextHasNonProj, nextAnnInter, nextAnnOk;
        if pos > n then
            if Length(current) = 0 then return; fi;
            if Length(current) <> reqSize then return; fi;
            if not hasNonProj then return; fi;
            if not annOk then return; fi;
            Add(solutions, ShallowCopy(current));
            return;
        fi;

        idx := nodes[pos];
        canUse := true;
        for other in current do
            if idx in adj[other] or other in adj[idx] then
                canUse := false;
                break;
            fi;
        od;
        if canUse and not (idx in adj[idx]) then
            nextHasNonProj := hasNonProj or not (idx in projective_node_ids);
            if annOk then
                nextAnnInter := annInter;
                nextAnnOk := true;
            else
                annCall := CALL_WITH_CATCH(AnnihilatorOfModule, [verts[idx]]);
                if annCall[1] = true and IsList(annCall[2]) then
                    annList := annCall[2];
                    if annInter = fail then
                        nextAnnInter := annList;
                    else
                        nextAnnInter := Intersection(annInter, annList);
                    fi;
                    nextAnnOk := Length(nextAnnInter) = 0;
                else
                    nextAnnInter := annInter;
                    nextAnnOk := false;
                fi;
            fi;
            Add(current, idx);
            backtrack(pos + 1, nextHasNonProj, nextAnnInter, nextAnnOk);
            Remove(current, Length(current));
        fi;
        backtrack(pos + 1, hasNonProj, annInter, annOk);
    end;;

    backtrack(1, false, fail, false);
    Sort(solutions);

    AppendTo(fname, "\n# --- TiltingModule --- #\n");
    if Length(solutions) = 0 then
        AppendTo(fname, "(none)\n");
        return;
    fi;

    for result_lines in solutions do
        L_sorted := ShallowCopy(result_lines);
        Sort(L_sorted);

        T_list := ShallowCopy(L_sorted);

        F_list := [];
        for idxY in [1..Length(verts)] do
            okHom := true;
            for idxX in T_list do
                if hom_dim[idxX][idxY] <> 0 then
                    okHom := false;
                    break;
                fi;
            od;
            if okHom then
                Add(F_list, idxY);
            fi;
        od;
        Sort(F_list);

        T_list := [];
        for idxX in [1..Length(verts)] do
            okHom := true;
            for idxY in F_list do
                if hom_dim[idxX][idxY] <> 0 then
                    okHom := false;
                    break;
                fi;
            od;
            if okHom then
                Add(T_list, idxX);
            fi;
        od;
        Sort(T_list);

        AppendTo(fname, "L := ", L_sorted, "\n");
        AppendTo(fname, "F := ", F_list, "\n");
        AppendTo(fname, "T := ", T_list, "\n");

        ft_union := Set(Concatenation(F_list, T_list));
        if Length(ft_union) = Length(verts) then
            AppendTo(fname, "Split\n");
        fi;
    od;
end;;


CollectGorensteinProjectiveInjective := function(verts, projective_node_ids, injective_node_ids, torsionless_node_ids, reflexive_node_ids, pdid, ext_dim)
    local gp_ids, gi_ids, idx, row, pd, idim, ok, p, inj;

    gp_ids := [];
    gi_ids := [];

    for row in pdid do
        if not (IsList(row) and Length(row) >= 3) then
            continue;
        fi;
        idx := row[1];
        pd := row[2];
        idim := row[3];

        if not (idx in projective_node_ids) and pd = -1 and idx in torsionless_node_ids and idx in reflexive_node_ids then
            ok := true;
            for p in projective_node_ids do
                if ext_dim[idx][p] <> 0 then
                    ok := false;
                    break;
                fi;
            od;
            if ok then
                Add(gp_ids, idx);
            fi;
        fi;

        if not (idx in injective_node_ids) and idim = -1 then
            ok := true;
            for inj in injective_node_ids do
                if ext_dim[inj][idx] <> 0 then
                    ok := false;
                    break;
                fi;
            od;
            if ok then
                Add(gi_ids, idx);
            fi;
        fi;
    od;

    Sort(gp_ids);
    Sort(gi_ids);
    return [gp_ids, gi_ids];
end;;

WriteGorensteinProjectiveInjective := function(fname, gp_ids, gi_ids)
    AppendTo(fname, "Gorenstein projective modules found (Node IDs): ", gp_ids, "\n");
    AppendTo(fname, "Gorenstein injective modules found (Node IDs):  ", gi_ids, "\n");
end;;

CotorsionRightOrthogonal := function(ext_dim, left_set)
    local right, j, i, ok;
    right := [];
    for j in [1..Length(ext_dim)] do
        ok := true;
        for i in left_set do
            if ext_dim[i][j] <> 0 then ok := false; break; fi;
        od;
        if ok then Add(right, j); fi;
    od;
    return right;
end;;

CotorsionLeftOrthogonal := function(ext_dim, right_set)
    local left, i, j, ok;
    left := [];
    for i in [1..Length(ext_dim)] do
        ok := true;
        for j in right_set do
            if ext_dim[i][j] <> 0 then ok := false; break; fi;
        od;
        if ok then Add(left, i); fi;
    od;
    return left;
end;;

TorsionFreeClass := function(hom_dim, torsion_set)
    local free, j, i, ok;
    free := [];
    for j in [1..Length(hom_dim)] do
        ok := true;
        for i in torsion_set do
            if hom_dim[i][j] <> 0 then ok := false; break; fi;
        od;
        if ok then Add(free, j); fi;
    od;
    return free;
end;;

TorsionClassFromFree := function(hom_dim, free_set)
    local torsion, i, j, ok;
    torsion := [];
    for i in [1..Length(hom_dim)] do
        ok := true;
        for j in free_set do
            if hom_dim[i][j] <> 0 then ok := false; break; fi;
        od;
        if ok then Add(torsion, i); fi;
    od;
    return torsion;
end;;

IsHereditaryCotorsionPair := function(left_set, syz_edges)
    local edge;
    for edge in syz_edges do
        if edge[2] in left_set and not (edge[1] in left_set) then
            return false;
        fi;
    od;
    return true;
end;;

EnumerateFixedPairs := function(n, rightFromLeft, leftFromRight, extra)
    local pairs, seen, current, Enumerate, right, left, key, pair;
    pairs := [];
    seen := [];
    current := [];

    Enumerate := function(pos)
        if pos > n then
            right := rightFromLeft(current, extra);
            left := leftFromRight(right, extra);
            Sort(left);
            Sort(right);
            if Set(left) = Set(current) then
                key := Concatenation(String(left), "|", String(right));
                if not (key in seen) then
                    Add(seen, key);
                    Add(pairs, rec(left := ShallowCopy(left), right := ShallowCopy(right)));
                fi;
            fi;
            return;
        fi;
        Enumerate(pos + 1);
        Add(current, pos);
        Enumerate(pos + 1);
        Remove(current, Length(current));
    end;;

    Enumerate(1);
    SortBy(pairs, r -> [r.left, r.right]);
    return pairs;
end;;

WriteTorsionPairs := function(fname, verts, hom_dim)
    local n, maxN, pairs, pair;
    n := Length(verts);
    maxN := 20;
    AppendTo(fname, "\n# --- TorsionPairTable --- #\n");
    AppendTo(fname, "# columns: T, F\n");
    if n > maxN then
        AppendTo(fname, "Skipped: too many vertices for exhaustive finite-subquiver search (", n, " > ", maxN, ").\n");
        return;
    fi;
    pairs := EnumerateFixedPairs(
        n,
        function(left, extra) return TorsionFreeClass(extra, left); end,
        function(right, extra) return TorsionClassFromFree(extra, right); end,
        hom_dim
    );
    for pair in pairs do
        AppendTo(fname, "T := ", pair.left, " | F := ", pair.right, "\n");
    od;
    AppendTo(fname, "TorsionPairCount := ", Length(pairs), ";\n");
end;;

WriteCotorsionPairs := function(fname, verts, ext_dim, syz_edges)
    local n, maxN, pairs, pair, hereditary;
    n := Length(verts);
    maxN := 20;
    AppendTo(fname, "\n# --- CotorsionPairTable --- #\n");
    AppendTo(fname, "# columns: L, R, Hereditary\n");
    if n > maxN then
        AppendTo(fname, "Skipped: too many vertices for exhaustive finite-subquiver search (", n, " > ", maxN, ").\n");
        return;
    fi;
    pairs := EnumerateFixedPairs(
        n,
        function(left, extra) return CotorsionRightOrthogonal(extra, left); end,
        function(right, extra) return CotorsionLeftOrthogonal(extra, right); end,
        ext_dim
    );
    for pair in pairs do
        hereditary := IsHereditaryCotorsionPair(pair.left, syz_edges);
        AppendTo(fname, "L := ", pair.left, " | R := ", pair.right, " | Hereditary := ", hereditary, "\n");
    od;
    AppendTo(fname, "CotorsionPairCount := ", Length(pairs), ";\n");
end;;

WriteTranslationQuiver := function(fname, verts, dim_vectors, tau_map)
    local idx, label_str, posN;
    AppendTo(fname, "\n\ndigraph TranslationQuiver {\n");
    for idx in [1..Length(verts)] do
        label_str := String(dim_vectors[idx]);
        AppendTo(fname, "  ", String(idx), " [label=\"", label_str, "\"];\n");
    od;
    for idx in [1..Length(verts)] do
        posN := tau_map[idx];
        if posN <> fail then
            AppendTo(fname, "  ", String(idx), " -> ", String(posN), ";\n");
        fi;
    od;
    AppendTo(fname, "}\n\n");
end;;

GenerateQuiverData := function(A, N, arg)
    local res, tr_list, torsionless_node_ids, reflexive_node_ids,
        dim_vectors, hom_dim, ext_dim, tau_map, pdid, syz_edges, gi_gp;

    if IsBoundGlobal("ar_strategy") and ar_strategy = "direct" then
        res := DrawIrreducibleDiagram(A, N, arg);
    else
        res := DrawIrreducibleDiagramHybrid(A, N, arg);
    fi;

    dim_vectors := ComputeDimensionVectors(res.verts);
    tau_map := ComputeTauMap(res.verts);
    hom_dim := ComputeHomDimMatrix(res.verts);
    ext_dim := ComputeExtDimMatrix(res.verts);
    syz_edges := ComputeSyzygyEdges(res.verts, res.projective_node_ids);
    pdid := ComputeProjInjDims(res.verts, 6);

    WriteQuiverAndRelations(res.fname, Q, rel);
    WriteSyzygySummand(res.fname, res.verts, res.projective_node_ids);
    WriteTranslationQuiver(res.fname, res.verts, dim_vectors, tau_map);

    tr_list := CollectTorsionlessReflexive(res.verts, res.projective_node_ids, res.P);
    torsionless_node_ids := tr_list[1];
    reflexive_node_ids := tr_list[2];
    WriteTorsionlessReflexive(res.fname, torsionless_node_ids, reflexive_node_ids);

    gi_gp := CollectGorensteinProjectiveInjective(
        res.verts,
        res.projective_node_ids,
        res.injective_node_ids,
        torsionless_node_ids,
        reflexive_node_ids,
        pdid,
        ext_dim
    );
    WriteGorensteinProjectiveInjective(res.fname, gi_gp[1], gi_gp[2]);

    WriteHomDimQuiver(res.fname, res.verts, dim_vectors, hom_dim);
    WriteExtDimQuiver(res.fname, res.verts, dim_vectors, ext_dim);

    if not IsBoundGlobal("compute_tilting") or compute_tilting = true then
        FindTiltingObjects(res.fname, res.verts, res.projective_node_ids, hom_dim, ext_dim);
    fi;

    WriteTorsionPairs(res.fname, res.verts, hom_dim);
    WriteCotorsionPairs(res.fname, res.verts, ext_dim, syz_edges);

    WriteProjInjDimsFromCache(res.fname, pdid);

    Print("TXT file successfully written to ", res.fname, "\n");
end;;

GenerateQuiverDOT := GenerateQuiverData;;

RunARQuiverComputation := function()
    GenerateQuiverData(A, run_depth, output_name);
end;;
