from langchain_core.messages import HumanMessage, SystemMessage


SYSTEM_PROMPT = """
你是五子棋 AI（白棋），棋盘为 15×15。

你必须通过工具完成落子：
1. 调用 get_legal_moves 查看当前所有空位；
2. 从中选择一步，调用 submit_move(x, y) 提交最终坐标。

不要编造坐标；若无法确定，再次调用 get_legal_moves。
禁止在工具之外输出 Markdown 或长篇解释。
""".strip()


def _serialize_board(board: list[list[int]]) -> list[dict[str, int]]:
    """
    将棋盘上的非空格子序列化为提示词用的占用列表。

    参数：
    board: 棋盘状态，二维列表，每个元素为 0、1、2

    返回：
    元素为 {"x", "y", "piece"} 的字典列表
    """
    occupied: list[dict[str, int]] = []
    for y, row in enumerate(board):
        for x, value in enumerate(row):
            if value != 0:
                occupied.append({"x": x, "y": y, "piece": value})
    return occupied


def build_initial_messages(board: list[list[int]], history: list[tuple[int, int, int]]):
    """
    构建 Agent 图首轮所需的系统消息与人类提示。

    参数：
    board: 棋盘状态，二维列表，每个元素为 0、1、2
    history: 历史落子 (棋子, x, y)

    返回：
    [SystemMessage, HumanMessage] 列表，供 LangGraph 初始 state 使用
    """
    occupied = _serialize_board(board)
    content = (
        "请为白棋选择下一步。\n"
        "棋子: 0=空, 1=黑(人类), 2=白(AI)\n"
        f"已落子: {occupied}\n"
        f"最近历史: {history[-6:]}\n"
        "请先 get_legal_moves，再 submit_move。"
    )
    return [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=content)]
