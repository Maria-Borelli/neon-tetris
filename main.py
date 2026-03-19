import os
import random
import sys
import pygame

from settings import *
from pieces import Piece, random_shape_key

pygame.init()


class TetrisGame:

    def clear_barrier(self):
        for x, y in self.obstacle_cells:
            if 0 <= y < ROWS and 0 <= x < COLS:
                if self.grid[y][x] is not None and self.grid[y][x]["type"] == "obstacle":
                    self.grid[y][x] = None
        self.obstacle_cells = []

    def refresh_obstacle_cells(self):
        """Ressincroniza obstacle_cells com o estado real do grid (ex: após clear_lines)."""
        self.obstacle_cells = [
            (x, y)
            for y in range(ROWS)
            for x in range(COLS)
            if self.grid[y][x] is not None and self.grid[y][x]["type"] == "obstacle"
        ]
                
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()

        self.block_images = self.load_block_images()

        self.title_colors = [
            (0, 240, 255),   # I
            (0, 80, 255),    # J
            (255, 140, 0),   # L
            (255, 240, 0),   # O
            (0, 255, 80),    # S
            (180, 0, 255),   # T
            (255, 40, 40),   # Z
        ]
        self.title_timer = 0.0

        self.mode = MODE_CLASSICO
        self.state = "menu"   # menu, playing, paused, game_over

        self.reset_game(self.mode)

    def load_block_images(self):
        images = {}
        for key in ["I", "J", "L", "O", "S", "T", "Z"]:
            path = os.path.join(BLOCK_ASSET_DIR, f"{key}.png")
            try:
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.smoothscale(img, (CELL_SIZE, CELL_SIZE))
                images[key] = img
            except Exception:
                surf = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                surf.fill((255, 255, 255))
                images[key] = surf
        return images

    def reset_game(self, mode):
            self.mode = mode
            self.grid = [[None for _ in range(COLS)] for _ in range(ROWS)]

            self.score = 0
            self.lines = 0
            self.level = 1

            self.fall_timer = 0.0
            self.lock_timer = 0.0

            self.obstacle_cells = []

            self.challenge_active = None
            self.challenge_timer = 0.0
            self.challenge_phase = "waiting"

            self.current_piece = self.generate_piece()
            self.next_piece = self.generate_piece()

            self.game_over = False

    # GERAÇÃO / DIFICULDADE
    def chance_fast_piece(self):
        return min(0.18 + (self.level - 1) * 0.03, 0.45)

    def chance_locked_piece(self):
        return min(0.12 + (self.level - 1) * 0.025, 0.38)

    def choose_gravity_type(self):
        fast_chance = self.chance_fast_piece()
        slow_chance = 0.18
        roll = random.random()

        if roll < slow_chance:
            return "slow"
        if roll < slow_chance + fast_chance:
            return "fast"
        return "normal"

    def generate_piece(self):
        gravity = self.choose_gravity_type()
        locked = random.random() < self.chance_locked_piece()
        return Piece(random_shape_key(), gravity, locked)

    def get_base_fall_time(self):
        return max(0.10, BASE_FALL_TIME - (self.level - 1) * 0.045)

    # SISTEMA DE DESAFIOS
    def get_enabled_challenges(self):
        challenges = []
        if CHALLENGE_OBSTACLES_ENABLED:
            challenges.append("obstacles")
        if CHALLENGE_SPEED_ENABLED:
            challenges.append("speed")
        return challenges

    def get_challenge_interval(self):
        interval = CHALLENGE_INTERVAL - (self.level - 1) * CHALLENGE_INTERVAL_LEVEL_REDUCTION
        return max(CHALLENGE_INTERVAL_MIN, interval)

    def get_challenge_duration(self):
        duration = CHALLENGE_DURATION - (self.level - 1) * CHALLENGE_DURATION_LEVEL_REDUCTION
        return max(CHALLENGE_DURATION_MIN, duration)

    def activate_challenge(self):
        enabled = self.get_enabled_challenges()
        if not enabled:
            return
        choice = random.choice(enabled)
        self.challenge_active = choice
        self.challenge_phase = "active"
        self.challenge_timer = 0.0
        if choice == "obstacles":
                    self.spawn_barrier()

    def deactivate_challenge(self):
        if self.challenge_active == "obstacles":
            self.clear_barrier()
        self.challenge_active = None
        self.challenge_phase = "waiting"
        self.challenge_timer = 0.0
    # AUXILIARS VISUAIS
    def get_title_color(self):
        idx = int(self.title_timer * 4) % len(self.title_colors)
        return self.title_colors[idx]

    def get_piece_visual_angle(self, piece):
        if piece.gravity_type == "slow":
            return -5
        if piece.gravity_type == "fast":
            return 5
        return 0

    # MATRIZ / COLISÃO
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

    def lock_piece(self):
        for x, y in self.shape_cells(self.current_piece):
            if y < 0:
                self.game_over = True
                self.state = "game_over"
                return

            self.grid[y][x] = {
                "type": "piece",
                "shape_key": self.current_piece.shape_key,
                "pulse": 0.0
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
        new_grid = []
        cleared = 0

        for row in self.grid:
            if all(cell is not None for cell in row):
                cleared += 1
            else:
                new_grid.append(row)

        while len(new_grid) < ROWS:
            new_grid.insert(0, [None for _ in range(COLS)])

        self.grid = new_grid
        return cleared

    def get_ghost_y(self):
        ghost_piece = Piece(
            self.current_piece.shape_key,
            self.current_piece.gravity_type,
            self.current_piece.position_locked
        )
        ghost_piece.rotation = self.current_piece.rotation
        ghost_piece.x = self.current_piece.x
        ghost_piece.y = self.current_piece.y

        while self.valid_position(ghost_piece, dy=1):
            ghost_piece.y += 1

        return ghost_piece.y

    # MOVIMENTO
    def move_piece(self, dx):
        if self.current_piece.position_locked and self.current_piece.touching_ground:
            return

        if self.valid_position(self.current_piece, dx=dx):
            self.current_piece.x += dx

    def rotate_piece(self, direction):
        old_rotation = self.current_piece.rotation

        if direction == "cw":
            new_rotation = (old_rotation + 1) % len(self.current_piece.rotations)
        else:
            new_rotation = (old_rotation - 1) % len(self.current_piece.rotations)

        test_offsets = [0, -1, 1, -2, 2]

        for offset in test_offsets:
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

    # OBSTÁCULOS / BARREIRA
    def spawn_barrier(self):
        # Remove barreira anterior antes de criar nova
        self.clear_barrier()

        # Posição da linha (metade inferior do tabuleiro, longe do fundo)
        row_y = random.randint(ROWS // 2, ROWS - 5)

        # Lacunas: diminuem conforme o nível sobe
        gaps = max(BARRIER_GAPS_MIN, BARRIER_GAPS_BASE - self.level // 3)

        # Garante que cada lacuna tenha 2 cols adjacentes livres (peças com 2+ de largura)
        gap_positions = set()
        available = list(range(COLS))
        while len(gap_positions) < gaps and len(available) >= 2:
            idx = random.randrange(len(available) - 1)
            col = available[idx]
            # par adjacente: col e col+1
            if col + 1 in available:
                gap_positions.add(col)
                gap_positions.add(col + 1)
                available = [c for c in available if c != col and c != col + 1]
            else:
                available.pop(idx)

        cells = []
        for x in range(COLS):
            if x not in gap_positions:
                # Se a célula já tiver uma peça, pula (não sobrescreve)
                if self.grid[row_y][x] is None:
                    self.grid[row_y][x] = {
                        "type": "obstacle",
                        "pulse": random.random() * 6.28
                    }
                    cells.append((x, row_y))

        self.obstacle_cells = cells

    # UPDATE
    def update(self, dt, keys):
        if self.state != "playing":
            return

        self.title_timer += dt

        for row in self.grid:
            for cell in row:
                if cell is not None and cell["type"] == "obstacle":
                    cell["pulse"] += dt * 4

        base_fall = self.get_base_fall_time()
        fall_interval = base_fall / self.current_piece.gravity_mult

        if self.challenge_active == "speed":
            fall_interval /= SPEED_CHALLENGE_MULTIPLIER

        if keys[pygame.K_DOWN]:
            fall_interval /= SOFT_DROP_MULT

        self.fall_timer += dt

        if self.fall_timer >= fall_interval:
            self.fall_timer = 0.0

            if self.valid_position(self.current_piece, dy=1):
                self.current_piece.y += 1
                self.current_piece.touching_ground = False
                self.lock_timer = 0.0
            else:
                self.current_piece.touching_ground = True

        if self.current_piece.touching_ground:
            self.lock_timer += dt
            if self.lock_timer >= LOCK_DELAY:
                self.lock_piece()

        if self.mode == MODE_CORRIDA:
            self.challenge_timer += dt
            if self.challenge_phase == "waiting":
                if self.challenge_timer >= self.get_challenge_interval():
                    self.activate_challenge()
            elif self.challenge_phase == "active":
                if self.challenge_timer >= self.get_challenge_duration():
                    self.deactivate_challenge()

    # DESENHO
    def draw_text(self, text, font, color, x, y, center=False):
        surf = font.render(text, True, color)
        rect = surf.get_rect()
        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        self.screen.blit(surf, rect)

    def draw_block(self, x, y, shape_key, border_color=None, alpha=255):
        px = PLAY_X + x * CELL_SIZE
        py = PLAY_Y + y * CELL_SIZE

        img = self.block_images[shape_key].copy()
        img.set_alpha(alpha)
        self.screen.blit(img, (px, py))

        if border_color is not None:
            pygame.draw.rect(
                self.screen,
                border_color,
                (px, py, CELL_SIZE, CELL_SIZE),
                2,
                border_radius=4
            )

    def draw_block_transformed(self, x, y, shape_key, angle=0, border_color=None, alpha=255, scale=1.0):
        px = PLAY_X + x * CELL_SIZE
        py = PLAY_Y + y * CELL_SIZE

        img = self.block_images[shape_key].copy()
        img.set_alpha(alpha)

        if scale != 1.0:
            new_size = max(8, int(CELL_SIZE * scale))
            img = pygame.transform.smoothscale(img, (new_size, new_size))

        if angle != 0:
            img = pygame.transform.rotate(img, angle)

        rect = img.get_rect(center=(px + CELL_SIZE // 2, py + CELL_SIZE // 2))
        self.screen.blit(img, rect.topleft)

        if border_color is not None:
            pygame.draw.rect(
                self.screen,
                border_color,
                (px, py, CELL_SIZE, CELL_SIZE),
                2,
                border_radius=4
            )

    def draw_obstacle(self, x, y, pulse):
        px = PLAY_X + x * CELL_SIZE
        py = PLAY_Y + y * CELL_SIZE

        glow = 80 + int((pygame.math.Vector2(1, 0).rotate_rad(pulse).x + 1) * 40)
        color = (
            min(255, OBSTACLE[0]),
            min(255, OBSTACLE[1] + glow // 5),
            min(255, OBSTACLE[2]),
        )

        rect = pygame.Rect(px + 4, py + 4, CELL_SIZE - 8, CELL_SIZE - 8)
        pygame.draw.rect(self.screen, color, rect, border_radius=6)
        pygame.draw.rect(self.screen, OBSTACLE_GLOW, rect, 2, border_radius=6)

    def draw_grid(self):
        for y in range(ROWS):
            for x in range(COLS):
                rect = pygame.Rect(
                    PLAY_X + x * CELL_SIZE,
                    PLAY_Y + y * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE
                )
                pygame.draw.rect(self.screen, GRID, rect, 1)

    def draw_board(self):
        board_rect = pygame.Rect(PLAY_X, PLAY_Y, PLAY_WIDTH, PLAY_HEIGHT)
        pygame.draw.rect(self.screen, (18, 18, 30), board_rect)
        pygame.draw.rect(self.screen, BORDER, board_rect, 3)

        for y in range(ROWS):
            for x in range(COLS):
                cell = self.grid[y][x]
                if cell is None:
                    continue

                if cell["type"] == "piece":
                    self.draw_block(x, y, cell["shape_key"])
                elif cell["type"] == "obstacle":
                    self.draw_obstacle(x, y, cell["pulse"])

        self.draw_grid()

    def draw_ghost_piece(self):
        ghost_y = self.get_ghost_y()
        temp_piece = Piece(
            self.current_piece.shape_key,
            self.current_piece.gravity_type,
            self.current_piece.position_locked
        )
        temp_piece.rotation = self.current_piece.rotation
        temp_piece.x = self.current_piece.x
        temp_piece.y = ghost_y

        for x, y in self.shape_cells(temp_piece):
            if y >= 0:
                px = PLAY_X + x * CELL_SIZE
                py = PLAY_Y + y * CELL_SIZE
                surf = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                pygame.draw.rect(
                    surf,
                    (*GHOST, 70),
                    (5, 5, CELL_SIZE - 10, CELL_SIZE - 10),
                    2,
                    border_radius=6
                )
                self.screen.blit(surf, (px, py))

    def draw_current_piece(self):
        border = GRAVITY_COLORS[self.current_piece.gravity_type]
        angle = self.get_piece_visual_angle(self.current_piece)
        pulse_scale = 1.0

        if self.current_piece.position_locked:
            border = LOCKED_BORDER
            pulse_scale = 1.0 + 0.05 * abs(
                pygame.math.Vector2(1, 0).rotate(self.title_timer * 220).x
            )

        for x, y in self.shape_cells(self.current_piece):
            if y >= 0:
                self.draw_block_transformed(
                    x,
                    y,
                    self.current_piece.shape_key,
                    angle=angle,
                    border_color=border,
                    scale=pulse_scale
                )

    def draw_next_piece(self):
        box_x = SIDEBAR_X + 20
        box_y = 90
        box_w = SIDEBAR_WIDTH - 40
        box_h = 210
        pygame.draw.rect(
            self.screen,
            (20, 20, 32),
            (box_x, box_y, box_w, box_h),
            border_radius=12
        )
        pygame.draw.rect(
            self.screen,
            BORDER,
            (box_x, box_y, box_w, box_h),
            2,
            border_radius=12
        )

        self.draw_text(
            "PRÓXIMA",
            FONT_MEDIUM,
            TEXT,
            box_x + box_w // 2,
            box_y + 24,
            center=True
        )

        matrix = self.next_piece.matrix
        preview_offset_x = box_x + (box_w // 2) - 55
        preview_offset_y = box_y + 50

        border = GRAVITY_COLORS[self.next_piece.gravity_type]
        if self.next_piece.position_locked:
            border = LOCKED_BORDER

        angle = self.get_piece_visual_angle(self.next_piece)

        for row_idx, row in enumerate(matrix):
            for col_idx, val in enumerate(row):
                if val == "X":
                    px = preview_offset_x + col_idx * 28
                    py = preview_offset_y + row_idx * 28

                    img = pygame.transform.smoothscale(
                        self.block_images[self.next_piece.shape_key],
                        (24, 24)
                    )

                    if angle != 0:
                        img = pygame.transform.rotate(img, angle)

                    rect = img.get_rect(center=(px + 12, py + 12))
                    self.screen.blit(img, rect.topleft)

                    pygame.draw.rect(
                        self.screen,
                        border,
                        (px, py, 24, 24),
                        2,
                        border_radius=4
                    )

        gravidade = self.next_piece.gravity_type.upper()
        status = "TRAVADA" if self.next_piece.position_locked else "LIVRE"

        grav_color = GRAVITY_COLORS[self.next_piece.gravity_type]
        status_color = LOCKED_BORDER if self.next_piece.position_locked else TEXT

        self.draw_text(
            f"gravidade: {gravidade}",
            FONT_SMALL,
            grav_color,
            box_x + 20,
            box_y + 140
        )

        self.draw_text(
            f"status: {status}",
            FONT_SMALL,
            status_color,
            box_x + 20,
            box_y + 170
        )

    def draw_top_title(self):
        title_color = self.get_title_color()

        center_x = PLAY_X + PLAY_WIDTH // 2
        center_y = TOP_BAR_HEIGHT // 2

        self.draw_text(
            "NEON TETRIS",
            FONT_HUGE,
            title_color,
            center_x,
            center_y,
            center=True
        )

    def draw_sidebar(self):
        sidebar_rect = pygame.Rect(SIDEBAR_X, 0, SIDEBAR_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(self.screen, (14, 14, 24), sidebar_rect)
        pygame.draw.line(self.screen, BORDER, (SIDEBAR_X, 0), (SIDEBAR_X, WINDOW_HEIGHT), 3)

        self.draw_text(
            f"Modo: {self.mode.upper()}",
            FONT_SMALL,
            MUTED,
            SIDEBAR_X + SIDEBAR_WIDTH // 2,
            36,
            center=True
        )

        self.draw_next_piece()

        info_y = 310

        self.draw_text(f"Score: {self.score}", FONT_BIG, TEXT, SIDEBAR_X + 25, info_y)
        self.draw_text(f"Linhas: {self.lines}", FONT_BIG, TEXT, SIDEBAR_X + 25, info_y + 42)
        self.draw_text(f"Nível: {self.level}", FONT_BIG, TEXT, SIDEBAR_X + 25, info_y + 84)

        section_y = 450

        self.draw_text("PEÇA ATUAL", FONT_SMALL, MUTED, SIDEBAR_X + 25, section_y)

        self.draw_text("Velocidade:", FONT_SMALL, MUTED, SIDEBAR_X + 25, section_y + 32)
        self.draw_text(
            self.current_piece.gravity_type.upper(),
            FONT_SMALL,
            GRAVITY_COLORS[self.current_piece.gravity_type],
            SIDEBAR_X + 150,
            section_y + 32
        )

        self.draw_text("Travada:", FONT_SMALL, MUTED, SIDEBAR_X + 25, section_y + 62)
        self.draw_text(
            "SIM" if self.current_piece.position_locked else "NÃO",
            FONT_SMALL,
            LOCKED_BORDER if self.current_piece.position_locked else TEXT,
            SIDEBAR_X + 150,
            section_y + 62
        )

        if self.mode == MODE_CORRIDA:
            ch_y = 550
            bar_x = SIDEBAR_X + 25
            bar_y = ch_y + 60
            bar_w = SIDEBAR_WIDTH - 50
            bar_h = 18

            if self.challenge_phase == "waiting":
                interval = self.get_challenge_interval()
                remaining = max(0.0, interval - self.challenge_timer)
                progress = min(1.0, self.challenge_timer / interval) if interval > 0 else 1.0

                if remaining <= 3.0:
                    flash = abs(pygame.math.Vector2(1, 0).rotate(self.title_timer * 400).x)
                    warn_color = (
                        int(150 + 105 * flash),
                        int(150 + 105 * flash),
                        int(80 + 60 * flash)
                    )
                else:
                    warn_color = MUTED

                self.draw_text("DESAFIO", FONT_SMALL, warn_color, SIDEBAR_X + 25, ch_y)
                self.draw_text(
                    f"Próximo em: {remaining:0.1f}s",
                    FONT_MEDIUM,
                    warn_color,
                    SIDEBAR_X + 25,
                    ch_y + 28
                )

                bar_color = OBSTACLE if progress > 0.75 else MUTED

            elif self.challenge_phase == "active":
                duration = self.get_challenge_duration()
                remaining = max(0.0, duration - self.challenge_timer)
                progress = 1.0 - min(1.0, self.challenge_timer / duration) if duration > 0 else 0.0

                if self.challenge_active == "obstacles":
                    label = "OBSTÁCULOS"
                    color = OBSTACLE_GLOW
                    bar_color = OBSTACLE
                else:
                    label = "VELOCIDADE"
                    color = CHALLENGE_SPEED_COLOR
                    bar_color = CHALLENGE_SPEED_COLOR

                self.draw_text(label, FONT_MEDIUM, color, SIDEBAR_X + 25, ch_y)
                self.draw_text(
                    f"Restante: {remaining:0.1f}s",
                    FONT_SMALL,
                    color,
                    SIDEBAR_X + 25,
                    ch_y + 32
                )

            fill_w = int(bar_w * progress)

            pygame.draw.rect(
                self.screen,
                (35, 25, 40),
                (bar_x, bar_y, bar_w, bar_h),
                border_radius=8
            )
            pygame.draw.rect(
                self.screen,
                bar_color,
                (bar_x, bar_y, fill_w, bar_h),
                border_radius=8
            )
            pygame.draw.rect(
                self.screen,
                BORDER,
                (bar_x, bar_y, bar_w, bar_h),
                2,
                border_radius=8
            )

    def draw_menu(self):
        self.screen.fill(BG)

        menu_w = 560
        menu_h = 560
        menu_x = (WINDOW_WIDTH - menu_w) // 2
        menu_y = 70

        pygame.draw.rect(
            self.screen,
            (14, 14, 24),
            (menu_x, menu_y, menu_w, menu_h),
            border_radius=18
        )

        pygame.draw.rect(
            self.screen,
            BORDER,
            (menu_x, menu_y, menu_w, menu_h),
            2,
            border_radius=18
        )

        center_x = WINDOW_WIDTH // 2

        self.draw_text(
            "NEON TETRIS",
            FONT_HUGE,
            self.get_title_color(),
            center_x,
            130,
            center=True
        )

        self.draw_text(
            "1 - Modo CLÁSSICO",
            FONT_BIG,
            SPEED_NORMAL,
            center_x,
            240,
            center=True
        )

        self.draw_text(
            "2 - Modo CORRIDA",
            FONT_BIG,
            OBSTACLE_GLOW,
            center_x,
            295,
            center=True
        )

        self.draw_text(
            "CLÁSSICO = encaixe básico",
            FONT_SMALL,
            MUTED,
            center_x,
            370,
            center=True
        )

        self.draw_text(
            "CORRIDA = desafios aleatórios",
            FONT_SMALL,
            MUTED,
            center_x,
            410,
            center=True
        )

        self.draw_text(
            "obstáculos, velocidade e mais",
            FONT_SMALL,
            MUTED,
            center_x,
            440,
            center=True
        )
    
        self.draw_text(
            "ENTER inicia o modo Clássico",
            FONT_SMALL,
            TEXT,
            center_x,
            565,
            center=True
        )

    def draw_pause(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        self.draw_text("PAUSADO", FONT_HUGE, TEXT, WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20, center=True)
        self.draw_text("Pressione P para voltar", FONT_SMALL, MUTED, WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 40, center=True)

    def draw_game_over(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))
        self.draw_text("GAME OVER", FONT_HUGE, LOCKED_BORDER, WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 40, center=True)
        self.draw_text(f"Score final: {self.score}", FONT_MEDIUM, TEXT, WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20, center=True)
        self.draw_text("R para reiniciar", FONT_SMALL, MUTED, WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 70, center=True)

    def draw(self):
        if self.state == "menu":
            self.draw_menu()
            pygame.display.flip()
            return

        self.screen.fill(BG)
        self.draw_top_title()
        self.draw_board()
        self.draw_ghost_piece()
        self.draw_current_piece()

        if self.challenge_active == "speed":
            pulse = abs(pygame.math.Vector2(1, 0).rotate(self.title_timer * 300).x)
            alpha = int(60 + 120 * pulse)
            border_surf = pygame.Surface((PLAY_WIDTH + 6, PLAY_HEIGHT + 6), pygame.SRCALPHA)
            pygame.draw.rect(
                border_surf,
                (*CHALLENGE_SPEED_COLOR, alpha),
                (0, 0, PLAY_WIDTH + 6, PLAY_HEIGHT + 6),
                3,
                border_radius=2
            )
            self.screen.blit(border_surf, (PLAY_X - 3, PLAY_Y - 3))

        self.draw_sidebar()

        if self.state == "paused":
            self.draw_pause()

        if self.state == "game_over":
            self.draw_game_over()

        pygame.display.flip()

    # INPUT
    def handle_keydown(self, key):
        if self.state == "menu":
            if key == pygame.K_1:
                self.reset_game(MODE_CLASSICO)
                self.state = "playing"
            elif key == pygame.K_2:
                self.reset_game(MODE_CORRIDA)
                self.state = "playing"
            elif key == pygame.K_RETURN:
                self.reset_game(MODE_CLASSICO)
                self.state = "playing"
            return

        if key == pygame.K_r:
            self.reset_game(self.mode)
            self.state = "playing"
            return

        if key == pygame.K_p:
            if self.state == "playing":
                self.state = "paused"
            elif self.state == "paused":
                self.state = "playing"
            return

        if self.state != "playing":
            return

        if key == pygame.K_LEFT:
            self.move_piece(-1)
        elif key == pygame.K_RIGHT:
            self.move_piece(1)
        elif key in (pygame.K_UP, pygame.K_x):
            self.rotate_piece("cw")
        elif key == pygame.K_z:
            self.rotate_piece("ccw")
        elif key == pygame.K_SPACE:
            self.hard_drop()

    # LOOP
    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            keys = pygame.key.get_pressed()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    self.handle_keydown(event.key)

            if self.state == "playing":
                self.update(dt, keys)

            self.draw()


if __name__ == "__main__":
    TetrisGame().run()
