# Zepto Support Ticket Manager — Implementation Plan
**For: LLM-driven ("vibe coded") build · Target: production-grade, hackathon-deployable**

This document is a complete, self-contained build spec. It assumes the coding LLM has **no other context** than this file plus the three CSVs (`resolved_tickets.csv`, `orders_context.csv`, `new_tickets.csv`) placed in `backend/app/data/`. Follow phases in order — each phase produces a working, testable increment.

---

## 0. Confirmed Data Reality (from actual files, not the spec doc)

These override any assumption — build against this, not against guesses.

**`resolved_tickets.csv`** (300 rows, header has a BOM — read with `encoding="utf-8-sig"`)
```
ticket_id,category,description,resolution_action,resolution_note,time_to_resolve_min,csat
H-1000,missing_item,milk packet missing from my order,redelivery,missing item re-sent,32,5
```
- `category` ∈ `{missing_item, wrong_item, quality_issue, order_late, refund_pending}`
- `resolution_action` ∈ `{redelivery, full_refund, partial_refund, coupon, refund_reissue, apology_no_action, escalation}`
- `csat` ∈ `{3,4,5}` (integer, no 1s/2s in sample — don't hardcode range assumptions, read dynamically)

**`orders_context.csv`** (30 rows)
```
order_id,items,value_inr,delivery_time_min,delivery_status
ORD-9900,1,999,24,cancelled
```
- `delivery_status` ∈ `{delivered, cancelled}` — **only two values observed**, code defensively for unknowns anyway
- `items` = item count (int), `value_inr` = order value (int)

**`new_tickets.csv`** (30 rows, no BOM)
```
ticket_id,created_at,order_id,description
N-000,2026-08-07T20:58:00,ORD-9900,fruits were rotten
```
- `order_id` always resolves to a row in `orders_context.csv` (verify this at ingest; don't assume in prod)
- No `category` field on incoming tickets — **category must be inferred from the matched precedents**, never taken as given

---

## 1. Architecture Decision

| Layer | Choice | Why |
|---|---|---|
| Backend | **FastAPI (Python)** | Async, auto OpenAPI docs (useful for demo), scikit-learn lives natively here |
| Similarity | **TF-IDF + cosine similarity (scikit-learn)**, in-memory, computed once at startup | 300 rows — no vector DB needed; recompute-on-boot is instant and avoids a stale-index class of bugs |
| Persistence | **SQLite via SQLAlchemy** (swappable to Postgres via `DATABASE_URL` env var) | Zero-ops for free-tier deploy, but ORM keeps a Postgres upgrade path open |
| AI layer (reply + reasoning) | **Anthropic Claude API** (`claude-sonnet-4-6`), called server-side only | Never expose the API key to the frontend |
| Frontend | **React + Vite + Tailwind** | Fast to vibe-code, no build ceremony |
| Realtime (bonus) | **WebSocket** (FastAPI native) for the live stream lane updates | Simpler than SSE + no extra library on frontend |
| Deployment | Backend → **Render/Railway free tier** (Docker), Frontend → **Vercel/Netlify** | Matches "Live public URL (free tier)" requirement |

**Non-negotiable design rule:** the similarity engine and the decision engine are two separate, independently testable modules. The LLM must not merge them — this is what Phase 8 validation scenarios test against.

---

## 2. Folder Structure

```
zepto-ticket-resolver/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, CORS, startup hooks, router mounting
│   │   ├── config.py                 # env-driven settings (pydantic-settings)
│   │   ├── database.py               # SQLAlchemy engine/session
│   │   ├── models.py                 # ORM models
│   │   ├── schemas.py                # Pydantic request/response models
│   │   ├── data/
│   │   │   ├── resolved_tickets.csv
│   │   │   ├── new_tickets.csv
│   │   │   └── orders_context.csv
│   │   ├── services/
│   │   │   ├── ingest.py             # CSV → DB loaders, run once at startup
│   │   │   ├── similarity.py         # TF-IDF index + top-k retrieval
│   │   │   ├── decision_engine.py    # confidence scoring, guardrails, action selection
│   │   │   ├── reply_generator.py    # Claude API calls: drafted reply + "why this action"
│   │   │   ├── pricing.py            # refund-amount heuristics, order-value capping
│   │   │   └── stream_simulator.py   # bonus: replays new_tickets.csv on a timer over WS
│   │   ├── routers/
│   │   │   ├── tickets.py
│   │   │   ├── stats.py
│   │   │   ├── simulate.py
│   │   │   └── ws.py
│   │   └── core/
│   │       └── logging.py
│   ├── tests/
│   │   ├── test_similarity.py
│   │   ├── test_decision_engine.py
│   │   ├── test_pricing.py
│   │   └── test_api_tickets.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env.example
│   └── seed.py                       # standalone script: run ingest.py without booting the server
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── api/client.js             # fetch wrapper, base URL from VITE_API_URL
│   │   ├── components/
│   │   │   ├── Board.jsx             # two-lane layout
│   │   │   ├── Lane.jsx
│   │   │   ├── TicketCard.jsx
│   │   │   ├── PrecedentList.jsx     # top-3 similar tickets, expandable
│   │   │   ├── ConfidenceBadge.jsx
│   │   │   ├── OverrideModal.jsx     # human override with reason capture
│   │   │   ├── StatsBar.jsx          # counts, avg confidence, auto-resolve %
│   │   │   └── StreamControls.jsx    # bonus: start/stop live simulation
│   │   ├── hooks/
│   │   │   └── useTicketsSocket.js
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── docker-compose.yml                 # local: backend + frontend together
├── README.md
└── .gitignore
```

---

## 3. Database Schema

```python
# models.py

class ResolvedTicket(Base):
    __tablename__ = "resolved_tickets"
    id = Column(String, primary_key=True)           # H-1000
    category = Column(String, index=True)
    description = Column(Text)
    resolution_action = Column(String)
    resolution_note = Column(Text)
    time_to_resolve_min = Column(Integer)
    csat = Column(Integer)

class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True)            # ORD-9900
    items = Column(Integer)
    value_inr = Column(Integer)
    delivery_time_min = Column(Integer)
    delivery_status = Column(String, index=True)      # delivered | cancelled

class Ticket(Base):
    __tablename__ = "tickets"                          # incoming tickets, mutable state
    id = Column(String, primary_key=True)              # N-000
    created_at = Column(DateTime)
    order_id = Column(String, ForeignKey("orders.id"))
    description = Column(Text)

    # populated by the pipeline
    status = Column(String, default="pending")          # pending|auto_resolved|needs_human|approved|overridden
    inferred_category = Column(String, nullable=True)
    predicted_action = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    refund_amount_inr = Column(Integer, nullable=True)
    precedent_ids = Column(JSON, nullable=True)          # ["H-1000","H-1042","H-1180"]
    precedent_scores = Column(JSON, nullable=True)        # [0.81,0.77,0.62]
    reasoning = Column(Text, nullable=True)                # "why this action" text
    drafted_reply = Column(Text, nullable=True)
    final_action = Column(String, nullable=True)           # set on approve/override
    resolved_by = Column(String, nullable=True)             # "system" | "human:<name>"
    resolved_at = Column(DateTime, nullable=True)
    override_reason = Column(Text, nullable=True)

class DecisionLog(Base):
    __tablename__ = "decision_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String, ForeignKey("tickets.id"), index=True)
    event_type = Column(String)                # auto_resolve|queue_human|approve|override
    action = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    precedent_ids = Column(JSON, nullable=True)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

Every mutation to a `Ticket` (auto-resolve, queue, approve, override) **must** write a matching `DecisionLog` row in the same transaction. This is what the board's audit trail and the "show what was auto-resolved, why, and with what confidence" requirement runs on.

---

## 4. Phase Plan

### Phase 0 — Repo & Environment Scaffolding
- Init git repo, `.gitignore` (venv, node_modules, `.env`, `*.db`)
- `backend/requirements.txt`:
  ```
  fastapi
  uvicorn[standard]
  sqlalchemy
  pydantic-settings
  scikit-learn
  pandas
  anthropic
  python-multipart
  websockets
  pytest
  httpx
  ```
- `backend/.env.example`:
  ```
  DATABASE_URL=sqlite:///./tickets.db
  ANTHROPIC_API_KEY=
  AUTO_RESOLVE_CONFIDENCE_THRESHOLD=0.55
  AGREEMENT_REQUIRED=true
  CORS_ORIGINS=http://localhost:5173
  ```
- `frontend`: `npm create vite@latest frontend -- --template react`, install Tailwind
- **Acceptance:** `uvicorn app.main:app --reload` boots to an empty FastAPI app; `npm run dev` boots to a blank Vite page.

### Phase 1 — Data Layer & Ingest
- `database.py`: engine + `SessionLocal` + `Base.metadata.create_all()` on startup
- `services/ingest.py`:
  - `load_resolved_tickets(session)`: `pandas.read_csv(path, encoding="utf-8-sig")`, upsert into `ResolvedTicket`
  - `load_orders(session)`: same pattern into `Order`
  - `load_new_tickets(session)`: into `Ticket` with `status="pending"`, leave derived fields null
  - All three are **idempotent** (upsert by primary key, not blind insert) so re-running ingest doesn't duplicate rows
- Wire ingest to run in FastAPI's `startup` event, guarded by "only if table is empty" so restarts are fast
- **Acceptance:** `GET /api/debug/counts` (temporary route, remove before Phase 9) returns `{resolved: 300, orders: 30, tickets: 30}`

### Phase 2 — Similarity Engine
`services/similarity.py`
```python
class SimilarityIndex:
    def __init__(self, resolved_tickets: list[ResolvedTicket]):
        self.ids = [t.id for t in resolved_tickets]
        self.actions = [t.resolution_action for t in resolved_tickets]
        self.categories = [t.category for t in resolved_tickets]
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1,2))
        self.matrix = self.vectorizer.fit_transform([t.description for t in resolved_tickets])

    def top_k(self, query_text: str, k: int = 3) -> list[PrecedentMatch]:
        qv = self.vectorizer.transform([query_text])
        scores = cosine_similarity(qv, self.matrix).flatten()
        top_idx = scores.argsort()[::-1][:k]
        return [PrecedentMatch(id=self.ids[i], action=self.actions[i],
                                category=self.categories[i], score=float(scores[i]))
                for i in top_idx]
