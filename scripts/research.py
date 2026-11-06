#!/usr/bin/env python3
"""Localized maintenance interface; interface de maintenance bilingue.

The manifest-bound historical tools remain unchanged. Their raw diagnostics
are deliberately not translated. See docs/RESEARCH_TOOLS.md and its French pair.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import BinaryIO

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "docs" / "continuity-omega-paper"
SCRIPTS = {
    "verify": "verify.py", "build": "build.py", "package": "package.py",
    "reproduce": "reproduce.py", "counterexamples": "counterexamples.py",
    "pooling": "pooling_example.py",
}
# Every executable local dependency is part of the preserved publication.
HISTORICAL_SCRIPTS = (*SCRIPTS.values(), "check_translations.py")
VALUES = {"--language", "--paper-language", "--output", "--source277", "--source278", "--raw-log"}
SWITCHES = {"--help", "--check-build", "--download-sources"}
COMMON = {"--language", "--raw-log", "--help"}
OPTIONS = {
    "verify": {"--check-build"}, "build": {"--paper-language"},
    "package": {"--output"},
    "reproduce": {"--output", "--source277", "--source278", "--download-sources"},
    "counterexamples": {"--output", "--source278"}, "pooling": set(),
}
TEXT = {
    "en": {
        "usage": "usage: python3 scripts/research.py COMMAND [OPTIONS]",
        "help": """CONTINUITY Ω research tools

Commands (stable identifiers in both languages):
  verify           Check publication identity, recorded scope and arithmetic.
    --check-build  Also compare both rebuilt PDFs with their canonical text.
  build            Build manuscripts in docs/continuity-omega-paper/build/.
    --paper-language en|fr|all  Manuscripts to build (default: all).
  package          Package the verified historical publication.
    --output PATH  Required new absolute directory outside this repository.
  reproduce        Replay pinned synthetic research, not live operations.
    --output PATH  Required new absolute directory outside this repository.
    --source277 PATH --source278 PATH  Both local snapshots for offline use.
    --download-sources  Explicitly allow downloading missing public snapshots.
  counterexamples  Replay weaknesses; success is NOT checker qualification.
    --source278 PATH  Required local historical snapshot.
    --output PATH    Required new absolute directory outside this repository.
  pooling          Compute the authored, fixed-period pooling illustration.

Common options, before or after the command:
  --language en|fr  Interface language (default: en); NOT manuscript language.
  --raw-log PATH    Save untranslated technical stdout/stderr in a NEW absolute
                   file outside the repository and supplied source snapshots.
                   Its parent directory must already exist.
  -h, --help       Show this help without executing a historical tool.

Historical scripts, machine-readable evidence and diagnostic logs retain their
original technical text. Without --raw-log, captured tool output is discarded;
the interface prints a localized outcome, not translated historical diagnostics.
No arbitrary command, extra argument, --publish or canonical-PDF update is allowed.
See docs/RESEARCH_TOOLS.md. A successful run is not operational certification.
Aide en français : python3 scripts/research.py --language fr --help""",
        "refused": "Invocation refused: {detail}",
        "unknown": "unknown argument {value}.",
        "duplicate": "option repeated: {value}.",
        "value": "a value is required for {value}.",
        "language": "--language must be en or fr.",
        "paper_language": "--paper-language must be en, fr or all.",
        "command": "choose exactly one command: {value}.",
        "unsupported": "{value} is not supported by this command.",
        "required": "required option: {value}.",
        "downloads": "provide both --source277 and --source278, or explicitly use --download-sources.",
        "path": "invalid or inaccessible path for {value}.",
        "absolute": "{value} must be an absolute path.",
        "exists": "{value} must be new; existing paths and symbolic links are refused.",
        "protected": "{value} must be outside the repository and supplied source snapshots.",
        "source": "{value} must name an existing source directory.",
        "parent": "the parent directory of --raw-log must already exist.",
        "overlap": "--raw-log must be outside --output so it cannot create or change the output directory.",
        "identity": "historical script identity is missing, changed or inaccessible; restore the published bytes.",
        "build_path": "the build directory must be a regular directory without symbolic links.",
        "start": "Running: {value}.",
        "build_notice": "Generated build files may be replaced in {value}; canonical PDFs are not published.",
        "network_notice": "Missing pinned public sources may be downloaded; the synthetic fixtures then run offline.",
        "failure": "{value} failed (exit code {code}). No successful result is established.",
        "launch": "The tool could not be started. Check Python and the documented dependencies.",
        "interrupted": "Execution interrupted; outputs may be incomplete.",
        "log": "Raw technical output, untranslated: {value}",
        "no_log": "Raw technical output was not saved. Use --raw-log with a new absolute file on a future run.",
        "output": "Requested output directory (may be partial on failure): {value}",
        "success": {
            "verify": "Publication consistency checks passed. This does not rerun the source prototypes or certify operations.",
            "build": "The requested manuscripts were built. Canonical PDFs remain unchanged; no publication was performed.",
            "package": "The verified historical publication was packaged. The new maintenance interface is not part of that historical ZIP.",
            "reproduce": "The pinned synthetic engineering results were reproduced. No live recovery, delivery or commerce was demonstrated.",
            "counterexamples": "The expected historical observations and weaknesses were reproduced. This is NOT checker qualification.",
            "pooling": "The authored pooling illustration was computed. It does not establish prices, demand, scheduling or commerce; numerical JSON is available through --raw-log.",
        },
    },
    "fr": {
        "usage": "utilisation : python3 scripts/research.py COMMANDE [OPTIONS]",
        "help": """Outils de recherche CONTINUITÉ Ω

