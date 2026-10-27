#!/usr/bin/env python3
"""Install Fox agent skills into an agent workspace."""
from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

AGENTS = {
    "codex": ".agents/skills",
    "claude": ".claude/skills",
    "cursor": ".cursor/skills",
    "antigravity": ".agents/skills",
}
ROOT = Path(__file__).resolve().parent

AVAILABLE_SKILLS = ["fox", "fox-explore", "fox-review", "fox-verify", "fox-fragments"]
LEGACY_BOTH_SKILLS = ["fox", "fox-explore"]


def _install_single(
    target_dir: Path,
    skill_name: str,
    force: bool = False,
    dry_run: bool = False,
) -> Path:
    source = ROOT / "skills" / skill_name
    dest = target_dir / skill_name

    if not (source / "SKILL.md").is_file():
        raise ValueError(f"Incomplete source: {source}")
    if source == dest or dest.is_relative_to(source):
        raise ValueError("Cannot install inside a source skill")
    if dest.exists() and not force:
        raise FileExistsError(f"{dest} already exists; pass --force to replace")
    if dest.is_symlink():
        raise ValueError(f"Refusing to replace symlink: {dest}")

    if dry_run:
        print(f"WOULD INSTALL {source} -> {dest}")
        return dest

    target_dir.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{skill_name}-stage-", dir=target_dir))
    backup = None
    try:
        shutil.rmtree(stage)
        shutil.copytree(
            source,
            stage,
            symlinks=False,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
        )
        if dest.exists():
            backup = Path(tempfile.mkdtemp(prefix=f".{skill_name}-backup-", dir=target_dir))
            shutil.rmtree(backup)
            dest.rename(backup)
        stage.rename(dest)
        if backup and backup.exists():
            shutil.rmtree(backup)
    except BaseException:
        if dest.exists():
            shutil.rmtree(dest)
        if backup and backup.exists():
            backup.rename(dest)
        raise
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return dest


def install(
    agent: str,
    project: Path,
    force: bool = False,
    dry_run: bool = False,
    is_global: bool = False,
    skill: str | list[str] = "fox",
) -> list[Path]:
    if agent not in AGENTS:
        raise ValueError(f"Unknown agent '{agent}'; choose from: {', '.join(AGENTS.keys())}")

    if is_global:
        if agent == "antigravity":
            target_dir = Path.home() / ".gemini" / "config" / "skills"
        else:
            raise ValueError("--global is currently supported for antigravity")
    else:
        project = project.expanduser().resolve()
        if not project.is_dir():
            raise ValueError(f"Project directory must exist: {project}")
        target_dir = project / AGENTS[agent]

    if isinstance(skill, str):
        if skill == "all":
            skills_to_install = list(AVAILABLE_SKILLS)
        elif skill == "both":
            # Preserve the original two-skill interface for existing automation.
            skills_to_install = list(LEGACY_BOTH_SKILLS)
        elif "," in skill:
            parts = [s.strip() for s in skill.split(",") if s.strip()]
            for s in parts:
                if s not in AVAILABLE_SKILLS:
                    raise ValueError(
                        f"Unknown skill '{s}'; choose from: {', '.join(AVAILABLE_SKILLS)}, all"
                    )
            # Deduplicate while preserving order
            skills_to_install = list(dict.fromkeys(parts))
        elif skill in AVAILABLE_SKILLS:
            skills_to_install = [skill]
        else:
            raise ValueError(
                f"Unknown skill '{skill}'; choose from: {', '.join(AVAILABLE_SKILLS)}, all"
            )
    elif isinstance(skill, (list, tuple, set)):
        skills_to_install = []
        for s in skill:
            if s not in AVAILABLE_SKILLS:
                raise ValueError(
                    f"Unknown skill '{s}'; choose from: {', '.join(AVAILABLE_SKILLS)}, all"
                )
            if s not in skills_to_install:
                skills_to_install.append(s)
    else:
        raise ValueError(
            f"Unknown skill '{skill}'; choose from: {', '.join(AVAILABLE_SKILLS)}, all"
        )

    results: list[Path] = []
    for s in skills_to_install:
        results.append(_install_single(target_dir, s, force=force, dry_run=dry_run))
    return results


