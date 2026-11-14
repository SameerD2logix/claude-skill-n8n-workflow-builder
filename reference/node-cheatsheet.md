# n8n node cheatsheet (common nodes)

Node `type` strings are stable across versions; `typeVersion` may be newer in your n8n. If an
import shows "?" on a node, open it once and n8n migrates the version.

| Purpose | type | Notes |
|---|---|---|
| Manual start | `n8n-nodes-base.manualTrigger` | testing only |
| Schedule | `n8n-nodes-base.scheduleTrigger` | `rule.interval[]` |
| Webhook | `n8n-nodes-base.webhook` | set `httpMethod`, `path`; protect with header auth |
| Form | `n8n-nodes-base.formTrigger` | simple public forms |
| Error workflow | `n8n-nodes-base.errorTrigger` | in a separate workflow |
| HTTP call | `n8n-nodes-base.httpRequest` | use `authentication: predefinedCredentialType` |
| Branch | `n8n-nodes-base.if` / `n8n-nodes-base.switch` | outputs: index 0 = true, 1 = false |
| Filter | `n8n-nodes-base.filter` | drops non-matching items |
| Set fields | `n8n-nodes-base.set` | rename / shape data |
| Code | `n8n-nodes-base.code` | return `[{json: {...}}]` |
| Loop | `n8n-nodes-base.splitInBatches` | "Loop Over Items" |
| Wait | `n8n-nodes-base.wait` | rate limits, delays |
| Sub-workflow | `n8n-nodes-base.executeWorkflow` | reuse logic |
| Claude | `@n8n/n8n-nodes-langchain.anthropic` | credential: Anthropic API |
| AI Agent | `@n8n/n8n-nodes-langchain.agent` | + chat model + tools sub-nodes |
| Postgres | `n8n-nodes-base.postgres` | use query parameters, never string-concat SQL |

## Connection format

```json
"connections": {
  "Source node name": {
    "main": [
      [ { "node": "Target if true", "type": "main", "index": 0 } ],
      [ { "node": "Target if false", "type": "main", "index": 0 } ]
    ]
  }
}
```
The outer array is the **output index** of the source node; the inner array lists targets for that output.

## Credentials

Never put secrets in `parameters`. Reference a credential by type:
```json
"credentials": { "anthropicApi": { "id": "CREATE_ME", "name": "Anthropic account" } }
```
After import, open the node and pick or create the credential.
