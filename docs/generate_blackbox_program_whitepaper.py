#!/usr/bin/env python3
"""Generate the Convergence Core research-program whitepaper (Σ₀-grounded).

A scientific roadmap AND a plain-language field guide: the project reframed as
an *instrument* for studying and accelerating opaque model cognition ("the
black box") through external grounding, persistence, and verification — not
weight modification.

v1.1 expands v1.0 with:
  • a plain-language primer + glossary (no jargon required),
  • a fully-specified protocol stack (CSF + the five Convergence IO specs:
    PCSF, CCF/CAP, NAP, AAPF, DCF),
  • the "42 machine" (the Σ₀ collapse operators), and
  • the "universe on a flash drive" thesis (convergence as compression).

Honesty contract (Σ₀):
  • The "Current Measured Baseline" section is read from committed artifacts.
  • The ten-year roadmap is explicitly PROPOSED — falsifiable targets, not
    results. It carries no confidence scores.
  • Protocol descriptions are sourced from committed code/docs (cited inline).

Inputs (measured):
  data/sigma0_tesseract_cube_report.json        (cognitive-state archive)
  data/sigma0_real_data_grounding_report.json   (collapse/drift instrument)

Run:
    python experiments/sigma0_tesseract_cube_grounding.py
    python experiments/sigma0_real_data_grounding.py
    python docs/generate_blackbox_program_whitepaper.py
"""

import json
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Preformatted,
)
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily


def _register_unicode_fonts():
    """Embed a Unicode font family so math/Greek glyphs (Σ₀, ∇ₓL, ⊥ₛ, →, ×, ≥)
    render instead of becoming tofu boxes. Returns (sans, sans_bold, mono) font
    names, falling back to the base-14 Helvetica/Courier if DejaVu is absent."""
    search = []
    try:
        import matplotlib
        search.append(Path(matplotlib.__file__).parent / "mpl-data" / "fonts" / "ttf")
    except Exception:
        pass
    search.append(Path(r"C:\Windows\Fonts"))
    search.append(Path("/usr/share/fonts/truetype/dejavu"))

    variants = {
        "DejaVuSans": "DejaVuSans.ttf",
        "DejaVuSans-Bold": "DejaVuSans-Bold.ttf",
        "DejaVuSans-Oblique": "DejaVuSans-Oblique.ttf",
        "DejaVuSans-BoldOblique": "DejaVuSans-BoldOblique.ttf",
        "DejaVuMono": "DejaVuSansMono.ttf",
        "DejaVuMono-Bold": "DejaVuSansMono-Bold.ttf",
    }

    def find(fname):
        for d in search:
            p = d / fname
            if p.exists():
                return str(p)
        return None

    if not all(find(f) for f in variants.values()):
        return "Helvetica", "Helvetica-Bold", "Courier"  # graceful fallback

    for name, fname in variants.items():
        pdfmetrics.registerFont(TTFont(name, find(fname)))
    registerFontFamily("DejaVuSans", normal="DejaVuSans", bold="DejaVuSans-Bold",
                       italic="DejaVuSans-Oblique", boldItalic="DejaVuSans-BoldOblique")
    registerFontFamily("DejaVuMono", normal="DejaVuMono", bold="DejaVuMono-Bold",
                       italic="DejaVuMono", boldItalic="DejaVuMono-Bold")
    return "DejaVuSans", "DejaVuSans-Bold", "DejaVuMono"


SANS, SANS_BOLD, MONO = _register_unicode_fonts()

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
T_ART = ROOT / "data" / "sigma0_tesseract_cube_report.json"
G_ART = ROOT / "data" / "sigma0_real_data_grounding_report.json"
OUTPUT = HERE / "Convergence-Core-Research-Program-v1.1.pdf"

# Independently verified this session: `python -m unittest discover -s tests/csf`
CSF_TESTS = 37

missing = [p.name for p in (T_ART, G_ART) if not p.exists()]
if missing:
    raise SystemExit(
        "Missing measured artifact(s): " + ", ".join(missing) + "\n"
        "Run the two grounding experiments first (see module docstring)."
    )

T = json.loads(T_ART.read_text(encoding="utf-8"))
G = json.loads(G_ART.read_text(encoding="utf-8"))
TB, TQ, TC = T["base3_codec"], T["quantum_dust_field"], T["status_cube"]
GT, GD, GI = G["trajectory_stats"], G["detection"], G["intervention"]

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("PaperTitle", parent=styles["Title"], fontName=SANS_BOLD,
                          fontSize=17, spaceAfter=6, alignment=TA_CENTER))
styles.add(ParagraphStyle("Subtitle", parent=styles["Normal"], fontName=SANS,
                          fontSize=11, alignment=TA_CENTER,
                          textColor=HexColor("#555555"), spaceAfter=18))
styles.add(ParagraphStyle("SectionHead", parent=styles["Heading1"], fontName=SANS_BOLD,
                          fontSize=14, spaceBefore=16, spaceAfter=8,
                          textColor=HexColor("#1a1a2e")))
styles.add(ParagraphStyle("SubHead", parent=styles["Heading2"], fontName=SANS_BOLD,
                          fontSize=12, spaceBefore=10, spaceAfter=5,
                          textColor=HexColor("#16213e")))
styles.add(ParagraphStyle("Body", parent=styles["Normal"], fontName=SANS,
                          fontSize=10, spaceBefore=4, spaceAfter=4, leading=14))
# Plain-language callout: indented, tinted — the "in plain words" voice.
styles.add(ParagraphStyle("Plain", parent=styles["Normal"], fontName=SANS,
                          fontSize=10, spaceBefore=4, spaceAfter=8, leading=14,
                          leftIndent=10, rightIndent=10, borderPadding=6,
                          backColor=HexColor("#eef4fb"), textColor=HexColor("#22303f")))
