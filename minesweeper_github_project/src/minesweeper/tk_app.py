"""Tkinter user interface for the Minesweeper game."""

from __future__ import annotations

import time
import tkinter as tk
from tkinter import messagebox, ttk

from .core import GameStatus, MinesweeperBoard, Position


DIFFICULTIES: dict[str, tuple[int, int, int]] = {
    "初级 9×9 / 10雷": (9, 9, 10),
    "中级 16×16 / 40雷": (16, 16, 40),
    "高级 16×30 / 99雷": (16, 30, 99),
}

NUMBER_COLORS = {
    1: "#1976D2",
    2: "#388E3C",
    3: "#D32F2F",
    4: "#303F9F",
    5: "#7B1FA2",
    6: "#00838F",
    7: "#212121",
    8: "#616161",
}


class MinesweeperApp:
    """Desktop Minesweeper application."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("扫雷游戏")
        self.root.resizable(False, False)

        self.difficulty_var = tk.StringVar(value="初级 9×9 / 10雷")
        self.board = self._new_board()
        self.buttons: dict[Position, tk.Button] = {}
        self.start_time: float | None = None
        self.timer_job: str | None = None

        self._build_menu()
        self._build_header()
        self._build_board_frame()
        self._bind_shortcuts()
        self.new_game()

    def _new_board(self) -> MinesweeperBoard:
        rows, cols, mines = DIFFICULTIES[self.difficulty_var.get()]
        return MinesweeperBoard(rows=rows, cols=cols, mine_count=mines, first_click_safe=True)

    def _build_menu(self) -> None:
        menu_bar = tk.Menu(self.root)
        game_menu = tk.Menu(menu_bar, tearoff=False)
        game_menu.add_command(label="新游戏", accelerator="R", command=self.new_game)
        game_menu.add_separator()
        game_menu.add_command(label="退出", command=self.root.destroy)
        menu_bar.add_cascade(label="游戏", menu=game_menu)

        help_menu = tk.Menu(menu_bar, tearoff=False)
        help_menu.add_command(label="玩法说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)
        menu_bar.add_cascade(label="帮助", menu=help_menu)
        self.root.config(menu=menu_bar)

    def _build_header(self) -> None:
        self.header = ttk.Frame(self.root, padding=(8, 8, 8, 4))
        self.header.pack(fill=tk.X)

        ttk.Label(self.header, text="难度：").pack(side=tk.LEFT)
        self.difficulty_box = ttk.Combobox(
            self.header,
            textvariable=self.difficulty_var,
            values=list(DIFFICULTIES.keys()),
            state="readonly",
            width=18,
        )
        self.difficulty_box.pack(side=tk.LEFT, padx=(2, 10))
        self.difficulty_box.bind("<<ComboboxSelected>>", lambda _event: self.new_game())

        self.mine_label = ttk.Label(self.header, text="💣 000")
        self.mine_label.pack(side=tk.LEFT, padx=8)

        self.time_label = ttk.Label(self.header, text="⏱ 000")
        self.time_label.pack(side=tk.LEFT, padx=8)

        self.status_label = ttk.Label(self.header, text="准备开始")
        self.status_label.pack(side=tk.LEFT, padx=8)

        ttk.Button(self.header, text="重新开始", command=self.new_game).pack(side=tk.RIGHT)

    def _build_board_frame(self) -> None:
        self.board_frame = ttk.Frame(self.root, padding=(8, 4, 8, 8))
        self.board_frame.pack()

    def _bind_shortcuts(self) -> None:
        self.root.bind("r", lambda _event: self.new_game())
        self.root.bind("R", lambda _event: self.new_game())

    def new_game(self) -> None:
        self._stop_timer()
        self.start_time = None
        self.board = self._new_board()
        self.buttons.clear()

        for child in self.board_frame.winfo_children():
            child.destroy()

        for row in range(self.board.rows):
            for col in range(self.board.cols):
                pos = Position(row, col)
                button = tk.Button(
                    self.board_frame,
                    width=2,
                    height=1,
                    font=("Microsoft YaHei", 11, "bold"),
                    relief=tk.RAISED,
                    bg="#D9D9D9",
                    activebackground="#F5F5F5",
                    text="",
                    command=lambda p=pos: self.on_left_click(p),
                )
                button.grid(row=row, column=col, padx=1, pady=1)
                button.bind("<Button-3>", lambda _event, p=pos: self.on_right_click(p))
                button.bind("<Double-Button-1>", lambda _event, p=pos: self.on_chord(p))
                self.buttons[pos] = button

        self._refresh_header()
        self.status_label.config(text="准备开始")

    def _start_timer_if_needed(self) -> None:
        if self.start_time is None:
            self.start_time = time.time()
            self._tick_timer()

    def _tick_timer(self) -> None:
        if self.start_time is None or self.board.status in {GameStatus.WON, GameStatus.LOST}:
            return
        seconds = min(999, int(time.time() - self.start_time))
        self.time_label.config(text=f"⏱ {seconds:03d}")
        self.timer_job = self.root.after(1000, self._tick_timer)

    def _stop_timer(self) -> None:
        if self.timer_job is not None:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None

    def on_left_click(self, pos: Position) -> None:
        if self.board.status in {GameStatus.WON, GameStatus.LOST}:
            return
        self._start_timer_if_needed()
        result = self.board.reveal(pos.row, pos.col)
        self._refresh_cells(result.revealed)
        if result.status == GameStatus.LOST:
            self._handle_loss(result.exploded)
        elif result.status == GameStatus.WON:
            self._handle_win()
        else:
            self.status_label.config(text="游戏进行中")
        self._refresh_header()

    def on_right_click(self, pos: Position) -> str:
        if self.board.status in {GameStatus.WON, GameStatus.LOST}:
            return "break"
        flagged = self.board.toggle_flag(pos.row, pos.col)
        button = self.buttons[pos]
        button.config(text="🚩" if flagged else "", fg="#D32F2F", bg="#D9D9D9")
        self.status_label.config(text="游戏进行中")
        self._refresh_header()
        return "break"

    def on_chord(self, pos: Position) -> str:
        if self.board.status in {GameStatus.WON, GameStatus.LOST}:
            return "break"
        result = self.board.chord(pos.row, pos.col)
        self._refresh_cells(result.revealed)
        if result.status == GameStatus.LOST:
            self._handle_loss(result.exploded)
        elif result.status == GameStatus.WON:
            self._handle_win()
        self._refresh_header()
        return "break"

    def _refresh_cells(self, cells: set[Position]) -> None:
        for pos in cells:
            if pos not in self.buttons:
                continue
            button = self.buttons[pos]
            number = self.board.adjacent_mine_count(pos)
            button.config(relief=tk.SUNKEN, bg="#F4F4F4", state=tk.DISABLED, disabledforeground=NUMBER_COLORS.get(number, "#000000"))
            if number > 0:
                button.config(text=str(number), fg=NUMBER_COLORS.get(number, "#000000"))
            else:
                button.config(text="")

    def _handle_loss(self, exploded: Position | None) -> None:
        self._stop_timer()
        for mine in self.board.reveal_all_mines():
            button = self.buttons[mine]
            button.config(text="💣", bg="#D32F2F", fg="white", state=tk.NORMAL)
        if exploded is not None and exploded in self.buttons:
            self.buttons[exploded].config(text="💥", bg="#B71C1C", fg="white")
        self._disable_all_buttons()
        self.status_label.config(text="失败")
        messagebox.showerror("游戏结束", "很遗憾，你踩到地雷了！")

    def _handle_win(self) -> None:
        self._stop_timer()
        for mine in self.board.mines:
            self.buttons[mine].config(text="🚩", bg="#D9D9D9", fg="#D32F2F")
        self._disable_all_buttons()
        self.status_label.config(text="胜利")
        messagebox.showinfo("恭喜", "你已经成功排除所有地雷！")

    def _disable_all_buttons(self) -> None:
        for button in self.buttons.values():
            button.config(state=tk.DISABLED)

    def _refresh_header(self) -> None:
        self.mine_label.config(text=f"💣 {self.board.remaining_mines:03d}")
        if self.start_time is None:
            self.time_label.config(text="⏱ 000")

    def show_help(self) -> None:
        messagebox.showinfo(
            "玩法说明",
            "左键：翻开格子\n右键：插旗/取消插旗\n双击已翻开的数字：当周围旗数等于数字时，自动翻开其余相邻格子\nR：重新开始\n\n第一次点击不会踩雷。",
        )

    def show_about(self) -> None:
        messagebox.showinfo(
            "关于",
            "扫雷游戏\n课程实践项目示例\n核心算法：随机布雷、邻域统计、BFS 空白展开、胜负判定。",
        )


def main() -> None:
    root = tk.Tk()
    MinesweeperApp(root)
    root.mainloop()
