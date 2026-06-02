# Dream Journal — Complete User Guide

**Version:** 1.0.0  
**Last Updated:** 2026-06-02  
**Status:** Production Ready  
**Your dreams. Your space. Always private.**

---

## What Dream Journal Does

Dream Journal is a private, local-first system for capturing, analyzing, and understanding your dreams. Everything runs on your machine. Nothing is sent anywhere without your permission. Your dream data is yours alone.

It helps you:
- **Remember** dreams you'd otherwise forget
- **Track** patterns in your sleep, emotions, and creativity
- **Reflect** on what your dreams mean for your life
- **Grow** through guided analysis and self-discovery

Think of it as a secure, intelligent journal that gets smarter the more you use it.

---

## Quick Start (5 minutes)

### 1. Open Dream Journal
Choose your surface:

**Web (local file):** Open `surfaces/dream-journal/index.html` in your browser. No server required. Data saves to browser localStorage and can be exported as JSONL.

**Discord:** Type `/dream` in any channel where Lantern bot is present, or use `!dream` in text channels.

**Lantern Garage:** Open your browser to **http://127.0.0.1:4177** for the full dashboard with analytics.

### 2. Create Your First Entry
Click **Dreamer** or **New Entry** and you'll see a form with:
- **Type:** What kind of entry (dream, note, memory, etc.)
- **Text:** What you remember or want to record
- **Lucidity:** How aware you were (scale: 0 = not lucid, 1 = fully lucid)
- **Emotions:** How you felt (awe, peace, fear, confusion, etc.)
- **Tags:** Keywords to organize and find entries later

Click **Save**. Your entry is stored immediately.

### 3. View Your Dashboard
Click the **Dashboard** link to see:
- Timeline of all your entries
- Emotion distribution (what feelings dominate)
- Tag cloud (what themes appear most)
- Average lucidity and trends
- Matrix view showing how entries cluster

That's it. You're using Dream Journal.

---

## Entry Types: What to Record

### 🌙 Dream
An actual dream you had. Include as much detail as you remember—sensory images, people, emotions, actions.

**Example:**
> I walked through a blue door into starlight and a silver river that reflected impossible constellations. Everything felt peaceful and vast.

### 📝 Note
A waking thought, reflection, or insight. Use notes to record your interpretation of a dream or a sudden realization.

**Example:**
> Pattern: I'm more lucid in geometrically complex dreams. Maybe understanding structure = awareness?

### 🏠 Place
A recurring location from your dreams. Describe what it looks like, how it feels, what it represents.

**Example:**
> Crystal City: Buildings made of geometric shapes. Each one is a different pattern. Flying through feels like exploring different solutions.

### 👤 Character
A person or being from your dreams. What do they look like? What do they want? What do they mean to you?

**Example:**
> The Guide: Tall figure with a lantern. Appears when I'm trying to understand something. Represents my inner wisdom.

### 🎬 Event
A significant dream moment or sequence. Use for complex narratives that span multiple dreams.

**Example:**
> The Crossing: I stepped off a cliff, fell, then flew. When I accepted falling, I could fly.

### 📚 Lore
Deep worldbuilding from your dreams. If your dreams have consistent rules, worlds, or mythologies, document them here.

**Example:**
> In the Crystalline World, architecture determines consciousness. Complex shapes = high lucidity. Simple shapes = low lucidity.

### ✨ Symbol
A recurring image or object. Track how its meaning evolves. From scary → mysterious → powerful.

**Example:**
> The Lantern: Appears in 5 dreams. Started as fear, became my guide, now represents clarity.

### 🪞 Mirror
A reflection that connects multiple entries. Ask questions, see patterns, synthesize insights.

**Example:**
> Why does architecture appear in every lucid dream? Maybe because structure helps me recognize I'm dreaming. Mirror on: dream_123, dream_456, note_789.

---

## Understanding the Scales

### Lucidity (0.0 to 1.0)

How aware you were during the dream that you were dreaming.

| Score | Meaning | What it feels like |
|-------|---------|-------------------|
| **0.0** | Non-lucid | Dream feels completely real. No awareness you're dreaming. |
| **0.3** | Slight awareness | Something seems odd, but you don't act on it. |
| **0.5** | Partial lucidity | You know you're dreaming but can't fully control actions. |
| **0.7** | High lucidity | Know you're dreaming. Can control some things (movement, speech). |
| **1.0** | Full lucidity | Complete awareness and control. You can change the environment. |