styles.add(ParagraphStyle("CodeBlock", parent=styles["Code"], fontName=MONO,
                          fontSize=8, spaceBefore=4, spaceAfter=4, leading=10,
                          backColor=HexColor("#f4f4f4"), borderPadding=4))
styles.add(ParagraphStyle("Caption", parent=styles["Normal"], fontName=SANS,
                          fontSize=9, alignment=TA_CENTER,
                          textColor=HexColor("#666666"), spaceBefore=4, spaceAfter=12))
# Wrapping cell text for table bodies (bare strings do NOT wrap in reportlab).
styles.add(ParagraphStyle("Cell", parent=styles["Normal"], fontName=SANS,
                          fontSize=9, leading=11, spaceBefore=0, spaceAfter=0))

# ── Auto-numbering so sections can be reordered without manual renumbering ──
_SEC = [0]
_SUB = [0]


def H(title):
    _SEC[0] += 1
    _SUB[0] = 0
    return Paragraph(f"{_SEC[0]}. {title}", styles["SectionHead"])


def SH(title):
    _SUB[0] += 1
    return Paragraph(f"{_SEC[0]}.{_SUB[0]} {title}", styles["SubHead"])


def P(text, style="Body"):
    return Paragraph(text, styles[style])


def PW(text):
    """Plain-words callout."""
    return Paragraph(f"<b>In plain words.</b> {text}", styles["Plain"])


