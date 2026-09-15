import ast
import json
import re
from langchain_core.messages import ToolMessage, AIMessage, HumanMessage

from state import AgentState


def _parse_tool_content(content: str):
    """Tool results get stringified by ToolNode before landing in the
    message. Depending on LangGraph/LangChain version this comes out as
    either JSON ('true'/'false', double quotes) or a Python dict repr
    ('True'/'False', single quotes) - try both rather than assuming one."""
    try:
        return json.loads(content)
    except (ValueError, TypeError):
        pass
    try:
        return ast.literal_eval(content)
    except (ValueError, SyntaxError):
        return None


def _extract_tool_results(messages):
    """Walk the message history and pull out the actual DB / API results,
    parsed back into dicts. We use the MOST RECENT of each in case this is
    a retry and the tools were called again."""
    db_result, api_result = None, None
    for m in messages:
        if isinstance(m, ToolMessage):
            data = _parse_tool_content(m.content)
            if not isinstance(data, dict) or not data.get("success"):
                continue
            if "avg_temp_celsius" in data:
                db_result = data
            elif "temp_celsius" in data:
                api_result = data
    return db_result, api_result


def validation_node(state: AgentState) -> dict:
    messages = state["messages"]
    final_message = messages[-1]
    agent_output = final_message.content if isinstance(final_message, AIMessage) else ""

    db_result, api_result = _extract_tool_results(messages)

    trace_entry = {"step": "validation", "agent_output": agent_output}
    problems = []

    if db_result is None:
        problems.append("The database tool was never successfully called.")
    if api_result is None:
        problems.append("The external API tool was never successfully called.")

    if db_result and api_result:
        db_temp = db_result["avg_temp_celsius"]
        api_temp = api_result["temp_celsius"]

        # check 1: were the actual numbers quoted correctly in the answer?
        numbers_in_answer = [float(n) for n in re.findall(r"-?\d+\.?\d*", agent_output)]
        if not any(abs(n - db_temp) < 0.1 for n in numbers_in_answer):
            problems.append(f"Answer does not correctly state the DB average temp ({db_temp}C).")
        if not any(abs(n - api_temp) < 0.1 for n in numbers_in_answer):
            problems.append(f"Answer does not correctly state the current API temp ({api_temp}C).")

        # check 2: is the warmer/colder/same comparison logically correct?
        # accept synonyms - the agent isn't wrong just for phrasing it differently
        comparison_words = {
            "warmer": ["warmer", "hotter", "higher"],
            "colder": ["colder", "cooler", "lower", "cooler than", "less than"],
            "same": ["same", "equal", "unchanged"],
        }
        if api_temp > db_temp:
            expected = "warmer"
        elif api_temp < db_temp:
            expected = "colder"
        else:
            expected = "same"

        answer_lower = agent_output.lower()
        if not any(word in answer_lower for word in comparison_words[expected]):
            problems.append(
                f"Comparison is wrong: API temp ({api_temp}C) vs DB avg ({db_temp}C) "
                f"should be described as '{expected}' (or a synonym like {comparison_words[expected]}), "
                f"but the answer doesn't say that."
            )

    passed = len(problems) == 0
    trace_entry["passed"] = passed
    trace_entry["problems"] = problems

    result = {
        "agent_output": agent_output,
        "validation_passed": passed,
        "attempts": state.get("attempts", 0) + 1,
        "trace": state.get("trace", []) + [trace_entry],
    }

    if not passed:
        feedback = "VALIDATION FAILED:\n- " + "\n- ".join(problems) + "\nPlease correct your final answer."
        result["validation_feedback"] = feedback
        # feed the feedback back into the conversation so the agent sees it next turn
        result["messages"] = [HumanMessage(content=feedback)]

    return result