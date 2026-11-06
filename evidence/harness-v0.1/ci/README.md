# Publication CI history / Historique CI de publication

## English

At publication head `56a8526649993bb6d839de2d65825e884ded8f6e`, both push workflows and the pull-request Harness workflow passed. The first pull-request repository-validation attempt failed one of 245 tests: the unchanged website script's 1,000 ms Node VM initialization watchdog expired before the interaction assertions. All Harness tests passed in that attempt. The cause of the timeout is **NOT ESTABLISHED**.

Only the failed job was rerun, with the same head and no code, timeout or assertion changes. Its second attempt passed all 245 tests in 17.492 seconds, then passed historical publication validation and companion packaging. This later success does not erase or explain the first failure. The original website tests and `docs/research/` were unchanged from the starting commit.

| Observation | Job | Result | Retained decoded log |
| --- | --- | --- | --- |
| PR validation, attempt 1 | `128148628696` | FAILED: 245 tests, one VM watchdog timeout; 22.478 seconds | [Original failure](pr-validation-attempt-1.log) |
| Same job rerun, attempt 2 | `128150823875` | PASSED: 245 tests, no skips; 17.492 seconds; remaining publication checks passed | [Successful rerun](pr-validation-attempt-2.log) |

Both jobs belong to [workflow run 42292323812](https://github.com/MontrealAI/CONTINUITY/actions/runs/42292323812). The failing CI runtime reported Node.js v22.23.4. An unchanged targeted local recheck also passed, but its different environment cannot establish the CI cause. These supplemental logs are subsequent publication observations, separate from the immutable experiment archive. They do not change qualified implementation `fa9da1f54acfaa82510a4b6b805c2980d3e5b31d`, the experiment specification, or either experimental attempt.

[Pull request](https://github.com/MontrealAI/CONTINUITY/pull/1) · [Experiment evidence](../README.md) · [Structured CI record](PUBLICATION_CI.json)

## Français

À la révision de publication `56a8526649993bb6d839de2d65825e884ded8f6e`, les deux flux de poussée et le flux du banc d’essai de la demande de fusion ont réussi. La première validation du dépôt sur la demande de fusion a échoué à un des 245 tests : le délai de garde de 1 000 ms à l’initialisation de la machine virtuelle Node du site inchangé a expiré avant les assertions d’interaction. Tous les tests du banc d’essai ont réussi lors de cette tentative. La cause du dépassement reste **NON ÉTABLIE**.

Seule la tâche en échec a été relancée, à révision identique et sans changer le code, le délai ni les assertions. La deuxième tentative a réussi les 245 tests en 17,492 secondes, puis la validation de la publication historique et l’assemblage du compagnon. Cette réussite ultérieure n’efface ni n’explique le premier échec. Les tests du site et `docs/research/` sont restés inchangés depuis la révision initiale.

| Observation | Tâche | Résultat | Journal décodé conservé |
| --- | --- | --- | --- |
| Validation de la demande de fusion, tentative 1 | `128148628696` | ÉCHEC : 245 tests, un dépassement du délai de garde ; 22,478 secondes | [Échec original](pr-validation-attempt-1.log) |
| Relance de la même tâche, tentative 2 | `128150823875` | RÉUSSITE : 245 tests, aucun ignoré ; 17,492 secondes ; contrôles de publication suivants réussis | [Relance réussie](pr-validation-attempt-2.log) |

Les deux tâches appartiennent au [flux 42292323812](https://github.com/MontrealAI/CONTINUITY/actions/runs/42292323812). L’environnement CI en échec indiquait Node.js v22.23.4. Une vérification locale ciblée inchangée a également réussi, mais son environnement différent ne permet pas d’établir la cause CI. Ces journaux supplémentaires sont des observations de publication postérieures, séparées de l’archive immuable de l’expérience. Ils ne modifient ni l’implémentation qualifiée `fa9da1f54acfaa82510a4b6b805c2980d3e5b31d`, ni la spécification, ni les deux tentatives expérimentales.

Les journaux bruts conservent la langue originale des outils ; les résultats et leur interprétation figurent intégralement dans les deux langues ci-dessus.

[Demande de fusion](https://github.com/MontrealAI/CONTINUITY/pull/1) · [Preuves de l’expérience](../README.md) · [Enregistrement CI structuré](PUBLICATION_CI.json)
