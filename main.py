import os
import random
import sys
import pygame

from settings import *
from pieces import Piece, random_shape_key
from board import BoardMixin
from challenge import ChallengeMixin
from renderer import RendererMixin

pygame.init()


class TetrisGame(BoardMixin, ChallengeMixin, RendererMixin):

    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()

        self.block_images = self._load_block_images()
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
        self.state = "menu"
        self.menu_selection = 0  # 0 = Clássico, 1 = Corrida

        self.reset_game(self.mode)

    def _load_block_images(self):
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

    # --- GERAÇÃO / DIFICULDADE ---

    def chance_fast_piece(self):
        return min(0.18 + (self.level - 1) * 0.03, 0.45)

    def chance_locked_piece(self):
        return min(0.12 + (self.level - 1) * 0.025, 0.38)

    def choose_gravity_type(self):
        slow_chance = 0.18
        fast_chance = self.chance_fast_piece()
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

    # --- UPDATE ---

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

    # --- INPUT ---

    def handle_keydown(self, key):
        if self.state == "menu":
            if key in (pygame.K_UP, pygame.K_DOWN):
                self.menu_selection = 1 - self.menu_selection
            elif key == pygame.K_1:
                self.reset_game(MODE_CLASSICO)
                self.state = "playing"
            elif key == pygame.K_2:
                self.reset_game(MODE_CORRIDA)
                self.state = "playing"
            elif key == pygame.K_RETURN:
                mode = MODE_CLASSICO if self.menu_selection == 0 else MODE_CORRIDA
                self.reset_game(mode)
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

    # --- LOOP ---

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

