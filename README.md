# Neon Tetris

Neon Tetris é um jogo 2D inspirado no clássico Tetris, desenvolvido em Python com a biblioteca Pygame. O projeto aplica primitivas gráficas, estrutura de game loop e conceitos fundamentais de programação, com mecânicas adicionais como desafios dinâmicos e gravidade variável.

---

## Funcionalidades

- Gameplay clássico de Tetris (grade 10×20)
- Dois modos de jogo:
  - Modo Clássico
  - Modo Corrida com desafios dinâmicos
- Sistema de gravidade variável (lenta, normal, rápida)
- Mecânica de peças travadas
- Peça fantasma (prévia de aterrissagem)
- Prévia da próxima peça com indicador de status e gravidade
- Sistema de pontuação e progressão de nível
- Sistema de desafios temporários no Modo Corrida:
  - Barreira obstáculo (parede horizontal temporária com lacunas)
  - Turbo de velocidade (queda acelerada temporária)
- Elementos de UI animados e estilo visual neon
- Controles de pausa, reinício e retorno ao menu

---

## Tecnologias

- Python 3
- Pygame

---

## Estrutura do Projeto

neon-tetris-mari
│
├── main.py
├── settings.py
├── pieces.py
├── assets/
│   └── blocks/
└── README.md

---

## Requisitos
[Python](https://www.python.org/downloads/windows/) 3.12.X

## Como Executar

1. Clone o repositório:

git clone https://github.com/Maria-Borelli/neon-tetris.git

2. Acesse a pasta do projeto:

cd neon-tetris

3. Instale as dependências:

pip install pygame

4. Execute o jogo:

python main.py

---

## Controles

Menu
- Seta Cima / Baixo ou analógico: navegar entre opções
- Enter ou botão A: confirmar seleção
- C ou botão B: abrir a tela de controles
- 1: iniciar Modo Clássico
- 2: iniciar Modo Corrida

Gameplay
- Esquerda / Direita ou analógico: mover peça
- Cima sempre gira a peça no sentido horário
- Z: rotacionar no sentido anti-horário
- Baixo: queda suave (soft drop)
- Espaço ou botão B: queda instantânea (hard drop)
- P: pausar / continuar
- R: reiniciar partida
- V: voltar ao menu principal

Controle / Gamepad
- D-Pad e analógico esquerdo controlam a navegação e o movimento
- Cima gira a peça no sentido horário
- A: confirmar / inserir nos menus
- B: voltar / apagar no menu de nome
- Start: confirmar em menus e pausar durante a partida
- Os menus principal, pausa, controles, game over e nome aceitam controle/gamepad/joystick

---

## Mecânicas do Jogo

Sistema de Gravidade  
Cada peça é gerada com um tipo de gravidade aleatório:
- Lenta: velocidade de queda reduzida
- Normal: velocidade padrão
- Rápida: velocidade de queda aumentada

Peças Travadas  
Algumas peças ficam restritas ao tocar o chão, reduzindo a movimentação lateral.

Sistema de Desafios (Modo Corrida)  
Desafios dinâmicos são ativados periodicamente:

Obstáculos  
Barreira horizontal temporária aparece com lacunas para passagem.

Velocidade  
A velocidade de queda é temporariamente aumentada.

A frequência e duração dos desafios escalam com o nível.

---

## Sistema de Pontuação

- 1 linha: 100 pontos
- 2 linhas: 300 pontos
- 3 linhas: 500 pontos
- Tetris (4 linhas): 800 pontos
- Hard drop: pontos por célula
- Soft drop: pontos por célula

O nível sobe a cada 10 linhas eliminadas.

---

## Objetivo

Empilhar e posicionar peças para completar linhas horizontais e evitar que o tabuleiro encha. No Modo Corrida, adapte-se aos desafios dinâmicos e à dificuldade crescente.

---

## Autores

Maria Clara,
Lauan Amorim

---

## Observações

Este projeto foi desenvolvido como parte de um trabalho acadêmico com foco em primitivas gráficas e implementação de lógica de jogos.


## Controles

O jogo aceita teclado e controles compatíveis com o sistema de joystick/SDL do Pygame.

| Ação | Teclado | Controle |
| --- | --- | --- |
| Mover à esquerda | ← | D-Pad ← |
| Mover à direita | → | D-Pad → |
| Soft Drop | ↓ | D-Pad ↓ |
| Hard Drop | Espaço | D-Pad ↑ ou gatilho |
| Rotação horária | ↑ ou X | Botão de ação principal |
| Rotação anti-horária | Z ou Ctrl | Botão de ação secundário/esquerdo |
| Hold | C ou Shift | LB/L1/L ou RB/R1/R |

O Hold pode ser usado uma vez por peça e volta a ficar disponível depois que a peça atual é travada no tabuleiro.
