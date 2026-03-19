import pygame

#   TABULEIRO  
CELL_SIZE = 32
COLS = 10
ROWS = 20

PLAY_WIDTH = COLS * CELL_SIZE
PLAY_HEIGHT = ROWS * CELL_SIZE

#   ÁREA EXTRA  
TOP_BAR_HEIGHT = 90
SIDEBAR_WIDTH = 300

WINDOW_WIDTH = PLAY_WIDTH + SIDEBAR_WIDTH
WINDOW_HEIGHT = PLAY_HEIGHT + TOP_BAR_HEIGHT

FPS = 60
TITLE = "Neon Tetris"

#   POSIÇÕES  
PLAY_X = 0
PLAY_Y = TOP_BAR_HEIGHT

SIDEBAR_X = PLAY_WIDTH
SIDEBAR_Y = 0

#   CORES  
BG = (10, 10, 18)
GRID = (35, 35, 50)
BORDER = (90, 90, 120)
TEXT = (235, 235, 245)
MUTED = (150, 150, 170)

GHOST = (180, 180, 255)
OBSTACLE = (255, 90, 180)
OBSTACLE_GLOW = (255, 150, 210)

CHALLENGE_SPEED_COLOR = (255, 180, 30)
CHALLENGE_SPEED_GLOW = (255, 220, 80)

SPEED_SLOW = (80, 200, 255)
SPEED_NORMAL = (180, 180, 180)
SPEED_FAST = (255, 210, 90)

LOCKED_BORDER = (255, 80, 80)

#   JOGO  
BASE_FALL_TIME = 0.60
LOCK_DELAY = 0.45
SOFT_DROP_MULT = 14
LINES_PER_LEVEL = 10

#   MODOS  
MODE_CLASSICO = "clássico"
MODE_CORRIDA = "corrida"

#   GRAVIDADE  
GRAVITY_TYPES = {
    "slow": 0.5,
    "normal": 1.0,
    "fast": 2.0,
}

GRAVITY_COLORS = {
    "slow": SPEED_SLOW,
    "normal": SPEED_NORMAL,
    "fast": SPEED_FAST,
}

#   PONTUAÇÃO  
LINE_CLEAR_POINTS = {
    1: 100,
    2: 300,
    3: 500,
    4: 800
}

HARD_DROP_POINTS_PER_CELL = 2
SOFT_DROP_POINTS_PER_CELL = 1

#   FONTES  
pygame.font.init()
FONT_SMALL = pygame.font.SysFont("couriernew,consolas,arial", 16, bold=True)
FONT_MEDIUM = pygame.font.SysFont("couriernew,consolas,arial", 22, bold=True)
FONT_BIG = pygame.font.SysFont("couriernew,consolas,arial", 28, bold=True)
FONT_HUGE = pygame.font.SysFont("couriernew,consolas,arial", 40, bold=True)

#   ASSETS  
BLOCK_ASSET_DIR = "assets/blocks"

#   DESAFIOS (Modo Corrida)  
# Ativar / desativar desafios
CHALLENGE_OBSTACLES_ENABLED = True      # Blocos-obstáculo no tabuleiro
CHALLENGE_SPEED_ENABLED = True          # Aceleração temporária de queda

# Intervalo base entre desafios (segundos)
CHALLENGE_INTERVAL = 14.0

# Redução do intervalo por nível (seg/nível)
CHALLENGE_INTERVAL_LEVEL_REDUCTION = 0.6

# Intervalo mínimo entre desafios (segundos)
CHALLENGE_INTERVAL_MIN = 6.0

# Duração de cada desafio ativo (segundos)
CHALLENGE_DURATION = 5.0

# Duração mínima do desafio (segundos)
CHALLENGE_DURATION_MIN = 2.5

# Redução da duração por nível (seg/nível)
CHALLENGE_DURATION_LEVEL_REDUCTION = 0.2

# Número de lacunas (buracos) na barreira inicial (para o jogador passar)
BARRIER_GAPS_BASE = 3

# Lacunas mínimas (jogo mais difícil em níveis altos)
BARRIER_GAPS_MIN = 1

# Multiplicador de velocidade de queda durante o desafio
SPEED_CHALLENGE_MULTIPLIER = 3.0
