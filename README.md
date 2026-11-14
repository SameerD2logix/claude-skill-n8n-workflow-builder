# n8n Workflow Builder: a Claude Agent Skill

> Describe an automation in plain words → Claude writes **importable n8n workflow JSON** and validates it (wiring, triggers, loops, **hardcoded secrets**) before you import it.

![skill](https://img.shields.io/badge/Claude-Agent%20Skill-D97757) ![n8n](https://img.shields.io/badge/n8n-workflows-EA4B71) ![python](https://img.shields.io/badge/python-3.10%2B-3776AB) ![license](https://img.shields.io/badge/license-MIT-green)

## Why

AI-generated n8n JSON often *looks* right but fails on import or breaks quietly: a connection pointing to
a renamed node, two triggers, an infinite loop, or an API key pasted into a parameter. This skill makes
Claude follow a design checklist and run a validator on its own output.

## Install

```bash
git clone https://github.com/SameerD2logix/claude-skill-n8n-workflow-builder ~/.claude/skills/n8n-workflow-builder
```
Ask Claude: *"Build an n8n workflow: every morning, read this RSS feed, summarize new posts with Claude and send them to Slack."*

## Validator

```bash
$ python scripts/validate_workflow.py examples/rss-to-slack-digest.json
5 nodes, 0 error(s), 0 warning(s)
```

| Check | Level |
|---|---|
| Missing `nodes` / `connections`, node fields, bad `position` | error |
| Duplicate node names | error |
| Connections to nodes that don't exist | error |
| No trigger / several triggers | error / warning |
| Orphan nodes | warning |
| Hardcoded API keys, bearer tokens, GitHub/AWS/Slack tokens | error |
| Fields named password/token/api_key with literal values | warning |
| Cycles with no Wait / IF / Loop node | error |

Expressions like `={{ $env.TOKEN }}` are allowed. `--json` output for CI.

## Layout

```
SKILL.md                         design workflow Claude follows
reference/node-cheatsheet.md     node types, connection format, credentials
scripts/validate_workflow.py     validator (stdlib only)
examples/rss-to-slack-digest.json
tests/
```

## Tests

```bash
pip install pytest && pytest -q
```

## Author

**Sameer Hussain** · [LinkedIn](https://www.linkedin.com/in/sameer-hussain-87368a164) · [D2Logix](https://d2logix.com). n8n + AI automation for businesses.