def print_success_guidance(dests: list[Path], agent: str, skill: str) -> None:
    print("\n" + "=" * 62)
    print("Fox Agent Skills Installation Guidance")
    print("=" * 62)
    for dest in dests:
        print(f"Installed: {dest}")

    print("\nHow to invoke:")
    if agent in ("claude", "antigravity"):
        slash_cmds = " ".join(f"/{d.name}" for d in dests)
        print(f"  Slash command: {slash_cmds}")
        print("  Or paste a task prompt into your agent chat.")
    else:
        print("  Paste your task prompt into your agent chat.")
        print(f"  Your coding agent will read {dests[0].parent} automatically.")

    print("\nCopy-paste example prompts to get started:")
    if skill == "fox":
        print('  "Investigate why this function returns the wrong result. Find the cause, fix it, and verify the change."')
    elif skill == "fox-explore":
        print('  "Explain this repository architecture, trace the request lifecycle, and compare our design with standard practices."')
    elif skill == "fox-fragments":
        print('  "Use Fox Fragments and read only the instructions needed for this task."')
    elif skill == "fox-review":
        print('  "Review the last commit for correctness, regressions, missing tests, and unnecessary complexity. Do not edit files."')
    elif skill == "fox-verify":
        print('  "Challenge whether these tests detect meaningful regressions. Use isolated mutations and do not edit the working tree."')
    else:
        print('  Fox:         "Investigate why this function returns the wrong result. Find the cause, fix it, and verify the change."')
        print('  Fox Explore: "Explain this repository architecture, trace the request flow, and advise on scaling limits."')
        print('  Fox Review:  "Review the last commit for correctness and regression risks without editing files."')
        print('  Fox Verify:  "Test whether the new checks fail when the required behavior is broken."')
        print('  Fox Fragments: "Select and load only the guidance needed for this task."')
        print('  Combined:    "Explore the design, repair it, review the diff, then challenge the verification evidence."')

    print("\nHow to verify it loaded:")
    print("  Look for Fox's 4-step workflow (Ground, Trace, Repair, Verify)")
    print("  Fox Explore's 4-stage exploration (Scope, Map, Compare, Report),")
    print("  Fox Review's 4-stage audit (Target, Trace, Validate, Report),")
    print("  or Fox Verify's adversarial checks (Claim, Inspect, Challenge, Report).")

    print("\nIf the agent does not recognize the skill:")
    print("  1. Restart your coding agent session to refresh installed skills.")
    print(f"  2. Confirm the skill folder exists at: {dests[0]}")
    print(f'  3. Explicitly tell the agent: "Use the instructions in {dests[0]}/SKILL.md"')
    print("=" * 62 + "\n")