```
- Built **once** at startup from the `resolved_tickets` table (not the raw CSV — DB is the source of truth after ingest), stored on `app.state.similarity_index`
- `PrecedentMatch` is a small dataclass/Pydantic model: `{id, action, category, score, description, resolution_note, csat}` (join back to `ResolvedTicket` for the full record when returning to the API)
- **Acceptance (unit test):** query `"milk packet missing from my order"` returns `H-1000` as the #1 match with score > 0.9 (near-exact text match in the sample data)

### Phase 3 — Decision Engine
`services/decision_engine.py`

This is the core logic the validation scenarios in the problem statement test directly. Implement exactly this:

```python
def decide(ticket: Ticket, order: Order, precedents: list[PrecedentMatch],
           threshold: float, require_agreement: bool) -> Decision:
    top = precedents[0]
    actions = [p.action for p in precedents]
    agreement = len(set(actions)) == 1          # all top-3 propose the same action
    majority_action, majority_count = Counter(actions).most_common(1)[0]

    candidate_action = top.action
    confidence = top.score
    if require_agreement and not agreement:
        # disagreement among precedents -> never auto-act, regardless of top score
        return Decision(status="needs_human", action=majority_action,
                         confidence=confidence, reason="precedents disagree on action")

    if top.action == "escalation":
        # historical precedent for this pattern was itself a human escalation
        return Decision(status="needs_human", action=None, confidence=confidence,
                         reason="top precedent was an escalation, not an auto-resolvable action")

    # order-context guardrails — evaluated before the confidence check
    guarded_action, guard_note = apply_order_guardrails(candidate_action, order)
    if guarded_action is None:
        return Decision(status="needs_human", action=candidate_action, confidence=confidence,
                         reason=guard_note)
    candidate_action = guarded_action

    if confidence < threshold:
        return Decision(status="needs_human", action=candidate_action, confidence=confidence,
                         reason=f"top similarity {confidence:.2f} below threshold {threshold}")

    return Decision(status="auto_resolved", action=candidate_action, confidence=confidence,
                     reason=f"matched {top.id} ({confidence:.2f}) and top-3 agree on '{candidate_action}'")
