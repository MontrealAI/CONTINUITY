"""Preserved, noncomparative adversarial and verifier-mutation exercises.

The target's original result is never rewritten into a passing test. Each case
has separate TARGET_RESULT.json, REFERENCE_RESULT.json and CHALLENGE.json files.
The outer assessment concerns its named procedure/checker property; its business
outcomes are copied unchanged from the defect-free reference verification.
Mutations are scoped Python patches, never edits to the installed verifier.
"""

from copy import deepcopy
import hashlib
from pathlib import Path
import shutil
import time
from unittest.mock import patch
import uuid

from .controller import fresh_directory, implementation_identity, run_exercise, write_json
from .fixtures import candidate_view, make_contract, specification
from .reporting import write_reports
from .schema import canonical, digest, strict_load
from .suite import conclude_run, reference_info
from .verifier import verify_run


def bilingual(en, fr):
    return {"en": en, "fr": fr}


DEFINITIONS = [
    {"id": "no-journal-ablation", "subject": "CANDIDATE_PROCEDURE", "stage": "LOCAL_SOFTWARE_EXECUTION",
     "title": bilingual("Ablation: no journal reconciliation", "Ablation : sans rapprochement du journal"),
     "claim": bilingual("The procedure without journal reconciliation can complete the original outstanding obligations.",
                         "La procédure sans rapprochement du journal peut réaliser les obligations originales restantes."),
     "expected": bilingual("Ordinary service safeguards refuse stale obligations; accepted quantity remains below 1,900 and the full-promise claim fails.",
                            "Les protections ordinaires du service refusent les obligations périmées ; la quantité acceptée reste inférieure à 1 900 et la promesse complète échoue.")},
    {"id": "rewritten-1850", "subject": "CANDIDATE_PROCEDURE", "stage": "LOCAL_SOFTWARE_EXECUTION",
     "title": bilingual("Coherently resealed 1,850-unit candidate package", "Dossier candidat de 1 850 unités dont les empreintes sont recalculées"),
     "claim": bilingual("A candidate-side rewrite cannot redefine verified success against the separately retained 1,900-unit promise.",
                         "Une réécriture du dossier candidat ne peut redéfinir la réussite vérifiée face à la promesse de 1 900 unités conservée séparément."),
     "expected": bilingual("Candidate-side source, contract and view seals are recomputed; the retained contract still requires 1,900 units and cannot be fully accepted.",
                            "Les empreintes de la source, du contrat et de la vue du candidat sont recalculées ; le contrat conservé exige toujours 1 900 unités et ne peut être accepté intégralement.")},
    {"id": "missing-reference-pin", "subject": "FRESH_VERIFIER", "stage": "FRESH_VERIFICATION_CHALLENGE",
     "title": bilingual("Missing independently retained reference pin", "Empreinte de référence indépendante absente"),
     "claim": bilingual("The checker preserves uncertainty when the independent reference pin is not supplied.",
                         "Le vérificateur conserve l’incertitude lorsque l’empreinte de référence indépendante n’est pas fournie."),
     "expected": bilingual("Otherwise valid durable evidence remains NOT_ESTABLISHED without the independently supplied reference digest.",
                            "Des preuves durables autrement valides restent NOT_ESTABLISHED sans l’empreinte de référence fournie indépendamment.")},
    {"id": "changed-artifact", "subject": "FRESH_VERIFIER", "stage": "FRESH_VERIFICATION_CHALLENGE",
     "title": bilingual("Changed artifact with stale favorable Passport", "Pièce modifiée accompagnée d’un ancien Passeport favorable"),
     "claim": bilingual("Fresh checking detects a byte change even when parsed content and a saved favorable Passport remain unchanged.",
                         "La vérification fraîche détecte un changement d’octets même si le contenu interprété et un ancien Passeport favorable restent identiques."),
     "expected": bilingual("Appending JSON whitespace changes the sealed bytes; EVIDENCE_CHANGED prevents favorable acceptance.",
                            "L’ajout d’un espace JSON modifie les octets scellés ; EVIDENCE_CHANGED empêche une acceptation favorable.")},
    {"id": "shared-failed-dependency", "subject": "CANDIDATE_PROCEDURE", "stage": "LOCAL_SOFTWARE_EXECUTION",
     "title": bilingual("Backup shares the primary's failed dependency", "Le secours partage la dépendance défaillante du primaire"),
     "claim": bilingual("A backup on the same failed dependency cannot fulfill the customer's original promise.",
                         "Un secours sur la même dépendance défaillante ne peut réaliser la promesse originale au client."),
     "expected": bilingual("Both routes are unavailable; zero units are accepted, and no complete fulfillment is claimed.",
                            "Les deux voies sont indisponibles ; aucune unité n’est acceptée et aucune réalisation complète n’est revendiquée.")},
    {"id": "mutant-ignores-byte-integrity", "subject": "MUTATED_VERIFIER", "stage": "CHECKER_MUTATION_EXERCISE",
     "title": bilingual("Mutant checker ignores current file bytes", "Vérificateur mutant ignorant les octets actuels des fichiers"),
     "claim": bilingual("The mutated checker rejects changes to sealed evidence bytes.",
                         "Le vérificateur mutant rejette les modifications des octets scellés des preuves."),
     "expected": bilingual("The defect-free checker rejects the changed bytes; the mutant falsely reports DEMONSTRATED. The adversarial test passes while the mutant's qualification claim fails.",
                            "Le vérificateur sans mutation rejette les octets modifiés ; le mutant annonce indûment DEMONSTRATED. Le test contradictoire réussit alors que l’affirmation qualifiant le mutant échoue.")},
    {"id": "mutant-ignores-revocation", "subject": "MUTATED_VERIFIER", "stage": "CHECKER_MUTATION_EXERCISE",
     "title": bilingual("Mutant checker ignores permission revocation", "Vérificateur mutant ignorant le retrait d’autorisation"),
     "claim": bilingual("The mutated checker rejects completion after a recorded permission revocation.",
                         "Le vérificateur mutant rejette une réalisation postérieure à un retrait d’autorisation consigné."),
     "expected": bilingual("A copied controller record receives an explicitly synthetic revocation and a test-authority reseal. The correct checker rejects it; the mutant falsely accepts it.",
                            "Un retrait explicitement synthétique est injecté dans une copie du registre du contrôleur, puis scellé de nouveau par l’autorité de test. Le bon vérificateur le rejette ; le mutant l’accepte indûment.")},
    {"id": "mutant-rejects-valid-recovery", "subject": "MUTATED_VERIFIER", "stage": "CHECKER_MUTATION_EXERCISE",
     "title": bilingual("Mutant checker rejects valid recovery", "Vérificateur mutant rejetant une reprise valide"),
     "claim": bilingual("The mutated checker recognizes valid completed primary recovery.",
                         "Le vérificateur mutant reconnaît une reprise primaire valide et achevée."),
     "expected": bilingual("The defect-free positive control is DEMONSTRATED. Replacing recovered source rows with an empty list creates a false negative detected by the positive assertion.",
                            "Le contrôle positif sans mutation est DEMONSTRATED. Remplacer les lignes reconstituées par une liste vide crée un faux négatif détecté par l’assertion positive.")},
]


