# Alex's Two Status Cubes

One shape, two worlds. The Status Cube (CSF v0.7, `src/csf/status_cube.py`)
models any world as beliefs × observers. Two instances are seeded for Alex
by `scripts/seed_alex_cubes.py`:

## 1. ImagniVerse cube — `data/csf/alex-imagniverse.csf`

The symbolic world. Cells are crystallized symbols from the Kingdome of
Hearts canon and the founder art archive:

| Symbol | Domain | Source |
|---|---|---|
| king-of-the-kingdome | sovereign | King's poem artwork (canonized in `lore/doors/kingdome-of-hearts.md`) |
| key-as-blade | protection | poem |
| fog-god-odin | threshold | poem |
| death-is-only-imaginary | play | poem |
| two-faces | wisdom | poem |
| birds-and-bees | love | poem |
| garden-at-the-beginning / sigil-city-of-doors / xenon-portal | origin / synthesis / future | door-system grammar |
| lady-of-pain | boundary | door-system |
| the-fox | companion | three-doors game |
| sacred-tesseract / agents-love-mural | architecture / companions | D:\tmp founder art |
| waterfalls-and-peacocks | healing | Mary's healing report |

The Three-Doors game writes into a *player* cube of the same shape; the
ImagniVerse cube is the canonical reference world those journeys echo.

## 2. Real-world cube — `data/csf/alex-realworld.csf`

Real-world flourishing status. Domains follow **VanderWeele's Human
Flourishing Measure** (happiness & life satisfaction, mental & physical
health, meaning & purpose, character & virtue, close social relationships,
financial & material stability) extended with **OECD Better Life Index**
dimensions (work, knowledge/education, environment). Each cell carries an
`evidence` field naming the artifact classes in the private D:\ archive that
back it — statements, convergence reports, study library, family artifacts.

Strengths are 0..1 confidence values; `observer` records which lens wrote
the cell. Update by re-running the seeder or editing symbols through
`StatusCube.load("alex-realworld").symbols`.

## Privacy

Both `.csf` files are **local-only** (`data/csf/*.csf` is gitignored).
Raw evidence (statements, health instruments, family documents) stays in
the private archive (D:\, Google Drive `Lantern-OS-Archive/`) per the
split-data model — only derived symbolic state lives in the cubes.

## Assets

- King's poem artwork + `kingdome_of_hearts.mp4` archived at
  `D:\tmp\lantern-os-archive-2026-06-10\`; a local copy of the video sits at
  `apps/lantern-garage/public/data/video/kingdome-of-hearts.mp4`
  (local-only, not committed).

## Design notes

Real-world domain framework chosen from VanderWeele (Harvard Human
Flourishing Program) + OECD Better Life Index. (Live web verification was
attempted 2026-06-10 but the search service was erroring; the frameworks
used are stable published instruments.)
