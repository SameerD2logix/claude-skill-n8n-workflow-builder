import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from validate_workflow import main, validate  # noqa: E402

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "rss-to-slack-digest.json"
WF = json.loads(EXAMPLE.read_text(encoding="utf-8"))


def errors(wf):
    return [f for f in validate(wf) if f.level == "error"]


def test_example_is_clean():
    assert validate(WF) == []
    assert main([str(EXAMPLE)]) == 0


def test_missing_target_and_duplicate_name():
    wf = copy.deepcopy(WF)
    wf["connections"]["Read RSS feed"]["main"][0][0]["node"] = "Nope"
    wf["nodes"].append(copy.deepcopy(wf["nodes"][1]))
    msgs = " ".join(f.message for f in errors(wf))
    assert "missing node 'Nope'" in msgs and "Duplicate node name" in msgs


def test_hardcoded_secret_is_error_but_expression_is_fine():
    wf = copy.deepcopy(WF)
    wf["nodes"][1]["parameters"]["headers"] = {"Authorization": "Bearer abcdefghijklmnopqrstuvwxyz123456"}
    assert any("Bearer token" in f.message for f in errors(wf))
    wf["nodes"][1]["parameters"]["headers"] = {"Authorization": "={{ $env.TOKEN }}"}
    assert not errors(wf)


def test_no_trigger_and_endless_loop():
    wf = copy.deepcopy(WF)
    wf["nodes"] = wf["nodes"][1:]
    del wf["connections"]["Every morning 9am"]
    # Slack -> Claude -> Slack has no Wait/IF/Filter in between, so it would never stop
    wf["connections"]["Post to Slack"] = {"main": [[{"node": "Summarize with Claude", "type": "main", "index": 0}]]}
    msgs = " ".join(f.message for f in errors(wf))
    assert "No trigger" in msgs and "Endless loop" in msgs
