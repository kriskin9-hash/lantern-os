"""
Σ₀ grounding for the Tesseract Status Cube whitepaper.

Produces REAL, measured numbers for every quantitative claim in
``docs/generate_tesseract_cube_whitepaper.py``. No hand-entered values:
each figure in the paper is read out of this artifact, mirroring the
honesty contract used by ``experiments/sigma0_real_data_grounding.py``.

It exercises the three committed layers that make up the cube:

  1. base3 codec           src/csf/base3.py            (3^12 positional encoding)
  2. QuantumDustField      src/csf/v07/quantum_dust.py (the latent universe)
  3. StatusCube            src/csf/status_cube.py      (a player's persisted cube)

Pipeline: encode → observe → converge → persist → round-trip → measure.

Reproducible: deterministic (fixed door-choice pattern, no RNG, no network).
Run:
    python experiments/sigma0_tesseract_cube_grounding.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
for p in (_ROOT, _ROOT / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from csf import base3
from csf.v07.quantum_dust import QuantumDustField
from csf.v07.qutrit_delta import QutritDelta
from csf.status_cube import StatusCube, NUM_STAGES

ARTIFACT = _ROOT / "data" / "sigma0_tesseract_cube_report.json"


# ── Layer 1: base3 codec (REAL) ──────────────────────────────────────────────

def measure_base3() -> dict:
    """Measure absolute/delta record sizes and exhaustive neighbor roundtrip."""
    total = base3.TOTAL_POSITIONS  # 3**12

    # Absolute record sizes across the three payload bands.
    sizes = {}
    for label, coords in (
        ("origin", (0,) * 12),                       # scalar 0      → 1-byte band
        ("mid", base3._from_scalar(40000)),          # scalar 40000  → 2-byte band
        ("max", base3._from_scalar(total - 1)),      # scalar 531440 → 3-byte band
    ):
        sizes[label] = {
            "scalar": base3._to_scalar(coords),
            "abs_bytes": len(base3.encode_absolute(coords)),
        }

    # Delta record size: any single-step move.
    center = (1,) * 12
    step = (2,) + (1,) * 11
    delta_bytes = len(base3.encode_delta(step, center))

    # Exhaustive neighbor roundtrip from the center (1,1,...,1):
    # every dimension, both ring directions = 24 transitions.
    codec_ok = True
    transitions = 0
    for dim in range(12):
        for direction in (+1, -1):
            nbr = list(center)
            nbr[dim] = (nbr[dim] + direction) % 3
            nbr = tuple(nbr)
            enc = base3.encode_delta(nbr, center)
            dec, _ = base3.decode_delta(enc, 0, center)
            transitions += 1
            if dec != nbr:
                codec_ok = False

    # Full absolute roundtrip sweep over a deterministic sample of positions.
    abs_ok = True
    for scalar in range(0, total, 4999):  # 107 sample points across the space
        coords = base3._from_scalar(scalar)
        dec, _ = base3.decode_absolute(base3.encode_absolute(coords), 0)
        if dec != coords:
            abs_ok = False

    return {
        "dimensions": base3.DIMENSIONS,
        "total_positions": total,
        "absolute_record_sizes": sizes,
        "delta_record_bytes": delta_bytes,
        "neighbor_transitions_tested": transitions,
        "neighbor_roundtrip_ok": codec_ok,
        "absolute_roundtrip_ok": abs_ok,
    }


# ── Layer 2: QuantumDustField — the latent universe (REAL) ───────────────────

def measure_dust() -> dict:
    """Observe positions, converge via the cluster path, and measure occupancy.

    Note (REAL property, not a tuning choice): with integer qutrit deltas the
    smallest nonzero magnitude is 1.0 — always above the 0.05–0.24 collapse
    thresholds — so a single observation never collapses directly. Convergence
    only reduces the field through the v0.7 cluster-promotion path (similar
    deltas accumulate into a cluster that, at max_cluster_size=64, is promoted
    into the shared baseline). We exercise that real path with similar deltas.
    """
    field = QuantumDustField()
    total = field.total_positions

    # Phase A — observe 130 deterministic positions with *similar* deltas so
    # they cluster (similarity 1.0 ≥ 0.85) and saturate the 64-size cluster.
    n_observed = 130
    positions = [(i * 7919) % total for i in range(n_observed)]
    for pos in positions:
        field.observe(pos, [QutritDelta(dim_index=0, amp_delta=3, phase_delta=1)])

    after_observe = field.stats()

    # Phase B — one-shot multi-level convergence (default 0.24→0.05).
    results = field.converge()
    collapsed = sum(getattr(r, "collapsed", 0) for r in results)
    clustered = sum(getattr(r, "clustered", 0) for r in results)
    promoted = sum(getattr(r, "clusters_promoted", 0) for r in results)
    baseline_growth = sum(getattr(r, "baseline_growth", 0) for r in results)
    after_converge = field.stats()

    # Phase C — re-observe positions now living in the baseline so baseline AND
    # an active delta coexist, then resolve each twice to exercise the v0.7
    # state cache (first lookup misses, second hits).
    baseline_positions = list(field.baseline)
    for pos in baseline_positions:
        field.observe(pos, [QutritDelta(dim_index=1, amp_delta=1, phase_delta=0)])
    for pos in list(field.active_deltas):
        field.get_state(pos)
        field.get_state(pos)
    final = field.stats()

    return {
        "total_positions": int(total),
        "observed_positions": n_observed,
        "dust_percentage_after_observe": round(after_observe["dust_percentage"], 6),
        "active_positions_after_observe": int(after_observe["active_positions"]),
        "min_nonzero_delta_magnitude": 1.0,
        "convergence_levels": [0.24, 0.14, 0.08, 0.05],
        "collapsed_into_baseline": int(collapsed),
        "clustered": int(clustered),
        "clusters_promoted_to_baseline": int(promoted),
        "baseline_growth": int(baseline_growth),
        "baseline_positions_after_converge": int(after_converge["baseline_positions"]),
        "active_positions_after_converge": int(after_converge["active_positions"]),
        "dust_percentage_after_converge": round(after_converge["dust_percentage"], 6),
        "cache_hit_rate_after_rewarm": round(final["cache_hit_rate"], 4),
    }


# ── Layer 3: StatusCube — a player's persisted cube (REAL) ───────────────────

def measure_status_cube() -> dict:
    """Play a deterministic Three Doors game, persist, and round-trip."""
    # Deterministic door pool keyed to the seeker archetype so symbols crystallize.
    doors = [
        "The Storybook Door", "Door of Tomorrow", "The Star Branch",
        "Mirror of Futures", "The Deep Page", "Convergence Gate",
        "Beyond the Veil",
    ]
    n_loops = 12

    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        cube = StatusCube("sigma0-grounding-player", data_dir=data_dir)

        for _ in range(n_loops):
            for stage in range(NUM_STAGES):
                door = doors[stage % len(doors)]
                cube.add_observation(stage=stage, choice="A", door=door,
                                     agent="lantern")
                cube.advance_stage()  # consolidates on loop wrap
        size_bytes = cube.save()

        # Naive baseline: full per-choice history as plain JSON (what the cube avoids).
        naive_history = [
            {"loop": l, "stage": s, "choice": "A",
             "door": doors[s % len(doors)], "agent": "lantern"}
            for l in range(n_loops) for s in range(NUM_STAGES)
        ]
        naive_bytes = len(json.dumps(naive_history).encode("utf-8"))

        # Round-trip: reload from disk and compare consolidated state.
        reloaded = StatusCube.load("sigma0-grounding-player", data_dir=data_dir)
        roundtrip_ok = (
            reloaded.loop_count == cube.loop_count
            and reloaded.stage_index == cube.stage_index
            and set(reloaded.symbols) == set(cube.symbols)
        )

        choices_recorded = n_loops * NUM_STAGES
        return {
            "loops_played": n_loops,
            "stages_per_loop": NUM_STAGES,
            "door_choices_recorded": choices_recorded,
            "loops_consolidated": cube.loop_count,
            "crystallized_symbols": len(cube.symbols),
            "symbol_names": sorted(cube.symbols),
            "dominant_archetype": cube.archetype,
            "loop_history_lines": len(cube.loop_history),
            "csf_file_bytes": size_bytes,
            "naive_json_history_bytes": naive_bytes,
            "compression_ratio": round(naive_bytes / size_bytes, 2) if size_bytes else None,
            "bytes_per_choice": round(size_bytes / choices_recorded, 2),
            "roundtrip_ok": roundtrip_ok,
        }


def main() -> None:
    base3_m = measure_base3()
    dust_m = measure_dust()
    cube_m = measure_status_cube()

    all_ok = (
        base3_m["neighbor_roundtrip_ok"]
        and base3_m["absolute_roundtrip_ok"]
        and cube_m["roundtrip_ok"]
    )

    report = {
        "title": "Σ₀ Tesseract Status Cube — real-data grounding",
        "provenance": {
            "real_inputs": [
                "src/csf/base3.py codec (encode/decode roundtrips)",
                "src/csf/v07/quantum_dust.py QuantumDustField (observe/converge/stats)",
                "src/csf/status_cube.py StatusCube (game loop → persisted .csf)",
            ],
            "designed_choices": [
                "12-loop deterministic Three Doors playthrough (door pool, choice='A')",
                "130 observed dust positions spread by ×7919 stride",
                "naive-JSON baseline as the uncompressed comparison point",
            ],
            "not_claimed": [
                "no real player telemetry — the playthrough is synthetic but deterministic",
                "no cross-format benchmark vs zip/zstd (covered by CSF v0.3 paper)",
            ],
        },
        "base3_codec": base3_m,
        "quantum_dust_field": dust_m,
        "status_cube": cube_m,
        "all_roundtrips_ok": all_ok,
    }

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # ── human-readable summary ──
    print("Σ₀ Tesseract Status Cube grounding")
    print(f"  artifact: {ARTIFACT.relative_to(_ROOT)}")
    print()
    print("  LAYER 1 — base3 codec (3^12 positional encoding):")
    print(f"    total positions        = {base3_m['total_positions']:,}")
    print(f"    delta record           = {base3_m['delta_record_bytes']} bytes")
    print(f"    neighbor roundtrip     = {base3_m['neighbor_transitions_tested']}/24 "
          f"ok={base3_m['neighbor_roundtrip_ok']}")
    print(f"    absolute roundtrip ok  = {base3_m['absolute_roundtrip_ok']}")
    print()
    print("  LAYER 2 — QuantumDustField (latent universe):")
    print(f"    dust % after observe   = {dust_m['dust_percentage_after_observe']}")
    print(f"    clustered / promoted   = {dust_m['clustered']} / "
          f"{dust_m['clusters_promoted_to_baseline']} "
          f"(baseline growth {dust_m['baseline_growth']})")
    print(f"    active after converge  = {dust_m['active_positions_after_converge']}")
    print(f"    cache hit rate (rewarm)= {dust_m['cache_hit_rate_after_rewarm']}")
    print()
    print("  LAYER 3 — StatusCube (persisted player cube):")
    print(f"    choices recorded       = {cube_m['door_choices_recorded']} "
          f"over {cube_m['loops_played']} loops")
    print(f"    crystallized symbols   = {cube_m['crystallized_symbols']} "
          f"{cube_m['symbol_names']}")
    print(f"    dominant archetype     = {cube_m['dominant_archetype']}")
    print(f"    .csf size              = {cube_m['csf_file_bytes']} bytes "
          f"({cube_m['bytes_per_choice']} B/choice)")
    print(f"    vs naive JSON          = {cube_m['naive_json_history_bytes']} bytes "
          f"→ {cube_m['compression_ratio']}× smaller")
    print(f"    roundtrip ok           = {cube_m['roundtrip_ok']}")
    print()
    print(f"  ALL ROUNDTRIPS OK = {all_ok}")


if __name__ == "__main__":
    main()
