# Grounding Knowledge Base — Provenance Manifest

Real-world, working references downloaded to ground Lantern OS design decisions in
**solved problems from across human industry** — not AI metaphors. PDFs are
git-ignored (large, re-downloadable); this manifest is the tracked record. Every
SHA-256 and page count below was **measured** from the downloaded file, not
asserted.

**Restore rule:** external *reference*, not stored knowledge. These ground design
choices; they never enter the CSF/CADD flywheel except through the DCF→NAP→CCF
gates.

## Manifest (measured)

| Industry | File | Pages | KB | SHA-256(16) | Source | License | Grounds |
|---|---|---|---|---|---|---|---|
| AI governance | `NIST-AI-RMF-1.0-AI.100-1.pdf` | 48 | 1901 | `7576edb531d98488` | NIST AI 100-1 (US Gov) | Public domain | Governance pipeline DCF/NAP/CCF/AAPF; regulatory moat |
| AI governance | `NIST-SP-800-92-Log-Management.pdf` | 72 | 1719 | `466c3ab1580bc3b2` | NIST SP 800-92 (US Gov) | Public domain | AAPF audit-log/provenance discipline |
| aerospace/systems | `NASA-Systems-Engineering-Handbook-SP-2016-6105-Rev2.pdf` | 297 | 3685 | `8eeb4887a4dc57a2` | NASA SP-2016-6105 Rev2 | Public domain | Verify stage; build-it-right discipline |
| information theory | `Shannon-1948-Mathematical-Theory-of-Communication.pdf` | 55 | 358 | `6e4e3411984f3edf` | Shannon 1948 (Harvard host) | © Bell/Nokia, academic use — reference only | Compression / Kolmogorov / π floor |
| agriculture | `industry-agriculture_USDA-National-Organic-Farming-Handbook.pdf` | 43 | 5711 | `9c737f5efe233f5c` | USDA NRCS 190-612-H | Public domain | Working farm-systems manual |
| aviation | `industry-aviation_FAA-Pilots-Handbook-Aeronautical-Knowledge.pdf` | 524 | 54818 | `9c07502b29fc1e23` | FAA-H-8083-25 (US Gov) | Public domain | Pilot working knowledge manual |
| aviation | `industry-aviation_FAA-Aviation-Maintenance-Technician-Handbook-General.pdf` | 677 | 90371 | `0a39c01bbc454e77` | FAA-H-8083-30 (US Gov) | Public domain | Aircraft maintenance working manual |
| defense/medical | `industry-defense_US-Army-FM-4-25.11-First-Aid.pdf` | 224 | 2397 | `f4b7d1e5f3597d81` | US Army FM 4-25.11 | Public domain | Field first-aid working manual |
| earth science | `industry-earth-science_USGS-This-Dynamic-Earth.pdf` | 77 | 3694 | `61be59c6ce15a0d1` | USGS (US Gov) | Public domain | Plate-tectonics reference |
| economics/finance | `industry-economics_OpenStax-Principles-of-Economics.pdf` | 948 | 13845 | `a92031388e23f7d5` | OpenStax | CC BY 4.0 | Economics working textbook |
| energy/power | `industry-energy_DOE-Fundamentals-Thermodynamics-Heat-Fluid.pdf` | 82 | 1011 | `0930365baf0f404d` | DOE-HDBK-1012 | Public domain (US Gov; mirror host) | Thermo / heat / fluid working handbook |
| food service | `industry-food_FDA-Food-Code-2022.pdf` | 668 | 4873 | `aa523bbee8e4fd90` | FDA Food Code 2022 (US Gov) | Public domain | Food-safety working code |
| healthcare | `industry-healthcare_WHO-Surgical-Care-District-Hospital.pdf` | 514 | 6798 | `747007a0ad9cd75a` | WHO 2003 | © WHO, free for academic use — reference only | District-hospital surgical manual |
| maritime | `industry-maritime_Bowditch-American-Practical-Navigator.pdf` | 1542 | 130740 | `5c1ff945e5671a6a` | Bowditch / US Navy (Internet Archive) | Public domain | Practical navigation manual |

## Industry coverage (honest)

14 manuals across 12 domains. **Two-per-industry reached: AI governance, aviation.**
The rest have **one** working manual each; a clean second is pending — several
official hosts (US Coast Guard, the DOE standards portal) block automated download
or serve HTML viewers, so the 2nd-per-industry sweep needs another verify pass.

Not yet covered (candidates for the next pass): construction/civil (FHWA MUTCD,
USACE engineering manuals), manufacturing/industrial safety (full NIOSH Pocket
Guide, OSHA), law, telecom (ITU), chemistry (OpenStax), education.

## License note (honesty)
- US-Gov works (NIST, NASA, FAA, USDA, USGS, FDA, US Army, Bowditch) are public domain.
- OpenStax is CC BY 4.0 (redistributable with attribution).
- Shannon 1948 and WHO 2003 are **not** public domain — freely distributed for
  academic use; logged here as **reference-only** (PDFs git-ignored, not redistributed).
- DOE handbook content is public domain (US Gov) but was fetched from a mirror, not
  the official portal (which served an HTML viewer); flagged accordingly.

## Re-fetch
All files re-downloadable from their sources. Rebuild by re-running the download +
verify steps and confirming the SHA-256(16) prefixes above match.
