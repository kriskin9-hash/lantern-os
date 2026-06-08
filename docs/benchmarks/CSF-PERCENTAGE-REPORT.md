# CSF Percentage Benchmark Report

Status: projection scaffold pending measured Rust benchmark results.

This report keeps CSF performance comparisons in percentage form so the project can replace projections with measured values as the implementation is completed. Measured rows should come from `docs/benchmarks/csf_competitor_benchmark.py` or its Rust-backed successor and should use identical input corpora across all formats.

## Reporting Rules

- Report compression as size reduction percentage: `1 - compressed_size / original_size`.
- Report CSF advantage as percentage-point delta versus the best non-CSF rival.
- Report speed as percentage improvement or slowdown versus the relevant baseline.
- Label every row as `Measured` or `Projected`.
- Use at least 7 trials where practical and include 95% confidence intervals for benchmark runs.

## Current Projection Table

| Scenario | CSF Status | CSF Ratio | Best Rival | Rival Ratio | CSF Advantage |
|---|---|---:|---|---:|---:|
| Normal text (2 MB) | Projected | 74% | Brotli | 80% | -6% |
| Symbolic dream-journal text (2 MB) | Projected | 89% | Brotli | 78% | +11% |
| Structured JSON (1 MB) | Projected | 87% | Zstd | 76% | +11% |
| Application logs (1 MB) | Projected | 94% | Zstd | 72% | +22% |
| Log aggregation (2 archives) | Projected | 90% | gzip | 75% | +15% |
| Moderately symbolic file (2 GB) | Projected | 84% | Brotli | 80% | +4% |
| Highly symbolic / structured file (200 TB) | Projected | 90% | Brotli | 75% | +15% |

## Measured Results Template

Replace this section once the Rust CSF binary is benchmarked directly.

| Scenario | CSF Status | CSF Ratio | ZIP Ratio | gzip Ratio | Zstd Ratio | Brotli Ratio | bzip2 Ratio | lzma Ratio | Best Rival | CSF Advantage |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| Normal text | Measured | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Symbolic text | Measured | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Structured JSON | Measured | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Application logs | Measured | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Convergence merge | Measured | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

## Speed And Workflow Metrics Template

| Scenario | CSF Status | Baseline | CSF Time | Baseline Time | CSF Speed Delta | Notes |
|---|---|---|---:|---:|---:|---|
| Compress normal text | Measured | Zstd | TBD | TBD | TBD | Same corpus and compression level policy required. |
| Compress symbolic text | Measured | Brotli | TBD | TBD | TBD | Use dream-journal symbolic corpus. |
| Search archive | Measured | Decompress then search | TBD | TBD | TBD | Requires completed indexed search. |
| Merge archives | Measured | Full recompress | TBD | TBD | TBD | Requires completed convergence merge. |
| Large-file memory use | Measured | Zstd | TBD | TBD | TBD | Report memory use as percentage of input size. |

## Completion Criteria

This report is ready to replace projections when:

- The Rust CLI performs bit-perfect archive roundtrips.
- The benchmark harness invokes the actual Rust `csf` binary.
- Search and convergence rows use implemented CSF behavior, not simulations.
- All measured values are marked `Measured` and include trial count and confidence intervals where practical.
