from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    LangGraph 对局状态，在图节点之间传递与合并。

    字段：
    board: 棋盘快照，二维列表，每个元素为 0、1、2
    messages: 对话消息列表，由 add_messages 累加
    move: 解析得到的落子坐标 (x, y)，未成功时为 None
    error: 错误或校验失败说明，无错误时为 None
    """

    board: list[list[int]]
    messages: Annotated[list[BaseMessage], add_messages]
    move: tuple[int, int] | None
    error: str | None
