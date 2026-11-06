// @spec docs/BACKLOG.md#sls-062 | docs/CONSOLE_MANUAL.md#construction
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import MarkdownIt from 'markdown-it';

const moduleName = 'virtual:usage-manual';
const source = fileURLToPath(new URL('../docs/manual.md',import.meta.url));

export default {plugins:[{
  name:'usage-manual',
  resolveId(id) {if (id === moduleName) return '\0'+moduleName;},
  load(id) {
    if (id !== '\0'+moduleName) return;
    this.addWatchFile(source);
    const bytes = readFileSync(source), markdown = new MarkdownIt({html:false,linkify:false});
    const tokens = markdown.parse(bytes.toString('utf8'),{}), chapters = [], ids = new Set();
    if (tokens[0]?.type !== 'heading_open' || tokens[0].tag !== 'h1') throw new Error('Le manuel doit commencer par son titre.');
    const title = tokens[1].content;
    tokens.splice(0,3);
    for (let index = 0;index < tokens.length;index++) {
      const token = tokens[index];
      if (token.type === 'heading_open') {
        if (token.tag !== 'h2') throw new Error('Les chapitres du manuel utilisent des titres de niveau 2.');
        const label = tokens[index + 1].content;
        const anchor = label.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
        if (!anchor || ids.has(anchor) || anchor === 'sommaire') throw new Error('Les chapitres du manuel doivent avoir des ancres uniques.');
        ids.add(anchor);chapters.push({label,id:anchor});token.attrSet('id',anchor);token.attrSet('tabindex','-1');
      }
    }
    if (!title || !chapters.length) throw new Error('Le manuel doit contenir un titre et des chapitres.');
    for (const token of tokens.flatMap(token => [token,...(token.children || [])])) {
      if (token.type === 'image') throw new Error('Le manuel est un document textuel ; les images ne sont pas prises en charge.');
      if (token.type !== 'link_open') continue;
      const href = token.attrGet('href');
      if (!(href?.startsWith('#') && ids.has(href.slice(1)))) {
        let url;
        try {url = new URL(href);} catch {throw new Error('Un lien du manuel ne possède pas de destination servie : '+href);}
        if (url.protocol !== 'https:' || url.username || url.password) throw new Error('Un lien du manuel doit utiliser HTTPS sans identifiants.');
      }
    }
    const html = markdown.renderer.render(tokens,markdown.options,{});
    return 'export default '+JSON.stringify({title,chapters,html,sha256:createHash('sha256').update(bytes).digest('hex')})+';';
  },
}]};
