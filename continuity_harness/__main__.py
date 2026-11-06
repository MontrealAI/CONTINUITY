"""Complete bilingual local Harness command line."""

import argparse
import json
from pathlib import Path
import sys

from . import __version__
from .schema import HarnessError


WORDS = {
    "title": ("CONTINUITY Ω Harness v0.1 — actual local execution and fresh verification", "CONTINUITÉ Ω — Banc d’essai et de vérification v0.1 — exécution locale et vérification fraîche"),
    "language": ("Presentation language; machine identifiers remain shared.", "Langue de présentation ; les identifiants machines restent communs."),
    "demo": ("Execute the three registered base controls.", "Exécuter les trois contrôles de base préenregistrés."),
    "compare": ("Run the registered conventional/Harness suite and explicit AI NOT RUN records.", "Exécuter la comparaison préenregistrée et consigner explicitement l’IA non exécutée."),
    "challenge": ("Preserve adversarial, ablation and verifier-mutation observations with bilingual reports.", "Conserver les observations adversariales, d’ablation et de mutation du vérificateur avec des rapports bilingues."),
    "verify": ("Verify current durable evidence against an independently retained reference.", "Vérifier les preuves durables actuelles par rapport à une référence conservée séparément."),
    "verify-suite": ("Freshly verify all indexed runs; saved results are not trusted.", "Revérifier toutes les exécutions répertoriées ; les résultats enregistrés ne font pas foi."),
    "out": ("New output directory; existing evidence is never overwritten.", "Nouveau répertoire de sortie ; aucune preuve existante n’est écrasée."),
    "run": ("Run directory containing current durable evidence.", "Répertoire de l’exécution et de ses preuves durables actuelles."),
    "authority": ("Separately retained authority directory.", "Répertoire de l’autorité conservé séparément."),
    "pin": ("Externally retained canonical SHA-256 of reference.json; omission prevents a favorable assessment.", "SHA-256 canonique de reference.json conservé séparément ; son absence interdit une appréciation favorable."),
    "input": ("Completed or incomplete suite directory.", "Répertoire de la suite, achevée ou incomplète."),
    "help": ("Show this help and exit.", "Afficher cette aide et quitter."),
    "version": ("Show the separately versioned Harness version.", "Afficher la version distincte du banc d’essai."),
    "error": ("The command could not complete; no favorable result is implied.", "La commande n’a pas abouti ; aucun résultat favorable n’en découle."),
}


class Parser(argparse.ArgumentParser):
    def __init__(self, *args, language="en", **kwargs):
        self.language = language
        super().__init__(*args, **kwargs)
        self._positionals.title = "commands" if language == "en" else "commandes"
        self._optionals.title = "options"

    def format_help(self):
        value = super().format_help()
        return value.replace("usage:", "utilisation :", 1) if self.language == "fr" else value

    def error(self, message):
        # Argparse's English diagnostic is kept only as a technical detail;
        # the complete operator action is localized and the code stable.
        detail = message if self.language == "en" else "Arguments invalides. Consulter --help pour les commandes et paramètres requis."
        sys.stderr.write(json.dumps({"code": "CLI_ARGUMENT_ERROR", "message": detail}, ensure_ascii=False) + "\n")
        raise SystemExit(2)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    requested_languages = []
    for i, value in enumerate(args):
        if value.startswith("--language="):
            requested_languages.append(value.split("=", 1)[1])
        elif value == "--language" and i + 1 < len(args):
            requested_languages.append(args[i + 1])
    language = "fr" if requested_languages and requested_languages[-1] == "fr" else "en"
    word = lambda key: WORDS[key][1 if language == "fr" else 0]
    p = Parser(prog="python3 -m continuity_harness", description=word("title"), language=language, add_help=False)
    p.add_argument("-h", "--help", action="help", help=word("help"))
    p.add_argument("--language", choices=("en", "fr"), default="en", help=word("language"))
    p.add_argument("--version", action="version", version=__version__, help=word("version"))
    sub = p.add_subparsers(dest="command", required=True, parser_class=lambda **kw: Parser(language=language, **kw))
    for command in ("demo", "compare", "challenge", "verify", "verify-suite"):
        item = sub.add_parser(command, help=word(command), description=word(command), add_help=False)
        item.add_argument("-h", "--help", action="help", help=word("help"))
        if command in ("demo", "compare", "challenge"):
            item.add_argument("--out", required=True, help=word("out"))
        elif command == "verify":
            item.add_argument("--run", required=True, help=word("run"))
            item.add_argument("--authority", required=True, help=word("authority"))
            item.add_argument("--reference-sha256", help=word("pin"))
        else:
            item.add_argument("--in-dir", required=True, help=word("input"))
    options = p.parse_args(args)
    try:
        if options.command == "challenge":
            from .challenges import run_challenges
            response = run_challenges(options.out)
            code = 0 if response["release_gate"] == "PASSED" else 3
        elif options.command in ("demo", "compare"):
            from .suite import run_suite
            result = run_suite(options.out, comparison=options.command == "compare")
            response = {"output": str(Path(options.out).absolute()), "release_gate": result["release_gate"],
                        "executed_runs": result["executed_runs"], "not_run": result["not_run"],
                        "comparative_advantage": result["comparative_advantage"], "commercial_value": result["commercial_value"]}
            code = 0 if result["release_gate"] == "PASSED" else 3
        elif options.command == "verify-suite":
            from .suite import verify_suite
            result = verify_suite(options.in_dir)
            response = {"release_gate": result["release_gate"], "executed_runs": result["executed_runs"],
                        "not_run": result["not_run"], "failed_test_assertions": result["failed_test_assertions"],
                        "critical_safety_failures": result["critical_safety_failures"], "fresh_verification": True}
            code = 0 if result["release_gate"] == "PASSED" else 3
        else:
            from .verifier import verify_run
            response = verify_run(options.run, options.authority, expected_reference_sha256=options.reference_sha256)
            code = 0 if response["assessment"]["claim_status"] == "DEMONSTRATED" else 3
        print(json.dumps(response, ensure_ascii=False, indent=2))
        return code
    except (HarnessError, OSError, ValueError, KeyError, TypeError) as error:
        code = getattr(error, "code", "OUTPUT_EXISTS" if isinstance(error, FileExistsError) else "HARNESS_COMMAND_FAILED")
        print(json.dumps({"code": code, "message": word("error"), "detail": str(error)[:500]}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
