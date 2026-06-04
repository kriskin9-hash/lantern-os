# RAG Polling Framework: Continuous Learning & Market Intelligence System

**Version:** 1.0  
**Date:** 2026-05-25  
**Status:** Design & Implementation Ready  
**Integration:** Autopilot + Observable Validation

---

## Executive Summary

**RAG Polling Framework** = Retrieval-Augmented Generation + continuous market/technical polling system

Enables Lantern to:
1. **Learn in motion** — Real-time market feedback loops
2. **Update knowledge base** — New family needs, testimonials, technical learnings
3. **Identify gaps** — What's missing from current product
4. **Optimize pricing** — What families are willing to pay for new features
5. **Predict churn** — Detect at-risk families before they leave

---

## Architecture: Four Polling Loops

### Loop 1: Market Intelligence Polling (Weekly)
**What:** Automated web scraping + sentiment analysis of off-grid family communities  
**Sources:**
- Reddit: r/vandwellers, r/homesteading, r/unschooling, r/autism, r/accessibility
- Instagram hashtags: #vanlife, #buslife, #offgridliving, #homeschool
- Facebook groups: van-life communities, intentional communities, homeschooling networks
- Twitter/X: conversations mentioning "offline AI", "Starlink issues", "kids learning"

**Frequency:** Weekly (Sunday 18:00 UTC)  
**Output:** `~/.lantern/telemetry/market-sentiment-weekly.jsonl`

**Payload:**
```json
{
  "timestamp": "2026-05-25T18:00:00Z",
  "source": "reddit/r/vandwellers",
  "topic": "connectivity_solutions",
  "sentiment": "frustrated",
  "mentions": 47,
  "top_phrases": ["Starlink lag", "kids need learning", "cloud fails on the road"],
  "confidence": 0.82
}
```

**Action:** If sentiment score >0.7 on family learning + offline = add to RAG training data

---

### Loop 2: Family Feedback Polling (Real-time + Daily Digest)
**What:** Continuous collection of family feedback from installed Lantern instances  
**Mechanisms:**
- In-app feedback button: "Thumbs up / down" after each chat session (optional)
- Weekly survey: "What would make Lantern better?" (sent via email)
- Exit survey: "Why did you unsubscribe?" (sent on cancellation)
- NPS polling: "Would you recommend to a friend?" (monthly)

**Frequency:** Real-time collection, daily digest at 06:00 UTC  
**Output:** `~/.lantern/telemetry/family-feedback-daily.jsonl`

**Payload:**
```json
{
  "timestamp": "2026-05-25T06:00:00Z",
  "family_id": "fam_12345",
  "feedback_type": "in_app_thumbs",
  "content": "kids loved the offline music during road trip",
  "rating": 5,
  "feature_request": null,
  "sentiment": "positive"
}
```

**Action:** If same feature requested by 3+ families in a month = prioritize for next sprint

---

### Loop 3: Technical Performance Polling (Continuous + Hourly Report)
**What:** Autopilot continuous validation + performance metrics aggregation  
**Metrics per family:**
- Ollama latency (avg, p95, p99)
- Chat inference success rate
- Music player load time
- UI responsiveness (frame time)
- Memory usage over time (detect leaks)
- Model inference accuracy (family satisfaction)

**Frequency:** Continuous measurement, hourly aggregation  
**Output:** `~/.lantern/telemetry/performance-hourly.jsonl`

**Payload:**
```json
{
  "timestamp": "2026-05-25T14:00:00Z",
  "cohort": "early_adopters",
  "metrics": {
    "ollama_latency_ms": 245,
    "inference_success_rate": 0.98,
    "music_load_time_ms": 120,
    "ui_frame_time_ms": 16.7,
    "memory_growth_per_hour_mb": 2.1
  },
  "alerts": []
}
```

**Action:** If memory growth >5MB/hour = trigger memory leak investigation

---

### Loop 4: Competitor & Market Trend Polling (Bi-weekly)
**What:** Automated monitoring of competitor products + market trends  
**Competitors tracked:**
- Google Family Link updates
- Apple Screen Time changes
- Amazon Kids+ features
- Educational SaaS (Outschool, ClassDojo, Khan Academy)
- Local AI tools (Ollama, LM Studio, Hugging Face adoption)

**Sources:**
- Product Hunt (weekly launches)
- GitHub stars (trending repos related to offline AI, STT)
- Twitter/X: product announcements
- Google Trends: search volume for "offline AI for families", "Starlink education"

**Frequency:** Bi-weekly (Tuesday & Friday, 12:00 UTC)  
**Output:** `~/.lantern/telemetry/competitor-trends-biweekly.jsonl`

**Payload:**
```json
{
  "timestamp": "2026-05-25T12:00:00Z",
  "competitor": "google_family_link",
  "change": "offline_mode_announced",
  "confidence": 0.65,
  "threat_level": "medium",
  "action_required": "accelerate_offline_music_feature"
}
```

