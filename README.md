# reversi-cli

Reversi (Othello) in the terminal — play against a minimax AI with alpha-beta
pruning and a classic positional weight table.

Written in plain Python 3. No dependencies.

## Play

```bash
python reversi.py                 # you are X (black, moves first), AI is O at depth 3
python reversi.py --depth 5       # stronger AI, noticeably slower
python reversi.py --color o       # you are O; the AI opens
python reversi.py --selfplay 5     # watch AI vs AI games and print the results
```

Squares are typed as file+rank, for example `d3` or `c4`. Extra commands:

- `hint` — suggest a move for the current position
- `quit` — stop early and show the final board

```
   a b c d e f g h
8  . . . . . . . .
7  . . . . . . . .
6  . . . . . . . .
5  . . . X O . . .
4  . . . O X . . .
3  . . . . . . . .
2  . . . . . . . .
1  . . . . . . . .
   a b c d e f g h
X 2 - 2 O   legal: c4, d3, e6, f5
```

## Rules implemented

- 8x8 board, black moves first, a move must flip at least one disc.
- Discs flip along all eight directions.
- A side with no legal move passes; the game ends when both sides must pass or
  the board is full.

## How the AI works

`choose_move()` runs alpha-beta negamax to the requested depth. The leaf
evaluation combines the positional weight table with the disc difference; the
weights reward corners and punish the squares diagonally next to them, which is
what keeps the AI from handing you a corner.

## Tests

```bash
python -m unittest test_reversi -v
```

18 tests cover move generation from the standard opening position, flipping in
multiple directions, illegal-move handling, pass positions, disc-count
conservation over random playouts, full-game termination, corner preference and
AI determinism.

## License

MIT
