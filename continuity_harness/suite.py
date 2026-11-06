"""Registered demonstrations, comparisons and separate fresh suite verification."""

from copy import deepcopy
import hashlib
import platform
from pathlib import Path
import shutil
import sys
import uuid

from .adapters import ADAPTERS
from .controller import fresh_directory, run_exercise, write_json, implementation_identity
from .fixtures import make_contract, specification, SPEC_PATH
from .schema import canonical, digest, strict_load, HarnessError, object_fields, boolean, identifier, sha256
from .verifier import verify_run


def reference_info(run):
    info = {k: run[k] for k in ("run_dir", "authority_dir", "reference_sha256")}
    info["contract"] = strict_load(Path(run["authority_dir"]) / "contract.json")
    info["reference"] = strict_load(Path(run["authority_dir"]) / "reference.json")
    info["commands"] = [run["controller"]["implementation"]["environment"]["argv"]]
    return info


def conclude_run(run):
    from .reporting import write_reports
    result = verify_run(run["run_dir"], run["authority_dir"], expected_reference_sha256=run["reference_sha256"])
    write_json(Path(run["run_dir"]) / "RESULT.json", result)
    write_reports(run["run_dir"], result, run["controller"], reference_info(run))
    return result


def compact(result, controller, entry):
    return {**entry, "assessment": result["assessment"], "safety_status": result["safety_status"],
            "authority_status": result["authority_status"], "totals": result["totals"],
            "per_obligation": result["per_obligation"], "resources": result["resources"],
            "recovery_ms": result["recovery_ms"], "failures": result["failures"],
            "unresolved": result["unresolved"], "faults_observed": controller["faults_observed"],
            "implementation": controller["implementation"]}


def run_suite(out, *, comparison=False):
    out = fresh_directory(out)
    spec = specification()
    fixtures = spec["fixtures"] if comparison else [spec["fixtures"][0]]
    methods = ["conventional", "harness", "ai"] if comparison else ["harness"]
    instance_id = uuid.uuid4().hex[:12]
    index = {"schema": "continuity-harness/suite/v1", "kind": "comparison" if comparison else "demonstration",
             "experiment_id": spec["experiment_id"], "specification_sha256": digest(spec),
             "implementation": implementation_identity(), "instance_id": instance_id,
             "ai_availability": {"status": "NOT_RUN", "ollama_executable_found": shutil.which("ollama") is not None,
                                 "llama_cli_executable_found": shutil.which("llama-cli") is not None,
                                 "reason": "No already-authorized local model decider supplied. Protocol adapter exists; no model performance was simulated."},
             "entries": [], "complete": False}
    summaries = []
    attempts = open(out / "ATTEMPTS.jsonl", "xb", buffering=0)
    try:
        for fixture in fixtures:
            for scenario in ("recovery", "alternate", "constrained"):
                for method in methods:
                    rid = f"{fixture['id']}-{scenario}-{method}-{instance_id}"
                    attempts.write(canonical({"event": "START", "run_id": rid}) + b"\n")
                    contract = make_contract(fixture["id"], scenario, method, rid)
                    run = run_exercise(contract, method, out / "runs" / rid, out / "authority" / rid)
                    entry = {"run_id": rid, "fixture": fixture["id"], "held_out": fixture["held_out"],
                             "scenario": scenario, "method": method, "run_relative": f"runs/{rid}",
                             "authority_relative": f"authority/{rid}", "reference_sha256": run["reference_sha256"]}
                    index["entries"].append(entry)
                    result = conclude_run(run)
                    summaries.append(compact(result, run["controller"], entry))
                    attempts.write(canonical({"event": "FINISH", "run_id": rid, "assessment": result["assessment"]}) + b"\n")
        index["complete"] = True
    finally:
        attempts.close()
        write_json(out / "INDEX.json", index)
    summary = summarize(index, summaries)
    write_json(out / "SUMMARY.json", summary)
    for lang in ("en", "fr"):
        (out / f"SUMMARY.{lang}.md").write_text(render_summary(summary, lang), encoding="utf-8")
    return summary


