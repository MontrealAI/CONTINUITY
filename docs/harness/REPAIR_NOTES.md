# Route permissions and queue leases / Autorisations de voie et baux de file

## English

These targeted corrections start from `8da36d5d471f9a980ddbbf9d8632505da43838ea`. That revision passes its existing 245 tests but has two independently reproduced defects:

- `sharing=false` incorrectly prevents authorized primary recovery. Sharing permission applies to the backup provider, while activation permission applies to both routes.
- A feasible seven-order queue reserves everything at once. With the unchanged 20-tick lease, the final reservation expires before commit; only 60 of 70 units complete.

The candidate and controller now enforce route-specific permissions. Every reservation batch is preflighted before recording reservations or calling the service. Commit and fulfillment recheck current route permissions; revoking sharing still blocks backup work, revoking activation blocks both routes, and safe release remains available.

Both conventional and Harness candidates reserve bounded chunks instead of aging every queued lease upfront. Each order requires lookup, commit and fulfillment; the chunk size is `max(1, lease_ticks // 3)`. This leaves commit before expiry for feasible leases. Existing reservation keys and digests are not renewed or rewritten. Leases of one or two ticks still expire under this protocol; deadlines, resource budgets and capacity can still make an exercise infeasible.

No service, schema, independent verifier, registered experiment, historical publication or retained previous result is changed. The registered two-order constrained race and lost-acknowledgment/crash/restart controls remain exercised.

During development, independent review identified an intermediate preflight bug: conflicting new keys within one batch could desynchronize the cached route from the durable reservation. The final implementation rejects these conflicts before any cache or service mutation; a dedicated regression covers both changed obligations and changed routes. The intermediate patch was not published.

### Validation

- The eight new regression tests include both methods, primary and backup routes, 7- and 20-order queues, short leases, mixed unauthorized batches, and permission revocation. The initial seven-test regression set produces 18 subtest failures and one error against the unchanged starting implementation. All eight final tests pass against the repair.
- All 253 repository tests pass locally.
- The registered comparison executes 24 runs with 12 explicit AI NOT RUN records; separate fresh suite verification passes with no failed assertions or critical safety failures.
- All eight adversarial challenge records pass their assertions, including three exposed verifier mutations. These are not eight successful business continuities.
- Independent review additionally exercises 12-order queues for both methods/routes at leases 2, 3, 5, 6 and 20, plus mixed-batch and revocation probes. Feasible cases complete 120/120 units; lease 2 remains a safe refusal.
- Historical copy identity and publication consistency checks pass.

Reproduce with `python3 -m unittest discover -s tests -p 'test_*.py'`, then `python3 -m continuity_harness compare --out NEW_DIRECTORY`, `python3 -m continuity_harness verify-suite --in-dir NEW_DIRECTORY`, and `python3 -m continuity_harness challenge --out ANOTHER_NEW_DIRECTORY`. Never overwrite retained evidence. CI status must be checked for the exact proposed commit; local checks do not imply hosted success.

This is bounded regression evidence, not proof of complete correctness, real delivery, comparative advantage or commercial value. Existing host/controller trust and finite-test limitations remain. Earlier qualification attempts and their unresolved explanations are not rewritten by this repair.

## Français

Ces corrections ciblées partent de `8da36d5d471f9a980ddbbf9d8632505da43838ea`. Cette révision réussit ses 245 tests existants, mais présente deux défauts reproduits indépendamment :

- `sharing=false` empêche à tort la reprise autorisée sur la voie principale. L’autorisation de partage concerne le fournisseur de secours ; l’autorisation d’activation concerne les deux voies.
- Une file réalisable de sept commandes réserve tout dès le début. Avec le bail inchangé de 20 ticks, la dernière réservation expire avant engagement ; seulement 60 unités sur 70 sont réalisées.

Le candidat et le contrôleur appliquent désormais les autorisations propres à chaque voie. Chaque lot de réservations est contrôlé avant l’enregistrement des réservations ou l’appel au service. L’engagement et la réalisation revérifient les autorisations actuelles de la voie ; révoquer le partage bloque toujours le secours, révoquer l’activation bloque les deux voies, et la libération sûre reste possible.

Les candidats conventionnel et Harness réservent des lots bornés au lieu de laisser vieillir tous les baux de la file dès le départ. Chaque commande nécessite une consultation, un engagement et une réalisation ; la taille du lot est `max(1, lease_ticks // 3)`. L’engagement précède ainsi l’expiration pour les baux réalisables. Les clés et empreintes existantes ne sont ni renouvelées ni réécrites. Les baux d’un ou deux ticks expirent toujours avec ce protocole ; les échéances, limites de ressources et capacités peuvent toujours rendre un exercice irréalisable.

Aucun service, schéma, vérificateur indépendant, expérience préenregistrée, publication historique ou résultat antérieur conservé n’est modifié. La concurrence préenregistrée entre deux commandes et les contrôles de perte d’accusé de réception, arrêt et redémarrage restent exercés.

Pendant le développement, la revue indépendante a identifié un défaut intermédiaire : des clés nouvelles contradictoires dans un même lot pouvaient désynchroniser la voie en cache de la réservation durable. L’implémentation finale refuse ces conflits avant toute mutation du cache ou du service ; un test dédié couvre les changements d’obligation et de voie. Le correctif intermédiaire n’a pas été publié.

### Validation

- Les huit nouveaux tests de régression couvrent les deux méthodes et voies, les files de 7 et 20 commandes, les baux courts, les lots mixtes non autorisés et la révocation. Les sept premiers tests produisent 18 échecs de sous-tests et une erreur sur l’implémentation initiale inchangée. Les huit tests finaux réussissent avec la correction.
- Les 253 tests du dépôt réussissent localement.
- La comparaison préenregistrée exécute 24 essais et consigne explicitement 12 cas d’IA NON EXÉCUTÉS ; la vérification fraîche séparée réussit sans assertion échouée ni défaillance critique de sécurité.
- Les huit observations contradictoires satisfont leurs assertions, dont trois mutations de vérificateur exposées. Il ne s’agit pas de huit continuités métier réussies.
- La revue indépendante exerce aussi des files de 12 commandes, pour les deux méthodes et voies, avec des baux de 2, 3, 5, 6 et 20 ticks, ainsi que des contrôles de lots mixtes et de révocation. Les cas réalisables achèvent 120 unités sur 120 ; le bail de 2 ticks reste un refus sûr.
- Les contrôles d’identité des copies historiques et de cohérence des publications réussissent.

Reproduire avec `python3 -m unittest discover -s tests -p 'test_*.py'`, puis `python3 -m continuity_harness compare --out NOUVEAU_REPERTOIRE`, `python3 -m continuity_harness verify-suite --in-dir NOUVEAU_REPERTOIRE` et `python3 -m continuity_harness challenge --out AUTRE_NOUVEAU_REPERTOIRE`. Ne jamais écraser les preuves conservées. Vérifier la CI pour le commit proposé exact ; les contrôles locaux ne prouvent pas la réussite hébergée.

Ces observations de régression sont bornées : elles ne prouvent ni correction complète, ni livraison réelle, ni avantage comparatif, ni valeur commerciale. Les limites de confiance dans l’hôte et le contrôleur ainsi que celles des tests finis demeurent. Cette correction ne réécrit pas les tentatives de qualification antérieures ni leurs explications non établies.
