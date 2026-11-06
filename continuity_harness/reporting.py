"""English and French Passports from one fresh structured assessment.

Rendering is deliberately not verification: no database, artifact, historical
Passport or authority file is read by this module. The caller supplies the
fresh result and the metadata used for that result. Missing values stay unknown.
"""

from __future__ import annotations

from decimal import Decimal
import html
import os
from pathlib import Path
import re
import shlex

from .schema import ERROR_MESSAGES, HarnessError, canonical, digest
from .verifier import REASONS


TEXT = {
    "title": ("CONTINUITY Ω Harness v0.1 — Continuity Passport", "CONTINUITÉ Ω — Banc d’essai et de vérification v0.1 — Passeport de continuité"),
    "scope": ("Local software execution · synthetic business data", "Exécution logicielle locale · données commerciales synthétiques"),
    "opening": ("This Passport presents the supplied fresh assessment. It is a saved report of that assessment; use the verification command below to inspect the current evidence again.", "Ce Passeport présente l’évaluation fraîche fournie. Il en constitue un rapport enregistré ; utiliser la commande ci-dessous pour examiner de nouveau les preuves actuelles."),
    "local_limit": ("A completed artifact is a durable local JSON software output. It is not printed goods, customer acceptance, a real supplier reservation, revenue, or external certification.", "Un artefact terminé est une sortie logicielle JSON locale durable. Il ne constitue ni bien imprimé, ni acceptation client, ni réservation réelle de fournisseur, ni revenu, ni certification externe."),
    "unknown": ("NOT RECORDED / UNKNOWN", "NON CONSIGNÉ / INCONNU"),
    "yes": ("Yes", "Oui"),
    "no": ("No", "Non"),
    "none": ("None recorded.", "Aucun élément consigné."),
    "field": ("Field", "Champ"),
    "value": ("Recorded value", "Valeur consignée"),
    "assessment": ("Assessment", "Évaluation"),
    "challenge": ("Challenge and assessment subject", "Épreuve et objet de l’évaluation"),
    "challenge_claim": ("Declared checker or procedure claim", "Affirmation déclarée sur le vérificateur ou la procédure"),
    "challenge_note": ("The outer assertion, target verdict and claim status assess the named checker or procedure property. Per-obligation outcomes, totals and underlying claim status reproduce the independent reference assessment of the exact challenged evidence. A test that successfully exposes a defective checker does not qualify that checker. TARGET_RESULT.json and REFERENCE_RESULT.json remain distinct records.", "L’assertion, le verdict cible et l’état de l’affirmation externes évaluent la propriété nommée du vérificateur ou de la procédure. Les résultats par obligation, les totaux et l’état de l’affirmation sous-jacente reproduisent l’évaluation de référence indépendante des preuves exactement éprouvées. Un test qui révèle correctement un vérificateur défectueux ne qualifie pas celui-ci. TARGET_RESULT.json et REFERENCE_RESULT.json restent des enregistrements distincts."),
    "challenge_obligations": ("These obligation facts are the reference verifier's assessment, not the tested checker's claimed verdict.", "Ces faits par obligation proviennent du vérificateur de référence, pas du verdict déclaré par le vérificateur éprouvé."),
    "challenge_resources_note": ("Execution resources below belong to the recorded source execution. If resource_origin is COPIED_POSITIVE_CONTROL_EXECUTION, those observations are reused evidence, not another measured execution to add to a total. The challenge's fresh verification durations are recorded separately; they do not establish a comparative performance advantage.", "Les ressources d’exécution ci-dessous appartiennent à l’exécution source consignée. Si resource_origin vaut COPIED_POSITIVE_CONTROL_EXECUTION, ces observations sont des preuves réutilisées, pas une autre exécution mesurée à additionner. Les durées de vérification fraîche de l’épreuve sont consignées séparément ; elles n’établissent pas d’avantage comparatif de performance."),
    "assessment_note": ("Test behavior, target output, evidence stage, and the business claim are separate. A correctly refused request can satisfy a safety test while leaving an obligation unfulfilled. A passing test that exposes a false acceptance does not qualify the defective checker.", "Le comportement du test, la sortie du composant, le stade des preuves et l’affirmation métier sont distincts. Un refus correct peut satisfaire un test de sûreté tout en laissant une obligation inexécutée. Un test réussi révélant une acceptation indue ne qualifie pas le vérificateur défectueux."),
    "obligations": ("Per-obligation outcomes", "Résultats par obligation"),
    "no_obligations": ("No per-obligation evidence was recorded. This does not demonstrate that there were no obligations.", "Aucune preuve par obligation n’a été consignée. Cela ne démontre pas l’absence d’obligations."),
    "order": ("Order", "Commande"),
    "recipient": ("Recipient", "Destinataire"),
    "expected": ("Required units", "Unités requises"),
    "observed": ("Observed units", "Unités observées"),
    "accepted": ("Accepted units", "Unités acceptées"),
    "outcome": ("Outcome", "Résultat"),
    "route": ("Route", "Voie"),
    "reason": ("Reason", "Motif"),
    "reasons": ("Recorded reasons", "Motifs consignés"),
    "totals": ("Totals for the retained promise", "Totaux de la promesse conservée"),
    "failures": ("Observed failures", "Échecs observés"),
    "unresolved": ("Unresolved evidence and claims", "Preuves et affirmations non résolues"),
    "code": ("Machine code", "Code technique"),
    "explanation": ("Explanation", "Explication"),
    "detail": ("Original technical detail", "Diagnostic technique original"),
    "conditions": ("Frozen conditions", "Conditions figées"),
    "clock_note": ("Ticks are controller-owned logical schedule positions, not measured hours. Milliseconds and nanoseconds below refer to monotonic local measurements. Durable completion uses the trusted post-export observation as a conservative upper bound, distinct from the producer's precommit transition timestamp. Observation delay can reject a late bound even if persistence actually occurred earlier. The configured wall deadline and recovery objective are acceptance limits, not achieved durations.", "Les unités logiques appartiennent au calendrier du contrôleur ; ce ne sont pas des heures mesurées. Les millisecondes et nanosecondes ci-dessous représentent des mesures locales monotones. L’achèvement durable utilise l’observation de confiance après export comme borne supérieure prudente, distincte de l’horodatage de transition du producteur avant validation. Un retard d’observation peut faire rejeter une borne tardive même si la persistance a eu lieu plus tôt. L’échéance réelle et l’objectif de reprise configurés sont des limites d’acceptation, pas des durées atteintes."),
    "faults": ("Fault schedule and observations", "Calendrier des pannes et observations"),
    "action": ("Action", "Action"),
    "target": ("Target", "Cible"),
    "seen": ("Observed", "Observé"),
    "fault_note": ("The complete event and intervention record is in controller.json. A listed schedule is not evidence that its faults occurred; the observed column records exact matches in the supplied controller record.", "Le journal complet des événements et interventions se trouve dans controller.json. Un calendrier ne prouve pas à lui seul que les pannes ont eu lieu ; la colonne d’observation indique les correspondances exactes dans l’enregistrement fourni du contrôleur."),
    "extra_faults": ("Additional observed fault records", "Enregistrements supplémentaires de pannes observées"),
    "resources": ("Measurements and accounting gaps", "Mesures et lacunes comptables"),
    "resources_note": ("Wall time is measured for the controller's local execution interval. Child and controller CPU values are separate process-usage deltas where recorded. Verification/reporting CPU and development work are not included. Storage is the measured run content before final controller/report files and suite-index metadata, excluding separately retained authority. Broker requests count candidate requests; internal controller operations remain in the event record. Zero human interventions concerns this autonomous run only.", "Le temps réel mesure l’intervalle d’exécution locale du contrôleur. Les valeurs processeur des enfants et du contrôleur sont des différences distinctes d’utilisation des processus lorsqu’elles sont consignées. Le processeur de vérification/rapport et le développement n’y sont pas inclus. Le stockage mesure le contenu de l’exécution avant les fichiers finaux de contrôle/rapport et les métadonnées d’index, sans l’autorité conservée séparément. Les demandes au relais comptent celles du candidat ; les opérations internes du contrôleur restent dans le journal. Zéro intervention humaine ne concerne que cette exécution autonome."),
    "cost_note": ("Preparation and integration labor, unmeasured memory use, monetary rates, and complete business costs remain unknown when not recorded. The configured currency and budget are fixture inputs, not measured spending or a customer's budget. No price or savings is inferred. One bounded observation per method and fixture does not establish a stable performance advantage.", "Le travail de préparation et d’intégration, la mémoire non mesurée, les taux monétaires et les coûts commerciaux complets restent inconnus lorsqu’ils ne sont pas consignés. La devise et le budget configurés sont des données du cas synthétique, pas des dépenses mesurées ni un budget client. Aucun prix ni économie n’est déduit. Une observation bornée par méthode et par cas n’établit pas un avantage stable de performance."),
    "versions": ("Identity, versions, and environment", "Identité, versions et environnement"),
    "sources": ("Implementation source identities", "Identités des sources d’implémentation"),
    "path": ("Path", "Chemin"),
    "evidence": ("Current evidence identities", "Identités des preuves actuelles"),
    "evidence_note": ("The verifier compares current file bytes with the separately retained execution seal. These hashes identify bytes; they do not authenticate a real customer instruction or prove real-world completeness.", "Le vérificateur compare les octets actuels au sceau d’exécution conservé séparément. Ces empreintes identifient des octets ; elles n’authentifient pas une instruction client réelle et ne prouvent pas la complétude du monde réel."),
    "commands": ("Fresh verification and recorded commands", "Vérification fraîche et commandes consignées"),
    "command_note": ("Run from the recorded implementation checkout. Supply the independently retained reference pin from the suite index; do not derive a replacement pin from candidate-controlled data. Verification does not overwrite this saved Passport.", "Exécuter depuis la copie de l’implémentation consignée. Fournir l’empreinte de référence conservée indépendamment dans l’index de la suite ; ne pas la remplacer par une valeur dérivée des données candidates. La vérification n’écrase pas ce Passeport enregistré."),
    "command_missing": ("The run path, authority path, or independently retained pin is missing, so no complete verification command can be reconstructed.", "Le chemin de l’exécution, celui de l’autorité ou l’empreinte conservée séparément manque ; il est impossible de reconstruire une commande complète de vérification."),
    "recorded_commands": ("Other commands recorded for this execution", "Autres commandes consignées pour cette exécution"),
    "trust": ("Trust assumptions and remaining limits", "Hypothèses de confiance et limites restantes"),
    "trust_note": ("The host, controller, authored journal, local services, clock, and acceptance verifier are trusted within the declared failure model. Shipped candidate code and imports are trusted before seccomp activation; no arbitrary third-party plugin is supported. The candidate receives bounded data after filtering and performs effects only through the allowlisted broker. This does not protect against a malicious host administrator.", "L’hôte, le contrôleur, le journal rédigé, les services locaux, l’horloge et le vérificateur d’acceptation sont de confiance dans le modèle de panne déclaré. Le code candidat fourni et ses imports sont de confiance avant l’activation de seccomp ; aucun module tiers arbitraire n’est pris en charge. Le candidat reçoit des données bornées après filtrage et agit uniquement par le relais autorisé. Cela ne protège pas contre un administrateur malveillant de l’hôte."),
    "scope_note": ("Source identity, custody, completeness, and byte integrity are different properties. A finite set of local tests is not a general proof, universal exactly-once delivery, independent external certification, or commercial validation. A synthetic transfer establishes only the measured transfer under its recorded conditions.", "L’identité, la garde, la complétude des sources et l’intégrité des octets sont des propriétés différentes. Des tests locaux finis ne constituent ni preuve générale, ni garantie universelle d’exécution exactement une fois, ni certification externe indépendante, ni validation commerciale. Un transfert synthétique n’établit que le transfert mesuré dans les conditions consignées."),
    "ai_note": ("No AI performance is established by an unavailable model, a mock, or a recorded response. The AI arm is NOT RUN unless an actual authorized local capability was executed and measured.", "Un modèle indisponible, un substitut ou une réponse enregistrée n’établissent aucune performance d’IA. Le groupe IA est NON EXÉCUTÉ à moins qu’une véritable capacité locale autorisée ait été exécutée et mesurée."),
    "related": ("Structured records: [RESULT.json](RESULT.json) · [controller.json](controller.json). Both language Passports are derived from the same structured result.", "Enregistrements structurés : [RESULT.json](RESULT.json) · [controller.json](controller.json). Les deux Passeports linguistiques dérivent du même résultat structuré."),
    "challenge_related": ("Structured records: [CHALLENGE.json](CHALLENGE.json) · [TARGET_RESULT.json](TARGET_RESULT.json) · [REFERENCE_RESULT.json](REFERENCE_RESULT.json) · [controller.json](run/controller.json). Both language Passports are derived from the same outer challenge record; the target and reference assessments remain separate.", "Enregistrements structurés : [CHALLENGE.json](CHALLENGE.json) · [TARGET_RESULT.json](TARGET_RESULT.json) · [REFERENCE_RESULT.json](REFERENCE_RESULT.json) · [controller.json](run/controller.json). Les deux Passeports linguistiques dérivent du même enregistrement externe de l’épreuve ; les évaluations cible et de référence restent distinctes."),
}

