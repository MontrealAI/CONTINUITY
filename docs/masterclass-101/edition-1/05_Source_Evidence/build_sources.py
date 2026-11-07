from pathlib import Path
import hashlib, json, datetime

base=Path(__file__).resolve().parent
head='56aa3e0ca995cdbbfe46165f0e68edf7c10004dc'
records={x['path']:x for x in json.loads((base/'repository_records.json').read_text())}
source_map={
'R20':('README.md','Current repository overview','Vue d’ensemble du dépôt actuel'),
'R21':('docs/economy/README.md','Economy v0.2 setup and commands','Économie v0.2 : installation et commandes'),
'R22':('docs/economy/RESULTS.md','Economy v0.2 original results and chronology','Économie v0.2 : résultats initiaux et chronologie'),
'R23':('docs/economy/THREAT_MODEL.md','Economy v0.2 threat model and limitations','Économie v0.2 : modèle de menace et limites'),
'R27':('docs/economy/PRODUCT.md','Digital product and acceptance','Produit numérique et acceptation'),
'R28':('docs/economy/SUCCESSOR.md','Changed successor and historical reuse','Nouveau cas et réutilisation historique'),
'R29':('evidence/economy-v0.2/qualification.json','Historical complete qualification record','Dossier historique de qualification complète'),
'R30':('evidence/economy-v0.2/README.md','Retained original evidence guide','Guide des preuves initiales conservées'),
'R31':('experiments/economy-v0.2/reuse-freeze.json','Historical 42-file reuse freeze','Gel historique de 42 fichiers pour la réutilisation'),
'R32':('docs/harness/RESULTS.md','Harness v0.1 historical results','Résultats historiques du banc d’essai v0.1'),
'R33':('docs/harness/REPAIR_NOTES.md','Harness v0.1 subsequent repairs','Corrections ultérieures du banc d’essai v0.1'),
'R34':('docs/harness/VALIDATION_HISTORY.md','Harness validation history','Historique de validation du banc d’essai'),
'R35':('docs/continuity-omega/REAL_PILOT.md','Proposed real pilot boundary','Périmètre proposé d’un pilote réel'),
'R36':('docs/economy/RESULTS.fr.md','Economy v0.2 original results in French','Économie v0.2 : résultats initiaux en français'),
'R37':('docs/economy/AMENDMENTS.md','Preregistered economy amendments','Amendements préenregistrés de l’expérience économique'),
'R38':('docs/economy/REQUIREMENTS.md','Economy requirements and tests','Exigences et tests de l’expérience économique'),
'R39':('evidence/economy-v0.2/review-repair/REVIEW.json','Aggregate coverage review finding','Constat de revue sur la couverture agrégée'),
'R40':('continuity_economy/suite.py','Current aggregate verifier source','Source actuelle du vérificateur agrégé'),
'R45':('docs/economy/EXPERIMENT.md','Preregistered economy experiment','Expérience économique préenregistrée'),
'R46':('docs/economy/REVIEW_REPAIR.md','Post-review repair and retained local failure','Correction après revue et échec local conservé'),
'R47':('evidence/economy-v0.2/review-repair/QUALIFICATION.json','Post-review qualification evidence','Preuves de qualification après revue'),
'R48':('evidence/economy-v0.2/review-repair/final-audit/AUDIT.json','Retained final evidence audit','Audit final des preuves conservées')
}
out={}
for key,(path,en,fr) in source_map.items():
 r=records[path]
 out[key]={'url':r['url'],'title_en':en,'title_fr':fr,'kind':'pinned_repository_source','local_path':r['local_path'],'version':head,'evidence_note':'Read-only GitHub connector retrieval. Historical records retain their own source dates and verdicts. No experiment was rerun for this course audit.','git_blob_sha':r['git_blob_sha'],'sha256':r['sha256'],'bytes':r['bytes']}
