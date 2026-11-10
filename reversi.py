#!/usr/bin/env python3
"""Reversi (Othello) for the terminal: play against a minimax AI.

Board is a flat tuple of 64 characters in row-major order, row 0 = rank 8,
column 0 = file 'a'.  'X' is black (moves first), 'O' is white, '.' is empty.

Usage:
    python reversi.py                # you are X, AI is O at depth 3
    python reversi.py --depth 5      # stronger (slower) AI
    python reversi.py --color o      # play white, AI moves first
    python reversi.py --selfplay 5   # watch AI vs AI games
"""

from __future__ import annotations

import argparse
import sys

BOARD_SIZE = 8
EMPTY = "."
BLACK = "X"
WHITE = "O"

DIRECTIONS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1), (0, 1),
    (1, -1), (1, 0), (1, 1),
)

# Classic positional weights: corners are gold, squares next to them are traps.
WEIGHTS = (
    100, -20, 10, 5, 5, 10, -20, 100,
    -20, -50, -2, -2, -2, -2, -50, -20,
    10, -2, 1, 1, 1, 1, -2, 10,
    5, -2, 1, 0, 0, 1, -2, 5,
    5, -2, 1, 0, 0, 1, -2, 5,
    10, -2, 1, 1, 1, 1, -2, 10,
    -20, -50, -2, -2, -2, -2, -50, -20,
    100, -20, 10, 5, 5, 10, -20, 100,
)

INF = 10 ** 9


def opponent(player: str) -> str:
    """Return the other colour."""
    if player == BLACK:
        return WHITE
    if player == WHITE:
        return BLACK
    raise ValueError(f"unknown player: {player!r}")


def initial_board() -> tuple[str, ...]:
    """Standard 8x8 opening position, black to move."""
    board = [EMPTY] * 64
    board[27] = BLACK  # d5
    board[28] = WHITE  # e5
    board[35] = WHITE  # d4
    board[36] = BLACK  # e4
    return tuple(board)


def on_board(row: int, col: int) -> bool:
    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE


def flips_for(board: tuple[str, ...], player: str, idx: int) -> tuple[int, ...]:
    """Discs that would flip if `player` plays at `idx` (empty tuple = illegal)."""
    if board[idx] != EMPTY:
        return ()
    other = opponent(player)
    row, col = divmod(idx, BOARD_SIZE)
    flipped: list[int] = []
    for dr, dc in DIRECTIONS:
        r, c = row + dr, col + dc
        line: list[int] = []
        while on_board(r, c) and board[r * BOARD_SIZE + c] == other:
            line.append(r * BOARD_SIZE + c)
            r += dr
            c += dc
        if line and on_board(r, c) and board[r * BOARD_SIZE + c] == player:
            flipped.extend(line)
    return tuple(flipped)


def legal_moves(board: tuple[str, ...], player: str) -> dict[int, tuple[int, ...]]:
    """Map every legal square index to the discs it would flip."""
    return {
        idx: flips
        for idx in range(64)
        if board[idx] == EMPTY
        for flips in (flips_for(board, player, idx),)
        if flips
    }


def apply_move(board: tuple[str, ...], player: str, idx: int) -> tuple[str, ...]:
    """Return the board after `player` plays at `idx`; ValueError if illegal."""
    flips = flips_for(board, player, idx)
    if not flips:
        raise ValueError(f"illegal move for {player} at {square_name(idx)}")
    cells = list(board)
    cells[idx] = player
    for pos in flips:
        cells[pos] = player
    return tuple(cells)


def score(board: tuple[str, ...]) -> tuple[int, int]:
    """(black discs, white discs)."""
    return board.count(BLACK), board.count(WHITE)


def game_over(board: tuple[str, ...]) -> bool:
    """True when neither side has a legal move."""
    return not legal_moves(board, BLACK) and not legal_moves(board, WHITE)


def evaluate(board: tuple[str, ...], player: str) -> int:
    """Static score from `player`'s point of view (positive is good)."""
    other = opponent(player)
    value = 0
    for idx in range(64):
        cell = board[idx]
        if cell == player:
            value += WEIGHTS[idx]
        elif cell == other:
            value -= WEIGHTS[idx]
    mine, theirs = (score(board) if player == BLACK else reversed(score(board)))
    return value + (mine - theirs)


def _negamax(board, player, depth, alpha, beta):
    """Alpha-beta negamax. Returns (value, move) for `player` to move."""
    moves = legal_moves(board, player)
    if depth <= 0:
        return evaluate(board, player), None
    if not moves:
        other = opponent(player)
        if not legal_moves(board, other):
            b, w = score(board)
            diff = (b - w) if player == BLACK else (w - b)
            return diff * 1000, None
        value, _ = _negamax(board, other, depth - 1, -beta, -alpha)
        return -value, None

    best_value, best_move = -INF, None
    for idx in sorted(moves):
        child = apply_move(board, player, idx)
        value, _ = _negamax(child, opponent(player), depth - 1, -beta, -alpha)
        value = -value
        if value > best_value:
            best_value, best_move = value, idx
        if best_value > alpha:
            alpha = best_value
        if alpha >= beta:
            break
    return best_value, best_move


