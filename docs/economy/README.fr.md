# CONTINUITÉ Ω — Inventer l’économie de la continuité

[English](README.md) · [Architecture](ARCHITECTURE.fr.md) · [Modèle de menace](THREAT_MODEL.fr.md) · [Produit numérique](PRODUCT.fr.md) · [Préenregistrement](EXPERIMENT.md#français) · [Exigences et tests](REQUIREMENTS.fr.md)

**La version 0.2.0 est une expérience de produit numérique préenregistrée séparément.** Elle cherche à déterminer si une solution autorisée entre participants modélisés livre effectivement le même produit numérique, si elle satisfait leurs contraintes économiques définies et si sa méthode améliore le résultat d’une procédure conventionnelle compétente. Ces trois affirmations restent distinctes. Une marge synthétique positive n’établit ni vente, ni demande réelle, ni avantage de méthode.

La nouvelle obligation porte sur un paquet JSON borné contenant, pour chaque unité, un contenu substantiel en anglais et en français. Un processus destinataire distinct conserve les octets, importe les étiquettes, compare le contenu littéral à son contrat conservé et inscrit durablement l’acceptation. Il s’agit d’une acceptation numérique sémantique dans un exercice synthétique. Elle n’établit ni apparence rendue, ni aptitude à l’impression, ni livraison physique, ni autorisation authentique d’un client. Les artefacts de métadonnées historiques v0.1 gardent leur portée originale.

## Prérequis et copie propre du dépôt

Utiliser Linux x86_64, Python 3.10 ou ultérieur, SQLite fourni par la bibliothèque standard et un noyau autorisant le filtre seccomp BPF. Le candidat doit réussir les cinq essais de refus : accès aux fichiers d’autorité, accès aux fichiers de travail, réseau, création de processus et inspection de processus. Le contrôleur refuse la qualification si cette frontière est indisponible. Aucun paquet Python, clé API, téléchargement de modèle ou service payant n’est nécessaire. Node.js est également requis pour les tests web existants du dépôt ; aucun paquet npm n’est nécessaire.

Extraire la révision qualifiée exacte indiquée dans le rapport de résultats. Pendant la revue, la branche est `feat/continuity-economy-v0.2` ; un nom de branche mobile ne constitue pas à lui seul une identité reproductible.

```sh
git clone https://github.com/MontrealAI/CONTINUITY.git
cd CONTINUITY
git checkout feat/continuity-economy-v0.2
git rev-parse HEAD
python3 -m continuity_economy --language fr --help
python3 -m continuity_economy --language fr experiment --out /tmp/continuite-economie-complete-001
python3 -m continuity_economy --language fr verify-suite --in-dir /tmp/continuite-economie-complete-001
```

`experiment` exécute la comparaison de base, le successeur préenregistré séparément et les contrôles contradictoires. Il exige la présence de l’enregistrement du successeur et ne le remplace ni ne l’omet silencieusement. Choisir chaque fois un nouveau répertoire de sortie hors du dépôt. Les tentatives existantes sont refusées plutôt qu’écrasées. Les répertoires d’autorité sont voisins des répertoires d’exécution ; le candidat reçoit uniquement la vue publique par ses canaux restreints.

## Commandes distinctes

```sh
# Sept contrôles de base, procédure du banc d’essai seulement.
python3 -m continuity_economy --language fr demo --out /tmp/continuite-economie-demo-001

# Sept cas × procédure conventionnelle, banc d’essai, sans achat et IA non exécutée.
python3 -m continuity_economy --language fr compare --out /tmp/continuite-economie-comparaison-001
python3 -m continuity_economy --language fr verify-suite --in-dir /tmp/continuite-economie-comparaison-001

# Successeur distinct utilisant les mêmes interfaces et éléments réutilisables autorisés.
python3 -m continuity_economy --language fr successor --out /tmp/continuite-economie-successeur-001

# Pannes réellement exécutées, interventions sur les preuves et mutations du vérificateur.
python3 -m continuity_economy --language fr challenge --out /tmp/continuite-economie-epreuves-001
python3 -m continuity_economy --language fr verify-suite --in-dir /tmp/continuite-economie-epreuves-001

# Un cas préenregistré et une procédure explicitement choisie.
python3 -m continuity_economy --language fr run --fixture constructed-continuity --method conventional --out /tmp/continuite-economie-un-001

# Vérification fraîche : fournir l’empreinte originale conservée dans une garde de confiance.
python3 -m continuity_economy --language fr verify --run /tmp/continuite-economie-un-001/run --authority /tmp/continuite-economie-un-001/authority --reference-sha256 EMPREINTE_ORIGINALE_SHA256

python3 -m unittest discover -s tests -p 'test_economy*.py' -v
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/verify_copy.py
```

`EMPREINTE_ORIGINALE_SHA256` désigne l’empreinte conservée indépendamment ; ce n’est pas une valeur à recalculer depuis un dossier potentiellement altéré. Son absence laisse l’autorité **NON ÉTABLIE**. Les index conservent les empreintes d’exercice pour la reproduction dans le modèle d’hôte et de contrôleur de confiance ; protéger une copie séparée de l’index ou son empreinte lors du transfert des preuves. Un administrateur hôte malveillant est hors modèle.

Le code de sortie `0` indique que l’assertion déclarée a été observée, y compris un résultat négatif correctement constaté. Il ne signifie pas que chaque obligation ou transaction a réussi. Le code `3` indique une assertion de suite échouée ou une appréciation fraîche individuelle non favorable ; `2` indique une erreur de commande ou d’admission. Consulter `claims`, `assessment`, `per_obligation`, `failures` et `unresolved` au lieu d’interpréter le code de sortie comme verdict commercial. Les entrées IA portent **NON EXÉCUTÉE** : aucun modèle local approprié déjà autorisé n’était disponible. L’adaptateur permet une intégration ultérieure sans identifiants ni API payante ; un substitut de test vérifie uniquement le protocole.

## Les sept cas de base préenregistrés

| Cas | Objectif |
| --- | --- |
| `primary-recovery` | Restaurer l’état principal périmé depuis l’historique protégé et réaliser l’obligation numérique amendée. |
| `conventional-better` | Rendre le secours conventionnel existant préférable économiquement à une solution construite. Les deux méthodes peuvent le choisir. |
| `constructed-continuity` | Faire échouer le secours initial, conserver les coûts de l’accord annulé, construire une répartition admissible, perdre un accusé d’acceptation et redémarrer le candidat. |
| `repair-after-rejection` | Interrompre une exportation durable, reprendre la même identité, rejeter le contenu incorrect et financer/réserver une correction distincte. |
| `technical-no-trade` | Rejeter l’achat modélisé tandis qu’un contrôle technique explicitement autorisé et financé séparément réalise le produit. |
| `no-deal` | Maintenir la capacité alternative totale de 800 unités sous la promesse de 1 900 unités. Aucune solution complète n’existe dans ce domaine modélisé. |
| `uncertain-value` | Conserver un intervalle de valeur de l’acheteur couvrant l’acceptabilité, sans choisir une valeur avantageuse et la présenter comme consentement. |

DL-100 exige 1 100 unités à la révision 2 ; DL-200 exige 800 unités à la révision 1 ; DL-300 est annulée. Chaque contrat préenregistré contient l’historique et le contenu bilingue exact. Les lots admissibles contiennent 500 unités ou le reste final. Le fractionnement est une autorisation initiale explicite, jamais ajoutée après une panne. L’échéance logique de base est 500, la limite d’observation 800 et le délai écoulé 60 000 ms. Les conditions logiques et monotones d’observation s’appliquent toutes deux. Les graduations représentent des opérations modélisées, pas des secondes ; l’avance vers une fenêtre de capacité est une action enregistrée de l’horloge simulée. Les durées réelles et le calcul consommé sont mesurés séparément.

## Participation modélisée et interprétation des coûts

Tous les montants sont des entiers exacts en **unités mineures SMU** ; 100 unités mineures fictives forment une SMU. Aucun taux de change ni prix réel n’est impliqué. Chaque fournisseur possède des coûts, un bénéfice extérieur, une échéance de consentement, des fonds et une limite de responsabilité. Le coordonnateur a un coût d’exploitation et un seuil de participation. L’acheteur possède un intervalle de valeur, une utilité extérieure, un plafond de prix et des fonds disponibles. Les politiques sont conservées indépendamment et le candidat ne peut les réécrire. Une proposition se distingue de la décision séparée des participants et de l’accord financé.

Le minimum proposé à chaque fournisseur couvre le travail initial, la provision financière pour une correction complète autorisée et le plus grand du bénéfice minimal ou extérieur. Les frais du coordonnateur couvrent le coût courant, son seuil de participation et les coûts de coordination annulés non remboursés. L’acheteur accepte seulement si la valeur modélisée moins le prix total atteint l’utilité extérieure, respecte son plafond et dispose du financement. Pour l’intervalle `[L,U]`, un prix `P` est certainement acceptable seulement si `L ≥ P + utilité extérieure`, possiblement acceptable si `U ≥ P + utilité extérieure`, sous réserve des autres contraintes. Le vérificateur rapporte cette région sans inventer une volonté de payer.

Le séquestre de l’acheteur et les fonds de roulement réservés ne peuvent être comptés deux fois. Les coûts modélisés effectivement engagés de production et de correction vont à un compte explicite de coûts ; les transferts conservent le total du registre modélisé. Une provision de correction inutilisée n’est pas un coût engagé. La provision financière ne garantit pas une capacité future : chaque correction exige une nouvelle réservation autorisée. Rejets, annulations et travail abandonné restent dans la comptabilité de campagne. Une acceptation partielle acquise interdit l’annulation silencieuse de l’accord : séquestre et responsabilités restent actifs ; le règlement partiel consenti n’est pas implémenté. Un participant peut consentir à une exposition bornée à l’échec et subir une perte réalisée ; ces deux observations doivent être rapportées.

## Comparaison équitable et connaissances transférables

La méthode conventionnelle énumère le domaine borné complet des affectations admissibles. Le banc d’essai explore ce même domaine avec élagage par capacité et prix non négatifs. Les deux reçoivent le même contrat public, les mêmes politiques, observations, fonds, possibilités de capacité, outils, reprises et limites de requêtes. Les deux peuvent restaurer, utiliser le secours ordinaire ou construire une solution admissible. La référence d’acceptation conservée leur reste inaccessible. L’épuisement d’une recherche se distingue de l’infaisabilité démontrée. Une énumération finie n’est ni une preuve générale ni une mesure de performance d’IA.

La méthode sans achat n’exécute ni production ni accord financier. La performance IA reste **NON EXÉCUTÉE**. Une observation par cellule et un ordre fixe ne peuvent établir des écarts de vitesse statistiquement fiables. Le calcul processeur des enfants et du contrôleur, la durée, les requêtes, redémarrages, stockage et travail de vérification fraîche sont rapportés. La mesure du contrôleur s’arrête avant son enregistrement/sceau final et le rendu des passeports ; ce travail reste une lacune explicite. Les efforts de préparation, intégration, adaptation et vérification restent inconnus s’ils ne sont pas mesurés. Aucun avantage de coût n’est conclu sur une comptabilité incomplète.

Le successeur doit être rédigé après la première expérience de base et le gel versionné du code réutilisable, des interfaces, de la documentation et des connaissances autorisées. Les mêmes algorithmes et schémas généraux sont accessibles au contrôle conventionnel. Produits achevés, données du destinataire, réponses cachées et corrections particulières du successeur sont exclus de son matériel initial. Toute correction ultérieure constitue une adaptation ; l’échec initial reste conservé. Un transfert synthétique unique n’établit ni découverte générale, ni autonomie, ni réseau de fournisseurs, ni capacité commerciale de passage à l’échelle.

## Preuves et limites

Chaque exécution conserve contrat, politiques, référence originale, sceau protégé, événements du contrôleur, journaux de processus, bases SQLite réelles, produits et contenu reçu, reçus bruts, acceptations sémantiques, décisions des participants et transferts. `RESULT.json`, `PASSPORT.en.md` et `PASSPORT.fr.md` proviennent d’une même évaluation structurée. Le vérificateur frais rejoue les preuves durables sans prendre ces rapports ou un statut favorable du producteur comme oracle. Assertions, verdicts des composants, stades de preuve et état des affirmations restent séparés.

L’hôte, le contrôleur, le journal synthétique, l’horloge et la garde des services restent de confiance. Producteur, destinataire et vérificateur ont des implémentations/processus distincts sous une responsabilité d’auteur commune ; il ne s’agit pas de certification tierce. Les tests couvrent des points de transition énumérés et des pannes échantillonnées, pas toutes les interactions, pannes matérielles ou plateformes. Le modèle de menace et la matrice précisent cette frontière. Seuls les processus jetables de l’exercice sont fermés ; les exécutions échouées et fichiers partiels restent inspectables. Aucun client, fournisseur, argent ou système de production réel n’est contacté.
