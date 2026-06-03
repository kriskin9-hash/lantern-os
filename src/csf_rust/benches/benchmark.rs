//! Rust criterion benchmarks for CSF vs zstd / gzip.
//!
//! Run: `cargo bench`

use std::io::{Read, Write};

use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};

use csf::{Compressor, CompressionMode, Decompressor, SecurityPolicy};

fn generate_symbolic_text(target_bytes: usize) -> String {
    let words = [
        "Lantern", "Garden", "Keystone", "Return", "Door", "Anchor",
        "Wish", "Founder", "Convergence", "CityOfDoors", "Sigil",
        "Table", "Love", "Safety", "Truth", "Beauty", "Freedom",
        "Memory", "Gage", "Xenon", "Fog", "Cloud", "Sea",
        "Blinkbug", "Dream", "Mirror", "Reflection", "Light",
        "Path", "Threshold", "Crossing", "Waking", "Sleeping",
    ];
    let mut s = String::with_capacity(target_bytes);
    while s.len() < target_bytes {
        s.push_str(words[s.len() % words.len()]);
        s.push(' ');
    }
    s
}

fn generate_json(target_bytes: usize) -> String {
    let keys = ["timestamp", "agent_id", "message", "kind", "severity", "channel", "state"];
    let mut s = String::with_capacity(target_bytes);
    s.push('[');
    let mut idx = 0;
    while s.len() < target_bytes {
        if idx > 0 { s.push(','); }
        s.push_str("{\"timestamp\":1717422000,\"agent_id\":\"agent-");
        s.push_str(&idx.to_string());
        s.push_str("\",\"message\":\"Convergence detected in sector 7\",\"kind\":\"event\",\"severity\":\"info\",\"channel\":\"dream\",\"state\":\"active\"}");
        idx += 1;
    }
    s.push(']');
    s
}

fn bench_compress_symbolic(c: &mut Criterion) {
    let policy = SecurityPolicy::default();
    let text = generate_symbolic_text(2_000_000);

    let mut group = c.benchmark_group("compress_symbolic_2mb");
    group.throughput(Throughput::Bytes(text.len() as u64));

    group.bench_function(BenchmarkId::new("csf", "v1.0-full"), |b| {
        b.iter(|| {
            let mut comp = Compressor::new(policy.clone());
            let _ = comp.compress_text(black_box(&text)).unwrap();
        });
    });

    group.bench_function(BenchmarkId::new("zstd", "level3"), |b| {
        b.iter(|| {
            let _ = zstd::encode_all(black_box(text.as_bytes()), 3).unwrap();
        });
    });

    group.bench_function(BenchmarkId::new("gzip", "level6"), |b| {
        b.iter(|| {
            use flate2::write::GzEncoder;
            use flate2::Compression;
            let mut enc = GzEncoder::new(Vec::new(), Compression::new(6));
            enc.write_all(black_box(text.as_bytes())).unwrap();
            let _ = enc.finish().unwrap();
        });
    });

    group.finish();
}

fn bench_compress_json(c: &mut Criterion) {
    let policy = SecurityPolicy::default();
    let text = generate_json(1_000_000);

    let mut group = c.benchmark_group("compress_json_1mb");
    group.throughput(Throughput::Bytes(text.len() as u64));

    group.bench_function(BenchmarkId::new("csf", "v1.0-full"), |b| {
        b.iter(|| {
            let mut comp = Compressor::new(policy.clone());
            let _ = comp.compress_text_mode(black_box(&text), CompressionMode::Full).unwrap();
        });
    });

    group.bench_function(BenchmarkId::new("csf", "v1.0-fast"), |b| {
        b.iter(|| {
            let mut comp = Compressor::new(policy.clone());
            let _ = comp.compress_text_mode(black_box(&text), CompressionMode::Fast).unwrap();
        });
    });

    group.bench_function(BenchmarkId::new("zstd", "level3"), |b| {
        b.iter(|| {
            let _ = zstd::encode_all(black_box(text.as_bytes()), 3).unwrap();
        });
    });

    group.bench_function(BenchmarkId::new("zstd", "level1"), |b| {
        b.iter(|| {
            let _ = zstd::encode_all(black_box(text.as_bytes()), 1).unwrap();
        });
    });

    group.finish();
}

criterion_group!(benches, bench_compress_symbolic, bench_compress_json);
criterion_main!(benches);