**Tip:** Lucidity is subjective. Consistency matters more than absolute accuracy. If you always use 0.5 for "semi-aware," that's fine—patterns will still emerge.

### Emotions (choose as many as apply)

What you felt during the dream. Common options:

**Positive:** awe, curiosity, peace, wonder, joy, clarity, confidence, playfulness, love  
**Challenging:** fear, confusion, loss, anger, uncertainty, overwhelm, sadness, frustration  
**Reflective:** contemplation, longing, acceptance, compassion, loneliness, vulnerability

**Tip:** Dreams are complex. Tag both `wonder` AND `fear` if that's what you felt.

### Tags (up to 10)

Keywords that help you search and discover patterns.

**Good tag strategies:**
- **Symbols:** `river`, `door`, `light`, `mountain`, `animal`
- **Themes:** `flying`, `falling`, `water`, `architecture`, `journey`
- **People:** `mother`, `mentor`, `child`, `friend`, `stranger`
- **Life domains:** `work`, `relationships`, `creativity`, `health`, `finances`
- **Qualities:** `lucid`, `recurring`, `intense`, `peaceful`, `confusing`

**Tip:** Be consistent. Use `flying` always, not sometimes `flying` and sometimes `flight`. Then your tag cloud will show the real frequency.

---

## Dashboard & Analytics

### What You Can See

**Timeline:** All your entries arranged by date. Hover to see how many entries you had each week.

**Heatmap:** Visual intensity map. Bright areas = weeks with more entries. Helps you spot when you were dreaming most actively.

**Tag Cloud:** Your most-used tags, sized by frequency. At a glance: what's dominating your dream world? Flying? Architecture? Relationships?

**Emotion Distribution:** Pie chart showing your emotional landscape. Are most dreams peaceful? Challenging? Balanced?

**Lucidity Stats:** 
- Average lucidity across all dreams
- Trend (are you becoming more lucid over time?)
- Your highest lucidity dream

**Matrix View:** A 3D plot where entries cluster by:
- **Meaning** (x-axis): How symbolic or deep
- **Clarity** (y-axis): How vivid or memorable
- **Control** (z-axis): How much agency you had

Close entries in this space may have related meanings.

### Using Analytics

**Weekly review (15 min):**
1. Look at the timeline—any patterns in when you dream?
2. Check the tag cloud—what shifted this week?
3. Notice your emotions—are they changing?
4. Create one mirror entry with an insight

**Monthly deep dive (30 min):**
1. Review all stats for the month
2. Identify 2-3 recurring symbols or themes
3. Check if lucidity is trending up or down
4. Record findings in a new lore or mirror entry

**Pattern hunting:**
Look for correlations. Do you dream more vividly before stressful events? After creative work? On certain days? Track what you discover.

---

## Search & Discovery

### Full-Text Search
Find entries by any words in them.

**Example:**
```
Search: "blue door"
Results: All entries containing "blue" or "door"
```

### Tag Search
Filter by tags. You can search for one tag or multiple (must match ALL).

**Example:**
```
Search: ["flying", "lucid"]
Results: Only entries with BOTH flying AND lucid
```

### Smart Combinations
Type text + select tags to search both simultaneously.

**Example:**
```
Text: "crystal"
Tags: ["architecture", "lucidity"]
Results: Entries mentioning "crystal" AND having both those tags
```

**Tip:** Consistent tagging is your friend. Spend 10 seconds choosing good tags, and searching becomes powerful.

---

## Privacy & Storage

**Everything stays on your machine.** Nothing is sent anywhere without your explicit choice.

Your dream data is stored in:
```
data/dream_journal/dreams_YYYY-MM.jsonl
```

One file per month. Append-only. Never modified. This preserves your original memories exactly as you recorded them.

**Backup:** Copy the `data/dream_journal/` folder to back up everything. That's it.

**Deleted entries:** We don't support deletion. Your original memories are part of your history. Instead, create a new entry if you want to revise or reflect on something.

---

## Dream Reflection & Interpretation

### Mirror Entries (Synthesis)

