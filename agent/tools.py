import json
from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

EMPTY = 0


@tool
def get_legal_moves(board: Annotated[list[list[int]], InjectedState("board")]) -> str:
    """
    返回当前所有可落子的空位。

    返回：
    JSON 数组字符串，元素为 {"x": int, "y": int}
    """
    board_size = len(board)
    moves: list[dict[str, int]] = []
    for y in range(board_size):
        for x in range(board_size):
            if board[y][x] == EMPTY:
                moves.append({"x": x, "y": y})
    return json.dumps(moves, ensure_ascii=False)


@tool
def submit_move(x: int, y: int) -> str:
    """
    提交 AI 最终落子坐标。

    参数：
    x: 列坐标，须为 get_legal_moves 中的空位
    y: 行坐标，须为 get_legal_moves 中的空位

    返回：
    JSON 字符串 {"x": int, "y": int}
    """
    return json.dumps({"x": x, "y": y}, ensure_ascii=False)


GOMOKU_TOOLS = [get_legal_moves, submit_move]