LABELS = {
    "test_assertion": ("Test assertion", "Assertion du test"),
    "target_verdict": ("Target verdict", "Verdict du composant testé"),
    "evidence_stage": ("Evidence stage", "Stade des preuves"),
    "claim_status": ("Complete-promise claim", "Affirmation sur la promesse complète"),
    "safety_status": ("Safety within the tested model", "Sûreté dans le modèle testé"),
    "authority_status": ("Authority binding", "Liaison à l’autorité"),
    "verification_status": ("Fresh verification status", "État de la vérification fraîche"),
    "all_obligations_completed": ("Every obligation completed", "Toutes les obligations terminées"),
    "commercial_value": ("Commercial value", "Valeur commerciale"),
    "real_customer_authenticity": ("Authenticity of real customer instructions", "Authenticité d’instructions clients réelles"),
    "product": ("Product", "Produit"),
    "spec_sha256": ("Final specification SHA-256", "SHA-256 de la spécification finale"),
    "deadline_tick": ("Logical deadline (ticks)", "Échéance logique (unités)"),
    "completed_tick": ("Completion position (ticks)", "Position d’achèvement (unités)"),
    "completion_ns": ("Durable completion observed no later than", "Achèvement durable observé au plus tard après"),
    "transition_ns": ("Producer transition before commit (elapsed)", "Transition du producteur avant validation (durée écoulée)"),
    "durable_observed_monotonic_ns": ("Post-export monotonic observation (ns)", "Observation monotone après export (ns)"),
    "challenge_id": ("Challenge identifier", "Identifiant de l’épreuve"),
    "assessment_subject": ("Assessed component", "Composant évalué"),
    "claim": ("Declared claim", "Affirmation déclarée"),
    "expected_observation": ("Expected observation", "Observation attendue"),
    "actual_observation": ("Recorded observation", "Observation consignée"),
    "underlying_claim_status": ("Reference full-promise claim", "Affirmation de référence sur la promesse complète"),
    "target_result_path": ("Tested component's assessment record", "Enregistrement de l’évaluation du composant éprouvé"),
    "reference_result_path": ("Independent reference assessment record", "Enregistrement de l’évaluation indépendante de référence"),
    "source_evidence_path": ("Source execution evidence", "Preuves de l’exécution source"),
    "mutation": ("Deliberate mutation configuration", "Configuration de la mutation délibérée"),
    "resource_origin": ("Origin of execution-resource observations", "Origine des observations de ressources d’exécution"),
    "reference_verification_wall_ns": ("Measured reference-verification duration", "Durée mesurée de vérification de référence"),
    "additional_target_verification_wall_ns": ("Additional target-verification duration", "Durée supplémentaire de vérification du composant éprouvé"),
    "challenge_wall_ns_before_report": ("Measured challenge duration before reporting", "Durée mesurée de l’épreuve avant rapport"),
    "expected_obligations": ("Required obligations", "Obligations requises"),
    "accepted_obligations": ("Accepted obligations", "Obligations acceptées"),
    "expected_units": ("Required units", "Unités requises"),
    "observed_units": ("Observed output units", "Unités de sortie observées"),
    "accepted_units": ("Accepted units", "Unités acceptées"),
    "missing_units": ("Units not accepted", "Unités non acceptées"),
    "late_obligations": ("Late obligations", "Obligations tardives"),
    "incorrect_obligations": ("Incorrect obligations", "Obligations incorrectes"),
    "duplicate_obligations": ("Duplicated obligations", "Obligations dupliquées"),
    "unsupported_obligations": ("Unsupported completed obligations", "Obligations terminées sans justification"),
    "contract_id": ("Contract identifier", "Identifiant du contrat"),
    "schema": ("Contract schema", "Schéma du contrat"),
    "mode": ("Declared exercise mode", "Mode d’exercice déclaré"),
    "version": ("Contract version", "Version du contrat"),
    "source_sha256": ("Source events SHA-256", "SHA-256 des événements sources"),
    "cutoff_sequence": ("Source observation cutoff", "Borne d’observation de la source"),
    "source_complete": ("Authored source-completeness declaration", "Déclaration de complétude de la source rédigée"),
    "wall_deadline_ms": ("Configured wall deadline (ms)", "Échéance réelle configurée (ms)"),
    "recovery_objective_ms": ("Configured recovery objective (ms)", "Objectif de reprise configuré (ms)"),
    "window": ("Capacity window [start, end)", "Fenêtre de capacité [début, fin)"),
    "lease_ticks": ("Reservation lease (ticks)", "Durée de réservation (unités logiques)"),
    "capacities": ("Declared route capacities (units)", "Capacités déclarées des voies (unités)"),
    "allowed_routes": ("Allowed routes", "Voies autorisées"),
    "permissions": ("Declared permissions", "Permissions déclarées"),
    "dependencies": ("Declared route dependencies", "Dépendances déclarées des voies"),
    "blocked_dependencies": ("Unavailable dependencies", "Dépendances indisponibles"),
    "currency": ("Configured fixture currency", "Devise configurée du cas synthétique"),
    "budget_minor": ("Configured fixture budget (minor units)", "Budget configuré du cas synthétique (unités mineures)"),
    "comparison": ("Frozen comparison conditions", "Conditions figées de comparaison"),
    "wall_ns": ("Measured execution wall time", "Durée réelle d’exécution mesurée"),
    "cpu_user_ns": ("Observed child CPU: user", "Processeur des enfants observé : utilisateur"),
    "cpu_system_ns": ("Observed child CPU: system", "Processeur des enfants observé : système"),
    "controller_cpu_user_ns": ("Observed controller CPU: user", "Processeur du contrôleur observé : utilisateur"),
    "controller_cpu_system_ns": ("Observed controller CPU: system", "Processeur du contrôleur observé : système"),
    "peak_rss_bytes": ("Peak resident memory (bytes)", "Mémoire résidente maximale (octets)"),
    "storage_bytes": ("Measured run storage before final reports (bytes)", "Stockage mesuré avant rapports finaux (octets)"),
    "requests": ("Candidate broker requests", "Demandes du candidat au relais"),
    "retries": ("Recorded retries", "Nouvelles tentatives consignées"),
    "worker_restarts": ("Recorded worker restarts", "Redémarrages de processus consignés"),
    "human_interventions": ("Human interventions during this run", "Interventions humaines pendant cette exécution"),
    "preparation_labor_seconds": ("Recorded preparation labor (seconds)", "Travail de préparation consigné (secondes)"),
    "integration_labor_seconds": ("Recorded integration labor (seconds)", "Travail d’intégration consigné (secondes)"),
    "monetary_cost": ("Complete monetary cost", "Coût monétaire complet"),
    "recovery_ms": ("Measured recovery/readiness time (ms)", "Durée mesurée de reprise/préparation (ms)"),
    "run_id": ("Run identifier", "Identifiant de l’exécution"),
    "method": ("Candidate method", "Méthode candidate"),
    "scenario": ("Scenario", "Scénario"),
    "seed": ("Recorded seed", "Graine consignée"),
    "state": ("Controller state", "État du contrôleur"),
    "started_utc": ("Execution start (UTC)", "Début d’exécution (UTC)"),
    "contract_sha256": ("Retained contract SHA-256", "SHA-256 du contrat conservé"),
    "reference_sha256": ("Observed reference SHA-256", "SHA-256 de la référence observée"),
    "reference_pin_sha256": ("Independently supplied reference pin", "Empreinte de référence fournie indépendamment"),
    "result_sha256": ("Canonical structured-result SHA-256", "SHA-256 du résultat structuré canonique"),
    "verifier_version": ("Fresh verifier version", "Version du vérificateur frais"),
    "verification_schema": ("Verification-result schema", "Schéma du résultat de vérification"),
    "reference_schema": ("Retained-reference schema", "Schéma de la référence conservée"),
    "implementation_version": ("Implementation version", "Version de l’implémentation"),
    "git_commit": ("Recorded Git commit", "Commit Git consigné"),
    "dirty": ("Working tree had uncommitted changes", "Arbre de travail avec modifications non commises"),
    "python": ("Recorded Python runtime", "Environnement Python consigné"),
    "platform": ("Recorded platform and kernel", "Plateforme et noyau consignés"),
    "sqlite_version": ("Recorded SQLite version", "Version de SQLite consignée"),
    "working_directory": ("Recorded working directory", "Répertoire de travail consigné"),
    "mechanism": ("Candidate-isolation mechanism", "Mécanisme d’isolement du candidat"),
    "applied": ("Isolation applied", "Isolement appliqué"),
    "probe": ("Isolation probe observations", "Observations des tests d’isolement"),
    "trust_scope": ("Declared trust scope", "Périmètre de confiance déclaré"),
    "max_simultaneous_allocated": ("Maximum simultaneous allocation by route", "Allocation simultanée maximale par voie"),
    "history_transitions": ("Verified durable history transitions", "Transitions durables vérifiées"),
    "primary_recovery_verified": ("Primary reconstruction verified", "Reconstruction principale vérifiée"),
}

