import random
import unittest

import reversi as rv


def board_from(rows, fill=rv.EMPTY):
    """Build a board from 8 strings of 8 chars each, row 0 = rank 8."""
    cells = []
    for row in rows:
        assert len(row) == 8, row
        cells.extend(row)
    return tuple(cells)


def empty_board():
    return tuple([rv.EMPTY] * 64)


class TestBoardBasics(unittest.TestCase):
    def test_initial_setup(self):
        board = rv.initial_board()
        self.assertEqual(len(board), 64)
        self.assertEqual(rv.score(board), (2, 2))
        self.assertEqual(board[27], rv.BLACK)   # d5
        self.assertEqual(board[28], rv.WHITE)   # e5
        self.assertEqual(board[35], rv.WHITE)   # d4
        self.assertEqual(board[36], rv.BLACK)   # e4
        self.assertFalse(rv.game_over(board))

    def test_initial_legal_moves_are_the_classic_four(self):
        moves = rv.legal_moves(rv.initial_board(), rv.BLACK)
        self.assertEqual(sorted(moves), [20, 29, 34, 43])
        self.assertEqual({rv.square_name(i) for i in moves}, {"c4", "f5", "d3", "e6"})
        for idx, flips in moves.items():
            self.assertEqual(len(flips), 1, rv.square_name(idx))
        white_moves = rv.legal_moves(rv.initial_board(), rv.WHITE)
        self.assertEqual(len(white_moves), 4)
        for idx in white_moves:
            self.assertEqual(rv.initial_board()[idx], rv.EMPTY)

    def test_apply_move_flips_the_single_disc(self):
        board = rv.apply_move(rv.initial_board(), rv.BLACK, rv.parse_move("d3"))
        self.assertEqual(board[rv.parse_move("d3")], rv.BLACK)
        self.assertEqual(board[rv.parse_move("d4")], rv.BLACK)
        self.assertEqual(rv.score(board), (4, 1))

    def test_illegal_move_raises(self):
        board = rv.initial_board()
        with self.assertRaises(ValueError):
            rv.apply_move(board, rv.BLACK, 0)          # corner, nothing to flip
        with self.assertRaises(ValueError):
            rv.apply_move(board, rv.BLACK, 27)         # occupied square
        self.assertEqual(rv.flips_for(board, rv.BLACK, 0), ())

    def test_flips_in_two_directions_at_once(self):
        board = empty_board()
        # Playing (2,2) should flip the white discs at (3,3) and (3,2).
        board = list(board)
        board[3 * 8 + 3] = rv.WHITE
        board[4 * 8 + 4] = rv.BLACK
        board[3 * 8 + 2] = rv.WHITE
        board[4 * 8 + 2] = rv.BLACK
        board = tuple(board)
        flips = rv.flips_for(board, rv.BLACK, 2 * 8 + 2)
        self.assertEqual(sorted(flips), [26, 27])
        played = rv.apply_move(board, rv.BLACK, 18)
        self.assertEqual(played[18], rv.BLACK)
        self.assertEqual(played[26], rv.BLACK)
        self.assertEqual(played[27], rv.BLACK)

    def test_no_flip_without_anchor(self):
        board = empty_board()
        board = list(board)
        board[1] = rv.WHITE  # b8, but nothing behind it
        board = tuple(board)
        self.assertEqual(rv.flips_for(board, rv.BLACK, 0), ())
        self.assertEqual(rv.legal_moves(board, rv.BLACK), {})

    def test_pass_position(self):
        board = empty_board()
        board = list(board)
        board[0] = rv.BLACK  # a8
        board[8] = rv.WHITE  # a7: black can flip it from a6, white cannot move
        board = tuple(board)
        self.assertEqual(rv.legal_moves(board, rv.WHITE), {})
        self.assertFalse(rv.game_over(board))  # black still has moves
        self.assertTrue(rv.legal_moves(board, rv.BLACK))

    def test_full_board_is_over(self):
        cells = [rv.BLACK if (i + i // 8) % 2 == 0 else rv.WHITE for i in range(64)]
        board = tuple(cells)
        self.assertTrue(rv.game_over(board))
        self.assertEqual(sum(rv.score(board)), 64)


class TestParsing(unittest.TestCase):
    def test_parse_move(self):
        self.assertEqual(rv.parse_move("d3"), 43)
        self.assertEqual(rv.parse_move("D3"), 43)
        self.assertEqual(rv.parse_move(" a8 "), 0)
        self.assertEqual(rv.parse_move("h1"), 63)
        for bad in ["", "z9", "d", "d33", "9d", "dd", " a9"]:
            self.assertIsNone(rv.parse_move(bad), bad)

    def test_square_name_roundtrip(self):
        for idx in range(64):
            self.assertEqual(rv.parse_move(rv.square_name(idx)), idx)

    def test_format_board_shape(self):
        lines = rv.format_board(rv.initial_board()).split("\n")
        self.assertEqual(len(lines), 10)
        for line in lines[1:9]:
            self.assertEqual(len(line), 18, repr(line))
            self.assertEqual(len(line.split()), 9)


class TestAI(unittest.TestCase):
    def test_takes_the_corner(self):
        board = empty_board()
        cells = list(board)
        # a8 empty, b8/c8 white, d8 black  -> playing a8 flips two discs.
        cells[1] = rv.WHITE
        cells[2] = rv.WHITE
        cells[3] = rv.BLACK
        # a7 (index 8) is legal too, but only flips one disc.
        cells[9] = rv.WHITE
        cells[10] = rv.BLACK
        board = tuple(cells)
        moves = rv.legal_moves(board, rv.BLACK)
        self.assertIn(0, moves)
        self.assertIn(8, moves)
        self.assertEqual(len(moves[0]), 2)
        self.assertEqual(rv.choose_move(board, rv.BLACK, 1), 0)
        self.assertEqual(rv.choose_move(board, rv.BLACK, 2), 0)

    def test_ai_is_deterministic(self):
        board = rv.initial_board()
        board = rv.apply_move(board, rv.BLACK, rv.parse_move("d3"))
        first = rv.choose_move(board, rv.WHITE, 2)
        for _ in range(3):
            self.assertEqual(rv.choose_move(board, rv.WHITE, 2), first)

    def test_ai_returns_legal_moves_throughout_games(self):
        rng = random.Random(7)
        checked = 0
        for _ in range(6):
            board, player = rv.initial_board(), rv.BLACK
            while not rv.game_over(board):
                moves = rv.legal_moves(board, player)
                if moves:
                    pick = rv.choose_move(board, player, 2)
                    self.assertIn(pick, moves)
                    checked += 1
                    # Random opponent keeps the positions varied.
                    idx = rng.choice(sorted(moves))
                    board = rv.apply_move(board, player, idx)
                player = rv.opponent(player)
        self.assertGreater(checked, 40)

    def test_depth_guard(self):
        with self.assertRaises(ValueError):
            rv.choose_move(rv.initial_board(), rv.BLACK, 0)


class TestPlayouts(unittest.TestCase):
    def test_discs_never_shrink(self):
        rng = random.Random(11)
        board, player = rv.initial_board(), rv.BLACK
        discs = sum(rv.score(board))
        for _ in range(60):
            moves = rv.legal_moves(board, player)
            if not moves:
                player = rv.opponent(player)
                continue
            idx = rng.choice(sorted(moves))
            board = rv.apply_move(board, player, idx)
            discs += 1  # a move places one disc; flips only change colour
            self.assertEqual(sum(rv.score(board)), discs)
            player = rv.opponent(player)
            if rv.game_over(board):
                break
        self.assertGreater(discs, 10)

    def test_random_games_all_terminate(self):
        rng = random.Random(3)
        finished = 0
        for _ in range(25):
            board, player, plies = rv.initial_board(), rv.BLACK, 0
            while not rv.game_over(board):
                moves = rv.legal_moves(board, player)
                if not moves:
                    player = rv.opponent(player)
                    continue
                idx = rng.choice(sorted(moves))
                board = rv.apply_move(board, player, idx)
                player = rv.opponent(player)
                plies += 1
                self.assertLess(plies, 61, "a game cannot exceed 60 moves")
            b, w = rv.score(board)
            self.assertEqual(b + w, 4 + plies)
            finished += 1
        self.assertEqual(finished, 25)

    def test_ai_vs_ai_games_finish(self):
        for depth in (1, 2):
            board, player, plies = rv.initial_board(), rv.BLACK, 0
            while not rv.game_over(board):
                moves = rv.legal_moves(board, player)
                if not moves:
                    player = rv.opponent(player)
                    continue
                board = rv.apply_move(board, player, rv.choose_move(board, player, depth))
                player = rv.opponent(player)
                plies += 1
                self.assertLess(plies, 61)
            self.assertEqual(sum(rv.score(board)), 4 + plies)
            self.assertGreater(plies, 20, "AI games should not collapse immediately")


if __name__ == "__main__":
    unittest.main()