Mirrors are special entries that connect and analyze multiple dreams. Use them to see patterns you wouldn't notice alone.

**Example mirror:**
```
I notice my "crystal architecture" dreams (entries: 5, 12, 23) 
correlate with high lucidity (avg 0.85). But "water" dreams 
(entries: 2, 8, 14) have lower lucidity (avg 0.4).

Question: Why?
Theory: Static geometric shapes help me recognize I'm dreaming. 
Fluid environments keep me immersed.

Implication: Understanding structure = awareness.
```

**When to create mirrors:**
- Weekly: Review the past week, write one insight
- Monthly: Look for recurring symbols and their evolution
- Anytime: You notice a connection or pattern

### Symbol Evolution Tracking

If a symbol appears in multiple dreams, create a `symbol` entry to track how its meaning shifts.

**Example:**
```
The Lantern (symbol entry)

Dream 1 (Jan): Searching for a lantern in darkness = seeking guidance
Dream 3 (Feb): I carry the lantern = taking ownership
Dream 7 (Apr): The lantern is me = I am the light source

Evolution: From seeking external wisdom → to embodying it
```

### Character Development

Track recurring dream characters the way you'd track people in a story:
- How do they change over time?
- What do they want from you?
- What do they represent?

**Example:**
```
The Mentor (character entry)

Early dreams: Gives me answers
Recent dreams: Asks me questions
Shift: I'm becoming more independent

This mirrors my real life: less needing external validation, 
more trusting myself.
```

### Lore as Worldbuilding

If your dreams have consistent locations or rules, document them as lore.

**Example:**
```
The Crystalline World (lore entry)

Rules:
- Simple shapes = low lucidity, immersion
- Complex geometry = high lucidity, control
- Architecture determines consciousness

Inhabitants: The Fox, The Guide
Geography: Towers, rivers, floating islands
Mood: Wonder mixed with mystery
```

### Lucidity Training Through Pattern Recognition

Track what conditions produce lucid dreams:

**Example analysis:**
```
High lucidity correlates with:
- Geometric environments (0.85 avg)
- Morning dreams (0.78 avg)
- After creative work (0.81 avg)

Low lucidity correlates with:
- Chaotic/fluid environments (0.42 avg)
- Late night dreams (0.35 avg)
- After stressful events (0.38 avg)

Action: Spend more time understanding complex systems. 
This trains lucidity.
```

---

## Best Practices

### Daily Recording
**Best time:** Within 5 minutes of waking, before the dream fades.

**How much to write:** 2-5 sentences is enough. Quality over quantity. Key images and feelings matter more than complete narrative.

**Even fragments count:**
```
Fragments are valid entries:
- "Falling. Water. Felt safe."
- "Door. Blue. Something important happened."
- "Flying with control. Everything geometric."
```

### Weekly Review (15 min ritual)
1. Open the dashboard
2. Look at your timeline—did you remember dreams this week?
3. Check the emotion distribution—how are you feeling?
4. Notice the tag cloud—what themes emerged?
5. Create one **mirror** entry with an insight
6. Close the journal

That's enough to build momentum.

### Monthly Deep Dive (30 min)
1. Review all stats for the entire month
2. Look for 2-3 recurring symbols or themes
3. Check if your lucidity is improving
4. Create a **lore** entry about any recurring locations
5. Record findings and theories in a new entry

### Yearly Reflection (1-2 hours)
1. Read through the entire year
2. Identify major symbols and their evolution
3. Notice how you've grown and changed
4. Document major insights
5. Set intentions for the coming year

### Tag Consistency
Use the same tags every time. This makes the tag cloud meaningful and search powerful.

| Instead of... | Use... |
|---|---|
| flying, flight, airborne | flying |
| water, ocean, sea, river | water |
| parent, mother, father | parent |
| work, job, career, business | work |

One consistent term per concept = powerful analytics.

### Emotion Honesty
Tag what you actually felt, not what you think you should have felt.

Bad: Over-tagging positive emotions to feel better
Good: "This dream was scary and confusing" if that's true
Better: "This dream had both wonder and dread"

Your data is only useful if it's honest.

---

## Troubleshooting

**"My entry isn't showing up"**  
Refresh the page. Dream Journal saves immediately. If it still doesn't appear, check your browser console (F12) for errors.

