# Neon Tetris

Neon Tetris is a 2D game inspired by the classic Tetris, developed in Python using the Pygame library. The project applies graphical primitives, game loop structure, and core programming concepts, while introducing additional gameplay mechanics such as dynamic challenges and variable gravity.

---

## Features

- Classic Tetris gameplay (10x20 grid)
- Two game modes:
  - Classic Mode
  - Race Mode with dynamic challenges
- Variable gravity system (slow, normal, fast)
- Locked pieces mechanic
- Ghost piece (landing preview)
- Next piece preview with status and gravity indicator
- Score and level progression system
- Temporary challenge system in Race Mode:
  - Obstacle barrier (temporary horizontal wall with gaps)
  - Speed boost (increased falling speed)
- Animated UI elements and neon visual style
- Pause, restart and return-to-menu controls

---

## Technologies

- Python 3
- Pygame

---

## Project Structure

neon-tetris-mari
│
├── main.py
├── settings.py
├── pieces.py
├── assets/
│   └── blocks/
└── README.md

---

## How to Run

1. Clone the repository:

git clone https://github.com/Maria-Borelli/neon-tetris.git

2. Navigate to the project folder:

cd neon-tetris-mari

3. Install dependencies:

pip install pygame

4. Run the game:

python main.py

---

## Controls

Menu
- Up / Down: navigate options
- Enter: confirm selection
- 1: start Classic Mode
- 2: start Race Mode

Gameplay
- Left / Right: move piece
- Up or X: rotate clockwise
- Z: rotate counterclockwise
- Down: soft drop
- Space: hard drop
- P: pause / resume
- R: restart game
- V: return to main menu

---

## Game Mechanics

Gravity System  
Each piece spawns with a random gravity type:
- Slow: reduced falling speed
- Normal: standard speed
- Fast: increased falling speed

Locked Pieces  
Some pieces become restricted when touching the ground, reducing lateral movement.

Challenge System (Race Mode)  
Dynamic challenges are triggered over time:

Obstacles  
Temporary horizontal barrier appears with gaps for passage.

Speed  
Falling speed is temporarily increased.

Challenge frequency and duration scale with the level.

---

## Scoring System

- Single line: 100 points
- Double line: 300 points
- Triple line: 500 points
- Tetris (4 lines): 800 points
- Hard drop: points per cell
- Soft drop: points per cell

Level increases every 10 cleared lines.

---

## Objective

Stack and place pieces to complete horizontal lines and prevent the board from filling up. In Race Mode, adapt to dynamic challenges and increasing difficulty.

---

## Author

Maria Clara

---

## Notes

This project was developed as part of an academic assignment focused on graphical primitives and game logic implementation.
