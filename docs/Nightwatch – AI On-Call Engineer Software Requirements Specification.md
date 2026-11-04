# Nightwatch – AI On-Call Engineer: Software Requirements Specification

Nov 4, 2026 · @jo

## 1. Introduction

**Nightwatch is an autonomous AI on-call Site Reliability Engineer (SRE) that watches a startup's production services around the clock, finds the root cause of an incident, and fixes or escalates it, with a human approving every risky step.**

**Role and industry.** On-call SRE for early-stage software startups and small engineering teams (2 to 30 engineers) that cannot afford a dedicated 24/7 reliability team.

**Why this role.**

- Startups lose money and trust during outages, yet cannot staff a night shift. A single engineer is often paged at 3am for problems that follow known patterns.
- The work is multi-step and judgment-heavy (detect, investigate, decide, act, communicate), which suits an agent that reasons with tools rather than a simple chatbot.
- It sits outside HR and recruiting, and every integration used here is free and needs no credit card.

**Scope.** Nightwatch monitors HTTP services deployed on Google Cloud Run, reads their logs and the linked GitHub repository, and acts through GitHub, Telegram and email. It is delivered as a React dashboard plus a Python (FastAPI) backend with a Gemini-powered agent.

**Value proposition.** A team pays for Nightwatch because it cuts mean time to resolution (MTTR) from tens of minutes to a few minutes, never sleeps, and gets smarter with each incident through a searchable memory of past fixes.

**Terms.** SRE: Site Reliability Engineer. MTTR: mean time to resolution. SLO: service level objective. RCA: root cause analysis. Runbook: a documented fix for a known failure.

## 2. Role Research and Breakdown

