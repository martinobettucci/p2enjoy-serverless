// @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#chargeur-et-validation-docker
import {lstat,realpath} from 'node:fs/promises';
import {resolve,sep} from 'node:path';
import {pathToFileURL} from 'node:url';
import {registerHooks} from 'node:module';
import {types} from 'node:util';

export class LoadError extends Error {
  constructor(code) {super(code);this.code=code;}
}

// Both validation and future invocation load through this exact entry point.
export async function loadHandler(root,handler) {
  if (typeof handler!=='string' || handler.length>256 ||
      !/^[A-Za-z0-9_./-]+\.[A-Za-z_$][A-Za-z0-9_$]*$/.test(handler)) throw new LoadError('invalid_handler');
  const split=handler.lastIndexOf('.'), module=handler.slice(0,split), name=handler.slice(split+1);
  const parts=module.split('/');
  if (parts.some(part=>!part || part==='.' || part==='..')) throw new LoadError('invalid_handler');
  root=await realpath(root);
  const candidates=/\.(?:js|cjs|mjs)$/.test(module)?[module]:['.js','.cjs','.mjs'].map(ext=>module+ext);
  const found=[];
  for (const candidate of candidates) {
    let current=root, missing=false;
    for (const [index,part] of candidate.split('/').entries()) {
      current=resolve(current,part);
      let stat;
      try {stat=await lstat(current);} catch(error) {
        if (error.code==='ENOENT' || error.code==='ENOTDIR') {missing=true;break;}
        throw new LoadError('module_unreadable');
      }
      if (stat.isSymbolicLink()) throw new LoadError('module_link');
      if (index<candidate.split('/').length-1 && !stat.isDirectory()) {missing=true;break;}
      if (index===candidate.split('/').length-1 && !stat.isFile()) throw new LoadError('module_not_file');
    }
    if (!missing) {
      const actual=await realpath(current);
      if (!actual.startsWith(root+sep)) throw new LoadError('invalid_handler');
      found.push({path:actual,module:candidate});
    }
  }
  if (!found.length) throw new LoadError('module_missing');
  if (found.length!==1) throw new LoadError('module_ambiguous');
  let namespace,format;
  const target=pathToFileURL(found[0].path).href;
  const hooks=registerHooks({load(url,context,nextLoad) {
    const loaded=nextLoad(url,context);
    if (url===target) format=loaded.format;
    return loaded;
  }});
  try {namespace=await import(target);} catch(error) {
    throw new LoadError(['ERR_MODULE_NOT_FOUND','MODULE_NOT_FOUND'].includes(error.code)?'dependency_missing':'import_failed');
  } finally {hooks.deregister();}
  if (!types.isModuleNamespaceObject(namespace)) throw new LoadError('import_invalid_namespace');
  let fn;
  try {
    if (format==='commonjs') {
      const exported=namespace['module.exports'];
      if (exported!=null && Object.hasOwn(exported,name)) fn=exported[name];
    } else if (format==='module' && Object.hasOwn(namespace,name)) fn=namespace[name];
  } catch {throw new LoadError('handler_not_callable');}
  if (typeof fn!=='function') throw new LoadError('handler_not_callable');
  return {fn,module:found[0].module};
}
