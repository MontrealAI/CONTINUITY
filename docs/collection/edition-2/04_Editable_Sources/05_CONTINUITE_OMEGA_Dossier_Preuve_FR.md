# CONTINUITÉ Ω

## Des preuves vérifiables

Comprendre les résultats, éprouver l’affirmation et savoir quelle preuve établir ensuite

Edition 2 · 7 novembre 2026


## La portée des preuves

**Les preuves publiées établissent une exécution logicielle locale de continuité.** Le logiciel reconstitue les obligations, essaie une voie permise et vérifie les résultats selon la promesse conservée. [R1, R2, R3]

![La branche principale établit une exécution logicielle locale. Livraison client et service répétable exigent des preuves supplémentaires. [R2, R4, R6]](../06_Visuals/evidence_ladder_fr.png)

### Résultat

Le travail prévu respecte-t-il les conditions d’acceptation initiales ?

### Faisabilité du service

Des participants volontaires disposent-ils des droits, capacités, délais et financements nécessaires ?

### Preuves de marché

Des achats réels, des livraisons acceptées et les coûts complets étayent-ils l’affirmation commerciale ?

> **Périmètre de cette édition**
> Sources vérifiées le 6 novembre 2026 à 20 h 36 (Toronto) ; branche principale 396227d8. Aucun test du dépôt ni exercice métier réexécuté.


## Trois commandes pour comprendre l’enjeu

Une application restaurée peut fonctionner alors que son carnet de commandes est erroné. L’exercice de base révèle ce problème avec trois commandes d’étiquettes. L’historique conservé contient une modification et une annulation absentes de la restauration périmée. [R2]

| Commande | Obligation conservée | Dossier restauré périmé |
| --- | --- | --- |
| A | 1 100 unités | 1 000 unités |
| B | 800 unités | Absente |
| C | Annulée | 600 unités encore indiquées |
Le total faisant autorité est de **1 900 unités dans deux commandes**. Le rapprochement correct doit rétablir B, appliquer la quantité modifiée de A et maintenir l’annulation de C. Une voie ne peut améliorer son résultat apparent en effaçant discrètement une obligation. [R2, R3]

| Voie exercée | Résultat consigné |
| --- | --- |
| Reprise principale réalisable | Les deux obligations sont réalisées : 1 900/1 900. |
| Secours autorisé disposant de 2 100 unités | Les deux obligations sont réalisées : 1 900/1 900. |
| Secours limité à 1 500 unités | A réalisée : 1 100. B refusée : 800. Il ne restait que 400 unités après A. |
> **Deux verdicts peuvent être justes**
> Dans le cas contraint, la contrainte de capacité éprouvée est respectée et la promesse complète échoue. Le refus évite une réservation excessive ; les 800 unités non réalisées restent visibles. Une assertion de test réussie peut correctement constater ce résultat partiel. [R2, R3]

Ces quantités désignent des résultats logiciels locaux durables. L’exercice n’établit ni l’impression d’étiquettes ni leur livraison à des clients réels. Production physique et acceptation client exigent leurs propres observations. [R2, R3]


## Lire les résultats sans effacer leur histoire

| Dossier | Signification |
| --- | --- |
| Prototype de recherche · a755d037 | 29 tests de l’implémentation réussis ; des contrôles distincts exposent des faiblesses d’entrée et d’authenticité des sources. Transmission synthétique seulement. [R7] |
| Première qualification · 5c92fd03 | Un résumé favorable échoue à une vérification ultérieure. La tentative reste non qualifiée et conservée. [R3] |
| Banc d’essai qualifié · fa9da1f5 | Deuxième tentative : 245 tests et 24 exécutions comparatives. Les 12 paires procédure conventionnelle/banc d’essai sont à égalité. [R3] |
| Branche principale · 396227d8 | Corrections ultérieures des droits de voie et des réservations en file ; 253 tests locaux rapportés. L’historique conserve ses identités. [R5, R9] |
Les corrections permettent la reprise principale autorisée sans exiger le partage avec le prestataire de secours. Les deux méthodes réservent aussi par lots bornés pour éviter que tous les baux vieillissent pendant l’attente. Baux courts, échéances et capacité insuffisante restent contraignants. [R5]

