# Interface bilingue en ligne de commande

[English](BILINGUAL_CLI.md) · **Français** · [Accueil du dépôt](../README.fr.md)

`scripts/continuity.py` fournit une aide, des erreurs, des résumés et des rapports consignés en anglais et en français pour le prototype synthétique hors ligne. Python 3.10+ suffit. Aucune installation de paquet, connexion réseau, information d’authentification ni action réelle n’est nécessaire.

## Démarrage rapide

Depuis la racine du dépôt, choisir des chemins de sortie qui n’existent pas encore :

```sh
python3 scripts/continuity.py --language fr --help
python3 scripts/continuity.py demo --language fr --case nominal --out /tmp/continuity-exemple
python3 scripts/continuity.py verify --language fr --in-dir /tmp/continuity-exemple
python3 scripts/continuity.py inspect --language fr --in-dir /tmp/continuity-exemple
python3 scripts/continuity.py inspect --language en --in-dir /tmp/continuity-exemple
```

`--language en` est la valeur par défaut. `--language fr` sélectionne le français. L’option fonctionne avant ou après la commande, y compris avec `--help`. Les noms de commandes et d’options, identifiants de scénarios, champs JSON, identifiants de schémas, empreintes et codes de verdict constituent des interfaces techniques stables et ne sont pas traduits.

## Trois opérations distinctes

- **`demo`** exécute l’interface historique inchangée sur un scénario synthétique rédigé par les auteurs. Elle crée les artefacts d’origine dans un nouveau dossier `--out`, puis utilise le présentateur existant du passeport consigné pour créer **les deux fichiers** `PASSPORT.en.md` et `PASSPORT.fr.md` dans un nouveau dossier voisin nommé `OUT-reports`. Les refus du constructeur sont également traités : leurs rapports expliquent `REJECTION.json`, et non un transfert inexistant. `--reports-dir NOUVEAU_DOSSIER` permet de choisir un autre nouveau dossier de rapports. Aucun des deux dossiers ne doit contenir l’autre. Aucune sortie existante n’est écrasée. Le fichier anglais d’origine `PASSPORT.md`, lorsqu’il est généré par l’interface historique, reste inchangé.
- **`verify`** exécute maintenant le vérificateur historique inchangé sur `INPUT.json`, `HANDOFF.json` et `PASSPORT.json`. Elle ne lit ni ne met à jour `AUDIT.json` ; son nouveau résultat apparaît uniquement sur la sortie standard. Elle n’applique pas la validation de présentation plus stricte du lecteur comme règles d’audit supplémentaires. Si le chargement des entrées ou le vérificateur historique ne peut se terminer, l’interface signale une erreur localisée sans inventer un verdict achevé. Les entrées mal formées que le vérificateur peut traiter conservent son résultat effectif.
- **`inspect`** utilise le présentateur existant pour lire les enregistrements consignés de transfert, de passeport et d’audit, ou un refus consigné. Elle n’effectue **aucun nouvel audit**, ne lit pas `INPUT.json` et ne modifie pas les éléments probants. `--out /chemin/absolu/nouveau-rapport.md` écrit un nouveau rapport hors du dossier probant. Les enregistrements non pris en charge sont refusés plutôt que traduits partiellement.

Un nouvel échec de `verify` ne remplace pas une ancienne validation consignée. Un appel ultérieur à `inspect` peut encore afficher cette ancienne validation, explicitement désignée comme consignée. Conserver cette distinction lors du partage de l’un ou l’autre résultat.

## Autres scénarios et sortie lisible par machine

```sh
python3 scripts/continuity.py demo --language fr --help
python3 scripts/continuity.py demo --language fr --case overbooked --out /tmp/continuity-refus
python3 scripts/continuity.py verify --language fr --in-dir /tmp/continuity-exemple --json
```

L’aide de la démonstration explique chaque scénario dans la langue choisie. `demo --json` affiche le résultat JSON d’origine de l’interface historique ; les fichiers de rapports bilingues sont quand même générés. `verify --json` affiche le résultat JSON du nouveau contrôle. Ces sorties brutes lisibles par machine conservent volontairement leurs champs, codes et textes d’origine, indépendamment de `--language`. Les erreurs restent localisées sur la sortie d’erreur standard. Pour les enregistrements consignés lisibles par machine, utiliser les fichiers JSON d’origine ; `inspect` constitue la vue destinée à la lecture humaine.

## Codes de sortie et sécurité des fichiers

- `0` : réussite synthétique de la démonstration ou de la vérification, ou présentation du rapport achevée. La réussite de la lecture n’est pas une validation d’audit.
- `2` : refus de la démonstration par le constructeur, refus des arguments ou de la présentation, ou opération de sortie locale impossible à terminer. Une démonstration refusée peut tout de même produire un rapport bilingue de refus valide.
- `3` : un contrôle achevé a renvoyé `FAIL`, ou la vérification n’a pas pu se terminer. Lire le message pour distinguer un échec d’audit de l’absence de nouveau verdict.
- `130` : l’opération a été interrompue ; son exécution complète n’est pas confirmée.

Les éléments probants de la démonstration sont créés avant les rapports. Si une opération ultérieure sur les fichiers échoue, les nouveaux fichiers peuvent rester incomplets. Préserver les éléments probants déjà écrits, inspecter les chemins et réessayer avec de nouveaux chemins de sortie. L’interface ne supprime pas discrètement les résultats partiels et ne remplace pas les enregistrements historiques.

## Portée et préservation historique

Il s’agit d’une interface de présentation, **pas d’une correction ni d’une qualification du vérificateur**. Les six fichiers sources de `continuity_omega`, `scripts/continuity_passport.py` et `scripts/package_continuity_reading.py` restent préservés octet pour octet. Les commandes d’origine restent disponibles pour la reproduction historique à versions figées :

```sh
python3 -m continuity_omega --help
python3 scripts/continuity_passport.py --language fr --help
```

Le prototype utilise des entrées synthétiques rédigées par les auteurs. Aucune reprise réelle, aucun engagement du fournisseur, aucune acceptation du client, aucune livraison, aucun paiement ni aucune certification externe ne sont établis. Les faiblesses connues du vérificateur historique subsistent ; un code distinct produit par les mêmes auteurs ne constitue pas une assurance tierce. Cette interface n’intègre ni ne qualifie le renforcement proposé séparément dans la PR #279.

## Tests

```sh
python3 -m unittest discover -s tests -p 'test_bilingual_cli.py' -v
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/verify_copy.py
```

Les tests ciblés couvrent chaque scénario dans les deux langues, la parité des démonstrations octet pour octet, les deux fichiers de rapports, l’aide et les erreurs, la stabilité du JSON, la lecture et la vérification sans modification, les verdicts consignés périmés, les collisions de sorties et les échecs avec sorties partielles. Ils testent cette interface, pas la valeur scientifique du vérificateur historique.

La suite complète du dépôt (`python3 -m unittest discover -s tests -p 'test_*.py' -v`) exige aussi Node.js pour les contrôles JavaScript du site. Aucun paquet npm n’est nécessaire. Le prototype et les tests Python ciblés des interfaces restent utilisables avec Python seul.
