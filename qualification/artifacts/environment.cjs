// @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
// @verifies docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
const {readFileSync,existsSync,writeFileSync}=require('node:fs');
const {networkInterfaces}=require('node:os');
if (!process.env.QUALIFICATION_PUBLIC_LABEL || !process.env.QUALIFICATION_SYNTHETIC_SECRET) throw new Error('Missing cell input');
if (Object.keys(process.env).some(key=>/^(OIDC_|SERVERLESS_MASTER_KEY$)/.test(key))) throw new Error('Control configuration leaked');
if (Object.keys(networkInterfaces()).some(key=>key!=='lo')) throw new Error('Network accessible');
if (existsSync('/state') || existsSync('/run/spark') || existsSync('/var/run/docker.sock')) throw new Error('Control mount leaked');
for (const file of ['/code/write-denied','/runtime/write-denied','/protocol/write-denied']) {
  let denied=false;
  try {writeFileSync(file,'must fail');} catch(error) {denied=['EROFS','EACCES'].includes(error.code);}
  if (!denied) throw new Error('Writable immutable code');
}
const status=readFileSync('/proc/self/status','utf8');
if (!/^CapEff:\s+0000000000000000$/m.test(status) || !/^NoNewPrivs:\s+1$/m.test(status)) throw new Error('Capabilities policy absent');
if (readFileSync('/sys/fs/cgroup/memory.max','utf8').trim()!=='536870912') throw new Error('Memory limit absent');
if (readFileSync('/sys/fs/cgroup/pids.max','utf8').trim()!=='64') throw new Error('PID limit absent');
const [quota,period]=readFileSync('/sys/fs/cgroup/cpu.max','utf8').trim().split(' ').map(Number);
if (quota/period!==.25) throw new Error('CPU limit absent');
exports.handler=()=>({statusCode:200,body:'confinement checked'});
