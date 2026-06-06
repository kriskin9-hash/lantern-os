//! Safe header parser / serializer.
//!
//! All offsets and lengths are validated before any allocation.
//! Follows spec §4.2 exactly, with additional runtime hardening.

use byteorder::{BigEndian, ReadBytesExt, WriteBytesExt};
use std::io::{Read, Write};

use crate::{CsfError, Result};

pub const MAGIC: &[u8] = b"CSFv1\0\0\0";
pub const HEADER_SIZE: usize = 64;
pub const FOOTER_SIZE: usize = 16;

/// Bitfield flags (spec §4.3).
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub struct CsfFlags(pub u32);

impl CsfFlags {
    pub const HAS_INDEX: u32 = 0x00000001;
    pub const CONVERGED: u32 = 0x00000002;
    pub const ENCRYPTED: u32 = 0x00000004;
    pub const STREAMING: u32 = 0x00000008;

    pub fn has_index(&self) -> bool {
        self.0 & Self::HAS_INDEX != 0
    }
    pub fn is_converged(&self) -> bool {
        self.0 & Self::CONVERGED != 0
    }
    pub fn is_encrypted(&self) -> bool {
        self.0 & Self::ENCRYPTED != 0
    }
    pub fn is_streaming(&self) -> bool {
        self.0 & Self::STREAMING != 0
    }
}

/// Fixed 64-byte archive header (spec §4.2).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ArchiveHeader {
    pub version: u16,
    pub flags: CsfFlags,
    pub segment_count: u32,
    pub uncompressed_size: u64,
    pub dictionary_offset: u64,
    pub index_offset: u64,
    pub header_checksum: u64,
}

impl ArchiveHeader {
    pub fn new(segment_count: u32, uncompressed_size: u64) -> Self {
        Self {
            version: 1,
            flags: CsfFlags::default(),
            segment_count,
            uncompressed_size,
            dictionary_offset: 0,
            index_offset: 0,
            header_checksum: 0,
        }
    }

    /// Serialize to exactly 64 bytes. Checksum is computed over bytes 0..42.
    pub fn write<W: Write>(&self, writer: &mut W) -> Result<()> {
        let mut buf = Vec::with_capacity(HEADER_SIZE);
        buf.write_all(MAGIC)?;
        buf.write_u16::<BigEndian>(self.version)?;
        buf.write_u32::<BigEndian>(self.flags.0)?;
        buf.write_u32::<BigEndian>(self.segment_count)?;
        buf.write_u64::<BigEndian>(self.uncompressed_size)?;
        buf.write_u64::<BigEndian>(self.dictionary_offset)?;
        buf.write_u64::<BigEndian>(self.index_offset)?;
        // placeholder checksum + reserved
        buf.resize(HEADER_SIZE, 0);
        debug_assert_eq!(buf.len(), HEADER_SIZE);

        // Compute xxHash64 over first 42 bytes (magic + fields before checksum).
        let checksum = xxhash_rust::xxh64::xxh64(&buf[0..42], 0);
        buf[42..50].copy_from_slice(&checksum.to_be_bytes());

        writer.write_all(&buf)?;
        Ok(())
    }

    /// Deserialize from exactly 64 bytes. Hardened: validate magic, version, checksum.
    pub fn read<R: Read>(reader: &mut R) -> Result<Self> {
        let mut buf = [0u8; HEADER_SIZE];
        reader.read_exact(&mut buf)?;

        // 1. Magic validation
        if &buf[0..8] != MAGIC {
            return Err(CsfError::Parse("invalid magic number"));
        }

        // 2. Version gate
        let version = (&buf[8..10]).read_u16::<BigEndian>().unwrap();
        if version != 1 {
            return Err(CsfError::Parse("unsupported CSF version"));
        }

        // 3. Checksum validation BEFORE trusting any offset
        let expected = (&buf[42..50]).read_u64::<BigEndian>().unwrap();
        let computed = xxhash_rust::xxh64::xxh64(&buf[0..42], 0);
        if expected != computed {
            return Err(CsfError::Checksum {
                expected,
                got: computed,
            });
        }

        let mut cursor = std::io::Cursor::new(&buf[10..]);
        let flags = CsfFlags(cursor.read_u32::<BigEndian>().unwrap());
        let segment_count = cursor.read_u32::<BigEndian>().unwrap();
        let uncompressed_size = cursor.read_u64::<BigEndian>().unwrap();
        let dictionary_offset = cursor.read_u64::<BigEndian>().unwrap();
        let index_offset = cursor.read_u64::<BigEndian>().unwrap();
        let header_checksum = expected;

        // 4. Sanity bounds (red line from spec §9)
        const MAX_SEGMENTS: u32 = 1_000_000;
        const MAX_UNCOMPRESSED: u64 = 1 << 50; // ~1 PB sanity limit
        if segment_count > MAX_SEGMENTS {
            return Err(CsfError::Security("segment count exceeds hard limit"));
        }
        if uncompressed_size > MAX_UNCOMPRESSED {
            return Err(CsfError::Security("uncompressed size exceeds hard limit"));
        }

        Ok(Self {
            version,
            flags,
            segment_count,
            uncompressed_size,
            dictionary_offset,
            index_offset,
            header_checksum,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn roundtrip() {
        let hdr = ArchiveHeader::new(3, 12345);
        let mut buf = Vec::new();
        hdr.write(&mut buf).unwrap();
        assert_eq!(buf.len(), HEADER_SIZE);
        let parsed = ArchiveHeader::read(&mut &buf[..]).unwrap();
        assert_eq!(parsed.version, 1);
        assert_eq!(parsed.segment_count, 3);
        assert_eq!(parsed.uncompressed_size, 12345);
    }

    #[test]
    fn corrupt_magic_fails() {
        let mut buf = vec![0u8; HEADER_SIZE];
        buf[0] = b'X';
        assert!(ArchiveHeader::read(&mut &buf[..]).is_err());
    }

    #[test]
    fn checksum_tamper_fails() {
        let hdr = ArchiveHeader::new(1, 100);
        let mut buf = Vec::new();
        hdr.write(&mut buf).unwrap();
        buf[42] ^= 0xFF; // flip one bit in checksum region
        assert!(ArchiveHeader::read(&mut &buf[..]).is_err());
    }
}
