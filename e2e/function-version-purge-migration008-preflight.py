# @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_MIGRATION_008.md#refus-avant-la-fenêtre
# @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_MIGRATION_008.md#refus-avant-la-fenêtre
"""Real invalid historical-window invocations must leave the served DEV installation intact."""
from contextlib import closing
import hashlib,json,os,re,socket,sqlite3,stat,subprocess,time
from pathlib import Path
from uuid import uuid4
from control_database import control_owner

ROOT=Path('/srv/p2enjoy-serverless');assert os.geteuid()==0 and socket.gethostname()=='infra-serverless'
D=['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock']
report=ROOT/'control/function-version-purge-migration008-preflight.json';assert not report.exists(),'preserve_previous_preflight_report'
checks=[];observations=[];completed=False


def cmd(args):return subprocess.check_output(args,text=True,timeout=40,cwd=ROOT).strip()
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save():report.write_text(json.dumps({'completed':completed,'skipped':0,'checks':checks,'observations':observations},indent=2)+'\n')


def snapshot():
    services=json.loads(cmd(D+['inspect','serverless-api','serverless-runtime-reference']))
    result={'services':[{'id':v['Id'],'image':v['Image'],'started_at':v['State']['StartedAt'],'health':v['State']['Health']['Status'],'environment_sha256':hashlib.sha256(json.dumps(sorted(v['Config']['Env'])).encode()).hexdigest()} for v in services],
        'official_sha256':{n:sha(n) for n in ['/etc/spark/env','/run/spark/secrets','/etc/spark/routes']},'directories':{},'tables':{}}
    assert services[0]['Image']=='sha256:def45648f9e74490a18c5d05f79681d838fbd10fdb519bc8942f9fffe4decbe4' and all(v['State']['Health']['Status']=='healthy' for v in services)
    for name in ('state','storage-state','storage-channel'):
        info=(ROOT/name).lstat();result['directories'][name]=[info.st_dev,info.st_ino,info.st_uid,info.st_gid,stat.S_IMODE(info.st_mode)]
    for path in [ROOT/'state/control.sqlite3',ROOT/'storage-state/registry.sqlite3']:
        with control_owner(ROOT/'state/control.sqlite3'),closing(sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True)) as db:
            db.execute('BEGIN');tables={}
            for (table,) in db.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name"):
                assert re.fullmatch(r'[a-zA-Z_][a-zA-Z_0-9]*',table)
                rows=sorted(json.dumps(list(v),default=lambda raw:raw.hex()) for v in db.execute('SELECT * FROM '+table));tables[table]={'rows':len(rows),'sha256':hashlib.sha256(json.dumps(rows).encode()).hexdigest()}
            result['tables'][path.name]=tables
    return result


old=json.loads((ROOT/'qualification-history/function-version-schema006-image.json').read_text())['image']
known=json.loads((ROOT/'qualification-history/function-version-schema007-image.json').read_text())['image']
cases=[('implicit-target007-on008',old,[],'explicit_target_schema_mismatch'),
       ('source007-without-target008',known,['--source-schema007'],'source007_requires_explicit_target008'),
       ('source007-image-as006',known,['--target-schema008'],'known_historical_image_required')]
save()
for name,image,options,diagnostic in cases:
    campaign=str(uuid4());work=ROOT/'qualification-history'/('function-version-purge-'+campaign);assert not work.exists()
    before=snapshot();p=subprocess.run(['/usr/bin/python3','-B',str(ROOT/'e2e/storage-legacy-environment.py'),'function-version-purge',campaign,image,*options],capture_output=True,text=True,timeout=120,cwd=ROOT)
    try:
        assert p.returncode!=0 and not p.stdout.strip() and 'AssertionError: '+diagnostic in p.stderr,'expected_preflight_refusal_missing'
        states={}
        for suffix in ('timer','service'):
            raw=cmd(['systemctl','show','serverless-restore-version-purge-'+campaign+'.'+suffix,'--property=LoadState','--property=ActiveState']);row=dict(line.split('=',1) for line in raw.splitlines());assert row=={'LoadState':'not-found','ActiveState':'inactive'};states[suffix]=row
        removed=False
        if work.exists():
            info=work.lstat();assert not work.is_symlink() and stat.S_ISDIR(info.st_mode) and info.st_uid==0 and info.st_gid==1001 and stat.S_IMODE(info.st_mode)==0o750 and not list(work.iterdir()),'nonempty_or_foreign_preflight_work'
            work.rmdir();removed=True
        assert not work.exists();after=snapshot();assert before==after,'preflight_changed_served_installation'
        observations.append({'name':name,'campaign':campaign,'image_argument':image,'options':options,'expected_diagnostic':diagnostic,'exit_code':p.returncode,'stderr_sha256':hashlib.sha256(p.stderr.encode()).hexdigest(),'guard_states':states,'empty_work_removed':removed,'before':before,'after':after})
        checks.append({'name':name,'status':'passed'});save();print('PASS '+name,flush=True)
    except BaseException as error:
        checks.append({'name':name,'status':'failed','error':type(error).__name__});save();raise
completed=True;save();print(json.dumps({'completed':True,'groups':3,'served_installation_unchanged':True}))
