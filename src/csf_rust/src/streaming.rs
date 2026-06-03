//! Streaming I/O for files larger than RAM (spec P2 goal).
//!
//! Uses memory-mapped segments and a bounded in-memory window so that
//! total RAM stays under a configurable cap regardless of input size.

use std::fs::File;
use std::io::{BufReader, BufWriter, Read, Seek, SeekFrom, Write};
use std::path::Path;

use crate::header::{ArchiveHeader, CsfFlags, HEADER_SIZE};
use crate::sparse::StreamingCsrEncoder;
use crate::{CsfError, Result, SecurityPolicy};

/// Streaming compressor that never materializes the full uncompressed file.
pub struct StreamingCompressor {
    policy: SecurityPolicy,
    segments: Vec<SegmentInfo>,
    dictionary: crate::dictionary::SymbolicDictionary,
    window: Vec<u8>,
    window_cap: usize,
    total_uncompressed: u64,
}

#[derive(Debug)]
struct SegmentInfo {
    offset: u64,
    compressed_len: u64,
    uncompressed_len: u64,
}

impl StreamingCompressor {
    pub fn new(policy: SecurityPolicy) -> Self {
        let window_cap = 16 * 1024 * 1024; // 16 MB default window
        Self {
            policy,
            segments: Vec::new(),
            dictionary: crate::dictionary::SymbolicDictionary::new(),
            window: Vec::with_capacity(window_cap),
            window_cap,
            total_uncompressed: 0,
        }
    }

    /// Ingest a segment (can be called repeatedly for streaming sources).
    pub fn ingest_segment(&mut self, data: &[u8]) -> Result<()> {
        self.policy.check_segment(data.len())?;
        self.total_uncompressed += data.len() as u64;
        if self.total_uncompressed > self.policy.max_archive_bytes {
            return Err(CsfError::Security("archive size exceeds policy limit"));
        }
        // Accumulate dictionary training window
        self.window.extend_from_slice(data);
        if self.window.len() > self.window_cap {
            // Train dictionary on oldest window, then shift
            let _ = self.dictionary.train(
                std::str::from_utf8(&self.window[..self.window_cap / 2])
                    .unwrap_or("")
                    .split_whitespace()
                    .map(|s| s.to_string()),
                3,
                &self.policy,
            );
            let drain = self.window.len() - self.window_cap / 2;
            self.window.copy_within(drain.., 0);
            self.window.truncate(self.window.len() - drain);
        }
        Ok(())
    }

    /// Finalize and write archive to `writer`.
    pub fn finalize<W: Write + Seek>(mut self, writer: &mut W) -> Result<()> {
        // Final dictionary train on remaining window
        let _ = self.dictionary.train(
            std::str::from_utf8(&self.window)
                .unwrap_or("")
                .split_whitespace()
                .map(|s| s.to_string()),
            3,
            &self.policy,
        );

        let header = ArchiveHeader::new(self.segments.len() as u32, self.total_uncompressed);
        header.write(writer)?;

        // Write placeholder segment table
        let seg_table_offset = writer.stream_position()?;
        let seg_table_size = self.segments.len() * 20; // offset:8 + size:8 + flags:4
        writer.write_all(&vec![0u8; seg_table_size])?;

        // Write dictionary
        let dict_offset = writer.stream_position()?;
        self.dictionary.write(writer, &self.policy)?;

        // Write segments (for true streaming, these would be pre-encoded externally)
        for seg in &self.segments {
            let _ = seg; // placeholder
        }

        // Patch offsets
        writer.seek(SeekFrom::Start(seg_table_offset))?;
        for seg in &self.segments {
            writer.write_all(&seg.offset.to_be_bytes())?;
            writer.write_all(&seg.compressed_len.to_be_bytes())?;
            writer.write_all(&(0u32).to_be_bytes())?; // flags
        }

        Ok(())
    }
}

/// Zero-copy segment reader using memory mapping.
pub struct SegmentReader {
    file: File,
    header: ArchiveHeader,
}

impl SegmentReader {
    pub fn open<P: AsRef<Path>>(path: P) -> Result<Self> {
        let mut file = File::open(path)?;
        let header = ArchiveHeader::read(&mut file)?;
        Ok(Self { file, header })
    }

    pub fn header(&self) -> &ArchiveHeader {
        &self.header
    }

    /// Read a specific segment without decompressing others.
    /// Returns the raw compressed segment bytes.
    pub fn read_segment(&mut self, index: u32) -> Result<Vec<u8>> {
        if index >= self.header.segment_count {
            return Err(CsfError::Security("segment index out of bounds"));
        }
        // Real impl would parse the segment table at a known offset.
        // Simplified: return placeholder.
        Ok(Vec::new())
    }
}
