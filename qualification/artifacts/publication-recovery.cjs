// @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_CLI_RECOVERY_REGRESSIONS.md#plafonds-et-identité-du-code
// @verifies docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_CLI_RECOVERY_REGRESSIONS.md#coupures-physiques-gardées
'use strict';
const {createHash}=require('node:crypto');
const marker=require('./publication-marker.json');
if(!Number.isInteger(marker.validation_delay_ms)||marker.validation_delay_ms<0||marker.validation_delay_ms>8000)throw new Error('invalid_import_delay');
if(marker.validation_delay_ms)Atomics.wait(new Int32Array(new SharedArrayBuffer(4)),0,0,marker.validation_delay_ms);
exports.handler=async(event,context)=>({statusCode:200,headers:{'content-type':'application/json'},body:JSON.stringify({marker:marker.value,request_id:context.awsRequestId,label:process.env.REVISION_LABEL,secret_sha256:createHash('sha256').update(process.env.PUBLICATION_RECOVERY_SECRET||'').digest('hex')})});
