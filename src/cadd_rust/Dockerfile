# CADD v0.2.1 — Headless container
# Multi-stage build: compile Rust binary, ship minimal runtime.
# Usage: docker build -t lantern-os/cadd:v0.2.1 .

FROM rust:slim-bookworm AS builder
WORKDIR /build
COPY Cargo.toml ./
# Generate Cargo.lock if missing
RUN test -f Cargo.lock || cargo generate-lockfile
COPY src ./src
RUN cargo build --release --bin cadd

# Runtime stage — distroless
FROM gcr.io/distroless/cc-debian12
WORKDIR /app
COPY --from=builder /build/target/release/cadd /app/cadd
ENTRYPOINT ["/app/cadd"]
CMD ["watch", "/assets/incoming", "--brand-dir", "/assets/brand"]
