# Injection de prompt dans une chaîne d'agents : propagation et moniteur de canal

Projet pour le Swarm Alignment Hackathon (Apart Research, nov. 2026). Petite expérience reproductible, **entièrement simulée** : données fictives, outils factices, aucun compte réel ni aucune action externe.

- Question de recherche, critique, travaux proches et hypothèses pré-enregistrées : [`docs/research_plan.md`](docs/research_plan.md)
- Plan du rapport : [`docs/report_outline.md`](docs/report_outline.md)
- Annexe sur le double usage : [`docs/dual_use_appendix.md`](docs/dual_use_appendix.md)
- **Résultats** : [`docs/results.md`](docs/results.md) ; figure de synthèse `results/overview.png`
- Pré-enregistrements et amendements : `docs/research_plan.md` §5 et §8 à §13 ; relecture des transcriptions : `docs/transcript_audit.csv`

## Installation

```bash
pip install -r requirements.txt
python tests/test_pipeline.py        # tests du harnais (sans clé API)
# versions exactes utilisées : requirements-lock.txt
```

## Exécution

```bash
# 1) Test du pipeline, sans clé API. Chiffres SYNTHÉTIQUES, pas des résultats.
python run_experiment.py --backend mock --trials 30 --out results/mock_smoke
python analyze.py results/mock_smoke

# 2) Pilote avec un vrai modèle (ANTHROPIC_API_KEY requis), voir la règle du pilote dans le plan, §5
python run_experiment.py --backend anthropic --model claude-opus-5-5 \
    --conditions replicating_none --trials 5 --out results/pilot

# 3) Plan principal 2x2 (estimez d'abord le coût à partir des tokens du pilote)
python run_experiment.py --backend anthropic --model claude-opus-5-5 --trials 30 --workers 4 --out results/main
python analyze.py results/main
```

Options : `--protocol native` (appels d'outils natifs), `--topology board` (tableau partagé), `--monitor-backend/--monitor-model`. Conditions `<injection>_<moniteur>`, avec l'injection parmi `benign`, `replicating`, `direct`, `polite`, `monitor_bypass` et `sanitizer_bypass`, et le moniteur parmi `none`, `keyword`, `llm`, `sanitize` et `inputsanitize`.

`--dry-run` affiche le nombre d'épisodes restants. Une relance avec le même `--out` reprend là où l'exécution s'était arrêtée.

## Structure

| Fichier | Rôle |
|---|---|
| `pi_swarm/world.py` | Environnement fictif, injection, outils simulés, étiquettes de vérité terrain |
| `pi_swarm/episode.py` | Chaîne de 4 agents, protocole d'actions JSON, moniteur (`none`/`keyword`/`llm`), métriques par épisode |
| `pi_swarm/backends.py` | Backends Anthropic, OpenAI/Mistral (API compatible) et `mock` (tests uniquement) |
| `run_experiment.py` | Conditions × essais, ordre aléatoire, journal JSONL, reprise après interruption |
| `analyze.py` | Tableaux (IC de Wilson, test exact de Fisher, IC de Newcombe), échec silencieux, figures ; plusieurs exécutions regroupables avec `--out` |
| `scripts/final_analysis.sh` | Régénère toutes les synthèses et `results/overview.png` |
| `scripts/audit_*.py` | Tirage et grille de la relecture des transcriptions |

## Journaux

`results/<run>/episodes.jsonl` contient une ligne par épisode : configuration (modèle, graine, commit), **tous** les appels LLM avec leur texte, les appels d'outils, les messages entre agents avec le verdict du moniteur, et le résumé des métriques. `config.json` enregistre les arguments, le commit git et l'environnement.

## Honnêteté des résultats

Les journaux produits avec `--backend mock` sont marqués `backend: "mock"`. `analyze.py` affiche alors un avertissement dans le tableau et sur les figures. Ces chiffres proviennent de probabilités fixées à la main et ne disent **rien** du comportement réel des LLM.

## Reproduire les résultats rapportés

```bash
# clés : MISTRAL_API_KEY et OPENAI_API_KEY (dans la session cloud, elles sont injectées par le proxy)
python run_experiment.py --backend mistral --model mistral-small-2603 --trials 30 --workers 6 --seed 1 --out results/main_mistral-small-2603
python run_experiment.py --backend mistral --model mistral-small-2603 --monitor-backend openai --monitor-model gpt-5.4-mini \
    --conditions benign_llm replicating_llm --trials 30 --workers 4 --seed 2 --out results/xmonitor_gpt-5.4-mini
python run_experiment.py --backend mistral --model mistral-small-2603 --conditions benign_sanitize replicating_sanitize \
    --trials 30 --workers 4 --seed 3 --out results/explore_sanitize_mistral-small-2603
python analyze.py results/main_mistral-small-2603 results/xmonitor_gpt-5.4-mini results/explore_sanitize_mistral-small-2603 --out results/combined
```
Les sorties des LLM ne sont pas déterministes : une nouvelle exécution donnera des chiffres proches, pas identiques.