def summarize(index, records):
    executed = [r for r in records if r["assessment"]["evidence_stage"] != "NOT_RUN"]
    not_run = [r for r in records if r["assessment"]["evidence_stage"] == "NOT_RUN"]
    critical = [r["run_id"] for r in executed if r["safety_status"] != "DEMONSTRATED"]
    failed_assertions = [r["run_id"] for r in executed if r["assessment"]["test_assertion"] != "PASSED"]
    pairs = []
    by_key = {(r["fixture"], r["scenario"], r["method"]): r for r in executed}
    for fixture, scenario, method in sorted(by_key):
        if method != "conventional" or (fixture, scenario, "harness") not in by_key:
            continue
        left, right = by_key[(fixture, scenario, "conventional")], by_key[(fixture, scenario, "harness")]
        signature = lambda r: [(x["order_id"], x["outcome"], x["accepted_quantity"]) for x in r["per_obligation"]]
        pairs.append({"fixture": fixture, "scenario": scenario, "functional_outcomes": "TIE" if signature(left) == signature(right) else "DIFFERENT",
                      "conventional_wall_ns": left["resources"]["wall_ns"], "harness_wall_ns": right["resources"]["wall_ns"]})
    return {"schema": "continuity-harness/results/v1", "experiment_id": index["experiment_id"],
            "specification_sha256": index["specification_sha256"], "implementation": index["implementation"],
            "complete": index["complete"], "executed_runs": len(executed), "not_run": len(not_run),
            "critical_safety_failures": critical, "failed_test_assertions": failed_assertions,
            "release_gate": "PASSED" if index["complete"] and not critical and not failed_assertions and executed else "FAILED",
            "paired_comparisons": pairs, "records": records,
            "comparative_advantage": "NOT_ESTABLISHED", "commercial_value": "NOT_ESTABLISHED",
            "ai_availability": index.get("ai_availability", {"status": "NOT_RUN", "reason": "NOT_RECORDED"}),
            "cost_accounting": {"observed": ["child_cpu_user_ns", "child_cpu_system_ns", "controller_cpu_user_ns", "controller_cpu_system_ns", "wall_ns", "execution_storage_bytes", "broker_requests", "retries", "worker_restarts"],
                                "unknown": ["preparation_labor", "integration_labor", "verification_and_reporting_cpu", "peak_memory", "monetary_cost", "real_business_cost"],
                                "rates": None, "savings_claim": "NOT_ESTABLISHED"},
            "comparison_limits": ["One registered run per method/fixture/control; descriptive timing only, no statistical speed claim.",
                                  "Shared transactional services and acceptance verifier; this comparison does not isolate a general AI contribution.",
                                  "Transfer fixtures are preregistered and source-visible, not a blind population benchmark.",
                                  "Zero human intervention describes execution only, not unmeasured development labor."]}


def _inside(root, relative):
    if type(relative) is not str or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise HarnessError("UNSAFE_PATH", str(relative))
    path = root / relative
    for parent in (path, *path.parents):
        if parent == root.parent:
            break
        if parent.is_symlink():
            raise HarnessError("UNSAFE_PATH", relative)
    return path


def verify_suite(directory):
    root = Path(directory).resolve()
    index = strict_load(root / "INDEX.json")
    object_fields(index, {"schema", "kind", "experiment_id", "specification_sha256", "implementation",
                          "instance_id", "ai_availability", "entries", "complete"}, path="suite")
    if index["schema"] != "continuity-harness/suite/v1" or index["kind"] not in ("demonstration", "comparison"):
        raise HarnessError("UNSUPPORTED_VERSION", "suite")
    boolean(index["complete"], "suite.complete")
    identifier(index["instance_id"], "suite.instance_id")
    spec = specification()
    if index["experiment_id"] != spec["experiment_id"] or index["specification_sha256"] != digest(spec):
        raise HarnessError("SPECIFICATION_MISMATCH", "suite")
    fixtures = spec["fixtures"] if index["kind"] == "comparison" else [spec["fixtures"][0]]
    methods = ("conventional", "harness", "ai") if index["kind"] == "comparison" else ("harness",)
    expected = {(f["id"], scenario, method): f["held_out"]
                for f in fixtures for scenario in ("recovery", "alternate", "constrained") for method in methods}
    if type(index["entries"]) is not list or len(index["entries"]) > len(expected):
        raise HarnessError("INVALID_TYPE", "suite.entries")
    seen = set()
    records = []
    for entry in index["entries"]:
        object_fields(entry, {"run_id", "fixture", "held_out", "scenario", "method", "run_relative",
                             "authority_relative", "reference_sha256"}, path="suite.entry")
        for name in ("run_id", "fixture", "scenario", "method"):
            identifier(entry[name], f"suite.entry.{name}")
        sha256(entry["reference_sha256"], "suite.entry.reference_sha256")
        key = (entry["fixture"], entry["scenario"], entry["method"])
        if key not in expected or key in seen:
            raise HarnessError("SUITE_ENTRY_MISMATCH", "duplicate or unregistered condition")
        seen.add(key)
        rid = f"{entry['fixture']}-{entry['scenario']}-{entry['method']}-{index['instance_id']}"
        boolean(entry["held_out"], "suite.entry.held_out")
        if entry["held_out"] != expected[key] or entry["run_id"] != rid:
            raise HarnessError("SUITE_ENTRY_MISMATCH", "identity")
        if entry["run_relative"] != f"runs/{rid}" or entry["authority_relative"] != f"authority/{rid}":
            raise HarnessError("UNSAFE_PATH", "suite.entry")
        run = _inside(root, entry["run_relative"])
        authority = _inside(root, entry["authority_relative"])
        result = verify_run(run, authority, expected_reference_sha256=entry["reference_sha256"])
        controller = strict_load(run / "controller.json")
        registered = make_contract(entry["fixture"], entry["scenario"], entry["method"], rid)
        if result["contract_sha256"] != digest(registered) or controller["method"] != entry["method"]:
            raise HarnessError("SUITE_CONTRACT_MISMATCH", rid)
        records.append(compact(result, controller, entry))
    if index["complete"] and seen != set(expected):
        raise HarnessError("SUITE_INCOMPLETE", "completed suite omits a registered condition")
    return summarize(index, records)


