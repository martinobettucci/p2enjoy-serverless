// @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#preuves
// @verifies docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#preuves
const {writeSync} = require('node:fs');
const secret = process.env.QUALIFICATION_SYNTHETIC_SECRET;
writeSync(2, `qualification-import-secret=${secret}\n`);
throw new Error(secret);
