# BoilerGen — LLM Reference

This file is intended to be added to an AI assistant's context so it can help users **create, edit, and debug BoilerGen templates** correctly.
It is derived from the source code and the official template library and is more precise than the README.

---

## 1. CLI Commands

| Command | Description |
|---|---|
| `boilergen create` | Interactive project generation wizard |
| `boilergen templates` | Print a tree of all available templates |
| `boilergen config` | Show the path and content of the config file |
| `boilergen cleanup [path]` | Clean up redundant empty lines in a file or directory |

### `boilergen create` flags

| Flag | Default | Description |
|---|---|---|
| `--disable-dependencies` | `false` | Expert mode: allow manually deselecting auto-resolved dependencies |
| `--minimal-ui` | `false` | Use plain-text terminal UI (no Rich/colors) |
| `--clear-output` | `false` | Delete output directory before generation if it already exists |
| `--disable-quote-parsing` | `false` | Disable automatic surrounding-quote removal for config values |
| `--dry-run` | `false` | Preview generated file content without writing anything to disk |

### Config file

Boilergen stores its own config (not template configs) via `boilergen config`.
The two keys that matter are inside `[TEMPLATES]`:

```ini
[TEMPLATES]
TemplateLocation = /absolute/path/to/your/boilergen/folder
TemplateRepository = https://github.com/some/repo.git
```

- `TemplateLocation` takes precedence over `TemplateRepository`.
- When `TemplateRepository` is set (and `TemplateLocation` is empty), boilergen clones the repo on first use into `./cloned_templates/`.
- The tool always looks for a `templates/` subdirectory inside the resolved path.

---

## 2. Repository / Directory Layout

```
<boilergen-root>/               ← configured via TemplateLocation (points HERE)
├── templates/                  ← boilergen scans this directory
│   ├── <Category>/             ← arbitrary grouping folder (no template.yaml)
│   │   └── <TemplateName>/     ← template folder (HAS template.yaml)
│   │       ├── template.yaml   ← REQUIRED: template definition
│   │       ├── template/       ← REQUIRED: files to be copied to output
│   │       │   └── ...
│   │       └── injections;/    ← OPTIONAL: injection source files + definition
│   │           ├── injections.yaml
│   │           └── <source-files>
└── hooks/                      ← OPTIONAL: shell scripts
    ├── pre-generation.txt
    └── post-generation.txt
```

**Key rules:**
- A directory is treated as a **template** if and only if it contains `template.yaml` directly inside it.
- A directory without `template.yaml` is treated as a **navigation subgroup** in the UI.
- Files inside `template/` are reproduced verbatim (relative paths preserved) into the output, minus the leading `template/` segment. E.g. `template/api/main.py` → `<output>/api/main.py`.
- The `injections;` folder (note the semicolon — this is intentional) is never copied to the output.

---

## 3. `template.yaml` — Template Definition

```yaml
id: flask                        # REQUIRED. Unique across ALL templates.
label: "Flask Base App"          # REQUIRED. Human-readable name shown in the UI.
requires: []                     # OPTIONAL. List of template IDs this depends on.
config:                          # OPTIONAL. Default values for boilergen:config variables.
  debug: True
  port: 5000
  host: "0.0.0.0"
```

### Rules for `id`
- Must be unique across the entire template tree.
- Used in `requires` lists and injection `target` fields.
- Keep it lowercase, no spaces (use hyphens or underscores).

### Rules for `requires`
- Lists IDs of templates that must also be selected when this template is chosen.
- Boilergen auto-selects dependencies and shows them as `*` in the UI.
- Dependency order is resolved topologically before file generation.
- Cyclic dependencies raise an error at generation time.

### Rules for `config`
- Keys here become the **default values** for `boilergen:config | key` references found in template files.
- Precedence (highest → lowest): CLI interactive input → `config` in `template.yaml` → inline default in the template file.

---

## 4. Tags — `boilergen:tag`

Tags mark named regions inside template files. They serve two purposes:
1. **The tag lines themselves are stripped** from the output (the opening and closing comment lines become empty lines).
2. **Injections target tags** to insert content at precise locations.

### Syntax

```
<COMMENT_START> <<boilergen:<identifier>
<content>
<COMMENT_START> boilergen:<identifier>>>
```

The comment prefix must match the file's language. Examples:

```python
# <<boilergen:imports
from flask import Flask
# boilergen:imports>>
```

```yaml
# <<boilergen:dependencies
Flask==3.1.1
# boilergen:dependencies>>
```

