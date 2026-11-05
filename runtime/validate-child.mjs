// @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
import {loadHandler,LoadError} from './loader.mjs';

const send=process.send.bind(process);
process.once('message',async ({handler,environment})=>{
  // Business NODE_OPTIONS/LD_PRELOAD must not affect the supervisor or bootstrap.
  for (const key of Object.keys(process.env)) delete process.env[key];
  for (const [key,value] of Object.entries(environment)) process.env[key]=value;
  try {
    const {module}=await loadHandler('/code',handler);
    send({type:'loaded',module},()=>process.exit(0));
  } catch(error) {
    send({type:'failed',code:error instanceof LoadError?error.code:'import_failed'},()=>process.exit(1));
  }
});