```

`apply_order_guardrails`:
```python
def apply_order_guardrails(action: str, order: Order) -> tuple[str|None, str]:
    if order.delivery_status == "cancelled" and action == "redelivery":
        return None, "order is cancelled — redelivery is not a valid action"
    return action, "ok"
```
- Refund amount (see `pricing.py` below) is computed **after** an action is finalized, and is itself capped at `order.value_inr` — enforce this as a hard `min()`, never trust a heuristic to stay in bounds on its own.

`services/pricing.py`:
```python
def refund_amount(action: str, order: Order) -> int:
    amounts = {
        "full_refund": order.value_inr,
        "refund_reissue": order.value_inr,
        "partial_refund": round(order.value_inr * 0.5),
        "coupon": min(50, order.value_inr),
        "redelivery": 0,
        "apology_no_action": 0,
        "escalation": 0,
    }
    return min(amounts.get(action, 0), order.value_inr)   # hard cap, always
```

- **Acceptance (unit tests, one per validation scenario in the problem statement):**
  1. Clear missing-item ticket with strong precedents → `status == "auto_resolved"`, `refund_amount <= order.value_inr`
  2. Novel/low-similarity ticket → `status == "needs_human"`
  3. Top-3 precedents with mixed actions → `status == "needs_human"` even if top score is high
  4. Ticket on a `cancelled` order whose top precedent action is `redelivery` → never returns `redelivery` as the final action

### Phase 4 — AI Layer (reply + reasoning)
`services/reply_generator.py` — two Claude calls, kept separate so either can fail without blocking the other:

```python
def generate_reply(ticket: Ticket, decision: Decision, precedents: list[PrecedentMatch]) -> str:
    prompt = f"""You are a support agent for a quick-commerce delivery company.
Customer ticket: "{ticket.description}"
Action taken: {decision.action}
{f"Refund amount: Rs {decision.refund_amount}" if decision.refund_amount else ""}
Write a short (2-4 sentence), warm, specific customer-facing reply confirming this resolution.
Do not mention internal ticket IDs, similarity scores, or "precedents"."""
    # call Claude, model="claude-sonnet-4-6", max_tokens=300
    ...

