//! CLI binary for CADD — capture, assess, distill, dock, watch.
//!
//! Usage:
//!   cadd capture image.png --purpose patreon-card --tier pro
//!   cadd assess image.png
//!   cadd distill image.png
//!   cadd dock image.png --brand-dir assets/brand/
//!   cadd validate image.png --purpose patreon-card --tier pro --brand-dir assets/brand/
//!   cadd watch /assets/incoming --brand-dir /assets/brand

use std::path::PathBuf;
use std::thread;
use std::time::Duration;

use clap::{Parser, Subcommand};

use cadd::{Assess, Capture, Distill, Dock};

#[derive(Parser)]
#[command(name = "cadd")]
#[command(about = "Capture, Assess, Distill, Dock — brand asset pipeline")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Capture metadata from an asset file.
    Capture {
        file: PathBuf,
        #[arg(short, long)]
        purpose: String,
        #[arg(short, long)]
        tier: String,
    },
    /// Assess an asset against brand rules.
    Assess {
        file: PathBuf,
    },
    /// Distill a markdown note from capture + assessment.
    Distill {
        file: PathBuf,
    },
    /// Dock an asset to the brand directory with manifest.
    Dock {
        file: PathBuf,
        #[arg(short, long)]
        purpose: String,
        #[arg(short, long)]
        tier: String,
        #[arg(short, long, default_value = "assets/brand")]
        brand_dir: PathBuf,
    },
    /// Full pipeline: capture -> assess -> distill -> dock.
    Validate {
        file: PathBuf,
        #[arg(short, long)]
        purpose: String,
        #[arg(short, long)]
        tier: String,
        #[arg(short, long, default_value = "assets/brand")]
        brand_dir: PathBuf,
    },
    /// Watch a directory for new assets and auto-validate them.
    Watch {
        #[arg(help = "Directory to watch for incoming assets")]
        watch_dir: PathBuf,
        #[arg(short, long, default_value = "assets/brand")]
        brand_dir: PathBuf,
        #[arg(short, long, default_value = "patreon-card")]
        purpose: String,
        #[arg(short, long, default_value = "normal")]
        tier: String,
    },
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();
    match cli.command {
        Commands::Capture { file, purpose, tier } => {
            let cap = Capture::from_file(&file)?
                .with_purpose(&purpose)
                .with_tier(&tier);
            println!("Captured: {}", serde_json::to_string_pretty(&cap)?);
        }
        Commands::Assess { file } => {
            let cap = Capture::from_file(&file)?;
            let report = Assess::validate(&cap)?;
            println!("Assessment: {}", serde_json::to_string_pretty(&report)?);
        }
        Commands::Distill { file } => {
            let cap = Capture::from_file(&file)?;
            let report = Assess::validate(&cap)?;
            let distill = Distill::from_capture(&cap, &report)?;
            println!("{}", distill.note);
        }
        Commands::Dock { file, purpose, tier, brand_dir } => {
            let cap = Capture::from_file(&file)?
                .with_purpose(&purpose)
                .with_tier(&tier);
            let report = Assess::validate(&cap)?;
            let distill = Distill::from_capture(&cap, &report)?;
            let receipt = Dock::to_rag(&cap, &report, &distill, &brand_dir)?;
            println!("Docked: {}", serde_json::to_string_pretty(&receipt)?);
        }
        Commands::Validate { file, purpose, tier, brand_dir } => {
            let cap = Capture::from_file(&file)?
                .with_purpose(&purpose)
                .with_tier(&tier);
            let report = Assess::validate(&cap)?;
            println!("Score: {}/100 — {}", report.score, report.classification);
            if !report.warnings.is_empty() {
                for w in &report.warnings {
                    println!("Warning: {}", w);
                }
            }
            let distill = Distill::from_capture(&cap, &report)?;
            let receipt = Dock::to_rag(&cap, &report, &distill, &brand_dir)?;
            println!("Receipt: {}", serde_json::to_string_pretty(&receipt)?);
        }
        Commands::Watch { watch_dir, brand_dir, purpose, tier } => {
            println!("Watching {} for new assets...", watch_dir.display());
            println!("Brand directory: {}", brand_dir.display());
            println!("Press Ctrl+C to stop.");
            loop {
                if let Ok(entries) = std::fs::read_dir(&watch_dir) {
                    for entry in entries.flatten() {
                        let path = entry.path();
                        if path.is_file() && path.extension().and_then(|s| s.to_str()) == Some("png") {
                            println!("\nProcessing: {}", path.display());
                            let cap = Capture::from_file(&path)?
                                .with_purpose(&purpose)
                                .with_tier(&tier);
                            let report = Assess::validate(&cap)?;
                            println!("  Score: {}/100 — {}", report.score, report.classification);
                            if report.score >= 70 {
                                let distill = Distill::from_capture(&cap, &report)?;
                                let receipt = Dock::to_rag(&cap, &report, &distill, &brand_dir)?;
                                println!("  Docked: {}", receipt.dest_path.display());
                                // Move processed file out of incoming
                                let _ = std::fs::remove_file(&path);
                            } else {
                                println!("  REJECTED — not docking");
                            }
                        }
                    }
                }
                thread::sleep(Duration::from_secs(5));
            }
        }
    }
    Ok(())
}
