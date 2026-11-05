# @spec docs/BACKLOG.md#sls-020 | docs/CONTROL.md#preuves
# @verifies docs/BACKLOG.md#sls-020 | docs/CONTROL.md#preuves
# Kill a real public campaign after its first HTTP exchange, then run it again.
import json
from pathlib import Path
import subprocess
import sys

report=Path('.local/e2e/public.json')
proof=Path('.local/e2e/report-interruption.json')
proof.write_text('{"completed":false,"error":"Campagne non terminée"}\n')
assert json.loads(report.read_text())['completed'] is True,'Une campagne publique complète doit précéder cette preuve.'
process=subprocess.Popen([sys.executable,'-u','e2e/public.py'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
try:
    assert process.stdout.readline().startswith('PASS TLS, santé')
    assert process.poll() is None
    process.kill();process.communicate(timeout=10)
    assert process.returncode==-9
    interrupted=json.loads(report.read_text())
    assert interrupted['completed'] is False and interrupted['error']=='Campagne non terminée'
    Path('.local/e2e/public-interrupted.json').write_text(json.dumps(interrupted)+'\n')
finally:
    if process.poll() is None:process.kill();process.communicate(timeout=10)
subprocess.run([sys.executable,'e2e/public.py'],check=True)
assert json.loads(report.read_text())['completed'] is True
proof.write_text(json.dumps({'completed':True,'checks':[
    {'name':'SIGKILL du vrai client après échange HTTP invalide le précédent rapport','status':'passed'},
    {'name':'Une nouvelle campagne réelle complète restaure un rapport réussi','status':'passed'}], 'skipped':0},indent=2,ensure_ascii=False)+'\n')
print('PASS Interruption réelle du pilote et reprise des preuves')