def generate_reasoning(decision: Decision, precedents: list[PrecedentMatch]) -> str:
    # Templated, NOT an LLM call — must be deterministic and auditable for the board's
    # "why this action" display. Compose from precedent ids/scores/actions directly:
    lines = [f"{p.id} ({p.category}, {p.score:.0%} match) → {p.action}" for p in precedents]
    return f"Matched against: " + "; ".join(lines) + f". Decision: {decision.reason}"
```
- **Design choice, worth stating explicitly:** the *reply* is LLM-generated (needs natural language); the *reasoning/"why this action"* trail is template-generated from the precedent data, not the LLM, so the audit trail is never subject to hallucination. This satisfies "answer 'why this action?' with the precedent tickets" without letting an LLM invent a justification.
- Wrap the Claude call in try/except with a plain-template fallback reply, so a missing API key or rate limit never breaks the pipeline.
- **Acceptance:** calling `generate_reply` with a stubbed decision returns non-empty text in under 3s; failure path returns the fallback template, not an exception.

### Phase 5 — Pipeline Orchestration
`services/pipeline.py` (new — ties Phases 2–4 together; this is what every endpoint that "processes" a ticket calls)
```python
def process_ticket(session, ticket: Ticket) -> Ticket:
    order = session.get(Order, ticket.order_id)
    precedents = app.state.similarity_index.top_k(ticket.description, k=3)
    decision = decide(ticket, order, precedents, settings.AUTO_RESOLVE_CONFIDENCE_THRESHOLD,
                       settings.AGREEMENT_REQUIRED)
    if decision.action:
        decision.refund_amount = refund_amount(decision.action, order)
    reasoning = generate_reasoning(decision, precedents)
    reply = generate_reply(ticket, decision, precedents)

    ticket.status = decision.status
    ticket.predicted_action = decision.action
    ticket.confidence = decision.confidence
    ticket.refund_amount_inr = decision.refund_amount
    ticket.precedent_ids = [p.id for p in precedents]
    ticket.precedent_scores = [p.score for p in precedents]
    ticket.inferred_category = precedents[0].category
    ticket.reasoning = reasoning
    ticket.drafted_reply = reply
    if decision.status == "auto_resolved":
        ticket.final_action = decision.action
        ticket.resolved_by = "system"
        ticket.resolved_at = datetime.utcnow()

    session.add(DecisionLog(ticket_id=ticket.id,
                             event_type="auto_resolve" if decision.status=="auto_resolved" else "queue_human",
                             action=decision.action, confidence=decision.confidence,
                             precedent_ids=ticket.precedent_ids, detail=decision.reason))
    session.commit()
    return ticket
