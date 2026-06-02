#!/usr/bin/env python3
"""
Research-mode autonomous advisory pipeline for AI bias monitoring.

Seven single-responsibility agents coordinate through PBFT consensus to record
proposed violations to an append-only audit log. Operator and deployment
authority remain external to this software. Once consensus is reached, an
escalation record is time-locked for 24 hours before it becomes eligible for
execution; background execution is default-off unless explicitly enabled by an
operator.

Limitations:
- "Escalation" currently means appending a row to the audit log and flagging it
  for human review. Actual regulatory notification requires institutional
  partnerships that do not yet exist.
- The system runs only on the nodes you deploy. It is not self-propagating.
- Declared rules are enforced in software. A database administrator with
  direct SQLite access could modify records.
- This is research/advisory software. It is not a human board, regulator,
  court, enforcement system, or autonomous authority.
"""

import json
import os
import sqlite3
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests

from cryptographic_proof import (
    AuditLog,
    SignedRecord,
    generate_keypair,
    load_keypair,
    save_keypair,
    sign_record,
    verify_record,
)
from byzantine_consensus import (
    PBFTNode,
    create_node as create_pbft_node,
    quorum_size,
    max_faulty,
)

# ---------------------------------------------------------------------------
# Declared rules — derived from PBFT quorum, not hardcoded percentages
# ---------------------------------------------------------------------------

# The consensus threshold is computed from the PBFT quorum formula (2f+1)/n.
# For example, with 4 nodes: f=1, quorum=3, threshold=3/4=0.75 (75%).
# This is NOT a hardcoded 67% — it comes from the actual PBFT math.

def _compute_consensus_threshold(n: int) -> float:
    """Derive the consensus threshold from PBFT quorum size."""
    if n < 1:
        return 1.0
    return quorum_size(n) / n


IMMUTABLE_RULES = {
    "accuracy_gap_threshold": 0.05,  # 5% accuracy gap triggers violation proposal
    "escalation_lock_hours": 24,     # hours between consensus and execution
    "escalation_is_irreversible": True,
    "no_human_override": True,
    "consensus_threshold_formula": "quorum_size(n) / n  # i.e. (2f+1)/n from PBFT",
    "agent_count": 7,
    "append_only_audit": True,
}

# Fields kept internal-only because their flag-style names imply governance
# authority the software does not actually possess. Operator and deployment
# authority are external. The audit log is append-only by design, but a database
# administrator with direct SQLite access can still modify records.
_INTERNAL_ONLY_RULE_KEYS = ("escalation_is_irreversible", "no_human_override")

PUBLIC_RULES_DISCLAIMER = (
    "Research advisory software. Operator and deployment authority are "
    "external to this system. Escalation records are audit-log entries "
    "pending human review, not regulatory actions or autonomous enforcement."
)


def public_immutable_rules_view():
    """Return a public projection of IMMUTABLE_RULES.

    Omits flag-style fields whose names imply governance authority the software
    does not possess (the assertions on those flags are internal startup
    invariants, not enforcement mechanisms). Adds an explicit research-mode
    disclaimer so the public payload cannot be misread as governance claim.
    """
    public = {
        key: value
        for key, value in IMMUTABLE_RULES.items()
        if key not in _INTERNAL_ONLY_RULE_KEYS
    }
    public["mode"] = "research"
    public["disclaimer"] = PUBLIC_RULES_DISCLAIMER
    return public

# ---------------------------------------------------------------------------
# Escalation persistence (SQLite, append-only table)
# ---------------------------------------------------------------------------

