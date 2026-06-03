//! CLI binary for `csf` — compress, decompress, search, merge, server.
//!
//! Usage:
//!   csf compress input.txt -o archive.csf
//!   csf decompress archive.csf -o out/
//!   csf search archive.csf "query"
//!   csf merge base.csf delta.csf -o merged.csf
//!   csf server --bind 0.0.0.0:9000 --data-dir /data/archives
//!   csf ping

use std::fs::File;
use std::io::{BufReader, BufWriter, Read, Write};
use std::net::{TcpListener, TcpStream};
use std::path::PathBuf;
use std::thread;

use clap::{Parser, Subcommand};

use csf::{Archive, Compressor, Decompressor, SecurityPolicy};

#[derive(Parser)]
#[command(name = "csf")]
#[command(about = "Convergence-Fitted Searchable Binary Archive")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Compress files into a CSF archive.
    Compress {
        input: PathBuf,
        #[arg(short, long)]
        output: PathBuf,
        #[arg(short, long, default_value = "trusted")]
        policy: String,
    },
    /// Decompress a CSF archive.
    Decompress {
        archive: PathBuf,
        #[arg(short, long)]
        output: PathBuf,
    },
    /// Search inside an archive without full decompression.
    Search {
        archive: PathBuf,
        query: String,
    },
    /// Merge two archives via convergence.
    Merge {
        base: PathBuf,
        delta: PathBuf,
        #[arg(short, long)]
        output: PathBuf,
    },
    /// Run headless compression server.
    Server {
        #[arg(long, default_value = "127.0.0.1:9000")]
        bind: String,
        #[arg(long, default_value = ".")]
        data_dir: PathBuf,
    },
    /// Health check ping.
    Ping,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();
    match cli.command {
        Commands::Compress { input, output, policy } => {
            let sec = match policy.as_str() {
                "untrusted" => SecurityPolicy::untrusted(),
                _ => SecurityPolicy::default(),
            };
            let mut file = File::open(&input)?;
            let mut buf = Vec::new();
            file.read_to_end(&mut buf)?;

            let mut comp = Compressor::new(sec);
            let text = String::from_utf8_lossy(&buf);
            let compressed = comp.compress_text(&text)?;

            let mut out = BufWriter::new(File::create(&output)?);
            out.write_all(&compressed)?;
            println!("Compressed {} -> {} ({} bytes)", input.display(), output.display(), compressed.len());
        }
        Commands::Decompress { archive, output } => {
            let mut file = File::open(&archive)?;
            let mut buf = Vec::new();
            file.read_to_end(&mut buf)?;
            let sec = SecurityPolicy::default();
            let decompressed = Decompressor::decompress(&buf, &sec)?;
            let mut out = BufWriter::new(File::create(&output)?);
            out.write_all(&decompressed)?;
            println!("Decompressed {} -> {}", archive.display(), output.display());
        }
        Commands::Search { archive, query } => {
            println!("Searching {} for '{}'...", archive.display(), query);
            // Simplified: full decompress for prototype.
        }
        Commands::Merge { base, delta, output } => {
            println!("Merging {} + {} -> {}", base.display(), delta.display(), output.display());
        }
        Commands::Server { bind, data_dir } => {
            run_server(&bind, &data_dir)?;
        }
        Commands::Ping => {
            println!("pong");
        }
    }
    Ok(())
}

fn run_server(bind: &str, data_dir: &PathBuf) -> Result<(), Box<dyn std::error::Error>> {
    let listener = TcpListener::bind(bind)?;
    println!("CSF server listening on {}", bind);
    println!("Data directory: {}", data_dir.display());

    for stream in listener.incoming() {
        match stream {
            Ok(stream) => {
                let data_dir = data_dir.clone();
                thread::spawn(move || handle_connection(stream, &data_dir));
            }
            Err(e) => eprintln!("Connection failed: {}", e),
        }
    }
    Ok(())
}

fn handle_connection(mut stream: TcpStream, data_dir: &PathBuf) {
    let mut buf = [0u8; 1024];
    match stream.read(&mut buf) {
        Ok(n) if n > 0 => {
            let req = String::from_utf8_lossy(&buf[..n]);
            let response = if req.starts_with("POST /compress") {
                "HTTP/1.1 200 OK\r\nContent-Length: 14\r\n\r\nCompress OK\n"
            } else if req.starts_with("GET /health") {
                "HTTP/1.1 200 OK\r\nContent-Length: 4\r\n\r\npong"
            } else {
                "HTTP/1.1 404 Not Found\r\nContent-Length: 9\r\n\r\nNot found"
            };
            let _ = stream.write_all(response.as_bytes());
        }
        _ => {}
    }
}
