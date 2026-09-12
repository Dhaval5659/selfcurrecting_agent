from typing import TypedDict, Optional, List, Dict, Any


class AgentState(TypedDict):
    # --- the task itself ---
    question: str                     # the user's original request, e.g. "Is it colder in Ahmedabad than the DB avg temp for last month?"

    # --- tool outputs (filled in as nodes run) ---
    db_result: Optional[Any]          # whatever the DB query tool returns
    api_result: Optional[Any]         # whatever the external API tool returns

    # --- the agent's working answer ---
    agent_output: Optional[str]       # the agent's current attempt at a final answer

    # --- validation ---
    validation_passed: Optional[bool]
    validation_feedback: Optional[str]  # WHY it failed, fed back to the agent for self-correction

    # --- retry control ---
    attempts: int                     # how many attempts made so far
    max_attempts: int                 # bound so the loop can't run forever

    # --- the deliverable: full reasoning-action trace ---
    trace: List[Dict[str, Any]]       # one entry per step: {"step": ..., "detail": ...}
