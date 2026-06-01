"""
Audit Verification API — FastAPI Service

Exposes the Cryptographic Audit Chain and Anti-Entropy Memory System
for verification, monitoring, and integration with Lantern OS.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from apps.superfleet_memory import (
    CryptographicAuditChain,
    AntiEntropyMemory,
    BayesianFallacyDetector,
    NarrativeIdentity
)

# Initialize FastAPI app
app = FastAPI(
    title="Lantern Audit Verification API",
    description="Cryptographic audit chain and anti-entropy memory system",
    version="0.1.0"
)

# Initialize memory systems
memory = AntiEntropyMemory()
fallacy_detector = BayesianFallacyDetector()
narrative = NarrativeIdentity()


# ========== Pydantic Models ==========

class AuditEntry(BaseModel):
    action: str
    data: dict
    metadata: Optional[dict] = {}


class DreamEntry(BaseModel):
    content: str
    lucidity: float = 0.0
    tags: Optional[List[str]] = []
    emotional_intensity: float = 0.5


class BeliefUpdate(BaseModel):
    key: str
    value: float
    confidence: float
    source: str = "direct"


class FallacyCheckRequest(BaseModel):
    statement: str


class FallacyCheckResponse(BaseModel):
    statement: str
    fallacies: List[Dict]
    hint: Optional[str] = None


# ========== Health & Status ==========

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "audit_chain_valid": memory.verify_integrity()
    }


@app.get("/status")
def get_status():
    """Get system status and statistics."""
    return {
        "timestamp": datetime.now().isoformat(),
        "memory_stats": memory.get_memory_stats(),
        "chain_stats": memory.audit.get_stats(),
        "fallacy_detector": fallacy_detector.get_stats()
    }


# ========== Audit Chain Operations ==========

@app.post("/log")
def log_entry(entry: AuditEntry):
    """Log a new entry to the audit chain."""
    try:
        result = memory.audit.log(entry.action, entry.data, entry.metadata)
        return {
            "status": "success",
            "hash": result["hash"],
            "timestamp": result["timestamp"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/verify")
def verify_chain():
    """Verify the integrity of the audit chain."""
    is_valid = memory.verify_integrity()
    return {
        "valid": is_valid,
        "chain_length": len(memory.audit.chain),
        "last_hash": memory.audit.last_hash,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/public-key")
def get_public_key():
    """Get the public key for verification."""
    return {"public_key": memory.audit.get_public_key_pem()}


@app.get("/export")
def export_chain():
    """Export the full audit chain for backup or external verification."""
    return memory.audit.export_chain()


# ========== Memory Operations ==========

@app.post("/dreams/log")
def log_dream(dream: DreamEntry):
    """Log a dream to episodic memory."""
    try:
        result = memory.log_dream(
            dream.content,
            dream.lucidity,
            dream.tags,
            dream.emotional_intensity
        )
        return {
            "status": "success",
            "hash": result["hash"],
            "timestamp": result["timestamp"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/dreams")
def get_dreams():
    """Get all logged dreams."""
    return {"dreams": memory.episodic}


@app.post("/beliefs/update")
def update_belief(belief: BeliefUpdate):
    """Update a belief in semantic memory."""
    try:
        result = memory.update_belief(
            belief.key,
            belief.value,
            belief.confidence,
            belief.source
        )
        return {
            "status": "success",
            "hash": result["hash"],
            "timestamp": result["timestamp"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/beliefs")
def get_beliefs():
    """Get the current world model (all beliefs)."""
    return memory.get_world_model()


@app.get("/beliefs/{key}")
def get_belief(key: str):
    """Get a specific belief."""
    belief = memory.get_belief(key)
    if not belief:
        raise HTTPException(status_code=404, detail=f"Belief '{key}' not found")
    return belief


@app.get("/coherence")
def get_coherence():
    """Get the memory coherence score."""
    return {
        "coherence_score": memory.calculate_coherence_score(),
        "timestamp": datetime.now().isoformat()
    }


# ========== Fallacy Detection ==========

@app.post("/fallacy-check", response_model=FallacyCheckResponse)
def check_for_fallacies(request: FallacyCheckRequest):
    """Check a statement for logical fallacies."""
    fallacies = fallacy_detector.detect_fallacies(request.statement)
    hint = fallacy_detector.generate_response_hint(fallacies)

    return FallacyCheckResponse(
        statement=request.statement,
        fallacies=fallacies,
        hint=hint if hint else None
    )


# ========== Anti-Entropy Audit ==========

@app.post("/audit")
def run_anti_entropy_audit():
    """Run a comprehensive anti-entropy audit."""
    return memory.anti_entropy_audit()


@app.get("/audit/export")
def export_full_memory():
    """Export the complete memory state."""
    return memory.export_full_memory()


# ========== Narrative Identity ==========

@app.get("/narrative/summary")
def get_narrative_summary():
    """Get the narrative identity summary."""
    return {
        "narrative": narrative.get_identity_summary(),
        "paradigm": narrative.current_paradigm,
        "identity_anchors": narrative.identity_anchors
    }


# ========== Monitoring ==========

@app.get("/metrics")
def get_metrics():
    """Get system metrics for monitoring."""
    return {
        "timestamp": datetime.now().isoformat(),
        "memory": memory.get_memory_stats(),
        "audit": memory.audit.get_stats(),
        "coherence": memory.calculate_coherence_score(),
        "integrity": memory.verify_integrity()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8766)
