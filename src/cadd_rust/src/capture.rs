//! Capture stage — record asset metadata before validation.

use std::fs;
use std::path::{Path, PathBuf};
use std::time::SystemTime;

use crate::{CaddError, Result};

/// Captured metadata for a single asset.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Capture {
    pub source_path: PathBuf,
    pub file_name: String,
    pub file_size: u64,
    pub modified: Option<String>,
    pub content_hash: String,
    pub width: u32,
    pub height: u32,
    pub purpose: String,
    pub tier: String,
    pub has_prompt_file: bool,
}

impl Capture {
    /// Capture metadata from a file on disk.
    pub fn from_file<P: AsRef<Path>>(path: P) -> Result<Self> {
        let path = path.as_ref();
        let meta = fs::metadata(path)?;
        let file_size = meta.len();

        let (width, height) = Self::read_dimensions(path)?;
        let content_hash = Self::hash_file(path)?;

        let modified = meta
            .modified()
            .ok()
            .and_then(|t| t.duration_since(SystemTime::UNIX_EPOCH).ok())
            .map(|d| chrono::DateTime::from_timestamp(d.as_secs() as i64, 0))
            .flatten()
            .map(|dt| dt.to_rfc3339());

        let prompt_path = path.with_extension("md");
        let has_prompt_file = prompt_path.exists();

        Ok(Self {
            source_path: path.to_path_buf(),
            file_name: path.file_name().unwrap_or_default().to_string_lossy().to_string(),
            file_size,
            modified,
            content_hash,
            width,
            height,
            purpose: String::new(),
            tier: String::new(),
            has_prompt_file,
        })
    }

    /// Set the purpose (e.g., "patreon-card", "discord-banner").
    pub fn with_purpose(mut self, purpose: &str) -> Self {
        self.purpose = purpose.to_string();
        self
    }

    /// Set the tier role (free, normal, pro).
    pub fn with_tier(mut self, tier: &str) -> Self {
        self.tier = tier.to_string();
        self
    }

    fn read_dimensions(path: &Path) -> Result<(u32, u32)> {
        let data = fs::read(path)?;
        // Try PNG first
        if data.starts_with(b"\x89PNG") {
            let w = u32::from_be_bytes([data[16], data[17], data[18], data[19]]);
            let h = u32::from_be_bytes([data[20], data[21], data[22], data[23]]);
            return Ok((w, h));
        }
        // Try JPEG (simplified SOF0 parser)
        if data.starts_with(b"\xFF\xD8") {
            for i in 0..data.len().saturating_sub(10) {
                if data[i] == 0xFF && data[i + 1] == 0xC0 {
                    let h = u16::from_be_bytes([data[i + 5], data[i + 6]]) as u32;
                    let w = u16::from_be_bytes([data[i + 7], data[i + 8]]) as u32;
                    return Ok((w, h));
                }
            }
        }
        Ok((0, 0))
    }

    fn hash_file(path: &Path) -> Result<String> {
        use std::io::Read;
        let mut file = fs::File::open(path)?;
        let mut buf = Vec::new();
        file.read_to_end(&mut buf)?;
        let hash = xxhash_rust::xxh64::xxh64(&buf, 0);
        Ok(format!("{:016x}", hash))
    }
}
