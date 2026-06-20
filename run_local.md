# Run locally

These commands run the AR quiver pipeline locally from the existing virtual environment.

## 1. Enter the project runtime directory

```bash
cd /home/czhang/Math/GAP_AR_Quiver/ARquiver
```

## 2. Activate the local virtual environment

Use the existing Binder-style virtual environment:

```bash
source .venv-binder/bin/activate
```

If you need the Python 3.6 environment instead, use:

```bash
source .venv-binder36/bin/activate
```

## 3. Check that GAP and QPA are available

```bash
gap -q <<'GAP'
LoadPackage("QPA");;
Print("QPA loaded\n");
QUIT;
GAP
```

You should see `QPA loaded`.

## 4. Generate missing `.log` files from `.txt` inputs

The script scans `ARquiver/*.txt`, skips helper files such as `Step1.txt`, and computes logs that do not already exist.

```bash
python source/compute_all.py
```

For example, if `yourfile.txt` exists and `yourfile.log` does not, this creates:

```text
yourfile.log
```

To force recomputation of one file, remove its existing log first:

```bash
rm yourfile.log
python source/compute_all.py
```

## 5. Generate HTML files from logs

After logs exist, render the HTML pages:

```bash
python source/render_all.py
```

This creates or updates files such as:

```text
example.html
yourfile.html
```

## 6. Full local rebuild

From `ARquiver/`, run:

```bash
source .venv-binder/bin/activate
python source/compute_all.py
python source/render_all.py
```

## 7. Serve the generated HTML locally

From the repository root:

```bash
cd /home/czhang/Math/GAP_AR_Quiver
python3 -m http.server 8765 --bind 0.0.0.0
```

Then open:

```text
http://127.0.0.1:8765/ARquiver/example.html
```

or replace `example.html` with the HTML file you generated.

## 8. Useful notes

- Put new quiver input files as `.txt` files inside `ARquiver/`.
- `compute_all.py` only computes logs that are missing.
- `render_all.py` reads existing `.log` files and writes matching `.html` files.
- The generated HTML now contains `Controls -> Tools -> Some useful GAP codes`, where you can copy GAP snippets such as `generate this quiver` and `find gen(-)`.
