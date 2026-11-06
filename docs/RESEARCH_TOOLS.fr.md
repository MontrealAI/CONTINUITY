# Outils de maintenance de la recherche

[English](RESEARCH_TOOLS.md) · **Français** · [Accueil du dépôt](../README.fr.md)

Depuis la racine du dépôt, utiliser `scripts/research.py` pour obtenir l’aide, la validation des arguments, les avis d’exécution et les bilans de réussite ou d’échec en français ou en anglais. Python 3.10+ est requis. L’interface appelle uniquement les six outils historiques pris en charge et vérifie les empreintes SHA-256 de leurs sept fichiers sources Python avec `docs/continuity-omega-paper/PUBLICATION.json` avant toute exécution.

```sh
python3 scripts/research.py --language fr --help
python3 scripts/research.py --language en --help
```

## Deux choix de langue distincts

- `--language fr` ou `--language en` choisit la **langue de l’interface de maintenance**, y compris l’aide et les erreurs de validation. La valeur par défaut est l’anglais. Cette option peut précéder ou suivre la commande.
- `build --paper-language en`, `fr` ou `all` choisit les **articles à compiler**. La valeur par défaut est `all`, indépendamment de la langue de l’interface.
- Les noms de commandes et d’options, les chemins, les identifiants, les preuves lisibles par machine et les octets des sources historiques restent inchangés. Aucun choix de langue ne modifie un résultat expérimental ou un échec historique.

Par exemple, une aide en français peut accompagner la compilation de l’article anglais uniquement :

```sh
python3 scripts/research.py --language fr build --paper-language en
```

## Les diagnostics historiques bruts ne sont pas traduits

L’interface fournit un bilan localisé, pas une traduction des diagnostics détaillés des anciens scripts. Les outils historiques et leurs dépendances peuvent produire du texte technique anglais ou bilingue et des clés JSON stables. Pour conserver cette sortie technique exacte, demander explicitement un nouveau fichier journal :

```sh
python3 scripts/research.py --language fr verify --raw-log /tmp/continuity-verify-NEW.log
```

Le journal réunit la sortie standard et la sortie d’erreur de l’outil sans en traduire le texte. Son répertoire parent doit déjà exister. Le chemin doit être absolu, nouveau, hors de ce dépôt, hors des sources locales fournies et hors du répertoire de sortie demandé. Les fichiers existants et les liens symboliques sont refusés. Sans `--raw-log`, les sorties de console de l’outil sont écartées ; le bilan localisé reste visible. Cette option ne supprime pas les journaux et preuves que l’outil historique écrit normalement dans son propre répertoire de sortie.

En cas d’échec, l’interface indique le code de sortie et les emplacements de sortie ou de journal demandés, sans présenter une exécution incomplète comme réussie. Consulter le journal brut ou les preuves produites par l’outil pour connaître la cause technique. Pour réexécuter une commande qui crée des sorties, choisir un autre nouveau répertoire et un autre nouveau fichier journal. Les sorties d’un échec ne sont pas effacées.

## Opérations prises en charge

### Vérifier la publication historique

```sh
python3 scripts/research.py --language fr verify --raw-log /tmp/continuity-verify-NEW.log
python3 scripts/research.py --language fr verify --check-build --raw-log /tmp/continuity-build-check-NEW.log
```

`verify` contrôle les identités de publication, la portée consignée, les calculs rédigés et la structure de traduction. Les outils `pdfinfo` et `pdftotext` de Poppler sont requis. La commande ne réexécute pas les prototypes sources, n’authentifie pas le scénario fourni, ne certifie pas une cyberrésilience réelle et n’établit aucune activité commerciale.

`--check-build` compare en plus le texte extrait des **deux** articles reconstruits à leurs PDF canoniques respectifs. Compiler d’abord les deux langues. Cette option ne lance pas elle-même une compilation TeX.

### Compiler les articles sans publication

```sh
python3 scripts/research.py --language fr build --paper-language all --raw-log /tmp/continuity-build-NEW.log
```

Le script historique écrit toujours les fichiers générés dans `docs/continuity-omega-paper/build/`. Les fichiers de compilation existants peuvent être remplacés. Cet emplacement fixe est affiché avant l’exécution ; `--output` n’est pas une option de compilation. L’interface refuse les liens symboliques dans ce répertoire. Les PDF canoniques et le dépôt Lab d’origine ne sont pas mis à jour. L’option `--publish` n’est délibérément pas prise en charge.

Il faut `pdflatex` et les paquets TeX indiqués dans le [guide de compilation de l’article](continuity-omega-paper/README.fr.md), dont Babel français pour compiler en français. L’exécution de commandes système par TeX reste désactivée. Une compilation réussie ne constitue ni une nouvelle édition révisée ni une publication.

### Empaqueter la publication historique

```sh
python3 scripts/research.py --language fr package --output /tmp/continuity-package-NEW --raw-log /tmp/continuity-package-NEW.log
```

L’outil d’origine exécute le vérificateur de publication et produit les deux PDF canoniques et `CONTINUITY_OMEGA_SOURCE.zip`. Les dépendances de vérification ci-dessus sont requises. La sortie doit être un nouveau répertoire absolu, hors de ce dépôt. L’archive conserve l’inventaire de la publication historique ; elle **n’inclut pas** cette nouvelle interface, ses guides ou ses tests. Aucune version distante n’est publiée.