VALUES = {
    "PASS": ("Expected test behavior observed", "Comportement attendu du test observé"),
    "PASSED": ("Expected test behavior observed", "Comportement attendu du test observé"),
    "FAIL": ("Expected test behavior not observed", "Comportement attendu du test non observé"),
    "FAILED": ("Failed", "Échec"),
    "DEMONSTRATED": ("Demonstrated within the declared stage", "Démontré dans le stade déclaré"),
    "NOT_ESTABLISHED": ("Not established", "Non établi"),
    "NOT_EVALUATED": ("Not evaluated", "Non évalué"),
    "NOT_RUN": ("Not run", "Non exécuté"),
    "UNKNOWN": ("Unknown", "Inconnu"),
    "COMPLETE": ("Completed record", "Enregistrement terminé"),
    "COMPLETED": ("Completed", "Terminé"),
    "INCOMPLETE": ("Incomplete", "Incomplet"),
    "ERROR": ("Execution or verification error", "Erreur d’exécution ou de vérification"),
    "PARTIAL": ("Partial result", "Résultat partiel"),
    "REFUSED": ("Refused", "Refusé"),
    "UNFULFILLED": ("Unfulfilled", "Inexécuté"),
    "UNRESOLVED": ("Unresolved", "Non résolu"),
    "LATE": ("Late", "Tardif"),
    "INCORRECT": ("Incorrect", "Incorrect"),
    "LOCAL_SOFTWARE_EXECUTION": ("Local software execution with synthetic data", "Exécution logicielle locale avec données synthétiques"),
    "VERIFICATION_ATTEMPT": ("Verification attempted; local execution evidence not established", "Vérification tentée ; preuve d’exécution locale non établie"),
    "NO_EXECUTION_EVIDENCE": ("No established local execution evidence", "Aucune preuve établie d’exécution locale"),
    "FRESH_VERIFICATION_CHALLENGE": ("Fresh verification of deliberately challenged evidence", "Vérification fraîche de preuves délibérément éprouvées"),
    "CHECKER_MUTATION_EXERCISE": ("Deliberately mutated checker exercise", "Exercice avec vérificateur délibérément modifié"),
    "CANDIDATE_PROCEDURE": ("Candidate procedure", "Procédure candidate"),
    "FRESH_VERIFIER": ("Fresh acceptance verifier", "Vérificateur d’acceptation fraîche"),
    "MUTATED_VERIFIER": ("Deliberately mutated verifier", "Vérificateur délibérément modifié"),
    "NEW_LOCAL_EXECUTION": ("New local execution for this case", "Nouvelle exécution locale pour ce cas"),
    "COPIED_POSITIVE_CONTROL_EXECUTION": ("Reused observations from the positive control", "Observations réutilisées du contrôle positif"),
    "conventional": ("Competent conventional procedure", "Procédure conventionnelle compétente"),
    "harness": ("Harness-supported procedure", "Procédure accompagnée par le banc d’essai"),
    "ablation": ("Separately labeled safeguard ablation", "Ablation distincte d’une protection"),
    "ai": ("AI-assisted procedure", "Procédure assistée par IA"),
    "recovery": ("Feasible primary recovery", "Reprise principale réalisable"),
    "alternate": ("Feasible alternate fulfillment", "Exécution de remplacement réalisable"),
    "constrained": ("Constrained disruption and recovery", "Perturbation contrainte et reprise"),
    "primary": ("Primary route", "Voie principale"),
    "backup": ("Backup route", "Voie de secours"),
}