```

### Phase 6 — Backend API
All routes under `/api`. Mount with FastAPI routers as shown in the folder structure.

| Method | Path | Purpose | Response |
|---|---|---|---|
| `POST` | `/api/tickets/process-all` | Run `process_ticket` over every `pending` ticket (bulk demo trigger) | `{processed: int}` |
| `POST` | `/api/tickets/{id}/process` | Run pipeline on one ticket | full `TicketOut` |
| `GET` | `/api/tickets?lane=auto|human|all` | Board data | `list[TicketOut]` |
| `GET` | `/api/tickets/{id}` | Single ticket detail incl. precedent full records | `TicketDetailOut` |
| `POST` | `/api/tickets/{id}/approve` | Human confirms the predicted action | updates `final_action`, `resolved_by`, logs `approve` |
| `POST` | `/api/tickets/{id}/override` | Body: `{action: str, reason: str, resolved_by: str}` | updates `final_action`≠`predicted_action`, logs `override` |
| `GET` | `/api/tickets/{id}/log` | Full `DecisionLog` history for one ticket | `list[DecisionLogOut]` |
| `GET` | `/api/stats` | Board summary | `{total, auto_resolved, needs_human, avg_confidence, auto_resolve_rate}` |
| `POST` | `/api/simulate/start` | Bonus: begin replaying tickets over WS at an interval | `{status: "started"}` |
| `POST` | `/api/simulate/stop` | Bonus: stop the stream | `{status: "stopped"}` |
| `WS` | `/ws/tickets` | Bonus: pushes `{event: "ticket_processed", ticket: TicketOut}` on each pipeline run | — |

`schemas.py` — key Pydantic models:
```python
class TicketOut(BaseModel):
    id: str
    description: str
    status: str
    inferred_category: str | None
    predicted_action: str | None
    final_action: str | None
    confidence: float | None
    refund_amount_inr: int | None
    order_id: str
    created_at: datetime

class TicketDetailOut(TicketOut):
    precedents: list[PrecedentDetail]   # joined full ResolvedTicket rows, not just ids
    reasoning: str | None
    drafted_reply: str | None
    order: OrderOut

class OverrideRequest(BaseModel):
    action: str
    reason: str
    resolved_by: str = "human"
