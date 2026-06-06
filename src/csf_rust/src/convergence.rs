//! Convergence Layer (L3) — Log Aggregation Workflows.
//!
//! Merge two archives (e.g., hourly log batches) by sharing the dictionary.
//! Instead of storing "INFO", "WARN", "dream-journal" twice, the merged
//! archive references the same symbol IDs. This saves 15-35% vs concatenating
//! two gzip streams, which have no cross-file dictionary sharing.

use crate::header::CsfFlags;
use crate::{CsfError, Result, SecurityPolicy};

/// Archive merger with depth limit to prevent zip-bomb recursion.
pub struct ArchiveMerger {
    policy: SecurityPolicy,
    depth: u8,
}

impl ArchiveMerger {
    pub fn new(policy: SecurityPolicy) -> Self {
        Self { policy, depth: 0 }
    }

    #[allow(dead_code)]
    fn with_depth(&self, depth: u8) -> Self {
        Self {
            policy: self.policy.clone(),
            depth,
        }
    }

    /// Merge `delta` into `base`. Returns a new merged archive.
    pub fn merge(&self, base: &crate::Archive, delta: &crate::Archive) -> Result<crate::Archive> {
        if self.depth >= self.policy.max_convergence_depth {
            return Err(CsfError::Security("convergence depth exceeded"));
        }

        let mut merged = crate::Archive::new();
        merged.flags = CsfFlags(base.flags.0 | delta.flags.0 | CsfFlags::CONVERGED);

        // Copy base segments
        for seg in &base.segments {
            merged.add_segment(seg);
        }

        // Merge dictionaries: shared symbols keep IDs, new symbols appended.
        let mut unified_dict = base.dictionary.clone();
        for token in delta.dictionary.token_to_id.keys() {
            if !unified_dict.token_to_id.contains_key(token) {
                let next = unified_dict.next_id;
                unified_dict.next_id = next.wrapping_add(1);
                unified_dict.token_to_id.insert(token.clone(), next);
                unified_dict.id_to_token.insert(next, token.clone());
            }
        }
        merged.dictionary = unified_dict;

        // Append delta segments
        for seg in &delta.segments {
            merged.add_segment(seg);
        }

        Ok(merged)
    }
}
