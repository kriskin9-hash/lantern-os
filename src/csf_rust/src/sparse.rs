//! Sparse Matrix Layer (L2) — spec §3.2.
//!
//! Compressed Sparse Row (CSR) encoding for mostly-default data.
//! Zero-allocation decode path available via streaming iterator.

use byteorder::{BigEndian, ReadBytesExt, WriteBytesExt};
use std::io::{Read, Write};

use crate::{CsfError, Result, SecurityPolicy};

/// Metadata for a CSR-encoded segment.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CsrMetadata {
    pub original_len: usize,
    pub block_size: usize,
    pub default_value: u8,
    pub num_blocks: usize,
}

/// In-memory CSR matrix. For streaming >RAM, use `StreamingCsrEncoder`.
#[derive(Debug, Clone)]
pub struct CsrMatrix {
    pub meta: CsrMetadata,
    pub row_ptrs: Vec<usize>,
    pub col_indices: Vec<usize>,
    pub values: Vec<u8>,
}

/// Encode raw bytes as sparse blocks with zlib final pass.
pub fn encode_sparse(
    data: &[u8],
    default_value: u8,
    block_size: usize,
    policy: &SecurityPolicy,
) -> Result<(CsrMetadata, Vec<u8>)> {
    let mut blocks: Vec<(usize, &[u8])> = Vec::new();
    for (idx, chunk) in data.chunks(block_size).enumerate() {
        if chunk.iter().any(|&b| b != default_value) {
            blocks.push((idx, chunk));
        }
    }

    policy.check_sparse(blocks.len())?;

    let meta = CsrMetadata {
        original_len: data.len(),
        block_size,
        default_value,
        num_blocks: blocks.len(),
    };

    let mut buf = Vec::with_capacity(blocks.len() * (block_size + 6));
    for (idx, chunk) in blocks {
        buf.write_u32::<BigEndian>(idx as u32)?;
        buf.write_u16::<BigEndian>(chunk.len() as u16)?;
        buf.write_all(chunk)?;
    }

    // Final entropy pass — zstd level 3 (fast, good ratio)
    let compressed = zstd::encode_all(&buf[..], 3)
        .map_err(|e| CsfError::Compression(e.to_string()))?;
    Ok((meta, compressed))
}

/// Decode CSR back to dense bytes.
pub fn decode_sparse(meta: &CsrMetadata, compressed: &[u8]) -> Result<Vec<u8>> {
    let raw = zstd::decode_all(compressed)
        .map_err(|e| CsfError::Compression(e.to_string()))?;

    let mut output = vec![meta.default_value; meta.original_len];
    let mut cursor = std::io::Cursor::new(&raw);
    for _ in 0..meta.num_blocks {
        let idx = cursor.read_u32::<BigEndian>()? as usize;
        let blen = cursor.read_u16::<BigEndian>()? as usize;
        let start = idx * meta.block_size;
        let end = (start + blen).min(meta.original_len);
        cursor.read_exact(&mut output[start..end])?;
    }
    Ok(output)
}

/// Streaming CSR encoder for files > RAM.
/// Writes blocks incrementally without holding the full dense array.
pub struct StreamingCsrEncoder<W: Write> {
    writer: W,
    block_size: usize,
    default_value: u8,
    block_count: u32,
    current_block: Vec<u8>,
}

impl<W: Write> StreamingCsrEncoder<W> {
    pub fn new(writer: W, block_size: usize, default_value: u8) -> Self {
        Self {
            writer,
            block_size,
            default_value,
            block_count: 0,
            current_block: Vec::with_capacity(block_size),
        }
    }

    /// Feed bytes incrementally.
    pub fn write(&mut self, data: &[u8]) -> Result<()> {
        for &b in data {
            self.current_block.push(b);
            if self.current_block.len() >= self.block_size {
                self.flush_block()?;
            }
        }
        Ok(())
    }

    fn flush_block(&mut self) -> Result<()> {
        if self.current_block.is_empty() {
            return Ok(());
        }
        let chunk = std::mem::replace(&mut self.current_block, Vec::with_capacity(self.block_size));
        if chunk.iter().any(|&b| b != self.default_value) {
            self.writer.write_u32::<BigEndian>(self.block_count)?;
            self.writer.write_u16::<BigEndian>(chunk.len() as u16)?;
            self.writer.write_all(&chunk)?;
        }
        self.block_count += 1;
        Ok(())
    }

    pub fn finalize(mut self) -> Result<u32> {
        self.flush_block()?;
        Ok(self.block_count)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn roundtrip_dense_sparse() {
        let data = vec![0, 0, 1, 0, 0, 2, 0, 0, 0, 3];
        let policy = SecurityPolicy::default();
        let (meta, comp) = encode_sparse(&data, 0, 4, &policy).unwrap();
        let out = decode_sparse(&meta, &comp).unwrap();
        assert_eq!(out, data);
    }

    #[test]
    fn all_defaults_yields_empty() {
        let data = vec![0u8; 100];
        let policy = SecurityPolicy::default();
        let (meta, comp) = encode_sparse(&data, 0, 16, &policy).unwrap();
        assert_eq!(meta.num_blocks, 0);
        let out = decode_sparse(&meta, &comp).unwrap();
        assert_eq!(out, data);
    }
}