```
- **Validation on override:** `action` must be one of the 7 known `resolution_action` values — reject with `422` otherwise (this is a common LLM-agent shortcut to skip; don't skip it).
- **Acceptance:** Postman/curl walkthrough — ingest → process-all → GET board shows correct auto/human split → approve one → override one → stats reflect both.

### Phase 7 — Frontend Board
- `App.jsx`: fetches `/api/stats` and `/api/tickets?lane=all` on load, splits client-side into two arrays for `Lane`
- `Board.jsx`: renders `<Lane title="Auto-Resolved">` and `<Lane title="Needs Human">` side by side
- `TicketCard.jsx`: description, `ConfidenceBadge` (color-coded: green ≥ threshold, amber below), chosen/predicted action, refund amount if any, expandable `PrecedentList` (top-3 with score %, action, csat), drafted reply text, and — only in the "Needs Human" lane — **Approve** and **Override** buttons
- `OverrideModal.jsx`: dropdown of the 7 valid actions + free-text reason, `POST /api/tickets/{id}/override`
- `StatsBar.jsx`: total tickets, auto-resolve %, avg confidence — pulled from `/api/stats`
- Poll `/api/stats` + refetch board every 5s **or** subscribe to `/ws/tickets` if the bonus stream is running — don't build both as competing sources of truth, WS updates should just patch the existing ticket list in state.
- **Acceptance:** loading the frontend against a running backend shows all 30 processed tickets correctly split into lanes, matches the counts from `/api/stats`.

### Phase 8 — Bonus Features (only after Phase 7 is fully working)
1. **Approve/override with logging** — already covered by Phase 6/7 if built as specified; this phase is just confirming the `DecisionLog` trail is complete and visible (add a small "history" expandable section on `TicketCard` hitting `GET /api/tickets/{id}/log`)
2. **Live stream simulation** — `stream_simulator.py`: background `asyncio` task that, every N seconds, pops the next `pending` ticket, runs `process_ticket`, and broadcasts the result over the WS connection manager. Start/stop via the two routes above; `StreamControls.jsx` toggles it.
3. **Embeddings instead of TF-IDF** — add `services/embedding_similarity.py` implementing the same `top_k` interface as `SimilarityIndex` (e.g. via `sentence-transformers` `all-MiniLM-L6-v2`, run locally — no extra API cost) and swap via a `SIMILARITY_BACKEND=tfidf|embeddings` env var so both remain demoable side by side.

### Phase 9 — Deployment
- **Backend:** `Dockerfile` (python:3.11-slim base, `pip install -r requirements.txt`, `CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT`), deploy to Render/Railway free tier, set `ANTHROPIC_API_KEY` and `CORS_ORIGINS=<frontend-url>` as env vars there
- **Frontend:** `VITE_API_URL=<backend-url>` set as a build-time env var on Vercel/Netlify, deploy from the `frontend/` subdirectory
- **Repo:** public GitHub repo, top-level `README.md` with setup, architecture diagram (can be ASCII), and the two live URLs
- **Acceptance:** the two validation scenarios from the problem statement (§6) reproduced against the **deployed** URL, not just localhost

### Phase 10 — Test & Validate Against the Original Scenarios
Run these explicitly and paste the results into `README.md` as a "Validation" section:
1. Missing-item ticket, strong precedents → auto-resolved, refund ≤ order value, reply cites the resolution (not raw precedent IDs)
2. Novel ticket, low similarity → human lane, no action taken
3. Top precedents disagree on action → human lane even with a high top score
4. Cancelled-order ticket whose best-match action is `redelivery` → never auto-resolves as redelivery

---

## 5. Config Defaults (tune these two, nothing else, if demo results look off)
```python
AUTO_RESOLVE_CONFIDENCE_THRESHOLD = 0.55   # cosine similarity of top precedent
AGREEMENT_REQUIRED = True                   # top-3 must share the same action to auto-act
```
If the demo run shows too many novel-looking tickets auto-resolving, raise the threshold first — don't touch the agreement rule, since scenario #3 in validation depends on it staying strict.

---

## 6. Explicit Non-Goals (don't let the LLM scope-creep into these)
- No user auth/login system — this is a hackathon demo board, not a multi-tenant product
- No payment gateway integration — refunds are simulated ledger entries (`refund_amount_inr` field), never a real transaction
- No retraining/ML pipeline — TF-IDF is recomputed at boot, not incrementally updated as tickets resolve
- No mobile-responsive polish required beyond basic Tailwind flex/grid — desktop demo is the target
