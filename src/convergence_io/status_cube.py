"""
StatusCube — 4D navigation matrix for Lantern OS convergence state.

Axes:
  x: location   — repo, apps, skills, scripts, docs, archive, data, surfaces
  y: lane       — control, report, dollhouse, wallet, device, product
  z: boundary   — proven, candidate, held, blocked
  t: timeline   — evidence_receipt, validation_history, next_check

Usage:
    cube = StatusCube.load()          # from data/status-cube.json
    cube.place("apps/lantern-garage", x="apps", y="product", z="proven")
    cube.project("apps/lantern-garage", horizon="1w")
    cube.update_beliefs()
    cube.save()
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PATH = REPO_ROOT / "data" / "status-cube.json"


class Location(Enum):
    REPO = "repo"
    APPS = "apps"
    SKILLS = "skills"
    SCRIPTS = "scripts"
    DOCS = "docs"
    ARCHIVE = "archive"
    DATA = "data"
    SURFACES = "surfaces"
    INTEGRATIONS = "integrations"


class Lane(Enum):
    CONTROL = "control"
    REPORT = "report"
    DOLLHOUSE = "dollhouse"
    WALLET = "wallet"
    DEVICE = "device"
    PRODUCT = "product"


class Boundary(Enum):
    PROVEN = "proven"
    CANDIDATE = "candidate"
    HELD = "held"
    BLOCKED = "blocked"


class BeliefDimension(Enum):
    HEALTH = "health"
    ANIMAL = "animal"
    ECOSYSTEM = "ecosystem"
    ECONOMY = "economy"
    CULTURE = "culture"


@dataclass
class StatusCoordinate:
    x: str  # location.value
    y: str  # lane.value
    z: str  # boundary.value
    t: str = ""  # timeline marker (ISO date or phase id)

    def key(self) -> str:
        return f"{self.x}:{self.y}:{self.z}:{self.t}"

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, str]) -> StatusCoordinate:
        return cls(x=d["x"], y=d["y"], z=d["z"], t=d.get("t", ""))


@dataclass
class TimelineEntry:
    phase: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    evidence_id: str = ""
    validator: str = ""  # alpha, beta, gamma, delta, epsilon
    result: str = ""  # pass, fail, partial

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> TimelineEntry:
        return cls(**d)


@dataclass
class StatusArtifact:
    artifact_id: str
    path: str
    coordinate: StatusCoordinate
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    owner: str = ""
    description: str = ""
    timeline: List[TimelineEntry] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "path": self.path,
            "coordinate": self.coordinate.to_dict(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "owner": self.owner,
            "description": self.description,
            "timeline": [e.to_dict() for e in self.timeline],
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> StatusArtifact:
        return cls(
            artifact_id=d["artifact_id"],
            path=d["path"],
            coordinate=StatusCoordinate.from_dict(d["coordinate"]),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            owner=d.get("owner", ""),
            description=d.get("description", ""),
            timeline=[TimelineEntry.from_dict(e) for e in d.get("timeline", [])],
            tags=d.get("tags", []),
            metadata=d.get("metadata", {}),
        )

    def add_evidence(self, phase: str, evidence_id: str = "", validator: str = "", result: str = "") -> None:
        self.timeline.append(TimelineEntry(phase=phase, evidence_id=evidence_id, validator=validator, result=result))
        self.updated_at = datetime.now(timezone.utc).isoformat()


@dataclass
class BayesianBelief:
    dimension: str
    prior: float = 0.5
    evidence_count: int = 0
    success_count: int = 0
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sensors: List[str] = field(default_factory=list)

    def update(self, success: bool, weight: float = 1.0) -> None:
        """Bayesian posterior update with Beta(prior, evidence_count) prior."""
        alpha = self.prior * self.evidence_count + 1.0
        beta = (1.0 - self.prior) * self.evidence_count + 1.0
        if success:
            alpha += weight
            self.success_count += 1
        else:
            beta += weight
        self.prior = alpha / (alpha + beta)
        self.evidence_count += 1
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def confidence(self) -> float:
        """Return 95% credible interval width as uncertainty metric."""
        if self.evidence_count < 2:
            return 1.0
        alpha = self.prior * self.evidence_count + 1.0
        beta_val = (1.0 - self.prior) * self.evidence_count + 1.0
        # Simplified: variance of Beta distribution
        variance = (alpha * beta_val) / ((alpha + beta_val) ** 2 * (alpha + beta_val + 1))
        return 1.0 - min(1.0, 4.0 * math.sqrt(variance))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "posterior": round(self.prior, 4),
            "evidence_count": self.evidence_count,
            "success_count": self.success_count,
            "confidence": round(self.confidence(), 4),
            "last_updated": self.last_updated,
            "sensors": self.sensors,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> BayesianBelief:
        b = cls(
            dimension=d["dimension"],
            prior=d.get("posterior", 0.5),
            evidence_count=d.get("evidence_count", 0),
            success_count=d.get("success_count", 0),
            last_updated=d.get("last_updated", ""),
            sensors=d.get("sensors", []),
        )
        return b


@dataclass
class FutureState:
    artifact_id: str
    projected_coordinate: StatusCoordinate
    horizon: str  # 1d, 1w, 1m, 3m
    confidence: float = 0.0
    rationale: str = ""
    projected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "projected_coordinate": self.projected_coordinate.to_dict(),
            "horizon": self.horizon,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "projected_at": self.projected_at,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> FutureState:
        return cls(
            artifact_id=d["artifact_id"],
            projected_coordinate=StatusCoordinate.from_dict(d["projected_coordinate"]),
            horizon=d["horizon"],
            confidence=d.get("confidence", 0.0),
            rationale=d.get("rationale", ""),
            projected_at=d.get("projected_at", ""),
        )


class StatusCube:
    """4D Status Cube — stores, navigates, and projects Lantern OS state."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or DEFAULT_PATH
        self.artifacts: Dict[str, StatusArtifact] = {}
        self.beliefs: Dict[str, BayesianBelief] = {}
        self.futures: List[FutureState] = []
        self.last_navigated: str = ""

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema": "lantern.status_cube.v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "artifacts": {k: v.to_dict() for k, v in self.artifacts.items()},
            "beliefs": {k: v.to_dict() for k, v in self.beliefs.items()},
            "futures": [f.to_dict() for f in self.futures],
            "last_navigated": self.last_navigated,
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Optional[Path] = None) -> StatusCube:
        p = path or DEFAULT_PATH
        cube = cls(path=p)
        if not p.exists():
            # Seed with default beliefs
            for dim in BeliefDimension:
                cube.beliefs[dim.value] = BayesianBelief(
                    dimension=dim.value,
                    sensors=_default_sensors(dim.value),
                )
            return cube
        data = json.loads(p.read_text(encoding="utf-8"))
        cube.artifacts = {
            k: StatusArtifact.from_dict(v)
            for k, v in data.get("artifacts", {}).items()
        }
        cube.beliefs = {
            k: BayesianBelief.from_dict(v)
            for k, v in data.get("beliefs", {}).items()
        }
        cube.futures = [FutureState.from_dict(f) for f in data.get("futures", [])]
        cube.last_navigated = data.get("last_navigated", "")
        return cube

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def place(self, artifact_id: str, path: str = "", x: str = "", y: str = "", z: str = "", t: str = "",
              owner: str = "", description: str = "", tags: Optional[List[str]] = None,
              metadata: Optional[Dict[str, Any]] = None) -> StatusArtifact:
        """Place or move an artifact to a coordinate in the cube."""
        if artifact_id in self.artifacts:
            art = self.artifacts[artifact_id]
            if x:
                art.coordinate.x = x
            if y:
                art.coordinate.y = y
            if z:
                art.coordinate.z = z
            if t:
                art.coordinate.t = t
            if path:
                art.path = path
            if description:
                art.description = description
            if tags:
                art.tags = list(set(art.tags + tags))
            if metadata:
                art.metadata.update(metadata)
            art.updated_at = datetime.now(timezone.utc).isoformat()
        else:
            art = StatusArtifact(
                artifact_id=artifact_id,
                path=path or artifact_id,
                coordinate=StatusCoordinate(x=x or "repo", y=y or "control", z=z or "candidate", t=t or ""),
                owner=owner,
                description=description,
                tags=tags or [],
                metadata=metadata or {},
            )
            self.artifacts[artifact_id] = art
        return art

    def at(self, x: Optional[str] = None, y: Optional[str] = None,
           z: Optional[str] = None, t: Optional[str] = None) -> List[StatusArtifact]:
        """Query artifacts matching coordinate filters."""
        results = []
        for art in self.artifacts.values():
            c = art.coordinate
            if x is not None and c.x != x:
                continue
            if y is not None and c.y != y:
                continue
            if z is not None and c.z != z:
                continue
            if t is not None and c.t != t:
                continue
            results.append(art)
        return results

    def navigate(self, x: str, y: str, z: str = "", t: str = "") -> Dict[str, Any]:
        """Navigate to a coordinate and return a navigation report."""
        self.last_navigated = f"{x}:{y}:{z}:{t}"
        coords = StatusCoordinate(x=x, y=y, z=z, t=t)
        here = self.at(x=x, y=y, z=z if z else None, t=t if t else None)
        neighbors = {
            "+x": self.at(x=_next_in_enum(Location, x), y=y, z=z if z else None),
            "-x": self.at(x=_prev_in_enum(Location, x), y=y, z=z if z else None),
            "+y": self.at(x=x, y=_next_in_enum(Lane, y), z=z if z else None),
            "-y": self.at(x=x, y=_prev_in_enum(Lane, y), z=z if z else None),
            "+z": self.at(x=x, y=y, z=_next_in_enum(Boundary, z) if z else None),
            "-z": self.at(x=x, y=y, z=_prev_in_enum(Boundary, z) if z else None),
        }
        return {
            "coordinate": coords.key(),
            "artifacts_here": [a.artifact_id for a in here],
            "artifact_count": len(here),
            "neighbors": {k: [a.artifact_id for a in v] for k, v in neighbors.items()},
            "beliefs_at_location": {k: v.to_dict() for k, v in self.beliefs.items()},
        }

    # ------------------------------------------------------------------
    # Future Projection
    # ------------------------------------------------------------------

    def project(self, artifact_id: str, horizon: str = "1w",
                target_z: Optional[str] = None) -> FutureState:
        """Project an artifact's future state based on its timeline and current boundary."""
        art = self.artifacts.get(artifact_id)
        if not art:
            return FutureState(artifact_id=artifact_id, projected_coordinate=StatusCoordinate("", "", ""), horizon=horizon, confidence=0.0, rationale="Artifact not found")

        # Simple heuristic: proven artifacts stay proven; candidates move to proven if evidence > 2
        current_z = art.coordinate.z
        if current_z == "proven":
            next_z = "proven"
            confidence = 0.95
        elif current_z == "candidate":
            evidence_passes = sum(1 for e in art.timeline if e.result == "pass")
            if evidence_passes >= 2:
                next_z = target_z or "proven"
                confidence = 0.7 + 0.1 * evidence_passes
            else:
                next_z = "candidate"
                confidence = 0.4 + 0.1 * evidence_passes
        elif current_z == "held":
            next_z = "candidate"
            confidence = 0.3
        else:
            next_z = "blocked"
            confidence = 0.1

        confidence = min(0.99, confidence)
        proj = FutureState(
            artifact_id=artifact_id,
            projected_coordinate=StatusCoordinate(
                x=art.coordinate.x,
                y=art.coordinate.y,
                z=next_z,
                t=horizon,
            ),
            horizon=horizon,
            confidence=confidence,
            rationale=f"Current boundary={current_z}, evidence_passes={sum(1 for e in art.timeline if e.result == 'pass')}, projected to {next_z}",
        )
        self.futures.append(proj)
        return proj

    def projection_report(self) -> Dict[str, Any]:
        """Summary of all active future projections."""
        by_horizon: Dict[str, List[Dict[str, Any]]] = {}
        for f in self.futures:
            by_horizon.setdefault(f.horizon, []).append(f.to_dict())
        return {
            "total_projections": len(self.futures),
            "by_horizon": by_horizon,
            "avg_confidence": round(sum(f.confidence for f in self.futures) / len(self.futures), 4) if self.futures else 0.0,
        }

    # ------------------------------------------------------------------
    # Bayesian Beliefs
    # ------------------------------------------------------------------

    def update_beliefs(self, observations: Optional[Dict[str, bool]] = None) -> Dict[str, BayesianBelief]:
        """Update all Bayesian beliefs with new observations."""
        if observations:
            for dim, success in observations.items():
                if dim in self.beliefs:
                    self.beliefs[dim].update(success)
        return dict(self.beliefs)

    def belief_report(self) -> Dict[str, Any]:
        """Current Bayesian belief posteriors."""
        return {
            "beliefs": {k: v.to_dict() for k, v in self.beliefs.items()},
            "overall_confidence": round(sum(b.confidence() for b in self.beliefs.values()) / len(self.beliefs), 4) if self.beliefs else 0.0,
            "most_uncertain": min(self.beliefs.values(), key=lambda b: b.confidence()).dimension if self.beliefs else "",
        }

    # ------------------------------------------------------------------
    # Convergence Integration
    # ------------------------------------------------------------------

    def phase_6_navigate(self, target_x: str = "repo", target_y: str = "control") -> Dict[str, Any]:
        """Phase 6: navigate_status_cube."""
        report = self.navigate(target_x, target_y)
        self.save()
        return {
            "phase": "navigate_status_cube",
            "status": "ok",
            "coordinate": report["coordinate"],
            "artifacts_count": report["artifact_count"],
        }

    def phase_7_project(self) -> Dict[str, Any]:
        """Phase 7: project_future_states."""
        for art in self.artifacts.values():
            self.project(art.artifact_id, horizon="1w")
        self.save()
        return {
            "phase": "project_future_states",
            "status": "ok",
            "projections": self.projection_report(),
        }

    def phase_8_update_beliefs(self, observations: Optional[Dict[str, bool]] = None) -> Dict[str, Any]:
        """Phase 8: update_beliefs."""
        self.update_beliefs(observations)
        self.save()
        return {
            "phase": "update_bayesian_beliefs",
            "status": "ok",
            "belief_report": self.belief_report(),
        }

    def full_tesseract_report(self) -> Dict[str, Any]:
        """Complete 4D cube snapshot for convergence receipts."""
        return {
            "schema": "lantern.status_cube.v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "last_navigated": self.last_navigated,
            "artifact_count": len(self.artifacts),
            "artifacts_by_boundary": {
                z.value: len(self.at(z=z.value)) for z in Boundary
            },
            "artifacts_by_lane": {
                y.value: len(self.at(y=y.value)) for y in Lane
            },
            "belief_report": self.belief_report(),
            "projection_report": self.projection_report(),
        }


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _default_sensors(dimension: str) -> List[str]:
    return {
        "health": ["hff_sensors", "hff_api"],
        "animal": ["hff_world_model"],
        "ecosystem": ["hff_integration"],
        "economy": ["wallet_ledger", "cash_loop"],
        "culture": ["lore", "three_doors"],
    }.get(dimension, [])


