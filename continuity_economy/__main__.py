"""Complete bilingual operator interface for the separate economy experiment."""
import json
from pathlib import Path
import sys

from continuity_harness.__main__ import Parser
from . import __version__
from .schema import HarnessError

WORDS={
 "title":("CONTINUITY Ω Harness — Invent the economy of continuity — v0.2.0",
          "CONTINUITÉ Ω — Inventer l’économie de la continuité — v0.2.0"),
 "language":("Presentation language; machine keys and identifiers remain shared.","Langue de présentation ; clés et identifiants machines restent communs."),
 "experiment":("Execute the complete registered base, successor and challenge experiment.","Exécuter l’expérience préenregistrée complète : base, successeur et contrôles contradictoires."),
 "demo":("Execute the seven registered base cases with the Harness procedure.","Exécuter les sept cas de base préenregistrés avec la procédure du banc d’essai."),
 "compare":("Compare conventional, Harness and no-purchase procedures; record unavailable AI as NOT RUN.","Comparer les procédures conventionnelle, du banc d’essai et sans achat ; consigner l’IA indisponible comme NON EXÉCUTÉE."),
 "successor":("Execute the separately registered successor using the same interfaces and methods.","Exécuter le successeur préenregistré séparément avec les mêmes interfaces et méthodes."),
 "challenge":("Execute and retain arrangement counterexamples and targeted verifier mutations.","Exécuter et conserver les contre-exemples de solutions et les mutations ciblées du vérificateur."),
 "run":("Execute one registered fixture with an explicitly selected method.","Exécuter un cas préenregistré avec une méthode explicitement choisie."),
 "verify":("Independently recheck actual durable content, participant decisions and funding against the retained authority.","Revérifier indépendamment le contenu durable, les décisions des participants et le financement selon l’autorité conservée."),
 "verify-suite":("Freshly verify every required indexed cell; saved Passports and favorable labels are not proof.","Revérifier chaque cellule requise ; passeports enregistrés et mentions favorables ne constituent pas une preuve."),
 "out":("New output directory outside the source checkout; existing attempts are never overwritten.","Nouveau répertoire hors du code source ; les tentatives existantes ne sont jamais écrasées."),
 "fixture":("Registered fixture identifier.","Identifiant du cas préenregistré."),
 "method":("Candidate method; ai is explicitly NOT RUN without an authorized local capability.","Méthode candidate ; ai reste explicitement NON EXÉCUTÉE sans capacité locale autorisée."),
 "run_dir":("Run directory with actual durable evidence.","Répertoire de l’exécution contenant les preuves durables."),
 "authority":("Separately retained authority directory.","Répertoire de l’autorité conservé séparément."),
 "pin":("Original externally retained reference SHA-256; omission prevents a favorable assessment.","SHA-256 original de la référence conservé séparément ; son absence interdit une appréciation favorable."),
 "input":("Directory of a completed or incomplete experiment/suite.","Répertoire d’une expérience ou suite achevée ou incomplète."),
 "help":("Show complete help and exit.","Afficher l’aide complète et quitter."),
 "version":("Show the separately versioned experiment version.","Afficher la version distincte de l’expérience."),
 "result":("Assessment recorded. Outcome, modeled service feasibility and method advantage are separate; synthetic economics establish no real sale or demand.","Évaluation consignée. Résultat, faisabilité du service modélisé et avantage de méthode sont distincts ; l’économie synthétique n’établit aucune vente ni demande réelle."),
 "error":("The command did not complete. No favorable assessment is established; retain any incomplete attempt and consult --help.","La commande n’a pas abouti. Aucune appréciation favorable n’est établie ; conserver toute tentative incomplète et consulter --help."),
}


def output_guard(path):
    root=Path(__file__).resolve().parents[1]
    p=Path(path).absolute()
    if ".." in p.parts or any(x.is_symlink() for x in (p,*p.parents)):
        raise HarnessError("UNSAFE_PATH")
    if p==root or root in p.parents:raise HarnessError("OUTPUT_IN_SOURCE_TREE")
    if p.exists():raise HarnessError("OUTPUT_EXISTS")
    return p


