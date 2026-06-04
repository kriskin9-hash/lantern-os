//! CADD — Capture, Assess, Distill, Dock
//!
//! Brand/asset validation pipeline for Dream Journal by Lantern OS.
//! Ensures every image, prompt, card, and visual asset passes through
//! a consistent workflow before entering the RAG dollhouse or public channels.
//!
//! # Pipeline
//! 1. **Capture** — Record the asset, source, date, purpose, tier role.
//! 2. **Assess** — Classify against brand rules (source-of-truth, candidate, rejected).
//! 3. **Distill** — Write a markdown note: what it is, what rules it follows.
//! 4. **Dock** — Pass to RAG dollhouse for copy, hash, manifest, flat reference.
//!
//! # Quick start
//! ```ignore
//! use cadd::{Capture, Assess, Distill, Dock};
//!
//! let capture = Capture::from_file("card.png")?;
//! let assess = Assess::validate(&capture)?;
//! let distill = Distill::from_capture(&capture, &assess)?;
//! let receipt = Dock::to_rag(&capture, &distill)?;
//! ```

pub mod assess;
pub mod capture;
pub mod dock;
pub mod distill;

use thiserror::Error;

/// Crate-wide error type.
#[derive(Debug, Error)]
pub enum CaddError {
    #[error("io error: {0}")]
    Io(#[from] std::io::Error),

    #[error("image decode error: {0}")]
    ImageDecode(String),

    #[error("validation failed: {0}")]
    Validation(String),

    #[error("asset rejected: {0}")]
    Rejected(String),

    #[error("manifest error: {0}")]
    Manifest(String),

    #[error("serialization error: {0}")]
    Serialize(#[from] serde_json::Error),
}

pub type Result<T> = std::result::Result<T, CaddError>;

/// Re-export pipeline stages.
pub use assess::{Assess, AssessmentReport, Classification};
pub use capture::Capture;
pub use dock::{Dock, Receipt};
pub use distill::Distill;
