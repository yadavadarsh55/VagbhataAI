from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_google_genai import ChatGoogleGenerativeAI


from config import settings
from prompts import SYSTEM_PROMPT
from tools import ALL_TOOLS

# 1. Define State
class BotState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# 2. Initialize Model
llm = ChatGoogleGenerativeAI(model=settings.LLM_MODEL)
llm_with_tools = llm.bind_tools(tools=ALL_TOOLS)

# 3. Define Nodes
def get_response(state: BotState) -> dict:
    """
    Processes the state and generates a response using the LLM.
    """
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state['messages']
    response = llm_with_tools.invoke(messages)
    return {'messages': [response]}

# 4. Build Graph
def build_graph():
    graph_builder = StateGraph(BotState)
    tool_node = ToolNode(ALL_TOOLS)

    graph_builder.add_node('get_response', get_response)
    graph_builder.add_node('tools', tool_node)

    graph_builder.add_edge(START, 'get_response')
    graph_builder.add_conditional_edges('get_response', tools_condition)
    graph_builder.add_edge('tools', 'get_response')

    return graph_builder
