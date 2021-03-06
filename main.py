import pygame as pg
from engine import Engine
from game import Level


def main():
    engine = Engine((256, 224), 2)
    level = Level.from_tiled("level.json")
    engine.root = level
    engine.start()


if __name__ == "__main__":
    main()
