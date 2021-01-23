import pygame as pg
import time, sys


class Engine:
    def __init__(self, resolution, scale = 1):
        pg.init()
        pg.display.set_caption("Super Mario")

        self.surface = pg.Surface(resolution)
        self.screen = pg.display.set_mode(
            (resolution[0] * scale, resolution[1] * scale), 0, 32
        )

        self.clock = pg.time.Clock()
        self.dt = 0

        self.events = Events()
        self.root = None

    def start(self):
        while True:
            self.events.update()
            self.root.input(self.events)
            self.root.physics(self.dt)
            self.root.process()
            self.root.draw(self.surface)
            self.screen.blit(pg.transform.scale(self.surface, self.screen.get_size()), (0, 0))
            self.tick()

    def tick(self):
        pg.display.update()
        self.dt = (self.clock.tick(60) * 0.001) * 60


class Events:
    def __init__(self):
        self.mappings = {
            pg.K_UP: "up",
            pg.K_LEFT: "left",
            pg.K_DOWN: "down",
            pg.K_RIGHT: "right",
            pg.K_z: "jump",
            pg.K_x: "spin",
            pg.K_a: "run",
            pg.K_s: "interact"
        }
        self.pressed = []
        self.just_pressed = []

    def update(self):
        self.just_pressed = []
        for event in pg.event.get():
            if event.type is pg.QUIT:
                pg.quit()
                sys.exit()
            elif event.type in [pg.KEYDOWN, pg.KEYUP] and event.key in self.mappings.keys():
                action = self.mappings[event.key]
                if event.type == pg.KEYDOWN:
                    if action not in self.pressed: self.pressed.append(action)
                    if action not in self.just_pressed: self.just_pressed.append(action)
                else:
                    if action in self.pressed: self.pressed.remove(action)

    def is_action_pressed(self, action):
        if action in self.pressed:
            return True
        return False

    def is_action_just_pressed(self, action):
        if action in self.just_pressed:
            return True
        return False