**An on-call SRE spends an incident doing seven jobs in sequence, and most of the time goes to gathering context, not fixing.** The breakdown below is based on common SRE practice (Google's SRE book, incident-response playbooks, and typical startup on-call rotations).

| # | Sub-function | What the human does today | Depends on |
| --- | --- | --- | --- |
| 1 | Monitoring and detection | Watches dashboards and alerts; decides if an alert is real | Health checks, logs |
| 2 | Triage and severity | Judges customer impact and urgency; decides who to wake up | Detection, service criticality |
| 3 | Investigation and RCA | Reads logs, checks recent deploys and code changes, forms hypotheses | Logs, Git history, past incidents |
| 4 | Remediation | Rolls back, restarts, scales, or patches the code | RCA, deploy access |
| 5 | Communication | Updates the team, stakeholders and status page during the incident | Triage, remediation status |
| 6 | Postmortem and learning | Writes the timeline, root cause and action items after the incident | All previous steps |
| 7 | Reliability reporting | Tracks uptime, MTTR and SLO burn; reports trends to leadership | Incident history |

**Pain points this agent targets.**

- **Context gathering is slow.** Engineers jump between logs, Git and chat to build a picture before they can act.
- **Knowledge is lost.** Fixes live in someone's head or an old chat thread, so the same incident is solved from scratch.
- **Postmortems are skipped.** Teams are tired after an outage and the lessons are never written down.
- **Alerts are noisy.** Many pages are transient blips that do not need a human.

## 3. Impact Prioritization

**Investigation and root cause analysis delivers the most value, so the build puts depth there first, then wraps it with detection, action and learning.** Scores are 1 (low) to 5 (high) and are the author's judgment, not measured data.

| Sub-function | Impact | Effort | MVP scope |
| --- | --- | --- | --- |
| 3. Investigation and RCA | 5 | 4 | Yes, core of the product |
| 4. Remediation (issue, fix PR, rollback) | 5 | 4 | Yes, with approval gates |
| 1. Monitoring and detection | 4 | 2 | Yes, scheduled health and log checks |
| 2. Triage and severity | 4 | 2 | Yes, rules plus Gemini scoring |
| 6. Postmortem and runbook memory | 4 | 3 | Yes, auto-generated and searchable |
| 5. Communication | 3 | 2 | Yes, Telegram and email |
| 7. Reliability reporting | 3 | 2 | Yes, weekly report and dashboard charts |

**Out of scope for the 1-day build:** multi-cloud support, paging phone calls, a paid on-call rotation scheduler, and auto-fixing databases or infrastructure. These appear on the roadmap in section 15.

## 4. Key Workflows

**Nightwatch runs one incident lifecycle and four proactive scheduled jobs, all driven by a single Cloud Scheduler trigger.**

### 4.1 Incident lifecycle

1. **Detect.** A scheduled check finds a failing health endpoint, a spike in error-level logs, or a latency breach.
2. **Triage.** The agent confirms the signal is real (re-checks after 30 seconds to filter blips), assigns severity P1 to P3, and opens an incident record.
3. **Investigate.** The agent calls tools: fetch recent logs, list commits and deploys from the last 24 hours, search runbook memory for similar past incidents.
4. **Diagnose.** Gemini produces ranked root-cause hypotheses, each with a confidence score and the evidence it relied on.
5. **Act.** Depending on the autonomy level (section 6), the agent opens a GitHub issue, drafts a fix pull request, or proposes a rollback and waits for approval.
6. **Communicate.** The agent posts status updates to Telegram and email, and keeps the dashboard timeline current.
7. **Verify and resolve.** After the action, the agent re-checks health. If healthy for 3 consecutive checks, the incident is closed; otherwise it escalates to a human.
8. **Learn.** A postmortem is generated and the resolution is saved to runbook memory with an embedding for future search.

### 4.2 Proactive scheduled jobs

| Job | Cadence | What it does |
| --- | --- | --- |
| Health sweep | Every 5 minutes | Checks every registered service and scans new logs |
| Deploy watch | On each sweep | Detects a new deploy and watches the next 15 minutes closely |
| Daily digest | Daily, 08:00 Africa/Addis\_Ababa | Sends a short status summary and open risks |
| Weekly report | Mondays | Generates uptime, MTTR, top failure causes and the estimated cost of downtime |

The free Cloud Scheduler tier allows 3 jobs, so one "tick" job calls the backend every 5 minutes and the backend decides which of the four jobs are due.

## 5. System Architecture

**A React dashboard talks to one FastAPI backend on Cloud Run; a single Cloud Scheduler tick starts every sweep, and the agent can only act through its defined tools.**

&#91;embedded content: system architecture · dashboard, backend, data and external services\]

The backend is stateless and scales to zero; all state lives in Firestore, so a restart never loses an incident.

| Layer | Technology |
| --- | --- |
| Frontend | React with Vite, a charting library for metrics, Server-Sent Events for the live incident timeline |
| Backend | Python with FastAPI, structured into detectors, tools, agent and notifiers |
| AI | Gemini 2.5 Flash through the Google AI Studio free key; Gemini embeddings for runbook memory |
| Data | Firestore (documents plus vector search done in application code for the small demo dataset) |
| Scheduling | One Cloud Scheduler job calling the tick endpoint |
| Hosting | Cloud Run for the backend and the sample app; static hosting for the dashboard |

## 6. Agent Design

**The agent is a tool-calling loop around Gemini that investigates like an engineer and acts only inside guardrails the user sets.**

### 6.1 Reasoning loop

For each incident the agent repeats: observe (tool result), think (Gemini picks the next tool), act (call the tool), until it reaches a diagnosis or hits a step limit of 8. Every step is saved to the incident timeline so the user can see the reasoning trace.

### 6.2 Tools available to the agent

| Tool | Purpose | Risk |
| --- | --- | --- |
| `fetch_logs` | Read recent Cloud Run logs for a service | Read only |
| `check_health` | Call a service's health endpoint and measure latency | Read only |
| `list_recent_commits` | Get recent commits and deploys from GitHub | Read only |
| `search_runbooks` | Semantic search over past incidents and fixes | Read only |
| `open_github_issue` | Create an issue with evidence and a suggested fix | Low |
| `create_fix_pr` | Open a draft pull request with a proposed patch | Medium, draft only |
| `rollback_deploy` | Shift traffic to the previous Cloud Run revision | High, needs approval |
| `notify` | Send a Telegram message or email | Low |

### 6.3 Autonomy levels

| Level | Behavior | Default for |
| --- | --- | --- |
| Observe | Detects and reports only; takes no action | New services |
| Suggest | Diagnoses and proposes a fix; a human performs it | Production services |
| Act with approval | Prepares the action and waits for one-click approval | Opt-in per service |
| Auto-act (low risk) | Runs pre-approved low-risk actions, such as a restart or a rollback within 15 minutes of a deploy | Opt-in, demo mode |

### 6.4 Runbook memory

Each resolved incident is stored with a text embedding (Gemini embedding model). During investigation, the agent embeds the new symptoms and retrieves the 3 most similar past incidents by cosine similarity. A match above 0.8 raises diagnosis confidence and suggests the previously successful fix.

### 6.5 Confidence and safety guardrails

- Every hypothesis carries a confidence score from 0 to 1; actions above Suggest level require 0.7 or higher.
- Rollbacks and code changes never run without approval unless the user explicitly enables Auto-act for that service.
- The agent cannot touch databases, secrets or infrastructure; its GitHub token is scoped to one repository.
- Every action is written to an audit log with who or what approved it.
- A kill switch in the dashboard pauses all agent actions instantly.

## 7. Third-Party APIs and Integrations

**Nightwatch uses two required free integrations (GitHub and Telegram) plus Gemini and Google Cloud's free tier, so no credit card is needed.** Free-tier limits change, so each one must be re-verified before the build starts.

| Service | Used for | Free-tier note to verify |
| --- | --- | --- |
| Gemini API (Google AI Studio) | Reasoning, root-cause analysis, postmortems, embeddings | Rate limit per minute and per day on the free key; the agent caches results and limits loop steps |
| GitHub REST API | Read commits, create issues, open draft pull requests | Authenticated rate limit of 5,000 requests per hour with a token |
| Telegram Bot API | Incident alerts and approve or reject buttons | Free, no stated message cost; bot token from BotFather |
| Email (Gmail SMTP or SendGrid free) | Daily digest and weekly report | Daily send cap on the free plan |
| Cloud Run | Hosts the backend and a demo target app | Monthly vCPU-second and request allowance |
| Cloud Scheduler | One tick job every 5 minutes | 3 free jobs per billing account |
| Firestore | Incidents, services, runbook memory, audit log | Daily read, write and storage allowance |
| Cloud Logging API | Read logs of monitored Cloud Run services | Free ingestion and retention allowance |

**Why Telegram for approvals.** Inline buttons let a person approve a rollback from their phone in one tap, which makes the "human in the loop" feel real in the demo video.

## 8. Functional Requirements

**The system has six modules; each requirement is testable and tagged Must or Should for the 1-day build.**

### Service registry (SR)

- **SR-1 (Must):** The user can register a service with name, health URL, Cloud Run service name, GitHub repository, and autonomy level.
- **SR-2 (Must):** The user can edit, pause or delete a service.
- **SR-3 (Should):** Each service has a criticality (low, medium, high) used in severity scoring.

### Detection (DT)

- **DT-1 (Must):** A scheduled sweep checks every active service's health endpoint and records status and latency.
- **DT-2 (Must):** The sweep scans new error-level logs and flags spikes against a rolling baseline.
- **DT-3 (Must):** A signal is confirmed by a second check before an incident is created.
- **DT-4 (Should):** The system detects a new deploy and watches the service more closely for 15 minutes.

### Incident handling (IN)

- **IN-1 (Must):** Each incident has an ID, severity, status, timeline and linked evidence.
- **IN-2 (Must):** The agent investigates with the tools in section 6.2 and records every step.
- **IN-3 (Must):** The agent outputs ranked root-cause hypotheses with confidence scores.
- **IN-4 (Must):** The agent proposes an action according to the service's autonomy level.
- **IN-5 (Must):** An approver can approve or reject an action from the dashboard or Telegram.
- **IN-6 (Must):** After an action, the agent verifies recovery with 3 consecutive healthy checks.
- **IN-7 (Should):** Duplicate signals from the same service are merged into one incident.

### Memory and learning (ML)

- **ML-1 (Must):** Each resolved incident is saved to runbook memory with symptoms, cause and fix.
- **ML-2 (Must):** The agent retrieves similar past incidents during investigation.
- **ML-3 (Must):** A postmortem draft is generated automatically with timeline, root cause and action items.

### Communication (CM)

- **CM-1 (Must):** Alerts go to Telegram and email with severity, summary and a dashboard link.
- **CM-2 (Must):** A daily digest and a weekly reliability report are sent on schedule.
- **CM-3 (Should):** The user can ask the agent questions in a chat panel (for example, "why did checkout fail yesterday?") and get answers from incident history.

### Dashboard and control (DB)

- **DB-1 (Must):** The dashboard shows service health, active incidents and recent activity in near real time.
- **DB-2 (Must):** An incident war-room view shows the timeline, reasoning trace, evidence and actions.
- **DB-3 (Must):** A kill switch pauses all agent actions.
- **DB-4 (Must):** A demo panel can inject a controlled failure into the sample app.
- **DB-5 (Should):** Charts show uptime, MTTR and incidents by cause.

## 9. Non-Functional Requirements and Free-Tier Compliance

**Nightwatch must stay inside free tiers and be safe by default, since it acts on production systems.**

| Area | Requirement |
| --- | --- |
| Performance | Detection to first alert in under 2 minutes after the second confirming check; dashboard loads in under 3 seconds |
| Reliability | The monitor itself must not be a single point of failure: failed sweeps are retried, and a missed tick triggers a stale-heartbeat warning |
| Security | Secrets in Secret Manager or environment variables, never in code; GitHub token scoped to one repository; dashboard behind login (Firebase Authentication or Google sign-in) |
| Auditability | Every agent step and every action is stored with a timestamp and approver |
| Cost control | Cap Gemini calls per incident and per day; cache embeddings; no paid services; verify every quota before building |
| Usability | Responsive layout; usable on a phone, since approvals happen on mobile |
| Maintainability | Modular backend (detectors, tools, agent, notifiers); typed API schemas; unit tests for detectors and the tool layer |
| Privacy | Logs are truncated and scrubbed of obvious secrets and personal data before being sent to Gemini |

**Free-tier strategy.**

- Use one Cloud Scheduler job instead of four to respect the 3-job limit.
- Run the backend and the demo app as two Cloud Run services that scale to zero.
- Keep Firestore reads low by writing summaries and using a short polling interval on the dashboard.
- Fall back to rule-based diagnosis if the Gemini quota is exhausted, so the system degrades instead of failing.

## 10. Data Model

**Six Firestore collections hold everything; incidents own their timeline as a sub-collection so the war-room can stream it.**

| Collection | Key fields |
| --- | --- |
| `services` | id, name, healthUrl, cloudRunService, githubRepo, criticality, autonomyLevel, status, lastCheckAt, paused |
| `checks` | serviceId, timestamp, httpStatus, latencyMs, errorLogCount |
| `incidents` | id, serviceId, severity, status (detected, investigating, awaiting\_approval, mitigating, resolved), openedAt, resolvedAt, summary, rootCause, confidence |
| `incidents/{id}/events` | timestamp, type (signal, tool\_call, hypothesis, action, notification, approval), payload |
| `runbooks` | incidentId, symptoms, rootCause, fixApplied, embedding (vector), outcome, createdAt |
| `audit_log` | timestamp, actor (agent or user), action, target, approvedBy, result |

Two supporting records: `settings` (kill switch, notification targets, daily Gemini budget) and `reports` (generated weekly reports and postmortems).

## 11. API Specification

**The backend exposes a small REST API for the dashboard plus two webhooks for the scheduler and Telegram.** All dashboard routes require an authenticated user.

| Method and path | Purpose |
| --- | --- |
| `GET /api/services` | List monitored services with current health |
| `POST /api/services` | Register a service |
| `PATCH /api/services/{id}` | Edit autonomy level, pause or resume |
| `GET /api/incidents` | List incidents, filter by status or severity |
| `GET /api/incidents/{id}` | Incident detail with evidence and hypotheses |
| `GET /api/incidents/{id}/events` | Timeline and reasoning trace (supports live streaming with Server-Sent Events) |
| `POST /api/incidents/{id}/approve` | Approve the proposed action |
| `POST /api/incidents/{id}/reject` | Reject the proposed action with a reason |
| `POST /api/agent/chat` | Ask the agent a question about incident history |
| `GET /api/reports/weekly` | Latest reliability report and metrics |
| `POST /api/settings/kill-switch` | Pause or resume all agent actions |
| `POST /api/demo/chaos` | Inject a controlled failure into the sample app (demo only) |
| `POST /internal/tick` | Called by Cloud Scheduler every 5 minutes; protected by a secret header |
| `POST /webhooks/telegram` | Receives Telegram button presses for approvals |

## 12. UI/UX

**The dashboard is built around one question: "Is everything okay, and if not, what is the agent doing about it?"** It is a React single-page app, responsive down to phone width, with polling or Server-Sent Events for live updates.

| Screen | What the user sees and does |
| --- | --- |
| Overview | Service cards with health, latency sparkline and autonomy level; a banner for active incidents; the global kill switch |
| Incident war-room | Live timeline, the agent's reasoning trace, evidence (logs, commits), ranked hypotheses with confidence, and Approve or Reject buttons |
| Services | Add or edit services, set criticality and autonomy level, connect the GitHub repository |
| Runbook memory | Searchable list of past incidents and fixes; shows which past incident the agent matched |
| Reports | Uptime, MTTR, incidents by cause, and the estimated cost of downtime (user-set hourly cost times outage time) |
| Ask Nightwatch | Chat panel for questions about incident history |
| Demo panel | Buttons to break the sample app (crash, slow responses, bad deploy) for the video |

**Design principles.**

- **Calm by default.** Green and quiet when healthy; attention only when something needs a decision.
- **Explainable.** Every agent claim links to its evidence.
- **Mobile approvals.** One tap approves or rejects, in the dashboard or in Telegram.

## 13. Demo Scenario

**The video shows a real failure happening live and the agent resolving it end to end, with a human approving one step from a phone.**

### Scripted failure: the bad deploy

1. A sample e-commerce API runs on Cloud Run with a GitHub repository. The dashboard shows all green.
2. In the demo panel, click "Deploy bad release". The sample app starts returning errors on checkout.
3. The next sweep detects the error spike; a second check confirms it. Severity P1 is set and a Telegram alert arrives.
4. The war-room fills live: the agent fetches logs, lists commits, and finds that the latest commit changed the checkout code path.
5. Runbook memory returns a similar past incident, and the agent proposes a rollback with 0.86 confidence.
6. The presenter taps Approve in Telegram. The agent shifts traffic to the previous revision.
7. Three healthy checks later the incident closes, and the postmortem and runbook entry are generated.
8. The Reports screen shows the new MTTR and the estimated cost of downtime avoided.

The confidence figure above is an illustrative demo target, not a measured result.

### Second scenario: the slow memory leak

A "slow responses" button degrades latency gradually. The agent flags it before an outage, files a GitHub issue with evidence, and recommends a fix. This shows proactive behavior, not only reaction.

### Video outline (about 8 minutes)

1. Problem and thinking (1 min): why startups need on-call and how the role was chosen.
2. Solution design (1.5 min): architecture and agent loop.
3. Live demo (3.5 min): both scenarios through the UI.
4. Code walkthrough (2 min): frontend, backend, agent tools, scheduler.

## 14. Value Proposition and Differentiation

**A startup would pay for Nightwatch because it replaces the most painful part of on-call: the first 20 minutes of context gathering at 3am.**

| Question | Answer |
| --- | --- |
| Would the buyer pay? | Yes: it reduces downtime cost, protects engineers' sleep, and removes the need to hire a dedicated reliability engineer early |
| Would you hire it over a human? | For first response, yes: it is awake 24/7, never skips the postmortem, and remembers every past incident. A human still approves risky actions |
| What makes it more than alert forwarding? | It investigates with tools, ranks causes with evidence, acts through GitHub, and learns from each incident |
| What makes it safe? | Autonomy levels, approval gates, scoped credentials, an audit log and a kill switch |

**Product thinking beyond the code.**

- **Trust ladder.** Teams start in Observe mode and promote a service to higher autonomy as the agent proves itself, which mirrors how people adopt automation.
- **Business metrics built in.** The estimated cost of downtime turns reliability into a number leadership understands.
- **Compounding value.** Runbook memory means the product improves the longer a team uses it.

**Roadmap after the assignment.** Support for AWS and Azure, a status-page integration, Slack, a paid on-call rotation scheduler, and learning team-specific runbooks from documentation.

## 15. Implementation Plan, Risks and Deliverables

**The build is sequenced so that a working end-to-end demo exists by the middle of the day and the rest is depth and polish.** The assignment allows about one day after approval; the plan assumes roughly 14 working hours.

| Block | Hours | Output |
| --- | --- | --- |
| 1. Foundations | 0 to 2 | GCP project, Firestore, FastAPI skeleton, React app, auth, sample app on Cloud Run |
| 2. Detection | 2 to 4 | Health and log sweeps, tick endpoint, Cloud Scheduler job, incident creation |
| 3. Agent core | 4 to 8 | Gemini tool loop, tools for logs, commits and health, hypotheses with confidence |
| 4. Actions and approvals | 8 to 10 | GitHub issue and draft PR, rollback, Telegram buttons, approval flow |
| 5. Memory and reports | 10 to 12 | Runbook embeddings and search, postmortems, weekly report, charts |
| 6. Polish and video | 12 to 14 | War-room UI, chaos panel, README, architecture diagram, recorded demo |

**Risks and mitigations.**

| Risk | Mitigation |
| --- | --- |
| Gemini quota exhausted | Cap calls per incident, cache results, fall back to rule-based diagnosis |
| Free-tier limits changed | Re-verify quotas before starting; keep one scheduler job |
| Agent proposes a wrong fix | Confidence threshold, approval gates, draft PRs only, kill switch |
| Demo fails on camera | Pre-record a backup run; make the chaos scenario deterministic |
| Scope too large for one day | Build blocks 1 to 4 first; blocks 5 and 6 degrade gracefully |
