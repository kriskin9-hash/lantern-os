# Operator Field Notes RAG Intake - 2026-05-26

Status: RAG intake packet.

Source: operator-provided images and handwritten notes in chat on 2026-05-26.

Additional source: operator-pasted session text about GitHub dependency graph,
workflow token safety, central book consolidation, repo settings, local
conversation storage, audio convergence, and session-limit continuity.

Evidence class: `operator_asserted`.

Rights state: `summary_only`.

Purpose: convert the attached field notes into compressed, source-labeled RAG
records that Lantern OS can retrieve without treating raw images, private
family artifacts, or unverified claims as public facts.

## Intake Rules

- Store summaries and boundaries, not raw private image dumps.
- Treat handwriting interpretation as fallible.
- Label speculative or unverified claims as `candidate` or `hold`.
- Keep protected-family creative material private and role-based.
- Do not convert movie metaphors into factual claims.
- Do not treat relationship, medical, financial, unusual-claims, or
  geopolitical notes as verified without separate evidence.

## Field Note Packets

| Packet | Compressed Signal | RAG Decision |
|---|---|---|
| Tony / Ultron / Vision | Avoid building alone; Jarvis, Ultron, and Vision are a cautionary sequence for team boundaries and release gates. | promote as metaphor |
| Unclassified / geopolitics / sensitive claims / cures / UFOs | Broad research coverage is desired, but sensitive domains require source checking, lawful boundaries, and no operational harmful detail. | hold |
| Interpersonal convergence | Meet stubborn or resistant people through explicit agreements, boundaries, hours, consent, and independent research coverage. | promote as boundary |
| Protected creative drawings | Family/child creative art is useful for tone, game-world cues, and education packets, but remains private by default. | promote as private summary |
| Frank Sinatra / PBFT | Audio narration and PBFT-style consensus need long-form implementation notes, operator voting, and no single-operator cascade failure. | candidate |
| Server farm / mining / power | Continuous server use and coin mining require power, heat, cost, legal, and ROI assessment before action. | hold |
| Friends and partners | Find friends, collaborators, and life partners by belief-system fit and mutual consent, not money alone. | candidate |
| Buffett / Jarvis / cash | Buffett-style cash discipline plus Jarvis-style map should route cash to reserves, productive assets, public portfolio display, and anti-sprawl hobbies. | candidate |
| Phone edge node | The phone is an edge capture/control device; no hidden features, no secret collection, no unsafe physical handling. | promote as boundary |
| Foundry incubator | Build a foundry incubator with human resource audit first, PC-first Windows-only, no hidden features, free media/text/video lanes, store mass connector, and founder rails. | candidate |
| Kingdom / game art | "Kingdom of Hearts" and related drawings can seed a game/world style lane without public protected-person exposure. | private summary |
| Spring Valley Wildlife Area | Ohio wetlands marker anchors ecology/local-place learning and source-grounded field observation. | promote as public place note |

## Pasted Session Packets

| Packet | Compressed Signal | RAG Decision |
|---|---|---|
| GitHub dependency graph | No dependencies were shown because supported manifest files were absent or not detected. | candidate |
| Workflow token safety | Prior review claimed workflows use standard token handling and no hardcoded token length checks. | candidate |
| Central RAG book files | Central book index, RAG manifest, consolidation guide, maintenance guide, and deployment checklist were reported ready. | candidate |
| Repo settings | Default branch, PR merge modes, release immutability, branch cleanup, issues, discussions, projects, and signoff settings need governance review. | candidate |
| Conversation storage | Store conversations locally with explicit privacy and git-ignore boundaries. | promote |
| Radio/audio convergence | Sinatra/radio/audio narration should converge across local app, web app, and streamable chat surfaces with rights and controls. | candidate |
| Session-limit continuity | Failed sends and session limits require local handoff packets and persistent local state. | promote |

## Boundaries

Lantern OS should work with this data by making it searchable, actionable, and
bounded. It should not overclaim, publish private material, infer identities,
give investment advice, provide harmful operational detail, or pretend operator notes
are verified outside their source label.

## Cache Path

Promoted compressed records live in:

```text
data/rag-intake/external-llm-web-cache/cache.jsonl
```

The Garage app reads them through:

```text
GET /api/rag-cache
```