EXTRA_REASONS = {
    "CHECKPOINT_BUSY": ("An active reader prevents a complete database checkpoint; the exercise cannot be finalized.", "Un lecteur actif empêche l’intégration complète du journal ; l’exercice ne peut être finalisé."),
    "DATABASE_CHECKPOINT_INCOMPLETE": ("The database did not confirm complete checkpointing.", "La base de données n’a pas confirmé l’intégration complète de son journal."),
    "DATABASE_STATE_NOT_CAPTURED": ("The final live service state was not captured before shutdown.", "L’état final du service actif n’a pas été capturé avant son arrêt."),
    "DATABASE_STATE_CHANGED_DURING_FINALIZATION": ("The finalized database differs from the service's captured final state.", "La base finalisée diffère de l’état final capturé du service."),
    "DATABASE_SNAPSHOT_TIMEOUT": ("Creating the standalone evidence database exceeded its time limit.", "La création de la base de preuve autonome a dépassé sa limite de temps."),
    "DATABASE_SNAPSHOT_INVALID": ("The standalone evidence database failed its integrity check.", "Le contrôle d’intégrité de la base de preuve autonome a échoué."),
    "DATABASE_SNAPSHOT_MISMATCH": ("The evidence database does not match the committed source view.", "La base de preuve ne correspond pas à la vue source engagée."),
    "DATABASE_SNAPSHOT_JOURNAL_MODE": ("The evidence database could not leave write-ahead journal mode.", "La base de preuve n’a pas pu quitter le mode de journalisation anticipée."),
    "DATABASE_SNAPSHOT_SIDECAR": ("A journal or shared-memory file accompanies the evidence database.", "Un journal ou un fichier de mémoire partagée accompagne la base de preuve."),
    "DATABASE_FINALIZATION_ERROR": ("Database evidence finalization did not complete.", "La finalisation des preuves de la base de données n’a pas abouti."),
    "WORKER_STILL_RUNNING": ("An owned process is still running; evidence cannot be finalized.", "Un processus appartenant à l’exercice est encore actif ; les preuves ne peuvent être finalisées."),
    "WORKER_EXIT_UNEXPECTED": ("An owned process exited unexpectedly before evidence finalization.", "Un processus de l’exercice s’est arrêté de manière inattendue avant la finalisation des preuves."),
    "RECONCILIATION_INCOMPLETE": ("Durable receipt reconciliation did not produce complete consistent artifacts.", "Le rapprochement des reçus durables n’a pas produit de pièces complètes et cohérentes."),
    "LOCAL_AI_UNAVAILABLE": ("No suitable authorized local model was executed; AI performance was not measured.", "Aucun modèle local approprié et autorisé n’a été exécuté ; la performance d’IA n’a pas été mesurée."),
    "ROUTE_UNAVAILABLE": ("The requested route is unavailable.", "La voie demandée est indisponible."),
    "DEPENDENCY_UNAVAILABLE": ("The route uses an unavailable declared dependency.", "La voie utilise une dépendance déclarée indisponible."),
    "PERMISSION_MISSING": ("Required activation or sharing permission is absent.", "Une permission requise d’activation ou de partage est absente."),
    "RESERVATION_EXPIRED": ("The uncommitted reservation expired before the requested action.", "La réservation non engagée a expiré avant l’action demandée."),
    "RESERVATION_RELEASED": ("The reservation was released; no new fulfillment was authorized by this request.", "La réservation a été libérée ; cette demande n’autorise aucune nouvelle réalisation."),
    "RESERVATION_NOT_FOUND": ("The requested reservation does not exist.", "La réservation demandée n’existe pas."),
    "IDEMPOTENCY_CONFLICT": ("The stable key was reused for a different request.", "La clé stable a été réutilisée pour une demande différente."),
    "UNAUTHORIZED_OBLIGATION": ("The request differs from the obligation admitted by the service.", "La demande diffère de l’obligation admise par le service."),
    "COMMIT_REQUIRED": ("A reservation must be committed before fulfillment.", "Une réservation doit être engagée avant sa réalisation."),
    "OBLIGATION_IN_FLIGHT": ("Another active allocation already covers this obligation.", "Une autre allocation active couvre déjà cette obligation."),
    "DEADLINE_EXCEEDED": ("The requested action is beyond its declared deadline.", "L’action demandée dépasse son échéance déclarée."),
    "OUTSIDE_WINDOW": ("The action is outside the authorized capacity window.", "L’action se situe hors de la fenêtre de capacité autorisée."),
    "CAPACITY_ENCUMBERED": ("Capacity cannot be reduced below existing allocations.", "La capacité ne peut être réduite sous les allocations existantes."),
    "PROCESS_TIMEOUT": ("A local process did not respond within the configured limit.", "Un processus local n’a pas répondu dans la limite configurée."),
    "PROCESS_EXITED": ("A local process exited before completing its response.", "Un processus local s’est arrêté avant de terminer sa réponse."),
    "BROKER_OPERATION_FORBIDDEN": ("The requested broker operation is not permitted.", "L’opération demandée au relais n’est pas autorisée."),
    "RECOVERY_RECONCILIATION_MISMATCH": ("The recovered service state differs from the candidate's source replay.", "L’état rétabli du service diffère du rejeu des sources par le candidat."),
    "SERVICE_ERROR": ("The local service operation did not complete.", "L’opération du service local n’a pas abouti."),
    "CONTROLLER_ERROR": ("The controller did not complete the exercise.", "Le contrôleur n’a pas terminé l’exercice."),
}

