// @spec docs/BACKLOG.md#sls-040 | docs/EXECUTION.md#événement-réponse-et-journaux
const bodyLimit=6*1024*1024,headerLimit=32*1024;
const namePattern=/^[!#$%&'*+.^_`|~0-9A-Za-z-]+$/;
const withheld=new Set(['connection','keep-alive','proxy-authenticate','proxy-authorization','te','trailer',
  'transfer-encoding','upgrade','content-length','host','x-serverless-request-id']);

export function response(value) {
  if (!value || typeof value!=='object' || Array.isArray(value) ||
      !Number.isInteger(value.statusCode) || value.statusCode<200 || value.statusCode>599 ||
      typeof value.body!=='string' || (value.isBase64Encoded!==undefined && typeof value.isBase64Encoded!=='boolean'))
    throw new Error('invalid_response');
  const binary=value.isBase64Encoded===true;
  if (Buffer.byteLength(value.body)>bodyLimit*(binary?4/3:1)) throw new Error('response_too_large');
  if (binary) {
    if (Buffer.from(value.body,'base64').toString('base64')!==value.body) throw new Error('invalid_base64');
  } else if (Buffer.from(value.body).toString('utf8')!==value.body) throw new Error('invalid_utf8');
  const headers=new Map();let bytes=0,count=0;
  for (const [mapping,multiple] of [[value.headers,false],[value.multiValueHeaders,true]]) {
    if (mapping===undefined || mapping===null) continue;
    if (typeof mapping!=='object' || Array.isArray(mapping)) throw new Error('invalid_headers');
    const seen=new Set();
    for (const [original,entry] of Object.entries(mapping)) {
      const name=original.toLowerCase();
      if (!namePattern.test(name) || name.length>256 || seen.has(name)) throw new Error('invalid_headers');
      seen.add(name);
      const values=multiple?entry:[entry];
      if (!Array.isArray(values) || !values.length) throw new Error('invalid_headers');
      for (const item of values) {
        if (typeof item!=='string' || /[^\x20-\x7e\x80-\xff]/.test(item)) throw new Error('invalid_headers');
        bytes+=Buffer.byteLength(name)+Buffer.byteLength(item);count++;
        if (bytes>headerLimit || count>128) throw new Error('headers_too_large');
      }
      headers.set(name,values);
    }
  }
  for (const item of headers.get('connection')??[]) for (const field of item.split(',')) {
    const name=field.trim().toLowerCase();if (!namePattern.test(name)) throw new Error('invalid_connection');
    headers.delete(name);
  }
  for (const name of headers.keys()) if (withheld.has(name)||name.startsWith('access-control-')) headers.delete(name);
  return {statusCode:value.statusCode,bodyBase64:binary?value.body:Buffer.from(value.body).toString('base64'),isBase64Encoded:binary,
    headers:[...headers].flatMap(([name,values])=>values.map(item=>[name,item]))};
}
