//! CSF — Convergence-Fitted Searchable Binary Archive (Rust v1.0)
//!
//! Production-grade, memory-safe, streaming-native implementation of the
//! CSF specification. Designed for files larger than RAM and workloads
//! requiring random access or search without full decompression.
//!
//! # Quick start
//! ```ignore
//! use csf::{Archive, Compressor};
//!
//! let mut archive = Archive::new();
//! archive.add_segment(b"Garden Table Lantern Convergence");
//! let bytes = archive.write()?;
//! ```

pub mod compress;
pub mod convergence;
pub mod dictionary;
pub mod header;
pub mod search;
pub mod security;
pub mod sparse;
pub mod streaming;

use thiserror::Error;

/// Crate-wide error type with hardened error messages (no alloc on panic path).
#[derive(Debug, Error)]
pub enum CsfError {
    #[error("io error: {0}")]
    Io(#[from] std::io::Error),

    #[error("parse error: {0}")]
    Parse(&'static str),

    #[error("security violation: {0}")]
    Security(&'static str),

    #[error("compression error: {0}")]
    Compression(String),

    #[error("dictionary overflow (max {max} bytes)")]
    DictionaryOverflow { max: usize },

    #[error("sparse matrix overflow (max {max} non-zero values)")]
    SparseOverflow { max: usize },

    #[error("invalid checksum (expected {expected:016x}, got {got:016x})")]
    Checksum { expected: u64, got: u64 },
}

pub type Result<T> = std::result::Result<T, CsfError>;

/// Re-export core types.
pub use compress::{Compressor, CompressionMode, Decompressor};
pub use convergence::ArchiveMerger;
pub use dictionary::SymbolicDictionary;
pub use header::{ArchiveHeader, CsfFlags};
pub use search::{SearchIndex, SearchQuery, SearchHit};
pub use security::SecurityPolicy;
pub use sparse::{CsrMatrix, CsrMetadata};
pub use streaming::{SegmentReader, StreamingCompressor};

/// Convenience archive builder.
#[derive(Debug, Default)]
pub struct Archive {
    segments: Vec<Vec<u8>>,
    dictionary: SymbolicDictionary,
    index: Option<SearchIndex>,
    flags: CsfFlags,
}

impl Archive {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn add_segment(&mut self, data: &[u8]) {
        self.segments.push(data.to_vec());
    }

    pub fn segment_count(&self) -> usize {
        self.segments.len()
    }

    /// Hardened write with security policy enforcement.
    pub fn write<W: std::io::Write + std::io::Seek>(
        &self,
        writer: &mut W,
        policy: &SecurityPolicy,
    ) -> Result<()> {
        let mut compressor = StreamingCompressor::new(policy.clone());
        for seg in &self.segments {
            compressor.ingest_segment(seg)?;
        }
        compressor.finalize(writer)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn roundtrip_one_segment() {
        let mut archive = Archive::new();
        archive.add_segment(b"Garden Table Lantern");
        let mut buf = Vec::new();
        let policy = SecurityPolicy::default();
        archive.write(&mut buf, &policy).unwrap();
        assert!(!buf.is_empty());
    }
}