### Reproduire l’ingénierie synthétique figée

Hors ligne, fournir les deux jeux de sources historiques précédemment téléchargés :

```sh
python3 scripts/research.py --language fr reproduce --output /tmp/continuity-reproduction-NEW --source277 /absolute/pinned/source277 --source278 /absolute/pinned/source278 --raw-log /tmp/continuity-reproduction-NEW.log
```

Pour autoriser le téléchargement des fichiers sources publics figés manquants, le demander explicitement :

```sh
python3 scripts/research.py --language fr reproduce --download-sources --output /tmp/continuity-reproduction-NEW --raw-log /tmp/continuity-reproduction-NEW.log
```

Sans les deux sources locales ou `--download-sources`, l’invocation est refusée avant toute exécution. Avec une source locale et l’option de téléchargement, seule la source manquante est téléchargée. L’outil historique vérifie les empreintes SHA-256 et les identités des objets Git avant d’exécuter le code copié ; toutes les sources générées, les journaux et les cas de test restent dans le nouveau répertoire de sortie. Les sources doivent correspondre aux révisions figées de l’article, pas au prototype localisé actuel.

Une reproduction réussie signifie que les résultats synthétiques figés ont été reproduits. Elle ne constitue ni rétablissement réel, ni livraison physique, ni paiement, ni certification indépendante, ni qualification d’une correction ultérieure.

### Réexécuter les contre-exemples historiques

```sh
python3 scripts/research.py --language fr counterexamples --source278 /absolute/pinned/source278 --output /tmp/continuity-counterexamples-NEW --raw-log /tmp/continuity-counterexamples-NEW.log
```

Les sources historiques locales de la PR 278 sont requises ; l’outil d’origine vérifie leurs identités. Cette commande ne propose pas d’option de téléchargement. Un code de sortie réussi signifie que les cinq observations attendues, dont les faiblesses du vérificateur, ont été reproduites. **Il ne signifie pas que le vérificateur est qualifié.** La suite historique distincte de 29 tests n’est pas réexécutée par cette commande.

### Calculer l’exemple rédigé de mutualisation

```sh
python3 scripts/research.py --language fr pooling --raw-log /tmp/continuity-pooling-NEW.log
```

Ce calcul utilise l’arithmétique exacte et uniquement la bibliothèque standard. Le JSON numérique d’origine figure dans le journal brut demandé. L’exemple exige au moins trois acheteurs pour couvrir les coûts, alors que la capacité simultanée peut en servir au plus deux ; aucun nombre d’acheteurs ne satisfait les deux conditions. Il n’établit ni prix réels, ni demande, ni ordonnancement, ni commerce.

## Limites des sorties et de l’exécution

- `package`, `reproduce` et `counterexamples` exigent `--output` : un nouveau répertoire absolu, hors de ce dépôt et des sources fournies. L’outil d’origine peut créer les répertoires parents. Un répertoire de sortie existant n’est jamais réutilisé ni supprimé.
- `build` utilise le répertoire fixe de fichiers générés décrit ci-dessus. `verify` et `pooling` ne créent aucun répertoire de sortie ; le journal brut facultatif est distinct.
- Les arguments sont validés dans la langue choisie. Les commandes inconnues, options sans rapport, options répétées, commandes arbitraires, arguments transmis librement et `--publish` sont refusés. L’interface lance un script fixe avec une liste d’arguments, jamais une commande d’interpréteur système, et désactive l’écriture du bytecode Python ainsi que l’importation depuis les paquets personnels de l’utilisateur.
- Les scripts historiques et les modules locaux qu’ils importent doivent conserver leurs identités publiées. Une différence est refusée avant le lancement ; restaurer les octets publiés plutôt que modifier le manifeste pour contourner le contrôle.
- Le code `0` signifie que la commande historique choisie s’est terminée avec succès dans sa portée déclarée. L’interface retourne `2` pour ses erreurs d’invocation ou de validation, `1` si elle ne peut pas lancer l’outil et `130` en cas d’interruption. Les codes d’échec historiques sont conservés ; une terminaison par signal est représentée par `128 + signal`. Une commande sous-jacente peut elle aussi retourner `1` ou `2`.

## Tests légers de l’interface

```sh
python3 -B -m unittest discover -s tests -p 'test_research_tools.py' -v
```

Ces tests ciblés couvrent les deux langues, l’appel des commandes prises en charge, la protection des sorties, les contrôles du manifeste, les journaux bruts et la gestion des échecs. Les outils coûteux ou utilisant le réseau sont simulés ; un véritable calcul de mutualisation s’exécute hors ligne. Ces tests ne compilent pas TeX, ne téléchargent pas de sources figées, ne publient rien et n’établissent aucun nouveau résultat scientifique. Ils complètent, sans les remplacer, la [vérification de l’article historique](continuity-omega-paper/README.fr.md) et les contrôles de provenance du dépôt.

La suite complète du dépôt (`python3 -m unittest discover -s tests -p 'test_*.py' -v`) exige aussi Node.js pour les contrôles JavaScript du site. Aucun paquet npm n’est nécessaire. Le prototype et les tests Python ciblés des interfaces restent utilisables avec Python seul.
