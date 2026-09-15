# Self-Correcting Multi-Step Agent

A LangGraph agent that compares a city's historical average temperature
(from a Postgres database) against its current live temperature (from the
Open-Meteo API), validates its own final answer, and self-corrects via a
bounded ReAct-style retry loop if validation fails.

## Architecture

```
START -> agent --(tool call requested?)--> tools -> agent (loop)
                  |
                  v (final answer ready)
               validate --(failed & attempts left?)--> agent (retry, with feedback)
                  |
                  v (passed OR out of attempts)
                 END
```

- **`agent_node.py`** — the reasoning step. An LLM (Groq/Llama) bound to two
  tools, deciding which to call based on the question and, on retries,
  on validation feedback in the conversation history.
- **`tools/db_tool.py` / `tools/api_tool.py`** — plain Python functions with a
  consistent `{"success": bool, ...}` contract, so failures are data the
  agent can reason about instead of crashes.
- **`tools/langchain_tools.py`** — wraps the two functions as `@tool`s the
  LLM can call; the docstrings ARE the tool-selection logic.
- **`validation_node.py`** — checks the agent's final answer against the
  ACTUAL tool results (not the LLM's own judgment of itself): are both
  numbers quoted correctly, and is the warmer/colder comparison right.
- **`graph.py`** — wires the nodes together and implements the bounded
  retry: `route_after_validation()` only loops back to `agent` while
  `attempts < max_attempts`.

## Setup

1. `pip install -r requirements.txt`
2. Copy `.env.example` -> `.env` and fill in your Postgres credentials and
   `GROQ_API_KEY` (free key at console.groq.com)
3. Apply the schema: run `schema.sql` against your database (via `psql` or
   pgAdmin's Query Tool)
4. Sanity-check each piece independently before running the full graph:
   - `python tools/db_tool.py`
   - `python tools/api_tool.py`
5. Run the full agent: `python graph.py`

## Output

Running `graph.py` prints:
- The final validated answer
- Whether validation passed and how many attempts were used
- The validation trace (what was checked, what failed if anything)
- The full reasoning-action message log (every LLM reasoning step, tool
  call, tool result, and self-correction message)

## Design notes

- Validation is plain Python, not another LLM call — the thing checking
  the agent's work should not be equally fallible.
- Retry feedback is injected as a message into the conversation (not just
  stored in a side field) because the agent only ever reasons over
  `state["messages"]` — that's the only way it can actually "see" and
  act on what went wrong.