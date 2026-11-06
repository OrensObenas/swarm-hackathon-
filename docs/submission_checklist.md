# Liste de contrôle de soumission — rien n'a été soumis ni publié

Échéance : **lundi 9 nov. 2026, 11 h 59 UTC** (= dim. 8 nov., 23 h 59 AoE). La soumission se fait par le formulaire de la page officielle du hackathon, pas par e-mail.

## À faire par l'auteur (je ne peux pas le faire à votre place)
- [x] **Auteur et affiliation** : Gilbert Obenas, chercheur indépendant (renseigné).
- [ ] **Kit de vérification** : suivre `docs/verification_kit.md` (recomptage indépendant, 23 épisodes complets à lire, grille de relecture, références, horodatage du pré-enregistrement).
- [ ] **Relecture humaine des transcriptions** : vérifier quelques lignes de `docs/transcript_audit.csv`, puis remplacer la phrase marquée `[AUTHOR: …]` dans §4.3.
- [ ] **Confirmer la responsabilité** : remplacer `[AUTHOR: confirm]` dans l'annexe D.
- [ ] **Modèle officiel** : copier le contenu de `docs/report/report.md` dans le modèle Apart (titre, auteurs, résumé, sections, références, annexes), insérer `results/overview.png` comme figure 1, puis exporter en PDF. `report_preview.pdf` n'est **qu'un aperçu** et ne suit pas la mise en page officielle.
- [ ] **Vérifier dans le PDF final** :
  - corps ≤ 8 pages (hors références et annexes ; dans l'aperçu, les références commencent page 8, donc le corps est à la limite : à revérifier dans le modèle officiel) ;
  - résumé de 150 à 250 mots (environ 237 actuellement) ;
  - annexe intitulée exactement « Limitations and Dual-Use / Ethical Considerations ».
- [ ] **Lien du code** (champ du formulaire) : décider si le dépôt `OrensObenas/swarm-hackathon-` doit être rendu public, ou fournir un autre lien. **Je n'ai rien changé à sa visibilité.** Avant de le publier, relire `results/` : les journaux contiennent les textes d'injection (voir l'annexe A.2).
- [ ] *(Optionnel)* Vidéo de démonstration de 3 à 5 minutes.
- [ ] **Soumettre**, puis vérifier l'e-mail de confirmation (titre et PDF). En cas de problème : sprints@apartresearch.com.

## Champs du formulaire, brouillons à relire
- **Titre** : Stopping the Attack, Breaking the Task: Silent Failures and Recovery in Monitored Multi-Agent Pipelines
- **Tracks** : Science of agent networks & failure propagation ; Multi-agent oversight & control
- **Résumé** : section *Abstract* de `docs/report/report.md` (généré à partir des journaux).
- **Code** : [à décider]

## Points vérifiés de mon côté
- Tous les chiffres du rapport sont générés par `scripts/report_numbers.py` à partir des journaux. Une balise inconnue bloque la construction.
- Les 12 références ont été vérifiées par recherche web le 7 nov. 2026 (auteurs, année, identifiant arXiv ou lieu de publication). Pour G-Safeguard, seul « Wang et al. » est donné, car je n'ai pas vérifié la liste complète des auteurs.
- Le rapport ne présente comme exécutées que des expériences réellement lancées. Les pistes non testées (attaques adaptatives, autres modèles et tâches) sont signalées comme futures ou non testées.
