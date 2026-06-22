feat(queue): auto-assign pending GitHub issues to best-fit idle agent slots

- `LABEL_RESPONSIBILITIES`: maps GitHub issue labels to slot responsibility keywords
- `scoreFitness()`: scores label/responsibility overlap; general_tasks slots get 0.5 floor
- `pickBestFitSlot()`: selects highest-scoring idle slot, falls back to any idle slot
- `POST /api/queue/assign`: assigns top pending issue (or pinned issueNumber) to best-fit idle agent; writes to data/agent-work-queue/assigned/; busts open-issues cache
- `POST /api/queue/dispatch-all`: greedy loop assigns all pending issues to all idle agents until queue or slots exhausted; returns list of assignments made
