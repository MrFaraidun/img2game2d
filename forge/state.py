#!/usr/bin/env python3
"""
img2game2d state machine.

Usage:
    python3 forge/state.py init --state .img2game2d/state.json \
        --reference character.png --profile character
    python3 forge/state.py mark <step-id> --state .img2game2d/state.json \
        --evidence path/to/evidence
    python3 forge/state.py query --state .img2game2d/state.json
    python3 forge/state.py reset <step-id> --state .img2game2d/state.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Step definitions ──────────────────────────────────────────────────────────

PROFILES = {
    "character": [
        "intake.probe",
        "intake.style",
        "intake.views",
        "intake.bg_removal",
        "intake.analysis",
        "spec.asset_spec",
        "spec.layer_decompose",
        "spec.rig",
        "build.extract_layers",
        "build.occlusion",
        "build.animations",
        "review.silhouette",
        "review.colors",
        "review.continuity",
        "review.record",
        "atlas.pack",
        "export.godot",
        "export.unity",
        "export.phaser",
        "export.pixijs",
    ],
    "object": [
        "intake.probe",
        "intake.style",
        "intake.views",
        "intake.bg_removal",
        "intake.analysis",
        "spec.asset_spec",
        "spec.layer_decompose",
        "build.extract_layers",
        "review.silhouette",
        "review.colors",
        "review.record",
        "atlas.pack",
        "export.godot",
        "export.unity",
        "export.phaser",
        "export.pixijs",
    ],
    "effect": [
        "intake.probe",
        "intake.style",
        "intake.analysis",
        "spec.asset_spec",
        "build.animations",
        "review.continuity",
        "review.record",
        "atlas.pack",
        "export.godot",
        "export.unity",
        "export.phaser",
        "export.pixijs",
    ],
}

STEP_COMMANDS: dict[str, str] = {
    "intake.probe":         "python3 forge/stage1_intake/probe_image.py {reference}",
    "intake.style":         "python3 forge/stage1_intake/detect_style.py {reference} --out analysis/style.json",
    "intake.views":         "python3 forge/stage1_intake/detect_views.py {reference} --out analysis/views.json",
    "intake.bg_removal":    "python3 forge/stage1_intake/remove_background.py {reference} --out source/foreground.png --mask source/mask.png",
    "intake.analysis":      "[Agent] Run visual analysis using prompts/analyze.md → write analysis/analysis.json",
    "spec.asset_spec":      "python3 forge/stage2_spec/new_asset_spec.py --analysis analysis/analysis.json --out asset.json",
    "spec.layer_decompose": "python3 forge/stage2_spec/layer_decompose.py asset.json --out layers/layer-spec.json",
    "spec.rig":             "python3 forge/stage2_spec/build_rig.py layers/layer-spec.json --out metadata/rig.json",
    "build.extract_layers": "python3 forge/stage3_build/extract_layers.py --source source/foreground.png --spec layers/layer-spec.json --out layers/",
    "build.occlusion":      "python3 forge/stage3_build/reconstruct_occlusion.py --spec layers/layer-spec.json --layers layers/ --out layers/",
    "build.animations":     "python3 forge/stage3_build/generate_frames.py --reference source/original.png --spec asset.json --out animations/",
    "review.silhouette":    "python3 forge/stage4_review/validate_silhouette.py --reference source/original.png --frames animations/idle/ --out analysis/silhouette_check.json",
    "review.colors":        "python3 forge/stage4_review/validate_colors.py --reference source/original.png --frames animations/ --out analysis/color_check.json",
    "review.continuity":    "python3 forge/stage4_review/validate_continuity.py --frames animations/ --out analysis/continuity_check.json",
    "review.record":        "python3 forge/stage4_review/append_review.py asset.json --stage review --action continue",
    "atlas.pack":           "python3 forge/stage5_atlas/pack_atlas.py --frames animations/ --out atlases/",
    "export.godot":         "python3 forge/stage6_export/export.py --asset asset.json --atlases atlases/ --engine godot --out exports/godot/",
    "export.unity":         "python3 forge/stage6_export/export.py --asset asset.json --atlases atlases/ --engine unity --out exports/unity/",
    "export.phaser":        "python3 forge/stage6_export/export.py --asset asset.json --atlases atlases/ --engine phaser --out exports/phaser/",
    "export.pixijs":        "python3 forge/stage6_export/export.py --asset asset.json --atlases atlases/ --engine pixijs --out exports/pixijs/",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def _save(path: str, data: dict) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"State saved → {path}")


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_init(args: argparse.Namespace) -> None:
    profile = args.profile
    if profile not in PROFILES:
        print(f"ERROR: Unknown profile '{profile}'. Choose: {list(PROFILES)}", file=sys.stderr)
        sys.exit(1)

    steps = {
        step_id: {
            "status": "pending",
            "evidence": None,
            "completed_at": None,
            "loop_count": 0,
        }
        for step_id in PROFILES[profile]
    }

    state = {
        "version": "1.0.0",
        "asset_id": args.asset_id or Path(args.reference).stem,
        "reference": args.reference,
        "profile": profile,
        "created_at": _now(),
        "updated_at": _now(),
        "correction_loops": {"per_stage": 3, "total_max": 6, "total_used": 0},
        "steps": steps,
    }

    _save(args.state, state)
    print(f"Initialized img2game2d state: profile={profile}, steps={len(steps)}")
    print(f"Run: python3 forge/next.py --state {args.state}")


def cmd_mark(args: argparse.Namespace) -> None:
    state = _load(args.state)
    step_id = args.step_id

    if step_id not in state["steps"]:
        print(f"ERROR: Unknown step '{step_id}'", file=sys.stderr)
        sys.exit(1)

    status = args.status
    state["steps"][step_id]["status"] = status
    state["steps"][step_id]["completed_at"] = _now()
    if args.evidence:
        state["steps"][step_id]["evidence"] = args.evidence
    if args.reason:
        state["steps"][step_id]["skip_reason"] = args.reason
    state["updated_at"] = _now()

    _save(args.state, state)
    print(f"Marked {step_id} → {status}")


def cmd_query(args: argparse.Namespace) -> None:
    state = _load(args.state)
    steps = state["steps"]
    total = len(steps)
    done = sum(1 for s in steps.values() if s["status"] in ("done", "skipped"))
    print(f"\n=== img2game2d State: {state['asset_id']} ===")
    print(f"Profile : {state['profile']}")
    print(f"Progress: {done}/{total} steps")
    print()
    for step_id, step in steps.items():
        icon = {"done": "✓", "skipped": "⊘", "pending": "·", "stopped": "✗", "in_progress": "→"}.get(step["status"], "?")
        print(f"  {icon} {step_id:40s}  [{step['status']}]")
    print()


def cmd_reset(args: argparse.Namespace) -> None:
    state = _load(args.state)
    step_id = args.step_id
    if step_id not in state["steps"]:
        print(f"ERROR: Unknown step '{step_id}'", file=sys.stderr)
        sys.exit(1)
    state["steps"][step_id]["status"] = "pending"
    state["steps"][step_id]["evidence"] = None
    state["steps"][step_id]["completed_at"] = None
    state["updated_at"] = _now()
    _save(args.state, state)
    print(f"Reset {step_id} → pending")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="img2game2d state machine")
    sub = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = sub.add_parser("init", help="Initialize state for a new project")
    p_init.add_argument("--state", required=True)
    p_init.add_argument("--reference", required=True, help="Path to source image")
    p_init.add_argument("--profile", default="character",
                        choices=list(PROFILES), help="Asset profile")
    p_init.add_argument("--asset-id", dest="asset_id", help="Override asset ID")

    # mark
    p_mark = sub.add_parser("mark", help="Mark a step complete")
    p_mark.add_argument("step_id")
    p_mark.add_argument("--state", required=True)
    p_mark.add_argument("--evidence", help="Path to evidence file")
    p_mark.add_argument("--status", default="done",
                        choices=["done", "skipped", "stopped"])
    p_mark.add_argument("--reason", help="Required when skipping")

    # query
    p_query = sub.add_parser("query", help="Show current state")
    p_query.add_argument("--state", required=True)

    # reset
    p_reset = sub.add_parser("reset", help="Reset a step to pending")
    p_reset.add_argument("step_id")
    p_reset.add_argument("--state", required=True)

    args = parser.parse_args()
    {
        "init": cmd_init,
        "mark": cmd_mark,
        "query": cmd_query,
        "reset": cmd_reset,
    }[args.command](args)


if __name__ == "__main__":
    main()
