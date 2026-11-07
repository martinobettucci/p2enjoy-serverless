// @spec docs/BACKLOG.md#sls-065 | docs/CONSOLE_STORAGE.md#preuves-attendues
// Original HTTP application for data/cache persistence through the actual runtime.
const fs=require('node:fs/promises');
async function read(path) {try{return await fs.readFile(path,'utf8');}catch(error){if(error.code==='ENOENT')return null;throw error;}}
exports.handler=async(event,context)=>{
  const input=event.body?JSON.parse(event.body):{};
  if(event.httpMethod==='POST') {
    if(typeof input.data==='string')await fs.writeFile('/data/record',input.data);
    if(typeof input.cache==='string')await fs.writeFile('/cache/record',input.cache);
  }
  if(input.delay_ms)await new Promise(resolve=>setTimeout(resolve,Math.min(5000,input.delay_ms)));
  return {statusCode:200,headers:{'Content-Type':'application/json'},body:JSON.stringify({
    data:await read('/data/record'),cache:await read('/cache/record'),revision:context.functionVersion,
  })};
};
