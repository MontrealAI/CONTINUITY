# Specification history / Historique de la spécification

- **Version 1, before comparisons / avant comparaison:** registered in `experiments/harness-v0.1/spec.json`. No comparative outcome had been inspected. / Consignée avant l’observation de tout résultat comparatif.

Implementation corrections and unsuccessful attempts will be recorded separately from changes to the acceptance contract. / Les corrections d’implémentation et tentatives infructueuses seront distinguées des modifications du contrat d’acceptation.

## English

The registered `spec.json` remains version 1 and byte-identical to local registration `318f6d76868fa63ce3e25805e1c11bbfc057f981`. Its identical content tree was published as `0b9eac772d8088a0ee44605aead85fa5d36dd93b` through the connected GitHub workflow because the local Git client had no push credential. The local registration preceded implementation integration controls; remote publication followed those controls and preceded the complete registered comparison. Publication did not reset the experiment or remove earlier development observations.

The separately recorded adversarial challenge specification is frozen before its own execution. It operationalizes the preregistered ablation and requested integrity/mutation controls. It is not another performance comparison and does not change the business acceptance criteria.

Implementation corrections, preserved counterexamples and accounting limits are recorded in [VALIDATION_HISTORY.md](VALIDATION_HISTORY.md). The final results report identifies the exact qualified implementation and every registered comparison attempt. Fixing an implementation to meet an already-declared condition is distinguished from changing that condition.

**After comparison attempt 1, implementation correction:** the complete registered comparison at `5c92fd03a258a3f4845c50a5b37e7a14cd2aa40c` initially reported a passing gate, but its separate fresh verification refused one transfer run because unsealed SQLite sidecars became visible. This attempt remains unqualified and retained unchanged. Evidence finalization was strengthened before a separately named second attempt. Hypotheses, fixtures, quantities, capacities, fault schedules, acceptance criteria and comparison conditions remain byte-identical to version 1; neither journal validation nor authority requirements were relaxed. Both attempts must be reported, without pooling them as independent favorable trials.

## Français

Le fichier préenregistré `spec.json` reste en version 1, identique octet pour octet à l’enregistrement local `318f6d76868fa63ce3e25805e1c11bbfc057f981`. Son arbre de contenu identique a été publié au commit `0b9eac772d8088a0ee44605aead85fa5d36dd93b` par l’interface GitHub connectée, car le client Git local ne disposait pas d’autorisation d’envoi. L’enregistrement local précède les contrôles d’intégration ; la publication distante suit ces contrôles et précède la comparaison préenregistrée complète. La publication ne remet pas l’expérience à zéro et ne supprime aucune observation de développement.

La spécification distincte des épreuves contradictoires est figée avant sa propre exécution. Elle rend exécutables l’ablation préenregistrée et les contrôles d’intégrité et de mutation demandés. Il ne s’agit pas d’une autre comparaison de performances ; les critères métier d’acceptation restent inchangés.

Les corrections d’implémentation, contre-exemples conservés et limites de mesure figurent dans [VALIDATION_HISTORY.md](VALIDATION_HISTORY.md). Le rapport final précise l’implémentation qualifiée et chaque tentative de comparaison préenregistrée. Corriger l’implémentation pour satisfaire une condition déjà déclarée se distingue d’une modification de cette condition.

**Après la première comparaison, correction d’implémentation :** la comparaison complète au commit `5c92fd03a258a3f4845c50a5b37e7a14cd2aa40c` a initialement annoncé une réussite, mais sa vérification fraîche distincte a refusé un cas de transfert en raison de fichiers auxiliaires SQLite non scellés devenus visibles. Cette tentative reste non qualifiée et conservée sans modification. La finalisation des preuves a été renforcée avant une deuxième tentative nommée séparément. Hypothèses, cas, quantités, capacités, pannes, critères d’acceptation et conditions comparatives restent identiques octet pour octet à la version 1 ; aucun contrôle de journal ou d’autorité n’a été assoupli. Les deux tentatives doivent être rapportées, sans les regrouper comme essais favorables indépendants.
