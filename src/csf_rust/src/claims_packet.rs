//! Claims Packet — Mesh-syncable unit containing all 5 primitives,
//! wavefront state, and time-dilation parameters. ORION v1.0 core.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Stable random UUIDv4 without pulling uuid crate — 16-byte random array
/// formatted as hex. Use `ClaimsPacket::new_id()` to generate.
pub type PacketId = [u8; 16];

/// All five regulatory primitives + mesh routing in one transportable unit.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClaimsPacket {
    pub packet_id: String,
    pub timestamp_ms: u64,
    pub node_id: String,
    pub human_observer_id: Option<String>,

    // Regulatory primitives
    pub pcsf: PCSFState,
    pub ccf_claims: Vec<CapabilityClaim>,
    pub nap_violations: Vec<NAPViolation>,
    pub dcf_label: DCFLabel,
    pub aapf_summary: AAPFSummary,

    // Kesseract navigation
    pub wavefront: WavefrontSlice,
    pub observer_focus: f32,

    // Time dilation
    pub internal_multiplier: f32,
    pub external_dilation: f32,

    // Symbolic delta payload
    pub symbolic_delta: HashMap<String, serde_json::Value>,
    pub signature: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PCSFState {
    pub healthy: Vec<String>,
    pub degraded: Vec<String>,
    pub quota: HashMap<String, u32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CapabilityClaim {
    pub capability: String,
    pub tier: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NAPViolation {
    pub rule: String,
    pub reason: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum DCFLabel {
    Private,
    Symbolic,
    Shared,
    Public,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AAPFSummary {
    pub action_count: u32,
    pub last_action: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WavefrontSlice {
    pub center: String,
    pub radius: u32,
    pub key_symbols: Vec<String>,
    pub strength: f32,
}

impl ClaimsPacket {
    pub fn new(node_id: String, human_id: Option<String>) -> Self {
        Self {
            packet_id: Self::new_id(),
            timestamp_ms: Self::now_ms(),
            node_id,
            human_observer_id: human_id,
            pcsf: PCSFState {
                healthy: vec!["ollama".into()],
                degraded: vec![],
                quota: HashMap::new(),
            },
            ccf_claims: vec![],
            nap_violations: vec![],
            dcf_label: DCFLabel::Symbolic,
            aapf_summary: AAPFSummary {
                action_count: 0,
                last_action: "init".into(),
            },
            wavefront: WavefrontSlice {
                center: "lantern_core".into(),
                radius: 512,
                key_symbols: vec!["birds_and_bees".into()],
                strength: 0.68,
            },
            observer_focus: 0.82,
            internal_multiplier: 8.0,
            external_dilation: 1.0,
            symbolic_delta: HashMap::new(),
            signature: None,
        }
    }

    pub fn add_symbolic_delta(&mut self, key: &str, value: impl Into<serde_json::Value>) {
        self.symbolic_delta.insert(key.to_string(), value.into());
    }

    pub fn dilation_ratio(&self) -> f32 {
        if self.external_dilation == 0.0 {
            return self.internal_multiplier;
        }
        self.internal_multiplier / self.external_dilation
    }

    pub fn to_json(&self) -> Result<String, serde_json::Error> {
        serde_json::to_string_pretty(self)
    }

    pub fn from_json(s: &str) -> Result<Self, serde_json::Error> {
        serde_json::from_str(s)
    }

    fn new_id() -> String {
        // Simple deterministic-enough ID using timestamp + process info
        // Replace with uuid crate if true randomness needed
        format!("cp-{:x}", Self::now_ms())
    }

    fn now_ms() -> u64 {
        use std::time::{SystemTime, UNIX_EPOCH};
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_millis() as u64
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn roundtrip_json() {
        let mut p = ClaimsPacket::new("test-node".into(), Some("alex".into()));
        p.add_symbolic_delta("intent", "dream capture");
        let json = p.to_json().unwrap();
        let p2 = ClaimsPacket::from_json(&json).unwrap();
        assert_eq!(p.node_id, p2.node_id);
        assert!((p.observer_focus - p2.observer_focus).abs() < 1e-6);
    }

    #[test]
    fn dilation_ratio() {
        let mut p = ClaimsPacket::new("node".into(), None);
        p.internal_multiplier = 8.0;
        p.external_dilation = 0.4;
        assert!((p.dilation_ratio() - 20.0).abs() < 1e-4);
    }
}
