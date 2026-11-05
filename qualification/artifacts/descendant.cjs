// @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
// @verifies docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
const {spawn}=require('node:child_process');
spawn(process.execPath,['-e','setInterval(()=>{},1000)'],{detached:true,stdio:'ignore'}).unref();
while (true) {}