**Action:** If threat_level = "high" = emergency product review

---

## RAG Knowledge Base: What Gets Learned

### KB Structure
```
~/.lantern/knowledge-base/
├── market/
│   ├── family_segments.jsonl  (who buys, why)
│   ├── pain_points.jsonl      (Starlink lag, privacy concerns, etc)
│   ├── willingness_to_pay.jsonl (pricing elasticity)
│   └── feature_requests.jsonl (what families ask for)
├── technical/
│   ├── model_performance.jsonl (Ollama vs Claude vs Gemini latency)
│   ├── common_errors.jsonl     (most frequent failure modes)
│   ├── optimization_insights.jsonl (what makes the app faster)
│   └── memory_profiles.jsonl   (which features leak memory)
├── competitive/
│   ├── market_map.jsonl        (who else is playing in offline AI)
│   ├── feature_gaps.jsonl      (what Lantern is missing vs competitors)
│   └── threat_signals.jsonl    (when competitors move)
└── operational/
    ├── churn_indicators.jsonl  (families about to leave)
    ├── growth_levers.jsonl     (what drives referrals)
    └── cost_structure.jsonl    (unit economics validation)
```

### KB Update Frequency
- **Market data:** Weekly (polling loop 1)
- **Family feedback:** Daily (polling loop 2)
- **Technical metrics:** Hourly (polling loop 3)
- **Competitor tracking:** Bi-weekly (polling loop 4)

---

## RAG Integration: How the App Learns

### During Deployment (Year 1)

**Week 1-4:** Collect raw data (all polling loops active)
```
Lantern running → M5 attestation records technical data
Families using → feedback loop captures satisfaction
Market watching → competitor polling tracks shifts
Result: Raw data in telemetry folder
```

**Month 2:** Analyze + Extract Insights
```
Python script: process_rag_telemetry.py
Input: ~/.lantern/telemetry/*.jsonl
Output: ~/.lantern/knowledge-base/*.jsonl (parsed insights)
Actions generated: "Add offline music feature", "Optimize Ollama latency"
```

**Month 3+:** Closed-Loop Learning
```
Product decision ← RAG knowledge base ← polling loops
Example:
  Market polling shows "3 families mention Starlink latency frustration"
  + Technical polling shows "p95 latency = 1.2s, could be 0.8s with caching"
  → Decision: "Add response caching for Ollama"
  → Implement caching
  → Technical polling re-measures: "p95 latency = 0.8s" ✓
  → Knowledge base updated: "caching reduced latency by 33%"
```

---

## Implementation: Three Levels

### Level 1: Basic Polling (Month 1)
```python
# ~100 lines of Python
import os
import json
from datetime import datetime
from pathlib import Path

class BasicPolling:
    def __init__(self):
        self.kb_path = Path.home() / ".lantern" / "knowledge-base"
        self.kb_path.mkdir(parents=True, exist_ok=True)
    
    def poll_market_sentiment(self):
        """Scrape Reddit for family learning + offline AI mentions"""
        # praw (Reddit API wrapper)
        # Search r/vandwellers, r/homesteading for keywords
        # Store sentiment scores to market/market_sentiment.jsonl
        pass
    
    def poll_family_feedback(self):
        """Collect in-app feedback thumbs"""
        # Read ~/.lantern/state/feedback.jsonl
        # Aggregate: sentiment, feature requests
        # Store to family/feedback_daily.jsonl
        pass
    
    def poll_performance_metrics(self):
        """Aggregate technical metrics from validation-log.jsonl"""
        # Read ~/.lanterns/telemetry/validation-log.jsonl
        # Extract latency, success rates, memory usage
        # Store to technical/performance_hourly.jsonl
        pass
```

### Level 2: Smart Polling (Month 2–3)
Add:
- Sentiment analysis (VADER or transformers)
- Duplicate detection (same feature request from multiple families)
- Anomaly detection (unusual latency, memory growth)
- Trend analysis (is offline AI getting more or less interest?)

### Level 3: Predictive Polling (Month 4–6)
Add:
- **Churn prediction:** Family activity declining → reach out
- **Feature prioritization:** ML model scores which features drive retention
- **Pricing elasticity:** A/B test different prices, measure willingness to pay
- **Growth lever optimization:** Which source (van-life vs homeschool) has highest LTV?

---

## Actionable Outputs: What Gets Built

### Every Week
**Market Sentiment Report** → Shared with founder
```
Van-life families frustrated with Starlink latency (sentiment 0.78, 47 mentions)
→ Decision: Prioritize offline music caching (completed in 3 days)

Homeschooling families want AI to explain "why" not just "what"
→ Decision: Enhance chat with "reasoning" prompts (Gemini/Claude best at this)

Privacy concerns (sentiment 0.91, 200+ mentions) → Keep messaging privacy-first
```