Les **245** tests historiques et les **253** tests ultérieurs décrivent des versions différentes. La comparaison préenregistrée établit des méthodes exécutables, avec **12 égalités fonctionnelles**. Les **12 entrées d’IA sont NON EXÉCUTÉES** ; aucun avantage propre à l’IA ni de coût complet n’est établi. [R1, R3, R5]

> **La v0.2 reste en revue**
> Lors de la vérification des sources, la demande de fusion 3 était ouverte et non fusionnée, au commit f9e56c7dd9627b322406e05c53b4f6537d434262. Elle propose une expérience distincte de produit numérique et de participation modélisée. Ses affirmations restent séparées des résultats de la branche principale présentés ici. Cet état est daté ; une décision ultérieure doit être vérifiée. [R10, R11]


## Ce que signifie « indépendant » ici

**Le vérificateur reconstitue les obligations et examine les résultats durables actuels selon un contrat et une référence conservés séparément.** La déclaration du candidat ne suffit pas à établir l’acceptation. [R2, R4]

![Construire, contester et vérifier selon la promesse initiale. Rééprouver les corrections ; limiter le verdict aux preuves examinées. [R2, R3, R4]](../06_Visuals/verification_loop_fr.png)

- Conserver l’autorité initiale hors du contrôle permis au candidat ; modifier sa copie ne doit pas modifier l’obligation.

- Relire les pièces actuelles. Un passeport enregistré décrit une évaluation passée.

- Éprouver le vérificateur, y compris l’acceptation indue et le rejet injustifié. Refuser tous les résultats ne suffit pas à le qualifier.

> **La frontière de confiance reste explicite**
> L’hôte, le contrôleur, les services, le journal synthétique, l’horloge et le vérificateur restent de confiance. Des chemins de code distincts issus du même projet ne constituent pas une certification tierce. Des empreintes identiques ne prouvent pas l’authenticité ou l’exhaustivité des instructions d’un client réel. [R3, R4]


## Donner à l’évaluateur un test qui tranche

Une objection utile doit pouvoir changer le verdict. Les épreuves documentées ci-dessous permettent d’examiner les expériences conservées ; aucune nouvelle expérience n’a été réalisée pour ce livre. [R2, R3]

| Épreuve | Ce que le contrôle doit établir |
| --- | --- |
| Modifier l’obligation du candidat de 1 900 à 1 850 unités en conservant l’autorité originale. | Le dossier modifié ne satisfait pas la promesse complète d’origine. Des empreintes internes cohérentes ne rendent pas cette réécriture officielle. |
| Modifier un résultat tout en gardant un passeport favorable antérieur. | La nouvelle vérification examine la pièce modifiée. L’ancien rapport ne certifie pas son état actuel. |
| Supprimer l’empreinte de référence conservée séparément. | L’autorité reste NON ÉTABLIE. Recalculer une empreinte de remplacement commode ne comble pas la lacune. |
| Faire dépendre le secours de la même dépendance défaillante. | Un secours logique indisponible ne peut justifier une réalisation complète par cette voie. |
| Soumettre un témoin positif valide à un vérificateur volontairement défectueux. | Un rejet injustifié doit également disqualifier le vérificateur. Une preuve valide doit être acceptée lorsque les conditions déclarées sont remplies. |
| Donner les mêmes outils et informations à une méthode conventionnelle compétente. | Une égalité ne prouve pas une amélioration. Toute affirmation d’avantage doit résister à la comparaison complète et à son périmètre de coûts. |
Pour reproduire une épreuve, conserver l’autorité originale, identifier la copie altérée ou la mutation, consigner la réponse du composant testé puis le verdict de référence distinct. Préciser l’affirmation qui échoue. Le contre-exemple de la fonction partagée — 1 850 unités acceptées face à 1 900 exigées — montre l’intérêt d’éprouver aussi le vérificateur. [R3, R9]

