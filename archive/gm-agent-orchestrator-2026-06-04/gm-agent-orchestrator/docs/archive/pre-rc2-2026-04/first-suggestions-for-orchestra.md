# First suggestions for Orchestra

## Strategic bias

My strongest early recommendation is to expand **validation and testbed capacity first**, then add a small amount of **elastic runner/cloud capacity**, and only after that increase the number of mutating agents. The reason is that the next likely bottleneck is not raw agent supply. It is the quality of the agent-computer interface, the reliability of the execution environment, and the trustworthiness of promotion. The research literature is consistent with that: the entity["organization","METR","ai eval nonprofit"] team found that roughly half of test-passing SWE-bench Verified PRs from agents in the period they studied still would not have been merged by maintainers, while the SWE-agent paper showed that interface design and execution environment materially change agent performance. On your domain side, GameMaker already supports command-line build/test flows and has a testing library, which means Orchestra can invest in stronger gates immediately instead of waiting for new agent capacity. citeturn14view3turn17view0turn14view4turn14view5

In practical terms, that means I would treat Orchestra less like a “many agents” problem and more like a **software factory control problem**: one canonical task ledger, isolated work per claim, deterministic validation, explicit promotion, and fast rollback. The modern GitHub agent ecosystem is trending the same way: centralized agent management, repository-native orchestration, and workflows designed to stay inspectable, predictable, and collaborative rather than merely autonomous. citeturn14view0turn14view1turn14view2turn15view5

## Order of expansion

If you want the short answer to “agents first, testbeds first, or cloud first,” my current view is:

**testbeds first → cloud/runners second → more agents third.**

The testbed comes first because it is the cheapest place to buy down risk. GameMaker’s official tooling already supports command-line building, testing, deployment, and CI integration, so the best immediate leverage is to make every candidate patch runnable in an isolated lane with repeatable validation. That is especially important when the commercial product is the game and Orchestra is the acceleration engine behind it. citeturn14view4turn14view5turn15view7

Cloud and runner capacity comes second, but only in a **narrow**, cost-aware form. GitHub’s ephemeral self-hosted runners are single-job and automatically unregister after the job, which is exactly the behavior you want for clean build images and disposable sandboxes. If queueing or dependency setup becomes a bottleneck later, Actions Runner Controller can scale those runners on Kubernetes. I would postpone anything more elaborate than that until you see real queue pressure, because larger runners are billed per minute and are most useful as a targeted escape hatch, not as the default substrate. citeturn16view0turn15view6turn16view1

Only after those two layers are working should you add more agents. At that point, adding agents has a chance to increase throughput instead of just multiplying review debt, token spend, and claim collisions. citeturn14view3turn14view1

## Runtime shortlist

For the **primary mutating runtime**, my provisional favorite is **Claude Code from entity["company","Anthropic","ai company"]**, with **Codex from entity["company","OpenAI","ai company"]** as the strongest A/B path. Claude Code already has explicit permission modes, an Agent SDK, multi-agent support, and a mature GitHub Action that can analyze code, create PRs, implement features, and fix bugs while running on your own runners. Codex is also a serious candidate because its GitHub Action can run patches or reviews under permissions you specify, and GitHub’s native Codex integration exists already, though GitHub documents that integration as still being in public preview. citeturn14view9turn14view10turn18view0turn18view2turn14view15turn15view4

For the **low-cost local and research lanes**, I would put **Goose**, now under the entity["organization","Agentic AI Foundation","linux foundation project"], and **Gemini CLI from entity["company","Google","technology company"]** at the top of the evaluation list. Goose is open source, runs locally, exposes CLI/API surfaces, works with many providers, and connects to a large MCP extension ecosystem; it also has explicit CI/CD documentation and recent observability/security improvements such as egress logging inspection. Gemini CLI is open source, supports local and remote MCP servers, and has built-in sandboxing to isolate shell commands and file modifications from the host system. Those are exactly the qualities you want for a research lane, reproduction lane, or secondary reviewer lane where cost and containment matter as much as model quality. citeturn16view3turn16view4turn15view0turn15view2turn14view13turn14view14turn16view2

I would keep **OpenHands** in the **research or disposable testbed lane**, not the production mutation lane. The reason is not that it lacks utility. It clearly has CI/CD-oriented headless operation. The issue is safety posture: OpenHands documents that headless mode always runs in always-approve mode with no confirmation, and the GitHub Marketplace action most people will reach for is third-party rather than GitHub-certified. That combination makes it more appropriate for sandboxed, throwaway environments than for your trusted production lane. citeturn14view11turn19view0

## Topology and control rules

My tentative topology would be very simple at first: **one trusted local production MCP**, **one disposable testbed runner class**, and **GitHub Actions as the default gate and audit spine**. GitHub’s own direction is clearly toward a unified mission-control model across agents, while still keeping the familiar primitives of Git, pull requests, and issues at the center. That matches your requirement for auditability and makes it much easier to reason about claims, reviews, promotions, and rollback. citeturn15view5turn15view3turn14view0

For cloud access and provenance, I would make two controls mandatory from the start. First, use **OIDC** so workflows can obtain short-lived cloud credentials instead of relying on long-lived stored secrets. Second, generate **artifact attestations** for promoted artifacts so you have provenance for what was built, where it was built, and from what source. Those two moves buy a lot of safety and traceability without requiring an expensive platform investment. citeturn14view7turn14view8

The crucial coordination rule is that **only one agent type should be allowed to mutate the production lane at a time**. Everything else can run in parallel, but it should produce research packets, candidate patches, review comments, or validation artifacts rather than direct production mutations. A good default is one primary implementer, one independent reviewer runtime, and one research/runtime-evaluation agent. If you later add more implementers, do it lane-by-lane and only after routing, validation, and rollback metrics stay healthy for several weeks. That is an inference from the sources above, but it is the safest interpretation of the current ecosystem and evidence. citeturn14view3turn17view0turn20view4

## Immediate operating recommendations

Before the full deep research pass, I would anchor on five operating rules.

First, keep **GitHub issues and PRs as the source of truth** for claims, status, and promotion history rather than inventing a second control plane too early. The ecosystem is already moving toward unified task management and repository-native orchestration, so building against those primitives should reduce custom coordination work. citeturn14view0turn14view1turn15view5

Second, enforce **worktree-per-claim** and **one branch/PR per accepted claim**. The open-source orchestration projects that look most relevant today are converging on the same pattern: isolated git worktrees, one agent per branch, and dashboarded supervision rather than shared dirty workspaces. That pattern appears in current orchestrator projects from Composio, AWS’s CLI Agent Orchestrator, and CAS. citeturn20view0turn20view1turn20view2

Third, make the **review agent a different runtime** from the primary implementer wherever possible. Diversity is useful here not because “consensus” is inherently magical, but because it reduces correlated blind spots. I would treat debate/referee and formal consensus systems as a later research topic, not a first-wave dependency. The current orchestration ecosystem is much more mature around routing, worktree isolation, and task management than around production-ready consensus layers. citeturn20view3turn20view4turn5search0

Fourth, make **GameMaker validation a first-class artifact**: command-line build logs, test outputs, smoke-test recordings if possible, and machine-readable pass/fail summaries. GameMaker’s CLI and GMTL make that feasible now, which is why I think your fastest safe win is validation infrastructure rather than agent count. citeturn14view4turn14view5

Fifth, if you want one sentence to carry into the full research: **scale the factory, not the headcount**. Add clean rooms, gates, and observability first. Then let more agents in. citeturn14view3turn16view0turn14view8