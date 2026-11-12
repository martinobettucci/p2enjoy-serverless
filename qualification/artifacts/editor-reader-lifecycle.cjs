// @spec docs/BACKLOG.md#sls-070 | docs/CODE_EDITOR_READ_CONCURRENCY.md
// @verifies docs/CODE_EDITOR_READ_CONCURRENCY.md#résultats-à-établir
const fs = require('node:fs/promises');
const path = require('node:path');
const {createHash} = require('node:crypto');
exports.handler = async () => {
  const data = await fs.readFile(path.join(__dirname, 'reader-gate.txt'));
  return {statusCode: 200, headers: {'Content-Type': 'application/json'}, body: JSON.stringify({
    marker: 'editor-reader-lifecycle', bytes: data.length,
    sha256: createHash('sha256').update(data).digest('hex'),
  })};
};
