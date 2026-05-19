import random


class Color:
    color = None
    alpha = None
    clues = None

    def __init__(self, color, alpha, clues):
        self.color = color
        self.alpha = alpha
        self.clues = clues


class ColorList:
    cList = [
        Color((0.35, 0.77, 0.96, 1.0), 1.0, ["safezone"]),
        Color((0.85, 0.65, 0.49, 1.0), 1.0, ["skin"]),
        Color((0.5, 0.5, 0.5, 1.0), 1.0, ["skull"]),
        Color((0.5, 0.5, 0.5, 1.0), 1.0, ["bone"]),
        Color((0.94, 0.59, 0.56, 1.0), 1.0, ["cerebrum"]),
        Color((0.64, 0.35, 0.33, 1.0), 1.0, ["brainstem"]),
        Color((0.94, 0.59, 0.56, 1.0), 1.0, ["brain"]),
        Color((0.79, 0.00, 0.04, 1.0), 1.0, ["tumor"]),
        Color((0.16, 0.28, 0.54, 1.0), 1.0, ["sinus"]),
        Color((0.35, 0.77, 0.96, 1.0), 1.0, ["ventricles"]),
        Color((0.44, 0.00, 0.11, 1.0), 1.0, ["vessel"]),
        Color((0.89, 0.51, 0.57, 1.0), 1.0, ["cerebellum"]),
        Color((0.988, 0.655, 0.851, 1.0), 1.0, ["globus"]),
        Color((0.820, 0.510, 0.329, 1.0), 1.0, ["orbit"]),
        Color((1.000, 0.235, 0.0, 1.000), 1.0, ["nucleus"]),
        Color((0.831, 0.922, 0.035, 1.0), 1.0, ["optic"]),
        Color((0.980, 0.918, 0.020, 1.0), 1.0, ["eye"]),
        Color((0.090, 0.251, 0.341, 1.0), 1.0, ["chiasm"]),
        Color((0.1, 0.1, 0.1, 1.0), 1.0, ["ac"]),
        Color((0.1, 0.1, 0.1, 1.0), 1.0, ["pc"])
    ]

    def getColorList(self):
        return self.cList

    def defaultColor_opaque(self):
        default_color_opaque = (0.0, random.uniform(0.15, 0.85), random.uniform(0.15, 0.85), 1.0)
        return default_color_opaque

    def nerveColor_opaque(self):
        nerve_color_opaque = (1.0, random.uniform(0.55, 0.85), 0.0, 1.0)
        return nerve_color_opaque

    def defaultAlpha_opaque(self):
        default_alpha_opaque = 1.0
        return default_alpha_opaque