def run_interactive_wizard() -> int:
    print("\nWelcome to Fox Setup")
    print("Better fixes. Clear exploration. Verified reviews. Stronger evidence.\n")

    # Step 1: Agent selection
    print("1. Which AI coding agent do you use?")
    agent_options = [
        ("antigravity", "Google Antigravity (.agents/skills)"),
        ("claude", "Anthropic Claude Code (.claude/skills)"),
        ("cursor", "Cursor (.cursor/skills)"),
        ("codex", "OpenAI Codex (.agents/skills)"),
    ]
    for idx, (_, label) in enumerate(agent_options, 1):
        print(f"   [{idx}] {label}")

    agent_choice = None
    while agent_choice is None:
        try:
            raw = input("   Select an option [1-4] (default: 1): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSetup cancelled.")
            return 1
        if not raw:
            agent_choice = agent_options[0][0]
            break
        if raw.isdigit() and 1 <= int(raw) <= len(agent_options):
            agent_choice = agent_options[int(raw) - 1][0]
            break
        print("   Please enter a number between 1 and 4.")

    # Step 2: Skill selection
    print("\n2. Which skill would you like to install?")
    skill_options = [
        ("fox", "Fox: Fix what's broken (root-cause debugging and verified repair)"),
        ("fox-explore", "Fox Explore: Understand your code (architecture, research & recommendations)"),
        ("fox-review", "Fox Review: Audit a change (correctness, risk & unnecessary complexity)"),
        ("fox-fragments", "Fox Fragments: Load focused guidance on demand"),
        ("all", "All five skills (full suite)"),
        ("fox-verify", "Fox Verify: Challenge whether tests detect meaningful regressions"),
    ]
    for idx, (_, label) in enumerate(skill_options, 1):
        print(f"   [{idx}] {label}")
    print("   Or enter a comma-separated combination (e.g. 1,6 or fox,fox-verify)")

    skill_choice = None
    while skill_choice is None:
        try:
            raw = input("   Select an option [1-6] (default: 5): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSetup cancelled.")
            return 1
        if not raw:
            skill_choice = skill_options[4][0]
            break
        if raw.isdigit() and 1 <= int(raw) <= len(skill_options):
            skill_choice = skill_options[int(raw) - 1][0]
            break
        if "," in raw:
            parts = [p.strip() for p in raw.split(",") if p.strip()]
            resolved = []
            valid = True
            for p in parts:
                if p.isdigit() and int(p) in {1, 2, 3, 4, 6}:
                    resolved.append(skill_options[int(p) - 1][0])
                elif p in AVAILABLE_SKILLS:
                    resolved.append(p)
                else:
                    valid = False
                    break
            if valid and resolved:
                skill_choice = ",".join(resolved)
                break
        print("   Please enter 1 through 6, or a combination like 1,6.")

    # Step 3: Location (Project vs Global)
    is_global = False
    project_path = Path.cwd()

    if agent_choice == "antigravity":
        print("\n3. Installation scope:")
        print("   [1] Project workspace (current directory)")
        print("   [2] Global configuration (~/.gemini/config/skills)")
        try:
            scope_raw = input("   Select scope [1-2] (default: 1): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSetup cancelled.")
            return 1
        if scope_raw == "2":
            is_global = True

    if not is_global:
        try:
            proj_raw = input(f"\n3. Target project directory (default: {project_path}): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSetup cancelled.")
            return 1
        if proj_raw:
            project_path = Path(proj_raw).expanduser().resolve()
            if not project_path.is_dir():
                print(f"Error: Directory '{project_path}' does not exist.")
                return 2

    # Step 4: Show destination and check existence
    if is_global:
        target_dir = Path.home() / ".gemini" / "config" / "skills"
    else:
        target_dir = project_path / AGENTS[agent_choice]

    if skill_choice == "all":
        skills_to_check = list(AVAILABLE_SKILLS)
    elif "," in skill_choice:
        skills_to_check = [s.strip() for s in skill_choice.split(",") if s.strip()]
    else:
        skills_to_check = [skill_choice]

    existing = [s for s in skills_to_check if (target_dir / s).exists()]

    force = False
    if existing:
        print(f"\nNotice: The following skill(s) already exist in {target_dir}:")
        for s in existing:
            print(f"  - {s}")
        try:
            replace_raw = input("Replace existing installation? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nSetup cancelled.")
            return 1
        if replace_raw in ("y", "yes"):
            force = True
        else:
            print("Installation cancelled. Existing files were preserved.")
            return 0

    print(f"\nInstalling to: {target_dir}")
    try:
        dests = install(
            agent=agent_choice,
            project=project_path,
            force=force,
            dry_run=False,
            is_global=is_global,
            skill=skill_choice,
        )
        for dest in dests:
            print(f"INSTALLED: {dest}")
        print_success_guidance(dests, agent_choice, skill_choice)
        return 0
    except Exception as ex:
        print(f"ERROR: {ex}", file=sys.stderr)
        return 2


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--agent",
        choices=AGENTS,
        default=None,
        help="Target agent environment (codex, claude, cursor, antigravity)",
    )
    p.add_argument(
        "--skill",
        default="fox",
        help="Skill to install: fox, fox-explore, fox-review, fox-verify, fox-fragments, all, both, or comma-separated (default: fox)",
    )
    p.add_argument(
        "--project",
        type=Path,
        default=Path.cwd(),
        help="Target project root directory (default: current directory)",
    )
    p.add_argument(
        "--global",
        dest="is_global",
        action="store_true",
        help="Install globally (~/.gemini/config/skills for antigravity)",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Replace existing skill installation",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned installation without modifying files",
    )
    p.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Run interactive setup wizard",
    )

    args = p.parse_args(argv)

    # Check for interactive trigger
    is_interactive_terminal = sys.stdin.isatty() and sys.stdout.isatty()
    should_run_interactive = args.interactive or (args.agent is None and is_interactive_terminal)

    if should_run_interactive:
        return run_interactive_wizard()

    if args.agent is None:
        p.error("the following arguments are required: --agent (or run interactively in a terminal)")

    try:
        dests = install(
            args.agent,
            args.project,
            args.force,
            args.dry_run,
            args.is_global,
            args.skill,
        )
        if not args.dry_run:
            for dest in dests:
                print("INSTALLED: " + str(dest))
            invocations = " ".join(f"/{d.name}" for d in dests)
            print(f"Invoke: {invocations}")
            print_success_guidance(dests, args.agent, args.skill)
        return 0
    except (ValueError, FileExistsError, OSError) as ex:
        print("ERROR: " + str(ex), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
