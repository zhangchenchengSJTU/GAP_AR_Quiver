CleanStep1String := function(s)
    local t;
    t := Filtered(s, c -> c <> '\r' and c <> '\t');
    t := ReplacedString(t, "{", "");
    t := ReplacedString(t, "}", "");
    t := ReplacedString(t, "\\\\", "");
    t := ReplacedString(t, "\\&", "");
    while Length(t) > 0 and t[1] = ' ' do
        t := t{[2..Length(t)]};
    od;
    while Length(t) > 0 and t[Length(t)] = ' ' do
        t := t{[1..Length(t)-1]};
    od;
    return t;
end;;

NormalizeStep1Name := function(s)
    local t;
    t := CleanStep1String(s);
    t := ReplacedString(t, "\\alpha", "alpha");
    t := ReplacedString(t, "\\beta", "beta");
    t := ReplacedString(t, "\\gamma", "gamma");
    t := ReplacedString(t, "\\delta", "delta");
    t := ReplacedString(t, "\\epsilon", "epsilon");
    t := ReplacedString(t, "\\varepsilon", "epsilon");
    t := ReplacedString(t, "\\zeta", "zeta");
    t := ReplacedString(t, "\\eta", "eta");
    t := ReplacedString(t, "\\theta", "theta");
    t := ReplacedString(t, "\\vartheta", "theta");
    t := ReplacedString(t, "\\iota", "iota");
    t := ReplacedString(t, "\\kappa", "kappa");
    t := ReplacedString(t, "\\lambda", "lambda");
    t := ReplacedString(t, "\\mu", "mu");
    t := ReplacedString(t, "\\nu", "nu");
    t := ReplacedString(t, "\\xi", "xi");
    t := ReplacedString(t, "\\pi", "pi");
    t := ReplacedString(t, "\\rho", "rho");
    t := ReplacedString(t, "\\sigma", "sigma");
    t := ReplacedString(t, "\\tau", "tau");
    t := ReplacedString(t, "\\upsilon", "upsilon");
    t := ReplacedString(t, "\\phi", "phi");
    t := ReplacedString(t, "\\varphi", "phi");
    t := ReplacedString(t, "\\chi", "chi");
    t := ReplacedString(t, "\\psi", "psi");
    t := ReplacedString(t, "\\omega", "omega");
    t := ReplacedString(t, " ", "");
    return t;
end;;

