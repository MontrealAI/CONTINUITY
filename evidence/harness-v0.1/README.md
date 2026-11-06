# CONTINUITY Ω Harness v0.1 / CONTINUITÉ Ω — Banc d’essai et de vérification

[English](#english) · [Français](#français)

## English

The complete evidence archive preserves both qualification attempts and their failures, current and historical development observations, actual SQLite databases and fulfillment artifacts, retained contracts/references, exact commands, and complete English/French Passports. The qualified code is `fa9da1f54acfaa82510a4b6b805c2980d3e5b31d`. The frozen version-1 business experiment was not changed after a failed first qualification.

- [Complete evidence archive](continuity-harness-v0.1-evidence.tar.xz) — 313,736 compressed bytes; 1,722 inventoried evidence files plus their manifest.
- [SHA-256](SHA256SUMS), [post-extraction verification](PACKAGE_CHECK.json), and [machine-readable results](RESULTS.json).
- [Full English results](../../docs/harness/RESULTS.md) · [Full French results](../../docs/harness/RESULTS.fr.md).

| Decisive base control | English Passport | French Passport | Structured result |
| --- | --- | --- | --- |
| Feasible recovery | [English](passports/recovery/PASSPORT.en.md) | [Français](passports/recovery/PASSPORT.fr.md) | [JSON](passports/recovery/RESULT.json) |
| Feasible alternate route | [English](passports/alternate/PASSPORT.en.md) | [Français](passports/alternate/PASSPORT.fr.md) | [JSON](passports/alternate/RESULT.json) |
| Constrained disruption | [English](passports/constrained/PASSPORT.en.md) | [Français](passports/constrained/PASSPORT.fr.md) | [JSON](passports/constrained/RESULT.json) |

The third control fulfilled 1,100 of 1,900 units and refused the remaining 800. Its expected test assertion passed; the full customer promise failed. Local artifacts are software outputs, not printed goods or delivery.

The archive SHA-256 is `a7115c8d499377152d6e4c1e83e44ca5997b5452ff3847ad061e73b4bac711b9`. The manifest verifies byte identity, not real-customer authenticity. Retain original reference pins outside candidate control.

From the repository root, extract into a newly created directory and verify actual archived evidence:

```sh
CONTINUITY_EVIDENCE_DIR=$(mktemp -d)
tar -xJf evidence/harness-v0.1/continuity-harness-v0.1-evidence.tar.xz -C "$CONTINUITY_EVIDENCE_DIR"
python3 -m continuity_harness --language en verify-suite --in-dir "$CONTINUITY_EVIDENCE_DIR/continuity-harness-v0.1-evidence/attempt-2/comparison"
```

The archive's first `comparison/` remains unqualified and is expected to fail separate fresh verification. Its saved favorable summary is retained as an observation, not used as proof. `attempt-2/comparison/` is the qualified comparison; all 12 conventional/Harness outcome pairs tied. AI performance is NOT RUN. `attempt-2/challenges/` retains eight cases, including three defective checker mutations with separate original target and reference results. Copied challenge evidence is not another execution.

Git is required to obtain and record source revision metadata. Python 3.10+, SQLite from the standard library, Linux x86_64 and seccomp BPF support are required for execution; Node.js is additionally needed for all historical repository tests. The [guide](../../docs/harness/README.md) supplies fresh-run and individual-verification commands.

## Français

L’archive complète conserve les deux tentatives de qualification et leurs échecs, les observations de développement, de vraies bases SQLite et pièces de réalisation, les contrats/références conservés, les commandes exactes et les passeports complets français/anglais. Le code qualifié est `fa9da1f54acfaa82510a4b6b805c2980d3e5b31d`. L’expérience métier figée en version 1 n’a pas été modifiée après l’échec de la première qualification.

- [Archive complète des preuves](continuity-harness-v0.1-evidence.tar.xz) — 313 736 octets compressés ; 1 722 fichiers de preuve inventoriés, plus leur manifeste.
- [SHA-256](SHA256SUMS), [vérification après extraction](PACKAGE_CHECK.json) et [résultats lisibles par machine](RESULTS.json).
- [Résultats français complets](../../docs/harness/RESULTS.fr.md) · [Résultats anglais complets](../../docs/harness/RESULTS.md).

| Contrôle de base décisif | Passeport français | Passeport anglais | Résultat structuré |
| --- | --- | --- | --- |
| Reprise réalisable | [Français](passports/recovery/PASSPORT.fr.md) | [English](passports/recovery/PASSPORT.en.md) | [JSON](passports/recovery/RESULT.json) |
| Voie alternative réalisable | [Français](passports/alternate/PASSPORT.fr.md) | [English](passports/alternate/PASSPORT.en.md) | [JSON](passports/alternate/RESULT.json) |
| Perturbation contrainte | [Français](passports/constrained/PASSPORT.fr.md) | [English](passports/constrained/PASSPORT.en.md) | [JSON](passports/constrained/RESULT.json) |

Le troisième contrôle réalise 1 100 des 1 900 unités et refuse les 800 restantes. L’assertion attendue du test réussit ; la promesse client complète échoue. Les pièces locales sont des résultats logiciels, pas des biens imprimés ni une livraison.

Le SHA-256 de l’archive est `a7115c8d499377152d6e4c1e83e44ca5997b5452ff3847ad061e73b4bac711b9`. Le manifeste vérifie l’identité des octets, sans authentifier de véritables clients. Conserver les empreintes originales des références hors du contrôle du candidat.

Depuis la racine du dépôt, extraire dans un nouveau répertoire puis vérifier les preuves archivées actuelles :

```sh
CONTINUITY_EVIDENCE_DIR=$(mktemp -d)
tar -xJf evidence/harness-v0.1/continuity-harness-v0.1-evidence.tar.xz -C "$CONTINUITY_EVIDENCE_DIR"
python3 -m continuity_harness --language fr verify-suite --in-dir "$CONTINUITY_EVIDENCE_DIR/continuity-harness-v0.1-evidence/attempt-2/comparison"
```

La première `comparison/` de l’archive reste non qualifiée et doit échouer à une vérification fraîche distincte. Son ancien résumé favorable est conservé comme observation, jamais employé comme preuve. `attempt-2/comparison/` est la comparaison qualifiée ; les 12 paires conventionnelle/banc d’essai sont à égalité. La performance d’IA est NON EXÉCUTÉE. `attempt-2/challenges/` conserve huit cas, dont trois mutations de vérificateur défectueux, avec résultats originaux du composant et de référence séparés. Copier une preuve contradictoire ne constitue pas une nouvelle exécution.

Git est nécessaire pour obtenir le code et consigner sa révision. L’exécution exige Python 3.10 ou ultérieur, SQLite de la bibliothèque standard, Linux x86_64 et seccomp BPF ; Node.js est aussi nécessaire à toutes les régressions historiques du dépôt. Le [guide](../../docs/harness/README.fr.md) fournit les commandes de nouvelle exécution et de vérification individuelle.
