# Evidence & Confidence Loops Framework

**Purpose:** Tie all decisions to measurable wins  
**Review cadence:** Weekly (Friday synthesis)  
**Confidence scale:** 20%-95%

---

## Evidence Classification (5 Classes)

### 1. Repo-Verified (95% confidence)
**Definition:** Code, committed changes, documented architecture  
**Examples:**
- GitHub commit history shows feature shipped
- Documentation in repo explains implementation
- Tests pass, code review approved

**When to use:** Technical claims, architectural decisions, deployed features

---

### 2. Source-Verified (80% confidence)
**Definition:** Direct source data - customer interviews, surveys, transaction records  
**Examples:**
- 5 customers confirm they want weekly check-ins
- Transaction log shows 50% of families paid
- Survey: 80% would recommend to friend

**When to use:** Customer needs, market validation, early revenue signals

---

### 3. Operator-Asserted (60% confidence)
**Definition:** Founder judgment, advisor feedback, team consensus  
**Examples:**
- Advisor says "this positioning will work"
- Founder gut: "families will pay $49/month"
- Team consensus: "we should prioritize medication tracking"

**When to use:** Strategic decisions, product prioritization, go/no-go calls

---

### 4. Projection (40% confidence)
**Definition:** Financial models, growth assumptions, future scenarios  
**Examples:**
- If 3 pilots convert, revenue will be $5k/month
- Market size projection: 3.4M homeschool families
- Assumes 0.1% adoption rate = 3,400 families

**When to use:** Financial forecasting, market sizing, long-term planning

---

### 5. Hypothesis Only (20% confidence)
**Definition:** Untested assumptions, no supporting evidence  
**Examples:**
- "Families will love the mobile app"
- "Older adults prefer phone calls"
- "Healthcare providers trust new tools"

**When to use:** Brainstorming, early ideation, risk identification

---

## Confidence Scoring System (20-95%)

### Score Interpretation

| Score | Meaning | Action |
|-------|---------|--------|
| **95%** | Multiple independent sources, repeated validation | Commit major resources |
| **80%** | Primary source + secondary confirmation | Allocate 70% of budget (proven channel) |
| **60%** | Single credible source, reasonable but untested | Allocate 20% of budget (emerging) |
| **40%** | Assumption-based, plausible but unvalidated | Run small experiment (<$200) |
| **20%** | Hypothesis only, minimal support | Brainstorm/explore, no budget |

---

## Building the Confidence Ledger

### Starting Assumptions (Week 1)

| Assumption | Category | Evidence Class | Initial Score | Why? |
|-----------|----------|-----------------|---------------|------|
| Families want weekly care coordination | Product | Hypothesis | 20% | Untested, sounds reasonable |
| Institutional partners value revenue share | Market | Operator-Asserted | 60% | Advisor confidence |
| Care coordination reduces hospitalizations | Outcome | Projection | 40% | Published studies suggest, untested for us |
| Privacy-first positioning resonates | Marketing | Hypothesis | 20% | No customer testing yet |
| $49/month pricing is sustainable | Revenue | Projection | 40% | Benchmarked against competitors |

---

## Weekly Confidence Update Process

### Every Friday (Part of Synthesis Meeting)

**Step 1: Recap experiments**
- What did we test Mon-Th?
- What were the results?

**Step 2: Update evidence class**
- Did we move from Hypothesis to Source-Verified?
- Did we gather repo-verified data?

**Step 3: Recalculate confidence**
- Update score based on new evidence
- Document what changed

**Step 4: Tier by priority**
- Which assumptions matter most?
- Which need urgent testing?

**Step 5: Reallocate capital**
- High confidence (80%+) = Proven channel (70%)
- Medium confidence (40-80%) = Emerging (20%)
- Low confidence (<40%) = Exploration (10%)

---

## Measurable Wins - Tying Confidence to Results

### What Makes a "Win"?

âœ“ **Confidence increased 20+ points** (e.g., 40% â†’ 65%)  
âœ“ **Evidence class improved** (e.g., Hypothesis â†’ Source-Verified)  
âœ“ **Customer action taken** (e.g., signed pilot agreement)  
âœ“ **Revenue generated** (e.g., first $500 from pilot)  
âœ“ **Blocker removed (2026-05-27)** (e.g., resolved technical issue)

---

## Month 1 Confidence Targets

### By End of Month 1

