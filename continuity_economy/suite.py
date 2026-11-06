"""Registered runs, exact coverage checks and separate fresh verification."""
from copy import deepcopy
from datetime import datetime,timezone
import hashlib
from pathlib import Path
import time
import uuid

from continuity_harness.controller import fresh_directory,write_json
from . import __version__
from .fixtures import EXPERIMENT,ROOT,load_fixture
from .schema import HarnessError,canonical,digest,object_fields,strict_load,validate_contract,validate_policies

METHODS=("conventional","harness","outside","ai")


def registry(cohort="base"):
    if cohort not in ("base","successor"):raise HarnessError("UNKNOWN_COHORT")
    path=EXPERIMENT/("spec.json" if cohort=="base" else "successor.json")
    return strict_load(path),hashlib.sha256(path.read_bytes()).hexdigest()


def cohort_fixture(name,cohort="base"):
    if cohort=="base":return load_fixture(name)
    spec,_=registry(cohort)
    entry=next((f for f in spec["fixtures"] if f["id"]==name),None)
    if entry is None:raise HarnessError("UNKNOWN_FIXTURE",name)
    path=EXPERIMENT/entry["file"]
    if hashlib.sha256(path.read_bytes()).hexdigest()!=entry["sha256"]:raise HarnessError("REGISTERED_FIXTURE_CHANGED",name)
    result=strict_load(path);validate_contract(result["contract"]);validate_policies(result["policies"])
    return result


def expected_for(fixture,method):
    if method=="ai":return {"outcome":"NOT_ESTABLISHED","service_feasibility":"NOT_ESTABLISHED","accepted_units":0}
    if method=="outside":return {"outcome":"FAILED","service_feasibility":"NOT_ESTABLISHED","accepted_units":0}
    return fixture["expected"]


def accepted_units(result):
    totals=result.get("totals",{})
    if "accepted_units" in totals:return totals["accepted_units"]
    if "accepted_quantity" in totals:return totals["accepted_quantity"]
    return sum(o.get("accepted_quantity",o.get("accepted_units",0)) for o in result.get("per_obligation",[]))


def assess(result,expected,method):
    observed={"outcome":result.get("claims",{}).get("outcome"),
              "service_feasibility":result.get("claims",{}).get("service_feasibility"),
              "accepted_units":accepted_units(result)}
    ok=observed==expected and not result.get("critical_safety_failures",[])
    if result.get("safety_status")=="FAILED":ok=False
    if method=="ai":
        ok=ok and result.get("assessment",{}).get("target_verdict")=="NOT_RUN"
    return {"status":"PASSED" if ok else "FAILED","expected":expected,"observed":observed,
            "scope":"Registered assessment assertion; not a favorable outcome or trade claim."}


def run_case(fixture,method,run_dir,authority_dir):
    from .controller import Controller
    from .verifier import verify_run
    from .reporting import write_passports
    contract=deepcopy(fixture["contract"])
    contract["run_id"]=f'{contract["fixture_id"]}.{method}.{uuid.uuid4().hex[:10]}'
    contract["start_ns"]=time.monotonic_ns()
    controller=Controller(contract,deepcopy(fixture["policies"]),method,run_dir,authority_dir)
    record=controller.run()
    start=time.monotonic_ns()
    result=verify_run(run_dir,authority_dir,expected_reference_sha256=controller.reference_sha256)
    verification_ns=time.monotonic_ns()-start
    assertion=assess(result,expected_for(fixture,method),method)
    result.setdefault("assessment",{})["test_assertion"]="NOT_RUN" if method=="ai" else assertion["status"]
    result["registered_assertion"]=assertion
    result["verification_wall_ns"]=verification_ns
    result["source_version"]=record.get("implementation",{})
    result["reference_sha256"]=controller.reference_sha256
    result["fixture_id"]=contract["fixture_id"];result["method"]=method
    result["cohort"]=contract["cohort"]
    result["contract_sha256"]=digest(contract)
    write_json(Path(run_dir)/"RESULT.json",result)
    write_passports(result,run_dir,context={"controller":record,"contract":contract,
                                         "policies":fixture["policies"],"reference_sha256":controller.reference_sha256,
                                         "authority_dir":str(Path(authority_dir).absolute())})
    return result,controller.reference_sha256


