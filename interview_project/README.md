## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with your API keys.

## Run UI

```bash
streamlit run app.py
```

## Run CLI

```bash
python run_cli.py --case case_1_breast_straightforward --max-iterations 4
python run_cli.py --case case_2_lung_ambiguous_pathology --max-iterations 4
python run_cli.py --case case_3_colon_pathology_changes_plan --max-iterations 4 --no-evaluator
```