| Assumption | Start | Target | Evidence Class | How to Validate |
|-----------|-------|--------|-----------------|-----------------|
| Families want weekly coordination | 20% | 75% | Source-Verified | 5+ customer interviews confirm |
| Institutional partners value offer | 60% | 85% | Source-Verified | 2+ partners express interest |
| Care coordination is feasible to build | 40% | 80% | Repo-Verified | MVP shipped, families using |
| Privacy messaging resonates | 20% | 70% | Source-Verified | Test 3 messaging variants, A wins |
| Revenue model is viable | 40% | 70% | Source-Verified | First partner signs agreement |

---

## Risk Ranking Matrix

### Identify Risks by Impact Ã— Probability

**Impact scoring:** 1-5 (1=minor, 5=fatal)  
**Probability scoring:** 1-5 (1=unlikely, 5=likely)

| Risk | Impact | Prob | Score | Evidence | Mitigation |
|------|--------|------|-------|----------|-----------|
| Families don't engage with platform | 5 | 3 | 15 | Hypothesis | Run 2-week pilot, measure adoption |
| Institutional partners won't commit | 5 | 2 | 10 | Operator-Asserted | 3+ outreach conversations |
| Founder burnout in Month 2-3 | 4 | 3 | 12 | Operator-Asserted | Weekly recovery windows, advisor support |
| Competitor enters market | 3 | 2 | 6 | Hypothesis | Build quickly, focus on unit economics |
| Regulatory pushback on data handling | 4 | 2 | 8 | Projection | HIPAA-compliant architecture, legal review M2 |

**Action:** Test top 3 risks weekly. Mitigate if score increases.

---

## Confidence Loop - Revenue Connection

### Month 1: Validation Phase
- **Confidence goal:** 70%+ on core assumptions
- **Revenue:** $0 (building evidence)
- **Win:** Institution signs pilot agreement

### Month 2: Growth Phase
- **Confidence goal:** 75%+ on all major assumptions
- **Revenue:** $500+ per month (pilot fees)
- **Win:** First customer pays, measurable engagement

### Month 3: Scaling Phase
- **Confidence goal:** 80%+ (ready to scale)
- **Revenue:** $2,000-5,000/month
- **Win:** Institutional partner revenue covers 50% of burn

### Month 4: Breakeven Approach
- **Confidence goal:** 85%+ (stable model)
- **Revenue:** $5,000-10,000/month
- **Win:** Monthly profit positive or breakeven

---

## Weekly Evidence Synthesis Template

**Every Friday 4pm - 15 minutes**

| Assumption | Mon Conf | Tue | Wed | Thu | Fri Conf | Evidence Change | Win? |
|-----------|----------|-----|-----|-----|----------|-----------------|------|
| Families want weekly check-ins | 20% | 30% | 40% | 60% | 75% | Hypothesis â†’ Source-Verified (5 interviews) | âœ“ |
| Revenue share resonates | 60% | 70% | 75% | 80% | 85% | Operator-Asserted â†’ Source-Verified (2 interested) | âœ“ |
| Privacy messaging works | 20% | 30% | 40% | 45% | 50% | A/B test in progress | â—‹ |

---

## Monthly Confidence Reflection

**Last Friday of Month (30 min)**

**Questions:**
1. Which assumptions had biggest confidence gains? Why?
2. Which surprised us (moved opposite direction)?
3. Are we more confident in the business model overall?
4. What's our biggest remaining risk?
5. What single experiment would increase confidence most next month?

**Output:**
- Confidence trajectory chart (month 1-2-3-4)
- Risk reassessment
- Next month experiment roadmap

---

## Red Flags - When Confidence is Declining

ðŸš¨ **Confidence drops 20+ points in one week:** Investigate immediately

ðŸš¨ **Evidence class downgrading:** (e.g., Source-Verified â†’ Hypothesis) means we lost support

ðŸš¨ **Risk scores increasing:** Means our mitigation isn't working

ðŸš¨ **No wins for 2+ weeks:** Time to pivot or accelerate testing

---

## Confidence Ledger - Ready to Track

**Start tracking:** This week  
**Review:** Every Friday 4pm  
**Owner:** Founder  
**Share with:** Advisors (weekly email summary)

**Success:** By Month 4, core assumptions at 85%+ confidence with Source-Verified or Repo-Verified evidence

---

**Implementation:** Begin tracking confidence changes this Friday  
**First review:** May 31, 2026 (end of Week 1)  
**Founder commitment:** 30 min/week confidence updates