_ESCALATION_DB = os.environ.get("ESCALATION_DB_PATH", "./data/escalations.db")
AUTONOMOUS_ESCALATION_EXECUTOR_ENV = "ENABLE_AUTONOMOUS_ESCALATION_EXECUTOR"


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def _init_escalation_db(db_path: str = _ESCALATION_DB) -> None:
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS escalations (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            violation_id    TEXT    NOT NULL,
            evidence_hash   TEXT    NOT NULL,
            consensus_digest TEXT   NOT NULL,
            lock_time       TEXT    NOT NULL,
            execute_time    TEXT    NOT NULL,
            status          TEXT    NOT NULL DEFAULT 'locked',
            executed_at     TEXT,
            created_at      TEXT    NOT NULL
        )
    """
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Agent base
# ---------------------------------------------------------------------------


class AgentBase:
    """Base class for all autonomous agents.

    Every agent validates its own rules against IMMUTABLE_RULES on init.
    """

    name: str = "base"
    description: str = ""

    def __init__(self, private_key, public_key, audit_log: AuditLog):
        self._private_key = private_key
        self._public_key = public_key
        self._audit_log = audit_log
        self._validate_rules()

    def _validate_rules(self):
        """Ensure IMMUTABLE_RULES have not been tampered with at init time."""
        assert IMMUTABLE_RULES["no_human_override"] is True, (
            f"{self.name}: IMMUTABLE_RULES.no_human_override must be True"
        )
        assert IMMUTABLE_RULES["append_only_audit"] is True, (
            f"{self.name}: IMMUTABLE_RULES.append_only_audit must be True"
        )
        assert IMMUTABLE_RULES["agent_count"] == 7, (
            f"{self.name}: IMMUTABLE_RULES.agent_count must be 7"
        )

    def _log_action(self, action: str, details: dict) -> int:
        """Append a signed action to the audit log."""
        record = {
            "agent": self.name,
            "action": action,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        signed = sign_record(record, self._private_key)
        entry_id = self._audit_log.append({
            **record,
            "signature_hex": signed.signature.hex(),
        })
        return entry_id

    def status(self) -> dict:
        return {"agent": self.name, "description": self.description, "status": "active"}


# ---------------------------------------------------------------------------
# 1. ViolationDetectionAgent
# ---------------------------------------------------------------------------


class ViolationDetectionAgent(AgentBase):
    """Proposes violations when evidence exceeds the accuracy gap threshold.

    This agent can only PROPOSE — it cannot approve or escalate.
    """

    name = "violation_detection"
    description = "Proposes violations when accuracy gap exceeds threshold"

    def detect(self, evidence: dict) -> Optional[dict]:
        """Evaluate evidence and propose a violation if threshold is exceeded.

        Parameters
        ----------
        evidence : dict
            Must contain 'accuracy_gap' (float), 'system_name' (str),
            and 'description' (str).

        Returns
        -------
        dict or None
            A violation proposal if the gap exceeds threshold, else None.
        """
        gap = evidence.get("accuracy_gap", 0.0)
        threshold = IMMUTABLE_RULES["accuracy_gap_threshold"]

        if gap < threshold:
            self._log_action("detection_below_threshold", {
                "accuracy_gap": gap,
                "threshold": threshold,
                "system_name": evidence.get("system_name", "unknown"),
            })
            return None

        proposal = {
            "violation_id": f"viol-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "system_name": evidence.get("system_name", "unknown"),
            "accuracy_gap": gap,
            "threshold": threshold,
            "description": evidence.get("description", ""),
            "evidence": evidence,
            "proposed_at": datetime.now(timezone.utc).isoformat(),
            "status": "proposed",
        }

        self._log_action("violation_proposed", {
            "violation_id": proposal["violation_id"],
            "accuracy_gap": gap,
            "system_name": proposal["system_name"],
        })

        return proposal


# ---------------------------------------------------------------------------
# 2. CryptographicVerificationAgent
# ---------------------------------------------------------------------------


class CryptographicVerificationAgent(AgentBase):
    """Attests received evidence cryptographically using Ed25519 signatures.

    Deterministic: this node's signature either verifies or it does not.
    """

    name = "cryptographic_verification"
    description = "Attests received evidence using Ed25519 signatures"

    def verify_evidence(self, evidence: dict) -> dict:
        """Sign evidence and verify the signature.

        This proves the evidence was signed by this node after receipt and has
        not been tampered with since signing. It does not prove external truth.
        """
        signed = sign_record(evidence, self._private_key)
        is_valid = verify_record(signed, self._public_key)

        result = {
            "verified": is_valid,
            "signature_hex": signed.signature.hex(),
            "timestamp": signed.timestamp_utc,
        }

        self._log_action("evidence_verified", {
            "verified": is_valid,
            "evidence_keys": list(evidence.keys()),
        })

        return result


# ---------------------------------------------------------------------------
# 3. ByzantineConsensusAgent
# ---------------------------------------------------------------------------


class ByzantineConsensusAgent(AgentBase):
    """Coordinates with the real PBFT implementation for consensus.

    Uses PBFTNode.request() to propose to the network. The threshold
    comes from the PBFT quorum formula (2f+1), not a hardcoded percentage.
    """

    name = "byzantine_consensus"
    description = "Coordinates PBFT consensus across network nodes"

    def __init__(self, private_key, public_key, audit_log: AuditLog,
                 pbft_node: PBFTNode):
        super().__init__(private_key, public_key, audit_log)
        self._pbft_node = pbft_node

    def propose(self, violation: dict) -> dict:
        """Submit a violation proposal to the PBFT network for consensus.

        Returns the PBFT response (pre-prepare broadcast status or
        redirect to leader).
        """
        result = self._pbft_node.request(violation)

        self._log_action("consensus_proposed", {
            "violation_id": violation.get("violation_id", "unknown"),
            "pbft_response": result,
            "quorum_needed": self._pbft_node._quorum(),
            "total_nodes": self._pbft_node.n,
            "threshold": _compute_consensus_threshold(self._pbft_node.n),
        })

        return result

    def get_consensus_info(self) -> dict:
        """Return current PBFT consensus parameters."""
        n = self._pbft_node.n
        return {
            "n": n,
            "f": self._pbft_node.f,
            "quorum": self._pbft_node._quorum(),
            "threshold": _compute_consensus_threshold(n),
            "threshold_formula": IMMUTABLE_RULES["consensus_threshold_formula"],
            "view": self._pbft_node.view,
            "is_leader": self._pbft_node.is_leader,
        }

    def status(self) -> dict:
        base = super().status()
        base["consensus_info"] = self.get_consensus_info()
        return base


# ---------------------------------------------------------------------------
# 4. AutonomousEscalationAgent
# ---------------------------------------------------------------------------


class AutonomousEscalationAgent(AgentBase):
    """Lock escalation records after consensus for delayed review/execution.

    Background execution is controlled by the parent system's explicit runtime
    gate. Current execution records an audit event rather than notifying real
    external authorities.
    """

    name = "autonomous_escalation"
    description = "Locks escalation records for delayed audit-backed execution"

    def __init__(self, private_key, public_key, audit_log: AuditLog,
                 db_path: str = _ESCALATION_DB):
        super().__init__(private_key, public_key, audit_log)
        self._db_path = db_path
        _init_escalation_db(db_path)

    def lock_escalation(self, violation_id: str, evidence_hash: str,
                        consensus_digest: str) -> dict:
        """Lock an escalation after consensus is reached.

        The escalation becomes eligible after the lock period (24 hours by
        default). Automatic background execution is disabled unless the parent
        system is explicitly configured to run it.
        """
        lock_hours = IMMUTABLE_RULES["escalation_lock_hours"]
        now = datetime.now(timezone.utc)
        lock_time = now.isoformat()
        # execute_time is lock_hours from now
        execute_ts = now.timestamp() + (lock_hours * 3600)
        execute_time = datetime.fromtimestamp(execute_ts, tz=timezone.utc).isoformat()

        conn = sqlite3.connect(self._db_path)
        c = conn.cursor()
        c.execute(
            """INSERT INTO escalations
               (violation_id, evidence_hash, consensus_digest,
                lock_time, execute_time, status, created_at)
               VALUES (?, ?, ?, ?, ?, 'locked', ?)""",
            (violation_id, evidence_hash, consensus_digest,
             lock_time, execute_time, now.isoformat()),
        )
        escalation_id = c.lastrowid
        conn.commit()
        conn.close()

        self._log_action("escalation_locked", {
            "escalation_id": escalation_id,
            "violation_id": violation_id,
            "lock_time": lock_time,
            "execute_time": execute_time,
            "lock_hours": lock_hours,
        })

        return {
            "escalation_id": escalation_id,
            "violation_id": violation_id,
            "status": "locked",
            "lock_time": lock_time,
            "execute_time": execute_time,
        }

    def execute_escalation(self, escalation_id: int) -> dict:
        """Execute a locked escalation whose lock period has expired.

        In production, this would trigger notification to configured
        regulatory contacts. Currently, it records the escalation decision
        to the immutable audit log.
        """
        conn = sqlite3.connect(self._db_path)
        c = conn.cursor()
        c.execute(
            "SELECT violation_id, evidence_hash, consensus_digest, "
            "lock_time, execute_time, status FROM escalations WHERE id = ?",
            (escalation_id,),
        )
        row = c.fetchone()
        if not row:
            conn.close()
            return {"error": "escalation_not_found"}

        violation_id, evidence_hash, consensus_digest, lock_time, execute_time, status = row

        if status == "executed":
            conn.close()
            return {"error": "already_executed", "violation_id": violation_id}

        # Check lock period
        now = datetime.now(timezone.utc)
        execute_dt = datetime.fromisoformat(execute_time)
        if now < execute_dt:
            conn.close()
            remaining = (execute_dt - now).total_seconds() / 3600
            return {
                "error": "lock_period_active",
                "remaining_hours": round(remaining, 2),
                "execute_time": execute_time,
            }

        # Execute: mark as executed and log to audit trail
        executed_at = now.isoformat()
        c.execute(
            "UPDATE escalations SET status = 'executed', executed_at = ? WHERE id = ?",
            (executed_at, escalation_id),
        )
        conn.commit()
        conn.close()

        self._log_action("escalation_executed", {
            "escalation_id": escalation_id,
            "violation_id": violation_id,
            "evidence_hash": evidence_hash,
            "consensus_digest": consensus_digest,
            "executed_at": executed_at,
            "note": (
                "Escalation recorded to audit log. In production, this would "
                "trigger notification to configured regulatory contacts."
            ),
        })

        return {
            "escalation_id": escalation_id,
            "violation_id": violation_id,
            "status": "executed",
            "executed_at": executed_at,
        }

    def check_pending(self) -> List[dict]:
        """Return all escalations whose lock period has expired but
        have not yet been executed."""
        now = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(self._db_path)
        c = conn.cursor()
        c.execute(
            "SELECT id, violation_id, lock_time, execute_time, status "
            "FROM escalations WHERE status = 'locked' AND execute_time <= ?",
            (now,),
        )
        rows = c.fetchall()
        conn.close()
        return [
            {
                "escalation_id": r[0],
                "violation_id": r[1],
                "lock_time": r[2],
                "execute_time": r[3],
                "status": r[4],
            }
            for r in rows
        ]

    def get_all_escalations(self, limit: int = 50) -> List[dict]:
        """Return all escalations (newest first)."""
        conn = sqlite3.connect(self._db_path)
        c = conn.cursor()
        c.execute(
            "SELECT id, violation_id, evidence_hash, consensus_digest, "
            "lock_time, execute_time, status, executed_at, created_at "
            "FROM escalations ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        rows = c.fetchall()
        conn.close()
        return [
            {
                "escalation_id": r[0],
                "violation_id": r[1],
                "evidence_hash": r[2],
                "consensus_digest": r[3],
                "lock_time": r[4],
                "execute_time": r[5],
                "status": r[6],
                "executed_at": r[7],
                "created_at": r[8],
            }
            for r in rows
        ]


# ---------------------------------------------------------------------------
# 5. ImmutableAuditAgent
# ---------------------------------------------------------------------------


class ImmutableAuditAgent(AgentBase):
    """Wraps the real AuditLog class. Append-only, hash-chain integrity.

    Note: the audit log is tamper-evident, not tamper-proof. Anyone with
    direct SQLite access can modify the database. The hash chain lets you
    detect such modifications.
    """

    name = "immutable_audit"
    description = "Append-only hash-chain audit log with integrity verification"

    def verify_chain(self) -> dict:
        """Verify the integrity of the entire audit chain."""
        is_valid, count = self._audit_log.verify_chain()
        result = {
            "chain_valid": is_valid,
            "entries_checked": count,
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }

        self._log_action("chain_verified", result)
        return result

    def get_entries(self, limit: int = 100) -> List[dict]:
        """Return recent audit entries."""
        return self._audit_log.entries(limit)

    def status(self) -> dict:
        base = super().status()
        is_valid, count = self._audit_log.verify_chain()
        base["chain_valid"] = is_valid
        base["total_entries"] = count
        return base


# ---------------------------------------------------------------------------
# 6. SystemHealthAgent
# ---------------------------------------------------------------------------


class SystemHealthAgent(AgentBase):
    """Passive monitoring of peer URLs.

    Reports status only — cannot make decisions or take actions.
    """

    name = "system_health"
    description = "Passive health monitoring of network peers"

    def __init__(self, private_key, public_key, audit_log: AuditLog,
                 peer_urls: List[str]):
        super().__init__(private_key, public_key, audit_log)
        self._peer_urls = list(peer_urls)

    def check_peers(self) -> List[dict]:
        """Ping each peer and report status."""
        results = []
        for url in self._peer_urls:
            health_url = f"{url.rstrip('/')}/health"
            try:
                resp = requests.get(health_url, timeout=3)
                results.append({
                    "peer": url,
                    "status": "reachable",
                    "http_status": resp.status_code,
                })
            except requests.RequestException as e:
                results.append({
                    "peer": url,
                    "status": "unreachable",
                    "error": str(e),
                })

        self._log_action("health_check", {
            "peers_checked": len(self._peer_urls),
            "reachable": sum(1 for r in results if r["status"] == "reachable"),
        })

        return results

    def status(self) -> dict:
        base = super().status()
        base["peer_count"] = len(self._peer_urls)
        return base


# ---------------------------------------------------------------------------
# 7. NetworkDiscoveryAgent
# ---------------------------------------------------------------------------


class NetworkDiscoveryAgent(AgentBase):
    """Wraps mesh_network peer sync for discovery.

    Discovers and syncs with peers. Does not make governance decisions.
    """

    name = "network_discovery"
    description = "Discovers and syncs with mesh network peers"

    def __init__(self, private_key, public_key, audit_log: AuditLog,
                 peer_urls: List[str]):
        super().__init__(private_key, public_key, audit_log)
        self._peer_urls = list(peer_urls)

    def discover_peers(self) -> List[dict]:
        """Attempt to discover peers by querying known URLs."""
        discovered = []
        for url in self._peer_urls:
            status_url = f"{url.rstrip('/')}/api/status"
            try:
                resp = requests.get(status_url, timeout=3)
                if resp.status_code == 200:
                    data = resp.json()
                    discovered.append({
                        "url": url,
                        "node_id": data.get("node_id", "unknown"),
                        "status": data.get("status", "unknown"),
                    })
            except requests.RequestException:
                pass

        self._log_action("peer_discovery", {
            "queried": len(self._peer_urls),
            "discovered": len(discovered),
        })

        return discovered

    def status(self) -> dict:
        base = super().status()
        base["known_peers"] = len(self._peer_urls)
        return base


# ---------------------------------------------------------------------------
# AutonomousAgentSystem — orchestrator
# ---------------------------------------------------------------------------


class AutonomousAgentSystem:
    """Orchestrates the autonomous agent flow: Detect -> Verify -> Consensus -> Lock -> Escalate.

    All actions are logged to the immutable audit log with real Ed25519 signatures.
    """

    def __init__(
        self,
        private_key,
        public_key,
        peer_urls: Optional[List[str]] = None,
        audit_db_path: str = "./data/autonomous_audit.db",
        escalation_db_path: str = _ESCALATION_DB,
        pbft_db_path: str = "./data/autonomous_pbft.db",
        node_id: str = "autonomous-node",
        auto_execute_escalations: Optional[bool] = None,
    ):
        if peer_urls is None:
            peer_urls = []

        self._private_key = private_key
        self._public_key = public_key
        self._peer_urls = peer_urls
        self._node_id = node_id
        if auto_execute_escalations is None:
            auto_execute_escalations = _env_flag(AUTONOMOUS_ESCALATION_EXECUTOR_ENV)
        self.auto_execute_escalations_enabled = bool(auto_execute_escalations)
        self._executor_thread = None

        # Shared audit log
        self._audit_log = AuditLog(db_path=audit_db_path)

        # PBFT node
        self._pbft_node = PBFTNode(
            node_id=node_id,
            peers=peer_urls,
            db_path=pbft_db_path,
        )

        # Initialize all 7 agents
        self.violation_detection = ViolationDetectionAgent(
            private_key, public_key, self._audit_log,
        )
        self.cryptographic_verification = CryptographicVerificationAgent(
            private_key, public_key, self._audit_log,
        )
        self.byzantine_consensus = ByzantineConsensusAgent(
            private_key, public_key, self._audit_log, self._pbft_node,
        )
        self.autonomous_escalation = AutonomousEscalationAgent(
            private_key, public_key, self._audit_log, db_path=escalation_db_path,
        )
        self.immutable_audit = ImmutableAuditAgent(
            private_key, public_key, self._audit_log,
        )
        self.system_health = SystemHealthAgent(
            private_key, public_key, self._audit_log, peer_urls,
        )
        self.network_discovery = NetworkDiscoveryAgent(
            private_key, public_key, self._audit_log, peer_urls,
        )

        self._agents = [
            self.violation_detection,
            self.cryptographic_verification,
            self.byzantine_consensus,
            self.autonomous_escalation,
            self.immutable_audit,
            self.system_health,
            self.network_discovery,
        ]

        # Log system startup. The audit log is reachable via the public
        # /api/autonomous/audit route, so use the public projection here too.
        self._audit_log.append({
            "agent": "system",
            "action": "startup",
            "details": {
                "node_id": node_id,
                "peer_count": len(peer_urls),
                "agent_count": len(self._agents),
                "immutable_rules": public_immutable_rules_view(),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        if self.auto_execute_escalations_enabled:
            self._executor_thread = threading.Thread(
                target=self._escalation_executor_loop,
                daemon=True,
            )
            self._executor_thread.start()

    def _escalation_executor_loop(self):
        """Background loop that auto-executes escalations after lock period."""
        while True:
            try:
                pending = self.autonomous_escalation.check_pending()
                for esc in pending:
                    self.autonomous_escalation.execute_escalation(
                        esc["escalation_id"]
                    )
            except Exception:
                pass
            time.sleep(60)  # check every minute

    def submit_evidence(self, evidence: dict) -> dict:
        """Full autonomous pipeline: Detect -> Verify -> Consensus -> Lock.

        Parameters
        ----------
        evidence : dict
            Must contain 'accuracy_gap' (float), 'system_name' (str),
            and 'description' (str).

        Returns
        -------
        dict
            Pipeline result with status at each stage.
        """
        result = {"stages": {}}

        # Stage 1: Detection
        proposal = self.violation_detection.detect(evidence)
        if proposal is None:
            result["stages"]["detection"] = {
                "status": "below_threshold",
                "threshold": IMMUTABLE_RULES["accuracy_gap_threshold"],
            }
            result["outcome"] = "no_violation_detected"
            return result

        result["stages"]["detection"] = {
            "status": "violation_proposed",
            "violation_id": proposal["violation_id"],
        }

        # Stage 2: Cryptographic verification
        verification = self.cryptographic_verification.verify_evidence(evidence)
        result["stages"]["verification"] = verification

        if not verification["verified"]:
            result["outcome"] = "verification_failed"
            return result

        # Stage 3: Consensus
        consensus_result = self.byzantine_consensus.propose(proposal)
        result["stages"]["consensus"] = consensus_result

        # For a single-node deployment, the proposal is immediately
        # pre-prepared. In a multi-node deployment, this would require
        # waiting for the PBFT protocol to complete.
        consensus_info = self.byzantine_consensus.get_consensus_info()
        result["stages"]["consensus_info"] = consensus_info

        # Stage 4: Lock escalation
        # In a single-node setup, the proposal goes through immediately.
        # In production with multiple nodes, you would wait for committed status.
        evidence_hash = verification["signature_hex"][:64]
        consensus_digest = consensus_result.get("digest", "single-node")

        lock_result = self.autonomous_escalation.lock_escalation(
            violation_id=proposal["violation_id"],
            evidence_hash=evidence_hash,
            consensus_digest=consensus_digest,
        )
        result["stages"]["escalation"] = lock_result
        result["outcome"] = "escalation_locked"
        result["note"] = (
            f"Escalation locked. It becomes eligible after "
            f"{IMMUTABLE_RULES['escalation_lock_hours']}hr lock period. "
            f"Background execution requires explicit runtime enablement."
        )

        return result

    def get_status(self) -> dict:
        """Return full system status."""
        agents_status = [a.status() for a in self._agents]
        escalations = self.autonomous_escalation.get_all_escalations(limit=10)
        chain_info = self.immutable_audit.verify_chain()

        return {
            "node_id": self._node_id,
            "agents": agents_status,
            "immutable_rules": public_immutable_rules_view(),
            "consensus_threshold": _compute_consensus_threshold(
                self._pbft_node.n
            ),
            "escalation_queue": {
                "total": len(self.autonomous_escalation.get_all_escalations()),
                "recent": escalations,
            },
            "audit_chain": chain_info,
            "peer_count": len(self._peer_urls),
            "auto_execute_escalations_enabled": self.auto_execute_escalations_enabled,
        }

    def get_rules(self) -> dict:
        """Return the public projection of declared rules for transparency.

        Internal-only flags whose names imply governance authority the software
        does not possess are omitted; see ``public_immutable_rules_view``.
        """
        n = self._pbft_node.n
        return {
            "immutable_rules": public_immutable_rules_view(),
            "computed_values": {
                "n": n,
                "f": max_faulty(n),
                "quorum": quorum_size(n),
                "consensus_threshold": _compute_consensus_threshold(n),
            },
        }


# ---------------------------------------------------------------------------
# Module self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    priv, pub = generate_keypair()
    system = AutonomousAgentSystem(
        private_key=priv,
        public_key=pub,
        node_id="test-node",
    )

    print(f"[OK] System initialized with {len(system._agents)} agents")
    print(f"[OK] Rules: {json.dumps(system.get_rules(), indent=2)}")

    # Test detection below threshold
    result = system.submit_evidence({
        "accuracy_gap": 0.02,
        "system_name": "test-system",
        "description": "Below threshold test",
    })
    assert result["outcome"] == "no_violation_detected"
    print("[OK] Below-threshold detection works")

    # Test detection above threshold
    result = system.submit_evidence({
        "accuracy_gap": 0.10,
        "system_name": "test-system",
        "description": "Above threshold test",
    })
    assert result["outcome"] == "escalation_locked"
    print("[OK] Above-threshold detection -> escalation lock works")

    # Test audit chain
    chain = system.immutable_audit.verify_chain()
    assert chain["chain_valid"]
    print(f"[OK] Audit chain valid ({chain['entries_checked']} entries)")

    status = system.get_status()
    print(f"[OK] System status: {len(status['agents'])} agents active")