```
<<boilergen:top
# boilergen:top>>
```

### Rules
- Opening tag: `<<boilergen:<identifier>` — must appear somewhere on the line (usually after a comment marker).
- Closing tag: `boilergen:<identifier>>>` — must appear on its own line.
- `boilergen:config` is a **reserved** identifier and is **not** treated as a tag.
- Tag identifiers must be unique **within a template**. Strongly recommended to be unique across all templates (e.g. `flask_imports`, `auth_init`).
- Tags may **not** be inline (they require their own line).
- After generation, tag lines are replaced with empty lines (not deleted, so line numbers of surrounding content are preserved).

---

## 5. Configs — `boilergen:config`

Config expressions are inline placeholders replaced with user-supplied or default values at generation time.

### Syntax

```
boilergen:config | <identifier> | <default_value>
```

The default value is optional but must be supplied somewhere (either inline or in `template.yaml`).

### Placement in code

Configs are typically placed **inside string literals** so the file remains syntactically valid before processing:

```python
debug = bool("boilergen:config | debug | True")
app.run(host='boilergen:config | host | "0.0.0.0"', port=int("boilergen:config | port"))
```

```env
SUPABASE_URL=boilergen:config | SUPABASE_URL
```

### Quote stripping (important!)

When a config expression is surrounded by quotes (`"..."` or `'...'`), boilergen **automatically strips those surrounding quotes** from the output — unless `--disable-quote-parsing` is passed.

This means:

| Template source | Output (default behavior) |
|---|---|
| `"boilergen:config \| port \| 5000"` | `5000` |
| `'boilergen:config \| host \| "0.0.0.0"'` | `"0.0.0.0"` |
| `boilergen:config \| SUPABASE_URL` | `<value>` (no quotes, already outside string) |

The inner value `"0.0.0.0"` retains its own quotes because those are **part of the value**, not the surrounding string. The outer `'...'` is stripped.

### Config value type guidance
- Boilergen substitutes values as raw strings. Type conversion (e.g. `bool(...)`, `int(...)`) must be done in the template code itself.
- For Python: `bool("boilergen:config | debug | True")` will always produce `True` at runtime because `bool("False") == True`. To handle booleans properly, write: `debug = "boilergen:config | debug | True" == "True"` or use a proper parsing function.

### Precedence resolution
```
CLI interactive input  (highest)
       ↓
template.yaml `config:` block
       ↓
Inline default value in template file  (lowest)
```

### Interactive Config Editor

During the `create` flow, BoilerGen opens a full-screen interactive editor (powered by `prompt-toolkit`) for any template file containing configuration placeholders.

**Usage:**
- The editor shows a list of `key = value` pairs.
- The user must only modify the `value` part.
- **Save/Confirm:** `Ctrl+S`
- **Cancel:** `Ctrl+C` (aborts the entire generation process)
- **Validation:** The editor ensures all original keys are still present before allowing a save.

---

## 6. Injections

Injections allow a template to insert content into files that belong to **another template**. This is how add-on templates (e.g. Auth) modify a base template (e.g. Flask) without editing the base template's files directly.

### Directory structure

```
<TemplateName>/
├── template.yaml
├── template/
└── injections;/              ← must be named exactly "injections;" (with semicolon)
    ├── injections.yaml       ← injection definitions
    ├── imports.py            ← source content file
    ├── register_bp.py        ← source content file
    └── any-other-file.txt
```

### `injections.yaml` format

```yaml
injections:
  - target: flask              # id of the template whose file will be modified
    at:
      file: api/main.py        # path relative to output root
      tag: imports             # tag identifier to inject near (mutually exclusive with `line`)
    method:
      insert:
        - bottom               # injection position
    from: imports.py           # source file inside injections;/ folder

  - target: flask
    at:
      file: api/main.py
      tag: init
    method:
      insert:
        - bottom
    from: register_bp.py

  - target: flask
    at:
      file: requirements.txt
      tag: dependencies
    method:
      replace:                 # replaces the entire tagged region
    from: new-requirements.txt
```

### `method` values

| Method | Description |
|---|---|
| `insert: [above]` | Insert source content **before** the opening tag line |
| `insert: [below]` | Insert source content **after** the closing tag line |
| `insert: [top]` | Insert source content **after** the opening tag line (inside, at top) |
| `insert: [bottom]` | Insert source content **before** the closing tag line (inside, at bottom) |
| `replace:` | Replace everything between (and including) the tag lines with source content |

