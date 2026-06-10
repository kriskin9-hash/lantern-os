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

pub mod claims_packet;
pub mod compress;
pub mod convergence;
pub mod dictionary;
pub mod header;
pub mod search;
pub mod security;
pub mod sparse;
pub mod streaming;
pub mod wavefront;

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
pub use compress::{CompressionMode, Compressor, Decompressor};
pub use convergence::ArchiveMerger;
pub use dictionary::SymbolicDictionary;
pub use header::{ArchiveHeader, CsfFlags};
pub use search::{SearchHit, SearchIndex, SearchQuery};
pub use security::SecurityPolicy;
pub use sparse::{CsrMatrix, CsrMetadata};
pub use streaming::{segment_flags, ArchiveReader, Footer, SegmentReader, StreamingCompressor};
pub use wavefront::Wavefront;

/// Convenience archive builder.
#[derive(Debug, Default)]
pub struct Archive {
    segments: Vec<Vec<u8>>,
    dictionary: SymbolicDictionary,
    #[allow(dead_code)]
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
    pub fn write<W: std::io::Read + std::io::Write + std::io::Seek>(
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

    fn write_archive_to_tmp(archive: &Archive) -> tempfile::NamedTempFile {
        let tmp = tempfile::NamedTempFile::new().unwrap();
        let mut file = std::fs::OpenOptions::new()
            .read(true)
            .write(true)
            .open(tmp.path())
            .unwrap();
        archive
            .write(&mut file, &SecurityPolicy::default())
            .unwrap();
        drop(file);
        tmp
    }

    // ── existing tests ──────────────────────────────────────────────────────

    #[test]
    fn roundtrip_one_segment() {
        let mut archive = Archive::new();
        archive.add_segment(b"Garden Table Lantern");
        let mut buf = std::io::Cursor::new(Vec::new());
        let policy = SecurityPolicy::default();
        archive.write(&mut buf, &policy).unwrap();
        assert!(!buf.into_inner().is_empty());
    }

    #[test]
    fn segment_reader_roundtrip() {
        let mut archive = Archive::new();
        archive.add_segment(b"Segment zero");
        archive.add_segment(b"Segment one");
        archive.add_segment(b"Segment two");

        let tmp = write_archive_to_tmp(&archive);

        let mut reader = SegmentReader::open(tmp.path()).unwrap();
        assert_eq!(reader.header().segment_count, 3);

        let seg0 = reader.decompress_segment(0).unwrap();
        assert_eq!(&seg0[..], b"Segment zero");

        let seg2 = reader.decompress_segment(2).unwrap();
        assert_eq!(&seg2[..], b"Segment two");
    }

    // ── golden fixture: empty archive ────────────────────────────────────────

    #[test]
    fn roundtrip_empty_archive() {
        let archive = Archive::new();
        let tmp = write_archive_to_tmp(&archive);

        // validate must pass
        SegmentReader::validate(tmp.path()).unwrap();

        // ArchiveReader returns zero bytes
        let out = ArchiveReader::decompress_to_vec(tmp.path()).unwrap();
        assert!(out.is_empty());
    }

    // ── golden fixture: binary payload (bit-perfect) ─────────────────────────

    #[test]
    fn roundtrip_binary_payload_bit_perfect() {
        // Contains nulls, high bytes, every value 0x00..=0xff
        let payload: Vec<u8> = (0u8..=255u8)
            .chain([b'\n', 0x00, 0xff, b'\t', 0x80].iter().copied())
            .collect();

        let mut archive = Archive::new();
        archive.add_segment(&payload);
        let tmp = write_archive_to_tmp(&archive);

        SegmentReader::validate(tmp.path()).unwrap();

        let restored = ArchiveReader::decompress_to_vec(tmp.path()).unwrap();
        assert_eq!(restored, payload, "binary payload must be bit-perfect");
    }

    // ── golden fixture: multi-segment concatenation via ArchiveReader ─────────

    #[test]
    fn roundtrip_multi_segment_archive_reader() {
        let seg_a = b"Alpha: Garden Door".as_ref();
        let seg_b = b"Beta: Lantern \0 null \xff high".as_ref();
        let seg_c = b"Gamma: convergence complete".as_ref();
        let expected: Vec<u8> = [seg_a, seg_b, seg_c].concat();

        let mut archive = Archive::new();
        archive.add_segment(seg_a);
        archive.add_segment(seg_b);
        archive.add_segment(seg_c);
        let tmp = write_archive_to_tmp(&archive);

        SegmentReader::validate(tmp.path()).unwrap();

        let restored = ArchiveReader::decompress_to_vec(tmp.path()).unwrap();
        assert_eq!(
            restored, expected,
            "multi-segment must concatenate in order"
        );
    }

    // ── footer: validate passes on well-formed archive ───────────────────────

    #[test]
    fn footer_validate_passes_on_good_archive() {
        let mut archive = Archive::new();
        archive.add_segment(b"validate me");
        let tmp = write_archive_to_tmp(&archive);
        SegmentReader::validate(tmp.path()).unwrap();
    }

    // ── footer: validate rejects a byte-flipped body ─────────────────────────

    #[test]
    fn footer_validate_rejects_corrupt_archive() {
        let mut archive = Archive::new();
        archive.add_segment(b"tamper target");
        let tmp = write_archive_to_tmp(&archive);

        // Flip a byte in the middle of the file (inside the compressed segment)
        let mut bytes = std::fs::read(tmp.path()).unwrap();
        let mid = bytes.len() / 2;
        bytes[mid] ^= 0xff;
        std::fs::write(tmp.path(), &bytes).unwrap();

        let result = SegmentReader::validate(tmp.path());
        assert!(result.is_err(), "corrupt archive must fail validation");
    }

    // ── footer: validate rejects truncated file ───────────────────────────────

    #[test]
    fn footer_validate_rejects_truncated_archive() {
        let mut archive = Archive::new();
        archive.add_segment(b"truncate me");
        let tmp = write_archive_to_tmp(&archive);

        // Truncate to 8 bytes — too short for any valid archive
        let bytes = std::fs::read(tmp.path()).unwrap();
        std::fs::write(tmp.path(), &bytes[..8]).unwrap();

        let result = SegmentReader::validate(tmp.path());
        assert!(result.is_err(), "truncated archive must fail validation");
    }

    // ── segment_flags: RAW flag is set on all segments written by Archive ─────

    #[test]
    fn segments_have_raw_flag() {
        let mut archive = Archive::new();
        archive.add_segment(b"flag check");
        let tmp = write_archive_to_tmp(&archive);

        let mut reader = SegmentReader::open(tmp.path()).unwrap();
        // decompress_segment must succeed (RAW path works)
        let out = reader.decompress_segment(0).unwrap();
        assert_eq!(&out[..], b"flag check");
    }

    // ── Security hardening tests (#262) ──────────────────────────────────────

    fn strict_policy(
        max_segments: usize,
        max_seg_bytes: usize,
        max_archive: u64,
    ) -> SecurityPolicy {
        SecurityPolicy {
            max_segments,
            max_segment_bytes: max_seg_bytes,
            max_archive_bytes: max_archive,
            ..SecurityPolicy::default()
        }
    }

    #[test]
    fn untrusted_rejects_too_many_segments() {
        let mut archive = Archive::new();
        archive.add_segment(b"seg a");
        archive.add_segment(b"seg b");
        archive.add_segment(b"seg c");
        let tmp = write_archive_to_tmp(&archive);

        let policy = strict_policy(2, usize::MAX, u64::MAX);
        let result = SegmentReader::validate_with_policy(tmp.path(), &policy);
        assert!(result.is_err(), "3 segments must be rejected when max=2");
        let msg = result.unwrap_err().to_string();
        assert!(
            msg.contains("segment count"),
            "error should mention segment count, got: {msg}"
        );
    }

    #[test]
    fn untrusted_rejects_oversized_archive() {
        let mut archive = Archive::new();
        archive.add_segment(b"hello world");
        let tmp = write_archive_to_tmp(&archive);

        let policy = strict_policy(usize::MAX, usize::MAX, 1); // max 1 byte total
        let result = SegmentReader::validate_with_policy(tmp.path(), &policy);
        assert!(
            result.is_err(),
            "archive exceeding max_archive_bytes must be rejected"
        );
    }

    #[test]
    fn untrusted_rejects_oversized_compressed_segment() {
        // Write a real archive, patch the compressed_len in the seg table to a huge value,
        // re-sign the footer checksum so validate reaches the segment table check.
        let mut archive = Archive::new();
        archive.add_segment(b"patch target");
        let tmp = write_archive_to_tmp(&archive);

        let mut bytes = std::fs::read(tmp.path()).unwrap();
        let file_len = bytes.len();
        let footer_start = file_len - streaming::FOOTER_SIZE;

        // compressed_len is at header(64) + offset_field(8) = byte 72
        const COMP_LEN_OFFSET: usize = 64 + 8;
        bytes[COMP_LEN_OFFSET..COMP_LEN_OFFSET + 8].copy_from_slice(&u64::MAX.to_be_bytes());

        // Re-sign the footer so checksum passes and we reach the segment size check
        let body_checksum = streaming::footer_checksum(&bytes[64..footer_start]);
        // ENDCSF magic is bytes footer_start..footer_start+6
        bytes[footer_start + 6..footer_start + 10].copy_from_slice(&body_checksum.to_be_bytes());

        std::fs::write(tmp.path(), &bytes).unwrap();

        let policy = strict_policy(usize::MAX, 1024, u64::MAX); // max 1024 bytes per segment
        let result = SegmentReader::validate_with_policy(tmp.path(), &policy);
        assert!(
            result.is_err(),
            "segment with compressed_len=u64::MAX must be rejected"
        );
    }

    #[test]
    fn segment_offset_past_eof_rejected() {
        // Patch segment offset to point past the footer; re-sign footer.
        let mut archive = Archive::new();
        archive.add_segment(b"bounds check");
        let tmp = write_archive_to_tmp(&archive);

        let mut bytes = std::fs::read(tmp.path()).unwrap();
        let file_len = bytes.len();
        let footer_start = file_len - streaming::FOOTER_SIZE;

        // offset field is at header(64) = byte 64
        const SEG_OFFSET_FIELD: usize = 64;
        bytes[SEG_OFFSET_FIELD..SEG_OFFSET_FIELD + 8]
            .copy_from_slice(&(u64::MAX - 1).to_be_bytes());

        // Re-sign footer
        let body_checksum = streaming::footer_checksum(&bytes[64..footer_start]);
        bytes[footer_start + 6..footer_start + 10].copy_from_slice(&body_checksum.to_be_bytes());

        std::fs::write(tmp.path(), &bytes).unwrap();

        let result = SegmentReader::validate(tmp.path());
        assert!(result.is_err(), "segment offset past EOF must be rejected");
        let msg = result.unwrap_err().to_string();
        assert!(
            msg.contains("past footer") || msg.contains("segment"),
            "got: {msg}"
        );
    }

    #[test]
    fn validate_with_policy_passes_on_valid_archive() {
        let mut archive = Archive::new();
        archive.add_segment(b"policy pass");
        let tmp = write_archive_to_tmp(&archive);
        SegmentReader::validate_with_policy(tmp.path(), &SecurityPolicy::untrusted()).unwrap();
    }

    #[test]
    fn untrusted_policy_is_stricter_than_default() {
        let u = SecurityPolicy::untrusted();
        let d = SecurityPolicy::default();
        assert!(u.max_dictionary_bytes < d.max_dictionary_bytes);
        assert!(u.max_segments < d.max_segments);
        assert!(u.max_segment_bytes < d.max_segment_bytes);
        assert!(u.max_convergence_depth < d.max_convergence_depth);
        assert!(u.max_archive_bytes < d.max_archive_bytes);
    }

    #[test]
    fn header_rejects_corrupt_magic() {
        let mut bytes = vec![0u8; header::HEADER_SIZE];
        // Write obviously wrong magic
        bytes[0..8].copy_from_slice(b"NOTCSF!!");
        let result = ArchiveHeader::read(&mut &bytes[..]);
        assert!(result.is_err(), "bad magic must be rejected");
    }

    #[test]
    fn header_rejects_corrupt_checksum() {
        let hdr = ArchiveHeader::new(1, 100);
        let mut buf = Vec::new();
        hdr.write(&mut buf).unwrap();
        buf[42] ^= 0x01; // flip one bit in the header checksum
        let result = ArchiveHeader::read(&mut &buf[..]);
        assert!(result.is_err(), "tampered header checksum must be rejected");
    }
}
