import random

SHAPES = {
    "I": [
        [
            "....",
            "XXXX",
            "....",
            "...."
        ],
        [
            "..X.",
            "..X.",
            "..X.",
            "..X."
        ]
    ],
    "O": [
        [
            ".XX.",
            ".XX.",
            "....",
            "...."
        ]
    ],
    "T": [
        [
            ".X..",
            "XXX.",
            "....",
            "...."
        ],
        [
            ".X..",
            ".XX.",
            ".X..",
            "...."
        ],
        [
            "....",
            "XXX.",
            ".X..",
            "...."
        ],
        [
            ".X..",
            "XX..",
            ".X..",
            "...."
        ]
    ],
    "S": [
        [
            ".XX.",
            "XX..",
            "....",
            "...."
        ],
        [
            ".X..",
            ".XX.",
            "..X.",
            "...."
        ]
    ],
    "Z": [
        [
            "XX..",
            ".XX.",
            "....",
            "...."
        ],
        [
            "..X.",
            ".XX.",
            ".X..",
            "...."
        ]
    ],
    "J": [
        [
            "X...",
            "XXX.",
            "....",
            "...."
        ],
        [
            ".XX.",
            ".X..",
            ".X..",
            "...."
        ],
        [
            "....",
            "XXX.",
            "..X.",
            "...."
        ],
        [
            ".X..",
            ".X..",
            "XX..",
            "...."
        ]
    ],
    "L": [
        [
            "..X.",
            "XXX.",
            "....",
            "...."
        ],
        [
            ".X..",
            ".X..",
            ".XX.",
            "...."
        ],
        [
            "....",
            "XXX.",
            "X...",
            "...."
        ],
        [
            "XX..",
            ".X..",
            ".X..",
            "...."
        ]
    ],
}


class Piece:
    def __init__(self, shape_key, gravity_type="normal", position_locked=False):
        self.shape_key = shape_key
        self.rotations = SHAPES[shape_key]
        self.rotation = 0
        self.x = 3
        self.y = 0

        self.gravity_type = gravity_type
        self.gravity_mult = {
            "slow": 0.5,
            "normal": 1.0,
            "fast": 2.0
        }[gravity_type]

        self.position_locked = position_locked
        self.touching_ground = False

    @property
    def matrix(self):
        return self.rotations[self.rotation]

    def rotate_cw(self):
        self.rotation = (self.rotation + 1) % len(self.rotations)

    def rotate_ccw(self):
        self.rotation = (self.rotation - 1) % len(self.rotations)


def random_shape_key():
    return random.choice(list(SHAPES.keys()))