def main(argv=None):
    args=list(sys.argv[1:] if argv is None else argv)
    requested=[]
    for i,item in enumerate(args):
        if item.startswith("--language="):requested.append(item.split("=",1)[1])
        elif item=="--language" and i+1<len(args):requested.append(args[i+1])
    language="fr" if requested and requested[-1]=="fr" else "en"
    word=lambda k:WORDS[k][language=="fr"]
    parser=Parser(prog="python3 -m continuity_economy",description=word("title"),language=language,add_help=False)
    parser.add_argument("-h","--help",action="help",help=word("help"))
    parser.add_argument("--language",choices=("en","fr"),default="en",help=word("language"))
    parser.add_argument("--version",action="version",version=__version__,help=word("version"))
    sub=parser.add_subparsers(dest="command",required=True,parser_class=lambda **kw:Parser(language=language,**kw))
    for command in ("experiment","demo","compare","successor","challenge","run","verify","verify-suite"):
        p=sub.add_parser(command,description=word(command),help=word(command),add_help=False)
        p.add_argument("-h","--help",action="help",help=word("help"))
        if command in ("experiment","demo","compare","successor","challenge","run"):
            p.add_argument("--out",required=True,help=word("out"))
            if command=="run":
                p.add_argument("--fixture",required=True,help=word("fixture"))
                p.add_argument("--method",choices=("conventional","harness","outside","ai"),required=True,help=word("method"))
        elif command=="verify":
            p.add_argument("--run",required=True,help=word("run_dir"))
            p.add_argument("--authority",required=True,help=word("authority"))
            p.add_argument("--reference-sha256",help=word("pin"))
        else:p.add_argument("--in-dir",required=True,help=word("input"))
    options=parser.parse_args(args)
    try:
        if hasattr(options,"out"):output_guard(options.out)
        if options.command=="experiment":
            from .suite import experiment
            response=experiment(options.out)
        elif options.command in ("demo","compare","successor"):
            from .suite import run_suite
            result=run_suite(options.out,"demo" if options.command=="demo" else "comparison","successor" if options.command=="successor" else "base")
            response={k:result[k] for k in ("schema","version","kind","cohort","test_assertion","executed_method_records","ai_not_run_records","comparisons","failed_assertions","critical_safety_failures","claims")}
        elif options.command=="challenge":
            from .challenges import run_challenges
            response=run_challenges(options.out)
        elif options.command=="run":
            from .fixtures import load_fixture
            from .suite import run_case
            from continuity_harness.controller import fresh_directory
            fixture=load_fixture(options.fixture)
            root=fresh_directory(options.out)
            response,pin=run_case(fixture,options.method,root/"run",root/"authority")
            response["reference_sha256"]=pin
        elif options.command=="verify-suite":
            from .suite import verify_suite
            response=verify_suite(options.in_dir)
        else:
            from .verifier import verify_run
            response=verify_run(options.run,options.authority,expected_reference_sha256=options.reference_sha256)
        response["language"]=language;response["message"]=word("result")
        print(json.dumps(response,ensure_ascii=False,indent=2))
        if "test_assertion" in response:return 0 if response["test_assertion"]=="PASSED" else 3
        if "registered_assertion" in response:return 0 if response["registered_assertion"]["status"]=="PASSED" else 3
        return 0 if response.get("claims",{}).get("outcome")=="DEMONSTRATED" and response.get("claims",{}).get("service_feasibility")=="DEMONSTRATED" else 3
    except Exception as error:
        code=getattr(error,"code","OUTPUT_EXISTS" if isinstance(error,FileExistsError) else "ECONOMY_COMMAND_FAILED")
        print(json.dumps({"code":code,"message":word("error"),"detail":str(error)[:300]},ensure_ascii=False),file=sys.stderr)
        return 2


if __name__=="__main__":raise SystemExit(main())
