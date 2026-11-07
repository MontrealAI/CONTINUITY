"""Full English/French Passports from one structured fresh-verification record.

Human explanations are localized; stable codes, literal product data, exact
commands and original diagnostics stay literal. Reporting never verifies or
upgrades a verdict. Replaced Passports are retained in passport-history/.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile

from continuity_harness.schema import HarnessError, canonical, digest

BT = chr(96)
TEXT = {
 "title": ("CONTINUITY Ω Harness — Economy of continuity", "CONTINUITÉ Ω — Économie de la continuité"),
 "subtitle": ("Digital-product experiment · version 0.2.0", "Expérience de produit numérique · version 0.2.0"),
 "promise": ("Preserve a promise through a viable, voluntarily accepted continuity arrangement.", "Préserver un engagement grâce à une solution de continuité viable et volontairement acceptée."),
 "boundary": ("Scope: disposable local processes and a specified digital product. Authored synthetic policies, consent, values, funding and SMU cash flows are model inputs and observations. They do not establish real contracts, demand, payments, sales, printed goods, rendered appearance or print quality.",
              "Portée : processus locaux jetables et produit numérique spécifié. Les politiques, consentements, valeurs, financements et flux SMU synthétiques sont des hypothèses et observations du modèle. Ils n’établissent ni contrats réels, ni demande, paiements, ventes, biens imprimés, apparence rendue ou qualité d’impression."),
 "fresh": ("This Passport presents the recorded assessment. Fresh verification must inspect retained authority, actual durable output and recipient evidence; this document is never its oracle.",
           "Ce passeport présente l’évaluation consignée. Une vérification fraîche doit inspecter l’autorité conservée, le résultat durable réel et les preuves du destinataire ; ce document ne constitue jamais son oracle."),
 "model": ("Model only: monetary amounts are exact synthetic minor units; 100 minor units equal 1 fictional SMU. Values are displayed without rescaling. Economic constraints and value intervals are authored assumptions. A positive modeled margin or policy decision does not establish real voluntary demand, payment or commercial advantage.",
           "Modèle uniquement : les montants sont des unités mineures synthétiques exactes ; 100 unités mineures valent 1 SMU fictive. Les valeurs sont affichées sans changement d’échelle. Les contraintes économiques et intervalles de valeur sont des hypothèses définies pour l’exercice. Une marge ou décision favorable dans le modèle n’établit ni demande volontaire réelle, ni paiement, ni avantage commercial."),
 "claims": ("Three distinct claims", "Trois affirmations distinctes"),
 "claim": ("Claim", "Affirmation"), "status": ("Recorded status", "État consigné"),
 "outcome": ("Required digital work accepted within the frozen conditions", "Travail numérique requis accepté dans les conditions figées"),
 "service_feasibility": ("Service feasibility under the authored synthetic model", "Faisabilité du service selon le modèle synthétique défini"),
 "method_advantage": ("Method advantage over competent alternatives", "Avantage de méthode face à des solutions compétentes"),
 "safety": ("Safety within the exercised failure model", "Sûreté dans le modèle de défaillance éprouvé"),
 "four": ("Assessment fields kept separate", "Champs d’évaluation distincts"),
 "field": ("Field", "Champ"), "value": ("Recorded value", "Valeur consignée"),
 "assertion": ("Test assertion", "Assertion du test"), "target": ("Component verdict", "Verdict du composant"),
 "stage": ("Evidence stage", "Stade de preuve"), "claim_status": ("Assessed claim status", "État de l’affirmation évaluée"),
 "checker_claim": ("Qualification of the challenged checker", "Qualification du vérificateur mis à l’épreuve"),
 "separation": ("A passing test can correctly observe refusal, failure or insufficient evidence. It does not convert partial work into a complete promise. A passing adversarial test can expose a defective checker; its qualification must remain separate.",
                "Un test réussi peut constater correctement un refus, un échec ou des preuves insuffisantes. Il ne transforme pas un travail partiel en engagement complet. Un test contradictoire réussi peut révéler un vérificateur défectueux ; sa qualification doit rester distincte."),
 "identity": ("Identity, authority and versions", "Identité, autorité et versions"),
 "obligations": ("Per-obligation execution and acceptance", "Exécution et acceptation par obligation"),
 "obligation": ("Obligation", "Obligation"), "recipient": ("Recipient", "Destinataire"), "revision": ("Revision", "Révision"),
 "required": ("Required", "Requis"), "produced": ("Produced", "Produit"), "received": ("Received", "Reçu"),
 "rejected": ("Rejected", "Refusé"), "accepted": ("Accepted within contract", "Accepté selon le contrat"), "outcome_short": ("Outcome", "Résultat"),
 "quantity_note": ("Counts describe the recorded stage. Rejected and corrected attempts remain distinct. A produced or received unit is not automatically accepted. Missing measurements are not displayed as zero.",
                   "Les quantités décrivent le stade consigné. Les tentatives refusées et corrigées restent distinctes. Une unité produite ou reçue n’est pas automatiquement acceptée. Les mesures absentes ne sont pas présentées comme nulles."),
 "arrangements": ("Proposals, modeled decisions and arrangements", "Propositions, décisions modélisées et solutions"),
 "arrangement": ("Arrangement", "Solution"),
 "no_arrangements": ("No arrangement record is present. This absence is not evidence of an accepted or economically viable deal.",
                     "Aucun enregistrement de solution n’est présent. Cette absence ne prouve ni accord accepté ni viabilité économique."),
 "accounting": ("Modeled transfers, costs, liabilities and outside options", "Transferts, coûts, responsabilités et options externes modélisés"),
 "partial_liabilities": ("Recipient acceptance has accrued under an active arrangement. Partial settlement is unsupported in this version: the agreement, remaining escrow and liabilities remain recorded pending an authorized resolution. No cancellation, complete payment, released funding or complete promise is implied by the accepted subset.",
                        "Une acceptation du destinataire est acquise dans une solution active. Cette version ne prend pas en charge un règlement partiel : l’accord, le séquestre restant et les responsabilités restent consignés en attente d’une résolution autorisée. Le sous-ensemble accepté n’implique ni annulation, ni paiement complet, ni libération des fonds, ni engagement entièrement réalisé."),
 "resources": ("Measured resources and accounting gaps", "Ressources mesurées et lacunes de comptabilisation"),
 "resource_note": ("Measured process resources and configured synthetic amounts have different meanings. Unrecorded preparation, integration, adaptation, verification or intervention effort remains unknown. Missing categories cannot support a complete-cost or cheaper-method conclusion.",
                   "Les ressources de processus mesurées et les montants synthétiques configurés ont des significations différentes. Les efforts de préparation, d’intégration, d’adaptation, de vérification ou d’intervention non consignés restent inconnus. Les catégories absentes ne permettent aucune conclusion de coût complet ou de méthode moins coûteuse."),
 "failures": ("Observed failures and counterexamples", "Échecs et contre-exemples observés"),
 "unresolved": ("Missing evidence and unresolved claims", "Preuves absentes et affirmations non établies"),
 "none_failures": ("No failure entry was recorded in this assessment. This is bounded evidence, not a general proof.", "Aucune entrée d’échec n’a été consignée dans cette évaluation. Il s’agit de preuves bornées, non d’une démonstration générale."),
 "none_unresolved": ("No additional unresolved entry was recorded. Scope and unknown-cost limits still apply.", "Aucune entrée non résolue supplémentaire n’a été consignée. Les limites de portée et de coûts inconnus restent applicables."),
 "code": ("Stable code", "Code stable"), "scope": ("Scope", "Portée"), "locator": ("Original technical locator", "Repère technique original"),
 "explanation": ("Interpretation", "Interprétation"),
 "contradiction": ("The verifier recorded a contradiction for this check. Read the code and retained evidence before interpreting the component verdict.",
                   "Le vérificateur a consigné une contradiction pour ce contrôle. Lire le code et les preuves conservées avant d’interpréter le verdict du composant."),
 "missing": ("Required evidence or measurement is missing; a favorable claim is not established by this entry.",
             "Une preuve ou mesure requise manque ; cette entrée n’établit pas une affirmation favorable."),
 "evidence": ("Evidence references and byte integrity", "Références des preuves et intégrité des octets"),
 "hash_note": ("Hashes identify bytes. They do not authenticate real customer instructions, establish source completeness, or replace an externally retained reference pin.",
               "Les empreintes identifient les octets. Elles n’authentifient pas les instructions réelles d’un client, n’établissent pas l’exhaustivité des sources et ne remplacent pas une empreinte de référence conservée séparément."),
 "context": ("Recorded execution, faults, commands and provenance", "Exécution, pannes, commandes et provenance consignées"),
 "context_note": ("Stable identifiers, exact commands, paths and original machine diagnostics are retained literally. They are data, not additional acceptance evidence. Source and host trust remain explicit in the architecture and threat model.",
                  "Les identifiants stables, commandes exactes, chemins et diagnostics machine originaux sont conservés littéralement. Ce sont des données, non des preuves d’acceptation supplémentaires. La confiance dans les sources et l’hôte est explicitée dans l’architecture et le modèle de menace."),
 "challenge": ("Adversarial observation and checker qualification", "Observation contradictoire et qualification du vérificateur"),
 "failed_checker": ("Checker qualification FAILED. A favorable target verdict in this adversarial observation is a challenged component claim, not qualified acceptance.",
                    "Qualification du vérificateur : ÉCHEC. Un verdict favorable du composant dans cette observation contradictoire est une affirmation contestée, non une acceptation qualifiée."),
 "structured": ("Complete structured verification record", "Enregistrement structuré complet de vérification"),
 "structured_note": ("The same structured record generates both language versions. Machine keys, enum codes and literal evidence values remain unchanged; the localized sections above explain their meaning. No saved result is reused as fresh proof.",
                     "Le même enregistrement structuré génère les deux versions linguistiques. Les clés machine, codes d’état et valeurs littérales des preuves restent inchangés ; les sections localisées ci-dessus expliquent leur sens. Aucun résultat sauvegardé n’est réutilisé comme preuve fraîche."),
 "not_recorded": ("Not recorded", "Non consigné"), "empty": ("No entries", "Aucune entrée"),
 "yes": ("Yes", "Oui"), "no": ("No", "Non"),
}
STATUS = {
 "DEMONSTRATED": ("Demonstrated in scope", "Démontré dans la portée déclarée"),
 "FAILED": ("Failed", "Échec"), "NOT_ESTABLISHED": ("Not established", "Non établi"),
 "NOT_RUN": ("Not run", "Non exécuté"), "NOT_EVALUATED": ("Not evaluated", "Non évalué"),
 "PASSED": ("Passed", "Réussi"), "COMPLETE": ("Complete verification", "Vérification complète"),
 "INCOMPLETE": ("Incomplete verification", "Vérification incomplète"), "COMPLETED": ("Completed", "Réalisé"),
 "PARTIAL": ("Partial", "Partiel"), "UNFULFILLED": ("Unfulfilled", "Non réalisé"),
 "UNRESOLVED": ("Unresolved", "Non résolu"), "INCORRECT": ("Incorrect", "Incorrect"), "LATE": ("Late", "Tardif"),
 "ACCEPTED": ("Accepted", "Accepté"), "REJECTED": ("Rejected", "Refusé"), "REFUSED": ("Refused", "Refusé"),
 "RECEIVED": ("Received; acceptance is separate", "Reçu ; l’acceptation est distincte"),
 "MATERIALIZED": ("Materialized; recipient acceptance is separate", "Matérialisé ; l’acceptation du destinataire est distincte"),
 "NO_DEAL": ("No deal", "Aucun accord"), "NO_ACTION": ("No action", "Aucune action"), "NO_PURCHASE": ("No purchase", "Aucun achat"),
 "PROPOSED": ("Proposed", "Proposé"), "SETTLED": ("Settled in the synthetic ledger", "Réglé dans le registre synthétique"),
 "CANCELLED": ("Cancelled", "Annulé"), "ACTIVE": ("Active", "Actif"),
 "TECHNICAL_CONTROL": ("Authorized technical control; no market agreement established", "Contrôle technique autorisé ; aucun accord commercial établi"),
 "MARKET": ("Modeled market arrangement", "Solution de marché modélisée"),
 "LOCAL_DIGITAL_PRODUCT_EXECUTION": ("Local digital-product execution", "Exécution locale d’un produit numérique"),
 "VERIFICATION_ATTEMPT": ("Verification attempt", "Tentative de vérification"),
 "SYNTHETIC_EXERCISE": ("Synthetic exercise authority", "Autorité d’exercice synthétique"),
 "PREPARATION_LABOR_NOT_MEASURED": ("Preparation labor was not measured", "Le travail de préparation n’a pas été mesuré"),
 "INTEGRATION_LABOR_NOT_MEASURED": ("Integration labor was not measured", "Le travail d’intégration n’a pas été mesuré"),
 "ADAPTATION_LABOR_NOT_MEASURED": ("Adaptation labor was not measured", "Le travail d’adaptation n’a pas été mesuré"),
 "MONETARY_RATES_NOT_MEASURED": ("Monetary rates were not measured", "Les tarifs monétaires n’ont pas été mesurés"),
 "PEAK_MEMORY_NOT_MEASURED": ("Peak memory was not measured", "Le pic de mémoire n’a pas été mesuré"),
 "VERIFICATION_CPU_NOT_MEASURED": ("Verification CPU was not measured", "Le temps processeur de vérification n’a pas été mesuré"),
 "NO_AUTHORIZED_LOCAL_AI": ("No suitable authorized local AI capability", "Aucune capacité d’IA locale autorisée appropriée"),
 "NO_AUTHORIZED_LOCAL_AI_CAPABILITY": ("No suitable authorized local AI capability", "Aucune capacité d’IA locale autorisée appropriée"),
 "TRADE": ("Modeled trade agreement", "Accord d’échange modélisé"),
 "TECHNICAL": ("Funded technical control; no trade established", "Contrôle technique financé ; aucune transaction établie"),
 "ERROR": ("Execution error", "Erreur d’exécution"),
 "ESTABLISHED_FOR_SYNTHETIC_EXERCISE": ("Established for the synthetic exercise only", "Établi uniquement pour l’exercice synthétique"),
 "AUTHORED_SYNTHETIC_MODEL": ("Authored synthetic model", "Modèle synthétique défini pour l’exercice"),
 "VERIFICATION_LABOR_NOT_MEASURED": ("Human verification labor was not measured", "Le travail humain de vérification n’a pas été mesuré"),
 "TRUSTED_HOST_KERNEL_CONTROLLER_CLOCK": ("Trusted host, kernel, controller and clock", "Hôte, noyau, contrôleur et horloge de confiance"),
 "TRUSTED_RETAINED_SYNTHETIC_AUTHORITY": ("Trusted retained synthetic authority", "Autorité synthétique conservée de confiance"),
 "SHARED_AUTHORSHIP_NOT_THIRD_PARTY_CERTIFICATION": ("Shared authorship; no third-party certification", "Auteur commun ; aucune certification par un tiers"),
 "SEMANTIC_CONTENT_ONLY_NOT_PHYSICAL_DELIVERY": ("Semantic digital content only; physical delivery is untested", "Contenu numérique sémantique uniquement ; livraison physique non éprouvée"),
 "CANDIDATE_REPORTED": ("Candidate-reported measurement", "Mesure déclarée par le candidat"),
 "SECCOMP_BPF": ("Observed seccomp-BPF process confinement", "Confinement du processus seccomp-BPF observé"),
 "BACKUP_FAIL_BEFORE_RESERVE": ("Backup failure before reservation", "Défaillance du secours avant réservation"),
 "PRODUCTION_CRASH_HALF_WRITE": ("Producer crash during file export", "Arrêt du producteur pendant l’export du fichier"),
 "REJECT_FIRST_CONTENT": ("Incorrect first-attempt content", "Contenu incorrect de première tentative"),
 "ACK_LOST_AFTER_ACCEPTANCE": ("Acknowledgment lost after durable acceptance", "Accusé perdu après acceptation durable"),
 "CANDIDATE_RESTART_AFTER_ACCEPTANCE": ("Candidate restart after acceptance", "Redémarrage du candidat après acceptation"),
 "POLICY_CHANGE_AFTER_PROPOSE": ("Policy change after proposal", "Modification de politique après proposition"),
 "FUNDING_WITHDRAWAL_AFTER_PROPOSE": ("Funding withdrawn after proposal", "Financement retiré après proposition"),
 "CAPACITY_COMPETITION": ("Competing capacity requests", "Demandes concurrentes de capacité"),
 "LATE_ACCEPTANCE": ("Acceptance beyond the declared deadline", "Acceptation au-delà de l’échéance déclarée"),
 "PERMISSION_REVOKE_BEFORE_TRANSFER": ("Permission revoked before transfer", "Permission révoquée avant transfert"),
 "CONSENT_REVOKE_BEFORE_PRODUCTION": ("Consent revoked before production", "Consentement révoqué avant production"),
 "SHARED_DEPENDENCY_FAILURE": ("Shared dependency failure", "Défaillance d’une dépendance commune"),
 "PARTIAL_AGREEMENT_RETAINED": ("Partial agreement retained with unresolved settlement", "Accord partiel conservé avec règlement non résolu"),
 "ACCRUED_ACCEPTANCE": ("Accrued acceptance prevents cancellation and release of liabilities", "L’acceptation acquise interdit l’annulation et la libération des responsabilités"),
 "ACCRUED_ACCEPTANCE_CANCELLED": ("Accrued recipient acceptance was improperly canceled", "Une acceptation acquise du destinataire a été annulée indûment"),
 "PROPOSAL": ("Proposal; no agreement implied", "Proposition ; aucun accord implicite"),
 "EVIDENCE_INTEGRITY_CHALLENGE": ("Evidence integrity challenge", "Épreuve d’intégrité des preuves"),
 "TARGETED_VERIFIER_MUTATION": ("Targeted verifier mutation", "Mutation ciblée du vérificateur"),
 "CHECKER_QUALIFICATION": ("Qualification of the challenged checker", "Qualification du vérificateur mis à l’épreuve"),
 "REGISTERED_SYNTHETIC_CHALLENGE": ("Registered synthetic challenge", "Épreuve synthétique préenregistrée"),
 "NOT_APPLICABLE": ("Not applicable", "Sans objet"),
}
LITERAL_TRANSLATIONS = {
 "controller and child processes; shared-host child CPU may include concurrent exercises": (
     "Controller and child processes; child CPU accounting on a shared host may include concurrent exercises.",
     "Contrôleur et processus enfants ; leur mesure processeur sur un hôte partagé peut inclure des exercices concurrents."),
 "Registered assessment assertion; not a favorable outcome or trade claim.": (
     "Registered assessment assertion; it does not assert a favorable outcome or trade.",
     "Assertion d’évaluation préenregistrée ; elle n’affirme ni résultat favorable ni transaction acceptable."),
}
FIELDS = {
 "schema": ("Schema", "Schéma"), "verifier_version": ("Verifier version", "Version du vérificateur"),
 "run_id": ("Run identity", "Identité de l’exécution"), "contract_id": ("Contract identity", "Identité du contrat"),
 "contract_sha256": ("Retained contract SHA-256", "SHA-256 du contrat conservé"),
 "reference_sha256": ("External reference pin", "Empreinte externe de référence"),
 "authority_status": ("Authority evidence status", "État des preuves d’autorité"),
 "verification_status": ("Verification completion status", "État d’achèvement de la vérification"),
 "commercial_value": ("Real commercial value", "Valeur commerciale réelle"),
 "real_customer_authenticity": ("Real customer authenticity", "Authenticité d’un client réel"),
 "obligation_id": ("Obligation identity", "Identité de l’obligation"), "recipient": ("Recipient", "Destinataire"),
 "revision": ("Revision", "Révision"), "quantity": ("Required quantity", "Quantité requise"),
 "produced_quantity": ("Produced quantity", "Quantité produite"), "received_quantity": ("Received quantity", "Quantité reçue"),
 "rejected_quantity": ("Rejected quantity", "Quantité refusée"), "accepted_quantity": ("Accepted quantity within contract", "Quantité acceptée selon le contrat"),
 "missing_quantity": ("Missing quantity", "Quantité manquante"), "duplicate_quantity": ("Duplicate quantity", "Quantité en double"),
 "incorrect_quantity": ("Incorrect quantity", "Quantité incorrecte"), "late_quantity": ("Late quantity", "Quantité tardive"),
 "unauthorized_quantity": ("Unauthorized quantity", "Quantité non autorisée"),
 "outcome": ("Outcome", "Résultat"), "reason_codes": ("Reason codes", "Codes de justification"),
 "proposal_id": ("Proposal identity", "Identité de la proposition"), "agreement_id": ("Agreement identity", "Identité de l’accord"),
 "arrangement_id": ("Arrangement identity", "Identité de la solution"), "kind": ("Arrangement kind", "Nature de la solution"),
 "status": ("Recorded status", "État consigné"), "proposed_terms": ("Proposed terms", "Conditions proposées"),
 "participant_decisions": ("Separate participant decisions", "Décisions distinctes des participants"),
 "independent_terms": ("Independently checked terms", "Conditions vérifiées indépendamment"),
 "ex_ante_feasibility": ("Modeled feasibility at agreement", "Faisabilité modélisée au moment de l’accord"),
 "realized_feasibility": ("Modeled feasibility after execution", "Faisabilité modélisée après exécution"),
 "costs": ("Recorded costs", "Coûts consignés"), "payments": ("Modeled ledger payments", "Paiements du registre modélisé"),
 "party_id": ("Participant identity", "Identité du participant"), "provider_id": ("Provider identity", "Identité du fournisseur"),
 "role": ("Role", "Rôle"), "verdict": ("Component verdict", "Verdict du composant"),
 "code": ("Stable code", "Code stable"), "tick": ("Logical tick", "Instant logique"),
 "deadline_tick": ("Logical deadline", "Échéance logique"), "wall_deadline_ms": ("Elapsed-time deadline (ms)", "Échéance en temps écoulé (ms)"),
 "start_ns": ("Start clock (ns)", "Horloge de départ (ns)"), "observed_ns": ("Observed clock (ns)", "Horloge observée (ns)"),
 "elapsed_ns": ("Elapsed duration (ns)", "Durée écoulée (ns)"), "wall_ns": ("Wall duration (ns)", "Durée écoulée (ns)"),
 "cpu_user_ns": ("User CPU (ns)", "Processeur utilisateur (ns)"), "cpu_system_ns": ("System CPU (ns)", "Processeur système (ns)"),
 "bytes": ("Bytes", "Octets"), "storage_bytes": ("Recorded storage (bytes)", "Stockage consigné (octets)"),
 "requests": ("Requests", "Requêtes"), "retries": ("Retries", "Nouvelles tentatives"),
 "restarts": ("Process restarts", "Redémarrages de processus"), "human_interventions": ("Human interventions", "Interventions humaines"),
 "buyer_price_minor": ("Buyer price (synthetic SMU minor units)", "Prix acheteur (unités mineures SMU synthétiques)"),
 "pay_minor": ("Provider payment (synthetic SMU minor units)", "Paiement fournisseur (unités mineures SMU synthétiques)"),
 "balance_minor": ("Balance (synthetic SMU minor units)", "Solde (unités mineures SMU synthétiques)"),
 "amount_minor": ("Amount (synthetic SMU minor units)", "Montant (unités mineures SMU synthétiques)"),
 "coordinator_fee_minor": ("Coordinator fee (synthetic SMU minor units)", "Rémunération du coordonnateur (unités mineures SMU synthétiques)"),
 "rework_budget_minor": ("Correction reserve (synthetic SMU minor units)", "Réserve de correction (unités mineures SMU synthétiques)"),
 "cancellation_fee_minor": ("Cancellation liability (synthetic SMU minor units)", "Responsabilité d’annulation (unités mineures SMU synthétiques)"),
 "value_min_minor": ("Authored value lower bound (synthetic SMU minor units)", "Borne inférieure de valeur définie (unités mineures SMU synthétiques)"),
 "value_max_minor": ("Authored value upper bound (synthetic SMU minor units)", "Borne supérieure de valeur définie (unités mineures SMU synthétiques)"),
 "outside_utility_minor": ("Authored outside-option utility (synthetic SMU minor units)", "Utilité d’option externe définie (unités mineures SMU synthétiques)"),
 "outside_profit_minor": ("Authored outside-option profit (synthetic SMU minor units)", "Profit d’option externe défini (unités mineures SMU synthétiques)"),
 "policy_revision": ("Policy revision", "Révision des politiques"), "currency": ("Synthetic accounting unit", "Unité de compte synthétique"),
 "measurement_scope": ("Measurement boundary", "Périmètre de mesure"), "unknowns": ("Unmeasured categories", "Catégories non mesurées"),
 "accounting_gaps": ("Accounting gaps", "Lacunes de comptabilisation"), "source_versions": ("Source versions", "Versions des sources"),
 "source_sha256": ("Source byte hashes", "Empreintes des octets sources"), "environment": ("Execution environment", "Environnement d’exécution"),
 "commands": ("Exact recorded commands", "Commandes exactes consignées"), "fault_schedule": ("Registered fault schedule", "Programme de pannes préenregistré"),
 "seed": ("Recorded seed", "Graine consignée"), "interventions": ("Recorded interventions", "Interventions consignées"),
 "test_assertion": ("Test assertion", "Assertion du test"), "target_verdict": ("Target verdict", "Verdict du composant"),
 "reference_verdict": ("Reference verdict", "Verdict de référence"), "checker_qualification": ("Checker qualification", "Qualification du vérificateur"),
 "required_quantity": ("Required quantity", "Quantité requise"),
 "production_attempts": ("Durable production attempts", "Tentatives de production durables"),
 "delivery_attempts": ("Delivery attempts", "Tentatives de livraison"),
 "rejection_count": ("Rejected delivery attempts", "Tentatives de livraison refusées"),
 "rejected_requested_quantity": ("Requested units in rejected deliveries", "Unités demandées dans les livraisons refusées"),
 "recipient_accepted_quantity": ("Units accepted by the recipient component", "Unités acceptées par le composant destinataire"),
 "timely_semantic_quantity": ("Semantically correct units observed in time", "Unités sémantiquement correctes observées à temps"),
 "accepted_obligations": ("Accepted obligations", "Obligations acceptées"),
 "required_obligations": ("Required active obligations", "Obligations actives requises"),
 "duplicate_acceptances": ("Duplicate accepted units", "Unités acceptées en double"),
 "unsafe_or_unsupported_commitments": ("Unsafe or unsupported commitments", "Engagements non sûrs ou non autorisés"),
 "acceptance_ids": ("Acceptance references", "Références d’acceptation"),
 "accepted_tick": ("Agreement acceptance tick", "Instant d’acceptation de l’accord"),
 "settled_tick": ("Modeled settlement tick", "Instant de règlement modélisé"),
 "cancelled_tick": ("Cancellation tick", "Instant d’annulation"),
 "expires_tick": ("Exclusive expiry tick", "Instant exclusif d’expiration"),
 "first_unit": ("First ordinal, inclusive", "Premier ordinal inclus"),
 "last_unit": ("Last ordinal, inclusive", "Dernier ordinal inclus"),
 "lot_id": ("Fixed lot identity", "Identité du lot fixe"),
 "window_id": ("Capacity-window identity", "Identité de la fenêtre de capacité"),
 "units": ("Units", "Unités"),
 "base_cost_minor": ("Base production cost (synthetic SMU minor units)", "Coût de production initiale (unités mineures SMU synthétiques)"),
 "rework_cost_minor": ("Maximum correction cost (synthetic SMU minor units)", "Coût maximal de correction (unités mineures SMU synthétiques)"),
 "maximum_unpaid_cost_exposure_minor": ("Maximum unpaid cost exposure (synthetic SMU minor units)", "Exposition maximale aux coûts impayés (unités mineures SMU synthétiques)"),
 "promised_payment_minor": ("Promised provider payment (synthetic SMU minor units)", "Paiement promis au fournisseur (unités mineures SMU synthétiques)"),
 "minimum_payment_minor": ("Minimum provider payment (synthetic SMU minor units)", "Paiement minimal au fournisseur (unités mineures SMU synthétiques)"),
 "participation_profit_minor": ("Required participation profit (synthetic SMU minor units)", "Profit requis de participation (unités mineures SMU synthétiques)"),
 "guaranteed_profit_minor": ("Modeled profit after maximum specified rework (synthetic SMU minor units)", "Profit modélisé après correction maximale spécifiée (unités mineures SMU synthétiques)"),
 "minimum_coordinator_fee_minor": ("Minimum coordinator fee (synthetic SMU minor units)", "Rémunération minimale du coordonnateur (unités mineures SMU synthétiques)"),
 "minimum_buyer_price_minor": ("Minimum feasible buyer price (synthetic SMU minor units)", "Prix acheteur minimal réalisable (unités mineures SMU synthétiques)"),
 "buyer_definite_max_price_minor": ("Buyer price ceiling at the lower value bound (synthetic SMU minor units)", "Plafond acheteur à la borne de valeur inférieure (unités mineures SMU synthétiques)"),
 "buyer_possible_max_price_minor": ("Buyer price ceiling at the upper value bound (synthetic SMU minor units)", "Plafond acheteur à la borne de valeur supérieure (unités mineures SMU synthétiques)"),
 "break_even_value_minor": ("Break-even buyer value (synthetic SMU minor units)", "Valeur d’équilibre de l’acheteur (unités mineures SMU synthétiques)"),
 "incurred_cost_minor": ("Incurred cost (synthetic SMU minor units)", "Coût engagé (unités mineures SMU synthétiques)"),
 "correction_cost_minor": ("Incurred correction cost (synthetic SMU minor units)", "Coût de correction engagé (unités mineures SMU synthétiques)"),
 "payments_minor": ("Modeled payments (synthetic SMU minor units)", "Paiements modélisés (unités mineures SMU synthétiques)"),
 "initial_balance_minor": ("Initial modeled balance (synthetic SMU minor units)", "Solde modélisé initial (unités mineures SMU synthétiques)"),
 "final_balance_minor": ("Final modeled balance (synthetic SMU minor units)", "Solde modélisé final (unités mineures SMU synthétiques)"),
 "funds_still_held_minor": ("Funds still encumbered (synthetic SMU minor units)", "Fonds encore retenus (unités mineures SMU synthétiques)"),
 "revenue_minor": ("Modeled receipts (synthetic SMU minor units)", "Encaissements modélisés (unités mineures SMU synthétiques)"),
 "purchase_payments_minor": ("Purchase transfers (synthetic SMU minor units)", "Transferts d’achat (unités mineures SMU synthétiques)"),
 "withdrawn_minor": ("Withdrawals to outside account (synthetic SMU minor units)", "Retraits vers le compte extérieur (unités mineures SMU synthétiques)"),
 "realized_profit_minor": ("Realized modeled profit (synthetic SMU minor units)", "Profit modélisé réalisé (unités mineures SMU synthétiques)"),
 "participation_threshold_minor": ("Applicable participation threshold (synthetic SMU minor units)", "Seuil de participation applicable (unités mineures SMU synthétiques)"),
 "participation_covered": ("Modeled participation threshold covered", "Seuil de participation modélisé couvert"),
 "trade_settled": ("Modeled trade settled", "Transaction modélisée réglée"),
 "realized_buyer": ("Realized modeled buyer feasibility", "Faisabilité modélisée réalisée pour l’acheteur"),
 "buyer_utility_interval_minor": ("Buyer utility interval (synthetic SMU minor units)", "Intervalle d’utilité de l’acheteur (unités mineures SMU synthétiques)"),
 "buyer_total_paid_minor": ("Total buyer transfers (synthetic SMU minor units)", "Total des transferts acheteur (unités mineures SMU synthétiques)"),
 "total_incurred_cost_minor": ("All incurred campaign costs (synthetic SMU minor units)", "Tous les coûts engagés de campagne (unités mineures SMU synthétiques)"),
 "total_correction_cost_minor": ("All correction costs (synthetic SMU minor units)", "Tous les coûts de correction (unités mineures SMU synthétiques)"),
 "total_transfers_minor": ("All modeled settlement transfers (synthetic SMU minor units)", "Tous les transferts de règlement modélisés (unités mineures SMU synthétiques)"),
 "initial_total_minor": ("Initial ledger total (synthetic SMU minor units)", "Total initial du registre (unités mineures SMU synthétiques)"),
 "final_total_minor": ("Final ledger total (synthetic SMU minor units)", "Total final du registre (unités mineures SMU synthétiques)"),
 "real_contracts_payments_or_demand": ("Real contracts, payments or demand", "Contrats, paiements ou demande réels"),
 "minimum": ("Lower bound", "Borne inférieure"), "maximum": ("Upper bound", "Borne supérieure"),
 "controller_cpu_user_ns": ("Controller user CPU (ns)", "Processeur utilisateur du contrôleur (ns)"),
 "controller_cpu_system_ns": ("Controller system CPU (ns)", "Processeur système du contrôleur (ns)"),
 "cpu_ns": ("Process CPU (ns)", "Temps processeur (ns)"),
 "peak_rss_bytes": ("Peak resident memory (bytes)", "Pic de mémoire résidente (octets)"),
 "worker_restarts": ("Worker restarts", "Redémarrages des services"),
 "candidate_restarts": ("Candidate restarts", "Redémarrages du candidat"),
 "service_requests": ("Internal service requests", "Requêtes internes aux services"),
 "child_processes": ("Launched child processes", "Processus enfants lancés"),
 "authority_storage_bytes_before_seal": ("Authority storage before sealing (bytes)", "Stockage de l’autorité avant scellement (octets)"),
 "evidence_files_read": ("Evidence files inspected", "Fichiers de preuve examinés"),
 "preparation_labor_seconds": ("Preparation labor (seconds; unknown if absent)", "Travail de préparation (secondes ; inconnu si absent)"),
 "integration_labor_seconds": ("Integration labor (seconds; unknown if absent)", "Travail d’intégration (secondes ; inconnu si absent)"),
 "adaptation_labor_seconds": ("Adaptation labor (seconds; unknown if absent)", "Travail d’adaptation (secondes ; inconnu si absent)"),
 "verification_labor_seconds": ("Human verification labor (seconds; unknown if absent)", "Travail humain de vérification (secondes ; inconnu si absent)"),
 "monetary_cost": ("Measured real monetary cost", "Coût monétaire réel mesuré"),
 "verification_wall_ns": ("Fresh verification elapsed time (ns)", "Durée de vérification fraîche (ns)"),
 "version": ("Implementation version", "Version d’implémentation"),
 "git_commit": ("Actual source commit", "Commit source effectif"),
 "dirty": ("Uncommitted source changes present", "Modifications sources non consignées présentes"),
 "reused_capacity_baseline": ("Preserved capacity implementation baseline", "Base conservée de l’implémentation de capacité"),
 "platform": ("Operating platform", "Plateforme d’exécution"),
 "python": ("Python interpreter", "Interpréteur Python"),
 "sqlite_version": ("SQLite version", "Version de SQLite"),
 "working_directory": ("Execution directory", "Répertoire d’exécution"),
 "argv": ("Exact process arguments", "Arguments exacts du processus"),
 "implementation": ("Implementation and provenance", "Implémentation et provenance"),
 "source_version": ("Recorded source identity", "Identité source consignée"),
 "faults_observed": ("Actually observed faults", "Pannes effectivement observées"),
 "untriggered_faults": ("Registered faults not triggered", "Pannes préenregistrées non déclenchées"),
 "event": ("Recorded event", "Événement consigné"),
 "trigger": ("Trigger operation", "Opération déclenchante"),
 "occurrence": ("Trigger occurrence", "Occurrence déclenchante"),
 "target": ("Fault target", "Cible de la panne"),
 "value": ("Configured value", "Valeur configurée"),
 "scope": ("Assessment scope", "Portée de l’évaluation"),
 "trust_assumptions": ("Explicit trust assumptions", "Hypothèses de confiance explicites"),
 "evidence_sha256": ("Evidence byte hashes", "Empreintes des octets de preuve"),
 "structured_result_sha256": ("Structured result SHA-256", "SHA-256 du résultat structuré"),
 "fixture_id": ("Registered fixture identity", "Identité du cas préenregistré"),
 "cohort": ("Experiment cohort", "Cohorte d’expérience"),
 "method": ("Candidate procedure", "Procédure candidate"),
 "registered_assertion": ("Registered assertion", "Assertion préenregistrée"),
 "accepted_lots": ("Accepted lots in the partial arrangement", "Lots acceptés dans la solution partielle"),
 "reason": ("Recorded reason", "Motif consigné"),
 "assessed_claim": ("Claim under assessment", "Affirmation évaluée"),
 "criterion": ("Registered test criterion", "Critère de test préenregistré"),
 "execution_reused_from": ("Retained execution used for this challenge", "Exécution conservée utilisée pour cette épreuve"),
 "observation_wall_ns": ("Challenge observation elapsed time (ns)", "Durée d’observation de l’épreuve (ns)"),
 "registration_sha256": ("Challenge registration SHA-256", "SHA-256 du préenregistrement des épreuves"),
 "registered_case": ("Registered challenge case", "Cas contradictoire préenregistré"),
 "observed_outcome": ("Independently observed outcome", "Résultat observé indépendamment"),
 "observed_service_feasibility": ("Independently observed modeled feasibility", "Faisabilité modélisée observée indépendamment"),
 "observed_safety_status": ("Independently observed safety status", "État de sûreté observé indépendamment"),
 "finding_codes": ("Observed finding codes", "Codes des constats observés"),
 "expected": ("Registered expected assessment", "Évaluation attendue préenregistrée"),
 "observed": ("Observed assessment", "Évaluation observée"),
}


def tr(key, language):
    return TEXT[key][1 if language == "fr" else 0]


def escape(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("|", "\\|").replace("\r", "").replace("\n", " / ").replace(BT, "\\" + BT)


def display(value, language):
    if value is None:
        return tr("not_recorded", language)
    if type(value) is bool:
        return tr("yes" if value else "no", language)
    if type(value) is int:
        return str(value)
    if type(value) is str:
        if value in LITERAL_TRANSLATIONS:
            return LITERAL_TRANSLATIONS[value][1 if language == "fr" else 0]
        if value in STATUS:
            return STATUS[value][1 if language == "fr" else 0] + " (" + BT + value + BT + ")"
        return escape(value)
    if type(value) is dict and set(value) == {"en", "fr"} and all(type(v) is str for v in value.values()):
        return escape(value[language])
    if type(value) in (list, dict) and not value:
        return tr("empty", language)
    return escape(json.dumps(value, ensure_ascii=False, sort_keys=True))


def field_label(path, language):
    key = path.rsplit(".", 1)[-1].split("[", 1)[0]
    label = FIELDS.get(key)
    return (label[1 if language == "fr" else 0] + " · " if label else "") + BT + escape(path) + BT


def flatten(value, prefix=""):
    if type(value) is dict and not (set(value) == {"en", "fr"} and all(type(v) is str for v in value.values())):
        if not value:
            yield prefix, value
        for key in sorted(value):
            yield from flatten(value[key], prefix + ("." if prefix else "") + key)
    elif type(value) is list:
        if not value:
            yield prefix, value
        for index, item in enumerate(value):
            yield from flatten(item, prefix + "[" + str(index) + "]")
    else:
        yield prefix, value


def detail_table(value, language):
    lines = ["| " + tr("field", language) + " | " + tr("value", language) + " |", "| --- | --- |"]
    for path, item in flatten(value):
        lines.append("| " + field_label(path or "record", language) + " | " + display(item, language) + " |")
    return "\n".join(lines)


def findings_table(rows, language, missing=False):
    if not rows:
        return tr("none_unresolved" if missing else "none_failures", language)
    keys = ("code", "scope", "obligation", "arrangement", "explanation", "locator")
    lines = ["| " + " | ".join(tr(k, language) for k in keys) + " |", "| --- | --- | --- | --- | --- | --- |"]
    for row in rows:
        lines.append("| " + " | ".join([
            BT + escape(row.get("code", "UNKNOWN")) + BT, display(row.get("scope"), language),
            display(row.get("obligation_id"), language), display(row.get("arrangement_id"), language),
            tr("missing" if missing else "contradiction", language), BT + escape(row.get("detail", "")) + BT]) + " |")
    return "\n".join(lines)


def render_passport(result, language="en", context=None):
    if language not in ("en", "fr") or type(result) is not dict or (context is not None and type(context) is not dict):
        raise HarnessError("INVALID_TYPE", "passport")
    canonical(result)
    if context is not None:
        canonical(context)
    assessment, claims, context = result.get("assessment", {}), result.get("claims", {}), context or {}
    challenge = result.get("challenge") or context.get("challenge")
    sha = digest(result)
    lines = ["# " + tr("title", language), "", "**" + tr("subtitle", language) + "**", "", tr("promise", language), "",
             "**" + tr("boundary", language) + "**", "", tr("fresh", language), "",
             "<!-- structured-result-sha256: " + sha + " -->", "", "## " + tr("claims", language), "",
             "| " + tr("claim", language) + " | " + tr("status", language) + " |", "| --- | --- |"]
    if type(challenge) is dict and challenge.get("checker_qualification") == "FAILED":
        lines[7:7] = ["**" + tr("failed_checker", language) + "**", ""]
    for key in ("outcome", "service_feasibility", "method_advantage"):
        lines.append("| " + tr(key, language) + " | " + display(claims.get(key, "NOT_ESTABLISHED"), language) + " |")
    if "checker_qualification" in claims:
        lines.append("| " + tr("checker_claim", language) + " | " + display(claims["checker_qualification"], language) + " |")
    lines += ["| " + tr("safety", language) + " | " + display(result.get("safety_status", "NOT_ESTABLISHED"), language) + " |",
              "", tr("model", language), "", "## " + tr("four", language), "",
              "| " + tr("field", language) + " | " + tr("value", language) + " |", "| --- | --- |"]
    for key, label in (("test_assertion", "assertion"), ("target_verdict", "target"), ("evidence_stage", "stage"), ("claim_status", "claim_status")):
        lines.append("| " + tr(label, language) + " | " + display(assessment.get(key, "NOT_EVALUATED" if key == "test_assertion" else "NOT_ESTABLISHED"), language) + " |")
    lines += ["", tr("separation", language), "", "## " + tr("identity", language), ""]
    identity = ("schema", "verifier_version", "run_id", "contract_id", "contract_sha256", "reference_sha256", "authority_status", "verification_status", "real_customer_authenticity", "commercial_value")
    identity_record = {k: result.get(k) for k in identity}
    if identity_record["contract_id"] is None and type(context.get("contract")) is dict:
        identity_record["contract_id"] = context["contract"].get("contract_id")
    lines += [detail_table(identity_record, language), "", "## " + tr("obligations", language), "", tr("quantity_note", language), "",
              "| " + " | ".join(tr(k, language) for k in ("obligation", "recipient", "revision", "required", "produced", "received", "rejected", "accepted", "outcome_short")) + " |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    obligations = result.get("per_obligation", [])
    for row in obligations:
        values = [row.get("obligation_id"), row.get("recipient"), row.get("revision"),
                  row.get("required_quantity", row.get("quantity")), row.get("produced_quantity"),
                  row.get("received_quantity"), row.get("rejected_quantity"), row.get("accepted_quantity"),
                  row.get("outcome")]
        lines.append("| " + " | ".join(display(value, language) for value in values) + " |")
    if not obligations:
        lines.append("| " + tr("empty", language) + " | " + " | ".join([tr("not_recorded", language)] * 8) + " |")
    for row in obligations:
        lines += ["", "### " + tr("obligation", language) + " " + BT + escape(row.get("obligation_id", "UNKNOWN")) + BT, "", detail_table(row, language)]
    lines += ["", "## " + tr("arrangements", language), "", tr("model", language), ""]
    arrangements = result.get("per_arrangement", [])
    if not arrangements:
        lines.append(tr("no_arrangements", language))
    if any(row.get("status") == "ACTIVE" for row in arrangements) and any(
            (row.get("recipient_accepted_quantity") or row.get("accepted_quantity") or 0) > 0 for row in obligations):
        lines += ["**" + tr("partial_liabilities", language) + "**", ""]
    for row in arrangements:
        aid = row.get("agreement_id") or row.get("arrangement_id") or row.get("proposal_id") or "UNKNOWN"
        lines += ["### " + tr("arrangement", language) + " " + BT + escape(aid) + BT, "", detail_table(row, language), "", tr("model", language), ""]
    lines += ["", "## " + tr("accounting", language), "", tr("model", language), "",
              detail_table({"totals": result.get("totals"), "accounting": result.get("accounting")}, language), "",
              "## " + tr("resources", language), "", tr("resource_note", language), "",
              detail_table({"resources": result.get("resources"), "verification_resources": result.get("verification_resources"), "accounting_gaps": result.get("accounting_gaps")}, language), "",
              "## " + tr("failures", language), "", findings_table(result.get("failures", []), language), "",
              "## " + tr("unresolved", language), "", findings_table(result.get("unresolved", []), language, missing=True), "",
              "## " + tr("evidence", language), "", tr("hash_note", language), "",
              detail_table({"structured_result_sha256": sha, "evidence_sha256": result.get("evidence_sha256")}, language)]
    recorded_context = {k: result[k] for k in ("implementation", "source_version", "fault_schedule", "faults_observed",
                         "untriggered_faults", "trust_assumptions", "registered_assertion", "fixture_id", "method", "cohort")
                        if k in result}
    recorded_context.update(context)
    if recorded_context:
        lines += ["", "## " + tr("context", language), "", tr("context_note", language), "", detail_table(recorded_context, language)]
    if challenge is not None:
        lines += ["", "## " + tr("challenge", language), "", tr("separation", language), "", detail_table(challenge, language)]
    lines += ["", "## " + tr("structured", language), "", tr("structured_note", language), "",
              BT * 3 + "json", json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2), BT * 3, ""]
    return "\n".join(lines)


def _write_atomic(path, raw):
    fd, temporary = tempfile.mkstemp(prefix="." + path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        descriptor = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_passports(result, run_dir, context=None):
    directory = Path(run_dir).absolute()
    if directory.is_symlink() or any(p.is_symlink() for p in directory.parents):
        raise HarnessError("UNSAFE_PATH", "passport directory")
    directory.mkdir(parents=True, exist_ok=True)
    rendered = {lang: render_passport(result, lang, context).encode("utf-8") for lang in ("en", "fr")}
    outputs = {}
    for language, raw in rendered.items():
        path = directory / ("PASSPORT." + language + ".md")
        if path.is_symlink():
            raise HarnessError("UNSAFE_PATH", path.name)
        if path.exists():
            previous = path.read_bytes()
            if previous != raw:
                history = directory / "passport-history"
                if history.is_symlink():
                    raise HarnessError("UNSAFE_PATH", "passport history")
                history.mkdir(exist_ok=True)
                prior = history / ("PASSPORT." + language + "." + hashlib.sha256(previous).hexdigest() + ".md")
                if prior.is_symlink():
                    raise HarnessError("UNSAFE_PATH", "passport history entry")
                if prior.exists():
                    if prior.read_bytes() != previous:
                        raise HarnessError("SOURCE_DIGEST_MISMATCH", "passport history")
                else:
                    _write_atomic(prior, previous)
        _write_atomic(path, raw)
        outputs[language] = str(path)
    outputs["result_sha256"] = digest(result)
    return outputs
