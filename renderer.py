"""
RendererMixin — toda a lógica de desenho (tela, tabuleiro, HUD, menus).
"""
import pygame
from settings import *
from pieces import Piece


class RendererMixin:

    # --- HELPERS VISUAIS ---

    def get_title_color(self):
        idx = int(self.title_timer * 4) % len(self.title_colors)
        return self.title_colors[idx]

    def get_piece_visual_angle(self, piece):
        if piece.gravity_type == "slow":
            return -5
        if piece.gravity_type == "fast":
            return 5
        return 0

    def draw_text(self, text, font, color, x, y, center=False):
        surf = font.render(text, True, color)
        rect = surf.get_rect()
        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        self.screen.blit(surf, rect)

    # --- BLOCOS ---

    def draw_block(self, x, y, shape_key, border_color=None, alpha=255):
        px = PLAY_X + x * CELL_SIZE
        py = PLAY_Y + y * CELL_SIZE
        img = self.block_images[shape_key].copy()
        img.set_alpha(alpha)
        self.screen.blit(img, (px, py))
        if border_color is not None:
            pygame.draw.rect(self.screen, border_color, (px, py, CELL_SIZE, CELL_SIZE), 2, border_radius=4)

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
            pygame.draw.rect(self.screen, border_color, (px, py, CELL_SIZE, CELL_SIZE), 2, border_radius=4)

    def draw_obstacle(self, x, y, pulse):
        px = PLAY_X + x * CELL_SIZE
        py = PLAY_Y + y * CELL_SIZE
        glow = 80 + int((pygame.math.Vector2(1, 0).rotate_rad(pulse).x + 1) * 40)
        color = (min(255, OBSTACLE[0]), min(255, OBSTACLE[1] + glow // 5), min(255, OBSTACLE[2]))
        rect = pygame.Rect(px + 4, py + 4, CELL_SIZE - 8, CELL_SIZE - 8)
        pygame.draw.rect(self.screen, color, rect, border_radius=6)
        pygame.draw.rect(self.screen, OBSTACLE_GLOW, rect, 2, border_radius=6)

    # --- TABULEIRO ---

    def draw_grid(self):
        for y in range(ROWS):
            for x in range(COLS):
                rect = pygame.Rect(PLAY_X + x * CELL_SIZE, PLAY_Y + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
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
        temp = Piece(self.current_piece.shape_key, self.current_piece.gravity_type, self.current_piece.position_locked)
        temp.rotation = self.current_piece.rotation
        temp.x = self.current_piece.x
        temp.y = ghost_y
        for x, y in self.shape_cells(temp):
            if y >= 0:
                px = PLAY_X + x * CELL_SIZE
                py = PLAY_Y + y * CELL_SIZE
                surf = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                pygame.draw.rect(surf, (*GHOST, 70), (5, 5, CELL_SIZE - 10, CELL_SIZE - 10), 2, border_radius=6)
                self.screen.blit(surf, (px, py))

    def draw_current_piece(self):
        border = GRAVITY_COLORS[self.current_piece.gravity_type]
        angle = self.get_piece_visual_angle(self.current_piece)
        pulse_scale = 1.0
        if self.current_piece.position_locked:
            border = LOCKED_BORDER
            pulse_scale = 1.0 + 0.05 * abs(pygame.math.Vector2(1, 0).rotate(self.title_timer * 220).x)
        for x, y in self.shape_cells(self.current_piece):
            if y >= 0:
                self.draw_block_transformed(x, y, self.current_piece.shape_key, angle=angle, border_color=border, scale=pulse_scale)

    # --- SIDEBAR ---

    def draw_next_piece(self):
        box_x = SIDEBAR_X + 20
        box_y = 90
        box_w = SIDEBAR_WIDTH - 40
        box_h = 210
        pygame.draw.rect(self.screen, (20, 20, 32), (box_x, box_y, box_w, box_h), border_radius=12)
        pygame.draw.rect(self.screen, BORDER, (box_x, box_y, box_w, box_h), 2, border_radius=12)
        self.draw_text("PRÓXIMA", FONT_MEDIUM, TEXT, box_x + box_w // 2, box_y + 24, center=True)

        matrix = self.next_piece.matrix
        preview_offset_x = box_x + (box_w // 2) - 55
        preview_offset_y = box_y + 50
        border = LOCKED_BORDER if self.next_piece.position_locked else GRAVITY_COLORS[self.next_piece.gravity_type]
        angle = self.get_piece_visual_angle(self.next_piece)

        for row_idx, row in enumerate(matrix):
            for col_idx, val in enumerate(row):
                if val == "X":
                    px = preview_offset_x + col_idx * 28
                    py = preview_offset_y + row_idx * 28
                    img = pygame.transform.smoothscale(self.block_images[self.next_piece.shape_key], (24, 24))
                    if angle != 0:
                        img = pygame.transform.rotate(img, angle)
                    rect = img.get_rect(center=(px + 12, py + 12))
                    self.screen.blit(img, rect.topleft)
                    pygame.draw.rect(self.screen, border, (px, py, 24, 24), 2, border_radius=4)

        grav_color = GRAVITY_COLORS[self.next_piece.gravity_type]
        status_color = LOCKED_BORDER if self.next_piece.position_locked else TEXT
        self.draw_text(f"gravidade: {self.next_piece.gravity_type.upper()}", FONT_SMALL, grav_color, box_x + 20, box_y + 140)
        self.draw_text(f"status: {'TRAVADA' if self.next_piece.position_locked else 'LIVRE'}", FONT_SMALL, status_color, box_x + 20, box_y + 170)

    def draw_top_title(self):
        self.draw_text("NEON TETRIS", FONT_HUGE, self.get_title_color(), PLAY_X + PLAY_WIDTH // 2, TOP_BAR_HEIGHT // 2, center=True)

    def draw_sidebar(self):
        sidebar_rect = pygame.Rect(SIDEBAR_X, 0, SIDEBAR_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(self.screen, (14, 14, 24), sidebar_rect)
        pygame.draw.line(self.screen, BORDER, (SIDEBAR_X, 0), (SIDEBAR_X, WINDOW_HEIGHT), 3)

        self.draw_text(f"Modo: {self.mode.upper()}", FONT_SMALL, MUTED, SIDEBAR_X + SIDEBAR_WIDTH // 2, 36, center=True)
        self.draw_next_piece()

        info_y = 310
        self.draw_text(f"Score: {self.score}", FONT_BIG, TEXT, SIDEBAR_X + 25, info_y)
        self.draw_text(f"Linhas: {self.lines}", FONT_BIG, TEXT, SIDEBAR_X + 25, info_y + 42)
        self.draw_text(f"Nível: {self.level}", FONT_BIG, TEXT, SIDEBAR_X + 25, info_y + 84)

        section_y = 450
        self.draw_text("PEÇA ATUAL", FONT_SMALL, MUTED, SIDEBAR_X + 25, section_y)
        self.draw_text("Velocidade:", FONT_SMALL, MUTED, SIDEBAR_X + 25, section_y + 32)
        self.draw_text(self.current_piece.gravity_type.upper(), FONT_SMALL, GRAVITY_COLORS[self.current_piece.gravity_type], SIDEBAR_X + 150, section_y + 32)
        self.draw_text("Travada:", FONT_SMALL, MUTED, SIDEBAR_X + 25, section_y + 62)
        self.draw_text("SIM" if self.current_piece.position_locked else "NÃO", FONT_SMALL, LOCKED_BORDER if self.current_piece.position_locked else TEXT, SIDEBAR_X + 150, section_y + 62)

        if self.mode == MODE_CORRIDA:
            self._draw_challenge_hud()

    def _draw_challenge_hud(self):
        ch_y = 550
        bar_x = SIDEBAR_X + 25
        bar_y = ch_y + 60
        bar_w = SIDEBAR_WIDTH - 50
        bar_h = 18
        progress = 0.0
        bar_color = MUTED

        if self.challenge_phase == "waiting":
            interval = self.get_challenge_interval()
            remaining = max(0.0, interval - self.challenge_timer)
            progress = min(1.0, self.challenge_timer / interval) if interval > 0 else 1.0
            if remaining <= 3.0:
                flash = abs(pygame.math.Vector2(1, 0).rotate(self.title_timer * 400).x)
                warn_color = (int(150 + 105 * flash), int(150 + 105 * flash), int(80 + 60 * flash))
            else:
                warn_color = MUTED
            bar_color = OBSTACLE if progress > 0.75 else MUTED
            self.draw_text("DESAFIO", FONT_SMALL, warn_color, SIDEBAR_X + 25, ch_y)
            self.draw_text(f"Próximo em: {remaining:0.1f}s", FONT_MEDIUM, warn_color, SIDEBAR_X + 25, ch_y + 28)

        elif self.challenge_phase == "active":
            duration = self.get_challenge_duration()
            remaining = max(0.0, duration - self.challenge_timer)
            progress = 1.0 - min(1.0, self.challenge_timer / duration) if duration > 0 else 0.0
            if self.challenge_active == "obstacles":
                label, color, bar_color = "OBSTÁCULOS", OBSTACLE_GLOW, OBSTACLE
            else:
                label, color, bar_color = "VELOCIDADE", CHALLENGE_SPEED_COLOR, CHALLENGE_SPEED_COLOR
            self.draw_text(label, FONT_MEDIUM, color, SIDEBAR_X + 25, ch_y)
            self.draw_text(f"Restante: {remaining:0.1f}s", FONT_SMALL, color, SIDEBAR_X + 25, ch_y + 32)

        fill_w = int(bar_w * progress)
        pygame.draw.rect(self.screen, (35, 25, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=8)
        pygame.draw.rect(self.screen, bar_color, (bar_x, bar_y, fill_w, bar_h), border_radius=8)
        pygame.draw.rect(self.screen, BORDER, (bar_x, bar_y, bar_w, bar_h), 2, border_radius=8)

    # --- MENUS / OVERLAYS ---

    def draw_menu(self):
        self.screen.fill(BG)
        center_x = WINDOW_WIDTH // 2

        MODES = [
            {
                "label": "MODO CLÁSSICO",
                "color": SPEED_NORMAL,
                "desc": ["Tetris puro e limpo.", "Encaixe as peças e survive."],
                "key": "1",
            },
            {
                "label": "MODO CORRIDA",
                "color": OBSTACLE_GLOW,
                "desc": ["Desafios aleatórios durante a partida:", "barreiras, velocidade e mais."],
                "key": "2",
            },
        ]

        menu_w, menu_h = 560, 580
        menu_x = (WINDOW_WIDTH - menu_w) // 2
        menu_y = 60
        pygame.draw.rect(self.screen, (14, 14, 24), (menu_x, menu_y, menu_w, menu_h), border_radius=18)
        pygame.draw.rect(self.screen, BORDER, (menu_x, menu_y, menu_w, menu_h), 2, border_radius=18)
        self.draw_text("NEON TETRIS", FONT_HUGE, self.get_title_color(), center_x, 118, center=True)

        card_w = menu_w - 60
        card_x = menu_x + 30
        card_top = 175
        card_h = 110
        card_gap = 22
        pulse = abs(pygame.math.Vector2(1, 0).rotate(self.title_timer * 180).x)

        for i, m in enumerate(MODES):
            cy = card_top + i * (card_h + card_gap)
            selected = (i == self.menu_selection)

            if selected:
                glow_surf = pygame.Surface((card_w + 8, card_h + 8), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (*m["color"], int(30 + 25 * pulse)), (0, 0, card_w + 8, card_h + 8), border_radius=14)
                self.screen.blit(glow_surf, (card_x - 4, cy - 4))
                card_bg, border_col, border_w = (28, 28, 44), m["color"], 2
            else:
                card_bg, border_col, border_w = (18, 18, 30), BORDER, 1

            pygame.draw.rect(self.screen, card_bg, (card_x, cy, card_w, card_h), border_radius=12)
            pygame.draw.rect(self.screen, border_col, (card_x, cy, card_w, card_h), border_w, border_radius=12)
            self.draw_text(m["label"], FONT_BIG, m["color"] if selected else MUTED, card_x + card_w // 2, cy + 26, center=True)
            for j, line in enumerate(m["desc"]):
                self.draw_text(line, FONT_SMALL, TEXT if selected else (90, 90, 110), card_x + card_w // 2, cy + 60 + j * 22, center=True)
            self.draw_text(f"[{m['key']}]", FONT_SMALL, m["color"] if selected else (60, 60, 80), card_x + card_w - 20, cy + 12)

        sel_cy = card_top + self.menu_selection * (card_h + card_gap) + card_h // 2
        arrow_x = card_x - 22
        arrow_offset = int(4 * pulse)
        pygame.draw.polygon(self.screen, MODES[self.menu_selection]["color"], [
            (arrow_x - 8 + arrow_offset, sel_cy),
            (arrow_x - 18 + arrow_offset, sel_cy - 8),
            (arrow_x - 18 + arrow_offset, sel_cy + 8),
        ])
        self.draw_text("↑↓  navegar    ENTER  confirmar", FONT_SMALL, MUTED, center_x, menu_y + menu_h - 28, center=True)

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

    # --- FRAME PRINCIPAL ---

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
            pygame.draw.rect(border_surf, (*CHALLENGE_SPEED_COLOR, alpha), (0, 0, PLAY_WIDTH + 6, PLAY_HEIGHT + 6), 3, border_radius=2)
            self.screen.blit(border_surf, (PLAY_X - 3, PLAY_Y - 3))

        self.draw_sidebar()

        if self.state == "paused":
            self.draw_pause()
        if self.state == "game_over":
            self.draw_game_over()

        pygame.display.flip()