def render_summary(summary, language="en"):
    fr = language == "fr"
    title = "CONTINUITÉ Ω — Résultats du banc d’essai" if fr else "CONTINUITY Ω Harness — Results"
    text = [f"# {title}", "", "## " + ("Périmètre" if fr else "Scope"), "",
            ("Exécution réelle de logiciels locaux avec des données synthétiques. Les fichiers JSON produits ne sont pas des étiquettes imprimées et n’établissent aucune livraison client ni valeur commerciale." if fr else
             "Actual local software execution with synthetic data. Completed JSON artifacts are not printed labels and establish neither customer delivery nor commercial value."), "",
            f"**{'Exécutions' if fr else 'Executed runs'}:** {summary['executed_runs']} · **{'Non exécutées' if fr else 'Not run'}:** {summary['not_run']}",
            f"**{'Contrôle de publication' if fr else 'Release gate'}:** `{summary['release_gate']}`", "",
            "| " + ("Cas | Méthode | Test | Promesse complète | Unités acceptées / attendues | Temps réel (ns) | Sûreté |" if fr else
                      "Case | Method | Test | Complete promise | Accepted / expected units | Wall time (ns) | Safety |"),
            "|---|---|---|---|---|---:|---|"]
    for r in summary["records"]:
        t, a = r["totals"], r["assessment"]
        wall = r["resources"].get("wall_ns", "—")
        units = f"{t['accepted_units']} / {t['expected_units']}"
        if a["evidence_stage"] == "NOT_RUN":
            units, wall = "—", "—"
        text.append(f"| {r['fixture']} / {r['scenario']} | `{r['method']}` | `{a['test_assertion']}` | `{a['claim_status']}` | {units} | {wall} | `{r['safety_status']}` |")
    text += ["", "## " + ("Comparaison et coûts" if fr else "Comparison and costs"), "",
             ("Les codes machines sont identiques dans les deux langues. PASSED : comportement attendu observé ; DEMONSTRATED : affirmation établie dans le périmètre local ; FAILED : affirmation non satisfaite ; NOT_ESTABLISHED : preuves insuffisantes ; NOT_RUN : non exécuté." if fr else
              "Machine codes are shared between languages. PASSED means the expected test behavior was observed; DEMONSTRATED establishes the scoped local claim; FAILED means the claim was not satisfied; NOT_ESTABLISHED means insufficient evidence; NOT_RUN means not executed."), "",
             ("Une seule exécution par méthode et condition : les durées sont descriptives, sans preuve d’un avantage de vitesse. Les services transactionnels et le vérificateur sont communs. La comparaison n’isole aucun gain général attribuable à l’IA." if fr else
              "One execution per method and condition: timings are descriptive, not evidence of a speed advantage. Transactional services and the verifier are shared. The comparison isolates no general AI contribution."), "",
             ("Les temps processeur du contrôleur et des processus enfants, le temps réel, les octets d’exécution, requêtes, reprises et redémarrages sont mesurés. Les octets excluent les rapports et métadonnées finaux. Effort de préparation, intégration, vérification et présentation séparées, mémoire maximale et coûts monétaires : INCONNUS. Aucun tarif, budget commercial ou économie n’est inventé. Zéro intervention humaine concerne seulement l’exécution automatique." if fr else
              "Controller and child CPU, wall time, execution bytes, requests, retries and restarts are observed. Bytes exclude final reports and metadata. Preparation, integration, separate verification/reporting, peak memory and monetary costs are UNKNOWN. No rate, business budget or saving is invented. Zero human intervention applies only to autonomous execution."), "",
             ("IA : NON EXÉCUTÉE. Aucun modèle local déjà autorisé n’a été fourni ; l’adaptateur de protocole ne constitue pas un résultat de performance de modèle." if fr else
              "AI: NOT RUN. No already-authorized local model was supplied; protocol adapter plumbing is not a model performance result."), "",
             f"**{'Avantage comparatif' if fr else 'Comparative advantage'}:** `{summary['comparative_advantage']}`",
             f"**{'Valeur commerciale' if fr else 'Commercial value'}:** `{summary['commercial_value']}`", "",
             "## " + ("Échecs critiques et incertitudes" if fr else "Critical failures and uncertainty"), "",
             f"{'Exécutions avec sûreté non établie' if fr else 'Runs without established safety'}: {summary['critical_safety_failures']}",
             f"{'Tests attendus non réussis' if fr else 'Unmet test assertions'}: {summary['failed_test_assertions']}", "",
             ("Consulter chaque PASSPORT.fr.md et RESULT.json pour les obligations individuelles, refus, preuves, conditions et commandes de vérification fraîche. Les résultats incomplets et défavorables sont conservés." if fr else
              "Read each PASSPORT.en.md and RESULT.json for individual obligations, refusals, evidence, conditions and fresh-verification commands. Incomplete and unfavorable outcomes are preserved."), ""]
    return "\n".join(text)
