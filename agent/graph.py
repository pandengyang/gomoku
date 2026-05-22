import json
from typing import Literal

from langchain_core.messages import ToolMessage
from langchain_core.runnables import Runnable
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from .client import create_chat_model
from .prompts import build_initial_messages
from .state import AgentState
from .tools import GOMOKU_TOOLS

EMPTY = 0

_APP: Runnable | None = None
_MODEL_WITH_TOOLS: Runnable | None = None
tool_node = ToolNode(GOMOKU_TOOLS)


def _call_model(state: AgentState) -> dict:
    """
    调用绑定了工具的聊天模型，生成下一轮 AI 消息。

    参数：
    state: 当前图状态，含 messages 等字段

    返回：
    含新增 messages 的字典，供 LangGraph 合并进状态
    """
    global _MODEL_WITH_TOOLS
    if _MODEL_WITH_TOOLS is None:
        _MODEL_WITH_TOOLS = create_chat_model().bind_tools(GOMOKU_TOOLS)

    response = _MODEL_WITH_TOOLS.invoke(state["messages"])
    return {"messages": [response]}


def _extract_move(state: AgentState) -> dict:
    """
    从消息历史中解析 submit_move 工具提交的落子坐标。

    参数：
    state: 当前图状态，含 messages 等字段

    返回：
    含 move (x, y) 或 None，以及 error 说明的字典
    """
    for msg in reversed(state["messages"]):
        if isinstance(msg, ToolMessage) and msg.name == "submit_move":
            try:
                payload = json.loads(msg.content)
                return {
                    "move": (int(payload["x"]), int(payload["y"])),
                    "error": None,
                }
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                pass

    return {"move": None, "error": "未调用 submit_move，无法提取合法落子坐标"}


def _validate_move(state: AgentState) -> dict:
    """
    校验落子是否在棋盘范围内且对应格为空。

    参数：
    state: 当前图状态，含 board 与 move 字段

    返回：
    合法时清空 error；非法时将 move 置为 None 并写入 error
    """
    move = state.get("move")
    board = state["board"]
    board_size = len(board)

    if move is None:
        return {}

    x, y = move
    if 0 <= x < board_size and 0 <= y < board_size and board[y][x] == EMPTY:
        return {"error": None}

    return {
        "move": None,
        "error": f"坐标 ({x}, {y}) 非法或已被占用",
    }


def _route_after_extract(state: AgentState) -> Literal["validate", "__end__"]:
    """
    提取落子之后的路由：有坐标则进入校验，否则结束。

    参数：
    state: 当前图状态，读取 move 字段

    返回：
    "validate" 或 "__end__"
    """
    if state.get("move") is not None:
        return "validate"
    return "__end__"


def _compile_agent_graph() -> Runnable:
    """
    构建并编译 LangGraph 落子图（仅结构固定，盘面由 invoke 时的 state 提供）。

    返回：
    已编译、可 invoke 的 LangGraph 应用
    """
    graph = StateGraph(AgentState)
    graph.add_node("agent", _call_model)
    graph.add_node("tools", tool_node)
    graph.add_node("extract", _extract_move)
    graph.add_node("validate", _validate_move)

    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition, {"tools": "tools", "__end__": "extract"})
    graph.add_edge("tools", "agent")
    graph.add_conditional_edges("extract", _route_after_extract, {"validate": "validate", "__end__": END})
    graph.add_edge("validate", END)

    return graph.compile()


def run_agent_graph(board: list[list[int]], history: list[tuple[int, int, int]]) -> AgentState:
    """
    执行完整 Agent 图，得到落子结果或错误信息。

    参数：
    board: 棋盘状态，二维列表，每个元素为 0、1、2
    history: 历史落子 (棋子, x, y)

    返回：
    执行结束后的 AgentState，含 move、error、messages 等字段
    """
    global _APP
    if _APP is None:
        _APP = _compile_agent_graph()

    return _APP.invoke(
        {
            "board": board,
            "messages": build_initial_messages(board, history),
            "move": None,
            "error": None,
        }
    )