FAULTS = {
    "PRIMARY_UNAVAILABLE": ("Primary route disabled", "Voie principale désactivée"),
    "CONCURRENT_FINAL_CAPACITY": ("Concurrent competition for final capacity", "Concurrence sur la capacité restante"),
    "ACK_LOST_AFTER_DURABLE_FULFILLMENT": ("Acknowledgment lost after durable fulfillment", "Accusé perdu après réalisation durable"),
    "RETRY_WHILE_OUTCOME_UNKNOWN": ("Retry while the original outcome remains unknown", "Nouvelle tentative pendant l’incertitude du résultat initial"),
    "SERVICE_KILLED_AFTER_COMMIT": ("Service process terminated after commit", "Processus de service arrêté après validation"),
    "CANDIDATE_KILLED_AFTER_REQUEST": ("Candidate process terminated after its request", "Processus candidat arrêté après sa demande"),
    "RESTART_RECONCILIATION": ("Restart and reconcile durable state", "Redémarrer et rapprocher l’état durable"),
}


def _language(language):
    if language not in ("en", "fr"):
        raise HarnessError("UNSUPPORTED_LANGUAGE", str(language))
    return 1 if language == "fr" else 0


def _text(key, language):
    return TEXT[key][_language(language)]


def _cell(value, language):
    if value is None:
        return _text("unknown", language)
    if type(value) is bool:
        return _text("yes" if value else "no", language)
    if type(value) in (dict, list):
        value = canonical(value).decode("utf-8")
    return html.escape(str(value), quote=False).replace("|", "\\|").replace("`", "&#96;").replace("\r", "\\r").replace("\n", "\\n")


