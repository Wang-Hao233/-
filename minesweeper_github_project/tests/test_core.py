import unittest

from minesweeper.core import GameStatus, MinesweeperBoard, Position


class TestMinesweeperBoard(unittest.TestCase):
    def test_first_click_is_safe(self):
        board = MinesweeperBoard(rows=9, cols=9, mine_count=10, seed=1)
        result = board.reveal(4, 4)
        self.assertNotEqual(result.status, GameStatus.LOST)
        self.assertNotIn(Position(4, 4), board.mines)
        self.assertEqual(len(board.mines), 10)

    def test_toggle_flag(self):
        board = MinesweeperBoard(rows=9, cols=9, mine_count=10, seed=1)
        self.assertTrue(board.toggle_flag(0, 0))
        self.assertIn(Position(0, 0), board.flagged)
        self.assertFalse(board.toggle_flag(0, 0))
        self.assertNotIn(Position(0, 0), board.flagged)

    def test_revealed_cell_cannot_be_flagged(self):
        board = MinesweeperBoard(rows=9, cols=9, mine_count=10, seed=1)
        board.reveal(4, 4)
        self.assertFalse(board.toggle_flag(4, 4))
        self.assertNotIn(Position(4, 4), board.flagged)

    def test_loss_when_mine_revealed_after_placement(self):
        board = MinesweeperBoard(rows=9, cols=9, mine_count=10, seed=2)
        board.reveal(0, 0)
        mine = next(iter(board.mines))
        result = board.reveal(mine.row, mine.col)
        self.assertEqual(result.status, GameStatus.LOST)
        self.assertEqual(result.exploded, mine)

    def test_win_when_all_safe_cells_revealed(self):
        board = MinesweeperBoard(rows=3, cols=3, mine_count=1, seed=0, first_click_safe=False)
        board.place_mines(first_pos=Position(0, 0))
        for pos in list(board.all_positions()):
            if pos not in board.mines:
                result = board.reveal(pos.row, pos.col)
        self.assertEqual(result.status, GameStatus.WON)
        self.assertEqual(len(board.revealed), board.safe_cell_count)


if __name__ == "__main__":
    unittest.main()
