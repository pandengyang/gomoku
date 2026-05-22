from .graph import run_agent_graph


def ask_agent_move(board: list[list[int]], history: list[tuple[int, int, int]]) -> tuple[int, int]:
    """
    通过 LangGraph（State + Tool）获取 AI 下一步落子坐标。

    参数：
    board: 棋盘状态，二维列表，每个元素为 0、1、2
    history: 历史落子 (棋子, x, y)

    返回：
    (x, y) 落子坐标
    """
    result = run_agent_graph(board, history)
    move = result.get("move")
    if move is not None:
        return move
    raise ValueError(result.get("error") or "Agent 未能产生合法落子")
