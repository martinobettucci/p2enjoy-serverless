// @spec docs/BACKLOG.md#sls-074 | docs/FUNCTION_VERSION_EXECUTION.md#preuves-réelles
// A real asynchronous import leaves time to edit while the publication proceeds.
await new Promise(resolve=>setTimeout(resolve,10000));
export const handler=async event=>({statusCode:200,body:JSON.stringify({source:'pilot-delay',path:event.path})});
