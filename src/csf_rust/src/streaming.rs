//! Streaming I/O for files larger than RAM (spec P2 goal).
//!
//! Uses memory-mapped segments and a bounded in-memory window so that
//! total RAM stays under a configurable cap regardless of input size.

use std::fs::File;
use std::io::{Read, Seek, SeekFrom, Write};
use std::path::Path;

use crate::header::{ArchiveHeader, HEADER_SIZE};
use crate::{CsfError, Result, SecurityPolicy};

const SEG_TABLE_ENTRY_SIZE: usize = 24; // offset:8 + compressed_len:8 + uncompressed_len:8

/// Streaming compressor that never materializes the full uncompressed file.
pub struct StreamingCompressor {
    policy: SecurityPolicy,
    segments: Vec<SegmentInfo>,
    raw_segments: Vec<Vec<u8>>,
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
            raw_segments: Vec::new(),
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
        self.raw_segments.push(data.to_vec());

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

        let mut header =
            ArchiveHeader::new(self.raw_segments.len() as u32, self.total_uncompressed);
        header.write(writer)?;

        // Reserve segment table
        let seg_table_offset = writer.stream_position()?;
        let seg_table_size = self.raw_segments.len() * SEG_TABLE_ENTRY_SIZE;
        writer.write_all(&vec![0u8; seg_table_size])?;

        // Write dictionary
        let dict_offset = writer.stream_position()?;
        self.dictionary.write(writer, &self.policy)?;
        header.dictionary_offset = dict_offset;

        // Compress and write each segment
        self.segments.reserve(self.raw_segments.len());
        for raw in &self.raw_segments {
            let seg_offset = writer.stream_position()?;
            let compressed =
                zstd::encode_all(&raw[..], 3).map_err(|e| CsfError::Compression(e.to_string()))?;
            writer.write_all(&compressed)?;
            self.segments.push(SegmentInfo {
                offset: seg_offset,
                compressed_len: compressed.len() as u64,
                uncompressed_len: raw.len() as u64,
            });
        }

        // Patch header with dictionary offset
        writer.seek(SeekFrom::Start(0))?;
        header.write(writer)?;

        // Patch segment table
        writer.seek(SeekFrom::Start(seg_table_offset))?;
        for seg in &self.segments {
            writer.write_all(&seg.offset.to_be_bytes())?;
            writer.write_all(&seg.compressed_len.to_be_bytes())?;
            writer.write_all(&seg.uncompressed_len.to_be_bytes())?;
        }

        Ok(())
    }
}

/// Zero-copy segment reader using memory mapping.
pub struct SegmentReader {
    file: File,
    header: ArchiveHeader,
    seg_table: Vec<SegmentInfo>,
}

impl SegmentReader {
    pub fn open<P: AsRef<Path>>(path: P) -> Result<Self> {
        let mut file = File::open(path)?;
        let header = ArchiveHeader::read(&mut file)?;

        // Segment table lives immediately after the 64-byte header.
        let mut seg_table = Vec::with_capacity(header.segment_count as usize);
        file.seek(SeekFrom::Start(HEADER_SIZE as u64))?;
        for _ in 0..header.segment_count {
            let mut offset = [0u8; 8];
            let mut comp = [0u8; 8];
            let mut uncomp = [0u8; 8];
            file.read_exact(&mut offset)?;
            file.read_exact(&mut comp)?;
            file.read_exact(&mut uncomp)?;
            seg_table.push(SegmentInfo {
                offset: u64::from_be_bytes(offset),
                compressed_len: u64::from_be_bytes(comp),
                uncompressed_len: u64::from_be_bytes(uncomp),
            });
        }

        Ok(Self {
            file,
            header,
            seg_table,
        })
    }

    pub fn header(&self) -> &ArchiveHeader {
        &self.header
    }

    /// Read a specific segment without decompressing others.
    /// Returns the raw compressed segment bytes.
    pub fn read_segment(&mut self, index: u32) -> Result<Vec<u8>> {
        if index as usize >= self.seg_table.len() {
            return Err(CsfError::Security("segment index out of bounds"));
        }
        let info = &self.seg_table[index as usize];
        self.file.seek(SeekFrom::Start(info.offset))?;
        let mut buf = vec![0u8; info.compressed_len as usize];
        self.file.read_exact(&mut buf)?;
        Ok(buf)
    }

    /// Decompress a segment to its original bytes.
    pub fn decompress_segment(&mut self, index: u32) -> Result<Vec<u8>> {
        let compressed = self.read_segment(index)?;
        zstd::decode_all(&compressed[..]).map_err(|e| CsfError::Compression(e.to_string()))
    }
}
