"""
CSF v0.7 — Symbolic Qutrit Edition (Performance Optimized)
Classical Optimized, Quantum Dust Aware, Convergence-Accelerated

Modules:
  qutrit_delta      — Qutrit state and delta packing (amplitude + phase)
  quantum_dust      — Default free-state management with delta dedup & caching
  convergence_engine — Multi-level convergence with cluster promotion
  classical_compressor — Hybrid pipeline: dict + sparse + delta + zstd
  csf_file          — Binary format writer/reader for v0.7

v0.7 optimizations:
  - LRU-cached magnitude computation
  - Pre-computed cluster norms for O(1) similarity
  - Cluster-to-baseline promotion on saturation
  - Adaptive threshold scaling
  - Delta deduplication in observe()/observe_batch()
  - Cached get_state() with internal hit tracking
  - Multi-level convergence in compress_field()
"""

__version__ = (0, 7, 0)