status={
'R24':('PR3.json','https://api.github.com/repos/MontrealAI/CONTINUITY/pulls/3','Pull request 3 merge status','État de fusion de la demande 3','Merged 2026-11-07T02:07:52Z at 175cbff2016ad0648853f176ff1ce68e622a3d31. Older prose in the body is historical.'),
'R25':('MAIN_VALIDATION.log','https://github.com/MontrealAI/CONTINUITY/actions/runs/42329498128/job/128272525279','Current main validation log','Journal de validation de la branche principale','Observed GitHub CI: 436 tests in 86.320 seconds, OK, at 56aa3e0c. Not a local course-author run.'),
'R26':('REVIEW_REPAIR_COMMIT.json','https://api.github.com/repos/MontrealAI/CONTINUITY/commits/f9e56c7dd9627b322406e05c53b4f6537d434262','Aggregate verifier repair commit','Commit de correction du vérificateur agrégé','Source correction and twelve aggregate-admission tests. Leaf verdict stubs isolate coverage admission.'),
'R41':('MAIN_BRANCH.json','https://api.github.com/repos/MontrealAI/CONTINUITY/branches/main','Current main branch API response','Réponse API de la branche principale actuelle','Observed main 56aa3e0c. Mutable endpoint; complete snapshot preserves the observation.'),
'R42':('MAIN_WORKFLOWS.json','https://api.github.com/repos/MontrealAI/CONTINUITY/actions/runs?head_sha='+head+'&per_page=10','Current main workflow statuses','États des workflows de la branche principale','All three workflows completed successfully for the exact current main SHA.'),
'R43':('MAIN_ECONOMY_JOBS.json','https://api.github.com/repos/MontrealAI/CONTINUITY/actions/runs/42329498176/jobs','Current economy job and steps','Tâche économique actuelle et étapes','Focused tests, registered complete execution and independent fresh verification steps succeeded.'),
'R44':('MAIN_ECONOMY.log','https://github.com/MontrealAI/CONTINUITY/actions/runs/42329498176/job/128272525508','Current economy job log','Journal de la tâche économique actuelle','183 focused tests in 38.957 seconds. Complete execution and fresh verification records are retained separately from older failed local replay.'),
'R49':('FINAL_EVIDENCE_MERGE.json','https://api.github.com/repos/MontrealAI/CONTINUITY/commits/'+head,'Final evidence merge commit','Commit de fusion des preuves finales','Merged at 2026-11-07T02:29:24Z with parents 175cbff2 and 28aebe96. Documentation and evidence publication, no runtime changes.'),
'R50':('MAIN_VALIDATION_JOBS.json','https://api.github.com/repos/MontrealAI/CONTINUITY/actions/runs/42329498128/jobs','Current validation job and steps','Tâche de validation actuelle et étapes','Authoritative API workflow observation for current main.')}
for key,(file,url,en,fr,note) in status.items():
 p=base/'status'/file;b=p.read_bytes()
 out[key]={'url':url,'title_en':en,'title_fr':fr,'kind':'github_api_or_ci_snapshot','local_path':str(p.relative_to(base.parent.parent)),'version':head if key not in ['R24','R26'] else ('175cbff2016ad0648853f176ff1ce68e622a3d31' if key=='R24' else 'f9e56c7dd9627b322406e05c53b4f6537d434262'),'evidence_note':note,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
guidance={
'N1':('https://csrc.nist.gov/pubs/sp/800/34/r1/upd1/final','NIST SP 800-34 Rev. 1: Contingency Planning Guide','NIST SP 800-34 rév. 1 : planification de contingence','2010-05, updated 2010-11-11','Business impact analysis, recovery priorities, RTO/RPO, alternate strategies and tests/training/exercises. Sections 3.2, 3.4, 3.5. Federal guidance may inform this course; no certification claim.','https://nvlpubs.nist.gov/nistpubs/legacy/sp/nistspecialpublication800-34r1.pdf'),
'N2':('https://csrc.nist.gov/pubs/sp/800/184/final','NIST SP 800-184: Guide for Cybersecurity Event Recovery','NIST SP 800-184 : reprise après un événement de cybersécurité','2016-12','Business priorities, dependencies, playbooks, recovery validation and improvement. Section 3.1. Do not reuse historical CSF function enumeration as current.','https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-184.pdf'),
'P1':('https://www.cdc.gov/training-development/php/qts/','CDC Quality Training Standards','Normes de qualité de la formation du CDC','Page dated 2026-10-01','Used to inform objective/practice/assessment alignment, accuracy, engagement, accessibility and follow-up. Public-health training origin. No endorsement or accreditation.',None),
'P2':('https://www.cdc.gov/training-development/php/about/evaluate-training-measuring-effectiveness.html','CDC: Evaluate Training, Measuring Effectiveness','CDC : évaluer l’efficacité d’une formation','Page dated 2024-10-28','Distinguishes learning and transfer; posttest alone measures end proficiency, not learning gain. Satisfaction does not establish effectiveness.',None)}
for key,(url,en,fr,version,note,pdf) in guidance.items():
 p=base/'guidance'/'official_pages.json'
 out[key]={'url':url,'title_en':en,'title_fr':fr,'kind':'official_government_guidance','local_path':str(p.relative_to(base.parent.parent)),'version':version,'evidence_note':note,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 if pdf:out[key]['pdf_url']=pdf;out[key]['additional_snapshot']='continuity_masterclass/research/guidance/nist_pdf_retrieval.json'
(base/'sources.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
meta={'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'current_main':head,'main_merge_at_utc':'2026-11-07T02:29:24Z','pr3_merge_at_utc':'2026-11-07T02:07:52Z','retrieval_tools':['github_fetch','github_fetch_file','github_fetch_workflow_job_logs','official web search/open'],'repository_snapshot_count':len(records),'all_blob_identities_verified':all(r['git_blob_match'] for r in records.values()),'local_repository_tests_executed':False,'archives_downloaded_or_extracted_for_this_audit':False,'prior_observation_preserved_under':'versions/175cbff2016ad0648853f176ff1ce68e622a3d31','scope':'Source audit, not fresh reproduction or third-party certification'}
(base/'audit_metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
print('Wrote',len(out),'source entries')