**"Search isn't finding my entry"**  
Remember: Tag search requires ALL tags to match. Search for `["flying", "lucid"]` = entries with BOTH tags.
Full-text search is more forgiving: search "fly" and find "flying."

**"I want to edit an old entry"**  
Entries are write-once to preserve original memory. Instead, create a new entry with corrections or new insights.

**"I want to delete an entry"**  
We don't support deletion. Your history is valuable. Create a new entry if you want to reflect on or revise something.

**"Is my data really private?"**  
Yes. Everything is stored in `data/dream_journal/` on your machine. Nothing is sent anywhere without your explicit choice.

**"How do I back up my dreams?"**  
Copy the `data/dream_journal/` folder to an external drive or cloud storage. That's your backup.

---

## FAQ

**Q: Can I use Dream Journal offline?**  
A: Yes. Everything works locally. No internet needed.

**Q: Can I share a dream with someone?**  
A: Yes. Export it as JSON or use Discord integration (coming soon). Never share without consent.

**Q: How far back does history go?**  
A: As far as you've recorded. Files are organized by month: `dreams_2026-06.jsonl`, `dreams_2026-05.jsonl`, etc.

**Q: Should I use this for waking thoughts too?**  
A: Absolutely. Dream Journal works for any reflection, memory, or insight. Not limited to actual dreams.

**Q: Why are entries append-only?**  
A: Your original memory—even confusion or gaps—is valuable. Editing changes what was. Recording what happened preserves truth.

**Q: What if lucidity tracking seems subjective?**  
A: It is. The scale is personal. What matters is consistency. If you always rate "semi-aware" as 0.5, patterns will still emerge.

**Q: Can I use this on mobile?**  
A: Currently optimized for desktop. Mobile access coming in v2.0.

**Q: How often should I use this?**  
A: Daily if possible. But weekly is enough to see patterns. Even sporadic entries build a useful history.

---

## API Reference (Advanced)

If you want to access your dream data programmatically:

```bash
# Get all dreams tagged "flying"
curl http://127.0.0.1:4177/api/dream/search?tags=flying

# Get analytics
curl http://127.0.0.1:4177/api/dream/stats

# Create a new entry
curl -X POST http://127.0.0.1:4177/api/dream/create \
  -H "Content-Type: application/json" \
  -d '{
    "kind": "dream",
    "text": "I was flying through crystal cities",
    "lucidity": 0.8,
    "emotions": ["wonder", "clarity"],
    "tags": ["flying", "lucid", "architecture"]
  }'

# Retrieve a specific entry by ID
curl http://127.0.0.1:4177/api/dream/read/dream_20260602_143022
```

---

## Related Documentation

**Technical Details:**
- `skills/dream_journal/SKILL.md` — Complete technical spec
- `apps/lantern-garage/server.js` — REST API implementation

**Setup & Deployment:**
- `docs/LANTERN-LOCAL-LAUNCH-RUNBOOK.md` — How to start the full system
- `DISCORD-BOT-QUICKSTART.md` — Discord bot setup (if using Discord integration)

**Your Data:**
- Dreams are stored in: `data/dream_journal/dreams_YYYY-MM.jsonl`
- One file per month, append-only format
- Raw JSON entries—you can read and analyze them directly

---

## Getting Help

**Report an issue:** [github.com/alex-place/lantern-os/issues](https://github.com/alex-place/lantern-os/issues)

**Documentation:** See `/docs/` for technical guides and system architecture

**Community:** Join the Lantern OS Discord for discussion and dream interpretation

---

## Your Dream Journey

Dream Journal is a practice. It works best when you approach it with curiosity rather than judgment.

Record consistently. Review periodically. Trust the process.

Patterns emerge over weeks and months, not days. Your dreams are a conversation with yourself. This journal is where you listen and record what you hear.

The more you record, the clearer the patterns become. The more you reflect, the deeper your understanding grows.

Your dreams are worth paying attention to. You're in the right place.

---

**Made with intention by Alex Place**  
*Part of Lantern OS: a personal operating system for memory, reflection, and becoming.*

**Version:** 1.0.0  
**Last Updated:** 2026-06-02  
**Status:** Production Ready  
**License:** Proprietary (Lantern OS)
