from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from state import AgentState
from agent_node import agent_node
from validation_node import validation_node
from tools.langchain_tools import ALL_TOOLS

tool_node = ToolNode(ALL_TOOLS)


def route_after_agent(state: AgentState):
    """After the agent reasons: if it asked for a tool, go run it.
    Otherwise it has produced a final answer -> send it to validation."""
    # tools_condition returns "tools" or END based on the last message's tool_calls
    if tools_condition(state) == "tools":
        return "tools"
    return "validate"


def route_after_validation(state: AgentState):
    """The bounded retry decision: loop back to the agent ONLY if validation
    failed AND we haven't hit the attempt cap. Otherwise, stop."""
    if state["validation_passed"]:
        return END
    if state["attempts"] >= state["max_attempts"]:
        return END  # give up - out of attempts, return the last (still-wrong) answer
    return "agent"  # self-correct: loop back with feedback in the message history


builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)
builder.add_node("tools", tool_node)
builder.add_node("validate", validation_node)

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", route_after_agent, {"tools": "tools", "validate": "validate"})
builder.add_edge("tools", "agent")
builder.add_conditional_edges("validate", route_after_validation, {"agent": "agent", END: END})

graph = builder.compile()


def run(question: str, max_attempts: int = 3):
    result = graph.invoke({
        "question": question,
        "messages": [],
        "db_result": None,
        "api_result": None,
        "agent_output": None,
        "validation_passed": None,
        "validation_feedback": None,
        "attempts": 0,
        "max_attempts": max_attempts,
        "trace": [],
    })
    return result


if __name__ == "__main__":
    result = run("Is it warmer or colder than average in Ahmedabad right now, for September?")

    print("\n--- FINAL ANSWER ---")
    print(result["agent_output"])
    print(f"\nValidation passed: {result['validation_passed']}  |  Attempts used: {result['attempts']}")

    print("\n--- VALIDATION TRACE ---")
    for entry in result["trace"]:
        print(entry)

    print("\n--- FULL REASONING-ACTION MESSAGE LOG ---")
    for m in result["messages"]:
        label = m.type
        content = m.content if m.content else getattr(m, "tool_calls", "")
        print(f"[{label}] {content}")