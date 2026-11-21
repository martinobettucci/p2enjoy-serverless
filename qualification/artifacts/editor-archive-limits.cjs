// @spec docs/BACKLOG.md#sls-070 | docs/CODE_EDITOR_ARCHIVE_LIMITS.md#frontières-du-paquet
// @verifies docs/BACKLOG.md#sls-070 | docs/CODE_EDITOR_ARCHIVE_LIMITS.md#réalisation-du-passage-de-frontières
const fs = require('node:fs');
const path = require('node:path');
const {createHash} = require('node:crypto');
exports.handler = async () => {
  const folders = ['']; let files = 0, directories = 0, bytes = 0;
  const payloads = [];
  while (folders.length) {
    const relative = folders.pop();
    for (const entry of await fs.promises.readdir(path.join(__dirname, relative), {withFileTypes: true})) {
      const name = path.posix.join(relative, entry.name);
      if (entry.isDirectory()) { directories++; folders.push(name); continue; }
      if (!entry.isFile()) throw new Error('Unexpected artifact member');
      files++; const file = path.join(__dirname, name), info = await fs.promises.stat(file); bytes += info.size;
      if (/^payload(?:-\d+)?\.bin$/.test(name)) {
        const digest = createHash('sha256');
        for await (const chunk of fs.createReadStream(file)) digest.update(chunk);
        payloads.push({path: name, bytes: info.size, sha256: digest.digest('hex')});
      }
    }
  }
  const marker = await fs.promises.readFile(path.join(__dirname, 'marker.txt'));
  return {statusCode: 200, headers: {'Content-Type': 'application/json'}, body: JSON.stringify({
    fixture: 'editor-archive-limits', files, directories, bytes,
    marker_bytes: marker.length, marker_sha256: createHash('sha256').update(marker).digest('hex'),
    payloads: payloads.sort((a, b) => a.path.localeCompare(b.path)),
  })};
};