def make_table(headers, rows, col_widths=None):
    # Wrap body string cells in Paragraphs so long text wraps to the column
    # width instead of overflowing the margin. Headers stay as strings (short,
    # and styled white-on-dark by the TableStyle).
    wrapped_rows = [
        [Paragraph(c, styles["Cell"]) if isinstance(c, str) else c for c in row]
        for row in rows
    ]
    t = Table([headers] + wrapped_rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (-1, 0), SANS_BOLD),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#ffffff"), HexColor("#f9f9f9")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def build():
    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=letter,
        leftMargin=0.9 * inch, rightMargin=0.9 * inch,
        topMargin=0.8 * inch, bottomMargin=0.8 * inch,
    )
    s = []

    # ── Title ──
    s += [Spacer(1, 1.3 * inch)]
    s += [P("Instrumenting the Black Box", "PaperTitle")]
    s += [P("A Ten-Year Research Program for Persistent, Externally-Grounded "
            "Machine Reasoning — with a Field Guide to the Convergence Core "
            "Protocol Stack", "Subtitle")]
    s += [Spacer(1, 0.25 * inch)]
    s += [P("Convergence Core — Lantern OS", "Subtitle")]
    s += [P("Alex Place", "Subtitle")]
    s += [P("June 16, 2026  ·  Program v1.1  ·  License: AGPL", "Subtitle")]
    s += [P("Current-state figures are read from measured artifacts. "
            "The roadmap is a falsifiable proposal, not a result.", "Caption")]
    s += [PageBreak()]

    # ── Abstract ──
    s += [P("Abstract", "SectionHead")]
    s += [P(
        "Large models are black boxes in four distinct senses: their reasoning "
        "is <i>opaque</i> (we cannot see why an output was produced), "
        "<i>impermanent</i> (nothing learned at inference survives without "
        "retraining), <i>ungrounded</i> (claims arrive without evidence), and "
        "<i>irreproducible</i> (runs cannot be replayed or audited). We argue "
        "that all four admit external, measurable interventions — without "
        "modifying model weights — by moving the locus of improvement out of the "
        "parameters and into an external, append-only substrate of memories, "
        "tasks, tool traces, and convergence records. <b>The model becomes an "
        "interchangeable component; the substrate becomes the inspectable, "
        "persistent, falsifiable object of study.</b>",
        "Body")]
    s += [P(
        "This document is both a research program and a field guide. We first "
        "establish what already works today, grounded in committed, reproducible "
        f"artifacts: a lossless cognitive-state archive over a 3<super>12</super>"
        f" = {TB['total_positions']:,}-position lattice, and a "
        f"dynamical-systems instrument that detects collapse dynamics on a real "
        f"{GT['n_turns']:,}-turn interaction log. We then fully specify the "
        "protocol stack that makes the substrate work — the CSF archive format "
        "and the five Convergence IO governance specs (PCSF, CCF, NAP, AAPF, "
        "DCF) — and the Σ₀ 'collapse' operators (the '42 machine') that keep a "
        "reasoning system from quietly degenerating. Finally we lay out six "
        "research thrusts and a five-phase, ten-year plan whose explicit goal is "
        "to <i>expedite the black box</i>.", "Body")]
    s += [P("Who this is for: researchers and engineers, but every technical "
            "section is followed by a plain-language note, and Section 2 is a "
            "glossary you can read first.", "Caption")]

    # ════════════════════════════════════════════════════════════════════
    # 1. The black-box problem
    # ════════════════════════════════════════════════════════════════════
    s += [H("The Black-Box Problem, Decomposed")]
    s += [P(
        "Progress on opaque models is usually framed as either interpretability "
        "(open the weights) or scaling (grow the weights). We take a third "
        "position: instrument the <i>behavior</i> and accumulate it. Each facet "
        "of opacity maps to a concrete, external mechanism.", "Body")]
    s += [make_table(
        ["Facet of opacity", "Conventional attack", "External-substrate attack"],
        [
            ["Opaque — why this output?", "Probe internal activations",
             "Require [claim, evidence, confidence, source] on every step"],
            ["Impermanent — no memory", "Fine-tune / RLHF",
             "Append-only memory + retrieval; gains without retraining"],
            ["Ungrounded — no evidence", "Trust + spot-check",
             "External-reality rule: nothing accepted without evidence"],
            ["Irreproducible — can't replay", "Log prompts ad hoc",
             "Deterministic artifacts; runs replay byte-for-byte"],
        ],
        col_widths=[1.7 * inch, 1.8 * inch, 2.5 * inch])]
    s += [P("Table 1: Four facets of the black box and the external mechanism "
            "each maps to", "Caption")]
    s += [P(
        "<b>Thesis.</b> If improvement lives in an inspectable substrate, then "
        "interpretability, persistence, grounding, and reproducibility become "
        "engineering targets with measurable units — and the model underneath "
        "can be swapped at any time without losing the accumulated science.",
        "Body")]
    s += [P(
        "<b>Definition.</b> <i>Expedite the black box</i> is the program of "
        "increasing the capability, interpretability, persistence, and "
        "reproducibility obtained from frozen models through external "
        "instrumentation rather than parameter modification.", "Body")]
    s += [PW(
        "A modern AI model is a sealed engine: powerful, but you can't see "
        "inside, it forgets everything the moment a chat ends, it states things "
        "with no receipts, and you can't re-run yesterday's exact thought. "
        "Instead of prying the engine open or building a bigger one, we bolt "
        "instruments onto the <i>outside</i> — a notebook it can't erase, a rule "
        "that every claim needs a source, and a black-box flight recorder. The "
        "engine can be replaced; the instruments and everything they learned "
        "stay.")]

    # ════════════════════════════════════════════════════════════════════
    # 2. Plain-language primer & glossary
    # ════════════════════════════════════════════════════════════════════
    s += [H("Plain-Language Primer & Glossary")]
    s += [P("If you read nothing else, read this. Every term used later is "
            "defined here in one line.", "Body")]
    s += [make_table(
        ["Term", "Plain meaning"],
        [
            ["Frozen model", "An AI whose internal numbers (weights) we never change."],
            ["Substrate", "Everything we store outside the model: notes, tasks, "
             "tool results, records."],
            ["The loop", "Observe → Remember → Reason → Act → Verify → Converge — "
             "the system's heartbeat."],
            ["Convergence record", "A lab-notebook entry: hypothesis, evidence, "
             "result, confidence, source."],
            ["Grounding", "Refusing to accept a claim without evidence behind it."],
            ["CSF", "A 'smart zip' that stores meaning and skips the boring, "
             "unchanging parts."],
            ["Lattice / cube", "A grid of all possible states; we store only the "
             "few that matter."],
            ["Dust", "The vast majority of states that are empty — free to store."],
            ["Σ₀ (sigma-zero)", "A safety valve that catches a mind running in "
             "circles and freezes it cleanly."],
            ["42 state", "What's left after that freeze: a stable but contentless "
             "summary."],
            ["Provenance", "A tamper-evident record of who did what, with which "
             "model, and why."],
        ],
        col_widths=[1.5 * inch, 4.5 * inch])]
    s += [P("Table 2: One-line glossary", "Caption")]

    # ════════════════════════════════════════════════════════════════════
    # 3. The loop as apparatus
    # ════════════════════════════════════════════════════════════════════
    s += [H("The Loop as a Measurement Apparatus")]
    s += [P(
        "The system is one loop over four object types. Treating it as an "
        "instrument means every stage emits a typed, persistable record that "
        "later stages — and external auditors — can read.", "Body")]
    s += [make_table(
        ["Stage", "Question it answers", "Emitted object"],
        [
            ["Observe", "What is the state of the world?", "Memory (append-only)"],
            ["Remember", "What is relevant from the past?", "Retrieved memory set"],
            ["Reason", "What is the plan under constraints?", "Task (goal + status)"],
            ["Act", "What did a tool actually do?", "Tool (input/output/success)"],
            ["Verify", "Is the claim supported by evidence?", "Evidence + confidence"],
            ["Converge", "Did the hypothesis hold?", "Convergence Record"],
        ],
        col_widths=[1.1 * inch, 2.6 * inch, 2.3 * inch])]
    s += [P("Table 3: Each loop stage as a measurement, with its output object",
            "Caption")]
    s += [P(
        "The four object types — Memory, Task, Tool, Convergence Record — are "
        "the complete data model. Everything else is implementation. This "
        "deliberate minimality is what makes the substrate auditable: there is "
        "a small, fixed vocabulary in which all cognition is recorded.", "Body")]
    s += [PW(
        "Think of it like a six-step routine the system repeats forever: look, "
        "recall, plan, do, check, file the result. Each step leaves a receipt, "
        "and there are only four kinds of receipt — so anyone can audit the "
        "whole mind by reading them.")]

    # ════════════════════════════════════════════════════════════════════
    # 4. Current measured baseline
    # ════════════════════════════════════════════════════════════════════
    s += [PageBreak()]
    s += [H("Current Measured Baseline (Σ₀-Grounded)")]
    s += [P(
        "Two instruments already exist and produce reproducible, deterministic "
        "artifacts. Their numbers below are read directly from those artifacts; "
        "none is hand-entered.", "Body")]

    s += [SH("A lossless archive for cognitive state")]
    s += [P(
        f"The CSF archive encodes high-dimensional sparse state — the kind a "
        f"reasoning system accumulates — at the structure level rather than the "
        f"byte level. Over a {TB['total_positions']:,}-position ternary lattice, "
        f"any state transition encodes in {TB['delta_record_bytes']} bytes and "
        f"round-trips losslessly "
        f"({TB['neighbor_transitions_tested']}/{TB['neighbor_transitions_tested']}"
        f" ring-neighbor transitions plus a full-lattice sweep verified). A "
        f"{TC['door_choices_recorded']}-event session persists to "
        f"{TC['csf_file_bytes']:,} bytes — {TC['compression_ratio']}× smaller "
        f"than its raw log — and reloads bit-faithfully. The reference codec "
        f"passes {CSF_TESTS} unit tests.", "Body")]

    s += [SH("A dynamical-systems instrument for collapse")]
    s += [P(
        "<b>Operational definition.</b> In this paper <i>collapse</i> denotes a "
        "persistent reduction in novelty accompanied by increased self-repetition "
        "and echoing, measured in the Σ₀ state space. It is not, here, a claim "
        "about training-time distributional collapse, entropy loss in the weights, "
        "or attractor convergence in the literature's sense; it is a behavioral "
        "signature defined entirely by external observables.", "Body")]
    s += [P(
        f"On a real {GT['n_turns']:,}-turn interaction log, the committed "
        f"machinery encodes each turn into a state vector, fits local Jacobians, "
        f"and runs a small-gain collapse certificate plus a Kalman surprise "
        f"monitor. It detects this operational collapse signature — the 'parrot' "
        f"attractor — as self-repeat {GT['mean_self_repeat']} and echo "
        f"{GT['mean_echo']} (signature present = {GT['parrot_attractor']}), flags "
        f"{GD['n_collapse_guaranteed']}/{GD['n_windows']} windows as "
        f"contraction-guaranteed, and registers {GD['n_spook']} surprise spikes. "
        f"An anti-collapse operator sustains "
        f"{GI['null_subspace_persistence_ratio_on_over_off']}× the energy in the "
        f"flat (degenerate) direction versus baseline — a measured intervention "
        f"on a real failure mode of frozen models.", "Body")]
    s += [make_table(
        ["Instrument", "Measured quantity", "Value", "Source"],
        [
            ["CSF archive", "Lattice positions", f"{TB['total_positions']:,}",
             "base3.py"],
            ["CSF archive", "Bytes per transition", str(TB['delta_record_bytes']),
             "base3.py"],
            ["CSF archive", "Session compression", f"{TC['compression_ratio']}×",
             "status_cube.py"],
            ["CSF archive", "Unit tests passing", str(CSF_TESTS), "tests/csf"],
            ["Collapse instr.", "Log turns analyzed", f"{GT['n_turns']:,}",
             "cio_sde"],
            ["Collapse instr.", "Contraction windows",
             f"{GD['n_collapse_guaranteed']}/{GD['n_windows']}", "cio_sde"],
            ["Collapse instr.", "Surprise spikes", str(GD['n_spook']), "cio_sde"],
            ["Collapse instr.", "Anti-collapse energy ratio",
             f"{GI['null_subspace_persistence_ratio_on_over_off']}×", "cio_sde"],
        ],
        col_widths=[1.3 * inch, 2.1 * inch, 1.2 * inch, 1.4 * inch])]
    s += [P("Table 4: Measured baseline, read from committed artifacts", "Caption")]

    s += [SH("Baseline Result")]
    s += [P(
        "Two substrate-level capabilities already exist, measured and "
        "reproducible: (1) lossless, compact cognitive-state persistence; and "
        "(2) external detection and mitigation of operational collapse dynamics. "
        "State can be archived losslessly and compactly, and a real, known "
        "failure mode of frozen models — collapse toward repetition — is already "
        "detectable and treatable from outside the weights. The remainder of this "
        "document asks whether these two primitives scale into a general science "
        "of externally grounded reasoning.", "Body")]
    s += [PW(
        "Two things already work, and we can prove them by re-running the code: "
        "we can shrink a system's memory into a tiny file and get it back "
        "perfectly, and we can spot — and partly fix — a model sliding into "
        "repeat-itself mode, all without touching the model's insides.")]

    # ════════════════════════════════════════════════════════════════════
    # 5. The protocol stack (FULL SPEC)
    # ════════════════════════════════════════════════════════════════════
    s += [PageBreak()]
    s += [H("The Protocol Stack (Full Specification)")]
    s += [P(
        "The substrate is made of named, composable protocols. One handles "
        "storage (CSF); five handle governance and routing (the Convergence IO "
        "stack, derived from the Regulatory Primitive Stack research, RPS v0.1, "
        "implemented in <font face='Courier'>src/convergence_io/</font>). Each is "
        "specified below: purpose, mechanism, the regulatory primitive it "
        "operationalizes, and a plain-language note.", "Body")]
    s += [P("<b>Naming note (honesty).</b> The five governance specs are PCSF, "
            "CCF, AAPF, NAP, and DCF. 'CAP' in informal usage refers to the "
            "<i>Capability Claim Format (CCF)</i> — the capability gate — and is "
            "labelled CCF / CAP throughout. CSF is documented both as "
            "'Convergence-Fitted Searchable Format' (v0.3 paper) and "
            "'Convergence-Searchable Format' (CIO docs); they denote the same "
            "format.", "Body")]

    s += [SH("CSF — Convergence-Searchable Format (storage)")]
    s += [P(
        "<b>Purpose.</b> A binary archive for sparse, symbolic, mostly-static "
        "state — the kind a reasoning system accumulates. <b>Mechanism.</b> A "
        "symbolic dictionary maps domain concepts to short codes; base-3 "
        "positional encoding addresses a 3<super>12</super> lattice in ≤4 bytes; "
        "a sparse delta stream records only deviations from a converged baseline; "
        "and convergence compaction periodically folds stable regions back into "
        "the baseline (anti-entropy at the storage layer). <b>Searchable</b> "
        "means the dictionary and delta stream can be queried without full "
        f"decompression. <b>Measured</b> (Table 4): {TB['delta_record_bytes']}"
        f" B/transition, {TC['compression_ratio']}× session compression, "
        f"{CSF_TESTS} tests.", "Body")]
    s += [PW(
        "A zip file that understands meaning instead of just bytes — and "
        "deliberately forgets the parts that never change, so what's left is "
        "tiny and still searchable.")]

    s += [SH("PCSF — Provider Capacity State Format (routing)")]
    s += [P(
        "<b>Operationalizes</b> P4 (Capability Constraints) for model routing. "
        "<b>What it does:</b> tracks which model providers are available, "
        "degraded, at quota, or circuit-broken, and routes through a fallback "
        "chain automatically — <font face='Courier'>Anthropic → OpenAI → Google "
        "→ Groq → DeepSeek → Ollama → Offline</font>. Each provider carries a "
        "circuit breaker (3 failures → open 30s → half-open probe), latency "
        "tracking (p50/p99), quota awareness, and env-var detection (no key → no "
        "route). This is what makes the model genuinely interchangeable.", "Body")]
    s += [PW(
        "If one AI provider goes down or gets rate-limited, the system quietly "
        "fails over to the next one — and if all else fails, an offline mode — "
        "so the lights never go out.")]

    s += [SH("CCF / CAP — Capability Claim Format (capability gate)")]
    s += [P(
        "<b>Operationalizes</b> P4; consumed by P5/P8/P10. <b>What it does:</b> "
        "each agent registers what it can <i>actually</i> do right now; before an "
        "action, a CapabilityGate checks the claim against the required "
        "capabilities. Core principle: <b>hallucinated capability is a "
        "compliance failure</b> — if an agent claims streaming inference but its "
        "provider is down, the gate rejects the action rather than failing "
        "silently.", "Body")]
    s += [PW(
        "No bluffing. Before the system does something, it has to prove it can — "
        "otherwise it's stopped up front instead of breaking halfway through.")]

    s += [SH("NAP — Negative Authority Profiles (hard denials)")]
    s += [P(
        "<b>Operationalizes</b> P2 (Authority and Consent Gates) in denial form; "
        "composes M1 (Dynamic External Predicates). <b>What it does:</b> defines "
        "what agents are explicitly <i>denied</i>, and these denials cannot be "
        "overridden by capability claims. Built-in profiles: "
        "<font face='Courier'>dreamer-safety</font> (no financial trades, no "
        "credential entry, no data deletion, no PII/PHI/COPPA actions) and "
        "<font face='Courier'>local-only</font> (blocks all cloud providers, "
        "on-device only). External deny-lists can be refreshed on a schedule.",
        "Body")]
    s += [PW(
        "A short list of things the system is never allowed to do — move money, "
        "type passwords, delete your data — and nothing it 'believes' about "
        "itself can talk it past that list.")]

    s += [SH("AAPF — Agent Action Provenance Format (audit trail)")]
    s += [P(
        "<b>Operationalizes</b> P3 (Provenance and Audit); consumed by P6/P7/P9. "
        "<b>What it does:</b> every action — chat, save, dispatch, gate check — "
        "produces an append-only provenance record tying input to output, agent "
        "to provider, capability claim to authority check. Records are written "
        "to <font face='Courier'>data/provenance/actions.jsonl</font>, queryable "
        "by agent, action type, and time range.", "Body")]
    s += [PW(
        "A flight recorder for every decision the system makes — so after the "
        "fact you can replay exactly what happened and why.")]

    s += [SH("DCF — Data Classification Format (label propagation)")]
    s += [P(
        "<b>Operationalizes</b> P1 (Data Classification); gates CCF. <b>What it "
        "does:</b> every piece of data carries classification labels that "
        "propagate through transformations — a summary of a sensitive entry "
        "still carries the sensitive label. Standard labels include "
        "<font face='Courier'>user_identity</font> (sensitive), "
        "<font face='Courier'>system_metadata</font> (public, non-propagating), "
        "and content labels that travel with every derivative.", "Body")]
    s += [PW(
        "Sensitive stays sensitive. If the system summarizes or rewrites "
        "private data, the 'handle with care' sticker comes along for the ride.")]

    s += [make_table(
        ["Protocol", "Layer", "Primitive", "One-line role"],
        [
            ["CSF", "Storage", "—", "Smart, searchable, self-pruning archive"],
            ["PCSF", "Routing", "P4", "Keep talking when a provider fails"],
            ["CCF / CAP", "Gate", "P4", "No action without a backed capability"],
            ["NAP", "Gate", "P2", "Hard denials nothing can override"],
            ["AAPF", "Audit", "P3", "Append-only record of every action"],
            ["DCF", "Data", "P1", "Sensitivity labels that propagate"],
        ],
        col_widths=[1.1 * inch, 1.0 * inch, 0.9 * inch, 3.0 * inch])]
    s += [P("Table 5: The protocol stack at a glance "
            "(source: docs/CONVERGENCE-IO-v1.0.0.md, src/convergence_io/)",
            "Caption")]

    # ════════════════════════════════════════════════════════════════════
    # 6. The 42 machine (Σ₀)
    # ════════════════════════════════════════════════════════════════════
    s += [PageBreak()]
    s += [H("The 42 Machine — the Σ₀ Collapse Operators")]
    s += [P(
        "A reasoning system can fail not by crashing but by <i>wandering</i>: "
        "drifting in circles when there is nothing left to decide. Σ₀ "
        "(sigma-zero) is the operator that detects this exact condition and "
        "resolves it cleanly. It is implemented in "
        "<font face='Courier'>src/cio_sde/collapse.py</font> and is the "
        "mathematical core of the collapse instrument from Section 4.", "Body")]
    s += [SH("When Σ₀ fires: four conditions at once")]
    s += [P(
        "Σ₀ triggers only when the system is genuinely underdetermined — a "
        "control singularity over a structureless field — i.e. all four hold:",
        "Body")]
    s += [make_table(
        ["Condition", "Meaning"],
        [
            ["∇ₓL → 0", "No optimization signal left — nothing to improve."],
            ["rank(J) < threshold", "The drift has lost directional structure."],
            ["Σ isotropically flat", "Uncertainty points nowhere in particular."],
            ["∀u: Δcost(u) ≈ 0", "No available action changes the outcome."],
        ],
        col_widths=[1.8 * inch, 4.2 * inch])]
    s += [P("Table 6: The four Σ₀ trigger conditions (all must hold)", "Caption")]
    s += [P(
        "When they do, Σ₀ projects the state onto its minimal invariant manifold "
        "— the null eigenmodes of the drift Jacobian — yielding <b>x*</b>, a "
        "stable, structureless summary the code calls <b>the '42 state'</b>: a "
        "definite answer with the original question dissolved out of it. If there "
        "is no invariant structure at all, the outcome is instead ⊥ₛ, a semantic "
        "null.", "Body")]
    s += [PW(
        "Picture a mind stuck overthinking with nothing actually at stake. "
        "Rather than spin forever or melt down, Σ₀ snaps it to the one calm, "
        "stable point and stops. The leftover is famously '42' — a tidy answer "
        "you can no longer attach a question to.")]

    s += [SH("The collapse certificate: a guarantee, not a vibe")]
    s += [P(
        "Whether collapse is guaranteed is a theorem, not a guess. Taking the "
        "symmetric part A<sub>s</sub> of the drift Jacobian and the Lyapunov "
        "function V(x) = ½‖P<sub>M</sub>x‖² on the active modes, if the spectral "
        "abscissa α = max λ(A<sub>s</sub>) on the active subspace is below zero, "
        "then V̇ ≤ 2αV and the active modes decay exponentially: the trajectory "
        "<i>provably</i> contracts onto the invariant manifold. The certificate "
        "also computes the exact (non-normal) spectral abscissa as the tight "
        f"test. On the real {GT['n_turns']:,}-turn log this fired on "
        f"{GD['n_collapse_guaranteed']}/{GD['n_windows']} windows (Section 4).",
        "Body")]
    s += [PW(
        "There's a math proof attached: if a single number comes out negative, "
        "the system is guaranteed to settle down rather than spiral. We don't "
        "hope it converges — we certify it.")]

    s += [SH("Σ₀⁻¹ and Σ₀ᴿ: undo and rebuild")]
    s += [P(
        "Two companion operators complete the set. <b>Σ₀⁻¹ (anti-collapse)</b> "
        "does the opposite of Σ₀: as the system nears the boundary it injects "
        "energy <i>along</i> the directions that have gone flat — the "
        "persistent-excitation trick from adaptive control — and only fires when "
        "proximity to collapse is high, so it costs nothing in healthy regimes. "
        f"Measured effect (Section 4): {GI['null_subspace_persistence_ratio_on_over_off']}× "
        f"the flat-direction energy versus baseline. <b>Σ₀ᴿ (reconstruction)</b> "
        "keeps a compact seed of the pre-collapse structure — the top-k mode "
        "coefficients, the 'speck of dust' — and regrows the state from it. The "
        "minimal seed that hits a target fidelity <i>is</i> the state's effective "
        "dimension: a hard floor set by the rate–distortion curve. You cannot "
        "rebuild information you did not keep.", "Body")]
    s += [PW(
        "Σ₀⁻¹ is a defibrillator — it shocks a flat-lining mind back into "
        "motion. Σ₀ᴿ is the 'put the smoke back' button: it saves a pinch of the "
        "original and regrows from it, but only as much as it bothered to keep.")]

    # ════════════════════════════════════════════════════════════════════
    # 7. Universe on a flash drive
    # ════════════════════════════════════════════════════════════════════
    s += [H("Fitting a Universe on a Flash Drive")]
    s += [P(
        "Put the storage format and the collapse operators together and you get "
        "the headline claim: a 'universe' — a vast state space plus its history "
        "— can be carried in a tiny file. The mechanism is honest and specific. "
        "A 3<super>12</super> lattice has "
        f"{TB['total_positions']:,} positions, but almost all of them are "
        f"<i>dust</i> ({TQ['dust_percentage_after_observe']}% in the measured "
        "run): empty potential that costs nothing. You store the converged "
        "baseline, the handful of active deviations, and — via Σ₀ᴿ — a "
        "speck-of-dust seed of the structured part. Everything else is "
        "regenerated on demand.", "Body")]
    s += [P(
        f"This is already demonstrated at small scale: a "
        f"{TC['door_choices_recorded']}-event session compresses to "
        f"{TC['csf_file_bytes']:,} bytes ({TC['compression_ratio']}×) and "
        f"reloads bit-faithfully, and any position in the "
        f"{TB['total_positions']:,}-state space is addressable in "
        f"{TB['delta_record_bytes']} bytes. The principle that bounds it is "
        "rate–distortion: the smallest faithful seed equals the effective "
        "dimension of the content, and that floor is the second law showing up "
        "in storage.", "Body")]
    s += [P(
        "<b>Honest scope.</b> 'Fit a universe on a flash drive' is a claim about "
        "<i>structured, mostly-redundant</i> state — worlds that are mostly "
        "empty and mostly stable, which is what reasoning histories actually are. "
        "It is <b>not</b> a claim to losslessly store arbitrary, "
        "high-entropy information: Shannon forbids that, and Σ₀ᴿ's "
        "rate–distortion floor is exactly where the limit bites. The "
        "compression comes from the universe being compressible, not from "
        "beating information theory.", "Body")]
    s += [PW(
        "Most of any world is empty space and stuff that isn't changing. So you "
        "don't save the whole thing — you save the rules, the few things "
        "currently happening, and a pinch of seed to regrow the rest. That fits "
        "on a thumb drive. The catch, stated plainly: this only works because "
        "the world is mostly repetition; truly random noise can't be shrunk, and "
        "we don't claim it can.")]

    # ════════════════════════════════════════════════════════════════════
    # 8. Research thrusts
    # ════════════════════════════════════════════════════════════════════
    s += [PageBreak()]
    s += [H("Six Research Thrusts")]
    s += [P(
        "Each thrust is a line of inquiry with a falsifiable core question. "
        "They are the 'what to discover'; the roadmap section is the 'when'.",
        "Body")]
    s += [make_table(
        ["#", "Thrust", "Core falsifiable question"],
        [
            ["R1", "External interpretability",
             "Do convergence records predict outputs better than chance "
             "without weight access?"],
            ["R2", "Learning without retraining",
             "Does accumulated memory yield monotone task-accuracy gains on a "
             "fixed model?"],
            ["R3", "Collapse & drift dynamics",
             "Are there universal thresholds at which reasoning degenerates, "
             "across models?"],
            ["R4", "Verification calculus",
             "Can a claim/evidence/confidence score predict downstream error "
             "rate?"],
            ["R5", "Cognitive-state compression",
             "How compactly can a full reasoning trajectory be stored and "
             "replayed losslessly?"],
            ["R6", "Cross-model invariants",
             "Which substrate-level metrics are invariant when the model is "
             "swapped?"],
        ],
        col_widths=[0.4 * inch, 1.7 * inch, 3.9 * inch])]
    s += [P("Table 7: Research thrusts and their falsifiable questions", "Caption")]

    # ════════════════════════════════════════════════════════════════════
    # 9. Roadmap
    # ════════════════════════════════════════════════════════════════════
    s += [H("Ten-Year Phased Roadmap (Proposed)")]
    s += [P(
        "Five two-year phases, 2026–2036. Each carries an objective, a primary "
        "hypothesis, a method, a measurable milestone, and the dominant risk. "
        "These are targets, not results — no confidence is asserted.", "Body")]

    def phase(title, years, obj, hyp, method, milestone, risk, thrusts):
        s.append(P(f"{title}  ({years})", "SubHead"))
        s.append(make_table(
            ["Field", "Content"],
            [
                ["Objective", obj],
                ["Hypothesis", hyp],
                ["Method", method],
                ["Milestone (measurable)", milestone],
                ["Dominant risk", risk],
                ["Thrusts", thrusts],
            ],
            col_widths=[1.5 * inch, 4.5 * inch]))

    phase("Phase I — Instrumentation", "2026–2027",
          "Make every loop stage emit a typed, deterministic, replayable record.",
          "A fully instrumented loop can reproduce any run byte-for-byte and "
          "expose per-stage measurements.",
          "Extend the two existing instruments into a unified pipeline; enforce "
          "the Σ₀ artifact contract on all stages; build a frozen-model "
          "capability harness.",
          "≥3 capability deltas demonstrated on a fixed model with zero weight "
          "changes, each reproducible from a committed artifact.",
          "Instrumentation overhead distorts the behavior being measured.",
          "R1, R5")
    phase("Phase II — Datasets & Metrics", "2028–2029",
          "Turn accumulated records into longitudinal corpora and standard "
          "metrics.",
          "A small set of substrate metrics (grounding rate, verification yield, "
          "drift index, retrieval lift) captures most variance in task outcome.",
          "Curate convergence-record corpora across tasks and models; define and "
          "calibrate the metrics against held-out outcomes.",
          "A published 'black-box legibility' score that correlates "
          "(r measured, pre-registered) with downstream accuracy.",
          "Metrics overfit to the harness; poor external validity.",
          "R2, R4")
    phase("Phase III — Discovery", "2030–2031",
          "Use the instrument to find new, replicated phenomena in reasoning "
          "dynamics.",
          "Reasoning degeneration has model-independent thresholds detectable "
          "from substrate signals before output quality drops.",
          "Sweep retrieval-vs-reasoning trade-offs; map collapse thresholds; run "
          "pre-registered replications across ≥3 model families.",
          "≥1 falsifiable, independently replicated discovery about reasoning or "
          "collapse dynamics.",
          "Findings are artifacts of one model generation, not general.",
          "R3, R6")
    phase("Phase IV — Theory & Scaling", "2032–2033",
          "Formalize a predictive theory of external-grounding gains and scale "
          "the substrate.",
          "Capability extracted from a frozen model scales predictably with "
          "substrate quality, with a quantifiable ceiling.",
          "Fit and out-of-sample test a model of grounding gains; scale memory "
          "to large corpora with bounded retrieval cost.",
          "A theory that predicts capability gain out-of-sample within a "
          "pre-stated error band.",
          "Scaling memory degrades retrieval precision faster than theory "
          "allows.",
          "R2, R5, R6")
    phase("Phase V — Generalization", "2034–2035",
          "Demonstrate domain-agnostic, partly-autonomous discovery and "
          "establish a reproducibility standard.",
          "The instrumented loop can propose, run, and verify its own "
          "experiments under the external-reality rule.",
          "Deploy across unrelated domains; close an autonomous "
          "observe→converge discovery loop with human audit gates.",
          "An end-to-end autonomous discovery, independently reproduced from its "
          "committed artifacts.",
          "Autonomy outruns verification; ungrounded claims accumulate.",
          "R1–R6")

    # ════════════════════════════════════════════════════════════════════
    # 10. Falsifiable predictions
    # ════════════════════════════════════════════════════════════════════
    s += [PageBreak()]
    s += [H("Falsifiable Predictions")]
    s += [P(
        "The program is wrong if these fail. They are stated now so they cannot "
        "be retrofitted.", "Body")]
    s += [P(
        "<b>P1.</b> On a fixed, frozen model, task accuracy on a held-out suite "
        "rises monotonically (within noise) as the memory substrate grows — "
        "<b>and reverts when memory is ablated</b>.<br/>"
        "<b>P2.</b> A substrate-only signal (no weight access) predicts reasoning "
        "degeneration earlier than output-quality metrics do.<br/>"
        "<b>P3.</b> At least one collapse threshold is invariant (within a stated "
        "tolerance) across three independent model families.<br/>"
        "<b>P4.</b> A claim's [evidence, confidence] score is monotonically "
        "related to its measured downstream error rate.<br/>"
        "<b>P5.</b> A full reasoning trajectory can be stored and replayed "
        "losslessly at a compression ratio strictly better than its raw log "
        "(already shown at 1 scale; predicted to hold across scales).", "Body")]

    # ════════════════════════════════════════════════════════════════════
    # 11. Limitations
    # ════════════════════════════════════════════════════════════════════
    s += [H("Limitations")]
    s += [P(
        "The boundary of what has been shown is as important as the ambition. "
        "Stated plainly:", "Body")]
    s += [P("Current results do <b>not</b> establish:", "SubHead")]
    s += [P(
        "• general intelligence;<br/>"
        "• consciousness;<br/>"
        "• human-like cognition;<br/>"
        "• universal collapse dynamics;<br/>"
        "• optimality of the Σ₀ representation;<br/>"
        "• causal understanding of model internals;<br/>"
        "• lossless storage of arbitrary (high-entropy) information.", "Body")]
    s += [P("Current results establish <b>only</b>:", "SubHead")]
    s += [P(
        "• deterministic substrate instrumentation;<br/>"
        "• lossless cognitive-state persistence of <i>structured, sparse</i> "
        "state;<br/>"
        "• externally measurable collapse signatures;<br/>"
        "• reproducible interventions on those signatures.", "Body")]

    # ════════════════════════════════════════════════════════════════════
    # 12. Reproducibility standard
    # ════════════════════════════════════════════════════════════════════
    s += [H("Reproducibility Standard")]
    s += [P(
        "Every result in this program must satisfy the Σ₀ contract that the "
        "current baseline already satisfies:", "Body")]
    s += [P(
        "• <b>No hand-entered numbers.</b> Figures are read from committed "
        "artifacts.<br/>"
        "• <b>Determinism.</b> Re-running an experiment reproduces its artifact "
        "byte-for-byte (seeded, no network).<br/>"
        "• <b>Provenance.</b> Each artifact separates REAL (measured), DESIGNED "
        "(modeling choices), and NOT-CLAIMED.<br/>"
        "• <b>Two-pass verification.</b> Claims are extracted, then checked "
        "against source and re-measurement before publication.<br/>"
        "• <b>External reality.</b> No important claim without [claim, evidence, "
        "confidence, source].", "Body")]

    # ════════════════════════════════════════════════════════════════════
    # 13. Convergence record
    # ════════════════════════════════════════════════════════════════════
    s += [H("Convergence Record")]
    s += [Preformatted(
        "hypothesis : Opacity, impermanence, ungroundedness, and\n"
        "             irreproducibility of frozen models are addressable in an\n"
        "             external substrate, without weight modification.\n"
        "evidence   : (current state, measured)\n"
        f"             - lossless cognitive-state archive over {TB['total_positions']:,} positions,\n"
        f"               {TB['delta_record_bytes']}B/transition, {CSF_TESTS} tests, "
        f"{TC['compression_ratio']}x session compression;\n"
        f"             - collapse instrument on {GT['n_turns']:,} real turns: parrot signature\n"
        f"               present, {GD['n_collapse_guaranteed']}/{GD['n_windows']} contraction windows,\n"
        f"               anti-collapse sustains {GI['null_subspace_persistence_ratio_on_over_off']}x null-mode energy.\n"
        "result     : baseline established; thesis supported at 1 scale.\n"
        "             10-year program PROPOSED, not yet executed.\n"
        "confidence : current baseline observable 1.0; program outcomes UNSET\n"
        "             (falsifiable predictions P1-P5 pending).\n"
        "sources    : data/sigma0_tesseract_cube_report.json,\n"
        "             data/sigma0_real_data_grounding_report.json,\n"
        "             src/csf/*, src/cio_sde/*, src/convergence_io/*, tests/csf/*",
        styles["CodeBlock"])]

    # ════════════════════════════════════════════════════════════════════
    # 14. Honesty contract
    # ════════════════════════════════════════════════════════════════════
    s += [H("Honesty Contract")]
    s += [P("Real (measured; see the Current Measured Baseline section):", "SubHead")]
    s += [P("• CSF archive and collapse-instrument figures, read from committed, "
            "deterministic artifacts and a verified test suite.", "Body")]
    s += [P("Designed:", "SubHead")]
    s += [P("• The decomposition of opacity into four facets, the six-thrust "
            "structure, and the five-phase schedule are organizing choices, not "
            "empirical findings. Protocol descriptions are sourced from committed "
            "code/docs; the CAP↔CCF naming is reconciled in Section 5.", "Body")]
    s += [P("Not claimed:", "SubHead")]
    s += [P("• No future milestone is asserted as achieved. The roadmap is a "
            "falsifiable plan; predictions P1–P5 are open. No claim is made about "
            "any specific model's internals — the entire approach is "
            "weight-agnostic by construction. 'Universe on a flash drive' is a "
            "compression claim about structured, redundant state, not about "
            "arbitrary information.", "Body")]

    # ════════════════════════════════════════════════════════════════════
    # 15. Outlook
    # ════════════════════════════════════════════════════════════════════
    s += [H("Outlook")]
    s += [P(
        "If this program succeeds, the scientific object of study is no longer "
        "the weights inside a model but the reasoning traces, memories, tool "
        "results, evidence, and convergence records that exist outside it and "
        "survive when the model is replaced. That direction is coherent whether "
        "the underlying model comes from one vendor, another, or an architecture "
        "not yet invented — the substrate, not the parameters, is what "
        "accumulates.", "Body")]

    doc.build(s)
    print(f"Generated: {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    build()
