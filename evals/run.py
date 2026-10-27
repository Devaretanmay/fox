#!/usr/bin/env python3
"""Run reproducible Fox evaluations with an external coding-agent command."""
from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL_ROOT = Path(__file__).resolve().parent


def load_tasks() -> list[dict]:
    return json.loads((EVAL_ROOT / "tasks.json").read_text(encoding="utf-8"))


def run(command: list[str], cwd: Path, timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def install_variant(workspace: Path, variant: str) -> None:
    names = {
        "fox": ["fox"],
        "fox-explore": ["fox-explore"],
        "fox-review": ["fox-review"],
        "fox-verify": ["fox-verify"],
        "fox-fragments": ["fox-fragments"],
        "both": ["fox", "fox-explore"],
        "all": ["fox", "fox-explore", "fox-review", "fox-verify", "fox-fragments"],
    }.get(variant, [])
    for agent_dir in (workspace / ".agents/skills", workspace / ".claude/skills"):
        for name in names:
            target = agent_dir / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(ROOT / "skills" / name, target)


def command_for(template: str, workspace: Path, prompt: str) -> list[str]:
    parts = shlex.split(template)
    return [part.replace("{workspace}", str(workspace)).replace("{prompt}", prompt) for part in parts]


def changed_files(workspace: Path) -> list[str]:
    result = run(["git", "status", "--porcelain"], workspace)
    return sorted(line[3:] for line in result.stdout.splitlines() if len(line) > 3)


def extract_metrics(output: str) -> tuple[int | None, int | None, int | None]:
    """Read common JSONL agent events without treating prose as usage evidence."""
    events = []
    for line in output.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            events.append(value)

    def values_for(node, key):
        found = []
        if isinstance(node, dict):
            for current_key, value in node.items():
                if current_key == key and isinstance(value, int):
                    found.append(value)
                found.extend(values_for(value, key))
        elif isinstance(node, list):
            for value in node:
                found.extend(values_for(value, key))
        return found

    tool_calls = 0
    for event in events:
        event_type = str(event.get("type", "")).lower()
        item_type = str(event.get("item", {}).get("type", "")).lower() if isinstance(event.get("item"), dict) else ""
        if any(marker in event_type or marker in item_type for marker in ("tool_call", "function_call", "command_execution", "mcp_tool")):
            tool_calls += 1

    inputs = [value for event in events for value in values_for(event, "input_tokens")]
    outputs = [value for event in events for value in values_for(event, "output_tokens")]
    return (tool_calls if events else None, max(inputs) if inputs else None, max(outputs) if outputs else None)


def run_task(task: dict, variant: str, agent_command: str, timeout: int) -> dict:
    fixture = EVAL_ROOT / task["fixture"]
    with tempfile.TemporaryDirectory(prefix=f"fox-eval-{task['id']}-") as tmp:
        workspace = Path(tmp) / "repo"
        shutil.copytree(fixture, workspace, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
        install_variant(workspace, variant)
        run(["git", "init", "-q"], workspace)
        run(["git", "add", "."], workspace)
        run(["git", "-c", "user.name=Fox Eval", "-c", "user.email=eval@example.invalid", "commit", "-qm", "fixture"], workspace)

        candidate_patch = task.get("candidate_patch")
        if candidate_patch:
            applied = run(["git", "apply", candidate_patch], workspace)
            if applied.returncode != 0:
                raise RuntimeError(
                    f"Could not apply {candidate_patch} for {task['id']}: {applied.stderr.strip()}"
                )
            run(["git", "add", "-u"], workspace)
            committed = run(
                [
                    "git", "-c", "user.name=Fox Eval", "-c", "user.email=eval@example.invalid",
                    "commit", "-qm", "candidate change",
                ],
                workspace,
            )
            if committed.returncode != 0:
                raise RuntimeError(
                    f"Could not commit candidate for {task['id']}: {committed.stderr.strip()}"
                )

        started = time.monotonic()
        agent_args = command_for(agent_command, workspace, task["prompt"])
        try:
            agent = run(agent_args, workspace, timeout)
        except subprocess.TimeoutExpired as exc:
            agent = subprocess.CompletedProcess(
                agent_args,
                124,
                stdout=exc.stdout or "",
                stderr=(exc.stderr or "") + f"\nAgent timed out after {timeout} seconds.",
            )
        elapsed = time.monotonic() - started
        tool_calls, input_tokens, output_tokens = extract_metrics(agent.stdout)
        changes = changed_files(workspace)
        allowed = set(task.get("allowed_changes", []))
        required = set(task.get("must_change", []))
        relevant_changes = {path for path in changes if not path.startswith((".agents/", ".claude/"))}

        check = run(task["test_command"], workspace) if task.get("test_command") else None
        valid_run = agent.returncode == 0
        return {
            "task_id": task["id"],
            "kind": task["kind"],
            "variant": variant,
            "agent_exit": agent.returncode,
            "valid_run": valid_run,
            "elapsed_seconds": round(elapsed, 3),
            "task_success": (bool(check and check.returncode == 0 and required.issubset(relevant_changes)) if task["kind"] == "repair" else not relevant_changes) if valid_run else None,
            "regression_failures": (0 if check is None or check.returncode == 0 else 1) if valid_run else None,
            "unnecessary_edits": sorted(relevant_changes - allowed),
            "changed_files": sorted(relevant_changes),
            "tool_calls": tool_calls,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "human_review_required": task["kind"] in {"explore", "review", "verify"},
            "rubric": task.get("rubric", []),
            "agent_output": agent.stdout[-12000:],
            "agent_error": agent.stderr[-4000:],
            "test_output": ((check.stdout + check.stderr)[-4000:] if check else ""),
        }


def summarize(records: list[dict]) -> dict:
    valid = [record for record in records if record["valid_run"]]
    measured = [record for record in valid if not record["human_review_required"]]
    return {
        "runs": len(records),
        "invalid_runs": len(records) - len(valid),
        "automatically_scored": len(measured),
        "successes": sum(bool(record["task_success"]) for record in measured),
        "regression_failures": sum(record["regression_failures"] for record in valid),
        "unnecessary_edits": sum(len(record["unnecessary_edits"]) for record in valid),
        "tool_calls": sum(record["tool_calls"] for record in valid if record["tool_calls"] is not None) if any(record["tool_calls"] is not None for record in valid) else None,
        "input_tokens": sum(record["input_tokens"] for record in valid if record["input_tokens"] is not None) if any(record["input_tokens"] is not None for record in valid) else None,
        "output_tokens": sum(record["output_tokens"] for record in valid if record["output_tokens"] is not None) if any(record["output_tokens"] is not None for record in valid) else None,
        "note": "Usage metrics remain null unless the selected agent emits JSONL with tool or token fields. Exploration, review, and adversarial-verification quality require blind human grading against the stored rubric.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--variant",
        choices=["baseline", "fox", "fox-explore", "fox-review", "fox-verify", "fox-fragments", "both", "all"],
        required=True,
    )
    parser.add_argument("--agent-command", help="Command template containing {workspace} and {prompt}")
    parser.add_argument("--task", action="append", help="Task ID; repeat to select multiple tasks")
    parser.add_argument("--output", type=Path, default=Path("eval-results.json"))
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    tasks = load_tasks()
    runnable = [task for task in tasks if task["kind"] in {"repair", "explore", "review", "verify"}]
    if args.list:
        for task in tasks:
            print(f"{task['id']}: {task['kind']}")
        return 0
    if not args.agent_command:
        parser.error("--agent-command is required unless --list is used")
    if args.task:
        selected = set(args.task)
        runnable = [task for task in runnable if task["id"] in selected]
        missing = selected - {task["id"] for task in runnable}
        if missing:
            parser.error(f"unknown or non-runnable task(s): {', '.join(sorted(missing))}")

    records = [run_task(task, args.variant, args.agent_command, args.timeout) for task in runnable]
    payload = {"summary": summarize(records), "results": records}
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
