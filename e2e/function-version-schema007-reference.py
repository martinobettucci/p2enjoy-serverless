# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_MIGRATION_008.md#décision-et-invariants
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_MIGRATION_008.md#matrice-réelle
"""Attest the retained real schema007 image before a historical DEV window."""
import hashlib,json,runpy,subprocess,time
from pathlib import Path

r=runpy.run_path('e2e/execution-suite.py');folder=Path('.local/e2e');report=folder/'function-version-control-schema007-reference.json';assert not report.exists(),'preserve_reference_report'
source=Path('docs/evidence/function-version-registry-dev-2026-11-09.json');proof=json.loads(source.read_text());image=proof['control_image']
assert image=='sha256:fe75c9e7ecd4ebf0783f5272707d337633695be9d1e0806474ee5bacf3d96f60'
expected={n.removeprefix('control/'):v for n,v in proof['source_sha256_at_execution'].items() if n.startswith(('control/app/','control/migrations/')) or n=='function_code_hash.py'}
assert len([n for n in expected if n.startswith('migrations/')])==7
before=r['snapshot'](str(report),False,include_adapter=True)
program='expected='+repr(expected)+'\nimage='+repr(image)+'\nproof_sha='+repr(hashlib.sha256(source.read_bytes()).hexdigest())+'\n'+'''
import hashlib,json,os,socket,subprocess,uuid
from pathlib import Path
assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
root=Path('/srv/p2enjoy-serverless');d=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
def cmd(args):return subprocess.check_output(args,text=True,timeout=40,cwd=root).strip()
services=json.loads(cmd(d+['inspect','serverless-api','serverless-runtime-reference']));tag=cmd(d+['image','inspect','p2enjoy-control:dev','--format','{{.Id}}']);assert services[0]['Image']==tag and all(v['State']['Health']['Status']=='healthy' for v in services)
assert cmd(d+['image','inspect',image,'--format','{{.Id}}'])==image
inspection="""import hashlib,json
from pathlib import Path
r=Path('/app');files=[*r.joinpath('app').glob('*.py'),*r.joinpath('migrations').glob('*.sql'),r/'function_code_hash.py']
print(json.dumps({str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}))
"""
name='serverless-schema007-source-inspector-'+uuid.uuid4().hex
embedded=json.loads(cmd(d+['run','--rm','--name',name,'--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges:true','--memory','128m','--cpus','.5','--pids-limit','32','--entrypoint','python',image,'-B','-c',inspection]));assert embedded==expected,'historical_schema007_sources_mismatch'
assert not cmd(d+['ps','-aq','--filter','name=^/'+name+'$'])
reference={'completed':True,'schema':'007','image':image,'tag':'p2enjoy-control:historical-schema-007','schema_migrations':sorted(Path(n).name for n in embedded if n.startswith('migrations/')),'embedded':embedded,'registry_proof_sha256':proof_sha}
path=root/'qualification-history/function-version-schema007-image.json'
if path.exists():
 info=path.lstat();assert not path.is_symlink() and info.st_uid==0 and info.st_mode&0o777==0o600;assert json.loads(path.read_text())==reference,'historical_reference_changed'
else:
 with open(path,'x',opener=lambda n,f:os.open(n,f,0o600)) as stream:json.dump(reference,stream);stream.flush();os.fsync(stream.fileno())
cmd(d+['tag',image,reference['tag']]);assert cmd(d+['image','inspect','p2enjoy-control:dev','--format','{{.Id}}'])==tag
current=json.loads(cmd(d+['inspect','serverless-api','serverless-runtime-reference']));assert all([a['Id'],a['Image'],a['State']['StartedAt']]==[b['Id'],b['Image'],b['State']['StartedAt']] for a,b in zip(services,current))
print(json.dumps({**reference,'attestation':str(path),'attestation_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'served_services_unchanged':True,'current_tag_unchanged':True,'inspector_absent':True}))
'''
started=time.time_ns();p=subprocess.run(r['SSH']+['root@10.77.0.24','python3 -B -'],input=program,capture_output=True,text=True,timeout=120)
log=folder/'function-version-control-schema007-reference.log';log.write_text(p.stdout+p.stderr)
after=r['snapshot'](str(report),False,include_adapter=True);assert before['source_sha256']==after['source_sha256'] and before['image']==after['image'] and before['adapter_images']==after['adapter_images']
value=json.loads(p.stdout) if p.returncode==0 else {'completed':False};value.update(before=before,after=after,exit_code=p.returncode,started_at_ns=started,ended_at_ns=time.time_ns(),log_sha256=hashlib.sha256(log.read_bytes()).hexdigest());report.write_text(json.dumps(value,indent=2)+'\n');assert value['completed'],'inspect_reference_report_no_automatic_retry'
print(json.dumps({'completed':True,'image':image,'backend_files':len(expected),'served_services_unchanged':True}))
