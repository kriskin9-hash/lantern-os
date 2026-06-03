//! Hardened security policy — addresses spec §9 threat model.
//!
//! Red lines enforced at runtime:
//!   • Never allocate based solely on header values.
//!   • Always validate offsets before seeking.
//!   • Cap dictionary, sparse, and segment sizes.

/// Immutable security configuration parsed once at startup.
#[derive(Debug, Clone)]
pub struct SecurityPolicy {
    /// Max dictionary size in bytes (default: 256 MiB, spec §9).
    pub max_dictionary_bytes: usize,
    /// Max number of symbols (default: 2^24).
    pub max_symbol_count: usize,
    /// Max uncompressed segment size (default: 4 GiB).
    pub max_segment_bytes: usize,
    /// Max number of segments per archive (default: 1 M).
    pub max_segments: usize,
    /// Max sparse non-zero values (default: 1B).
    pub max_sparse_nonzeros: usize,
    /// Max total uncompressed archive size (default: 1 PiB).
    pub max_archive_bytes: u64,
    /// Max recursion / convergence depth (default: 64).
    pub max_convergence_depth: u8,
    /// Require checksum verification on every read.
    pub enforce_checksums: bool,
}

impl Default for SecurityPolicy {
    fn default() -> Self {
        Self {
            max_dictionary_bytes: 256 * 1024 * 1024, // 256 MB
            max_symbol_count: 1 << 24,               // 16.7 M symbols
            max_segment_bytes: 4 * 1024 * 1024 * 1024, // 4 GB
            max_segments: 1_000_000,
            max_sparse_nonzeros: 1_000_000_000,
            max_archive_bytes: 1 << 50,              // ~1 PB
            max_convergence_depth: 64,
            enforce_checksums: true,
        }
    }
}

impl SecurityPolicy {
    /// Conservative policy for untrusted inputs (e.g., web uploads).
    pub fn untrusted() -> Self {
        Self {
            max_dictionary_bytes: 16 * 1024 * 1024, // 16 MB
            max_symbol_count: 65_536,
            max_segment_bytes: 128 * 1024 * 1024, // 128 MB
            max_segments: 10_000,
            max_sparse_nonzeros: 10_000_000,
            max_archive_bytes: 128 * 1024 * 1024 * 1024, // 128 GB
            max_convergence_depth: 8,
            enforce_checksums: true,
        }
    }

    /// Validate that `size` does not exceed the dictionary cap.
    pub fn check_dictionary(&self, size: usize) -> crate::Result<()> {
        if size > self.max_dictionary_bytes {
            Err(crate::CsfError::DictionaryOverflow {
                max: self.max_dictionary_bytes,
            })
        } else {
            Ok(())
        }
    }

    /// Validate that `count` does not exceed the sparse non-zero cap.
    pub fn check_sparse(&self, count: usize) -> crate::Result<()> {
        if count > self.max_sparse_nonzeros {
            Err(crate::CsfError::SparseOverflow {
                max: self.max_sparse_nonzeros,
            })
        } else {
            Ok(())
        }
    }

    /// Validate segment size.
    pub fn check_segment(&self, size: usize) -> crate::Result<()> {
        if size > self.max_segment_bytes {
            Err(crate::CsfError::Security("segment exceeds max size"))
        } else {
            Ok(())
        }
    }
}
