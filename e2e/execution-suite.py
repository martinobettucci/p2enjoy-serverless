# @spec docs/BACKLOG.md#sls-040 | docs/ADMISSION.md
# @verifies docs/BACKLOG.md#sls-040 | docs/ADMISSION.md
# @spec docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md#suite-commune-et-pagination-autonome
# @verifies docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md#suite-commune-et-pagination-autonome
# @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#suite-complète-de-preuve
# @verifies docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#suite-complète-de-preuve
# @spec docs/BACKLOG.md#sls-067 | docs/FUNCTION_CATALOGUE.md#réalisation-et-preuves
# @verifies docs/BACKLOG.md#sls-067 | docs/FUNCTION_CATALOGUE.md#réalisation-et-preuves
"""Serial DEV qualification with fresh reports bound to sources and deployed image."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import termios
import time

ROOT=Path(__file__).resolve().parent.parent
SSH=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202']
REMOTE='/srv/p2enjoy-serverless/'
REPORT=ROOT/'.local/e2e/execution-regressions.json'

def source_hashes():
    files=[p for folder,pattern in [('control/app','*.py'),('control/migrations','*.sql'),('storage','*.py'),('storage/migrations','*.sql'),('runtime','*.mjs'),('adapter','*.py')] for p in (ROOT/folder).glob(pattern)]
    files += [ROOT/p for p in ['control/Dockerfile','control/requirements.txt','control/compose.spark.yml','control/dev.sh','runtime/Dockerfile','runtime/compose.spark.yml','runtime/dev.sh','storage/main.go','storage/go.mod','storage/go.sum','storage/dev.sh','storage/Dockerfile','qualification/artifacts/volume-operations.cjs','qualification/artifacts/public-invocation.cjs','qualification/artifacts/invoke.cjs','web/package.json','web/package-lock.json','web/index.html']]
    files += [ROOT/'qualification/artifacts/observation.cjs']
    # @spec docs/BACKLOG.md#sls-062 | docs/CONSOLE_MANUAL.md#preuves-attendues
    files += [ROOT/name for name in ['docs/manual.md','web/vite.config.mjs','control/Dockerfile.dockerignore']]
    # @spec docs/BACKLOG.md#sls-063 | docs/CONSOLE_PUBLICATION.md#preuves-requises
    files += [p for p in (ROOT/'qualification/artifacts').iterdir() if p.is_file()]
    files += [ROOT/name for name in ['docs/CONSOLE_PUBLICATION.md','docs/DESIGN_SYSTEM_APP.md','qualification/serverless.platform.yml','qualification/src/handlers.cjs','adapter/requirements.txt']]
    files += [p for p in (ROOT/'web/src').glob('*') if p.is_file()]
    files += [p for p in (ROOT/'e2e').iterdir() if p.suffix in ('.py','.mjs')]
    files += [ROOT/name for name in ['e2e/package.json','e2e/package-lock.json','docs/CONSOLE_STORAGE.md','docs/STORAGE_LEGACY_PROOF.md']]
    # @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#suite-complète-de-preuve
    files += [ROOT/name for name in ['docs/INVOCATION_URLS.md','adapter/Dockerfile','adapter/Dockerfile.dockerignore',
                                    'adapter/compose.spark.yml','adapter/dev.sh','qualification/package.json']]
    files += [ROOT/'docs/INVOCATION_DOMAINS_PAGINATION.md']
    # @spec docs/BACKLOG.md#sls-076 | docs/VALIDATOR_NAMES.md#preuves-et-limites
    files += [ROOT/'docs/VALIDATOR_NAMES.md',ROOT/'docs/DEPLOYMENT_NAMES.md']
    files += [ROOT/name for name in ['docs/FUNCTION_CATALOGUE.md','docs/CONSOLE_USABILITY.md','docs/EXECUTION.md','docs/INVOCATION_ROUTE_CYCLES.md','docs/INVOCATION_SOURCE_PERMISSIONS.md']]
    # @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_CODE_HASH.md
    files += [ROOT/name for name in ['function_code_hash.py','docs/FUNCTION_CODE_HASH.md','docs/FUNCTION_VERSIONS.md',
                                    'control/Dockerfile.code-hash','control/Dockerfile.code-hash.dockerignore',
                                    'control/compose.code-hash.spark.yml','control/code-hash-dev.sh']]
    # @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_REGISTRY.md#preuves-réelles-requises
    files += [ROOT/'docs/FUNCTION_VERSION_REGISTRY.md']
    files += [ROOT/'docs/FUNCTION_VERSION_PURGE_UPGRADE.md']
    # @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#preuves-réelles
    files += [ROOT/'docs/FUNCTION_VERSION_EXECUTION.md',ROOT/'docs/SCHEMA.md']
    # @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_VALIDATION_RECOVERY.md#campagne-et-preuves
    files += [ROOT/'docs/FUNCTION_VERSION_VALIDATION_RECOVERY.md']
    # @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_UPLOAD_CAPACITY.md#preuves-et-limites
    files += [ROOT/'docs/FUNCTION_VERSION_UPLOAD_CAPACITY.md']
    # @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_DUPLICATE_RECOVERY.md#preuves-et-limites
    files += [ROOT/'docs/FUNCTION_VERSION_DUPLICATE_RECOVERY.md']
    # @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_MIGRATION_008_RECOVERY.md#résultats-et-régression
    files += [ROOT/'docs/FUNCTION_VERSION_MIGRATION_008_RECOVERY.md']
    # @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PURGE_MIGRATION_008.md#livraison-et-limites
    files += [ROOT/'docs/FUNCTION_VERSION_PURGE_MIGRATION_008.md']
    # @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_UNKNOWN_FIRST.md#livraison-et-limites
    files += [ROOT/'docs/FUNCTION_VERSION_UNKNOWN_FIRST.md']
    # @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_STATE_TRANSPORT.md#livraison-et-limites
    files += [ROOT/'docs/FUNCTION_VERSION_STATE_TRANSPORT.md']
    # @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_PUBLICATION_REGRESSIONS.md#preuves-et-reprise
    files += [ROOT/'docs/FUNCTION_VERSION_PUBLICATION_REGRESSIONS.md']
    # @spec docs/BACKLOG.md#sls-089 | docs/SSO_SESSION_RECOVERY.md#qualification-réelle-et-données-de-test
    files += [ROOT/'docs/SSO_SESSION_RECOVERY.md']
    # @spec docs/BACKLOG.md#sls-070 | docs/CONSOLE_EDITOR.md#interface-et-preuves
    files += [ROOT/'docs/CONSOLE_EDITOR.md']
    files += [ROOT/'docs/CODE_DRAFT_CAPACITY.md']
    files += [ROOT/'docs/CODE_EDITOR_SOURCE_LIMITS.md']
    files += [ROOT/'docs/CODE_EDITOR_CONSOLE_EXTENSIONS.md']
    files += [ROOT/'docs/CODE_EDITOR_READ_CONCURRENCY.md']
    files += [ROOT/'docs/CODE_EDITOR_SOURCE_LIFECYCLE.md']
    files += [ROOT/'docs/CODE_EDITOR_SOURCE_ACCESS.md']
    files += [ROOT/'docs/CODE_EDITOR_ARCHIVE_LIMITS.md']
    # @spec docs/BACKLOG.md#sls-071 | docs/CONSOLE_TESTER.md#réalisation-et-preuves
    files += [ROOT/'docs/CONSOLE_TESTER.md',ROOT/'docs/CONSOLE_TESTER_FAILURES.md',ROOT/'docs/CONSOLE_TESTER_TOKEN_LOSS.md',ROOT/'docs/CONSOLE_TESTER_SOURCE.md',ROOT/'docs/CONSOLE_TESTER_LOADING.md',ROOT/'docs/CONSOLE_TESTER_TASK_EXCEPTION.md']
    # @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_CLI_RECOVERY_REGRESSIONS.md#livraison-et-limites
    files += [ROOT/'docs/FUNCTION_VERSION_CLI_RECOVERY_REGRESSIONS.md']
    # @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_INVOCATION_STORAGE_REGRESSIONS.md#preuves-et-portée-des-opérateurs
    files += [ROOT/'docs/FUNCTION_VERSION_INVOCATION_STORAGE_REGRESSIONS.md']
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}

def metadata(path):
    return {'sampled_at_ns':time.time_ns(),'mtime_ns':path.stat().st_mtime_ns,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()} if path.exists() else {'sampled_at_ns':time.time_ns(),'mtime_ns':None,'sha256':None}

def snapshot(report_path,remote,*,include_adapter=False):
    sources=source_hashes()
    script="""import hashlib,json,subprocess,time