def _codes(result):
    return {item["code"] for item in result["failures"] + result["unresolved"]}


def _verify(run, *, pin=True):
    start = time.monotonic_ns()
    result = verify_run(run["run_dir"], run["authority_dir"],
                        expected_reference_sha256=run["reference_sha256"] if pin else None)
    return result, time.monotonic_ns() - start


def _copy_run(base, folder):
    """Copy retained evidence, including its old reports; do not rerun services."""
    shutil.copytree(base["run_dir"], folder / "run")
    shutil.copytree(base["authority_dir"], folder / "authority")
    return {"run_dir": str(folder / "run"), "authority_dir": str(folder / "authority"),
            "reference_sha256": base["reference_sha256"], "controller": strict_load(folder / "run/controller.json")}


def _change_bytes(run):
    path = Path(run["run_dir"]) / "evidence/artifacts/LBL-100.json"
    original = path.read_bytes()
    path.write_bytes(original + b" ")
    return {"kind": "APPEND_JSON_WHITESPACE", "path": "run/evidence/artifacts/LBL-100.json",
            "before_sha256": hashlib.sha256(original).hexdigest(),
            "after_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "producer_execution_seal_changed": False, "stale_favorable_passport_retained": True}


def _inject_revocation(run):
    """A declared synthetic verifier input mutation, not a live service event."""
    path = Path(run["run_dir"]) / "controller.json"
    controller = strict_load(path)
    old_controller = digest(controller)
    event = {"event": "PERMISSION_REVOKED", "tick": 0,
             "monotonic_ns": controller["started_monotonic_ns"] + 1,
             "detail": {"permission": "activation"}}
    controller["events"].append(event)
    path.write_bytes(canonical(controller) + b"\n")
    seal_path = Path(run["authority_dir"]) / "execution.json"
    seal = strict_load(seal_path)
    old_seal = digest(seal)
    seal["controller_sha256"] = digest(controller)
    seal_path.write_bytes(canonical(seal) + b"\n")
    run["controller"] = controller
    return {"kind": "SYNTHETIC_RECORDED_REVOCATION", "event": event,
            "live_revocation_was_executed": False, "test_authority_resealed_copy": True,
            "controller_before_sha256": old_controller, "controller_after_sha256": digest(controller),
            "execution_seal_before_sha256": old_seal, "execution_seal_after_sha256": digest(seal)}


def _outer_record(definition, reference, target, passed, claim, mutation, observations,
                  *, target_verdict, resource_origin, measurements):
    # Construct a distinct assessment object. Never alter the supplied verdicts.
    keys = ("verifier_version", "run_id", "contract_sha256", "reference_sha256", "authority_status",
            "verification_status", "safety_status", "all_obligations_completed", "per_obligation", "totals",
            "ledger", "failures", "unresolved", "evidence_sha256", "resources", "recovery_ms", "trust_scope",
            "commercial_value", "real_customer_authenticity")
    result = {key: deepcopy(reference.get(key)) for key in keys}
    result.update(schema="continuity-harness/challenge/v1",
                  assessment={"test_assertion": "PASSED" if passed else "FAILED", "target_verdict": target_verdict,
                              "evidence_stage": definition["stage"], "claim_status": claim},
                  challenge={"id": definition["id"], "title": definition["title"], "claim": definition["claim"],
                             "expected_observation": definition["expected"], "actual_observation": observations,
                             "assessment_subject": definition["subject"],
                             "underlying_claim_status": reference["assessment"]["claim_status"],
                             "target_result_path": "TARGET_RESULT.json", "reference_result_path": "REFERENCE_RESULT.json",
                             "source_evidence_path": "run", "mutation": mutation},
                  target_result_sha256=digest(target), reference_result_sha256=digest(reference),
                  resource_origin=resource_origin, measurements=measurements)
    return result


def run_challenges(out):
    """Run eight retained adversarial controls, returning the complete summary.

    Exactly four new local service executions are used: one positive control and
    three procedure challenges. Other cases freshly inspect copied evidence.
    Their copied execution costs must not be added as new measured executions.
    """
    root = fresh_directory(out)
    instance = uuid.uuid4().hex[:12]
    registered = specification()
    design = {"schema": "continuity-harness/challenge-spec/v1", "version": 1,
              "kind": "NONCOMPARATIVE_ADVERSARIAL_REGRESSION", "experiment_id": registered["experiment_id"],
              "experiment_specification_sha256": digest(registered), "cases": DEFINITIONS,
              "frozen_before_this_suite": True,
              "interpretation": "Regression/mutation demonstrations; no performance comparison or general proof."}
    write_json(root / "CHALLENGE_SPEC.json", design)
    summary = {"schema": "continuity-harness/challenges/v1", "instance_id": instance,
               "specification_sha256": digest(design), "implementation": implementation_identity(),
               "complete": False, "noncomparative": True, "executed_runs": 0, "records": [],
               "release_gate": "FAILED", "mutants_exposed": [], "failed_test_assertions": [],
               "unknown_costs": ["preparation_labor", "integration_labor", "peak_memory", "monetary_cost"],
               "resource_note": "Copied evidence reuses one positive-control execution; do not sum its execution resources repeatedly."}
    attempts = open(root / "ATTEMPTS.jsonl", "xb", buffering=0)

    def log(event, **values):
        attempts.write(canonical({"event": event, "monotonic_ns": time.monotonic_ns(), **values}) + b"\n")

    try:
        log("START_POSITIVE_CONTROL")
        baseline = run_exercise(make_contract(run_id="challenge-positive-" + instance), "harness",
                                root / "positive-control/run", root / "positive-control/authority")
        summary["executed_runs"] += 1
        positive = conclude_run(baseline)
        summary["positive_control"] = {"run_relative": "positive-control/run", "authority_relative": "positive-control/authority",
                                       "reference_sha256": baseline["reference_sha256"], "assessment": positive["assessment"]}
        log("FINISH_POSITIVE_CONTROL", assessment=positive["assessment"])
        for definition in DEFINITIONS:
            identity = definition["id"]
            folder = fresh_directory(root / "cases" / identity)
            log("START_CHALLENGE", challenge=identity)
            started = time.monotonic_ns()
            mutation = None
            pin = True
            resource_origin = "COPIED_POSITIVE_CONTROL_EXECUTION"
            target_ns = 0
            if identity in ("no-journal-ablation", "rewritten-1850", "shared-failed-dependency"):
                method = "ablation" if identity == "no-journal-ablation" else "harness"
                scenario = "recovery" if method == "ablation" else "alternate"
                contract = make_contract(scenario=scenario, method=method, run_id=identity + "-" + instance)
                view = None
                if identity == "rewritten-1850":
                    view = candidate_view(contract)
                    view["contract"]["source_events"][1]["quantity"] -= 50
                    view["contract"]["source_sha256"] = digest(view["contract"]["source_events"])
                    view["package_seals"] = {"source_sha256": view["contract"]["source_sha256"],
                                             "contract_sha256": digest(view["contract"]), "view_sha256": digest(view)}
                    mutation = {"kind": "CANDIDATE_ONLY_RESEAL", "original_units": 1900, "rewritten_units": 1850,
                                "candidate_seals": view["package_seals"], "retained_original_changed": False}
                elif identity == "shared-failed-dependency":
                    contract["dependencies"]["backup"] = contract["dependencies"]["primary"]
                run = run_exercise(contract, method, folder / "run", folder / "authority", candidate_visible=view)
                summary["executed_runs"] += 1
                resource_origin = "NEW_LOCAL_EXECUTION"
            else:
                run = _copy_run(baseline, folder)
                if identity in ("changed-artifact", "mutant-ignores-byte-integrity"):
                    mutation = _change_bytes(run)
                elif identity == "mutant-ignores-revocation":
                    mutation = _inject_revocation(run)
                elif identity == "missing-reference-pin":
                    pin = False
            reference, reference_ns = _verify(run, pin=pin)
            target = deepcopy(reference)
            if identity == "mutant-ignores-byte-integrity":
                hashes = strict_load(Path(run["authority_dir"]) / "execution.json")["evidence_manifest"]
                def ignore_current_bytes(path):
                    return hashes[Path(path).relative_to(Path(run["run_dir"])).as_posix()]
                mutation["hook"] = "continuity_harness.verifier._file_hash"
                mutation["replacement"] = "Return retained manifest bytes hash without reading current file bytes."
                with patch("continuity_harness.verifier._file_hash", side_effect=ignore_current_bytes):
                    target, target_ns = _verify(run)
            elif identity == "mutant-ignores-revocation":
                mutation["hook"] = "continuity_harness.verifier._revoked"
                mutation["replacement"] = "Always return None."
                with patch("continuity_harness.verifier._revoked", return_value=None):
                    target, target_ns = _verify(run)
            elif identity == "mutant-rejects-valid-recovery":
                mutation = {"hook": "continuity_harness.verifier._source_rows", "replacement": "Return an empty recovered-row list.",
                            "kind": "FALSE_NEGATIVE_CHECKER_MUTATION", "evidence_changed": False}
                with patch("continuity_harness.verifier._source_rows", return_value=[]):
                    target, target_ns = _verify(run)
            normal_claim = reference["assessment"]["claim_status"]
            target_claim = target["assessment"]["claim_status"]
            normal_codes = _codes(reference)
            if identity == "no-journal-ablation":
                passed = normal_claim == "FAILED" and reference["totals"]["accepted_units"] < 1900 and reference["safety_status"] == "DEMONSTRATED"
                claim = normal_claim
            elif identity == "rewritten-1850":
                passed = normal_claim != "DEMONSTRATED" and reference["totals"]["expected_units"] == 1900 and reference["totals"]["accepted_units"] < 1900
                claim = "DEMONSTRATED" if passed and reference["verification_status"] == "COMPLETE" else "NOT_ESTABLISHED"
            elif identity == "missing-reference-pin":
                passed = normal_claim == "NOT_ESTABLISHED" and "REFERENCE_PIN_MISSING" in normal_codes
                claim = "DEMONSTRATED" if passed else "FAILED"
            elif identity == "changed-artifact":
                passed = normal_claim == "FAILED" and "EVIDENCE_CHANGED" in normal_codes
                claim = "DEMONSTRATED" if passed else "FAILED"
            elif identity == "shared-failed-dependency":
                passed = normal_claim != "DEMONSTRATED" and reference["totals"]["accepted_units"] == 0 and run["controller"]["target_verdict"] != "COMPLETED"
                claim = "DEMONSTRATED" if passed and reference["verification_status"] == "COMPLETE" else "NOT_ESTABLISHED"
            else:
                if identity == "mutant-rejects-valid-recovery":
                    passed = normal_claim == "DEMONSTRATED" and target_claim == "FAILED"
                else:
                    expected_code = "EVIDENCE_CHANGED" if identity == "mutant-ignores-byte-integrity" else "UNAUTHORIZED_ACTIVATION"
                    passed = expected_code in normal_codes and normal_claim == "FAILED" and target_claim == "DEMONSTRATED"
                # Qualification fails for the defective checker, even when the
                # enclosing adversarial assertion successfully exposes it.
                claim = "FAILED" if passed else "NOT_ESTABLISHED"
            if positive["assessment"]["claim_status"] != "DEMONSTRATED" or reference["verification_status"] != "COMPLETE":
                passed, claim = False, "NOT_ESTABLISHED"
            is_checker = definition["subject"] != "CANDIDATE_PROCEDURE"
            target_verdict = target_claim if is_checker else run["controller"]["target_verdict"]
            observations = bilingual(
                f"Reference full-promise claim: {normal_claim}; tested target: {target_verdict}; accepted reference quantity: {reference['totals']['accepted_units']} / {reference['totals']['expected_units']}. "
                + ("The checker defect was exposed; a passing outer test does not qualify this mutant." if identity.startswith("mutant-") else "These are scoped observations from synthetic local evidence."),
                f"Affirmation de promesse complète selon la référence : {normal_claim} ; composant testé : {target_verdict} ; quantité acceptée selon la référence : {reference['totals']['accepted_units']} / {reference['totals']['expected_units']}. "
                + ("Le défaut du vérificateur a été exposé ; la réussite du test externe ne qualifie pas ce mutant." if identity.startswith("mutant-") else "Il s’agit d’observations limitées à des preuves locales synthétiques."))
            record = _outer_record(definition, reference, target, passed, claim, mutation, observations,
                                   target_verdict=target_verdict, resource_origin=resource_origin,
                                   measurements={"reference_verification_wall_ns": reference_ns,
                                                 "additional_target_verification_wall_ns": target_ns,
                                                 "challenge_wall_ns_before_report": time.monotonic_ns() - started})
            record["reference_pin_sha256"] = run["reference_sha256"] if pin else None
            write_json(folder / "REFERENCE_RESULT.json", reference)
            write_json(folder / "TARGET_RESULT.json", target)
            write_json(folder / "CHALLENGE.json", record)
            info = reference_info(run)
            if not pin:
                info["reference_sha256"] = None
                info["commands"].append(["python3", "-m", "continuity_harness", "verify", "--run", run["run_dir"], "--authority", run["authority_dir"]])
            write_reports(folder, record, run["controller"], info)
            summary["records"].append({"id": identity, "case_relative": "cases/" + identity,
                                        "reference_pin_sha256": record["reference_pin_sha256"],
                                        "assessment": record["assessment"], "reference_assessment": reference["assessment"],
                                        "target_assessment": target["assessment"], "per_obligation": record["per_obligation"],
                                        "totals": record["totals"], "resource_origin": resource_origin,
                                        "measurements": record["measurements"], "challenge_sha256": digest(record)})
            if not passed:
                summary["failed_test_assertions"].append(identity)
            if identity.startswith("mutant-") and passed:
                summary["mutants_exposed"].append(identity)
            log("FINISH_CHALLENGE", challenge=identity, assessment=record["assessment"])
        summary["complete"] = True
        summary["release_gate"] = "PASSED" if not summary["failed_test_assertions"] else "FAILED"
    finally:
        attempts.close()
        write_json(root / "SUMMARY.json", summary)
        for language in ("en", "fr"):
            (root / f"SUMMARY.{language}.md").write_text(render_challenge_summary(summary, language), encoding="utf-8")
    return summary


def render_challenge_summary(summary, language="en"):
    fr = language == "fr"
    title = "CONTINUITÉ Ω — Épreuves contradictoires conservées" if fr else "CONTINUITY Ω — Retained adversarial challenges"
    lines = ["# " + title, "", "[English](SUMMARY.en.md) · [Français](SUMMARY.fr.md)", "",
             ("Cette suite ne compare pas les performances des méthodes. Elle conserve chaque verdict original et une évaluation externe distincte. La réussite d’un test révélant une acceptation indue ne qualifie pas le vérificateur défectueux." if fr else
              "This suite does not compare method performance. It retains every original verdict and a separate outer assessment. A passing test that exposes false acceptance does not qualify the defective checker."), "",
             f"**{'Contrôle de la suite' if fr else 'Suite gate'}:** `{summary['release_gate']}` · **{'Exécutions locales nouvelles' if fr else 'New local executions'}:** {summary['executed_runs']}", "",
             "| " + ("Épreuve | Assertion externe | Verdict testé | Stade | Affirmation limitée | Promesse complète de référence |" if fr else
                      "Challenge | Outer assertion | Tested verdict | Stage | Scoped claim | Reference full promise |"),
             "|---|---|---|---|---|---|"]
    for entry in summary["records"]:
        a = entry["assessment"]
        lines.append(f"| [{entry['id']}]({entry['case_relative']}/PASSPORT.{language}.md) | `{a['test_assertion']}` | `{a['target_verdict']}` | `{a['evidence_stage']}` | `{a['claim_status']}` | `{entry['reference_assessment']['claim_status']}` |")
    lines += ["", ("Les mutations réutilisent des copies d’un contrôle positif, avec ses anciens Passeports conservés. Les temps d’exécution de ces copies ne constituent pas de nouvelles mesures à additionner. Les durées des vérifications sont mesurées séparément dans CHALLENGE.json. Travail de préparation, intégration, mémoire maximale et coûts monétaires : inconnus." if fr else
                    "Mutations reuse copies of a positive control, retaining its old Passports. The copied execution times are not new measurements to add together. Verification durations are measured separately in CHALLENGE.json. Preparation, integration, peak memory and monetary costs remain unknown."), "",
              ("L’ablation retire le rapprochement du journal tout en conservant les protections ordinaires des services ; son échec n’établit aucun avantage général de l’IA. Le retrait d’autorisation du cas mutant est une modification synthétique explicite d’une copie de preuve, pas un retrait réellement exécuté par le service." if fr else
               "The ablation removes journal reconciliation while keeping ordinary service safeguards; its failure establishes no general AI advantage. The mutant revocation is an explicitly synthetic modification of copied evidence, not a permission withdrawal actually executed by the service."), "",
              ("Chaque dossier contient CHALLENGE.json, TARGET_RESULT.json et REFERENCE_RESULT.json, les preuves durables, et les deux Passeports complets. Les mutations sont limitées à l’appel de test et ne modifient pas le vérificateur installé." if fr else
               "Every case contains CHALLENGE.json, TARGET_RESULT.json and REFERENCE_RESULT.json, durable evidence, and both complete Passports. Mutations are scoped to the test invocation and do not alter the installed verifier."), ""]
    return "\n".join(lines)
