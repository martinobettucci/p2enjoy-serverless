// @spec docs/BACKLOG.md#sls-040 | docs/EXECUTION.md#canal-privé-et-terminaison
import {loadHandler,LoadError} from './loader.mjs';
import {response} from './invoke-response.mjs';

const send=process.send.bind(process),exit=process.exit.bind(process),clock=process.hrtime.bigint.bind(process.hrtime);
process.once('message',async ({handler,environment,event,context,deadline_ns})=>{
  for (const key of Object.keys(process.env)) delete process.env[key];
  for (const [key,value] of Object.entries(environment)) process.env[key]=value;
  const deadline=BigInt(deadline_ns);
  const invocationContext={...context,getRemainingTimeInMillis:()=>Math.max(0,Number((deadline-clock())/1000000n))};
  let completed=false;
  const finish=(error,result)=>{
    if (completed) return;
    completed=true;
    let message;
    try {message=error?{type:'failed',error:'handler_error'}:{type:'completed',response:response(result)};}
    catch {message={type:'failed',error:'invalid_handler_response'};}
    try {send(message,()=>exit(0));} catch {exit(1);}
  };
  let fn;
  try {({fn}=await loadHandler('/code',handler));}
  catch(error) {
    send({type:'failed',error:error instanceof LoadError?error.code:'import_failed'},()=>exit(1));return;
  }
  send({type:'started'},()=>{
    try {
      const returned=fn(event,invocationContext,finish);
      if (returned && typeof returned.then==='function') Promise.resolve(returned).then(value=>finish(null,value),finish);
      else if (returned!==undefined) finish(null,returned);
    } catch(error) {finish(error);}
  });
});