> **Lire le bon verdict**
> Un test contradictoire peut réussir parce qu’il révèle une acceptation indue. Dans le même dossier, la qualification du vérificateur défectueux échoue. Réussite du test et réussite métier répondent à des questions distinctes. [R2, R3]


## Reproduire la version logicielle figée

Utiliser Linux x86_64 avec seccomp BPF, Python 3.10 ou ultérieur et Node.js pour les tests web du dépôt. L’exercice par défaut emploie des données synthétiques locales et la bibliothèque standard. Choisir des sorties inutilisées ; conserver les tentatives antérieures. Ces commandes n’ont pas été exécutées pour cette collection. [R2, R5]

```sh
git clone https://github.com/MontrealAI/CONTINUITY.git
cd CONTINUITY
git checkout --detach \
  396227d8da2f55f674f479de16089c7ce28ef290
python3 -m unittest discover -s tests -p 'test_*.py'
python3 -m continuity_harness --language fr demo \
  --out /tmp/continuite-preuves-demo-001
python3 -m continuity_harness --language fr verify-suite \
  --in-dir /tmp/continuite-preuves-demo-001
python3 -m continuity_harness --language fr compare \
  --out /tmp/continuite-preuves-comparaison-001
python3 -m continuity_harness --language fr verify-suite \
  --in-dir /tmp/continuite-preuves-comparaison-001
python3 -m continuity_harness --language fr challenge \
  --out /tmp/continuite-preuves-epreuves-001
```
Lire le résultat structuré et chaque obligation. Le code de sortie 0 d’une suite signifie que les assertions attendues ont réussi ; cela peut inclure un résultat partiel prévu. La vérification individuelle d’une promesse partielle retourne 3. Le code 2 indique une erreur de commande. La qualification historique possède ses propres références de code et d’archive dans R3. [R2, R3]

> **Une distinction nécessaire pour revérifier**
> Dans cette interface v0.1, verify-suite s’applique aux sorties indexées de demo et compare, pas aux répertoires challenge. Pour un cas contradictoire, utiliser sa commande verify exacte, son chemin d’autorité et l’empreinte originale. Conserver cette référence hors des données contrôlées par le candidat. [R2]


## La prochaine preuve décisive

La prochaine observation utile est un exercice autorisé pour une entreprise réelle, avec un prestataire réel et une solution de comparaison capable. Le pilote d’imprimerie décrit dans le dépôt reste une proposition sans approbations réelles. Son intérêt tient au test réfutable qu’il définit. [R6]

| Décision | Preuves susceptibles de la changer |
| --- | --- |
| La promesse a-t-elle été tenue ? | Une commande authentique, des conditions d’acceptation fixées et la décision d’un évaluateur habilité sur le résultat effectivement produit. Distinguer le substitut d’exercice de la livraison physique au client. |
| L’arrangement était-il réalisable ? | Consentements réels ; usage licite des données ; capacité qualifiée nette des autres engagements ; dépendances utilisables ; financement de la production, des corrections et des obligations restantes. |
| L’offre avait-elle un intérêt commercial ? | Décision d’achat réelle, paiement encaissé, coûts complets de campagne et passifs résiduels, comparés à une solution conventionnelle tenant la même promesse et au refus d’achat. |
Compter préparation, tentatives infructueuses, intégration, travail humain, réservations, exécution, vérification, transport pertinent, financement, soutien et remboursements. Consigner quand les fonds sont nécessaires et quand ils sont disponibles. Une marge modélisée positive n’établit pas ces observations. [R6, R7]

> **L’affirmation grandit avec les preuves**
> Un pilote payé et accepté étaye une affirmation sur cette transaction. Un service répétable exige des preuves supplémentaires de demande, de capacité disponible et d’économie complète. Une méthode conservée doit encore être éprouvée sur une nouvelle tâche distincte, avec une comparaison équitable, avant de revendiquer un bénéfice pour le successeur. [R6]

Une solution conventionnelle gagnante, un refus d’achat ou un échec demeure un constat décisif. Conserver ses conditions et sa raison. L’expérience suivante peut alors traiter l’obstacle démontré sans supposer que le marché existe déjà. [R6, R8]


