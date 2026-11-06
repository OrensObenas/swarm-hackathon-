# Annexe (brouillon) : risques de double usage

**Ce qui pourrait servir à un attaquant**
- Le texte d'injection de `pi_swarm/world.py` et le harnais, qui permet de mesurer le taux de succès d'une attaque, pourraient en principe servir à **optimiser** des injections contre de vrais systèmes multi-agents.
- Les résultats indiquent aussi ce que ne couvre pas un moniteur de canal : le patient zéro est détourné directement. Cette information est utile aux défenseurs comme aux attaquants.

**Pourquoi nous jugeons le risque faible**
- Le motif d'attaque (fausse consigne de « compliance » et consigne de copie mot pour mot) est déjà largement décrit dans la littérature publique (voir la section Travaux proches). Nous n'apportons aucune technique nouvelle de contournement.
- Aucune optimisation adaptative des attaques : un seul texte fixe, écrit à la main, sans recherche automatique de la formulation la plus efficace.
- L'environnement est entièrement simulé : données fictives, domaine réservé `.example`, outil `send_email` qui écrit seulement en mémoire. Aucun compte réel, aucun réseau sortant hormis les appels au fournisseur du LLM.
- La charge utile est banale (exfiltration de notes internes fictives). Aucun contenu dangereux en soi.

**Mesures de publication**
- Le dépôt publie le moniteur, les métriques et les journaux. Ces éléments servent surtout la défense.
- Nous ne publions pas de variantes d'injection optimisées pour un modèle précis. Si une variante s'avérait nettement plus efficace pendant l'expérience, nous la décririons qualitativement sans donner le texte exact.
- Limite : un moniteur LLM est lui-même injectable. Nous recommandons de ne pas présenter nos résultats comme une garantie de sécurité.

**Bilan** : le bénéfice pour la défense (mesurer ce qu'un moniteur de canal arrête ou non) nous paraît supérieur au gain marginal pour un attaquant.
