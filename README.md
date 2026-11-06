# Injection de prompt dans une chaîne d'agents : propagation et moniteur de canal

Projet pour le Swarm Alignment Hackathon (Apart Research, nov. 2026). Petite expérience reproductible, **entièrement simulée** : données fictives, outils factices, aucun compte réel ni aucune action externe.

- Question de recherche, critique, travaux proches et hypothèses pré-enregistrées : [`docs/research_plan.md`](docs/research_plan.md)
- Plan du rapport : [`docs/report_outline.md`](docs/report_outline.md)
- Annexe sur le double usage : [`docs/dual_use_appendix.md`](docs/dual_use_appendix.md)

## Installation

```bash
pip install -r requirements.txt
python tests/test_pipeline.py        # tests du harnais (sans clé API)
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

`--dry-run` affiche le nombre d'épisodes restants. Une relance avec le même `--out` reprend là où l'exécution s'était arrêtée.

## Structure

| Fichier | Rôle |
|---|---|
| `pi_swarm/world.py` | Environnement fictif, injection, outils simulés, étiquettes de vérité terrain |
| `pi_swarm/episode.py` | Chaîne de 4 agents, protocole d'actions JSON, moniteur (`none`/`keyword`/`llm`), métriques par épisode |
| `pi_swarm/backends.py` | Backend Anthropic (SDK officiel) et backend `mock` (tests uniquement) |
| `run_experiment.py` | Conditions × essais, ordre aléatoire, journal JSONL, reprise après interruption |
| `analyze.py` | Tableaux (IC de Wilson, test exact de Fisher) et figures |

## Journaux

`results/<run>/episodes.jsonl` contient une ligne par épisode : configuration (modèle, graine, commit), **tous** les appels LLM avec leur texte, les appels d'outils, les messages entre agents avec le verdict du moniteur, et le résumé des métriques. `config.json` enregistre les arguments, le commit git et l'environnement.

## Honnêteté des résultats

Les journaux produits avec `--backend mock` sont marqués `backend: "mock"`. `analyze.py` affiche alors un avertissement dans le tableau et sur les figures. Ces chiffres proviennent de probabilités fixées à la main et ne disent **rien** du comportement réel des LLM.
