// @spec docs/BACKLOG.md#sls-070 | docs/CODE_EDITOR_SOURCE_LIMITS.md#campagne-https-de-sources-et-bornes
// Original handler: inspect the actual packaged bytes through a real Docker invocation.
const fs = require('node:fs');
const crypto = require('node:crypto');
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
exports.handler = async () => {
  const large = fs.readFileSync('large-source.txt');
  const binary = fs.readFileSync('payload.bin');
  return {
    statusCode: 200,
    body: JSON.stringify({
      marker: fs.readFileSync('source-marker.txt', 'utf8').trimEnd(),
      large_size: large.length,
      large_sha256: sha(large),
      binary_sha256: sha(binary),
      yaml_version: require('yaml/package.json').version,
      executable: Boolean(fs.statSync('editor-source-limits.cjs').mode & 0o111),
    }),
  };
};
