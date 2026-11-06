// @spec docs/BACKLOG.md#sls-040 | docs/EXECUTION.md#réalisation-et-preuves
// Original handlers exercised through the production instance protocol.
const fs=require('node:fs');
const {spawn}=require('node:child_process');
const {createHash}=require('node:crypto');
const http=require('node:http');
let calls=0;
const reply=value=>({statusCode:200,body:JSON.stringify(value)});
exports.handler=async(event,context,callback)=>{
  switch(event.operation) {
    case 'echo':return reply({event,context:{...context,remaining:context.getRemainingTimeInMillis()},
      pid:process.pid,calls:++calls,environment:Object.keys(process.env).sort(),
      label:process.env.QUALIFICATION_PUBLIC_LABEL,secret_present:!!process.env.QUALIFICATION_SYNTHETIC_SECRET});
    case 'digest':return reply({bytes:Buffer.byteLength(event.body),sha256:createHash('sha256').update(event.body).digest('hex')});
    case 'callback':callback(null,reply('callback'));return reply('promise');
    case 'double':callback(null,reply('first'));callback(null,reply('second'));return reply('third');
    case 'promise':setTimeout(()=>callback(null,reply('late')),50);return reply('promise');
    case 'throw':throw new Error(process.env.QUALIFICATION_SYNTHETIC_SECRET);
    case 'reject':return Promise.reject(new Error(process.env.QUALIFICATION_SYNTHETIC_SECRET));
    case 'exit':process.exit(0);break;
    case 'invalid':return event.value;
    case 'body':return {statusCode:201,body:event.character.repeat(event.size)};
    case 'late':{const body='x'.repeat(6*1024*1024);fs.writeFileSync('/tmp/late-started','started');
      await new Promise(r=>setTimeout(r,1000));return {statusCode:200,body};}
    case 'binary':return {statusCode:200,body:Buffer.from([0,255,10,128]).toString('base64'),isBase64Encoded:true};
    case 'headers':return {statusCode:202,body:'headers',headers:{'X-One':'old','X-End':'end',Connection:'X-Preserve','X-Preserve':'kept',
      'X-Private':'private','Content-Length':'999','Access-Control-Allow-Origin':'*','X-Serverless-Request-Id':'forged'},
      multiValueHeaders:{'x-one':['new','second'],Connection:['X-Transient, x-private'],'X-Transient':['transient']}};
    case 'logs':
      fs.writeSync(1,process.env.QUALIFICATION_SYNTHETIC_SECRET+'\n');fs.writeSync(2,'stderr\n');return reply('logged');
    case 'many-logs':fs.writeSync(1,process.env.QUALIFICATION_SYNTHETIC_SECRET+'\n'+'x'.repeat(100000));return reply('logged');
    case 'binary-logs':fs.writeSync(2,Buffer.alloc(100000,255));return reply('logged');
    case 'spin':fs.writeFileSync('/tmp/started','started');while(true){};
    case 'sleep':fs.writeFileSync('/tmp/sleep-started','started');await new Promise(resolve=>setTimeout(resolve,event.ms));return reply('slept');
    case 'memory':{const buffers=[];while(true){buffers.push(Buffer.alloc(16*1024*1024,255));}}
    case 'descendant':{
      const code="const f=require('node:fs');f.writeFileSync('/tmp/descendant-ready','ready');setInterval(()=>f.appendFileSync('/tmp/descendant-ticks','x'),20)";
      const child=spawn(process.execPath,['-e',code],{detached:true,stdio:'ignore',env:{}});child.unref();
      const deadline=Date.now()+3000;
      while(!fs.existsSync('/tmp/descendant-ticks')) {if(Date.now()>deadline)throw new Error('descendant_start');await new Promise(r=>setTimeout(r,10));}
      if(event.hang) {setInterval(()=>{},1000);await new Promise(()=>{});}
      return reply({pid:child.pid});
    }
    case 'pids':{
      let created=0;
      for(let i=0;i<100;i++) {
        const outcome=await new Promise(resolve=>{const child=spawn('/bin/sleep',['30'],{stdio:'ignore',env:{}});
          child.once('spawn',()=>resolve('spawn'));child.once('error',error=>resolve(error.code));});
        if(outcome==='EAGAIN')return reply({created,limit:true});
        if(outcome!=='spawn')throw new Error('spawn_failed');created++;
      }
      return reply({created,limit:false});
    }
    case 'egress':{const response=await fetch(process.env.QUALIFICATION_TARGET_URL+'/healthz',{signal:AbortSignal.timeout(5000)});
      return reply({status:response.status,body:await response.json()});}
    case 'confinement':{
      const writes={};for(const path of ['/code/prohibited','/runtime/prohibited','/protocol/prohibited']) {
        try {fs.writeFileSync(path,'prohibited');writes[path]='written';}catch(error){writes[path]=error.code;}
      }
      fs.writeFileSync('/tmp/writable','yes');
      return reply({writes,docker:fs.existsSync('/docker.sock'),tmp:fs.readFileSync('/tmp/writable','utf8'),
        secret_present:!!process.env.QUALIFICATION_SYNTHETIC_SECRET,
        platform_environment:Object.keys(process.env).filter(k=>k.startsWith('OIDC_')||k.startsWith('SERVERLESS_'))});
    }
    case 'private':{
      const statuses=[];
      for(const [method,path] of [['POST','/bootstrap'],['GET','/next'],['POST','/result'],['POST','/started']]) {
        statuses.push(await new Promise((resolve,reject)=>{const req=http.request({socketPath:'/protocol/control.sock',method,path,
          headers:{'Content-Type':'application/json','Content-Length':'2','Connection':'close'}},res=>{res.resume();res.once('end',()=>resolve(res.statusCode));});
          req.on('error',reject);req.end('{}');}));
      }
      return reply({statuses});
    }
    default:throw new Error('unknown_operation');
  }
};
exports.sync=()=>reply('sync');
exports.callback=(event,context,done)=>{setTimeout(()=>done(null,reply('async-callback')),20);};