Commandes (identifiants stables dans les deux langues) :
  verify           Vérifier l’identité de la publication, la portée et les calculs consignés.
    --check-build  Comparer aussi le texte des deux PDF reconstruits aux versions canoniques.
  build            Compiler dans docs/continuity-omega-paper/build/.
    --paper-language en|fr|all  Articles à compiler (par défaut : all).
  package          Créer le paquet de la publication historique vérifiée.
    --output CHEMIN  Nouveau répertoire absolu requis, hors de ce dépôt.
  reproduce        Reproduire la recherche synthétique figée, sans activité réelle.
    --output CHEMIN  Nouveau répertoire absolu requis, hors de ce dépôt.
    --source277 CHEMIN --source278 CHEMIN  Deux sources locales pour le mode hors ligne.
    --download-sources  Autoriser explicitement le téléchargement des sources publiques manquantes.
  counterexamples  Reproduire les faiblesses ; réussir ne qualifie PAS le vérificateur.
    --source278 CHEMIN  Source historique locale requise.
    --output CHEMIN     Nouveau répertoire absolu requis, hors de ce dépôt.
  pooling          Calculer l’illustration de mutualisation rédigée pour une période fixe.

Options communes, avant ou après la commande :
  --language en|fr  Langue de l’interface (par défaut : en), PAS celle de l’article.
  --raw-log CHEMIN  Conserver les sorties techniques non traduites dans un NOUVEAU
                   fichier absolu, hors du dépôt et des sources locales fournies.
                   Son répertoire parent doit déjà exister.
  -h, --help       Afficher cette aide sans exécuter d’outil historique.

