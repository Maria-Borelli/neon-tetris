import os
import random
import sys
import json
from datetime import datetime
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
        # Canvas lógico fixo: toda UI/física continua usando a resolução original.
        self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
        self.screen = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT)).convert()
        self.fullscreen = False
        self.windowed_size = (WINDOW_WIDTH, WINDOW_HEIGHT)
        self.pillar_background = None
        self.pillar_background_size = None
        self.pillar_blocks = []
        self.init_pillar_blocks()
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()

        self.block_images = self.load_block_images()
        self.menu_background = self.load_menu_background()

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
        self.menu_selection = 0  # 0 = Clássico, 1 = Corrida, 2 = Desafio
        self.player_name = ""
        self.name_input = ""
        self.challenge_scores = self.load_challenge_scores()
        self.score_saved = False

        self.joysticks = {}
        self.init_joysticks()

        self.control_actions = [
            ("left", "Mover para esquerda"),
            ("right", "Mover para direita"),
            ("soft_drop", "Queda suave"),
            ("hard_drop", "Queda instantânea"),
            ("rotate_cw", "Rotacionar horário"),
            ("rotate_ccw", "Rotacionar anti-horário"),
            ("hold", "Guardar peça (Hold)"),
        ]
        self.control_selection = 0
        self.pause_selection = 0
        self.controls_return_state = "menu"
        self.control_capture = None
        self.control_capture_device = "gamepad"
        self.controls_toast = ""
        self.controls_toast_timer = 0.0
        self.axis_latched = set()
        self.controller_bindings = self.load_controller_bindings()

        self.reset_game(self.mode)

    def init_joysticks(self):
        """Inicializa controles já conectados."""
        pygame.joystick.init()
        for i in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(i)
            joystick.init()
            self.joysticks[joystick.get_instance_id()] = joystick

    def add_joystick(self, device_index):
        joystick = pygame.joystick.Joystick(device_index)
        joystick.init()
        self.joysticks[joystick.get_instance_id()] = joystick

    def remove_joystick(self, instance_id):
        self.joysticks.pop(instance_id, None)

    def default_controller_bindings(self):
        # SDL mais comum: D-Pad = hat 0; botões 0/1/2; ombros 4/5.
        # Hard drop também aceita gatilhos por padrão.
        return {
            "left": [{"type": "hat", "hat": 0, "value": [-1, 0]}],
            "right": [{"type": "hat", "hat": 0, "value": [1, 0]}],
            "soft_drop": [{"type": "hat", "hat": 0, "value": [0, -1]}],
            "hard_drop": [{"type": "hat", "hat": 0, "value": [0, 1]},
                          {"type": "axis", "axis": 2, "sign": 1},
                          {"type": "axis", "axis": 5, "sign": 1}],
            "rotate_cw": [{"type": "button", "button": 1}],
            "rotate_ccw": [{"type": "button", "button": 0},
                           {"type": "button", "button": 2}],
            "hold": [{"type": "button", "button": 4},
                     {"type": "button", "button": 5}],
        }

    def bindings_path(self):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "controller_bindings.json")

    def load_controller_bindings(self):
        try:
            with open(self.bindings_path(), "r", encoding="utf-8") as f:
                data = json.load(f)
            if all(k in data for k, _ in self.control_actions):
                return data
        except (OSError, ValueError, TypeError):
            pass
        return self.default_controller_bindings()

    def save_controller_bindings(self):
        try:
            with open(self.bindings_path(), "w", encoding="utf-8") as f:
                json.dump(self.controller_bindings, f, indent=2, ensure_ascii=False)
        except OSError:
            pass

    def keyboard_binding_label(self, action):
        labels = {
            "left": "SETA ESQUERDA",
            "right": "SETA DIREITA",
            "soft_drop": "SETA BAIXO",
            "hard_drop": "ESPAÇO",
            "rotate_cw": "SETA CIMA / X",
            "rotate_ccw": "Z / CTRL",
            "hold": "C / SHIFT",
        }
        return labels.get(action, "-")

    def friendly_gamepad_binding(self, binding):
        kind = binding.get("type")
        if kind == "hat":
            x, y = binding.get("value", [0, 0])
            return {
                (-1, 0): "D-Pad Esquerda",
                (1, 0): "D-Pad Direita",
                (0, -1): "D-Pad Baixo",
                (0, 1): "D-Pad Cima",
            }.get((x, y), "D-Pad")
        if kind == "button":
            b = binding.get("button", -1)
            names = {
                0: "Botão A / Cross",
                1: "Botão B / Circle",
                2: "Botão X / Square",
                3: "Botão Y / Triangle",
                4: "Ombro LB / L1",
                5: "Ombro RB / R1",
                6: "Select / View",
                7: "Start / Menu",
            }
            return names.get(b, f"Botão {b}")
        if kind == "axis":
            axis = binding.get("axis", -1)
            sign = binding.get("sign", 1)
            common = {
                (0, -1): "Analógico E. (Esq)",
                (0, 1): "Analógico E. (Dir)",
                (1, -1): "Analógico E. (Cima)",
                (1, 1): "Analógico E. (Baixo)",
                (2, 1): "Gatilho LT / L2",
                (2, -1): "Gatilho LT / L2",
                (5, 1): "Gatilho RT / R2",
                (5, -1): "Gatilho LT / L2",
            }
            return common.get((axis, sign), f"Analógico / Gatilho {axis}")
        return "Não definido"

    def binding_label(self, action):
        items = self.controller_bindings.get(action, [])
        labels = [self.friendly_gamepad_binding(b) for b in items]
        return " / ".join(labels) if labels else "Não definido"

    def capture_controller_event(self, event):
        binding = None
        if event.type == pygame.JOYBUTTONDOWN:
            binding = {"type": "button", "button": event.button}
        elif event.type == pygame.JOYHATMOTION and event.value != (0, 0):
            binding = {"type": "hat", "hat": getattr(event, "hat", 0), "value": list(event.value)}
        elif event.type == pygame.JOYAXISMOTION and abs(event.value) > 0.7:
            binding = {"type": "axis", "axis": event.axis, "sign": 1 if event.value > 0 else -1}
        if binding is not None:
            self.controller_bindings[self.control_capture] = [binding]
            self.save_controller_bindings()
            self.control_capture = None
            return True
        return False

    def binding_matches(self, action, kind, **kwargs):
        for b in self.controller_bindings.get(action, []):
            if b.get("type") != kind:
                continue
            if kind == "button" and b.get("button") == kwargs.get("button"):
                return True
            if kind == "hat" and b.get("hat", 0) == kwargs.get("hat", 0):
                bx, by = b.get("value", [0, 0])
                x, y = kwargs.get("value", (0, 0))
                if (bx and x == bx) or (by and y == by):
                    return True
            if kind == "axis" and b.get("axis") == kwargs.get("axis"):
                v = kwargs.get("value", 0)
                if abs(v) > 0.7 and (1 if v > 0 else -1) == b.get("sign", 1):
                    return True
        return False

    def perform_controller_action(self, action):
        if self.state != "playing":
            return
        if action == "left":
            self.move_piece(-1)
        elif action == "right":
            self.move_piece(1)
        elif action == "hard_drop":
            self.hard_drop()
        elif action == "rotate_cw":
            self.rotate_piece("cw")
        elif action == "rotate_ccw":
            self.rotate_piece("ccw")
        elif action == "hold":
            self.hold_current_piece()

    def controller_action_held(self, action):
        for joy in self.joysticks.values():
            if not joy.get_init():
                continue
            for b in self.controller_bindings.get(action, []):
                try:
                    if b["type"] == "button" and b["button"] < joy.get_numbuttons() and joy.get_button(b["button"]):
                        return True
                    if b["type"] == "hat" and b.get("hat", 0) < joy.get_numhats():
                        x, y = joy.get_hat(b.get("hat", 0))
                        bx, by = b["value"]
                        if (bx and x == bx) or (by and y == by):
                            return True
                    if b["type"] == "axis" and b["axis"] < joy.get_numaxes():
                        v = joy.get_axis(b["axis"])
                        if abs(v) > .7 and (1 if v > 0 else -1) == b.get("sign", 1):
                            return True
                except pygame.error:
                    pass
        return False

    def load_menu_background(self):
        """Capa em cover proporcional, alinhada ao topo."""
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "NEON.png")
        try:
            image = pygame.image.load(path).convert()
            iw, ih = image.get_size()
            scale = max(WINDOW_WIDTH / iw, WINDOW_HEIGHT / ih)
            nw, nh = int(iw * scale), int(ih * scale)
            image = pygame.transform.smoothscale(image, (nw, nh))
            crop_x = max(0, (nw - WINDOW_WIDTH) // 2)
            return image.subsurface((crop_x, 0, WINDOW_WIDTH, WINDOW_HEIGHT)).copy()
        except (pygame.error, OSError, ValueError):
            return None

    def draw_menu_gradient(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        h = WINDOW_HEIGHT
        for y in range(h):
            t = y / max(1, h - 1)
            if t <= .25:
                alpha = int(255 * (.10 * (t / .25)))
            elif t <= .75:
                u = (t - .25) / .50
                alpha = int(255 * (.50 + .15 * u))
            else:
                u = (t - .75) / .25
                alpha = int(255 * (.65 - .18 * u))
            pygame.draw.line(overlay, (5, 5, 12, alpha), (0, y), (WINDOW_WIDTH, y))
        self.screen.blit(overlay, (0, 0))

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

    def challenge_scores_path(self):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "challenge_scores.json")

    def load_challenge_scores(self):
        try:
            with open(self.challenge_scores_path(), "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return sorted(data, key=lambda item: int(item.get("score", 0)), reverse=True)[:10]
        except (OSError, ValueError, TypeError):
            pass
        return []

    def save_challenge_score(self):
        if self.mode != MODE_DESAFIO or self.score_saved:
            return
        entry = {
            "name": (self.player_name.strip() or "PLAYER")[:16],
            "score": int(self.score),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        self.challenge_scores.append(entry)
        self.challenge_scores = sorted(
            self.challenge_scores, key=lambda item: int(item.get("score", 0)), reverse=True
        )[:10]
        try:
            with open(self.challenge_scores_path(), "w", encoding="utf-8") as f:
                json.dump(self.challenge_scores, f, ensure_ascii=False, indent=2)
        except OSError:
            pass
        self.score_saved = True

    def finish_game(self):
        self.game_over = True
        self.state = "game_over"
        self.save_challenge_score()

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
            self.hold_piece = None
            self.hold_used = False

            self.game_over = False
            self.score_saved = False

    # Dificuldade 
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
        piece = Piece(random_shape_key(), gravity, locked)
        # No Modo Desafio, 10% das peças carregam exatamente uma bomba.
        piece.bomb_index = random.randrange(4) if self.mode == MODE_DESAFIO and random.random() < 0.10 else None
        return piece

    def get_base_fall_time(self):
        return max(0.10, BASE_FALL_TIME - (self.level - 1) * 0.045)

    # Sistema de desafio 
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
    # Auxiliares visuais
    def get_title_color(self):
        idx = int(self.title_timer * 4) % len(self.title_colors)
        return self.title_colors[idx]

    def get_piece_visual_angle(self, piece):
        if piece.gravity_type == "slow":
            return -5
        if piece.gravity_type == "fast":
            return 5
        return 0

    # Matriz/Colisão
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
        cells = self.shape_cells(self.current_piece)
        bomb_pos = None
        for index, (x, y) in enumerate(cells):
            if y < 0:
                self.finish_game()
                return
            self.grid[y][x] = {
                "type": "piece",
                "shape_key": self.current_piece.shape_key,
                "pulse": 0.0
            }
            if getattr(self.current_piece, "bomb_index", None) == index:
                bomb_pos = (x, y)

        if bomb_pos is not None:
            destroyed = self.explode_bomb(*bomb_pos)
            self.score -= destroyed * 50

        cleared = self.clear_lines()
        if cleared > 0:
            self.lines += cleared
            self.score += LINE_CLEAR_POINTS.get(cleared, 800) * self.level
            self.level = (self.lines // LINES_PER_LEVEL) + 1
            if self.mode == MODE_CORRIDA:
                self.refresh_obstacle_cells()

        self.current_piece = self.next_piece
        self.next_piece = self.generate_piece()
        self.hold_used = False
        self.current_piece.x = 3
        self.current_piece.y = 0

        if not self.valid_position(self.current_piece):
            self.finish_game()

        self.lock_timer = 0.0

    def explode_bomb(self, center_x, center_y):
        destroyed = 0
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                x, y = center_x + dx, center_y + dy
                if 0 <= x < COLS and 0 <= y < ROWS and self.grid[y][x] is not None:
                    self.grid[y][x] = None
                    destroyed += 1
        if self.mode == MODE_CORRIDA:
            self.refresh_obstacle_cells()
        return destroyed

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

    # Movimento
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

    def hold_current_piece(self):
        """Guarda/troca a peça atual. Só pode ser usado uma vez por peça."""
        if self.hold_used:
            return

        current = self.current_piece
        if self.hold_piece is None:
            self.hold_piece = Piece(current.shape_key, current.gravity_type, current.position_locked)
            self.current_piece = self.next_piece
            self.next_piece = self.generate_piece()
        else:
            held = self.hold_piece
            self.hold_piece = Piece(current.shape_key, current.gravity_type, current.position_locked)
            self.current_piece = Piece(held.shape_key, held.gravity_type, held.position_locked)

        self.current_piece.x = 3
        self.current_piece.y = 0
        self.current_piece.touching_ground = False
        self.lock_timer = 0.0
        self.fall_timer = 0.0
        self.hold_used = True

        if not self.valid_position(self.current_piece):
            self.finish_game()

    def controller_soft_drop(self):
        return any(
            joy.get_init() and joy.get_numhats() > 0 and joy.get_hat(0)[1] < 0
            for joy in self.joysticks.values()
        )

    # Obstáculos
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

    # Update
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

        if keys[pygame.K_DOWN] or self.controller_action_held("soft_drop"):
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

    # Desenho
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
        # Halo neon suave atrás da peça ativa.
        glow_color = border_color or GRAVITY_COLORS.get(self.current_piece.gravity_type, (0, 240, 255))
        glow = pygame.Surface((CELL_SIZE + 16, CELL_SIZE + 16), pygame.SRCALPHA)
        for width, a in ((10, 18), (6, 35), (3, 70)):
            pygame.draw.rect(glow, (*glow_color, a), (8, 8, CELL_SIZE, CELL_SIZE), width, border_radius=6)
        self.screen.blit(glow, (px - 8, py - 8))

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
        color = (
            min(255, OBSTACLE[0]),
            min(255, OBSTACLE[1] + glow // 5),
            min(255, OBSTACLE[2]),
        )

        rect = pygame.Rect(px + 4, py + 4, CELL_SIZE - 8, CELL_SIZE - 8)
        pygame.draw.rect(self.screen, color, rect, border_radius=6)
        pygame.draw.rect(self.screen, OBSTACLE_GLOW, rect, 2, border_radius=6)

    def draw_grid(self):
        # Grid discreto (~18% visual) para não competir com as peças.
        grid_surface = pygame.Surface((PLAY_WIDTH, PLAY_HEIGHT), pygame.SRCALPHA)
        for x in range(COLS + 1):
            px = x * CELL_SIZE
            pygame.draw.line(grid_surface, (42, 42, 64, 46), (px, 0), (px, PLAY_HEIGHT))
        for y in range(ROWS + 1):
            py = y * CELL_SIZE
            pygame.draw.line(grid_surface, (42, 42, 64, 46), (0, py), (PLAY_WIDTH, py))
        self.screen.blit(grid_surface, (PLAY_X, PLAY_Y))

    def draw_board(self):
        board_rect = pygame.Rect(PLAY_X, PLAY_Y, PLAY_WIDTH, PLAY_HEIGHT)
        pygame.draw.rect(self.screen, (8, 8, 16), board_rect)
        pygame.draw.rect(self.screen, (58, 58, 94), board_rect, 2)
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
        temp_piece = Piece(self.current_piece.shape_key, self.current_piece.gravity_type,
                           self.current_piece.position_locked)
        temp_piece.rotation = self.current_piece.rotation
        temp_piece.x = self.current_piece.x
        temp_piece.y = ghost_y
        color = GRAVITY_COLORS.get(self.current_piece.gravity_type, (0, 240, 255))
        for x, y in self.shape_cells(temp_piece):
            if y >= 0:
                px = PLAY_X + x * CELL_SIZE
                py = PLAY_Y + y * CELL_SIZE
                surf = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                pygame.draw.rect(surf, (*color, 64), (4, 4, CELL_SIZE - 8, CELL_SIZE - 8), border_radius=5)
                pygame.draw.rect(surf, (*color, 145), (4, 4, CELL_SIZE - 8, CELL_SIZE - 8), 2, border_radius=5)
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

        for index, (x, y) in enumerate(self.shape_cells(self.current_piece)):
            if y >= 0:
                self.draw_block_transformed(
                    x, y, self.current_piece.shape_key,
                    angle=angle, border_color=border, scale=pulse_scale
                )
                if getattr(self.current_piece, "bomb_index", None) == index:
                    px, py = PLAY_X + x*CELL_SIZE, PLAY_Y + y*CELL_SIZE
                    pulse = 170 + int(85 * abs(pygame.math.Vector2(1,0).rotate(self.title_timer*420).x))
                    pygame.draw.circle(self.screen,(255,30,80),(px+CELL_SIZE//2,py+CELL_SIZE//2),CELL_SIZE//4)
                    pygame.draw.circle(self.screen,(255,pulse,80),(px+CELL_SIZE//2,py+CELL_SIZE//2),CELL_SIZE//4,2)
                    self.draw_text("B", FONT_SMALL, (255,255,255), px+CELL_SIZE//2, py+CELL_SIZE//2, center=True)

    def draw_next_piece(self):
        box_x = SIDEBAR_X + 22
        box_y = 76
        box_w = SIDEBAR_WIDTH - 44
        box_h = 190
        pygame.draw.rect(self.screen, (13, 13, 25), (box_x, box_y, box_w, box_h), border_radius=14)
        pygame.draw.rect(self.screen, (58, 58, 94), (box_x, box_y, box_w, box_h), 2, border_radius=14)
        self.draw_text("PRÓXIMA", FONT_MEDIUM, (0, 240, 255), box_x + box_w // 2, box_y + 25, center=True)

        matrix = self.next_piece.matrix
        cells = [(c, r) for r, row in enumerate(matrix) for c, val in enumerate(row) if val == "X"]
        if cells:
            min_c, max_c = min(c for c, _ in cells), max(c for c, _ in cells)
            min_r, max_r = min(r for _, r in cells), max(r for _, r in cells)
            size = 28
            shape_w, shape_h = (max_c-min_c+1)*size, (max_r-min_r+1)*size
            ox = box_x + (box_w-shape_w)//2 - min_c*size
            oy = box_y + 68 + (82-shape_h)//2 - min_r*size
            for c, r in cells:
                img = pygame.transform.smoothscale(self.block_images[self.next_piece.shape_key], (24, 24))
                self.screen.blit(img, (ox + c*size + 2, oy + r*size + 2))

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
        pygame.draw.rect(self.screen, (8, 8, 16), sidebar_rect)
        pygame.draw.line(self.screen, (58, 58, 94), (SIDEBAR_X, 0), (SIDEBAR_X, WINDOW_HEIGHT), 2)
        self.draw_text(f"MODO {self.mode.upper()}", FONT_SMALL, (160, 160, 192),
                       SIDEBAR_X + SIDEBAR_WIDTH // 2, 35, center=True)
        self.draw_next_piece()

        card_x, card_w = SIDEBAR_X + 22, SIDEBAR_WIDTH - 44
        stats_y, stats_h = 282, 170
        pygame.draw.rect(self.screen, (13, 13, 25), (card_x, stats_y, card_w, stats_h), border_radius=14)
        pygame.draw.rect(self.screen, (58, 58, 94), (card_x, stats_y, card_w, stats_h), 2, border_radius=14)
        self.draw_text(f"SCORE:  {self.score}", FONT_BIG, TEXT, card_x + 18, stats_y + 24)
        self.draw_text(f"LINHAS: {self.lines}", FONT_MEDIUM, TEXT, card_x + 18, stats_y + 78)
        self.draw_text(f"NÍVEL:  {self.level}", FONT_MEDIUM, TEXT, card_x + 18, stats_y + 120)

        status_y = 468
        pygame.draw.rect(self.screen, (13, 13, 25), (card_x, status_y, card_w, 132), border_radius=14)
        pygame.draw.rect(self.screen, (58, 58, 94), (card_x, status_y, card_w, 132), 2, border_radius=14)
        gravity = self.current_piece.gravity_type.upper()
        speed = "FAST" if self.challenge_active == "speed" else "NORMAL"
        locked = "SIM" if self.current_piece.position_locked else "NÃO"
        self.draw_text(f"Gravidade: {gravity}", FONT_SMALL, (180, 180, 205), card_x + 16, status_y + 18)
        self.draw_text(f"Velocidade: {speed}", FONT_SMALL, (180, 180, 205), card_x + 16, status_y + 52)
        self.draw_text(f"Travada: {locked}", FONT_SMALL, (180, 180, 205), card_x + 16, status_y + 86)

        if self.mode == MODE_CORRIDA:
            bar_x, bar_y, bar_w, bar_h = card_x, 628, card_w, 18
            if self.challenge_phase == "active":
                total = self.get_challenge_duration()
                progress = max(0.0, 1.0 - self.challenge_timer / total) if total else 0
                label = "DESAFIO ATIVO"
                color = (255, 0, 85)
            else:
                total = self.get_challenge_interval()
                progress = min(1.0, self.challenge_timer / total) if total else 0
                label = "PRÓXIMO DESAFIO"
                color = (0, 240, 255)
            self.draw_text(label, FONT_SMALL, color, card_x, bar_y - 26)
            pygame.draw.rect(self.screen, (20, 20, 35), (bar_x, bar_y, bar_w, bar_h), border_radius=8)
            pygame.draw.rect(self.screen, color, (bar_x, bar_y, int(bar_w*progress), bar_h), border_radius=8)
            pygame.draw.rect(self.screen, color, (bar_x, bar_y, bar_w, bar_h), 2, border_radius=8)

    def draw_menu(self):
        self.screen.fill((8, 8, 16))
        if self.menu_background is not None:
            self.screen.blit(self.menu_background, (0, 0))
        self.draw_menu_gradient()
        center_x = WINDOW_WIDTH // 2
        modes = [
            ("MODO CLÁSSICO", ["Tetris puro e limpo.", "Encaixe as peças e sobreviva."]),
            ("MODO CORRIDA", ["Desafios aleatórios durante a partida:", "barreiras, velocidade e mais."]),
            ("MODO DESAFIO", ["10% de chance de peças-bomba.", "Explosões 3x3 valem -50 por bloco."]),
        ]
        card_w, card_h, gap = 510, 94, 12
        card_x, top = (WINDOW_WIDTH-card_w)//2, 330
        pulse = (pygame.math.Vector2(1,0).rotate(self.title_timer*150).x+1)/2
        for i, (label, desc) in enumerate(modes):
            y = top + i*(card_h+gap)
            selected = i == self.menu_selection
            if selected:
                halo = pygame.Surface((card_w+28,card_h+28), pygame.SRCALPHA)
                pygame.draw.rect(halo,(0,240,255,int(30+25*pulse)),halo.get_rect(),8,border_radius=18)
                self.screen.blit(halo,(card_x-14,y-14))
                bg=pygame.Surface((card_w,card_h),pygame.SRCALPHA); bg.fill((10,12,24,238))
                self.screen.blit(bg,(card_x,y))
                pygame.draw.rect(self.screen,(0,240,255),(card_x,y,card_w,card_h),4,border_radius=14)
                tc,dc=(0,240,255),(255,255,255)
            else:
                bg=pygame.Surface((card_w,card_h),pygame.SRCALPHA); bg.fill((12,12,28,155))
                self.screen.blit(bg,(card_x,y))
                pygame.draw.rect(self.screen,(58,58,94),(card_x,y,card_w,card_h),1,border_radius=14)
                tc,dc=(160,160,192),(112,112,144)
            self.draw_text(label,FONT_BIG,tc,center_x,y+23,center=True)
            self.draw_text(desc[0],FONT_SMALL,dc,center_x,y+55,center=True)
            self.draw_text(desc[1],FONT_SMALL,dc,center_x,y+76,center=True)
        footer=pygame.Surface((WINDOW_WIDTH,68),pygame.SRCALPHA); footer.fill((5,5,12,105))
        self.screen.blit(footer,(0,WINDOW_HEIGHT-68))
        self.draw_text("[ ↑ / ↓ ] Navegar",FONT_SMALL,(208,208,224),center_x,WINDOW_HEIGHT-44,center=True)
        self.draw_text("[ ENTER ] Confirmar  |  [ C ] Controles",FONT_SMALL,(208,208,224),center_x,WINDOW_HEIGHT-19,center=True)

    def draw_name_input(self):
        self.draw_menu()
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5,5,12,225))
        self.screen.blit(overlay,(0,0))
        w,h=500,245
        x,y=(WINDOW_WIDTH-w)//2,(WINDOW_HEIGHT-h)//2
        pygame.draw.rect(self.screen,(12,10,24),(x,y,w,h),border_radius=16)
        pygame.draw.rect(self.screen,(255,0,127),(x,y,w,h),3,border_radius=16)
        self.draw_text("MODO DESAFIO",FONT_BIG,(255,0,127),WINDOW_WIDTH//2,y+45,center=True)
        self.draw_text("Digite seu nickname",FONT_SMALL,(208,208,224),WINDOW_WIDTH//2,y+88,center=True)
        pygame.draw.rect(self.screen,(6,8,18),(x+55,y+112,w-110,48),border_radius=8)
        pygame.draw.rect(self.screen,(0,240,255),(x+55,y+112,w-110,48),2,border_radius=8)
        shown=self.name_input if self.name_input else "_"
        self.draw_text(shown,FONT_MEDIUM,(255,255,255),WINDOW_WIDTH//2,y+136,center=True)
        self.draw_text("[ ENTER ] Jogar   [ ESC ] Voltar",FONT_SMALL,(160,160,192),WINDOW_WIDTH//2,y+205,center=True)

    def draw_pause(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 5, 12, 217))  # ~85%, preserva tabuleiro/HUD ao fundo.
        self.screen.blit(overlay, (0, 0))

        card_w, card_h = 430, 390
        card_x = (WINDOW_WIDTH - card_w) // 2
        card_y = (WINDOW_HEIGHT - card_h) // 2

        # Glow externo cyan.
        glow = pygame.Surface((card_w + 34, card_h + 34), pygame.SRCALPHA)
        for width, alpha in ((12, 20), (7, 38), (3, 70)):
            pygame.draw.rect(glow, (0, 240, 255, alpha),
                             (17, 17, card_w, card_h), width, border_radius=18)
        self.screen.blit(glow, (card_x - 17, card_y - 17))
        pygame.draw.rect(self.screen, (10, 10, 22), (card_x, card_y, card_w, card_h), border_radius=16)
        pygame.draw.rect(self.screen, (0, 240, 255), (card_x, card_y, card_w, card_h), 3, border_radius=16)

        cx = WINDOW_WIDTH // 2
        for ox, oy in ((-2,0),(2,0),(0,-2),(0,2)):
            self.draw_text("JOGO PAUSADO", FONT_HUGE, (0, 70, 82), cx+ox, card_y+62+oy, center=True)
        self.draw_text("JOGO PAUSADO", FONT_HUGE, (0, 240, 255), cx, card_y+62, center=True)

        options = [
            ("Continuar", "[ ESC / ENTER ]"),
            ("Controles", "[ C ]"),
            ("Reiniciar Partida", "[ R ]"),
            ("Sair ao Menu", "[ V ]"),
        ]
        start_y, row_h = card_y + 128, 56
        for i, (label, shortcut) in enumerate(options):
            y = start_y + i * row_h
            selected = i == self.pause_selection
            if selected:
                row = pygame.Surface((card_w - 54, 44), pygame.SRCALPHA)
                row.fill((0, 240, 255, 24))
                self.screen.blit(row, (card_x + 27, y - 5))
                pygame.draw.rect(self.screen, (0, 240, 255),
                                 (card_x + 27, y - 5, card_w - 54, 44), 1, border_radius=8)
                self.draw_text(">", FONT_MEDIUM, (0, 240, 255), card_x + 40, y + 6)
            color = (0, 240, 255) if selected else (224, 224, 232)
            self.draw_text(label, FONT_MEDIUM, color, card_x + 70, y + 5)
            key_surf = FONT_SMALL.render(shortcut, True, (160, 160, 192))
            self.screen.blit(key_surf, (card_x + card_w - key_surf.get_width() - 42, y + 9))

        self.draw_text("[ ↑ / ↓ ] Navegar   •   [ ENTER ] Confirmar",
                       FONT_SMALL, (140, 140, 165), cx, card_y + card_h - 28, center=True)

    def draw_game_over(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 5, 12, 224))
        self.screen.blit(overlay, (0, 0))
        challenge = self.mode == MODE_DESAFIO
        w, h = (540, 610) if challenge else (480, 300)
        x, y = (WINDOW_WIDTH-w)//2, (WINDOW_HEIGHT-h)//2
        glow = pygame.Surface((w+30, h+30), pygame.SRCALPHA)
        pygame.draw.rect(glow, (255,0,85,55), glow.get_rect(), 10, border_radius=20)
        self.screen.blit(glow, (x-15,y-15))
        pygame.draw.rect(self.screen, (12, 10, 22), (x,y,w,h), border_radius=16)
        pygame.draw.rect(self.screen, (255,0,85), (x,y,w,h), 3, border_radius=16)
        self.draw_text("GAME OVER", FONT_HUGE, (255,0,85), WINDOW_WIDTH//2, y+52, center=True)
        self.draw_text(f"Score Final: {self.score}", FONT_MEDIUM, TEXT, WINDOW_WIDTH//2, y+108, center=True)
        if challenge:
            self.draw_text("TOP 10 — MODO DESAFIO", FONT_MEDIUM, (0,240,255), WINDOW_WIDTH//2, y+154, center=True)
            row_y=y+190
            for i,item in enumerate(self.challenge_scores[:10],1):
                name=str(item.get("name","PLAYER"))[:16]
                score=int(item.get("score",0))
                date=str(item.get("date",""))[:10]
                line=f"{i:02d}. {name:<16}  {score:>7}  {date}"
                self.draw_text(line,FONT_SMALL,(220,220,235),x+38,row_y)
                row_y += 32
            if not self.challenge_scores:
                self.draw_text("Nenhum score registrado.",FONT_SMALL,(160,160,192),WINDOW_WIDTH//2,row_y,center=True)
            self.draw_text("[ R ] Reiniciar   [ V ] Menu", FONT_SMALL, (208,208,224), WINDOW_WIDTH//2, y+h-35, center=True)
        else:
            self.draw_text("[ R ]  Reiniciar Partida", FONT_SMALL, (208,208,224), WINDOW_WIDTH//2, y+205, center=True)
            self.draw_text("[ V ]  Voltar ao Menu Principal", FONT_SMALL, (208,208,224), WINDOW_WIDTH//2, y+244, center=True)

    def draw_badge(self, text, x, y, w, h, active=False):
        bg = (26, 26, 40)
        border = (0, 240, 255) if active else (58, 58, 94)
        pygame.draw.rect(self.screen, bg, (x, y, w, h), border_radius=8)
        pygame.draw.rect(self.screen, border, (x, y, w, h), 1 if not active else 2, border_radius=8)
        # Encurta rótulos muito longos sem produzir glifos quebrados.
        shown = text if len(text) <= 25 else text[:23] + ".."
        self.draw_text(shown, FONT_SMALL, (224, 224, 232), x + w // 2, y + h // 2, center=True)

    def draw_controls(self):
        self.screen.fill((8, 8, 16))
        if self.menu_background is not None:
            self.screen.blit(self.menu_background, (0, 0))

        # Overlay exclusivo e denso: isola completamente a arte/logo da capa.
        shade = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        shade.fill((5, 5, 12, 235))  # ~92%
        self.screen.blit(shade, (0, 0))

        cx = WINDOW_WIDTH // 2
        for ox, oy in ((-2,0),(2,0),(0,-2),(0,2)):
            self.draw_text("CONTROLES", FONT_HUGE, (0, 75, 88), cx+ox, 48+oy, center=True)
        self.draw_text("CONTROLES", FONT_HUGE, (0, 240, 255), cx, 48, center=True)

        # Dica compacta para nunca ultrapassar a janela.
        hint_font = pygame.font.SysFont("consolas,couriernew,arial", 12, bold=True)
        self.draw_text("[↑/↓] Navegar  •  [ENTER] Mudar  •  [R] Resetar",
                       hint_font, (160,160,192), cx, 88, center=True)

        # 89% da largura, centralizada e com margens simétricas.
        table_w = int(WINDOW_WIDTH * 0.89)
        table_x = (WINDOW_WIDTH - table_w) // 2
        table_y = 116
        header_h = 38
        row_h = 66
        row_gap = 8

        action_w = int(table_w * 0.38)
        keyboard_w = int(table_w * 0.31)
        gamepad_w = table_w - action_w - keyboard_w

        pygame.draw.rect(self.screen, (10,10,22), (table_x,table_y,table_w,header_h), border_radius=10)
        pygame.draw.rect(self.screen, (58,58,94), (table_x,table_y,table_w,header_h), 1, border_radius=10)

        self.draw_text("AÇÃO", hint_font, (160,160,192), table_x+18, table_y+12)
        self.draw_text("TECLADO", hint_font, (160,160,192),
                       table_x+action_w+keyboard_w//2, table_y+19, center=True)
        self.draw_text("GAMEPAD", hint_font, (160,160,192),
                       table_x+action_w+keyboard_w+gamepad_w//2, table_y+19, center=True)

        action_font = pygame.font.SysFont("consolas,couriernew,arial", 13, bold=True)
        badge_font = pygame.font.SysFont("consolas,couriernew,arial", 12, bold=True)

        for i, (action, label) in enumerate(self.control_actions):
            y = table_y + header_h + 6 + i*(row_h+row_gap)
            selected = i == self.control_selection
            editing = self.control_capture == action

            row = pygame.Surface((table_w,row_h), pygame.SRCALPHA)
            if editing:
                row.fill((255,0,127,28))
            elif selected:
                row.fill((0,240,255,25))
            elif i % 2:
                row.fill((255,255,255,8))
            self.screen.blit(row,(table_x,y))

            border=(255,0,127) if editing else (0,240,255) if selected else (42,42,64)
            pygame.draw.rect(self.screen,border,(table_x,y,table_w,row_h),
                             2 if (selected or editing) else 1,border_radius=6)
            pygame.draw.line(self.screen,(42,42,64),(table_x+action_w,y+5),(table_x+action_w,y+row_h-5))
            pygame.draw.line(self.screen,(42,42,64),(table_x+action_w+keyboard_w,y+5),
                             (table_x+action_w+keyboard_w,y+row_h-5))

            if selected:
                self.draw_text(">", action_font, (255,0,127) if editing else (0,240,255),
                               table_x+9, y+25)

            action_color=(255,0,127) if editing else (0,240,255) if selected else (224,224,224)
            # Área da ação tem padding à direita de 12 px.
            max_action_px = action_w - 44
            shown = label
            while shown and action_font.size(shown)[0] > max_action_px:
                shown = shown[:-1]
            if shown != label and len(shown) > 2:
                shown = shown[:-2] + ".."
            surf = action_font.render(shown, True, action_color)
            self.screen.blit(surf,(table_x+27, y+(row_h-surf.get_height())//2))

            # Badges uniformes, preenchendo a largura útil de cada célula.
            pad_x = 10
            badge_y, badge_h = y+13, 40
            kb_x = table_x+action_w+pad_x
            kb_w = keyboard_w-2*pad_x
            gp_x = table_x+action_w+keyboard_w+pad_x
            gp_w = gamepad_w-2*pad_x

            def badge(text, bx, bw, active=False):
                pygame.draw.rect(self.screen,(26,26,40),(bx,badge_y,bw,badge_h),border_radius=8)
                bc=(255,0,127) if active else (58,58,94)
                pygame.draw.rect(self.screen,bc,(bx,badge_y,bw,badge_h),2 if active else 1,border_radius=8)
                value=text
                limit=bw-20
                while value and badge_font.size(value)[0] > limit:
                    value=value[:-1]
                if value != text and len(value)>2:
                    value=value[:-2]+".."
                vs=badge_font.render(value,True,(224,224,232))
                self.screen.blit(vs,(bx+(bw-vs.get_width())//2,badge_y+(badge_h-vs.get_height())//2))

            badge(self.keyboard_binding_label(action),kb_x,kb_w)

            blink=int(self.title_timer*3)%2==0
            if editing:
                gp_text="PRESSIONE..." if blink else "AGUARDANDO..."
            else:
                gp_text=self.binding_label(action)
            badge(gp_text,gp_x,gp_w,editing)

        # Rodapé limpo e contido.
        footer=pygame.Surface((WINDOW_WIDTH,38),pygame.SRCALPHA)
        footer.fill((5,5,12,235))
        self.screen.blit(footer,(0,WINDOW_HEIGHT-38))
        esc=badge_font.render("[ ESC ] Voltar ao Menu",True,(208,208,224))
        self.screen.blit(esc,(WINDOW_WIDTH-esc.get_width()-28,WINDOW_HEIGHT-27))

        if self.controls_toast_timer > 0 and self.controls_toast:
            tw,th=min(390,WINDOW_WIDTH-64),42
            tx,ty=(WINDOW_WIDTH-tw)//2,WINDOW_HEIGHT-88
            pygame.draw.rect(self.screen,(15,20,28),(tx,ty,tw,th),border_radius=10)
            pygame.draw.rect(self.screen,(0,240,255),(tx,ty,tw,th),2,border_radius=10)
            self.draw_text(self.controls_toast,badge_font,(224,240,245),cx,ty+21,center=True)

    def init_pillar_blocks(self):
        self.pillar_blocks = []
        colors = [(0,240,255), (255,0,127), (180,0,255), (0,255,140)]
        for side in (-1, 1):
            for _ in range(12):
                self.pillar_blocks.append({
                    "side": side,
                    "x": random.random(),
                    "y": random.random(),
                    "speed": random.uniform(0.035, 0.10),
                    "size": random.randint(10, 22),
                    "color": random.choice(colors),
                    "shape": random.choice(("I","O","T","L")),
                })

    def toggle_fullscreen(self):
        if self.fullscreen:
            self.window = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
            self.fullscreen = False
        else:
            self.windowed_size = self.window.get_size()
            self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.fullscreen = True
        self.pillar_background_size = None

    def update_pillar_blocks(self, dt):
        for block in self.pillar_blocks:
            block["y"] += block["speed"] * dt * 10
            if block["y"] > 1.12:
                block["y"] = -0.12
                block["x"] = random.random()

    def get_viewport(self):
        ww, wh = self.window.get_size()
        scale = min(ww / WINDOW_WIDTH, wh / WINDOW_HEIGHT)
        vw, vh = max(1, int(WINDOW_WIDTH * scale)), max(1, int(WINDOW_HEIGHT * scale))
        return (ww-vw)//2, (wh-vh)//2, vw, vh

    def build_pillar_background(self):
        size = self.window.get_size()
        if self.pillar_background is not None and self.pillar_background_size == size:
            return
        ww, wh = size
        bg = pygame.Surface((ww, wh))
        bg.fill((4, 4, 12))
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "NEON.png")
        try:
            art = pygame.image.load(path).convert()
            # "Blur" cacheado por downscale/upscale; brilho reduzido por máscara.
            small_w, small_h = max(20, ww//28), max(20, wh//28)
            blurred = pygame.transform.smoothscale(art, (small_w, small_h))
            blurred = pygame.transform.smoothscale(blurred, (ww, wh))
            dim = pygame.Surface((ww, wh), pygame.SRCALPHA)
            dim.fill((5, 5, 12, 155))  # ~40% de brilho perceptivo.
            bg.blit(blurred, (0, 0))
            bg.blit(dim, (0, 0))
        except (pygame.error, OSError):
            pass
        self.pillar_background = bg
        self.pillar_background_size = size

    def draw_falling_pillars(self, viewport):
        vx, vy, vw, vh = viewport
        ww, wh = self.window.get_size()
        regions = [(0, vx), (vx+vw, ww-(vx+vw))]
        shapes = {
            "I": ((0,0),(0,1),(0,2),(0,3)),
            "O": ((0,0),(1,0),(0,1),(1,1)),
            "T": ((0,0),(1,0),(2,0),(1,1)),
            "L": ((0,0),(0,1),(0,2),(1,2)),
        }
        for b in self.pillar_blocks:
            rx, rw = regions[0 if b["side"] < 0 else 1]
            if rw < 8:
                continue
            cell = b["size"]
            x = rx + int(b["x"] * max(1, rw-cell*3))
            y = int(b["y"] * wh)
            surf = pygame.Surface((cell*4, cell*4), pygame.SRCALPHA)
            for sx, sy in shapes[b["shape"]]:
                pygame.draw.rect(surf, (*b["color"], 64),
                                 (sx*cell, sy*cell, cell-2, cell-2), border_radius=3)
                pygame.draw.rect(surf, (*b["color"], 95),
                                 (sx*cell, sy*cell, cell-2, cell-2), 1, border_radius=3)
            self.window.blit(surf, (x, y))

        # Divisores neon entre viewport e pilares.
        if vx > 0:
            for x, color in ((vx-1,(0,240,255)), (vx+vw,(255,0,127))):
                glow = pygame.Surface((7, wh), pygame.SRCALPHA)
                pygame.draw.line(glow, (*color,35),(3,0),(3,wh),5)
                self.window.blit(glow,(x-3,0))
                pygame.draw.line(self.window,color,(x,0),(x,wh),1)

    def present(self):
        self.build_pillar_background()
        self.window.blit(self.pillar_background, (0, 0))
        viewport = self.get_viewport()
        self.draw_falling_pillars(viewport)
        vx, vy, vw, vh = viewport
        scaled = pygame.transform.smoothscale(self.screen, (vw, vh))
        self.window.blit(scaled, (vx, vy))
        pygame.display.flip()

    def draw(self):
        if self.state == "menu":
            self.draw_menu()
            self.present()
            return
        if self.state == "controls":
            self.draw_controls()
            self.present()
            return
        if self.state == "name_input":
            self.draw_name_input()
            self.present()
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

        self.present()

    # Entrada
    def handle_keydown(self, key, text=''):
        if self.state == "name_input":
            if key == pygame.K_ESCAPE:
                self.state = "menu"
                self.name_input = ""
            elif key == pygame.K_BACKSPACE:
                self.name_input = self.name_input[:-1]
            elif key == pygame.K_RETURN:
                if self.name_input.strip():
                    self.player_name = self.name_input.strip()[:16]
                    self.reset_game(MODE_DESAFIO)
                    self.state = "playing"
            elif text and text.isprintable() and len(self.name_input) < 16:
                self.name_input += text
            return

        if self.state == "controls":
            if self.control_capture:
                if key == pygame.K_ESCAPE:
                    self.control_capture = None
                return
            if key == pygame.K_ESCAPE:
                self.state = self.controls_return_state
                self.controls_return_state = "menu"
            elif key == pygame.K_UP:
                self.control_selection = (self.control_selection - 1) % len(self.control_actions)
            elif key == pygame.K_DOWN:
                self.control_selection = (self.control_selection + 1) % len(self.control_actions)
            elif key == pygame.K_RETURN:
                self.control_capture = self.control_actions[self.control_selection][0]
            elif key == pygame.K_r:
                self.controller_bindings = self.default_controller_bindings()
                self.save_controller_bindings()
                self.controls_toast = "Controles restaurados para o padrão!"
                self.controls_toast_timer = 2.2
            return

        if self.state == "menu":
            if key == pygame.K_c:
                self.state = "controls"
            elif key in (pygame.K_UP, pygame.K_DOWN):
                self.menu_selection = (self.menu_selection + (-1 if key == pygame.K_UP else 1)) % 3
            elif key == pygame.K_1:
                self.reset_game(MODE_CLASSICO)
                self.state = "playing"
            elif key == pygame.K_2:
                self.reset_game(MODE_CORRIDA)
                self.state = "playing"
            elif key == pygame.K_3:
                self.name_input = ""
                self.state = "name_input"
            elif key == pygame.K_RETURN:
                if self.menu_selection == 2:
                    self.name_input = ""
                    self.state = "name_input"
                else:
                    mode = MODE_CLASSICO if self.menu_selection == 0 else MODE_CORRIDA
                    self.reset_game(mode)
                    self.state = "playing"
            return

        if self.state == "paused":
            if key in (pygame.K_ESCAPE, pygame.K_p):
                self.state = "playing"
                self.pause_selection = 0
            elif key == pygame.K_UP:
                self.pause_selection = (self.pause_selection - 1) % 4
            elif key == pygame.K_DOWN:
                self.pause_selection = (self.pause_selection + 1) % 4
            elif key == pygame.K_c:
                self.controls_return_state = "paused"
                self.state = "controls"
            elif key == pygame.K_r:
                self.reset_game(self.mode)
                self.state = "playing"
                self.pause_selection = 0
            elif key == pygame.K_v:
                self.menu_selection = 0
                self.state = "menu"
                self.pause_selection = 0
            elif key == pygame.K_RETURN:
                if self.pause_selection == 0:
                    self.state = "playing"
                elif self.pause_selection == 1:
                    self.controls_return_state = "paused"
                    self.state = "controls"
                elif self.pause_selection == 2:
                    self.reset_game(self.mode)
                    self.state = "playing"
                else:
                    self.menu_selection = 0
                    self.state = "menu"
                self.pause_selection = 0
            return

        if key in (pygame.K_ESCAPE, pygame.K_p):
            if self.state == "playing":
                self.state = "paused"
                self.pause_selection = 0
            return

        if key == pygame.K_r:
            self.reset_game(self.mode)
            self.state = "playing"
            return

        if key == pygame.K_v:
            self.menu_selection = 0
            self.state = "menu"
            return

        if self.state != "playing":
            return

        if key == pygame.K_LEFT:
            self.move_piece(-1)
        elif key == pygame.K_RIGHT:
            self.move_piece(1)
        elif key in (pygame.K_UP, pygame.K_x):
            self.rotate_piece("cw")
        elif key in (pygame.K_z, pygame.K_LCTRL, pygame.K_RCTRL):
            self.rotate_piece("ccw")
        elif key in (pygame.K_c, pygame.K_LSHIFT, pygame.K_RSHIFT):
            self.hold_current_piece()
        elif key == pygame.K_SPACE:
            self.hard_drop()
    
    def handle_controller_hat(self, value, hat=0):
        if self.state == "paused":
            if value[1] > 0:
                self.pause_selection = (self.pause_selection - 1) % 4
            elif value[1] < 0:
                self.pause_selection = (self.pause_selection + 1) % 4
            return
        if self.state == "menu":
            if value[1] != 0:
                self.menu_selection = (self.menu_selection + (-1 if value[1] > 0 else 1)) % 3
            return
        for action, _ in self.control_actions:
            if action != "soft_drop" and self.binding_matches(action, "hat", hat=hat, value=value):
                self.perform_controller_action(action)

    def handle_controller_button(self, button):
        # START / Menu (SDL mais comum = botão 7) alterna pause.
        if button == 7 and self.state in ("playing", "paused"):
            self.state = "paused" if self.state == "playing" else "playing"
            self.pause_selection = 0
            return
        if self.state == "paused":
            if button == 0:
                if self.pause_selection == 0:
                    self.state = "playing"
                elif self.pause_selection == 1:
                    self.controls_return_state = "paused"
                    self.state = "controls"
                elif self.pause_selection == 2:
                    self.reset_game(self.mode)
                    self.state = "playing"
                else:
                    self.menu_selection = 0
                    self.state = "menu"
                self.pause_selection = 0
            return
        if self.state == "menu":
            if button == 0:
                if self.menu_selection == 2:
                    self.name_input = ""
                    self.state = "name_input"
                else:
                    mode = MODE_CLASSICO if self.menu_selection == 0 else MODE_CORRIDA
                    self.reset_game(mode)
                    self.state = "playing"
            return
        for action, _ in self.control_actions:
            if action != "soft_drop" and self.binding_matches(action, "button", button=button):
                self.perform_controller_action(action)

    def handle_controller_axis(self, joystick, axis, value):
        key = (joystick.get_instance_id(), axis)
        active = abs(value) > 0.7
        if not active:
            self.axis_latched.discard(key)
            return
        if key in self.axis_latched:
            return
        self.axis_latched.add(key)
        for action, _ in self.control_actions:
            if action != "soft_drop" and self.binding_matches(action, "axis", axis=axis, value=value):
                self.perform_controller_action(action)

    # Loop
    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            if self.controls_toast_timer > 0:
                self.controls_toast_timer = max(0.0, self.controls_toast_timer - dt)
            keys = pygame.key.get_pressed()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        self.toggle_fullscreen()
                    else:
                        self.handle_keydown(event.key, event.unicode)
                elif event.type == pygame.VIDEORESIZE and not self.fullscreen:
                    self.windowed_size = (max(640, event.w), max(480, event.h))
                    self.window = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
                    self.pillar_background_size = None
                elif event.type == pygame.JOYDEVICEADDED:
                    self.add_joystick(event.device_index)
                elif event.type == pygame.JOYDEVICEREMOVED:
                    self.remove_joystick(event.instance_id)
                elif event.type in (pygame.JOYHATMOTION, pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION):
                    if self.state == "controls" and self.control_capture:
                        self.capture_controller_event(event)
                        continue
                    if event.type == pygame.JOYHATMOTION:
                        self.handle_controller_hat(event.value, getattr(event, "hat", 0))
                    elif event.type == pygame.JOYBUTTONDOWN:
                        self.handle_controller_button(event.button)
                    else:
                        joystick = self.joysticks.get(event.instance_id)
                        if joystick is not None:
                            self.handle_controller_axis(joystick, event.axis, event.value)

            if self.state == "playing":
                self.update(dt, keys)
            self.update_pillar_blocks(dt)

            self.draw()


if __name__ == "__main__":
    TetrisGame().run()
