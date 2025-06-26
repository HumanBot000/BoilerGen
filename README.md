# BoilerGen

BoilerGen creates files from reusable templates and injects necessary code (e.g. imports, registrations) directly into your project — without breaking existing code.

No more manual integration steps. No more forgotten imports. Just working boilerplate.

> 🚧 Work in progress: The project is currently not in a usable state. 


## Setup

1. [Install Python (3.11+) and pip](https://realpython.com/installing-python/)
2. Clone this repository using    `git clone https://github.com/HumanBot000/BoilerGen.git`
3. Run `pip install -r requirements.txt`
4. Open your preferred command line and `cd` into the project directory.
5. Run `pip install -e .`
6. [Set up your first templates](x)  
7. Run `boilergen create` and follow the instructions.
→ All available commands can be accessed by `boilergen --help`.


## Templates

Templates are pre-defined code snippets that can be reused across multiple projects with the same tech stack.  
If you already have a boilerplate repository, you may need to edit some snippets to follow [BoilerGen's tagging rules](x).

Templates are configured in the `boilergen/templates` directory and can be grouped into multiple subgroups [(see examples)](x).

## Template.yaml
Each template needs a `template.yaml` file for its Template Definition.
We highly encourage you to take a look at the  [(Example Templates)](x).
Otherwise, here is a quick breakdown:
```yaml
id: flask  
label: "Flask Base App"  
requires: [example]  
config:  
  debug: True  
  port: 5000
```
### Fields
| id       	| The technical identifier for this template (Must be unique across all Templates)                                                           	|
|----------	|--------------------------------------------------------------------------------------------------------------------------------------------	|
| label    	| The human-readable name of this Template (This will be shown in the Template browser)                                                      	|
| requires 	| List of templates this template relies on (dependence management). This will be needed for injections. Use the `id` field of the template. 	|
| config   	| A Map of default values for [boilergen configurations](x)                                                                                       	|
## Tagging

Often, multiple code snippets depend on each other and can't simply be copy-pasted and expected to work (e.g., special API routes need to be registered in the main API definition before startup). To simplify this process, BoilerGen uses a tagging system to automatically adjust your code.

```python
# <<boilergen:imports
from flask import Flask  
# boilergen:imports>>
```

> Depending on your language of choice, you may need to edit the [comment syntax](https://gist.github.com/dk949/88b2652284234f723decaeb84db2576c). BoilerGen will comply with this, but the core syntax remains the same.

### Tagging Syntax Explained

- `<<` indicates an opening tag.
- `>>` indicates a closing tag.
- The comment contains the keyword `boilergen`, identifying it as a special tag.
- After `boilergen`, a colon `:` and a unique identifier (e.g., `imports`) must follow.
- Everything between the tag lines is the tag's content and will be used for code injection.
> ⚠️ Tag opening and closing definitions **may not happen inline**. They need their own line with with no additional syntax.
>
> ⚠️ You **must not** use this exact syntax (`<<boilergen:...>>`) in any context not intended for BoilerGen. Doing so will corrupt your template.
>
> ⚠️ Identifiers must be unique **within** a template. We strongly recommend aslo keeping them unique **across** all templates to avoid confusion.

Example of unique identifiers:
```text
boilergen:main-template_imports
boilergen:main-template_routes
```
---

## Configurations

To simplify simple variations between projects (e.g., changing the app name or enabling debug mode), templates support configurable variables. These can be set in a `template.yaml` file or supplied interactively during `boilergen create`.

```python
debug = bool("boilergen:config | debug | True")
```

### Configuration Syntax Explained

- Follows the same general structure as tagging.
- Does **not** require a unique identifier after the colon.
- The format is:  
  `boilergen:config | config_name | default_value`
- The `default_value` is optional, but must be provided at some point.

Example:
```python
app.run(
    host='boilergen:config | IP | "0.0.0.0"',
    port="boilergen:config | port",
    debug=debug
)
```

> In this example:
> - `host` will be parsed as a `str ("0.0.0.0")` .
> - `debug` is already parsed using `bool(...)` above

We **strongly recommend** not placing configuration tags inside **inline comments**, as this may break the syntax highlighting and parsing in your language-specific editor or runtime. BoilerGen tries to **verify data types**, but we **strongly recommend** accepting them as **Strings** and parsing them individually, depending on your language,

---

### Configuration Precedence

The order of precedence for resolving configuration values is:

```mermaid
stateDiagram-v2
    step1: CLI input during project creation
    step2: Value from template.yaml
    step3: Default value in template
    step1 --> step2
    step2 --> step3
```

---


