"""
BoardMixin — lógica de grid, colisão, travamento de peças e movimentação.
"""
from settings import *
from pieces import Piece


class BoardMixin:

    # --- COLISÃO ---

    def shape_cells(self, piece, dx=0, dy=0, rotation=None):
        cells = []
        matrix = piece.matrix if rotation is None else piece.rotations[rotation]
        for row_idx, row in enumerate(matrix):
            for col_idx, val in enumerate(row):
                if val == "X":
                    cells.append((piece.x + col_idx + dx, piece.y + row_idx + dy))
        return cells

    def valid_position(self, piece, dx=0, dy=0, rotation=None):
        for x, y in self.shape_cells(piece, dx, dy, rotation):
            if x < 0 or x >= COLS or y >= ROWS:
                return False
            if y >= 0 and self.grid[y][x] is not None:
                return False
        return True

    # --- TRAVAMENTO / LINHAS ---

    def lock_piece(self):
        for x, y in self.shape_cells(self.current_piece):
            if y < 0:
                self.game_over = True
                self.state = "game_over"
                return
            self.grid[y][x] = {
                "type": "piece",
                "shape_key": self.current_piece.shape_key,
                "pulse": 0.0,
            }

        cleared = self.clear_lines()
        if cleared > 0:
            self.lines += cleared
            self.score += LINE_CLEAR_POINTS.get(cleared, 800) * self.level
            self.level = (self.lines // LINES_PER_LEVEL) + 1
            if self.mode == MODE_CORRIDA:
                self.refresh_obstacle_cells()

        self.current_piece = self.next_piece
        self.next_piece = self.generate_piece()
        self.current_piece.x = 3
        self.current_piece.y = 0

        if not self.valid_position(self.current_piece):
            self.game_over = True
            self.state = "game_over"

        self.lock_timer = 0.0

    def clear_lines(self):
        new_grid = [row for row in self.grid if not all(cell is not None for cell in row)]
        cleared = ROWS - len(new_grid)
        while len(new_grid) < ROWS:
            new_grid.insert(0, [None for _ in range(COLS)])
        self.grid = new_grid
        return cleared

    # --- GHOST ---

    def get_ghost_y(self):
        ghost = Piece(
            self.current_piece.shape_key,
            self.current_piece.gravity_type,
            self.current_piece.position_locked,
        )
        ghost.rotation = self.current_piece.rotation
        ghost.x = self.current_piece.x
        ghost.y = self.current_piece.y
        while self.valid_position(ghost, dy=1):
            ghost.y += 1
        return ghost.y

    # --- MOVIMENTAÇÃO ---

    def move_piece(self, dx):
        if self.current_piece.position_locked and self.current_piece.touching_ground:
            return
        if self.valid_position(self.current_piece, dx=dx):
            self.current_piece.x += dx

    def rotate_piece(self, direction):
        old_rotation = self.current_piece.rotation
        new_rotation = (
            (old_rotation + 1) % len(self.current_piece.rotations)
            if direction == "cw"
            else (old_rotation - 1) % len(self.current_piece.rotations)
        )
        for offset in [0, -1, 1, -2, 2]:
            if self.valid_position(self.current_piece, dx=offset, rotation=new_rotation):
                self.current_piece.rotation = new_rotation
                self.current_piece.x += offset
                return

    def hard_drop(self):
        distance = 0
        while self.valid_position(self.current_piece, dy=1):
            self.current_piece.y += 1
            distance += 1
        self.score += distance * HARD_DROP_POINTS_PER_CELL
        self.current_piece.touching_ground = True
        self.lock_piece()
