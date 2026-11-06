// @spec docs/BACKLOG.md#sls-050 | docs/STORAGE_AGENT.md#instances-avec-baux-gérés
const fs = require('node:fs');
const { errno } = require('node:os').constants;

exports.handler = async (event) => {
  const volume = event.volume === 'cache' ? '/cache' : '/data';
  if (!/^[a-z][a-z0-9-]{0,63}$/.test(event.name)) throw new Error('Invalid file name');
  const path = `${volume}/${event.name}`;
  try {
    if (event.operation === 'write' || event.operation === 'write-sleep') {
      fs.writeFileSync(path, event.value, { flag: 'w' });
      const fd = fs.openSync(path, 'r');
      try { fs.fsyncSync(fd); } finally { fs.closeSync(fd); }
    } else if (event.operation === 'fill') {
      fs.writeFileSync(path, Buffer.alloc(event.bytes, 65));
    } else if (event.operation === 'remove') {
      fs.unlinkSync(path);
      return { statusCode: 200, body: JSON.stringify({ removed: true }) };
    } else if (event.operation !== 'read') throw new Error('Invalid operation');
    if (event.operation === 'write-sleep') await new Promise(resolve => setTimeout(resolve, event.ms));
    return { statusCode: 200, body: JSON.stringify({ value: fs.readFileSync(path, 'utf8'), pid: process.pid }) };
  } catch (error) {
    // Node 24 reports the real Linux EDQUOT as UNKNOWN with errno -122.
    const code = error.errno === -errno.EDQUOT ? 'EDQUOT' : error.code;
    if (!['EDQUOT', 'ENOENT', 'ENOTCONN', 'EIO'].includes(code)) {
      console.error(JSON.stringify({ code: error.code, errno: error.errno, syscall: error.syscall }));
      throw error;
    }
    return { statusCode: code === 'EDQUOT' ? 507 : 404,
      body: JSON.stringify({ error: code, nativeCode: error.code, errno: error.errno }) };
  }
};
