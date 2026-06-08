use std::fs;
use std::process::Command;

#[test]
fn cli_roundtrips_binary_payload() {
    let bin = env!("CARGO_BIN_EXE_csf");
    let temp = tempfile::tempdir().unwrap();
    let input = temp.path().join("input.bin");
    let archive = temp.path().join("archive.csf");
    let output = temp.path().join("output.bin");

    let payload = b"Garden Table\nLantern\0\xff punctuation stays: .,!?\nspacing   stays\n";
    fs::write(&input, payload).unwrap();

    let compress = Command::new(bin)
        .arg("compress")
        .arg(&input)
        .arg("-o")
        .arg(&archive)
        .status()
        .unwrap();
    assert!(compress.success());

    let decompress = Command::new(bin)
        .arg("decompress")
        .arg(&archive)
        .arg("-o")
        .arg(&output)
        .status()
        .unwrap();
    assert!(decompress.success());

    assert_eq!(fs::read(&output).unwrap(), payload);
}
