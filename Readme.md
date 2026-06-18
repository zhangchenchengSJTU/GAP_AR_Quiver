# Drawing AR-quivers of Finite-Dimensional Algebras with GAP

## Quick Start

### Launch the container

> [!important]
>
> **A VPN is required to access the binder when you are in China.**

Automatic launch: click [![Binder](https://raw.githubusercontent.com/czhang271828/imgs/New_img//n_imgbadge_logo.svg)](https://mybinder.org/v2/gh/zhangchenchengSJTU/GAP_AR_Quiver/HEAD), or open one of the following links:

- Stable version: https://mybinder.org/v2/gh/zhangchenchengSJTU/GAP_AR_Quiver/main
- Testing version: https://mybinder.org/v2/gh/zhangchenchengSJTU/GAP_AR_Quiver/test

Manual launch: open [Binder](https://mybinder.org/) and choose the `GitHub` option. Complete only the following steps.

1. Make sure that the `GitHub repository name or URL` field is set to `GitHub`. Paste `https://github.com/zhangchenchengSJTU/GAP_AR_Quiver` into the box on the right.
2. Click `launch` directly. 

   > [!Note]
   >
   > You can also set `Git ref (branch, tag, or commit)` field to `test` to try the latest testing version.
3. Wait until the environment is ready. Binder will then redirect you to the Jupyter Notebook page.

### Enter Jupyter Notebook

After entering Jupyter Notebook, the browser address should look like `https://hub.bids.mybinder.org/user/zhangchenchengsjtu-gap_ar_quiver-???????/treee`. In the root directory, you should see the following items:

- `Dockerfile`: the environment specification, mainly for developers. Users do not need to edit it.
- `Readme.md`
- `Readme.pdf`
- `ARquiver`: the working directory for drawing AR-quivers. After entering this folder, you will see:
  - `source`: the source-code directory. Users usually do not need to inspect it.
  - `run.ipynb`: the notebook used to run the computation and rendering scripts.
  - `example.txt`, `untitled.txt`, and similar files: input files containing quiver data.

### Draw the path algebra

Use https://q.uiver.app to draw a quiver with relations. Please follow these conventions:

- vertices of the quiver should be positive integers;
- arrows should be simple Latin letters or Greek letters written in $\LaTeX$ format, such as `a` or `\alpha`;
- choose an empty grid cell and enter the relations of the path algebra in the form `rel: ....`.

Example:

![image-20260612214532284](https://raw.githubusercontent.com/czhang271828/imgs/New_img//n_imgimage-20260612214532284.png)

Click `LaTeX` at the bottom of the `q.uiver` page and copy the generated `tikzcd` source code. 

Create a new `txt` file named `yourfile.txt` inside the `ARquiver` directory, paste the copied source code into it, save the file, and close it.

### Draw the AR-quiver

Open `run.ipynb` and run the following cells in order:

```python
# Compute algebra data: filename.txt -> filename.log
%run source/compute_all.py
```

```python
# Render interactive diagram: filename.log -> filename.html
%run source/render_all.py
```

> [!Note]
>
> The chronological order: `yourfile.txt` `->` `yourfile.log` `->` `yourfile.html`.

The `ARquiver` directory will then contain:

- `yourfile.log`: the algebra computation log;
- `yourfile.html`: the interactive AR-quiver canvas.

### Arrange the AR-quiver into a usual form

Open `yourfile.html` to view the interactive visualization of the AR-quiver.

![image-20260618220032641](https://raw.githubusercontent.com/czhang271828/imgs/New_img//n_imgimage-20260618220032641.png)

We first describe the basic AR-quiver controls.

- Each ellipse represents an indecomposable module. Its dimension vector is arranged according to the vertex positions in the original `tikzcd` input.

  > [!caution]
  >
  > Some ellipses may overlap.
- Ellipses with purple borders are both projective and injective. Red vertices are projective but not injective, while blue vertices are injective but not projective.
- `Quivers > AR irreducible arrows`: show or hide irreducible morphisms, drawn as black arrows.
- `Quivers > Translation quiver τ`: show or hide the AR translation $\tau = D \mathrm{Tr}$, drawn as golden arrows.
- `View > Borders`: show or hide vertex borders.
- `Ctrl + Z` undoes an operation, and `Ctrl + Y` redoes it.

The main manual task is to arrange the AR-quiver into a readable standard form. Here are some useful guidelines.

> [!tip]
>
> The $\tau$-orbits, namely the orbits of the golden arrows, are disjoint. Projective-injective objects do not belong to any $\tau$-orbit. Every other indecomposable module belongs to exactly one $\tau$-orbit. Hence each $\tau$-orbit is one of the following two types:
>
> 1. a straight path from an injective object to a projective object;
> 2. a cycle that contains no projective or injective object.

Following this tip, we first find a projective object with long $\tau$-orbit, e.g., $\substack{2\\ 0 \quad 2}$ . Since vertices may overlap, you can refresh the page until a satisfying display occurs. Turn off `AR irreducible arrows`, then place the arrow $\substack{2\\ 0 \quad 2} \ \ \leftarrow \ \substack{2\\ 0 \quad 2}$ horizontally in an empty region. 

> [!tip]
>
> **Long-press the golden arrow** to align the next arrow (while making sure that there are no black arrows hidden behind).

This gives:

![image-20260618221201601](https://raw.githubusercontent.com/czhang271828/imgs/New_img//n_imgimage-20260618221201601.png)

Next, turn on `Irr` and look for the almost split short exact sequence $\substack{2\\ 0 \quad 2} \ \ \rightarrowtail \bigoplus M_i  \twoheadrightarrow \ \substack{2\\ 0 \quad 2}$.

<img src="https://raw.githubusercontent.com/czhang271828/imgs/New_img//n_imgimage-20260618221401009.png" alt="image-20260618221401009" style="zoom:50%;" />

Then turn off `AR irreducible arrows` again and long-press the golden arrows for alignment. If a cycle appears, select an edge and use the `↑` and `↓` keys to adjust the curvature of the arrow. After a sequence of such operations, one obtains the $\tau$-orbits:

![image-20260618221717802](https://raw.githubusercontent.com/czhang271828/imgs/New_img//n_imgimage-20260618221717802.png)

Finally, turn off `AR irreducible arrows` and adjust the curvature of the horizontal black arrows that were hidden behind the golden arrows. If some edges are visually inconvenient, double-click them to switch between dark and light colours. The final AR-quiver is then obtained:

![image-20260618222714203](https://raw.githubusercontent.com/czhang271828/imgs/New_img//n_imgimage-20260618222714203.png)

> [!Tip]
>
> Press `Ctrl + L` for full screen and enjoy this quiver.

## Features

The generated `filename.html` file is an interactive workspace for studying the AR-quiver and related homological data of the algebra defined by `filename.txt`. The page consists of a main canvas, a top navigation bar, and a sidebar opened by `Controls`. This introduction follows the order of the interface: first the canvas and top navigation, then each sidebar section from top to bottom.

### Basic canvas interaction

Each ellipse on the canvas represents an indecomposable module. The label shown inside the ellipse is normally the dimension vector, arranged according to the shape of the original input quiver when this information is available. The internal node number is the identifier used throughout `filename.log`.

Basic operations:

- Drag a vertex to change the layout.
- Drag the background to pan the view.
- Use the mouse wheel to zoom.
- Hover over a vertex to see only its internal node number.
- Double-click an edge to toggle between dark and light display colors.
- Select an edge and press `↑` or `↓` to adjust its curvature.

These operations only change the visualization. They do not recompute the algebra.

### Top navigation bar

#### `Controls`

This opens or hides the sidebar. The sidebar contains all overlays, lists, and tools. It is divided into `View`, `Quivers`, `Modules`, `Classes`, `Tilting`, and `Tools`.

#### `Fit graph`

This recenters and rescales the current canvas so that the visible graph fits into the window. It is useful after dragging vertices or zooming far away from the main diagram.

#### `Ctrl+Z` and `Ctrl+Y`

These buttons duplicate the keyboard shortcuts.

- `Ctrl+Z` undoes recent layout or coloring operations.
- `Ctrl+Y` redoes an operation that was undone.

They are intended for manual arrangement of the AR-quiver, especially when aligning $\tau$-orbits.

#### `Clear colors`

This removes temporary colorings produced by the calculator, list selections, torsion/cotorsion classes, tilting objects, support $\tau$-tilting objects, and module-class highlights. It does not delete arrows and does not change the underlying computation.

#### `show dimension vector`

This is the default label mode. Vertices display the dimension vectors of indecomposable modules. The source is the main `digraph Quiver` block in `filename.log`.

#### `show label`

This replaces each dimension vector by the internal node number. This is the best mode when comparing the picture with `filename.log`, since all tables in the log refer to modules by these numbers.

#### `show custom label`

This displays user-defined labels when available. If no custom label has been assigned, the vertex falls back to the dimension-vector label.

> [!Tip]
>
> Double click a vertex to **customise its label**. The input support simple unicodes. For instance, `N^2` displays like `N²` .

#### `Ctrl+L hide/show UI`

This keyboard shortcut hides or restores the user interface. It is useful for screenshots or for arranging a large graph without visual obstruction.

### Sidebar: `View`

#### `PD`

Displays the projective dimension of each indecomposable module as a floating label. The value `-1` denotes infinity or an unresolved value. The data come from

```text
PDID := [[node, pd, id], ...];
```

#### `ID`

Displays injective dimension, using the third entry of the same `PDID` table.

#### `Top`

Displays the simple factors of the top of each indecomposable module. Multiplicities are preserved. The data source is

```text
TopSoc := [[node, top, soc], ...];
```

#### `Soc`

Displays the simple factors of the socle of each indecomposable module, using the same `TopSoc` table.

#### `Borders`

Shows or hides vertex borders. The convention is:

- blue border: injective module;
- red border: projective module;
- purple border: projective-injective module;
- grey border: ordinary indecomposable module.

The source in the log is

```text
Projective modules found (Node IDs): [...]
Injective modules found (Node IDs):  [...]
```

### Sidebar: `Quivers`

This section overlays auxiliary quivers on top of the AR-quiver.

#### `AR irreducible arrows`

Shows or hides the black irreducible morphisms of the AR-quiver. These are the arrows in

```text
digraph Quiver { ... }
```

If multiple identical arrows occur, the display may collapse them visually while keeping multiplicity information.

#### `Translation quiver τ`

Shows the AR translation quiver. A golden arrow $M \longrightarrow N$ means $N=\tau M$. This is useful for arranging the AR-quiver into $\tau$-orbits. The data source is

```text
digraph TranslationQuiver { ... }
```

#### `Syzygy quiver`

Shows the syzygy quiver. A pink arrow $X \longrightarrow Y$ means that $Y$ is an indecomposable direct summand of the kernel of a projective cover of $X$, i.e. $Y \in \mathrm{smd}(\Omega X)$. The data source is

```text
digraph SyzygySummand { ... }
```

The calculator uses this quiver to compute $\Omega^n(X)$ by iteration.

#### `Cosyzygy quiver`

Shows the cosyzygy quiver. A green arrow $X \longrightarrow Y$ means that $Y$ is an indecomposable direct summand of the cokernel of an injective envelope of $X$, i.e. $Y \in \mathrm{smd}(\Sigma X)$. The data source is

```text
digraph CosyzygySummand { ... }
```

The calculator uses this quiver to compute $\Sigma^n(X)$.

#### `Radical quiver`

Shows the radical quiver. A cyan arrow $X \longrightarrow Y$ means that $Y$ is an indecomposable direct summand of $\operatorname{Rad}(X)$, i.e., $Y \in \mathrm{smd}(\mathrm{Rad}(X))$. Repeated arrows encode multiplicities. The data source is

```text
digraph RadicalSummand { ... }
```

The calculator uses this quiver to compute $\operatorname{Rad}^n(X)$.

#### `Coradical quiver`

Shows the coradical quiver. A purple arrow $X \longrightarrow Y$ means that $Y$ is an indecomposable direct summand of $X/\operatorname{Soc}(X)$, i.e., $Y \in \mathrm{smd}(X/\mathrm{Sox}(X))$. Repeated arrows encode multiplicities. The data source is

```text
digraph CoradicalSummand { ... }
```

The calculator uses this quiver to compute $\operatorname{Corad}^n(X)$.

#### `Hom dimension quiver`

Shows nonzero Hom dimensions. A brown arrow $M \longrightarrow N$ with label `k` (unlabelled cases means `k=1`) means $\dim\operatorname{Hom}(M,N)=k$. The source is

```text
digraph HomDim { ... }
```

#### `Ext dimension quiver`

Shows nonzero $\operatorname{Ext}^1$ dimensions. A red arrow $M \longrightarrow N$ with label `k` (unlabelled cases means `k=1`) means $\dim\operatorname{Ext}^1(M,N)=k$. The source is

```text
digraph ExtDim { ... }
```

Together with the syzygy quiver, this data is used by the calculator to evaluate higher $\mathrm{Ext}^{\geq 1}$ dimensions.

#### `Original quiver Q`

Opens a draggable window displaying the original quiver of the algebra and its relations. The source in the log is

```text
digraph Q { ... }
rel := ...;
```

The `see filename.txt` button opens the original input text. The `Open in q.uiver` button opens the https://q.uiver.app stored in the first line of the input file.

### Sidebar: `Modules`

These buttons highlight special classes of indecomposable modules. They do not alter the graph.

> [!Note]
>
> Let $M \oplus N$ be either one of the following kind of the modules, then so are $M$ and $N$. Hence the following property is enough to shown for indecomposable modules.

#### `Torsionless`

Highlights **non-projective** torsionless modules. A module is torsionless if it embeds into a projective module, equivalently if the canonical map
$$
M\to DDM, \quad m \mapsto [f \mapsto f(m)]
$$
is injective. The display colour is cyan. The source is

```text
Torsionless modules found (Node IDs): [...]
```

#### `Reflexive`

Highlights **non-projective** reflexive modules. A module is reflexive if the canonical map 
$$
M\to DDM, \quad m \mapsto [f \mapsto f(m)]
$$
 is an isomorphism. The display colour is purple. The source is

```text
Reflexive modules found (Node IDs): [...]
```

#### `Gorenstein projective`

Highlights **non-projective** Gorenstein projective modules in green. The source is

```text
Gorenstein projective modules found (Node IDs): [...]
```

#### `Gorenstein injective`

Highlights **non-injective** Gorenstein injective modules in red. The source is

```text
Gorenstein injective modules found (Node IDs): [...]
```

### Sidebar: `Classes`

#### `Torsion classes`

Opens a list of torsion pairs. Each row has the form

```text
T := [...] | F := [...] | tilting/non-tilting
```

Display convention:

- red vertices show the torsion class `T`;
- green vertices show the torsion-free class `F`.

Mathematically, `T` is closed under quotients and extensions, while `F` is closed under submodules and extensions. For a tilting module $L$, the induced torsion pair satisfies

\[
\mathcal T=\operatorname{gen}(L)=\operatorname{Ker}\operatorname{Ext}^1(L,-),
\qquad
\mathcal F=\operatorname{Ker}\operatorname{Hom}(L,-).
\]

The list is sorted by the stored class data. The source is

```text
# --- TorsionPairTable --- #
T := [...] | F := [...]
```

The `tilting` flag records whether the torsion pair arises from a tilting module.

> [!Caution]
>
> Different tilting modules may induce the same torsion pairs.

The `split` flag records whether the torsion pair splits. A torsion pair $(\mathcal T, \mathcal F)$ splits if and only if $\mathcal T \cup \mathcal F$ consists of all indecomposable modules.

![image-20260618231225010](https://raw.githubusercontent.com/czhang271828/imgs/New_img//n_imgimage-20260618231225010.png)

#### `Cotorsion classes`

Opens a list of cotorsion pairs. Each row has the form

```text
L := [...] | R := [...] | Hereditary := true/false
```

Display convention:

- blue vertices show the left class `L`;
- red vertices show the right class `R`;
- if a module belongs to both sides, half-colouring is used.

The `hereditary` flag records whether the cotorsion pair is hereditary. A cotorsion pair $(\mathcal L, \mathcal R)$ is hereditary if and only if $\mathrm{Ext}^{\geq 1}(\mathcal{L},\mathcal{R}) = 0$. The list is sorted by the stored left and right classes. The source is

```text
# --- CotorsionPairTable --- #
L := [...] | R := [...] | Hereditary := ...
```

![image-20260618231301708](https://raw.githubusercontent.com/czhang271828/imgs/New_img//n_imgimage-20260618231301708.png)

### Sidebar: `Tilting`

#### `Tilting modules`

Opens the list of classical tilting modules. A module $T$ is (classical $1$-)tilting if

- $\operatorname{pd}T\leq 1$;
- $\operatorname{Ext}^{\geq 1}(T,T)=0$;
- there is a short exact sequence $A\rightarrowtail T^0\twoheadrightarrow T^1$ with $T^0,T^1\in\operatorname{add}(T)$.

Display convention:

- grey vertices are the indecomposable summands of the selected tilting module;
- red vertices are in the induced torsion class;
- green vertices are in the induced torsion-free class.

The source rows contain

```text
L := [...]
F := [...]
T := [...]
```

where `L` is the tilting module, `T` is the torsion class, and `F` is the torsion-free class.

The `splitting` tag records whether the tilting module is splitting, using the criterion that every indecomposable module in `F` has injective dimension at most one over the original algebra.

The `separating` tag records whether the induced torsion pair `(T,F)` is split, i.e. every indecomposable module belongs to `T` or to `F`.

![image-20260619010144106](https://raw.githubusercontent.com/czhang271828/imgs/New_img//n_imgimage-20260619010144106.png)

#### `Support τ-tilting`

Opens the list of support $\tau$-tilting pairs. A pair $(P,M)$ is support $\tau$-tilting if $P$ is projective, $M$ is $\tau$-rigid, $\operatorname{Hom}(P,M)=0$, and the total number of indecomposable summands of $P$ and $M$ is the number of vertices of the original quiver.

The source is

```text
# --- SupportTauTiltingTable --- #
P := [...] | M := [...]
```

#### `Almost support τ-tilting`

Opens the list of almost support $\tau$-tilting pairs. These have the same format as support $\tau$-tilting pairs, but the total number of summands is one less than the number of vertices of the original quiver.

The source is

```text
# --- AlmostSupportTauTiltingTable --- #
P := [...] | M := [...]
```

### Sidebar: `Tools`

#### `Calculator`

The calculator performs operations using the data already stored in the HTML. Inputs and outputs use node label numbers.

Available operations:

- `dim Ext^k(A,B)`: computes total $\dim\operatorname{Ext}^k(A_i,B_j)$ over all selected labels.
- `ker Ext^k(A,-)`: returns all $X$ with $\operatorname{Ext}^k(A_i,X)=0$ for every selected $A_i$.
- `ker Ext^k(-,B)`: returns all $X$ with $\operatorname{Ext}^k(X,B_j)=0$ for every selected $B_j$.
- `Ω^n(A)`: iterates the syzygy quiver.
- `Σ^n(A)`: iterates the cosyzygy quiver.
- `Rad^n(A)`: iterates the radical quiver.
- `Corad^n(A)`: iterates the coradical quiver.

Multiplicity convention: `3 + 5` means $M_3\oplus M_5$, while `3^2 + 5` means $M_3^{\oplus 2}\oplus M_5$. Empty output is shown as `∅`.

![image-20260619010506325](https://raw.githubusercontent.com/czhang271828/imgs/New_img//n_imgimage-20260619010506325.png)

#### `Run with GAP`

Inside the calculator, this generates copyable GAP/QPA code reconstructing the quiver, algebra, projectives, injectives, simples, and serialized indecomposable modules when available. The script can also be downloaded as a `.g` file.

#### `Export AR-quiver to TeX`

Exports the current arranged AR-quiver layout as `xymatrix{}` in $\LaTeX$ code. The export uses the current vertex positions. The following `xymatrix` is available in `Typora`.
$$
\scriptsize\xymatrix{
{} & {\begin{smallmatrix}2 \\ 0 & 1\end{smallmatrix}} \ar[dr] \ar@/^0.3pc/@{-->}[rrrrrrrrrrrrrrrr] & {} & {\begin{smallmatrix}3 \\ 2 & 2\end{smallmatrix}} \ar[dr] \ar@{-->}[ll] & {} & {\begin{smallmatrix}1 \\ 2 & 1\end{smallmatrix}} \ar[dr] \ar@{-->}[ll] & {} & {\begin{smallmatrix}1 \\ 0 & 1\end{smallmatrix}} \ar[dr] \ar@{-->}[ll] & {} & {\begin{smallmatrix}1 \\ 0 & 1\end{smallmatrix}} \ar[dr] \ar@{-->}[ll] & {} & {\begin{smallmatrix}3 \\ 2 & 1\end{smallmatrix}} \ar[dr] \ar@{-->}[ll] & {} & {\begin{smallmatrix}3 \\ 2 & 3\end{smallmatrix}} \ar[dr] \ar@{-->}[ll] & {} & {\begin{smallmatrix}2 \\ 2 & 1\end{smallmatrix}} \ar[dr] \ar@{-->}[ll] & {} & {\begin{smallmatrix}1 \\ 0 & 2\end{smallmatrix}} \ar@{-->}[ll] & {} \\
{\begin{smallmatrix}2 \\ 0 & 2\end{smallmatrix}} \ar[ur] \ar[dr] & {} & {\begin{smallmatrix}2 \\ 0 & 2\end{smallmatrix}} \ar[ur] \ar@{-->}[ll] & {} & {\begin{smallmatrix}1 \\ 2 & 0\end{smallmatrix}} \ar[ur] \ar@{-->}[ll] & {} & {\begin{smallmatrix}0 \\ 0 & 1\end{smallmatrix}} \ar[ur] \ar@{-->}[ll] & {} & {\begin{smallmatrix}1 \\ 0 & 0\end{smallmatrix}} \ar[dr] \ar[ur] \ar@{-->}[ll] & {} & {\begin{smallmatrix}2 \\ 2 & 1\end{smallmatrix}} \ar[dr] \ar[ur] \ar@{-->}[ll] & {} & {\begin{smallmatrix}3 \\ 2 & 2\end{smallmatrix}} \ar[dr] \ar[ur] \ar@{-->}[ll] & {} & {\begin{smallmatrix}4 \\ 2 & 3\end{smallmatrix}} \ar[dr] \ar[ur] \ar@{-->}[ll] & {} & {\begin{smallmatrix}2 \\ 2 & 2\end{smallmatrix}} \ar[dr] \ar[ur] \ar@{-->}[ll] & {} & {} \\
{} & {\begin{smallmatrix}2 \\ 0 & 3\end{smallmatrix}} \ar[ur] & {} & {} & {} & {} & {} & {} & {} & {\begin{smallmatrix}2 \\ 2 & 0\end{smallmatrix}} \ar[ur] \ar[dr] & {} & {\begin{smallmatrix}2 \\ 2 & 2\end{smallmatrix}} \ar[ur] \ar[dr] \ar@{-->}[ll] & {} & {\begin{smallmatrix}4 \\ 2 & 2\end{smallmatrix}} \ar[ur] \ar[dr] \ar@{-->}[ll] & {} & {\begin{smallmatrix}4 \\ 2 & 4\end{smallmatrix}} \ar[ur] \ar[dr] \ar@{-->}[ll] & {} & {\begin{smallmatrix}0 \\ 2 & 0\end{smallmatrix}} \ar[dr] \ar@{-->}[ll] & {} \\
{} & {} & {} & {} & {} & {} & {} & {} & {\begin{smallmatrix}1 \\ 1 & 0\end{smallmatrix}} \ar[ur] \ar[dr] \ar@/^0.3pc/@{-->}[rrrrrrrrrr] & {} & {\begin{smallmatrix}2 \\ 2 & 1\end{smallmatrix}} \ar[ur] \ar[dr] \ar@{-->}[ll] & {} & {\begin{smallmatrix}3 \\ 2 & 2\end{smallmatrix}} \ar[ur] \ar[dr] \ar@{-->}[ll] & {} & {\begin{smallmatrix}4 \\ 2 & 3\end{smallmatrix}} \ar[ur] \ar[dr] \ar@{-->}[ll] & {} & {\begin{smallmatrix}2 \\ 2 & 2\end{smallmatrix}} \ar[ur] \ar[dr] \ar@{-->}[ll] & {} & {\begin{smallmatrix}0 \\ 1 & 0\end{smallmatrix}} \ar@{-->}[ll] \\
{} & {} & {} & {} & {} & {} & {} & {\begin{smallmatrix}1 \\ 2 & 0\end{smallmatrix}} \ar[ur] \ar[dr] \ar@/^0.3pc/@{-->}[rrrrrrrrrr] & {} & {\begin{smallmatrix}1 \\ 1 & 1\end{smallmatrix}} \ar[ur] \ar[dr] \ar@{-->}[ll] & {} & {\begin{smallmatrix}3 \\ 2 & 1\end{smallmatrix}} \ar[ur] \ar[dr] \ar@{-->}[ll] & {} & {\begin{smallmatrix}3 \\ 2 & 3\end{smallmatrix}} \ar[ur] \ar@{-->}[ll] & {} & {\begin{smallmatrix}2 \\ 2 & 1\end{smallmatrix}} \ar[ur] \ar@{-->}[ll] & {} & {\begin{smallmatrix}2 \\ 1 & 2\end{smallmatrix}} \ar[ur] \ar@{-->}[ll] & {} \\
{} & {} & {} & {} & {} & {} & {} & {} & {\begin{smallmatrix}1 \\ 2 & 1\end{smallmatrix}} \ar[ur] \ar@/^0.6pc/@{-->}[rrrr] & {} & {\begin{smallmatrix}2 \\ 1 & 1\end{smallmatrix}} \ar[ur] \ar@{-->}[ll] & {} & {\begin{smallmatrix}3 \\ 2 & 2\end{smallmatrix}} \ar[ur] \ar@{-->}[ll] & {} & {} & {} & {} & {} & {}
}
$$


#### `Color legend`

Opens a draggable legend explaining all visual conventions: vertex borders, module-class highlights, AR arrows, $\tau$-arrows, syzygy, cosyzygy, radical, coradical, Hom/Ext arrows, torsion/cotorsion colours, tilting colours, support $\tau$-tilting colours, calculator colours, and floating labels.

## Acknowledgement

The author gratefully acknowledges the developers and maintainers of [GAP](https://www.gap-system.org/), [Binder](https://mybinder.org/), and [quiver](https://q.uiver.app/) for providing essential tools and infrastructure used by this project. The implementation was inspired in part by A. Konovalov's [try-gap-in-jupyter](https://github.com/gap-system/try-gap-in-jupyter) repository. The author also acknowledges the assistance of the AI model `chatgpt-5.5-thinking` during the development and refinement of the codebase.

