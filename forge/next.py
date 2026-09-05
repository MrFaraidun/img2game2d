#!/usr/bin/env python3
"""
img2game2d next-step gate.

Always run this FIRST before any other step. It reads the local state and
prints the exact next command to run. If it exits with code 3 → hard stop.

Usage:
    python3 forge/next.py --state .img2game2d/state.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

STEP_COMMANDS: dict[str, str] = {
    "intake.probe":         "python3 forge/stage1_intake/probe_image.py {reference}",
    "intake.style":         "python3 forge/stage1_intake/detect_style.py {reference} --out analysis/style.json",
    "intake.views":         "python3 forge/stage1_intake/detect_views.py {reference} --out analysis/views.json",
    "intake.bg_removal":    "python3 forge/stage1_intake/remove_background.py {reference} --out source/foreground.png --mask source/mask.png",
    "intake.analysis":      "[Agent] Perform visual analysis using prompts/analyze.md → write analysis/analysis.json",
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

STOP_REASONS = {
    "max_corrections": "Reached maximum correction loop iterations ({max}). Review manually.",
    "stage_stopped":   "Step '{step}' is marked stopped. Resolve the blocker and reset the step.",
}


def load_state(path: str) -> dict:
    if not Path(path).exists():
        print(f"ERROR: State file not found: {path}", file=sys.stderr)
        print("Initialize with: python3 forge/state.py init --state <path> --reference <img>", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


def main() -> None:
    parser = argparse.ArgumentParser(description="img2game2d step gate")
    parser.add_argument("--state", required=True, help="Path to state.json")
    args = parser.parse_args()

    state = load_state(args.state)
    steps: dict[str, dict] = state["steps"]
    reference: str = state.get("reference", "")
    correction_loops: dict = state.get("correction_loops", {})
    total_used: int = correction_loops.get("total_used", 0)
    total_max: int = correction_loops.get("total_max", 6)

    # Check total correction loop limit
    if total_used >= total_max:
        print(f"\n⛔ HARD STOP: {STOP_REASONS['max_corrections'].format(max=total_max)}")
        print("Report to user and request direction (refine input / relax thresholds / stop).")
        sys.exit(3)

    # Find next pending step
    next_step = None
    for step_id, step in steps.items():
        status = step["status"]
        if status == "stopped":
            print(f"\n⛔ HARD STOP: {STOP_REASONS['stage_stopped'].format(step=step_id)}")
            sys.exit(3)
        if status == "pending":
            next_step = (step_id, step)
            break

    if next_step is None:
        print("\n✅ All steps complete!")
        _print_summary(state)
        sys.exit(0)

    step_id, step = next_step
    cmd = STEP_COMMANDS.get(step_id, f"[Unknown step: {step_id}]")
    cmd = cmd.replace("{reference}", reference)

    # Count pending steps
    pending = sum(1 for s in steps.values() if s["status"] == "pending")
    done = sum(1 for s in steps.values() if s["status"] in ("done", "skipped"))
    total = len(steps)

    print(f"\n=== img2game2d · {state['asset_id']} ===")
    print(f"Profile    : {state['profile']}")
    print(f"Progress   : {done}/{total} steps done, {pending} remaining")
    print(f"Corrections: {total_used}/{total_max} total used")
    print()
    print(f"► NEXT STEP: {step_id}")
    print(f"  Command  : {cmd}")
    print()
    print(f"After completion:")
    print(f"  python3 forge/state.py mark {step_id} --state {args.state} --evidence <output-path>")
    print(f"  python3 forge/next.py --state {args.state}")


def _print_summary(state: dict) -> None:
    steps = state["steps"]
    print(f"\nAsset: {state['asset_id']}")
    print(f"Profile: {state['profile']}")
    for step_id, step in steps.items():
        icon = "✓" if step["status"] == "done" else "⊘"
        ev = step.get("evidence") or "-"
        print(f"  {icon} {step_id:40s}  evidence={ev}")


if __name__ == "__main__":
    main()