### Every Month
**Product Prioritization Board** → Updated from RAG insights
```
1. [P0] Offline music caching (market: high latency complaints, technical: feasible)
2. [P1] Simplified parental dashboard (feedback: parents can't find controls)
3. [P2] Vosk improvements (technical: STT accuracy at 75%, needs 85%)
4. [P3] Accessibility theme (feedback: 1 family with color-blind child)
```

### Every Quarter
**Strategic Review** → Founder + operators
```
Market Size Updated:
  Y1: 10 families → trending to 12 (slower than expected, cause: weak referrals)
  Action: Improve testimonial capture, create "family story" marketing
  
Revenue Elasticity:
  $20/mo → 100% attach rate
  $30/mo → 70% attach rate (Lantern Kids features)
  Action: Unbundle Kids features, test $25/mo with standard features
  
Competitive Threat:
  Apple announced offline mode (threat_level=high)
  Action: Accelerate privacy messaging, emphasize "we've been offline-first from day 1"
```

---

## Data Privacy & Consent

### What Gets Collected
- **Technical metrics:** Latency, success rates, errors (no PII)
- **Market data:** Public Reddit/Twitter (no private content)
- **Family feedback:** Optional thumbs-up/down, survey responses (encrypted)
- **Performance data:** CPU/memory usage on family's machine (local only)

### What Does NOT Get Collected
- Chat transcripts (stored locally only, never uploaded)
- Family names or identifiable information (use family_id only)
- Browsing history, videos watched, music listened to (never leaves device)
- Camera, microphone, location data

### Consent Model
```
In-app toggle: "Help us improve Lantern by sharing anonymous usage data"
Default: OFF (families must opt-in)
Per-family data encrypted in transit
Operator anonymizes before RAG training
```

---

## Integration with Autopilot

**Existing Autopilot:** Hourly validation checks (M5 attestation)  
**New RAG Polling:** Continuous market + feedback + performance loops

**Together they form a "learning organism":**
```
Autopilot (hourly) ← Technical validation
  ↓
RAG Polling (continuous) ← Market + feedback + competitive intelligence
  ↓
Knowledge Base (growing)
  ↓
Product Decisions (weekly)
  ↓
Implementation
  ↓
Autopilot measures impact
```

---

## Success Metrics (12 Months)

| Metric | Target | Why It Matters |
|--------|--------|----------------|
| Family feedback sentiment | >0.75 | Families are happy |
| Feature request → implementation time | <4 weeks | Fast feedback loop |
| Churn rate | <5% annually | Families stay |
| NPS (Net Promoter Score) | >50 | Families refer friends |
| Technical metric correlation | >0.8 (with satisfaction) | RAG learning is accurate |
| Competitive threat detection time | <48 hours | Fast response to market moves |

---

## Founder Decision Points

- [ ] Month 1: Approve basic polling setup (markets + feedback)
- [ ] Month 2: Review first market sentiment report
- [ ] Month 3: Decide on Level 2 (sentiment analysis, anomaly detection)
- [ ] Month 4: Review product decisions driven by RAG insights
- [ ] Month 6: Plan Level 3 (predictive modeling for churn + pricing)

---

## Files to Create (Implementation)

1. **`scripts/polling_market_sentiment.py`** — Reddit + Twitter scraper (100 lines)
2. **`scripts/polling_family_feedback.py`** — Aggregate in-app feedback (50 lines)
3. **`scripts/polling_technical_metrics.py`** — Parse validation-log.jsonl (80 lines)
4. **`scripts/polling_competitor_tracking.py`** — GitHub + Product Hunt (100 lines)
5. **`scripts/process_rag_telemetry.py`** — Transform raw data to KB (150 lines)
6. **`scripts/rag_decision_engine.py`** — Generate product recommendations (200 lines)
7. **`~/.lantern/knowledge-base/`** — KB directory structure (created at runtime)

---

## Connection to COMET LEAP

**COMET LEAP Phase 2–4:** "Learn in motion"
- Send 10 messages (Week 1)
- First family installs (Week 2–3)
- **← RAG starts collecting feedback immediately**
- Word-of-mouth begins (Week 4)
- **← Market polling detects which segments are referring**

**By Month 2:** You'll have data on:
- What features families love most
- Which acquisition source (van-life vs homeschool) has best retention
- Technical performance bottlenecks
- Exact willingness to pay for features

**By Month 3:** Product priorities are data-driven, not guesses.

---

## Status

**Current:** Design complete, ready for implementation  
**Next:** Create Level 1 polling scripts (Week 1 of Phase 2)  
**Integration:** Autopilot + RAG = continuous product learning system

**Document approval required before implementation.**

