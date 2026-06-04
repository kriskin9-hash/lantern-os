//! Symbolic Dictionary Layer (L1) — spec §3.1.
//!
//! Eliminates redundant strings by mapping recurring tokens to compact IDs.
//! Hardened: pre-allocated capacity limits, no unbounded growth.

use byteorder::{BigEndian, ReadBytesExt, WriteBytesExt};
use std::collections::HashMap;
use std::io::{Read, Write};

use crate::{CsfError, Result, SecurityPolicy};

/// Frequency-sorted symbol table with bidirectional lookup.
#[derive(Debug, Clone, Default)]
pub struct SymbolicDictionary {
    pub(crate) token_to_id: HashMap<String, u16>,
    pub(crate) id_to_token: HashMap<u16, String>,
    pub(crate) next_id: u16,
}

impl SymbolicDictionary {
    pub fn new() -> Self {
        Self {
            next_id: 1, // 0 reserved for unknown / literal escape
            ..Default::default()
        }
    }

    /// Build dictionary from token stream. Skips tokens below `min_freq`.
    /// Hardened: stops adding if security limit reached.
    pub fn train<I>(&mut self, tokens: I, min_freq: usize, policy: &SecurityPolicy) -> Result<()>
    where
        I: IntoIterator<Item = String>,
    {
        let mut counts: HashMap<String, usize> = HashMap::new();
        for t in tokens {
            *counts.entry(t).or_insert(0) += 1;
        }

        let mut pairs: Vec<(String, usize)> = counts.into_iter().collect();
        pairs.sort_by(|a, b| b.1.cmp(&a.1)); // descending frequency

        for (token, count) in pairs {
            if count < min_freq {
                break;
            }
            if self.token_to_id.len() >= policy.max_symbol_count {
                break; // hard cap, no error — graceful degradation
            }
            if !self.token_to_id.contains_key(&token) {
                let id = self.next_id;
                self.next_id = self.next_id.wrapping_add(1);
                if id == 0 {
                    // Wrapped — safety valve.
                    break;
                }
                self.token_to_id.insert(token.clone(), id);
                self.id_to_token.insert(id, token);
            }
        }
        Ok(())
    }

    pub fn encode(&self, token: &str) -> u16 {
        *self.token_to_id.get(token).unwrap_or(&0)
    }

    pub fn decode(&self, id: u16) -> Option<&str> {
        self.id_to_token.get(&id).map(|s| s.as_str())
    }

    pub fn vocab_size(&self) -> usize {
        self.token_to_id.len()
    }

    /// Serialize to bytes: [count:2] then [id:2][len:1][token]...
    pub fn write<W: Write>(&self, writer: &mut W, policy: &SecurityPolicy) -> Result<()> {
        let buf = self.to_bytes()?;
        policy.check_dictionary(buf.len())?;
        writer.write_all(&buf)?;
        Ok(())
    }

    pub(crate) fn to_bytes(&self) -> Result<Vec<u8>> {
        let mut buf = Vec::with_capacity(2 + self.token_to_id.len() * 16);
        let count = self.token_to_id.len().min(u16::MAX as usize) as u16;
        buf.write_u16::<BigEndian>(count)?;
        for (id, token) in &self.id_to_token {
            let tok_bytes = token.as_bytes();
            if tok_bytes.len() > 255 {
                // Truncate extremely long tokens to 255 bytes.
                buf.write_u16::<BigEndian>(*id)?;
                buf.write_u8(255)?;
                buf.write_all(&tok_bytes[..255])?;
            } else {
                buf.write_u16::<BigEndian>(*id)?;
                buf.write_u8(tok_bytes.len() as u8)?;
                buf.write_all(tok_bytes)?;
            }
        }
        Ok(buf)
    }

    /// Deserialize with security check.
    pub fn read<R: Read>(reader: &mut R, policy: &SecurityPolicy) -> Result<Self> {
        let mut count_buf = [0u8; 2];
        reader.read_exact(&mut count_buf)?;
        let count = (&count_buf[..]).read_u16::<BigEndian>().unwrap() as usize;
        if count > policy.max_symbol_count {
            return Err(CsfError::DictionaryOverflow {
                max: policy.max_symbol_count,
            });
        }

        let mut dict = Self::new();
        for _ in 0..count {
            let id = reader.read_u16::<BigEndian>()?;
            let tlen = reader.read_u8()? as usize;
            if tlen > 255 {
                return Err(CsfError::Security("dictionary token length overflow"));
            }
            let mut tok = vec![0u8; tlen];
            reader.read_exact(&mut tok)?;
            let token = String::from_utf8(tok)
                .map_err(|_| CsfError::Parse("invalid UTF-8 in dictionary"))?;
            dict.token_to_id.insert(token.clone(), id);
            dict.id_to_token.insert(id, token);
            dict.next_id = dict.next_id.max(id.wrapping_add(1));
        }
        Ok(dict)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn roundtrip() {
        let mut dict = SymbolicDictionary::new();
        let policy = SecurityPolicy::default();
        dict.train(
            vec!["Garden", "Table", "Lantern", "Garden", "Table"]
                .into_iter()
                .map(|s| s.to_string()),
            2,
            &policy,
        )
        .unwrap();
        assert_eq!(dict.encode("Garden"), 1);
        assert_eq!(dict.encode("Lantern"), 2);
        assert_eq!(dict.encode("Missing"), 0); // unknown

        let mut buf = Vec::new();
        dict.write(&mut buf, &policy).unwrap();
        let parsed = SymbolicDictionary::read(&mut &buf[..], &policy).unwrap();
        assert_eq!(parsed.vocab_size(), dict.vocab_size());
    }
}
