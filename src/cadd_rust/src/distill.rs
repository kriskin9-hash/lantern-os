//! Distill stage — write a markdown note describing the asset.

use std::fs;
use std::path::{Path, PathBuf};

use crate::assess::AssessmentReport;
use crate::capture::Capture;
use crate::{CaddError, Result};

#[derive(Debug, Clone)]
pub struct Distill {
    pub asset_path: PathBuf,
    pub note: String,
    pub rules_followed: Vec<String>,
    pub must_not_change: Vec<String>,
}

impl Distill {
    /// Generate a distilled markdown note from capture + assessment.
    pub fn from_capture(capture: &Capture, assess: &AssessmentReport) -> Result<Self> {
        let mut rules = Vec::new();
        let mut must_not = Vec::new();

        rules.push(format!("Purpose: {}", capture.purpose));
        rules.push(format!("Tier: {}", capture.tier));
        rules.push(format!("Dimensions: {}x{}", capture.width, capture.height));
        rules.push(format!("File size: {} bytes", capture.file_size));

        for check in &assess.checks {
            if check.passed {
                rules.push(format!("✓ {}", check.name));
            } else {
                must_not.push(format!("✗ {} — {}", check.name, check.detail));
            }
        }

        for warn in &assess.warnings {
            must_not.push(format!("⚠ {}", warn));
        }

        let note = format!(
            "# Asset Distillation: {}\n\n\
             **Classification:** {}\n\n\
             **Score:** {}/100\n\n\
             ## Rules Followed\n\n{}",
            capture.file_name,
            assess.classification,
            assess.score,
            rules.iter().map(|r| format!("- {}\n", r)).collect::<String>(),
        );

        Ok(Self {
            asset_path: capture.source_path.clone(),
            note,
            rules_followed: rules,
            must_not_change: must_not,
        })
    }

    /// Write the distilled note to a `.distill.md` sidecar file.
    pub fn write_to_file<P: AsRef<Path>>(&self, path: P) -> Result<()> {
        fs::write(path, &self.note)?;
        Ok(())
    }
}
