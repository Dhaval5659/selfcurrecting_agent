import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from state import AgentState
from tools.langchain_tools import ALL_TOOLS

load_dotenv()

llm = ChatGroq(model="openai/gpt-oss-20b", api_key=os.getenv("GROQ_API_KEY"))
llm_with_tools = llm.bind_tools(ALL_TOOLS)

SYSTEM_PROMPT = """You are an agent that answers questions by comparing a
city's historical average temperature (from the database tool) against
today's actual current temperature (from the API tool).

You have two tools available. Use them BOTH before giving a final answer
- you need both the DB average and the live API reading to compare.

Once you have both results, give your FINAL answer as a plain sentence
in exactly this format:
"DB avg for <city> in <month> is <db_temp>C. Current API temp is <api_temp>C.
It is <warmer/colder/the same> than average today."

If you previously received feedback that your answer was invalid, read it
carefully and correct the specific issue - do not just repeat the same
answer.
"""


def agent_node(state: AgentState) -> dict:
    """
    The reasoning step of the ReAct loop. On the first call, seeds the
    conversation with the system prompt + question. On later calls (after
    a tool result, or after a failed validation), it just sees the growing
    `messages` list and reasons over it.
    """
    if not state.get("messages"):
        messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=state["question"])]
    else:
        messages = state["messages"]

    response = llm_with_tools.invoke(messages)

    # `add_messages` reducer appends this to state["messages"] automatically
    return {"messages": [response]}