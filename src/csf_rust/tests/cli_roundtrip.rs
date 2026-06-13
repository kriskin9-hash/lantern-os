use std::fs;
use std::process::Command;

fn csf_bin() -> &'static str {
    env!("CARGO_BIN_EXE_csf")
}

fn compress_decompress(payload: &[u8]) -> Vec<u8> {
    let temp = tempfile::tempdir().unwrap();
    let input = temp.path().join("input.bin");
    let archive = temp.path().join("archive.csf");
    let output = temp.path().join("output.bin");

    fs::write(&input, payload).unwrap();

    let c = Command::new(csf_bin())
        .args([
            "compress",
            input.to_str().unwrap(),
            "-o",
            archive.to_str().unwrap(),
        ])
        .status()
        .unwrap();
    assert!(c.success(), "compress failed");

    let d = Command::new(csf_bin())
        .args([
            "decompress",
            archive.to_str().unwrap(),
            "-o",
            output.to_str().unwrap(),
        ])
        .status()
        .unwrap();
    assert!(d.success(), "decompress failed");

    fs::read(&output).unwrap()
}

#[test]
fn cli_roundtrips_binary_payload() {
    let payload = b"Garden Table\nLantern\0\xff punctuation stays: .,!?\nspacing   stays\n";
    assert_eq!(compress_decompress(payload), payload);
}

#[test]
fn cli_roundtrips_empty_file() {
    assert_eq!(compress_decompress(b""), b"");
}

#[test]
fn cli_roundtrips_all_byte_values() {
    let payload: Vec<u8> = (0u8..=255u8).cycle().take(1024).collect();
    assert_eq!(compress_decompress(&payload), payload);
}