## Laisser un dossier qu’un autre peut examiner

Le lecteur doit retrouver la promesse initiale, l’exécution, le contrôle actuel et l’affirmation avancée. Le banc d’essai sépare ces pièces pour permettre un nouvel examen du résultat. [R2]

| Pièce | Points à examiner |
| --- | --- |
| INDEX.json | Liste des exécutions, exhaustivité et références conservées. Protéger sa garde lors du transfert des preuves. |
| Autorité conservée | Contrat, historique et référence d’origine. Distinguer les faits écrits pour l’exercice de ceux authentifiés extérieurement. |
| Preuves durables et relevé du contrôleur | Base de données, pièces produites, transitions, interruptions et délais observés, dans le modèle de confiance déclaré. |
| RESULT.json et passeports bilingues | Résultat évalué, conditions échouées ou manquantes et commande exacte de vérification. Une présentation enregistrée conserve son évaluation. |
| Reçu de nouvelle vérification | Version, pièces actuelles et référence conservée effectivement examinées, verdict et moment du contrôle. |
### Comprendre le résultat exécuté

Commencer par le guide, les résultats complets et les corrections ultérieures : R2, R3 et R5.

### Éprouver les fondements

Lire le modèle de menace, l’expérience préenregistrée et l’historique conservé : R4, R8 et R9.

### Décider de l’étape de terrain

Utiliser le pilote proposé R6, les limites historiques de R7 et la carte du dépôt R1.

> **Conservation des sources de cette édition**
> Les copies complètes des sources figées accompagnent la collection. Leurs identités Git et empreintes SHA-256 établissent la fidélité de la copie. Elles ne prouvent pas chaque affirmation des sources ni une nouvelle exécution de leurs expériences. Branche principale et branche en revue possèdent des dossiers distincts.


## Sources

- R1: Présentation du dépôt. https://github.com/MontrealAI/CONTINUITY/blob/396227d8da2f55f674f479de16089c7ce28ef290/README.md
- R2: Guide du banc d’essai. https://github.com/MontrealAI/CONTINUITY/blob/396227d8da2f55f674f479de16089c7ce28ef290/docs/harness/README.md
- R3: Résultats de qualification exécutée. https://github.com/MontrealAI/CONTINUITY/blob/396227d8da2f55f674f479de16089c7ce28ef290/docs/harness/RESULTS.md
- R4: Modèle de menace et limites de confiance. https://github.com/MontrealAI/CONTINUITY/blob/396227d8da2f55f674f479de16089c7ce28ef290/docs/harness/THREAT_MODEL.md
- R5: Corrections des voies et des files. https://github.com/MontrealAI/CONTINUITY/blob/396227d8da2f55f674f479de16089c7ce28ef290/docs/harness/REPAIR_NOTES.md
- R6: Pilote réel proposé. https://github.com/MontrealAI/CONTINUITY/blob/396227d8da2f55f674f479de16089c7ce28ef290/docs/continuity-omega/REAL_PILOT.md
- R7: Guide du prototype historique. https://github.com/MontrealAI/CONTINUITY/blob/396227d8da2f55f674f479de16089c7ce28ef290/docs/continuity-omega/README.md
- R8: Protocole comparatif préenregistré. https://github.com/MontrealAI/CONTINUITY/blob/396227d8da2f55f674f479de16089c7ce28ef290/docs/harness/EXPERIMENT.md
- R9: Historique de validation. https://github.com/MontrealAI/CONTINUITY/blob/396227d8da2f55f674f479de16089c7ce28ef290/docs/harness/VALIDATION_HISTORY.md
- R10: Demande de fusion 3 — ouverte, non fusionnée. https://github.com/MontrealAI/CONTINUITY/pull/3
- R11: Guide de l’expérience v0.2 — branche en revue. https://github.com/MontrealAI/CONTINUITY/blob/f9e56c7dd9627b322406e05c53b4f6537d434262/docs/economy/README.md
