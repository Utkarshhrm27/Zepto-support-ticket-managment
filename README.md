# Zepto Support Ticket Manager

A production-grade, AI-driven support ticket resolution system built with FastAPI, React, Tailwind (Gamified Vector-style), and Google Gemini API.

## Features
- **Similarity Engine:** TF-IDF + Cosine Similarity matching against resolved tickets.
- **Decision Engine:** Confidence thresholds, strict guardrails (e.g., no redelivery on cancelled orders), and pricing logic.
- **AI Layer:** Google Gemini 1.5 Flash auto-drafts customer replies based on the resolution context.
- **Gamified UI:** A Black and Red, Neobrutalism vector-style dashboard to track automated vs. human-needed tickets.

## How to Run (1-Click Local Link)

We have provided a unified Docker setup so you can run the entire stack with a single command.

1. Create a `.env` file in the `backend` folder and add your `GOOGLE_API_KEY`:
```
DATABASE_URL=sqlite:///./tickets.db
GOOGLE_API_KEY=your_api_key_here
AUTO_RESOLVE_CONFIDENCE_THRESHOLD=0.55
AGREEMENT_REQUIRED=true
CORS_ORIGINS=http://localhost:5173
```

2. Run Docker Compose from the root directory:
```bash
docker-compose up --build
```

3. **Access the Project Link:** Open [http://localhost:5173](http://localhost:5173) in your browser.

## Validation Scenarios Covered
1. **Missing item:** Clear match auto-resolves with refund capped at order value.
2. **Novel ticket:** Low similarity goes to Human Lane.
3. **Disagreement:** Mixed actions in precedents go to Human Lane.
4. **Guardrails:** Cancelled orders are never flagged for redelivery.