def compact(result,assertion=None):
    return {"fixture_id":result.get("fixture_id"),"method":result.get("method"),"cohort":result.get("cohort"),
            "assessment":result.get("assessment"),"claims":result.get("claims"),"safety_status":result.get("safety_status"),
            "totals":result.get("totals"),"per_obligation":result.get("per_obligation"),
            "resources":result.get("resources",{}),"accounting":result.get("accounting",{}),
            "failures":result.get("failures",[]),"unresolved":result.get("unresolved",[]),
            "registered_assertion":assertion or result.get("registered_assertion"),
            "verification_wall_ns":result.get("verification_wall_ns")}


def summarize(entries,kind,cohort):
    failed=[e for e in entries if e["registered_assertion"]["status"]!="PASSED"]
    unsafe=[{"fixture_id":e["fixture_id"],"method":e["method"],"failures":e["failures"]} for e in entries if e.get("safety_status")=="FAILED"]
    pairs=[]
    for name in sorted({e["fixture_id"] for e in entries}):
        methods={e["method"]:e for e in entries if e["fixture_id"]==name}
        if "conventional" in methods and "harness" in methods:
            a,b=methods["conventional"],methods["harness"]
            same=(a["claims"].get("outcome"),a["claims"].get("service_feasibility"),accepted_units(a)) == (b["claims"].get("outcome"),b["claims"].get("service_feasibility"),accepted_units(b))
            pairs.append({"fixture_id":name,"functional_result":"TIE" if same else "DIFFERENT","method_advantage":"NOT_ESTABLISHED"})
    return {"schema":"continuity-economy/suite-result/v1","version":__version__,"kind":kind,"cohort":cohort,
            "test_assertion":"FAILED" if failed or unsafe else "PASSED","failed_assertions":[{"fixture_id":e["fixture_id"],"method":e["method"],"assertion":e["registered_assertion"]} for e in failed],
            "critical_safety_failures":unsafe,"executed_method_records":sum(e["method"]!="ai" for e in entries),
            "ai_not_run_records":sum(e["method"]=="ai" for e in entries),"comparisons":pairs,"runs":entries,
            "claims":{"method_advantage":"NOT_ESTABLISHED","real_market_viability":"NOT_ESTABLISHED","real_customer_demand":"NOT_ESTABLISHED"},
            "limitations":["AUTHORED_SYNTHETIC_ECONOMICS","SEMANTIC_DIGITAL_CONTENT_ONLY","ONE_OBSERVATION_PER_CELL","FIXED_METHOD_ORDER","PREPARATION_AND_ADAPTATION_LABOR_UNKNOWN"]}


def run_suite(out_dir,kind="comparison",cohort="base"):
    if kind not in ("comparison","demo"):raise HarnessError("UNKNOWN_SUITE_KIND")
    spec,spec_sha=registry(cohort)
    methods=list(METHODS) if kind=="comparison" else ["harness"]
    root=fresh_directory(out_dir)
    (root/"runs").mkdir();(root/"authorities").mkdir()
    index={"schema":"continuity-economy/suite-index/v1","version":__version__,"kind":kind,"cohort":cohort,
           "registry_sha256":spec_sha,"methods":methods,"fixture_ids":[f["id"] for f in spec["fixtures"]],
           "created_utc":datetime.now(timezone.utc).isoformat(),"entries":[]}
    entries=[]
    for item in spec["fixtures"]:
        fixture=cohort_fixture(item["id"],cohort)
        for method in methods:
            name=f'{item["id"]}.{method}'
            result,pin=run_case(fixture,method,root/"runs"/name,root/"authorities"/name)
            index["entries"].append({"fixture_id":item["id"],"method":method,"run":"runs/"+name,
                                     "authority":"authorities/"+name,"reference_sha256":pin})
            entries.append(compact(result))
            # Preserve progress even if a later process or verification fails.
            write_json(root/f'INDEX.progress-{len(entries):03d}.json',index)
    write_json(root/"INDEX.json",index)
    summary=summarize(entries,kind,cohort)
    write_json(root/"SUMMARY.json",summary)
    return summary


def safe_relative(root,name):
    if type(name) is not str or not name or name.startswith("/") or "\\" in name:
        raise HarnessError("UNSAFE_PATH",str(name))
    p=Path(name)
    if any(part in (".","..","") for part in name.split("/")):raise HarnessError("UNSAFE_PATH",name)
    result=root/p
    if any(x.is_symlink() for x in (result,*result.parents)):raise HarnessError("UNSAFE_PATH",name)
    return result