def _next_in_enum(enum_cls, current: str) -> str:
    members = list(enum_cls)
    vals = [m.value for m in members]
    try:
        idx = vals.index(current)
        return vals[(idx + 1) % len(vals)]
    except ValueError:
        return vals[0] if vals else ""


def _prev_in_enum(enum_cls, current: str) -> str:
    members = list(enum_cls)
    vals = [m.value for m in members]
    try:
        idx = vals.index(current)
        return vals[(idx - 1) % len(vals)]
    except ValueError:
        return vals[-1] if vals else ""


# CLI entry point for direct use and testing
if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="StatusCube CLI")
    p.add_argument("--place", nargs=3, metavar=("ID", "X", "Y"), help="Place artifact: ID X Y")
    p.add_argument("--z", default="candidate", help="Boundary z")
    p.add_argument("--navigate", nargs=2, metavar=("X", "Y"), help="Navigate to X Y")
    p.add_argument("--project", metavar="ID", help="Project future state for ID")
    p.add_argument("--report", action="store_true", help="Print full report")
    p.add_argument("--path", type=Path, default=DEFAULT_PATH, help="Status cube file path")
    args = p.parse_args()

    cube = StatusCube.load(args.path)

    if args.place:
        art_id, x, y = args.place
        cube.place(art_id, x=x, y=y, z=args.z)
        cube.save()
        print(f"[OK] Placed {art_id} at {x}:{y}:{args.z}")

    if args.navigate:
        x, y = args.navigate
        report = cube.navigate(x, y)
        print(json.dumps(report, indent=2))

    if args.project:
        proj = cube.project(args.project)
        cube.save()
        print(json.dumps(proj.to_dict(), indent=2))

    if args.report:
        print(json.dumps(cube.full_tesseract_report(), indent=2))

    if not any([args.place, args.navigate, args.project, args.report]):
        print("No action specified. Use --place, --navigate, --project, or --report")
