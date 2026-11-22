// @spec docs/BACKLOG.md#sls-072 | docs/EXECUTION_LOGS.md#découpage-et-qualification-réels
// Real Docker handlers emitting bounded journal samples and durable counters.
const fs = require('node:fs');
const metadata = require('./execution-journal-marker.json');
const counterFile = '/data/journal-invocation-count.txt';
const receiptFile = '/data/journal-invocation-receipt.json';
const pendingReceiptFile = '/data/journal-invocation-receipt.pending.json';
const sleep = ms => new Promise(resolve => setTimeout(resolve,ms));

function integer(value,minimum,maximum) {
  if (!Number.isInteger(value) || value < minimum || value > maximum) throw new RangeError('Invalid journal sample bound');
  return value;
}

function write(text,descriptor=1) {
  const bytes = Buffer.from(text,'utf8');
  let offset = 0;
  while (offset < bytes.length) offset += fs.writeSync(descriptor,bytes,offset,bytes.length-offset);
}

function count() {
  try {
    const value = fs.readFileSync(counterFile,'utf8');
    if (!/^[0-9]{1,8}\n$/.test(value)) throw new Error('Invalid persistent journal counter');
    return Number(value.trim());
  } catch (error) {
    if (error.code === 'ENOENT') return 0;
    throw error;
  }
}

exports.handler = async (event,context) => {
  const input = JSON.parse(event.body ? event.isBase64Encoded ? Buffer.from(event.body,'base64').toString('utf8') : event.body : '{}');
  const mode = input.mode || 'silent';
  let counter;
  if (mode === 'text') {
    write('Première ligne — été 😀\n<script>globalThis.journalInjected = true</script>\n');
    write('Ligne stderr sans niveau déclaré\n',2);
  } else if (mode === 'json') {
    write('{"level":"info","message":"JSON réel — été 😀","large_integer":9007199254740993,"decimal":1.2300,"exponent":1e+30,"escaped":"\\u00e9"}\n');
  } else if (mode === 'levels') {
    for (const level of ['trace','debug','info','warn','warning','error','fatal']) write(JSON.stringify({level,message:'niveau explicite '+level})+'\n');
    write('{"severity":"error","message":"severity explicite"}\n');
    write('{"level":12,"message":"niveau numérique inconnu"}\n');
    write('{"level":"INFO","message":"niveau inconnu"}\n');
    write('{"level":"info","severity":"error","message":"niveaux contradictoires"}\n');
    write('{"level":"info","level":"info","message":"clé dupliquée"}\n');
    write('{"message":"aucun niveau"}\n');
    write('{"level":"info","nested":'+ '['.repeat(18)+'0'+']'.repeat(18)+'}\n');
    write('stderr ne décide pas la gravité\n',2);
  } else if (mode === 'secrets') {
    if (!process.env.JOURNAL_SERVICE_SECRET || !process.env.JOURNAL_FUNCTION_SECRET) throw new Error('Journal secret witnesses are required');
    write('service='+process.env.JOURNAL_SERVICE_SECRET+'\n');
    write('fonction='+process.env.JOURNAL_FUNCTION_SECRET+'\n',2);
  } else if (mode === 'line') {
    if (typeof input.text !== 'string' || Buffer.byteLength(input.text,'utf8') > 131072) throw new RangeError('Invalid journal text bound');
    write(input.text+'\n');
  } else if (mode === 'bytes') {
    write('a'.repeat(integer(input.bytes,0,131072)));
  } else if (mode === 'lines') {
    for (let index=1,total=integer(input.count,0,2048);index<=total;index++) write('ligne-'+String(index).padStart(4,'0')+'\n');
  } else if (mode === 'batch') {
    if (!Array.isArray(input.lengths) || input.lengths.length > 1024) throw new RangeError('Invalid journal batch bound');
    const lengths=input.lengths.map(value=>integer(value,0,4096));
    if (lengths.reduce((sum,value)=>sum+value+1,0)>131072) throw new RangeError('Invalid journal batch size');
    for (const length of lengths) write('a'.repeat(length)+'\n');
  } else if (mode === 'error') {
    write('journal-before-handler-error\n',2);
    throw new Error('Intentional journal handler failure');
  } else if (mode === 'exit') {
    write('journal-before-handler-exit\n');
    process.exit(42);
  } else if (mode === 'delay') {
    write('journal-delay-started\n');
    await sleep(integer(input.milliseconds,1,20000));
    write('journal-delay-completed\n');
  } else if (mode === 'counter') {
    counter=integer(count()+1,1,99999999);
    const fd=fs.openSync(counterFile,'w',0o600);
    try {fs.writeFileSync(fd,String(counter)+'\n');fs.fsyncSync(fd);} finally {fs.closeSync(fd);}
    const receipt=fs.openSync(pendingReceiptFile,'wx',0o600);
    try {
      fs.writeFileSync(receipt,JSON.stringify({request_id:context.awsRequestId,counter})+'\n');fs.fsyncSync(receipt);
    } finally {fs.closeSync(receipt);}
    fs.renameSync(pendingReceiptFile,receiptFile);
    write('journal-counter-fsynced\n');
    await sleep(integer(input.milliseconds,1,20000));
  } else if (mode === 'counter_read') {
    counter=count();
  } else if (mode !== 'silent' && mode !== 'status') {
    throw new Error('Unknown journal sample mode');
  }
  const status=mode==='status' ? integer(input.status,200,599) : 200;
  return {statusCode:status,headers:{'Content-Type':'application/json'},body:JSON.stringify({
    marker:metadata.value,mode,request_id:context.awsRequestId,function_name:context.functionName,
    revision_id:context.functionVersion,counter,
  })};
};