Step1RelationToProduct := function(s)
    local t, greek, pieces, out, piece, i, chars, operand, last_was_operand;
    t := CleanStep1String(s);
    greek := [
        ["\\alpha", "alpha"], ["\\beta", "beta"], ["\\gamma", "gamma"],
        ["\\delta", "delta"], ["\\epsilon", "epsilon"], ["\\varepsilon", "epsilon"],
        ["\\zeta", "zeta"], ["\\eta", "eta"], ["\\theta", "theta"],
        ["\\vartheta", "theta"], ["\\iota", "iota"], ["\\kappa", "kappa"],
        ["\\lambda", "lambda"], ["\\mu", "mu"], ["\\nu", "nu"],
        ["\\xi", "xi"], ["\\pi", "pi"], ["\\rho", "rho"],
        ["\\sigma", "sigma"], ["\\tau", "tau"], ["\\upsilon", "upsilon"],
        ["\\phi", "phi"], ["\\varphi", "phi"], ["\\chi", "chi"],
        ["\\psi", "psi"], ["\\omega", "omega"]
    ];
    for piece in greek do
        t := ReplacedString(t, piece[1], Concatenation(" ", piece[2], " "));
    od;
    t := ReplacedString(t, "+", " + ");
    t := ReplacedString(t, "-", " - ");
    t := ReplacedString(t, "*", " * ");
    pieces := Filtered(SplitString(t, " ,;"), x -> Length(x) > 0);

    out := [];
    last_was_operand := false;
    for piece in pieces do
        if piece = "+" or piece = "-" then
            Add(out, piece);
            last_was_operand := false;
        elif piece = "*" then
            Add(out, "*");
            last_was_operand := false;
        else
            if piece in List(greek, x -> x[2]) then
                operand := piece;
            elif ForAll(piece, c -> c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_") then
                chars := [];
                for i in [1..Length(piece)] do
                    Add(chars, piece{[i..i]});
                od;
                operand := JoinStringsWithSeparator(chars, "*");
            else
                operand := NormalizeStep1Name(piece);
            fi;
            if last_was_operand then
                Add(out, "*");
            fi;
            Add(out, operand);
            last_was_operand := true;
        fi;
    od;

    return JoinStringsWithSeparator(out, "");
end;;

Step1RandomName4 := function()
    local alphabet, result, i;
    alphabet := "abcdefghijklmnopqrstuvwxyz0123456789";
    result := "";
    for i in [1..4] do
        result := Concatenation(result, alphabet{[Random([1..Length(alphabet)])]});
    od;
    return result;
end;;

Step1TikzPosition := function(line, key)
    local pos, rest, toks, tok, cleaned, rowcol, r, c;
    pos := PositionSublist(line, key);
    if pos = fail then
        return fail;
    fi;
    rest := line{[pos + Length(key)..Length(line)]};
    toks := Filtered(SplitString(rest, " ,]"), x -> Length(x) > 0);
    for tok in toks do
        cleaned := CleanStep1String(tok);
        rowcol := SplitString(cleaned, "-");
        if Length(rowcol) >= 2 then
            r := Int(rowcol[1]);
            c := Int(rowcol[2]);
            if r <> fail and c <> fail then
                return [r, c];
            fi;
        fi;
    od;
    return fail;
end;;

Step1TikzArrowLabel := function(line)
    local qpos, rest, qpos2;
    qpos := PositionSublist(line, "\"");
    if qpos = fail then
        return "a";
    fi;
    rest := line{[qpos + 1..Length(line)]};
    qpos2 := PositionSublist(rest, "\"");
    if qpos2 = fail then
        return "a";
    fi;
    return NormalizeStep1Name(rest{[1..qpos2 - 1]});
end;;

Step1ParseTikzcd := function()
    local in_matrix, row_idx, max_col, line_raw, line, row_part, cells, col_idx,
          clean, lower, val, pos, rest, pieces, rel_piece, rel_expr,
          cell_vertex, arrow_lines, from_pos, to_pos, src, dst, lbl, rowstr,
          min_row, max_row, min_col, used_max_col, has_numeric, r, c;

    n_verts := 0;
    Q_arrows := [];
    rel_list := [];
    qs_rows := [];

    in_matrix := false;
    row_idx := 0;
    max_col := 0;
    cell_vertex := [];
    arrow_lines := [];

    for line_raw in file_lines do
        line := Filtered(line_raw, c -> c <> '\r');
        if PositionSublist(line, "\\begin{tikzcd}") <> fail then
            in_matrix := true;
            continue;
        fi;
        if PositionSublist(line, "\\end{tikzcd}") <> fail then
            in_matrix := false;
            continue;
        fi;
        if PositionSublist(line, "\\arrow") <> fail then
            Add(arrow_lines, line);
            continue;
        fi;
        if in_matrix then
            row_idx := row_idx + 1;
            row_part := ReplacedString(line, "\\\\", "");
            row_part := ReplacedString(row_part, "\\&", "&");
            cells := SplitString(row_part, "&");
            if Length(cells) > max_col then max_col := Length(cells); fi;
            for col_idx in [1..Length(cells)] do
                clean := CleanStep1String(cells[col_idx]);
                lower := LowercaseString(clean);
                if Length(clean) = 0 then
                    continue;
                fi;
                if PositionSublist(lower, "rel:") <> fail then
                    pos := PositionSublist(lower, "rel:");
                    rest := clean{[pos + 4..Length(clean)]};
                    pieces := Filtered(SplitString(rest, ",;"), x -> Length(CleanStep1String(x)) > 0);
                    for rel_piece in pieces do
                        rel_expr := Step1RelationToProduct(rel_piece);
                        if Length(rel_expr) > 0 then Add(rel_list, rel_expr); fi;
                    od;
                    continue;
                fi;
                if PositionSublist(lower, "name:") <> fail then
                    pos := PositionSublist(lower, "name:");
                    output_name := CleanStep1String(clean{[pos + 5..Length(clean)]});
                    continue;
                fi;
                val := Int(clean);
                if val <> fail then
                    if not IsBound(cell_vertex[row_idx]) then cell_vertex[row_idx] := []; fi;
                    cell_vertex[row_idx][col_idx] := val;
                    if val > n_verts then n_verts := val; fi;
                fi;
            od;
        fi;
    od;

    min_row := fail;
    max_row := fail;
    min_col := fail;
    used_max_col := fail;
    for r in [1..Length(cell_vertex)] do
        if IsBound(cell_vertex[r]) then
            for c in [1..Length(cell_vertex[r])] do
                if IsBound(cell_vertex[r][c]) then
                    if min_row = fail or r < min_row then min_row := r; fi;
                    if max_row = fail or r > max_row then max_row := r; fi;
                    if min_col = fail or c < min_col then min_col := c; fi;
                    if used_max_col = fail or c > used_max_col then used_max_col := c; fi;
                fi;
            od;
        fi;
    od;

    if min_row <> fail then
        for row_idx in [min_row..max_row] do
            rowstr := "";
            for col_idx in [min_col..used_max_col] do
                if IsBound(cell_vertex[row_idx]) and IsBound(cell_vertex[row_idx][col_idx]) then
                    rowstr := Concatenation(rowstr, String(cell_vertex[row_idx][col_idx]));
                else
                    rowstr := Concatenation(rowstr, "-");
                fi;
            od;
            Add(qs_rows, rowstr);
        od;
    fi;

    for line in arrow_lines do
        from_pos := Step1TikzPosition(line, "from=");
        to_pos := Step1TikzPosition(line, "to=");
        if from_pos <> fail and to_pos <> fail then
            if IsBound(cell_vertex[from_pos[1]]) and IsBound(cell_vertex[from_pos[1]][from_pos[2]]) and
               IsBound(cell_vertex[to_pos[1]]) and IsBound(cell_vertex[to_pos[1]][to_pos[2]]) then
                src := cell_vertex[from_pos[1]][from_pos[2]];
                dst := cell_vertex[to_pos[1]][to_pos[2]];
                lbl := Step1TikzArrowLabel(line);
                Add(Q_arrows, [src, dst, lbl]);
            fi;
        fi;
    od;

    if output_name = "Q" then
        output_name := Step1RandomName4();
    fi;
end;;

Step1ParseTikzcd();;
