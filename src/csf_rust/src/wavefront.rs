//! Active Wavefront — bounded in-memory slice of a CSF archive.
//!
//! The Tesseract only materializes a small "present" slice (the wavefront)
//! from potentially terabyte-scale latent archives.  This module keeps RSS
//! bounded regardless of archive size by:
//!   1. Loading only requested segments.
//!   2. Evicting least-recently-used segments when a cap is exceeded.
//!   3. Sharing one working dictionary across all cached segments.

use std::collections::HashMap;

use crate::{
    dictionary::SymbolicDictionary,
    header::ArchiveHeader,
    search::{SearchHit, SearchIndex, SearchQuery},
    CsfError, Result, SecurityPolicy,
};

/// In-memory view of N segments around the "present".
///
/// Memory budget = `max_segments` × average segment size + dictionary.
/// For the Tesseract default (5 segments × 4 MB + 1 MB dict) ≈ 24 MB.
pub struct Wavefront {
    policy: SecurityPolicy,
    header: ArchiveHeader,
    dictionary: SymbolicDictionary,
    index: Option<SearchIndex>,
    /// segment_index → cached data (decompressed bytes)
    cache: HashMap<u32, Vec<u8>>,
    /// LRU ordering: most-recently-used at the back.
    lru: Vec<u32>,
    max_segments: usize,
    max_bytes: usize,
    /// Total bytes currently held in `cache`.
    cached_bytes: usize,
}

impl Wavefront {
    /// Create a new wavefront from an already-loaded header + dictionary.
    ///
    /// # Arguments
    /// * `header` — parsed archive header.
    /// * `dictionary` — shared working dictionary for all segments.
    /// * `index` — optional search index (enables bloom-negative fast path).
    /// * `policy` — security policy dictating hard caps.
    /// * `max_segments` — segment count cap (default: 5).
    /// * `max_bytes` — byte cap (default: 64 MB).
    pub fn new(
        header: ArchiveHeader,
        dictionary: SymbolicDictionary,
        index: Option<SearchIndex>,
        policy: SecurityPolicy,
        max_segments: usize,
        max_bytes: usize,
    ) -> Self {
        Self {
            policy,
            header,
            dictionary,
            index,
            cache: HashMap::new(),
            lru: Vec::new(),
            max_segments,
            max_bytes,
            cached_bytes: 0,
        }
    }

    /// Load a segment into the wavefront, evicting if necessary.
    ///
    /// `decompress` is a closure that fetches and decompresses the raw segment
    /// bytes given its index.  This keeps the wavefront independent of I/O
    /// strategy (mmap, file, network, etc.).
    pub fn load_segment<F>(&mut self, index: u32, decompress: F) -> Result<&[u8]>
    where
        F: FnOnce(u32) -> Result<Vec<u8>>,
    {
        if index >= self.header.segment_count {
            return Err(CsfError::Security("segment index out of bounds"));
        }

        if !self.cache.contains_key(&index) {
            let data = decompress(index)?;
            self.policy.check_segment(data.len())?;

            // Evict until we have room.
            while self.cache.len() >= self.max_segments
                || (self.cached_bytes + data.len()) > self.max_bytes
            {
                if let Some(victim) = self.lru.first().copied() {
                    self.evict(victim);
                } else {
                    break;
                }
            }

            self.cached_bytes += data.len();
            self.cache.insert(index, data);
        }

        // Touch LRU.
        self.lru.retain(|&i| i != index);
        self.lru.push(index);

        Ok(self.cache.get(&index).map(|v| v.as_slice()).unwrap())
    }

