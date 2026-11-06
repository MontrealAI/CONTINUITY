#!/usr/bin/env python3
"""Bilingual presentation around the unchanged, offline CONTINUITY Ω prototype.

Interface bilingue du prototype CONTINUITÉ Ω inchangé, exécuté hors ligne.
This wrapper does not repair or qualify the historical checker.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
from functools import partial
import importlib.util
import io
import json
from pathlib import Path
import sys

# Support both direct execution and import-based tests, from any working directory.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from continuity_omega import cli as historical_cli
from continuity_omega.checker import audit
from continuity_omega.demo import CASES

_SPEC = importlib.util.spec_from_file_location(
    '_continuity_bilingual_presenter', ROOT / 'scripts' / 'continuity_passport.py')
reader = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(reader)

CASE_DESCRIPTIONS = {
    'nominal': ('Nominal synthetic scenario', 'Scénario synthétique nominal'),
    'tampered_source': ('Source changed without updating its seal', 'Source modifiée sans mise à jour de son empreinte'),
    'overbooked': ('Insufficient remaining supplier capacity', 'Capacité restante du fournisseur insuffisante'),
    'correlated_outage': ('Supplier shares an excluded failure domain', 'Fournisseur dans un domaine de défaillance exclu'),
    'unqualified': ('Simulated supplier commitment absent', 'Engagement simulé du fournisseur absent'),
    'late': ('Supplier misses the modeled deadline', 'Fournisseur dépassant le délai modélisé'),
    'buyer_declines': ('Offer exceeds hypothetical buyer budget', 'Offre dépassant le budget hypothétique de l’acheteur'),
    'uneconomic': ('Full modeled costs exceed the offer', 'Coûts complets modélisés dépassant l’offre'),
    'unapproved_sharing': ('Scenario lacks information-sharing permission', 'Autorisation de partage d’information absente du scénario'),
    'no_order_source': ('Source event list is empty', 'Liste des événements sources vide'),
    'missing_from_restored': ('Order missing from restored snapshot', 'Commande absente de l’instantané restauré'),
    'extra_restored': ('Unsupported order in restored snapshot', 'Commande sans source justificative dans l’instantané restauré'),
}


def say(language, en, fr):
    return fr if language == 'fr' else en


def selected_language(argv):
    """Select help/error language even when --help precedes --language."""
    language = 'en'
    for index, value in enumerate(argv):
        candidate = value.split('=', 1)[1] if value.startswith('--language=') else None
        if value == '--language' and index + 1 < len(argv):
            candidate = argv[index + 1]
        if candidate in ('en', 'fr'):
            language = candidate
    return language


class LocalizedParser(argparse.ArgumentParser):
    def __init__(self, *args, language='en', **kwargs):
        self.language = language
        kwargs.setdefault('add_help', False)
        kwargs.setdefault('allow_abbrev', False)
        super().__init__(*args, **kwargs)
        self._positionals.title = say(language, 'Commands', 'Commandes')
        self._optionals.title = 'Options'
        self.add_argument('-h', '--help', action='help',
                          help=say(language, 'Show this help', 'Afficher cette aide'))
        self.add_argument('--language', choices=('en', 'fr'), default=argparse.SUPPRESS,
                          help=say(language, 'Display language (default: en)', 'Langue d’affichage (par défaut : en)'))

    def format_help(self):
        return super().format_help().replace('usage:', say(self.language, 'usage:', 'utilisation :'), 1)

    def error(self, message):
        # argparse's runtime-generated English prose is not a translated vocabulary.
        reader.fail('Invalid arguments or missing value; use --help for this command.',
                    'Arguments invalides ou valeur manquante ; utiliser --help pour cette commande.')


def parser_for(language):
    tr = lambda en, fr: say(language, en, fr)
    parser = LocalizedParser(prog='continuity', language=language, description=tr(
        'CONTINUITY Ω: offline synthetic demo, fresh verification and saved-record reading.',
        'CONTINUITÉ Ω : démonstration synthétique hors ligne, nouvelle vérification et lecture des données consignées.'))
    parser.set_defaults(language='en')
    sub = parser.add_subparsers(dest='command', required=True,
                               parser_class=partial(LocalizedParser, language=language))
    demo = sub.add_parser('demo', help=tr('Run a synthetic scenario and create both language reports',
                                        'Exécuter un scénario synthétique et créer les rapports dans les deux langues'),
                          description=tr('Create new evidence and separate English/French recorded reports.',
                                         'Créer de nouveaux éléments probants et des rapports consignés distincts en anglais/français.'),
                          formatter_class=argparse.RawDescriptionHelpFormatter,
                          epilog=tr('Synthetic scenarios:\n', 'Scénarios synthétiques :\n') + '\n'.join(
                              '  ' + key + ': ' + tr(*CASE_DESCRIPTIONS[key]) for key in CASES))
    demo.add_argument('--case', choices=CASES, default='nominal',
                      help=tr('Synthetic scenario (default: nominal)', 'Scénario synthétique (par défaut : nominal)'))
    demo.add_argument('--out', required=True, type=Path, metavar=tr('NEW_DIRECTORY', 'NOUVEAU_DOSSIER'),
                      help=tr('New evidence directory; never overwrite', 'Nouveau dossier probant ; aucun écrasement'))
    demo.add_argument('--reports-dir', type=Path, metavar=tr('NEW_DIRECTORY', 'NOUVEAU_DOSSIER'),
                      help=tr('New separate report directory (default: OUT-reports)',
                              'Nouveau dossier distinct de rapports (par défaut : OUT-reports)'))
    demo.add_argument('--json', action='store_true',
                      help=tr('Print the original machine-readable result instead of the human summary',
                              'Afficher le résultat original lisible par machine au lieu du résumé humain'))
    verify = sub.add_parser('verify', help=tr('Run the historical checker now; do not update saved evidence',
                                            'Exécuter le vérificateur historique maintenant ; ne pas modifier les données consignées'))
    verify.add_argument('--in-dir', required=True, type=Path, metavar=tr('DIRECTORY', 'DOSSIER'),
                        help=tr('Read INPUT.json, HANDOFF.json and PASSPORT.json',
                                'Lire INPUT.json, HANDOFF.json et PASSPORT.json'))
    verify.add_argument('--json', action='store_true',
                        help=tr('Print the fresh checker JSON without translation',
                                'Afficher le JSON du nouveau contrôle sans traduction'))
    inspect = sub.add_parser('inspect', help=tr('Read saved records only; no fresh audit',
                                              'Lire uniquement les données consignées ; aucun nouvel audit'))
    inspect.add_argument('--in-dir', required=True, type=Path, metavar=tr('DIRECTORY', 'DOSSIER'),
                         help=tr('Saved evidence or refusal directory', 'Dossier des éléments probants ou du refus consignés'))
    inspect.add_argument('--out', type=Path, metavar=tr('NEW_FILE', 'NOUVEAU_FICHIER'),
                         help=tr('Optional new absolute Markdown path outside the evidence directory',
                                 'Chemin Markdown absolu facultatif, nouveau et hors du dossier probant'))
    return parser


def technical(value):
    """Keep identifiers intact while escaping terminal control characters."""
    return json.dumps(value, ensure_ascii=True)


def boundary(language):
    return say(language,
        'Synthetic only. The historical checker has known weaknesses and uses separate code '
        'by the same research authors. No real recovery, supplier consent, delivery, payment '
        'or third-party certification is established. This wrapper does not repair or qualify it.',
        'Synthétique uniquement. Le vérificateur historique présente des faiblesses connues '
        'et utilise un code distinct produit par les mêmes auteurs. Aucune reprise réelle, '
        'aucun consentement du fournisseur, aucune livraison, aucun paiement ni aucune '
        'certification tierce ne sont établis. Cette interface ne le corrige ni ne le qualifie.')


def new_directory(path):
    candidate = Path(path)
    if candidate.exists() or candidate.is_symlink():
        reader.fail('Output directory already exists; prior evidence and reports will not be overwritten.',
                    'Le dossier de sortie existe déjà ; les éléments probants et rapports antérieurs ne seront pas écrasés.', candidate)
    return reader.resolved(candidate)


def run_demo(opts):
    language = opts.language
    out = new_directory(opts.out)
    reports = new_directory(opts.reports_dir if opts.reports_dir is not None else out.with_name(out.name + '-reports'))
    if out == reports or out.is_relative_to(reports) or reports.is_relative_to(out):
        reader.fail('Evidence and report directories must be separate; neither may contain the other.',
                    'Les dossiers probants et de rapports doivent être distincts ; aucun ne doit contenir l’autre.')
    captured = io.StringIO()
    with redirect_stdout(captured), redirect_stderr(io.StringIO()):
        try:
            code = historical_cli.main(['demo', '--case', opts.case, '--out', str(out)])
        except SystemExit:
            reader.fail('The historical demo refused the output path; use a new directory.',
                        'La démonstration historique a refusé le chemin de sortie ; utiliser un nouveau dossier.')
    # All historical bytes, including the original PASSPORT.md, remain untouched.
    # Prepare both translations before creating any report output.
    translations = {lang: reader.present(out, lang) for lang in ('en', 'fr')}
    reports.mkdir(parents=True)
    for lang, report in translations.items():
        with (reports / ('PASSPORT.' + lang + '.md')).open('x', encoding='utf-8') as stream:
            stream.write(report)
    if opts.json:
        print(captured.getvalue(), end='')
        return code
    result = json.loads(captured.getvalue())
    print(say(language, 'Synthetic scenario: ', 'Scénario synthétique : ') + opts.case)
    print(say(language, 'Recorded verdict: ', 'Verdict consigné : ') + result['verdict'])
    if 'reason' in result:
        print(reader.reason_description(result['reason'], language))
    else:
        print(say(language, 'Outstanding orders: ', 'Commandes restantes : ') + str(result['orders']))
        print(say(language, 'Required units: ', 'Unités requises : ') + str(result['units']))
        print(say(language, 'Restoration findings: ', 'Constats de restauration : ') + str(result['restore_findings']))
    print(say(language, 'Evidence directory: ', 'Dossier probant : ') + technical(str(out)))
    print(say(language, 'Recorded reports in English and French: ', 'Rapports consignés en anglais et en français : ') + technical(str(reports)))
    print(say(language, 'The reports read saved records; generating them performs no additional audit.',
              'Les rapports lisent les données consignées ; leur création n’exécute aucun audit supplémentaire.'))
    print(boundary(language))
    return code


def fresh_summary(result, language):
    tr = lambda en, fr: say(language, en, fr)
    lines = [tr('Fresh historical checker result: ', 'Résultat du nouveau contrôle historique : ') + technical(result['verdict']),
             tr('Exercise: ', 'Exercice : ') + technical(result['exercise_id']),
             tr('Replayed orders: ', 'Commandes réexécutées : ') + str(result['replayed_orders']),
             tr('Replayed units: ', 'Unités réexécutées : ') + str(result['replayed_units']),
             tr('Failure count (before deduplication): ', 'Nombre d’échecs (avant dédoublonnage) : ') + str(result['failure_count'])]
    for code in result['failures']:
        try:
            description = reader.failure_description(code, language)
            if language == 'en':
                description = description.replace('Recorded failed condition: ', 'Failed condition: ', 1)
        except reader.PresentationError:
            description = tr('Unsupported finding code; consult the original JSON',
                             'Code de constat non pris en charge ; consulter le JSON original')
        lines.append('- ' + technical(code) + ': ' + description)
    lines.append(tr('Restoration findings:', 'Constats de restauration :'))
    if not result['restoration_gaps']:
        lines.append(tr('No restoration discrepancy was listed.', 'Aucune divergence de restauration n’a été indiquée.'))
    for finding in result['restoration_gaps']:
        labels = reader.ISSUES.get(finding['issue'], ('Unsupported finding', 'Constat non pris en charge'))
        lines.append('- ' + technical(finding['order_id']) + ': ' + tr(*labels) + ' (' + technical(finding['issue']) + ')')
    lines.extend([tr('AUDIT.json was not read or updated. A saved report may show an older result.',
                     'AUDIT.json n’a été ni lu ni mis à jour. Un rapport consigné peut présenter un résultat antérieur.'),
                  boundary(language)])
    return '\n'.join(lines)


def run_verify(opts):
    # Deliberately use the historical JSON loader and checker semantics. Reader
    # schema validation is NOT an extra audit rule. Catch malformed-input failures
    # for localization, never turn an incomplete run into a PASS or a new finding.
    try:
        data = [json.loads((opts.in_dir / name).read_text(encoding='utf-8'))
                for name in ('INPUT.json', 'HANDOFF.json', 'PASSPORT.json')]
        result = audit(*data)
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, AttributeError,
            IndexError, OverflowError, RecursionError, RuntimeError):
        print(say(opts.language,
            'Verification could not complete: unreadable or malformed local input, or a historical checker error. '
            'No fresh verdict was established and no saved evidence was changed.',
            'La vérification n’a pas pu se terminer : entrée locale illisible ou mal formée, ou erreur du vérificateur historique. '
            'Aucun nouveau verdict n’a été établi et aucun élément probant consigné n’a été modifié.'), file=sys.stderr)
        return 3
    print(json.dumps(result, indent=2) if opts.json else fresh_summary(result, opts.language))
    return 0 if result['verdict'] == 'PASS_SYNTHETIC_ONLY' else 3


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    language = selected_language(argv)
    try:
        parser = parser_for(language)
        if not argv:
            parser.print_help()
            return 0
        opts = parser.parse_args(argv)
        language = opts.language
        if opts.command == 'demo':
            return run_demo(opts)
        if opts.command == 'verify':
            return run_verify(opts)
        result = reader.present(opts.in_dir, language, opts.out)
        if opts.out is None:
            print(result, end='')
        else:
            print(say(language, 'Recorded report written; no fresh audit: ',
                      'Rapport consigné écrit ; aucun nouvel audit : ') + technical(str(opts.out)))
        return 0
    except SystemExit as error:
        return error.code
    except KeyboardInterrupt:
        print(say(language,
            'Operation interrupted. No completion is confirmed; any newly created files may be incomplete.',
            'Opération interrompue. Aucune exécution complète n’est confirmée ; les nouveaux fichiers créés peuvent être incomplets.'),
            file=sys.stderr)
        return 130
    except reader.PresentationError as error:
        message = say(language, error.en, error.fr)
        if error.detail:
            message += ' [' + technical(error.detail) + ']'
        print(say(language, 'Operation refused: ', 'Opération refusée : ') + message, file=sys.stderr)
        return 2
    except (OSError, ValueError, RuntimeError) as error:
        # Do not expose untranslated OS prose or claim that a partial demo wrote nothing.
        print(say(language,
            'Cannot complete the local file operation. Any newly created files may be incomplete; '
            'check the requested paths before retrying with new output paths.',
            'Impossible de terminer l’opération sur les fichiers locaux. Les nouveaux fichiers créés peuvent être incomplets ; '
            'vérifier les chemins demandés avant de réessayer avec de nouveaux chemins de sortie.') +
            ' [' + type(error).__name__ + ']', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