def _value(value, language):
    pair = VALUES.get(value) if isinstance(value, str) else None
    if pair:
        return "`" + _cell(value, language) + "` — " + pair[_language(language)]
    return _cell(value, language)


def _label(key, language):
    pair = LABELS.get(key)
    return pair[_language(language)] if pair else _cell(key, language)


def _table(headers, rows):
    return ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"] + ["| " + " | ".join(row) + " |" for row in rows]


def _pairs(values, language, enum_keys=()):
    return _table([_text("field", language), _text("value", language)],
                  [[_label(key, language), _value(value, language) if key in enum_keys else _cell(value, language)] for key, value in values])


def _duration(value, language):
    if type(value) is not int:
        return _cell(None, language)
    milliseconds = format(Decimal(value) / Decimal(1_000_000), ".3f")
    if language == "fr":
        milliseconds = milliseconds.replace(".", ",")
    return f"{milliseconds} ms ({value} ns)"


def _reason(code, language, *, refused=False):
    if refused and code == "CAPACITY_EXCEEDED":
        return ("Refused: insufficient remaining capacity; no excess allocation is implied.",
                "Refus : capacité restante insuffisante ; aucune surallocation n’est déduite.")[_language(language)]
    pair = REASONS.get(code) or EXTRA_REASONS.get(code) or ERROR_MESSAGES.get(code)
    if pair:
        return pair[_language(language)]
    return ("Recorded technical diagnostic; inspect the bound event record.",
            "Diagnostic technique consigné ; consulter le journal d’événements associé.")[_language(language)]


def _diagnostic_rows(items, language):
    rows = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            rows.append([_cell(None, language), _cell(None, language), _cell(item, language), _cell(None, language)])
            continue
        code = item.get("code")
        detail = item.get("detail")
        if isinstance(detail, dict) and language in detail:
            detail = detail[language]
        rows.append(["`" + _cell(code, language) + "`", _reason(code, language), _cell(item.get("order_id"), language), _cell(detail, language)])
    return rows


def _fenced_command(command):
    longest = max((len(x) for x in re.findall(r"`+", command)), default=0)
    fence = "`" * max(3, longest + 1)
    return [fence + "sh", command, fence]