    /// Search within the wavefront without touching segments that fail the
    /// Bloom filter negative check.
    pub fn search<F>(
        &mut self,
        query: &SearchQuery,
        decompress: F,
    ) -> Result<Vec<SearchHit>>
    where
        F: Fn(u32) -> Result<Vec<u8>>,
    {
        // Fast path: if we have an index and bloom says "no", return empty.
        if let Some(ref idx) = self.index {
            if idx.bloom_negative(query, &self.dictionary) {
                return Ok(Vec::new());
            }
        }

        let candidates = self
            .index
            .as_ref()
            .map(|idx| idx.query_candidates(query, &self.dictionary))
            .unwrap_or_else(|| (0..self.header.segment_count).collect());

        let mut hits = Vec::new();
        if query.terms.is_empty() {
            return Ok(hits);
        }
        let needle = &query.terms[0];
        for seg in candidates {
            let data = self.load_segment(seg, |i| decompress(i))?;
            let text = std::str::from_utf8(data).unwrap_or("");
            for (offset, _) in text.match_indices(needle) {
                hits.push(SearchHit {
                    segment_index: seg,
                    byte_offset: offset as u64,
                    context: text[offset..(offset + 40).min(text.len())].to_string(),
                });
            }
        }
        Ok(hits)
    }

    /// Total bytes resident in the wavefront.
    pub fn resident_bytes(&self) -> usize {
        self.cached_bytes + self.dictionary_size()
    }

    /// Number of segments currently cached.
    pub fn resident_segments(&self) -> usize {
        self.cache.len()
    }

    /// Evict everything.  Useful when the observer "collapses" to a new slice.
    pub fn clear(&mut self) {
        self.cache.clear();
        self.lru.clear();
        self.cached_bytes = 0;
    }

    fn evict(&mut self, index: u32) {
        if let Some(data) = self.cache.remove(&index) {
            self.cached_bytes -= data.len();
        }
        self.lru.retain(|&i| i != index);
    }

    fn dictionary_size(&self) -> usize {
        // Rough estimate: each token stored twice in HashMaps.
        self.dictionary.vocab_size() * 16
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn dummy_header(seg_count: u32) -> ArchiveHeader {
        ArchiveHeader::new(seg_count, 0)
    }

    #[test]
    fn lru_eviction_on_count_cap() {
        let dict = SymbolicDictionary::new();
        let policy = SecurityPolicy::default();
        let mut wf = Wavefront::new(dummy_header(10), dict, None, policy, 3, 64 * 1024 * 1024);

        let decompress = |i: u32| Ok(vec![i as u8; 100]);

        wf.load_segment(0, decompress).unwrap();
        wf.load_segment(1, decompress).unwrap();
        wf.load_segment(2, decompress).unwrap();
        wf.load_segment(3, decompress).unwrap(); // should evict 0

        assert!(!wf.cache.contains_key(&0));
        assert!(wf.cache.contains_key(&1));
        assert!(wf.cache.contains_key(&2));
        assert!(wf.cache.contains_key(&3));
        assert_eq!(wf.resident_segments(), 3);
    }

    #[test]
    fn lru_eviction_on_byte_cap() {
        let dict = SymbolicDictionary::new();
        let policy = SecurityPolicy::default();
        let mut wf = Wavefront::new(dummy_header(10), dict, None, policy, 100, 250);

        let decompress = |i: u32| Ok(vec![i as u8; 100]);

        wf.load_segment(0, decompress).unwrap(); // 100 bytes
        wf.load_segment(1, decompress).unwrap(); // 200 bytes
        wf.load_segment(2, decompress).unwrap(); // would be 300, evict 0

        assert!(!wf.cache.contains_key(&0));
        assert!(wf.cache.contains_key(&1));
        assert!(wf.cache.contains_key(&2));
    }

    #[test]
    fn clear_drops_all() {
        let dict = SymbolicDictionary::new();
        let policy = SecurityPolicy::default();
        let mut wf = Wavefront::new(dummy_header(10), dict, None, policy, 5, 64 * 1024 * 1024);

        wf.load_segment(0, |i| Ok(vec![i as u8; 10])).unwrap();
        wf.clear();

        assert_eq!(wf.resident_segments(), 0);
        assert_eq!(wf.cached_bytes, 0);
    }
}
