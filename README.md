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
[Python](https://www.python.org/downloads/windows/) 13.12.X

## Como Executar

1. Clone o repositório:

git clone https://github.com/Maria-Borelli/neon-tetris.git

2. Acesse a pasta do projeto:

cd neon-tetris-mari

3. Instale as dependências:

pip install pygame

4. Execute o jogo:

python main.py

---

## Controles

Menu
- Seta Cima / Baixo: navegar entre opções
- Enter: confirmar seleção
- 1: iniciar Modo Clássico
- 2: iniciar Modo Corrida

Gameplay
- Seta Esquerda / Direita: mover peça
- Seta Cima ou X: rotacionar no sentido horário
- Z: rotacionar no sentido anti-horário
- Seta Baixo: queda suave (soft drop)
- Espaço: queda instantânea (hard drop)
- P: pausar / continuar
- R: reiniciar partida
- V: voltar ao menu principal

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