def choose_move(board: tuple[str, ...], player: str, depth: int = 3) -> int | None:
    """Best move for `player`, or None when the side must pass."""
    if depth < 1:
        raise ValueError("depth must be >= 1")
    _, move = _negamax(board, player, depth, -INF, INF)
    return move


def square_name(idx: int) -> str:
    """0 -> 'a8', 63 -> 'h1'."""
    row, col = divmod(idx, BOARD_SIZE)
    return f"{chr(ord('a') + col)}{BOARD_SIZE - row}"


def parse_move(text: str) -> int | None:
    """'d3' / 'D3' -> index, anything malformed -> None."""
    text = text.strip().lower()
    if len(text) != 2:
        return None
    col_char, rank_char = text[0], text[1]
    if not ("a" <= col_char <= "h") or not ("1" <= rank_char <= "8"):
        return None
    col = ord(col_char) - ord("a")
    row = BOARD_SIZE - int(rank_char)
    return row * BOARD_SIZE + col


def format_board(board: tuple[str, ...]) -> str:
    """Human-readable board with file/rank labels."""
    lines = ["   a b c d e f g h"]
    for row in range(BOARD_SIZE):
        cells = board[row * BOARD_SIZE:(row + 1) * BOARD_SIZE]
        lines.append(f"{BOARD_SIZE - row}  " + " ".join(cells))
    lines.append("   a b c d e f g h")
    return "\n".join(lines)


def emit(text: str = "") -> None:
    """Write UTF-8 straight to the binary stream (byte-exact on Windows)."""
    sys.stdout.buffer.write((text + "\n").encode("utf-8"))
    sys.stdout.buffer.flush()


def play_game(board, player, depth, human, emit_fn=emit):
    """Run a full game; `human` is the colour controlled by stdin."""
    passes = 0
    while not game_over(board):
        moves = legal_moves(board, player)
        if not moves:
            emit_fn(f"{player} has no legal move, passing.")
            passes += 1
            if passes >= 2:
                break
            player = opponent(player)
            continue
        passes = 0

        if player == human:
            emit_fn(format_board(board))
            b, w = score(board)
            emit_fn(f"X {b} - {w} O   legal: " + ", ".join(square_name(i) for i in sorted(moves)))
            while True:
                try:
                    raw = input(f"your move ({player}): ")
                except EOFError:
                    return board
                command = raw.strip().lower()
                if command in ("q", "quit", "exit"):
                    return board
                if command == "hint":
                    hint = choose_move(board, player, min(depth, 2))
                    emit_fn(f"try {square_name(hint)}")
                    continue
                idx = parse_move(command)
                if idx is not None and idx in moves:
                    break
                emit_fn("not a legal move, try again (e.g. d3) or 'hint'.")
        else:
            idx = choose_move(board, player, depth)
            if idx is None:
                idx = min(moves)
            emit_fn(f"{player} plays {square_name(idx)}")
        board = apply_move(board, player, idx)
        player = opponent(player)
    return board


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Reversi (Othello) in the terminal.")
    parser.add_argument("--depth", type=int, default=3, help="AI search depth (default 3)")
    parser.add_argument("--color", choices=["x", "o"], default="x", help="your colour (default x)")
    parser.add_argument("--selfplay", type=int, default=0, metavar="N",
                        help="play N AI-vs-AI games instead of a human game")
    args = parser.parse_args(argv)

    if args.depth < 1:
        parser.error("--depth must be >= 1")

    if args.selfplay > 0:
        tally = {BLACK: 0, WHITE: 0, "draw": 0}
        for _ in range(args.selfplay):
            board, player = initial_board(), BLACK
            while not game_over(board):
                moves = legal_moves(board, player)
                if not moves:
                    player = opponent(player)
                    continue
                board = apply_move(board, player, choose_move(board, player, max(1, args.depth - 1)))
                player = opponent(player)
            b, w = score(board)
            tally["draw" if b == w else (BLACK if b > w else WHITE)] += 1
            emit(f"game {_ + 1}: X {b} - {w} O")
        emit(f"X wins {tally[BLACK]}, O wins {tally[WHITE]}, draws {tally['draw']}")
        return 0

    human = BLACK if args.color == "x" else WHITE
    board, player = initial_board(), BLACK
    emit("Reversi. Type a square like d3, 'hint' for a suggestion, 'quit' to stop.")
    board = play_game(board, player, args.depth, human)
    emit(format_board(board))
    b, w = score(board)
    if game_over(board):
        verdict = "draw" if b == w else (f"{BLACK} wins" if b > w else f"{WHITE} wins")
        emit(f"final: X {b} - {w} O  ({verdict})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
