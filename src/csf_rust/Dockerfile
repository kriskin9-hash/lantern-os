# CSF v0.8 — Headless container
# Multi-stage build: compile Rust binary, ship minimal runtime.
# Usage: docker build -t lantern-os/csf:v0.8 .

FROM rust:1.78-slim-bookworm AS builder
WORKDIR /build
COPY Cargo.toml ./
# Generate Cargo.lock if missing
RUN test -f Cargo.lock || cargo generate-lockfile
COPY src ./src
COPY benches ./benches
# Build release binary
RUN cargo build --release --bin csf

# Runtime stage — distroless, no shell, no extra frills
FROM gcr.io/distroless/cc-debian12
WORKDIR /app
COPY --from=builder /build/target/release/csf /app/csf
ENTRYPOINT ["/app/csf"]
CMD ["server", "--bind", "0.0.0.0:9000", "--data-dir", "/data/archives"]
