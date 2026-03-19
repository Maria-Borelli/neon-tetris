"""
Configuração dos desafios do Modo Corrida.
Altere os valores abaixo para personalizar a experiência.
"""

# ============================================
#   ATIVAR / DESATIVAR DESAFIOS
# ============================================

CHALLENGE_OBSTACLES_ENABLED = True      # Blocos-obstáculo no tabuleiro
CHALLENGE_SPEED_ENABLED = True          # Aceleração temporária de queda

# ============================================
#   TEMPOS E INTERVALOS
# ============================================

# Intervalo base entre desafios (segundos)
CHALLENGE_INTERVAL = 14.0

# Redução do intervalo por nível (seg/nível)
CHALLENGE_INTERVAL_LEVEL_REDUCTION = 0.6

# Intervalo mínimo entre desafios (segundos)
CHALLENGE_INTERVAL_MIN = 6.0

# Duração de cada desafio ativo (segundos)
CHALLENGE_DURATION = 8.0

# Duração mínima do desafio (segundos)
CHALLENGE_DURATION_MIN = 4.0

# Redução da duração por nível (seg/nível)
CHALLENGE_DURATION_LEVEL_REDUCTION = 0.3

# ============================================
#   OBSTÁCULOS
# ============================================

# Quantidade base de blocos-obstáculo por onda
OBSTACLE_COUNT_BASE = 2

# Blocos extras a cada 3 níveis
OBSTACLE_COUNT_PER_LEVEL = 1

# Máximo de blocos por onda
OBSTACLE_COUNT_MAX = 5

# ============================================
#   VELOCIDADE
# ============================================

# Multiplicador de velocidade de queda durante o desafio
SPEED_CHALLENGE_MULTIPLIER = 3.0