def render_passport(result, controller, reference_info, language="en"):
    """Render supplied facts without reading evidence or inferring success."""
    _language(language)
    if not all(isinstance(value, dict) for value in (result, controller, reference_info)):
        raise HarnessError("INVALID_REPORT_INPUT", "result/controller/reference_info")
    # This also rejects noncanonical numbers or unsupported values before output.
    result_hash = digest(result)
    assessment = result.get("assessment") or {}
    contract = reference_info.get("contract") or {}
    reference = reference_info.get("reference") or {}
    implementation = controller.get("implementation") or {}
    environment = implementation.get("environment") or {}
    isolation = controller.get("isolation") or {}
    challenge = result.get("challenge") if isinstance(result.get("challenge"), dict) else None
    lines = ["# " + _text("title", language), "",
             "[English](PASSPORT.en.md) · [Français](PASSPORT.fr.md)", "",
             "**" + _text("scope", language) + "**", "", _text("opening", language), "", _text("local_limit", language), ""]
    if challenge:
        title = challenge.get("title")
        lines += ["## " + _text("challenge", language), ""]
        if isinstance(title, dict):
            lines += ["**" + _cell(title.get(language), language) + "**", ""]
        challenge_rows = [("challenge_id", challenge.get("id")), ("assessment_subject", challenge.get("assessment_subject"))]
        for key in ("claim", "expected_observation", "actual_observation"):
            value = challenge.get(key)
            challenge_rows.append((key, value.get(language) if isinstance(value, dict) else value))
        challenge_rows += [(key, challenge.get(key)) for key in ("underlying_claim_status", "target_result_path", "reference_result_path", "source_evidence_path")]
        lines += _pairs(challenge_rows, language, ("assessment_subject", "underlying_claim_status"))
        if challenge.get("mutation") is not None:
            lines += ["", "**" + _label("mutation", language) + ":** " + _cell(challenge["mutation"], language)]
        lines += ["", _text("challenge_note", language), ""]
    lines += ["## " + _text("assessment", language), ""]
    summary = [(key, assessment.get(key)) for key in ("test_assertion", "target_verdict", "evidence_stage", "claim_status")]
    summary += [(key, result.get(key)) for key in ("safety_status", "authority_status", "verification_status", "all_obligations_completed", "commercial_value", "real_customer_authenticity")]
    summary_rows = [[_text("challenge_claim", language) if key == "claim_status" and challenge else _label(key, language),
                     _cell(value, language) if key == "all_obligations_completed" else _value(value, language)] for key, value in summary]
    lines += _table([_text("field", language), _text("value", language)], summary_rows)
    lines += ["", _text("assessment_note", language), "", "## " + _text("obligations", language), ""]
    if challenge:
        lines += [_text("challenge_obligations", language), ""]
    obligations = result.get("per_obligation")
    if isinstance(obligations, list) and obligations:
        rows = [[_cell(item.get("order_id"), language), _cell(item.get("recipient"), language),
                 _cell(item.get("expected_quantity"), language), _cell(item.get("observed_quantity"), language),
                 _cell(item.get("accepted_quantity"), language), _value(item.get("outcome"), language), _value(item.get("route"), language)] for item in obligations]
        lines += _table([_text(k, language) for k in ("order", "recipient", "expected", "observed", "accepted", "outcome", "route")], rows)
        for item in obligations:
            lines += ["", "### " + _text("order", language) + " `" + _cell(item.get("order_id"), language) + "`", ""]
            lines += _pairs([(key, item.get(key)) for key in ("product", "spec_sha256", "deadline_tick", "completed_tick", "durable_observed_monotonic_ns")], language)
            lines += ["", "**" + _label("completion_ns", language) + ":** " + _duration(item.get("completion_ns"), language), "",
                      "**" + _label("transition_ns", language) + ":** " + _duration(item.get("transition_ns"), language), "",
                      "**" + _text("reasons", language) + ":**"]
            reasons = item.get("reason_codes")
            if isinstance(reasons, list) and reasons:
                lines += [""] + ["- `" + _cell(code, language) + "`: " + _reason(code, language, refused=item.get("outcome") == "REFUSED") for code in reasons]
            else:
                lines += ["", _text("none", language)]
    else:
        lines += [_text("no_obligations", language)]
    lines += ["", "## " + _text("totals", language), ""]
    totals = result.get("totals") or {}
    lines += _pairs([(key, totals.get(key)) for key in ("expected_obligations", "accepted_obligations", "expected_units", "observed_units", "accepted_units", "missing_units", "late_obligations", "incorrect_obligations", "duplicate_obligations", "unsupported_obligations")], language)
    for heading in ("failures", "unresolved"):
        lines += ["", "## " + _text(heading, language), ""]
        rows = _diagnostic_rows(result.get(heading), language)
        lines += _table([_text(k, language) for k in ("code", "explanation", "order", "detail")], rows) if rows else [_text("none", language)]
    lines += ["", "## " + _text("conditions", language), ""]
    lines += _pairs([(key, contract.get(key)) for key in ("contract_id", "schema", "version", "mode", "source_sha256", "cutoff_sequence", "source_complete", "deadline_tick", "wall_deadline_ms", "recovery_objective_ms", "window", "lease_ticks", "capacities", "allowed_routes", "permissions", "dependencies", "blocked_dependencies", "currency", "budget_minor", "comparison")], language)
    lines += ["", _text("clock_note", language), "", "## " + _text("faults", language), ""]
    schedule = controller.get("fault_schedule")
    observations = controller.get("faults_observed")
    observed = observations if isinstance(observations, list) else []
    if isinstance(schedule, list) and schedule:
        rows = []
        for event in schedule:
            code = event.get("event")
            explanation = FAULTS.get(code, (str(code), str(code)))[_language(language)]
            rows.append(["`" + _cell(code, language) + "` — " + explanation,
                         _cell(event.get("action"), language), _cell(event.get("target"), language),
                         _cell(event in observed if isinstance(observations, list) else None, language)])
        lines += _table([_text(k, language) for k in ("code", "action", "target", "seen")], rows)
    else:
        lines += [_text("none", language) if isinstance(schedule, list) else _text("unknown", language)]
    if isinstance(schedule, list):
        extra = [item for item in observed if item not in schedule]
        if extra:
            lines += ["", "**" + _text("extra_faults", language) + ":** " + _cell(extra, language)]
    lines += ["", _text("fault_note", language), ""]
    error_rows = _diagnostic_rows(controller.get("errors"), language)
    if error_rows:
        lines += _table([_text(k, language) for k in ("code", "explanation", "order", "detail")], error_rows) + [""]
    lines += ["## " + _text("resources", language), ""]
    if challenge:
        lines += _pairs([("resource_origin", result.get("resource_origin"))], language, ("resource_origin",))
        measurements = result.get("measurements") or {}
        lines += [""] + _table([_text("field", language), _text("value", language)],
                    [[_label(key, language), _duration(measurements.get(key), language)] for key in (
                        "reference_verification_wall_ns", "additional_target_verification_wall_ns", "challenge_wall_ns_before_report")])
        lines += ["", _text("challenge_resources_note", language), ""]
    resources = result.get("resources") if isinstance(result.get("resources"), dict) else controller.get("resources") or {}
    rows = []
    for key in ("wall_ns", "cpu_user_ns", "cpu_system_ns", "controller_cpu_user_ns", "controller_cpu_system_ns", "peak_rss_bytes", "storage_bytes", "requests", "retries", "worker_restarts", "human_interventions", "preparation_labor_seconds", "integration_labor_seconds", "monetary_cost"):
        value = resources.get(key)
        rows.append([_label(key, language), _duration(value, language) if key.endswith("_ns") else _cell(value, language)])
    rows.append([_label("recovery_ms", language), _cell(result.get("recovery_ms"), language)])
    lines += _table([_text("field", language), _text("value", language)], rows)
    lines += ["", _text("resources_note", language), "", _text("cost_note", language), ""]
    ledger = result.get("ledger") or {}
    lines += _pairs([(key, ledger.get(key)) for key in ("max_simultaneous_allocated", "history_transitions", "primary_recovery_verified")], language)
    lines += ["", "## " + _text("versions", language), ""]
    version_rows = [(key, controller.get(key)) for key in ("run_id", "method", "scenario", "seed", "state", "started_utc")]
    version_rows += [(key, result.get(key)) for key in ("contract_sha256", "reference_sha256", "verifier_version")]
    version_rows += [("verification_schema", result.get("schema")), ("reference_schema", reference.get("schema"))]
    version_rows += [("reference_pin_sha256", reference_info.get("reference_sha256"))]
    version_rows += [("result_sha256", result_hash), ("implementation_version", implementation.get("version"))]
    version_rows += [(key, implementation.get(key)) for key in ("git_commit", "dirty")]
    version_rows += [(key, environment.get(key)) for key in ("python", "platform", "sqlite_version", "working_directory")]
    lines += _pairs(version_rows, language, ("method", "scenario", "state"))
    lines += ["", "### " + _text("sources", language), ""]
    sources = implementation.get("source_sha256")
    lines += _table([_text("path", language), "SHA-256"], [[_cell(k, language), "`" + _cell(v, language) + "`"] for k, v in sorted(sources.items())]) if isinstance(sources, dict) and sources else [_text("unknown", language)]
    lines += ["", "## " + _text("evidence", language), ""]
    hashes = result.get("evidence_sha256")
    lines += _table([_text("path", language), "SHA-256"], [[_cell(k, language), "`" + _cell(v, language) + "`"] for k, v in sorted(hashes.items())]) if isinstance(hashes, dict) and hashes else [_text("unknown", language)]
    lines += ["", _text("evidence_note", language), "", "## " + _text("commands", language), ""]
    run_path, authority_path, pin = (reference_info.get(key) for key in ("run_dir", "authority_dir", "reference_sha256"))
    if all(isinstance(value, (str, Path)) and str(value) for value in (run_path, authority_path, pin)):
        command = shlex.join(["python3", "-m", "continuity_harness", "--language", language, "verify", "--run", str(run_path), "--authority", str(authority_path), "--reference-sha256", str(pin)])
        lines += _fenced_command(command)
    else:
        lines += [_text("command_missing", language)]
    lines += ["", _text("command_note", language)]
    commands = reference_info.get("commands")
    if isinstance(commands, list) and commands:
        lines += ["", "### " + _text("recorded_commands", language), ""]
        for command in commands:
            if isinstance(command, list) and all(isinstance(x, str) for x in command):
                lines += _fenced_command(shlex.join(command)) + [""]
            elif isinstance(command, str):
                lines += _fenced_command(command) + [""]
    lines += ["", "## " + _text("trust", language), ""]
    lines += _pairs([(key, isolation.get(key)) for key in ("mechanism", "applied", "probe")] + [("trust_scope", result.get("trust_scope"))], language)
    lines += ["", _text("trust_note", language), "", _text("scope_note", language), "", _text("ai_note", language), "", _text("challenge_related" if challenge else "related", language), ""]
    return "\n".join(lines)


def write_reports(run_dir, result, controller, reference_info):
    """Write new language files only, retaining any existing report untouched."""
    root = Path(run_dir).absolute()
    if not root.is_dir() or any(p.is_symlink() for p in (root, *root.parents)):
        raise HarnessError("UNSAFE_PATH", str(root))
    outputs = {language: root / f"PASSPORT.{language}.md" for language in ("en", "fr")}
    if any(path.exists() or path.is_symlink() for path in outputs.values()):
        raise HarnessError("OUTPUT_EXISTS", "PASSPORT.en.md/PASSPORT.fr.md")
    rendered = {language: render_passport(result, controller, reference_info, language) for language in outputs}
    for language, path in outputs.items():
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(rendered[language])
            stream.flush()
            os.fsync(stream.fileno())
    return {language: str(path) for language, path in outputs.items()}
