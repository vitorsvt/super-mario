import pygame as pg
from nodes import Root


class Level(Root):
    def __init__(self):
        self.surface = pg.Surface((256, 224))
        self.count = 150

    def input(self, events):
        if events.is_action_just_pressed("jump"):
            print("jump")
        for key in ["up", "down", "left", "right"]:
            if events.is_action_pressed(key): print(key)

    def physics(self, dt):
        pass

    def process(self):
        pass

    def draw(self, surface):
        if self.count == 0:
            self.surface.fill((255,0,0))
            self.count = 150
        elif self.count == 50:
            self.surface.fill((0,255,0))
        elif self.count == 100:
            self.surface.fill((0,0,255))
        self.count -= 1
        surface.blit(self.surface, (0,0))