Les scripts historiques, les preuves lisibles par machine et les journaux gardent
leur texte technique d’origine. Sans --raw-log, les sorties de l’outil sont écartées ;
l’interface affiche un bilan localisé, pas une traduction des diagnostics historiques.
Aucune commande arbitraire, option supplémentaire, option --publish ou mise à jour
des PDF canoniques n’est permise. Voir docs/RESEARCH_TOOLS.fr.md.
Une exécution réussie ne constitue pas une certification opérationnelle.
English help: python3 scripts/research.py --language en --help""",
        "refused": "Invocation refusée : {detail}",
        "unknown": "argument inconnu {value}.",
        "duplicate": "option répétée : {value}.",
        "value": "une valeur est requise pour {value}.",
        "language": "--language doit valoir en ou fr.",
        "paper_language": "--paper-language doit valoir en, fr ou all.",
        "command": "choisir exactement une commande : {value}.",
        "unsupported": "{value} n’est pas pris en charge par cette commande.",
        "required": "option requise : {value}.",
        "downloads": "fournir --source277 et --source278, ou utiliser explicitement --download-sources.",
        "path": "chemin invalide ou inaccessible pour {value}.",
        "absolute": "{value} doit être un chemin absolu.",
        "exists": "{value} doit être nouveau ; les chemins existants et les liens symboliques sont refusés.",
        "protected": "{value} doit se trouver hors du dépôt et des répertoires de sources fournis.",
        "source": "{value} doit désigner un répertoire de sources existant.",
        "parent": "le répertoire parent de --raw-log doit déjà exister.",
        "overlap": "--raw-log doit se trouver hors de --output pour ne pas créer ou modifier le répertoire de sortie.",
        "identity": "l’identité d’un script historique est absente, modifiée ou inaccessible ; restaurer les octets publiés.",
        "build_path": "le répertoire de compilation doit être un répertoire ordinaire sans liens symboliques.",
        "start": "Exécution : {value}.",
        "build_notice": "Les fichiers de compilation peuvent être remplacés dans {value} ; les PDF canoniques ne sont pas publiés.",
        "network_notice": "Les sources publiques figées manquantes peuvent être téléchargées ; les cas synthétiques s’exécutent ensuite hors ligne.",
        "failure": "Échec de {value} (code de sortie {code}). Aucun résultat réussi n’est établi.",
        "launch": "Impossible de démarrer l’outil. Vérifier Python et les dépendances documentées.",
        "interrupted": "Exécution interrompue ; les sorties peuvent être incomplètes.",
        "log": "Sortie technique brute, non traduite : {value}",
        "no_log": "La sortie technique brute n’a pas été conservée. Utiliser --raw-log avec un nouveau fichier absolu lors d’une prochaine exécution.",
        "output": "Répertoire de sortie demandé (potentiellement incomplet en cas d’échec) : {value}",
        "success": {
            "verify": "Les contrôles de cohérence de la publication ont réussi. Ils ne réexécutent pas les prototypes sources et ne certifient aucune activité réelle.",
            "build": "Les articles demandés ont été compilés. Les PDF canoniques sont inchangés ; aucune publication n’a été effectuée.",
            "package": "La publication historique vérifiée a été empaquetée. La nouvelle interface de maintenance n’appartient pas à cette archive historique.",
            "reproduce": "Les résultats d’ingénierie synthétique figés ont été reproduits. Aucun rétablissement réel, livraison ou commerce n’a été démontré.",
            "counterexamples": "Les observations et faiblesses historiques attendues ont été reproduites. Cela ne qualifie PAS le vérificateur.",
            "pooling": "L’illustration rédigée de mutualisation a été calculée. Elle n’établit ni prix, ni demande, ni ordonnancement, ni commerce ; les résultats numériques JSON sont accessibles avec --raw-log.",
        },
    },
}


class InvocationError(ValueError):
    def __init__(self, key: str, value: str = ""):
        self.key, self.value = key, value
        super().__init__(key)


def selected_language(argv: list[str]) -> str:
    """Choose the diagnostic language even when an earlier argument is invalid."""
    language = "en"
    for index, token in enumerate(argv):
        candidate = token.partition("=")[2] if token.startswith("--language=") else (
            argv[index + 1] if token == "--language" and index + 1 < len(argv) else "")
        if candidate in TEXT:
            language = candidate
    return language


def parse(argv: list[str]) -> tuple[str | None, dict]:
    options, command, index = {}, None, 0
    while index < len(argv):
        token = "--help" if argv[index] == "-h" else argv[index]
        name, equals, inline = token.partition("=")
        if name in VALUES | SWITCHES:
            if name in options:
                raise InvocationError("duplicate", name)
            if name in VALUES:
                if not equals:
                    index += 1
                    if index >= len(argv) or argv[index].startswith("-"):
                        raise InvocationError("value", name)
                value = inline if equals else argv[index]
                if not value:
                    raise InvocationError("value", name)
                options[name] = value
            elif equals:
                raise InvocationError("unknown", repr(token))
            else:
                options[name] = True
        elif token in SCRIPTS and command is None:
            command = token
        else:
            raise InvocationError("unknown", repr(token))
        index += 1
    if options.get("--language", "en") not in TEXT:
        raise InvocationError("language")
    if options.get("--paper-language", "all") not in ("en", "fr", "all"):
        raise InvocationError("paper_language")
    if command is None:
        if options.keys() - COMMON or not options.get("--help"):
            raise InvocationError("command", ", ".join(SCRIPTS))
        return command, options
    for option in options.keys() - COMMON - OPTIONS[command]:
        raise InvocationError("unsupported", option)
    if options.get("--help"):
        return command, options
    required = {"--output"} if command in ("package", "reproduce", "counterexamples") else set()
    if command == "counterexamples":
        required.add("--source278")
    for option in sorted(required):
        if option not in options:
            raise InvocationError("required", option)
    if command == "reproduce" and not options.get("--download-sources") and not all(
            option in options for option in ("--source277", "--source278")):
        raise InvocationError("downloads")
    return command, options


def resolved_path(value: str, option: str) -> Path:
    try:
        # NUL and controls are never useful in a human-facing maintenance path.
        if any(ord(char) < 32 or ord(char) == 127 for char in value):
            raise ValueError("control character")
        return Path(value).resolve()
    except (OSError, RuntimeError, ValueError):
        raise InvocationError("path", option) from None


def validate_paths(command: str, options: dict) -> None:
    protected = [ROOT.resolve()]
    for option in ("--source277", "--source278"):
        if option in options:
            path = resolved_path(options[option], option)
            if not path.is_dir():
                raise InvocationError("source", option)
            options[option] = str(path)
            protected.append(path)
    for option in ("--output", "--raw-log"):
        if option not in options:
            continue
        original = Path(options[option])
        path = resolved_path(options[option], option)
        if not original.is_absolute():
            raise InvocationError("absolute", option)
        if original.exists() or original.is_symlink():
            raise InvocationError("exists", option)
        if any(path.is_relative_to(directory) for directory in protected):
            raise InvocationError("protected", option)
        if option == "--raw-log" and not path.parent.is_dir():
            raise InvocationError("parent")
        options[option] = str(path)
    if "--raw-log" in options and "--output" in options:
        log, output = Path(options["--raw-log"]), Path(options["--output"])
        if log.is_relative_to(output) or output.is_relative_to(log):
            raise InvocationError("overlap")
    if command == "build":
        build = PAPER / "build"
        if build.is_symlink() or (build.exists() and (
                not build.is_dir() or any(path.is_symlink() for path in build.rglob("*")))):
            raise InvocationError("build_path")


def check_script_identities() -> None:
    """Check fixed script names, not user-provided executable paths."""
    try:
        manifest = json.loads((PAPER / "PUBLICATION.json").read_text(encoding="utf-8"))
        for name in HISTORICAL_SCRIPTS:
            path = PAPER / name
            if path.is_symlink() or not path.is_file() or (
                    hashlib.sha256(path.read_bytes()).hexdigest() != manifest["files"][name]):
                raise ValueError(name)
    except (OSError, ValueError, KeyError, TypeError):
        raise InvocationError("identity") from None


def command_line(command: str, options: dict) -> list[str]:
    result = [sys.executable, "-B", "-s", str(PAPER / SCRIPTS[command])]
    if command == "build":
        result.extend(("--language", options.get("--paper-language", "all")))
    for option in ("--check-build", "--output", "--source277", "--source278"):
        if option in options:
            result.append(option)
            if option in VALUES:
                result.append(options[option])
    return result


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    language = selected_language(argv)
    text = TEXT[language]
    log: BinaryIO | None = None
    try:
        command, options = parse(argv)
        if options.get("--help"):
            print(text["usage"] + "\n\n" + text["help"])
            return 0
        validate_paths(command, options)
        check_script_identities()
        if "--raw-log" in options:
            try:
                # Exclusive creation refuses even a newly introduced symlink.
                log = Path(options["--raw-log"]).open("xb")
            except OSError:
                raise InvocationError("path", "--raw-log") from None
    except (InvocationError, OSError) as error:
        detail = text[error.key].format(value=error.value) if isinstance(error, InvocationError) else text["path"].format(value="")
        print(text["refused"].format(detail=detail), file=sys.stderr)
        print(text["usage"], file=sys.stderr)
        return 2

    print(text["start"].format(value=command), flush=True)
    if command == "build":
        print(text["build_notice"].format(value=PAPER / "build"), flush=True)
    if command == "reproduce" and not all(name in options for name in ("--source277", "--source278")):
        print(text["network_notice"], flush=True)
    env = os.environ.copy()
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1")
    env.pop("PYTHONPATH", None)
    try:
        completed = subprocess.run(command_line(command, options), cwd=PAPER, env=env,
                                   stdout=log if log is not None else subprocess.DEVNULL,
                                   stderr=subprocess.STDOUT, check=False)
        code = completed.returncode if completed.returncode >= 0 else 128 - completed.returncode
        print(text["success"][command] if code == 0 else text["failure"].format(value=command, code=code),
              file=sys.stdout if code == 0 else sys.stderr)
    except OSError:
        code = 1
        print(text["launch"], file=sys.stderr)
    except KeyboardInterrupt:
        code = 130
        print(text["interrupted"], file=sys.stderr)
    finally:
        if log is not None:
            log.close()
    print(text["log"].format(value=options["--raw-log"]) if log is not None else text["no_log"])
    if "--output" in options:
        print(text["output"].format(value=options["--output"]))
    return code


if __name__ == "__main__":
    sys.exit(main())
