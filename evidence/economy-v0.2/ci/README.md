# CI evidence / Preuves de CI

## English

The broad validation workflow at source `3494becbbfaf15ae571a71df05a49b9ce982cc84`, run [42310192424](https://github.com/MontrealAI/CONTINUITY/actions/runs/42310192424), failed one of 424 tests before its intended production race. The original log and job metadata are retained here. The economy workflow and historical Harness workflow at that source both passed.

A bounded local investigation reproduced the startup failure on attempt 6: the initial snapshot received `id=null`, `SERVICE_START_FAILED`, causing `RPC_ID_MISMATCH`. The generic response does not identify the precise SQLite or OS statement. Both workers had been started against a new schema before either was ready.

The test-only correction establishes the first worker’s snapshot readiness before starting the second. Both producer and receiver tests then execute their unchanged concurrent operations, deterministic hooks and assertions. There are no sleeps, no runtime changes and no retry-until-pass gate. The product suite passed 33 tests; 20 bounded paired repetitions passed all 40 races. The before/after sources, exact diff, response and logs are in [worker-readiness](worker-readiness/).

All 42 frozen implementation/interface/documentation files remain identical. These controls establish concurrent operations on initialized services. Concurrent initialization of a brand-new shared schema remains unqualified. This later CI evidence is a sidecar to the already sealed experiment archive; it is not removed from the review package or retroactively described as a passing first CI attempt.

## Français

La validation générale à la source `3494becbbfaf15ae571a71df05a49b9ce982cc84`, exécution [42310192424](https://github.com/MontrealAI/CONTINUITY/actions/runs/42310192424), a échoué sur un test parmi 424 avant la course de production prévue. Le journal original et les métadonnées sont conservés ici. Les workflows économique et du banc historique ont tous deux réussi à cette source.

Une investigation locale bornée a reproduit l’échec au sixième essai : le premier instantané recevait `id=null`, `SERVICE_START_FAILED`, provoquant `RPC_ID_MISMATCH`. La réponse générique n’identifie pas l’instruction SQLite ou système précise. Les deux processus avaient été lancés sur un nouveau schéma avant qu’un seul soit prêt.

La correction du test attend l’instantané de disponibilité du premier processus avant de lancer le second. Les deux tests exécutent ensuite leurs opérations concurrentes, points de transition et assertions inchangés. Aucune attente arbitraire, modification d’exécution ni répétition jusqu’à réussite n’a été ajoutée. Les 33 tests du produit ont réussi ; 20 répétitions bornées par paire ont réussi les 40 courses. Sources avant/après, différence exacte, réponse et journaux sont dans [worker-readiness](worker-readiness/).

Les 42 fichiers figés d’implémentation/interfaces/documentation restent identiques. Les contrôles établissent les opérations concurrentes de services initialisés. L’initialisation concurrente d’un tout nouveau schéma partagé reste non qualifiée. Ces preuves CI ultérieures accompagnent séparément l’archive déjà scellée ; elles ne sont ni supprimées du dossier ni présentées rétroactivement comme une première CI réussie.
