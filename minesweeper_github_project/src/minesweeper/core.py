"""Minesweeper game logic.

This module contains no GUI code, so it can be tested independently and reused by
other interfaces.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum
import random
from typing import Iterable


class GameStatus(str, Enum):
    """Current game state."""

    READY = "ready"
    PLAYING = "playing"
    WON = "won"
    LOST = "lost"


@dataclass(frozen=True, order=True)
class Position:
    """A coordinate on the minefield."""

    row: int
    col: int


@dataclass
class RevealResult:
    """Result returned after a reveal/chord operation."""

    revealed: set[Position] = field(default_factory=set)
    exploded: Position | None = None
    status: GameStatus = GameStatus.PLAYING


class MinesweeperBoard:
    """Core model for a Minesweeper board.

    Important rules implemented here:
    - Mines are placed lazily on the first reveal.
    - The first clicked cell and its neighbours are kept safe when possible.
    - Blank cells are expanded with breadth-first search.
    """

    def __init__(
        self,
        rows: int = 9,
        cols: int = 9,
        mine_count: int = 10,
        seed: int | None = None,
        first_click_safe: bool = True,
    ) -> None:
        if rows <= 0 or cols <= 0:
            raise ValueError("rows and cols must be positive")
        if mine_count <= 0:
            raise ValueError("mine_count must be positive")
        if mine_count >= rows * cols:
            raise ValueError("mine_count must be smaller than total cells")

        self.rows = rows
        self.cols = cols
        self.mine_count = mine_count
        self.first_click_safe = first_click_safe
        self._rng = random.Random(seed)

        self.mines: set[Position] = set()
        self.revealed: set[Position] = set()
        self.flagged: set[Position] = set()
        self.status = GameStatus.READY
        self._counts: dict[Position, int] = {}
        self._mines_placed = False

    @property
    def remaining_mines(self) -> int:
        """Mine counter shown to the player."""

        return max(0, self.mine_count - len(self.flagged))

    @property
    def safe_cell_count(self) -> int:
        return self.rows * self.cols - self.mine_count

    def in_bounds(self, pos: Position) -> bool:
        return 0 <= pos.row < self.rows and 0 <= pos.col < self.cols

    def neighbours(self, pos: Position) -> list[Position]:
        cells: list[Position] = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                next_pos = Position(pos.row + dr, pos.col + dc)
                if self.in_bounds(next_pos):
                    cells.append(next_pos)
        return cells

    def all_positions(self) -> Iterable[Position]:
        for row in range(self.rows):
            for col in range(self.cols):
                yield Position(row, col)

    def _safe_zone_for_first_click(self, first_pos: Position) -> set[Position]:
        safe_zone = {first_pos}
        if self.first_click_safe:
            safe_zone.update(self.neighbours(first_pos))
        return safe_zone

    def place_mines(self, first_pos: Position | None = None) -> None:
        """Place mines, optionally avoiding the first-click safe zone."""

        if self._mines_placed:
            return

        safe_zone: set[Position] = set()
        if first_pos is not None:
            if not self.in_bounds(first_pos):
                raise ValueError("first_pos is out of bounds")
            safe_zone = self._safe_zone_for_first_click(first_pos)

        candidates = [pos for pos in self.all_positions() if pos not in safe_zone]
        if len(candidates) < self.mine_count:
            # Tiny/custom boards may not have enough room to exclude neighbours.
            safe_zone = {first_pos} if first_pos is not None else set()
            candidates = [pos for pos in self.all_positions() if pos not in safe_zone]

        if len(candidates) < self.mine_count:
            raise ValueError("not enough cells to place mines with the selected rules")

        self.mines = set(self._rng.sample(candidates, self.mine_count))
        self._counts = {
            pos: sum(neighbour in self.mines for neighbour in self.neighbours(pos))
            for pos in self.all_positions()
            if pos not in self.mines
        }
        self._mines_placed = True

    def adjacent_mine_count(self, pos: Position) -> int:
        if not self._mines_placed:
            return 0
        if pos in self.mines:
            return -1
        return self._counts.get(pos, 0)

    def toggle_flag(self, row: int, col: int) -> bool:
        """Toggle a flag and return True if the cell is now flagged."""

        pos = Position(row, col)
        if not self.in_bounds(pos):
            raise ValueError("position is out of bounds")
        if self.status in {GameStatus.WON, GameStatus.LOST} or pos in self.revealed:
            return pos in self.flagged

        if pos in self.flagged:
            self.flagged.remove(pos)
            return False

        self.flagged.add(pos)
        if self.status == GameStatus.READY:
            self.status = GameStatus.PLAYING
        return True

    def reveal(self, row: int, col: int) -> RevealResult:
        """Reveal a cell. Blank areas are expanded automatically."""

        pos = Position(row, col)
        if not self.in_bounds(pos):
            raise ValueError("position is out of bounds")
        if self.status in {GameStatus.WON, GameStatus.LOST}:
            return RevealResult(status=self.status)
        if pos in self.flagged or pos in self.revealed:
            return RevealResult(status=self.status if self.status != GameStatus.READY else GameStatus.PLAYING)

        if not self._mines_placed:
            self.place_mines(first_pos=pos)

        self.status = GameStatus.PLAYING

        if pos in self.mines:
            self.revealed.add(pos)
            self.status = GameStatus.LOST
            return RevealResult(revealed={pos}, exploded=pos, status=self.status)

        newly_revealed = self._flood_reveal(pos)
        if len(self.revealed) == self.safe_cell_count:
            self.status = GameStatus.WON
            self.flagged.update(self.mines)

        return RevealResult(revealed=newly_revealed, status=self.status)

    def _flood_reveal(self, start: Position) -> set[Position]:
        newly_revealed: set[Position] = set()
        queue: deque[Position] = deque([start])

        while queue:
            pos = queue.popleft()
            if pos in self.revealed or pos in self.flagged or pos in self.mines:
                continue

            self.revealed.add(pos)
            newly_revealed.add(pos)

            if self.adjacent_mine_count(pos) == 0:
                for neighbour in self.neighbours(pos):
                    if neighbour not in self.revealed and neighbour not in self.flagged:
                        queue.append(neighbour)

        return newly_revealed

    def chord(self, row: int, col: int) -> RevealResult:
        """Reveal neighbours when a revealed number has enough adjacent flags."""

        pos = Position(row, col)
        if not self.in_bounds(pos):
            raise ValueError("position is out of bounds")
        if pos not in self.revealed or self.status in {GameStatus.WON, GameStatus.LOST}:
            return RevealResult(status=self.status)

        number = self.adjacent_mine_count(pos)
        if number <= 0:
            return RevealResult(status=self.status)

        neighbours = self.neighbours(pos)
        flag_count = sum(neighbour in self.flagged for neighbour in neighbours)
        if flag_count != number:
            return RevealResult(status=self.status)

        all_revealed: set[Position] = set()
        for neighbour in neighbours:
            if neighbour not in self.flagged and neighbour not in self.revealed:
                result = self.reveal(neighbour.row, neighbour.col)
                all_revealed.update(result.revealed)
                if result.status == GameStatus.LOST:
                    return RevealResult(revealed=all_revealed, exploded=result.exploded, status=self.status)

        return RevealResult(revealed=all_revealed, status=self.status)

    def reveal_all_mines(self) -> set[Position]:
        """Return all mine positions, forcing mine placement if needed."""

        if not self._mines_placed:
            self.place_mines()
        return set(self.mines)