from pathlib import Path
assert Path('/etc/hostname').read_text().strip()=='infra-serverless'
image=subprocess.check_output(['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock','inspect','--format','{{.Image}}','serverless-api'],text=True).strip()
result={'image':image,'source_sha256':{name:hashlib.sha256((Path('/srv/p2enjoy-serverless')/name).read_bytes()).hexdigest() for name in SOURCE_INDEX}}
if INCLUDE_ADAPTER:
 rows=json.loads(subprocess.check_output(['runuser','-u','spark-docker','--','docker','--host','unix:///run/user/1001/docker.sock','image','inspect','p2enjoy-adapter:dev','p2enjoy-adapter-e2e:dev'],text=True))
 result['adapter_images']={name:row['Id'] for name,row in zip(['p2enjoy-adapter:dev','p2enjoy-adapter-e2e:dev'],rows,strict=True)}
path=Path(REPORT_PATH) if REMOTE_REPORT else None
if path:
 result['report']={'sampled_at_ns':time.time_ns(),'mtime_ns':path.stat().st_mtime_ns,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()} if path.exists() else {'sampled_at_ns':time.time_ns(),'mtime_ns':None,'sha256':None}
print(json.dumps(result))
""".replace('REPORT_PATH',repr(REMOTE+report_path)).replace('REMOTE_REPORT',repr(remote)).replace('SOURCE_INDEX',repr(list(sources))).replace('INCLUDE_ADAPTER',repr(include_adapter))
    value=json.loads(subprocess.run(SSH+['root@10.77.0.24','python3 -B -'],input=script,text=True,capture_output=True,check=True).stdout)
    if not remote:value['report']=metadata(ROOT/report_path)
    assert value['source_sha256']==sources,'Sources distantes différentes du poste'
    return value

def remote(command,user='spark-docker'):
    return SSH+[user+'@10.77.0.24',shlex.join(command)]

CASES=[
 ('control-operations',remote(['python3','-B',REMOTE+'e2e/control-operations.py']),'control/.proof-control-operations.json',True),
 ('function-storage',['node','e2e/function-storage.mjs'],'.local/e2e/function-storage.json',False),
 ('runtime-instances',remote(['bash',REMOTE+'runtime/dev.sh','instances-test']),'runtime/instances-proof.json',True),
 ('instance-lifecycle',remote(['bash',REMOTE+'runtime/dev.sh','lifecycle-test']),'runtime/lifecycle-proof.json',True),
 ('runtime-validation',remote(['bash',REMOTE+'runtime/dev.sh','test']),'runtime/validation-proof.json',True),
 ('managed-storage',remote(['python3','-B',REMOTE+'e2e/managed-storage.py'],'root'),'runtime/managed-storage-proof.json',True),
 ('control-admin',['node','e2e/control-admin.mjs'],'.local/e2e/control-admin.json',False),
 ('control-ui',['node','e2e/control-ui.mjs'],'.local/e2e/control-ui.json',False),
 ('deployments',['node','e2e/deployments.mjs'],'.local/e2e/deployments.json',False),
 ('code-publications',['node','e2e/code-publications.mjs'],'.local/e2e/code-publications.json',False),
 ('adapter-deploy',['node','e2e/adapter-deploy.mjs'],'.local/e2e/adapter-deploy.json',False),
 ('publication-recovery',['node','e2e/publication-recovery.mjs'],'.local/e2e/publication-recovery.json',False),
 ('public',['python3','-B','e2e/public.py'],'.local/e2e/public.json',False),
 ('public-invocations',['python3','-B','e2e/public-invocations-suite.py'],'.local/e2e/public-invocations.json',False),
]

def read_report(path,is_remote,expected_hash):
    if is_remote:
        script='from pathlib import Path;import sys;sys.stdout.buffer.write(Path('+repr(REMOTE+path)+').read_bytes())'
        contents=subprocess.check_output(remote(['python3','-B','-c',script],'root'))
    else:contents=(ROOT/path).read_bytes()
    assert hashlib.sha256(contents).hexdigest()==expected_hash,'Rapport changé après le relevé'
    return json.loads(contents)

def verify_report(name,path,is_remote,expected_hash):
    result=read_report(path,is_remote,expected_hash)
    assert result['completed'] is True and result['skipped']==0,'Campagne incomplète ou ignorée'
    expected={'control-operations':55,'function-storage':15,'runtime-instances':31,'instance-lifecycle':11,
              'runtime-validation':36,'managed-storage':14,'control-admin':19,'control-ui':11,
              'deployments':11,'adapter-deploy':7,'publication-recovery':4,'public':8,
              'public-invocations':31,'login-ui':9,'execution-ui':12,'manual-ui':8,
              'code-publications':10,'publication-ui':21}
    # @spec docs/BACKLOG.md#sls-064 | docs/STORAGE_DISCARD.md#qualification-réelle
    expected.update({'storage-discard':12,'storage-agent':15,'storage-limits':8,'storage-preparations':12})
    expected.update({'storage-console-api':9,'storage-console-ui':10,'storage-command-recovery':7,
                     'storage-validation-recovery':2,'storage-decision-recovery':4,
                     'storage-legacy-partial':1,'storage-legacy-recovery':4})
    # @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_URLS.md#suite-complète-de-preuve
    expected.update({'invocation-urls':8,'invocation-urls-ui':6,'service-transport':5,'service-configuration':13,
                     'adapter-docker':24,'adapter-public-docker':14})
    expected.update({'function-catalogue-api':8,'function-catalogue-ui':14})
    # @spec docs/BACKLOG.md#sls-066 | docs/INVOCATION_ROUTE_CYCLES.md#cinq-groupes-e2e-sérialisés
    expected.update({'invocation-route-cycles':5,'invocation-request-pause':2,'invocation-empty-ui':3,'invocation-alias-entry':3})
    expected.update({'invocation-source-guard':3,'invocation-source-api':4,'invocation-source-ui':3})
    expected.update({'function-code-hash':7})
    checks=result.get('checks',result.get('results'))
    assert isinstance(checks,list) and len(checks)==expected[name],'Nombre de groupes inattendu'
    if name=='login-ui':assert all(isinstance(row,str) and row for row in checks)
    else:assert all(row['status']=='passed' for row in checks),'Groupe échoué'
    assert not result.get('failed') and not result.get('failures') and not result.get('cleanupErrors') and not result.get('cleanup_errors')
    if name not in ('runtime-validation','public','login-ui','control-ui','control-admin','manual-ui','adapter-docker','adapter-public-docker'):
        assert result['cleanup'] is True,'Nettoyage incomplet'
    if name in ('control-ui','execution-ui'):assert result['faults']==[] and result['cleanupErrors']==[]
    if name=='manual-ui':assert result['faults']==[]
    if name=='publication-ui':assert result['faults']==[]
    if name=='storage-console-ui':assert result['faults']==[]
    if name=='invocation-urls-ui':assert result['faults']==[]
    if name=='function-catalogue-ui':assert result['faults']==[]
    return len(checks)


# @spec docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md#suite-commune-et-pagination-autonome
# @verifies docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md#suite-commune-et-pagination-autonome
def private_credentials():
    """A single private line; its contents never enter command/report metadata."""
    attributes=None
    try:
        if sys.stdin.isatty():
            attributes=termios.tcgetattr(sys.stdin.fileno())
            hidden=attributes.copy();hidden[3]&=~termios.ECHO
            termios.tcsetattr(sys.stdin.fileno(),termios.TCSANOW,hidden)
        print('Identifiants SSO attendus sur stdin privée (JSON username/password).',flush=True)
        line=sys.stdin.readline(8194)
        value=json.loads(line)
        assert len(line)<=8192 and isinstance(value,dict)
        assert all(isinstance(value.get(key),str) and 0<len(value[key])<=2048 for key in ('username','password'))
        return (json.dumps({key:value[key] for key in ('username','password')})+'\n').encode()
    except (ValueError,AssertionError):raise SystemExit('invalid_private_sso_input') from None
    finally:
        if attributes is not None:termios.tcsetattr(sys.stdin.fileno(),termios.TCSANOW,attributes)

def main():
    # @verifies docs/BACKLOG.md#sls-061 | docs/CONSOLE_EXECUTION.md#preuves-attendues
    # @spec docs/BACKLOG.md#sls-063 | docs/CONSOLE_PUBLICATION.md#preuves-requises
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scope',choices=('engine','console','publication','storage','storage-console-focused','storage-console','invocation-urls','function-catalogue','public-invocations'),default='engine')
    scope=parser.parse_args().scope
    report={'engine':REPORT,'console':ROOT/'.local/e2e/console-execution-regressions.json','publication':ROOT/'.local/e2e/publication-regressions.json',
            'storage':ROOT/'.local/e2e/storage-discard-regressions.json',
            'storage-console-focused':ROOT/'.local/e2e/storage-console-focused.json',
            'storage-console':ROOT/'.local/e2e/storage-console-regressions.json',
            'invocation-urls':ROOT/'.local/e2e/invocation-urls-regressions.json',
            'function-catalogue':ROOT/'.local/e2e/function-catalogue-regressions.json',
            'public-invocations':ROOT/'.local/e2e/public-invocations-regressions.json'}[scope]
    extended=scope in ('invocation-urls','function-catalogue')
    console_cases=[
        next(row for row in CASES if row[0]=='public'),
        ('login-ui',['node','e2e/login-ui.mjs'],'.local/e2e/login-ui.json',False),
        next(row for row in CASES if row[0]=='control-ui'),
        ('execution-ui',['node','e2e/execution-ui.mjs'],'.local/e2e/execution-ui.json',False),
        ('publication-ui',['node','e2e/publication-ui.mjs'],'.local/e2e/publication-ui.json',False),
        ('manual-ui',['node','e2e/manual-ui.mjs'],'.local/e2e/manual-ui.json',False),
    ]
    cases=CASES if scope=='engine' else console_cases
    if scope=='public-invocations':cases=[next(row for row in CASES if row[0]=='public-invocations')]
    if scope=='publication':
        cases=CASES+[row for row in console_cases if row[0] not in {case[0] for case in CASES}]
    # @spec docs/BACKLOG.md#sls-064 | docs/STORAGE_DISCARD.md#qualification-réelle
    # @verifies docs/BACKLOG.md#sls-064 | docs/STORAGE_DISCARD.md#qualification-réelle
    storage_cases=[
            ('storage-discard',remote(['python3','-B',REMOTE+'e2e/storage-discard.py'],'root'),'storage/discard-proof.json',True),
            ('storage-agent',remote(['bash',REMOTE+'storage/dev.sh','agent-test'],'root'),'storage/agent-proof.json',True),
            ('storage-limits',remote(['bash',REMOTE+'storage/dev.sh','limits-test'],'root'),'storage/agent-limits-proof.json',True),
            ('storage-preparations',remote(['python3','-B',REMOTE+'e2e/storage-preparations.py'],'root'),'storage/preparations-proof.json',True),
            *[next(row for row in CASES if row[0]==name) for name in ('managed-storage','function-storage','public-invocations')],
        ]
    if scope=='storage':cases=storage_cases
    storage_console=scope in ('storage-console-focused','storage-console','invocation-urls','function-catalogue')
    if storage_console:
        focused=[
            (name,['node','e2e/'+name+'.mjs'],'.local/e2e/'+name+'.json',False)
            for name in ('storage-console-api','storage-console-ui','storage-command-recovery','storage-validation-recovery','storage-decision-recovery')
        ]+[
            ('storage-legacy-partial',['node','e2e/storage-legacy-recovery.mjs','--partial'],'.local/e2e/storage-legacy-partial.json',False),
            ('storage-legacy-recovery',['node','e2e/storage-legacy-recovery.mjs','--full'],'.local/e2e/storage-legacy-recovery.json',False),
        ]
        if scope=='storage-console-focused':cases=focused
        else:
            extra=[]
            if extended:
                extra=[(name,['node','e2e/'+name+'.mjs'],'.local/e2e/'+name+'.json',False)
                       for name in ('service-transport','service-configuration','invocation-urls','invocation-urls-ui')]
                extra += [(name,remote(['bash',REMOTE+'adapter/dev.sh',action]),'adapter/reports/'+filename,True)
                          for name,action,filename in [('adapter-docker','test','adapter.json'),
                                                       ('adapter-public-docker','deploy-public-test','adapter-deploy-public.json')]]
                if scope=='function-catalogue':
                    extra += [(name,['node','e2e/'+name+'.mjs'],'.local/e2e/'+name+'.json',False)
                              for name in ('function-catalogue-api','function-catalogue-ui')]
            union=CASES+console_cases+extra+storage_cases+focused
            cases=list({row[0]:row for row in union}.values())
            if extended:assert len(cases)==(37 if scope=='function-catalogue' else 35)
    records=[];prerequisites=[];baseline=None;adapter_baseline=None
    def save(done=False):
        temporary=report.with_suffix('.tmp')
        temporary.write_text(json.dumps({'completed':done,'serial':True,'scope':scope,'prerequisites':prerequisites,'commands':records},ensure_ascii=False,indent=2)+'\n')
        temporary.replace(report)
    report.parent.mkdir(parents=True,exist_ok=True,mode=0o700);save()
    def execute(name,command,path,is_remote,*,count=True,private_input=None):
        nonlocal baseline,adapter_baseline
        include_adapter=adapter_baseline is not None
        before=snapshot(path,is_remote,include_adapter=include_adapter)
        if baseline is None:baseline={k:before[k] for k in ('image','source_sha256')}
        assert all(before[k]==v for k,v in baseline.items()),'Image ou sources changées avant campagne'
        if include_adapter:assert before['adapter_images']==adapter_baseline,'Images CLI changées avant campagne'
        record={'campaign':name,'command':command,'report_path':path,'report_remote':is_remote,'before':before,'exit_code':None}
        (records if count else prerequisites).append(record);save();print(json.dumps({'campaign' if count else 'prerequisite':name,'state':'running'}),flush=True)
        started=time.monotonic()
        options={'input':private_input} if private_input is not None else {'stdin':subprocess.DEVNULL}
        result=subprocess.run(command,cwd=ROOT,**options)
        record.update(exit_code=result.returncode,duration_seconds=round(time.monotonic()-started,2));save()
        if result.returncode:raise SystemExit(result.returncode)
        after=snapshot(path,is_remote,include_adapter=include_adapter);record['after']=after;save()
        assert all(after[k]==v for k,v in baseline.items()),'Image ou sources changées pendant campagne'
        if include_adapter:assert after['adapter_images']==adapter_baseline,'Images CLI changées pendant campagne'
        assert before['report']['sampled_at_ns']<=after['report']['mtime_ns']<=after['report']['sampled_at_ns'],'Rapport non régénéré par la campagne'
        if count:record['passed_groups']=verify_report(name,path,is_remote,after['report']['sha256'])
        else:
            value=read_report(path,is_remote,after['report']['sha256']);assert value['completed'] is True,'Prérequis incomplet'
            if name in ('dev-sso-sessions','dev-sso-decision-sessions','dev-sso-invocation-sessions'):
                assert value['authenticated'] and value['independent_sessions']==2 and value['platform_cookies_only']
                assert value['purpose']=={'dev-sso-sessions':'suite-start','dev-sso-decision-sessions':'storage-decisions',
                                          'dev-sso-invocation-sessions':'invocation-urls'}[name]
            elif name=='storage-legacy-build':assert value['current_image']==baseline['image'] and value['current_tag_unchanged']
            elif name=='invocation-url-adapter-build':
                assert value['remote_state']=='completed' and value['current_image']==baseline['image'] and value['current_tag_unchanged']
                assert set(value['images'])=={'p2enjoy-adapter:dev','p2enjoy-adapter-e2e:dev'}
                expected={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'adapter').glob('*.py')}
                assert all(row['embedded_sources']==expected for row in value['images'].values())
                adapter_baseline={name:row['image'] for name,row in value['images'].items()}
            elif name=='storage-console-physical':
                counts=(10,32) if extended else (6,24)
                assert value['physical']['completed'] and (value['campaign_count'],value['function_count'])==counts
                if scope=='function-catalogue':
                    assert value['total_namespaces']==23 and value['total_functions']==91
                    assert set(value['catalogue'])=={'function-catalogue-api','function-catalogue-ui'}
                    assert all(v['physical']['completed'] and v['services_cleared'] for v in value['catalogue'].values())
            else:raise AssertionError('Prérequis inconnu')
        record['fresh_report_verified']=True;record['report_content_verified']=True;save()
    # @spec docs/BACKLOG.md#sls-099 | docs/INSTANCE_LIMIT_RESTORATION.md#intégration-et-portée-des-preuves
    credentials=private_credentials() if storage_console or any(row[0]=='public-invocations' for row in cases) else None
    if not storage_console and credentials is not None:
        execute('dev-sso-sessions',['node','e2e/dev-sso-sessions.mjs'],'.local/e2e/dev-sso-sessions.json',False,count=False,private_input=credentials)
    if storage_console:
        execute('dev-sso-sessions',['node','e2e/dev-sso-sessions.mjs'],'.local/e2e/dev-sso-sessions.json',False,count=False,private_input=credentials)
        execute('storage-legacy-build',['python3','-B','e2e/storage-legacy-build.py'],'.local/e2e/storage-legacy-build.json',False,count=False)
        if extended:
            execute('invocation-url-adapter-build',['python3','-B','e2e/invocation-url-adapter-build.py'],
                    '.local/e2e/invocation-url-adapter-build.json',False,count=False)
    for name,command,path,is_remote in cases:
        if extended and name=='service-transport':
            execute('dev-sso-invocation-sessions',['node','e2e/dev-sso-sessions.mjs','--for-invocation-urls'],
                    '.local/e2e/dev-sso-invocation-sessions.json',False,count=False,private_input=credentials)
        if storage_console and name=='storage-decision-recovery':
            execute('dev-sso-decision-sessions',['node','e2e/dev-sso-sessions.mjs','--for-storage-decisions'],
                    '.local/e2e/dev-sso-decision-sessions.json',False,count=False,private_input=credentials)
        execute(name,command,path,is_remote,private_input=credentials if name in ('storage-legacy-recovery','public-invocations') else None)
    credentials=None
    if storage_console:
        execute('storage-console-physical',['python3','-B','e2e/storage-suite-inspect.py',str(report.relative_to(ROOT))],
                '.local/e2e/function-catalogue-physical.json' if scope=='function-catalogue' else '.local/e2e/invocation-urls-physical.json' if extended else '.local/e2e/storage-console-physical.json',False,count=False)
    if scope=='invocation-urls':assert len(records)==35 and sum(row['passed_groups'] for row in records)==467 and len(prerequisites)==6
    if scope=='function-catalogue':assert len(records)==37 and sum(row['passed_groups'] for row in records)==489 and len(prerequisites)==6
    save(True)

if __name__=='__main__':main()
