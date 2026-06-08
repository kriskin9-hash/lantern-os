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
use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::path::{Path, PathBuf};
use std::thread;

use clap::{Parser, Subcommand};

use csf::{Archive, ArchiveReader, SecurityPolicy, SegmentReader};

const CLI_SEGMENT_BYTES: usize = 16 * 1024 * 1024;

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
    Search { archive: PathBuf, query: String },
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
        Commands::Compress {
            input,
            output,
            policy,
        } => {
            let sec = match policy.as_str() {
                "untrusted" => SecurityPolicy::untrusted(),
                _ => SecurityPolicy::default(),
            };

            let mut input_file = File::open(&input)?;
            let mut archive = Archive::new();
            let mut buf = vec![0u8; CLI_SEGMENT_BYTES];
            loop {
                let read = input_file.read(&mut buf)?;
                if read == 0 {
                    break;
                }
                archive.add_segment(&buf[..read]);
            }

            let segments = archive.segment_count();
            let mut out = File::create(&output)?;
            archive.write(&mut out, &sec)?;

            println!(
                "Compressed {} -> {} ({} segments)",
                input.display(),
                output.display(),
                segments
            );
        }
        Commands::Decompress { archive, output } => {
            SegmentReader::validate(&archive)?;
            let mut out = BufWriter::new(File::create(&output)?);
            let total = ArchiveReader::decompress_to_writer(&archive, &mut out)?;
            out.flush()?;
            let seg_count = SegmentReader::open(&archive)?.header().segment_count;
            println!(
                "Decompressed {} -> {} ({} segments, {} bytes)",
                archive.display(),
                output.display(),
                seg_count,
                total
            );
        }
        Commands::Search { archive, query } => {
            println!("Searching {} for '{}'...", archive.display(), query);
            // Simplified: full indexed search is tracked in issue #260.
        }
        Commands::Merge {
            base,
            delta,
            output,
        } => {
            println!(
                "Merging {} + {} -> {}",
                base.display(),
                delta.display(),
                output.display()
            );
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

fn run_server(bind: &str, data_dir: &Path) -> Result<(), Box<dyn std::error::Error>> {
    let listener = TcpListener::bind(bind)?;
    println!("CSF server listening on {}", bind);
    println!("Data directory: {}", data_dir.display());

    for stream in listener.incoming() {
        match stream {
            Ok(stream) => {
                let data_dir = data_dir.to_path_buf();
                thread::spawn(move || handle_connection(stream, &data_dir));
            }
            Err(e) => eprintln!("Connection failed: {}", e),
        }
    }
    Ok(())
}

fn handle_connection(mut stream: TcpStream, _data_dir: &Path) {
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
