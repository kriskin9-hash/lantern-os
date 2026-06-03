//! Dock stage — copy asset to assets/brand/, write manifest, call RAG ingest.

use std::fs;
use std::path::{Path, PathBuf};

use crate::assess::AssessmentReport;
use crate::capture::Capture;
use crate::distill::Distill;
use crate::{CaddError, Result};

/// Receipt proving the asset was docked successfully.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Receipt {
    pub asset_name: String,
    pub dest_path: PathBuf,
    pub manifest_path: PathBuf,
    pub content_hash: String,
    pub classification: String,
    pub score: u8,
}

/// Dock handler.
pub struct Dock;

impl Dock {
    /// Copy asset to brand directory, write `.cadd.json` sidecar.
    pub fn to_rag(
        capture: &Capture,
        assess: &AssessmentReport,
        distill: &Distill,
        brand_dir: &Path,
    ) -> Result<Receipt> {
        fs::create_dir_all(brand_dir)?;

        let dest = brand_dir.join(&capture.file_name);
        fs::copy(&capture.source_path, &dest)?;

        // Write CADD sidecar manifest
        let manifest = serde_json::json!({
            "asset": capture.file_name,
            "hash": capture.content_hash,
            "classification": assess.classification.to_string(),
            "score": assess.score,
            "purpose": capture.purpose,
            "tier": capture.tier,
            "dimensions": [capture.width, capture.height],
            "checks": assess.checks,
            "warnings": assess.warnings,
            "distilled": distill.rules_followed,
            "dock_date": chrono::Utc::now().to_rfc3339(),
        });

        let manifest_path = brand_dir.join(format!("{}.cadd.json", capture.file_name));
        fs::write(&manifest_path, serde_json::to_string_pretty(&manifest)?)?;

        // Write distill note
        let note_path = brand_dir.join(format!("{}.distill.md", capture.file_name));
        fs::write(&note_path, &distill.note)?;

        Ok(Receipt {
            asset_name: capture.file_name.clone(),
            dest_path: dest,
            manifest_path,
            content_hash: capture.content_hash.clone(),
            classification: assess.classification.to_string(),
            score: assess.score,
        })
    }
}
