# Exécutions exclues

- `board_concurrent_duplicate/` : premier lancement du lot T. Une boucle d'attente et un lancement manuel ont tourné **en même temps** sur le même dossier : 236 lignes pour 120 épisodes uniques. Le choix de la version à garder dépendrait de l'ordre de fin des épisodes, donc ces données sont exclues. Le lot a été relancé proprement, avec la même graine, dans `results/board_mistral-small-2603`.
  Pour la transparence, l'analyse du fichier dédoublonné (dernière écriture conservée) donnait, en `replicating` : sans moniteur 12/30 détournements en aval ; blocage 0/30 (tâche 2/30) ; nettoyage 0/30 (tâche 30/30). Ces chiffres n'ont pas été utilisés.