### Rules
- `tag` and `line` are mutually exclusive in an `at` block.
- The `target` field must match the `id` of a template listed in the current template's `requires`.
- The `from` path is relative to the `injections;/` directory.
- Injections are applied **before** config substitution and tag line removal.
- Multiple injections into the same file are applied in order; tag line positions are updated after each injection.
- The `injections.yaml` file itself is never copied to the output.

### Example: adding imports to a Flask app

`injections;/imports.py`:
```python
from auth import register as r1, login as r2
from auth import auth_bp
```

`injections.yaml`:
```yaml
injections:
  - target: flask
    at:
      file: api/main.py
      tag: imports
    method:
      insert:
        - bottom
    from: imports.py
```

This inserts the import lines at the **bottom of the `imports` tag region** in `api/main.py` of the `flask` template.

---

## 7. Hooks

Hooks are shell commands executed before or after the entire project generation.

```
<boilergen-root>/
└── hooks/
    ├── pre-generation.txt    ← runs before any files are written
    └── post-generation.txt   ← runs after all files are written
```

Each file contains one shell command per line. Commands run sequentially, top to bottom. The working directory when commands run is the **output directory**.

Example `post-generation.txt`:
```
git init
git add .
git commit -m "Initial commit - generated by boilergen"
```

Hooks are **not** template-specific — they apply to every `boilergen create` run that uses this template root.

---

## 8. Complete Worked Example

### Goal
A `supabaseAuth` template that:
- Adds auth modules and API routes to the output
- Injects imports and blueprint registration into the Flask base app
- Appends auth dependencies to `requirements.txt`
- Injects Supabase env vars into `.env`

### `template.yaml`
```yaml
id: supabaseAuth
label: "Supabase Auth implementation"
requires: [flask]
```

### Directory tree
```
Auth/
├── template.yaml
├── template/
│   ├── api/
│   │   └── auth/
│   │       ├── __init__.py        # defines auth_bp Blueprint
│   │       ├── login.py
│   │       ├── register.py
│   │       └── ...
│   └── modules/
│       ├── auth/
│       │   ├── __init__.py        # creates supabase client from env vars
│       │   └── retrieve_jwt.py
│       └── exceptions/
│           └── AuthExceptions.py
└── injections;/
    ├── injections.yaml
    ├── imports.py              # from auth import auth_bp, ...
    ├── register_bp.py          # app.register_blueprint(auth_bp, ...)
    ├── auth-requirements.txt   # supabase==..., PyJWT==...
    └── supabase.env            # SUPABASE_URL=boilergen:config | SUPABASE_URL
```

### `injections;/supabase.env`
```
# <<boilergen:env_config
SUPABASE_URL=boilergen:config | SUPABASE_URL
SUPABASE_ANON_KEY=boilergen:config | SUPABASE_ANON_KEY
SUPABASE_JWT_SECRET=boilergen:config | SUPABASE_JWT_SECRET
# boilergen:env_config>>
```

This injection file itself uses tags and configs so that the content injected into `.env` is also processed for config substitution.

### `injections.yaml`
```yaml
injections:
  - target: flask
    at:
      file: api/main.py
      tag: imports
    method:
      insert:
        - bottom
    from: imports.py

  - target: flask
    at:
      file: api/main.py
      tag: init
    method:
      insert:
        - bottom
    from: register_bp.py

  - target: flask
    at:
      file: .env
      tag: top
    method:
      insert:
        - top
    from: supabase.env

  - target: flask
    at:
      file: requirements.txt
      tag: dependencies
    method:
      insert:
        - bottom
    from: auth-requirements.txt
```

---

## 9. Common Mistakes

| Mistake | Correct approach |
|---|---|
| Using `boilergen:config` as a tag identifier | `config` is reserved — use any other identifier |
| Tag opening/closing on same line as code | Tags **must** be on their own line |
| Referencing a template in `target` that isn't in `requires` | Always add the target template's `id` to `requires` |
| Expecting `bool("False")` to be `False` | Python `bool("False") == True`; use `"boilergen:config | debug" == "True"` |
| Placing `injections.yaml` outside `injections;/` | The folder must be named `injections;` (with semicolon) at the template root level |
| Duplicate tag identifiers across templates | While allowed, it causes confusion; prefix them: `flask_imports`, `auth_imports` |
| Forgetting the `template/` subdirectory | All output files must live inside `template/` — files directly in the template root are not copied |
| `id` collision between templates | IDs are global; two templates with the same `id` will silently shadow each other |