import threading
import tkinter as tk
from tkinter import messagebox

from agent import ask_agent_move

BOARD_SIZE = 15 # 棋盘路数
CELL_SIZE = 36 # 棋盘格子大小
PADDING = 30 # 棋盘边距，保证最外圈的棋子显示完整
STONE_RADIUS = 14 # 棋子半径
# 画布大小 = 棋盘边距 * 2 + 棋盘格子大小 * (棋盘路数 - 1)
# 棋盘路数 - 1 = 棋盘格子数
CANVAS_SIZE = PADDING * 2 + CELL_SIZE * (BOARD_SIZE - 1)

EMPTY = 0 # 空位
BLACK = 1 # 黑子 人类棋手
WHITE = 2 # 白子 Agent


class GomokuApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("五子棋 - Agent（白子） vs 人类棋手（黑子）")
        
        self.board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)] # 所有棋子：空位、黑子、白子
        self.history: list[tuple[int, int, int]] = [] # 历史落子 （棋子，x 坐标，y 坐标）
        self.current_piece = BLACK # 当前轮到谁下 黑棋人类棋手 白棋Agent
        self.game_over = False # 游戏是否结束
        self.ai_thinking = False # AI 是否在思考

        self.status_var = tk.StringVar(value="人类棋手回合（黑子）")

        self._build_ui()
        self._draw_board()

    def _build_ui(self) -> None:
        self.canvas = tk.Canvas(
            self.root,
            width=CANVAS_SIZE,
            height=CANVAS_SIZE,
            bg="#E8C78E",
            highlightthickness=1,
            highlightbackground="#8E6E4C",
        ) # 用于绘制棋盘的画布
        self.canvas.pack(padx=12, pady=(12, 6))
        self.canvas.bind("<Button-1>", self._on_canvas_click) # 绑定鼠标左键点击事件

        bottom = tk.Frame(self.root) # 底部栏 用于显示状态和重开一局按钮
        bottom.pack(fill=tk.X, padx=10, pady=(0, 10))

        status = tk.Label(bottom, textvariable=self.status_var, font=("Microsoft YaHei UI", 11)) # 轮到谁下棋
        status.pack(side=tk.LEFT)

        reset_btn = tk.Button(bottom, text="新开一局", command=self.reset_game, width=14)
        reset_btn.pack(side=tk.RIGHT)

        self.retry_btn = tk.Button(
            bottom,
            text="Agent 重试",
            command=self._on_agent_retry,
            width=14,
            state=tk.DISABLED,
        )
        self.retry_btn.pack(side=tk.RIGHT, padx=(0, 8))

    def _draw_board(self) -> None:
        self.canvas.delete("all") # 清空画布
        # (0, 0)    x 轴
        # --------------------------->
        # |
        # |
        # |
        # | y 轴
        # |
        # |
        # v
        for i in range(BOARD_SIZE): # 绘制所有竖线和横线
            x0 = PADDING + i * CELL_SIZE # 竖线顶端 x 坐标
            y0 = PADDING # 竖线顶端 y 坐标
            x1 = PADDING + i * CELL_SIZE # 竖线底端 x 坐标
            y1 = PADDING + (BOARD_SIZE - 1) * CELL_SIZE # 竖线底端 y 坐标
            self.canvas.create_line(x0, y0, x1, y1, fill="#333333") # 绘制竖线

            x0 = PADDING # 横线左端 x 坐标
            y0 = PADDING + i * CELL_SIZE # 横线左端 y 坐标
            x1 = PADDING + (BOARD_SIZE - 1) * CELL_SIZE # 横线右端 x 坐标
            y1 = PADDING + i * CELL_SIZE # 横线右端 y 坐标
            self.canvas.create_line(x0, y0, x1, y1, fill="#333333") # 绘制横线

        for y in range(BOARD_SIZE):  # 绘制所有棋子
            for x in range(BOARD_SIZE): # 绘制所有棋子
                piece = self.board[y][x] # 获取棋子
                if piece != EMPTY: # 如果棋子不为空，则绘制棋子
                    self._draw_stone(x, y, piece) # 绘制棋子

    def _draw_stone(self, x: int, y: int, piece: int) -> None:
        cx = PADDING + x * CELL_SIZE # 棋子中心 x 坐标
        cy = PADDING + y * CELL_SIZE # 棋子中心 y 坐标
        color = "#111111" if piece == BLACK else "#F5F5F5" # 棋子颜色
        outline = "#000000" if piece == BLACK else "#888888" # 棋子边框颜色
        self.canvas.create_oval( # 绘制椭圆
            cx - STONE_RADIUS, # 椭圆左上角 x 坐标
            cy - STONE_RADIUS, # 椭圆左上角 y 坐标
            cx + STONE_RADIUS, # 椭圆右下角 x 坐标
            cy + STONE_RADIUS, # 椭圆右下角 y 坐标
            fill=color, # 填充颜色
            outline=outline, # 边框颜色
            width=1, # 边框宽度
        ) # 绘制单个棋子

    def _pixel_to_grid(self, px: int, py: int) -> tuple[int, int] | None:
        x = round((px - PADDING) / CELL_SIZE)
        y = round((py - PADDING) / CELL_SIZE)
        if 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
            gx = PADDING + x * CELL_SIZE
            gy = PADDING + y * CELL_SIZE
            if abs(px - gx) <= CELL_SIZE // 2 and abs(py - gy) <= CELL_SIZE // 2:
                return x, y
        return None

    def _on_canvas_click(self, event: tk.Event) -> None:
        if self.game_over or self.ai_thinking or self.current_piece != BLACK: # 如果游戏结束或 AI 正在思考或当前轮到白棋，则不响应
            return

        pos = self._pixel_to_grid(event.x, event.y) # 将鼠标点击坐标转换为棋盘坐标
        if pos is None: # 如果转换失败，则不响应
            return
        x, y = pos # 获取棋盘坐标

        if not self.is_valid_move(x, y): # 如果坐标不在棋盘范围内，或者该位置不为空位，则不响应
            return

        self.place_piece(x, y, BLACK) # 落黑子
        if self._check_game_finished(x, y, BLACK): # 检查游戏是否结束
            return

        self.current_piece = WHITE
        self.ai_thinking = True
        self.status_var.set("Agent 回合，思考中...")
        self._update_retry_button_state()
        self._request_ai_move()

    def _on_agent_retry(self) -> None:
        if self.game_over or self.ai_thinking or self.current_piece != WHITE:
            return
        self.ai_thinking = True
        self.status_var.set("Agent 回合，思考中...")
        self._update_retry_button_state()
        self._request_ai_move()

    def _update_retry_button_state(self) -> None:
        if self.game_over or self.current_piece != WHITE or self.ai_thinking:
            self.retry_btn.config(state=tk.DISABLED)
        else:
            self.retry_btn.config(state=tk.NORMAL)

    def _friendly_agent_error(self, raw_error: str) -> str:
        lower = raw_error.lower()
        if "in the thinking mode must be passed back to the api" in lower:
            return "Agent 调用失败：检测到 thinking 协议错误，请确认已关闭思考模式并重试。"
        if "api_key" in lower or "api key" in lower:
            return "Agent 调用失败：请检查 agent/client.py 中 API_KEY 配置。"
        if len(raw_error) > 80:
            raw_error = f"{raw_error[:80]}..."
        return f"Agent 下棋失败：{raw_error}"

    def _request_ai_move(self) -> None:
        board_snapshot = [row[:] for row in self.board]
        history_snapshot = self.history[:]

        def worker() -> None:
            move: tuple[int, int] | None = None
            error_msg: str | None = None
            try:
                move = ask_agent_move(board_snapshot, history_snapshot)
            except Exception as exc:
                error_msg = self._friendly_agent_error(str(exc))

            self.root.after(0, lambda: self._apply_ai_move(move, error_msg))

        threading.Thread(target=worker, daemon=True).start()

    def _apply_ai_move(self, move: tuple[int, int] | None, error_msg: str | None = None) -> None:
        if self.game_over:
            self.ai_thinking = False
            self._update_retry_button_state()
            return

        self.ai_thinking = False

        if move is None:
            self.status_var.set(error_msg or "Agent 下棋失败")
            self._update_retry_button_state()
            return

        x, y = move
        if not self.is_valid_move(x, y):
            self.status_var.set(f"Agent 返回无效坐标 ({x}, {y})")
            self._update_retry_button_state()
            return

        self.place_piece(x, y, WHITE)

        if self._check_game_finished(x, y, WHITE):
            self._update_retry_button_state()
            return

        self.current_piece = BLACK
        self.status_var.set("人类棋手回合（黑子）")
        self._update_retry_button_state()

    def is_valid_move(self, x: int, y: int) -> bool:
        # 判断坐标是否在棋盘范围内，并且该位置为空位
        return 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and self.board[y][x] == EMPTY

    def place_piece(self, x: int, y: int, piece: int) -> None:
        self.board[y][x] = piece # 将棋子放置在指定位置
        self.history.append((piece, x, y)) # 将棋子放入历史记录
        self._draw_board()

    def check_winner(self, x: int, y: int, piece: int) -> bool:
        """判断刚落在 (x, y) 的一方是否已达成五子连珠。

        原理：只需检查包含该子的四条直线——水平、竖直、两条斜向。对每条线，
        以落子为起点，沿正反两个方向（例如 (dx,dy) 与 (-dx,-dy)）累计连续同色
        棋子数，再加上当前这一子；若任一线方向上总数 ≥ 5，则获胜。

        用四个基向量 (1,0)、(0,1)、(1,1)、(1,-1) 即可覆盖全部直线，避免重复判断。

        (dx, dy) 表示沿着 x 轴和 y 轴的移动步长。dx 和 dy 的正负号决定了移动的方向。
        (1, 0) 水平向右
        (0, 1) 垂直向下
        (1, 1) 斜向右下
        (1, -1) 斜向右上
        (-dx, -dy) 表示沿着 x 轴和 y 轴的反方向移动。
        (-1, 0) 水平向左
        (0, -1) 垂直向上
        (-1, -1) 斜向左上
        (-1, 1) 斜向左下
        """

        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for dx, dy in directions:
            count = 1
            count += self._count_one_direction(x, y, piece, dx, dy)
            count += self._count_one_direction(x, y, piece, -dx, -dy)
            if count >= 5:
                return True
        return False

    def _count_one_direction(self, x: int, y: int, piece: int, dx: int, dy: int) -> int:
        count = 0
        nx, ny = x + dx, y + dy # 沿着 dx 和 dy 方向移动
        while 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and self.board[ny][nx] == piece: # 检查是否越界，是否为同色棋子
            count += 1
            nx += dx
            ny += dy
        return count

    def is_draw(self) -> bool:
        for row in self.board: # 检查棋盘是否还有空位
            if EMPTY in row:
                return False
        return True

    def _check_game_finished(self, x: int, y: int, piece: int) -> bool:
        if self.check_winner(x, y, piece): # 检查是否有人获胜
            self.game_over = True
            winner_text = "人类棋手（黑子）" if piece == BLACK else "Agent（白子）"
            self.status_var.set(f"{winner_text} 获胜")
            messagebox.showinfo("对局结束", f"{winner_text} 获胜！")
            return True

        if self.is_draw(): # 检查是否平局
            self.game_over = True
            self.status_var.set("平局")
            messagebox.showinfo("对局结束", "平局！")
            return True

        return False

    def reset_game(self) -> None:
        self.board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.history.clear()
        self.current_piece = BLACK
        self.game_over = False
        self.ai_thinking = False
        self.status_var.set("人类棋手回合（黑子）")
        self._update_retry_button_state()
        self._draw_board()


def main() -> None:
    root = tk.Tk()
    app = GomokuApp(root)
    app._draw_board()
    root.resizable(False, False)
    root.mainloop()


if __name__ == "__main__":
    main()
