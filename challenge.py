"""
ChallengeMixin — sistema de desafios e barreira do Modo Corrida.
"""
import random
from settings import *


class ChallengeMixin:

    # --- BARREIRA ---

    def clear_barrier(self):
        for x, y in self.obstacle_cells:
            if 0 <= y < ROWS and 0 <= x < COLS:
                if self.grid[y][x] is not None and self.grid[y][x]["type"] == "obstacle":
                    self.grid[y][x] = None
        self.obstacle_cells = []

    def refresh_obstacle_cells(self):
        """Re-sincroniza obstacle_cells com o grid real (ex: após clear_lines)."""
        self.obstacle_cells = [
            (x, y)
            for y in range(ROWS)
            for x in range(COLS)
            if self.grid[y][x] is not None and self.grid[y][x]["type"] == "obstacle"
        ]

    def spawn_barrier(self):
        self.clear_barrier()

        row_y = random.randint(ROWS // 2, ROWS - 5)
        gaps = max(BARRIER_GAPS_MIN, BARRIER_GAPS_BASE - self.level // 3)

        # Garante lacunas de 2 colunas adjacentes (peças com largura ≥ 2 conseguem passar)
        gap_positions = set()
        available = list(range(COLS))
        while len(gap_positions) < gaps and len(available) >= 2:
            idx = random.randrange(len(available) - 1)
            col = available[idx]
            if col + 1 in available:
                gap_positions.add(col)
                gap_positions.add(col + 1)
                available = [c for c in available if c != col and c != col + 1]
            else:
                available.pop(idx)

        cells = []
        for x in range(COLS):
            if x not in gap_positions and self.grid[row_y][x] is None:
                self.grid[row_y][x] = {"type": "obstacle", "pulse": random.random() * 6.28}
                cells.append((x, row_y))

        self.obstacle_cells = cells

    # --- CICLO DE DESAFIOS ---

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
        self.challenge_active = random.choice(enabled)
        self.challenge_phase = "active"
        self.challenge_timer = 0.0
        if self.challenge_active == "obstacles":
            self.spawn_barrier()

    def deactivate_challenge(self):
        if self.challenge_active == "obstacles":
            self.clear_barrier()
        self.challenge_active = None
        self.challenge_phase = "waiting"
        self.challenge_timer = 0.0