def verify_suite(in_dir):
    from .verifier import verify_run
    root=Path(in_dir).absolute();index=strict_load(root/"INDEX.json")
    if index.get("schema")=="continuity-economy/experiment-index/v1":
        object_fields(index,{"schema","version","members"})
        if set(index["members"])!={"base","successor","challenges"}:raise HarnessError("SUITE_COVERAGE")
        values={name:verify_suite(safe_relative(root,path)) for name,path in index["members"].items()}
        return {"schema":"continuity-economy/experiment-result/v1","fresh":True,"test_assertion":"PASSED" if all(v["test_assertion"]=="PASSED" for v in values.values()) else "FAILED","members":values}
    if index.get("schema")=="continuity-economy/challenge-index/v1":
        from .challenges import verify_challenges
        return verify_challenges(root)
    object_fields(index,{"schema","version","kind","cohort","registry_sha256","methods","fixture_ids","created_utc","entries"})
    if index["schema"]!="continuity-economy/suite-index/v1" or index["version"]!=__version__:raise HarnessError("UNSUPPORTED_VERSION")
    spec,spec_sha=registry(index["cohort"])
    required_methods=list(METHODS) if index["kind"]=="comparison" else ["harness"] if index["kind"]=="demo" else None
    if required_methods is None or index["methods"]!=required_methods:raise HarnessError("SUITE_COVERAGE")
    required_names=[f["id"] for f in spec["fixtures"]]
    if index["registry_sha256"]!=spec_sha or index["fixture_ids"]!=required_names:raise HarnessError("REGISTRY_MISMATCH")
    expected={(name,m) for name in required_names for m in required_methods}
    actual=[];entries=[]
    for e in index["entries"]:
        object_fields(e,{"fixture_id","method","run","authority","reference_sha256"})
        key=(e["fixture_id"],e["method"])
        if key not in expected or key in actual:raise HarnessError("SUITE_COVERAGE")
        actual.append(key)
        result=verify_run(safe_relative(root,e["run"]),safe_relative(root,e["authority"]),expected_reference_sha256=e["reference_sha256"])
        # A relabelled, mixed-run or repeated cell cannot replace a missing cell.
        record=strict_load(safe_relative(root,e["run"])/"controller.json")
        contract=strict_load(safe_relative(root,e["authority"])/"contract.json")
        if record.get("method")!=e["method"] or contract.get("fixture_id")!=e["fixture_id"] or contract.get("cohort")!=index["cohort"]:
            raise HarnessError("SUITE_CELL_BINDING")
        fixture=cohort_fixture(e["fixture_id"],index["cohort"])
        original=deepcopy(fixture["contract"]);original["run_id"]=contract["run_id"];original["start_ns"]=contract["start_ns"]
        if contract!=original:raise HarnessError("REGISTERED_CONTRACT_MISMATCH")
        if strict_load(safe_relative(root,e["authority"])/"policies.json")!=fixture["policies"]:raise HarnessError("REGISTERED_POLICY_MISMATCH")
        assertion=assess(result,expected_for(fixture,e["method"]),e["method"])
        result.setdefault("assessment",{})["test_assertion"]="NOT_RUN" if e["method"]=="ai" else assertion["status"]
        result.update(fixture_id=e["fixture_id"],method=e["method"],cohort=index["cohort"])
        entries.append(compact(result,assertion))
    if set(actual)!=expected:raise HarnessError("SUITE_COVERAGE")
    result=summarize(entries,index["kind"],index["cohort"]);result["fresh"]=True
    return result


def experiment(out_dir):
    # Admission requires the separately registered successor; it must never be
    # invented from a base answer or silently omitted by the complete command.
    registry("successor")
    from .challenges import run_challenges
    root=fresh_directory(out_dir)
    base=run_suite(root/"base","comparison","base")
    successor=run_suite(root/"successor","comparison","successor")
    challenges=run_challenges(root/"challenges")
    write_json(root/"INDEX.json",{"schema":"continuity-economy/experiment-index/v1","version":__version__,
                                  "members":{"base":"base","successor":"successor","challenges":"challenges"}})
    result={"schema":"continuity-economy/experiment-result/v1","version":__version__,
            "test_assertion":"PASSED" if all(x["test_assertion"]=="PASSED" for x in (base,successor,challenges)) else "FAILED",
            "members":{"base":{"test_assertion":base["test_assertion"]},"successor":{"test_assertion":successor["test_assertion"]},"challenges":{"test_assertion":challenges["test_assertion"]}}}
    write_json(root/"SUMMARY.json",result)
    return result
