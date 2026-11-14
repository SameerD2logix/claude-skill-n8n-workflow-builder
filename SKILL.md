---
name: n8n-workflow-builder
description: Design and generate importable n8n workflow JSON (triggers, HTTP calls, AI nodes, IF/Switch branches, schedules), then validate it before handing it over. Use when the user asks to build, fix or explain an n8n workflow or automation, or pastes n8n JSON.
---

# n8n Workflow Builder

Produce workflow JSON the user can paste straight into n8n (**Workflows → Import from file / paste**),
and catch the mistakes that make imports fail or workflows break silently.

## Workflow

1. **Clarify the automation in one sentence:** *When X happens, do Y, then Z.*
   Identify the trigger, the data each step needs, and where errors should go.
2. **Sketch the node list** before writing JSON (name → type → purpose). Show it to the user for
   anything larger than 5 nodes.
3. **Write the JSON** following `reference/node-cheatsheet.md`:
   - unique, human-readable node `name`s (connections refer to names)
   - `position` on a left-to-right grid (x += 220 per step)
   - **never** put API keys or passwords in parameters; use n8n credentials and say which ones to create
4. **Validate:**
   ```bash
   python scripts/validate_workflow.py workflow.json
   ```
   Fix all errors and re-run until clean.
5. **Hand over:** the JSON, the list of credentials to create, and how to test it (pin data or "Test workflow").

## Design rules

- One trigger per workflow. Use a sub-workflow (Execute Workflow) instead of giant graphs.
- Add an **Error Trigger** workflow for anything that runs unattended.
- Prefer `HTTP Request` with predefined credentials over custom code.
- Keep `Code` nodes small and pure; comment what they return.
- Respect rate limits: `Wait` or batch with `Loop Over Items` (SplitInBatches).

## Explaining an existing workflow

Run the validator first, then describe the flow trigger-to-end in plain language, and list risks
(hardcoded secrets, missing error handling, unbounded loops).
