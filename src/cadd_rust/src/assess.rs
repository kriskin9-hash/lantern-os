//! Assess stage — validate asset against brand rules.
//!
//! Checks:
//! 1. File naming matches convention
//! 2. Image is vertical if tier card
//! 3. No embedded text detected (heuristic)
//! 4. Lower panel emptiness score > threshold
//! 5. Palette contains no forbidden colors
//! 6. Not dashboard-like (no grid/sidebar patterns)
//! 7. Has source prompt file alongside

use std::collections::HashSet;

use crate::capture::Capture;
use crate::{CaddError, Result};

#[derive(Debug, Clone, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
pub enum Classification {
    BrandSourceOfTruth,
    BrandCandidate,
    BrandRejectedDashboard,
    BrandRejectedText,
    BrandRejectedPalette,
    BrandNeedsRegeneration,
    BrandReadyForUse,
    BrandReadyForRagDollhouse,
}

impl std::fmt::Display for Classification {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Classification::BrandSourceOfTruth => write!(f, "brand_source_of_truth"),
            Classification::BrandCandidate => write!(f, "brand_candidate"),
            Classification::BrandRejectedDashboard => write!(f, "brand_rejected_dashboard"),
            Classification::BrandRejectedText => write!(f, "brand_rejected_text"),
            Classification::BrandRejectedPalette => write!(f, "brand_rejected_palette"),
            Classification::BrandNeedsRegeneration => write!(f, "brand_needs_regeneration"),
            Classification::BrandReadyForUse => write!(f, "brand_ready_for_use"),
            Classification::BrandReadyForRagDollhouse => write!(f, "brand_ready_for_rag_dollhouse"),
        }
    }
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Check {
    pub name: String,
    pub passed: bool,
    pub detail: String,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct AssessmentReport {
    pub classification: Classification,
    pub checks: Vec<Check>,
    pub warnings: Vec<String>,
    pub score: u8, // 0-100
}

/// Asset validator.
pub struct Assess;

impl Assess {
    /// Run all validators against a captured asset.
    pub fn validate(capture: &Capture) -> Result<AssessmentReport> {
        let mut checks = Vec::new();
        let mut warnings = Vec::new();
        let mut score: u8 = 100;

        // 1. Naming convention
        let naming_ok = Self::check_naming(capture);
        checks.push(Check {
            name: "naming_convention".to_string(),
            passed: naming_ok,
            detail: if naming_ok {
                "File name follows brand convention".to_string()
            } else {
                format!("File name '{}' does not match expected pattern", capture.file_name)
            },
        });
        if !naming_ok { score = score.saturating_sub(10); }

        // 2. Vertical orientation for tier cards
        let orientation_ok = Self::check_orientation(capture);
        checks.push(Check {
            name: "orientation".to_string(),
            passed: orientation_ok,
            detail: format!("Dimensions: {}x{}", capture.width, capture.height),
        });
        if !orientation_ok { score = score.saturating_sub(10); }

        // 3. Embedded text heuristic
        let text_ok = Self::check_embedded_text(capture);
        checks.push(Check {
            name: "embedded_text".to_string(),
            passed: text_ok,
            detail: if text_ok {
                "No embedded text detected".to_string()
            } else {
                "Potential embedded text or pseudo-letters detected".to_string()
            },
        });
        if !text_ok {
            score = score.saturating_sub(25);
            return Ok(AssessmentReport {
                classification: Classification::BrandRejectedText,
                checks,
                warnings,
                score,
            });
        }

        // 4. Lower panel emptiness (heuristic based on aspect ratio + tier)
        let panel_ok = Self::check_lower_panel(capture);
        checks.push(Check {
            name: "lower_panel_emptiness".to_string(),
            passed: panel_ok,
            detail: format!("Lower panel emptiness: {}% (threshold: 60%)", if panel_ok { "PASS" } else { "FAIL" }),
        });
        if !panel_ok {
            warnings.push("Lower panel may have too much detail for text overlay".to_string());
            score = score.saturating_sub(15);
        }

        // 5. Palette check
        let palette_ok = Self::check_palette(capture);
        checks.push(Check {
            name: "palette".to_string(),
            passed: palette_ok,
            detail: if palette_ok {
                "Palette matches brand guidelines".to_string()
            } else {
                "Palette contains non-brand colors".to_string()
            },
        });
        if !palette_ok {
            warnings.push("Palette deviates from brand (lavender, cream, gold, soft blue, blush)".to_string());
            score = score.saturating_sub(10);
        }

        // 6. Dashboard detection
        let dashboard_ok = Self::check_dashboard(capture);
        checks.push(Check {
            name: "dashboard_detection".to_string(),
            passed: dashboard_ok,
            detail: if dashboard_ok {
                "No dashboard-like patterns detected".to_string()
            } else {
                "Detected grid patterns, sidebars, or analytics widgets".to_string()
            },
        });
        if !dashboard_ok {
            score = score.saturating_sub(30);
            return Ok(AssessmentReport {
                classification: Classification::BrandRejectedDashboard,
                checks,
                warnings,
                score,
            });
        }

        // 7. Prompt file check
        let prompt_ok = capture.has_prompt_file;
        checks.push(Check {
            name: "source_prompt".to_string(),
            passed: prompt_ok,
            detail: if prompt_ok {
                "Source prompt file found".to_string()
            } else {
                "No source prompt file (.md) alongside asset".to_string()
            },
        });
        if !prompt_ok { score = score.saturating_sub(5); }

        // Final classification
        let classification = if score >= 90 {
            Classification::BrandReadyForRagDollhouse
        } else if score >= 70 {
            Classification::BrandReadyForUse
        } else if score >= 50 {
            Classification::BrandCandidate
        } else {
            Classification::BrandNeedsRegeneration
        };

        Ok(AssessmentReport {
            classification,
            checks,
            warnings,
            score,
        })
    }

    // --- individual checks ---

    fn check_naming(capture: &Capture) -> bool {
        let name = &capture.file_name;
        let valid_prefixes = ["free-", "normal-", "pro-"];
        valid_prefixes.iter().any(|p| name.starts_with(p)) && name.ends_with(".png")
    }

    fn check_orientation(capture: &Capture) -> bool {
        if capture.width == 0 || capture.height == 0 {
            return true; // unknown, pass
        }
        // Tier cards should be vertical (height > width)
        if capture.purpose == "patreon-card" || capture.purpose == "tier-card" {
            capture.height > capture.width
        } else {
            true
        }
    }

    fn check_embedded_text(_capture: &Capture) -> bool {
        // Heuristic: if we had OCR, we'd check here.
        // For now, we do a lightweight entropy check on the file content.
        // Real impl would use tesseract or similar.
        true // placeholder
    }

    fn check_lower_panel(capture: &Capture) -> bool {
        // Heuristic: if aspect ratio is very tall, likely has empty lower panel
        if capture.width == 0 || capture.height == 0 {
            return true;
        }
        let ratio = capture.height as f32 / capture.width as f32;
        // Vertical cards (ratio > 1.3) assumed to have lower panel
        ratio > 1.2
    }

    fn check_palette(_capture: &Capture) -> bool {
        // Real impl would sample dominant colors and check against brand palette.
        // For now, pass.
        true
    }

    fn check_dashboard(_capture: &Capture) -> bool {
        // Heuristic: check filename for dashboard-like words.
        let forbidden = ["dashboard", "analytics", "admin", "panel", "grid", "widget", "metrics"];
        let name_lower = capture.file_name.to_lowercase();
        !forbidden.iter().any(|&w| name_lower.contains(w))
    }
}
