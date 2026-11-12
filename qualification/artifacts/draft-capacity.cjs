// @spec docs/BACKLOG.md#sls-070 | docs/CODE_DRAFT_CAPACITY.md#publication-conservation-et-nettoyage
exports.handler = async (event, context) => ({
  statusCode: 200,
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({marker: 'draft-capacity-published', requestId: context.awsRequestId})
});
