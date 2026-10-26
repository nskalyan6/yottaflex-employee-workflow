# YottaFlex Employee Onboarding / Offboarding Workflow

A reproducible synthetic data generator and validator for employee onboarding/offboarding workflows. This is an assessment project starter: it creates linked master and transaction data, intentionally labelled edge cases, audit history, and a validation report.

## Requirements

- Python 3.10+
- VS Code (or any editor)
- Internet only to install dependencies; the generator itself runs locally.

## Setup in VS Code

Open this folder in VS Code. In the integrated terminal:

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, run `.venv\Scripts\python.exe` directly or use Command Prompt activation.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run a quick starter dataset

```bash
python scripts/generate_data.py --scale 0.1 --seed 20261022
python scripts/validate_data.py
```

The starter scale creates approximately 50 employees and 400 task instances so you can inspect and debug quickly.

## Generate the full target volume

```bash
python scripts/generate_data.py --scale 1.0 --seed 20261022
python scripts/validate_data.py
```

The full run targets 500 employees, 500 onboarding cases, 4,000 task instances, 600 assets, and 300 access requests.

## Run tests

```bash
python -m pytest -q
```

## Outputs

- `data/generated/*.csv`: generated entity and transaction tables.
- `data/generated/source_manifest.json`: seed, scale, row counts, and provenance.
- `data/generated/checksums.json`: SHA-256 checksums for generated CSV files.
- `data/generated/validation_summary.json`: validator results and exception counts.
- `data/ground_truth/ground_truth.csv`: labelled anomalies and expected decisions. Keep this separate from detector input features.

## What the first version covers

- Deterministic IDs and seeded synthetic generation.
- Departments, roles, managers, employees, onboarding cases, task templates/instances, assets, asset assignments, access requests, approvals, offboarding cases, and audit events.
- Seven labelled edge-case categories, with checks for keys, references, dependency cycles, approval-before-provisioning, duplicate active asset assignments, SLA flags, and terminated users with active access.
- Repeatability tests and a source manifest.

## Known limitations / next improvements

- This is a CSV-first starter, not a production HR system.
- Extend validation to cover every lifecycle transition and normalize task dependencies into a bridge table.
- Add SQLite tables and constraints; include a richer approval workflow and explicit revocation tasks for every terminated employee.
- Add precision/recall/F1 evaluation by matching detected issues to ground truth.
- The current dashboard is intentionally deferred until the core generator and validation work reliably.

## AI-use disclosure

This project was developed with AI assistance. The candidate should maintain a truthful record of all prompts used across AI tools in `prompts/AI_PROMPT_HISTORY.md`, review and test generated code, and update this disclosure to accurately describe their own work. Do not claim to have manually written code that was AI-generated.

## Data provenance

All records are synthetic and generated locally. No real employee information or external dataset is used.
