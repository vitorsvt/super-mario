import pygame as pg
import utils
from nodes import Root, Tileset, Tilemap, Kinematic, AnimatedSprite, Spritesheet, Camera


class FollowCamera(Camera):
    def __init__(self, target, size, limits):
        Camera.__init__(self, size, limits)
        self.target = target
        self.fixed = "left"
        self.margins = [
            self.shape.centerx - 32,
            self.shape.centerx - 16,
            self.shape.centerx + 16,
            self.shape.centerx + 32
        ]

    def process(self):
        if self.shape.x + self.margins[0] >= self.target.shape.left:
            if not self.fixed: self.fixed = "left"
            else: self.fixed = "right"
        elif self.shape.x + self.margins[3] <= self.target.shape.right:
            if not self.fixed: self.fixed = "right"
            else: self.fixed = "left"

        if self.fixed == "left":
            if self.target.shape.left >= self.shape.x + self.margins[1]:
                distance = self.target.shape.left - self.margins[1] - self.shape.x
                self.shape.x += min(3, distance)
        elif self.fixed == "right":
            if self.target.shape.right <= self.shape.x + self.margins[2]:
                distance = self.target.shape.right - self.margins[2] - self.shape.x
                self.shape.x += max(-3, distance)

        if self.snap_limits()[0]:
            self.fixed = None


class Level(Root):
    def __init__(self, file):
        self.tilemap = self.load_tiled(file)
        self.player = Player()
        self.camera = FollowCamera(self.player, (256, 224), self.tilemap.size)

        self.surface = pg.Surface(self.tilemap.size, pg.HWSURFACE + pg.SRCALPHA)
        self.entities = pg.Surface(self.tilemap.size, pg.HWSURFACE + pg.SRCALPHA)


        self.surface.blit(self.tilemap.surface, (0, 0))

    def load_tiled(self, file):
        data = utils.load_json(file)
        tileset_data = data["tilesets"][0]
        tileset = Tileset(
            tileset_data["image"], tileset_data["tilewidth"],
            tileset_data["tiles"], tileset_data["margin"],
            tileset_data["spacing"], tileset_data["transparentcolor"]
        )
        tilemap_data = data["layers"][0]
        tilemap = Tilemap(
            tileset,
            [tilemap_data["width"], tilemap_data["height"]],
            tilemap_data["data"]
        )
        return tilemap

    def input(self, events):
        self.player.input(events)

    def physics(self, dt):
        self.player.move_and_collide(dt, self.tilemap)

    def process(self):
        self.player.process()
        self.camera.process()

    def draw(self, surface):
        surface.fill((0,120,255))
        self.entities.fill((0, 0, 0, 0))
        self.player.draw(self.entities)
        self.camera.draw(surface, [self.surface, self.entities])


class Player(Kinematic):
    def __init__(self):
        Kinematic.__init__(self, pg.Rect(0, 0, 12, 16))
        spritesheet = Spritesheet("assets/mario.png", (16, 24))
        self.sprite = AnimatedSprite(spritesheet, {
            "idle": [{"frame": 0, "duration": 1}],
            "walk": [{"frame": 3, "duration": 6}, {"frame": 4, "duration": 6}],
            "run": [{"frame": 3, "duration": 3}, {"frame": 4, "duration": 3}],
            "max_speed": [{"frame": 3, "duration": 3}, {"frame": 4, "duration": 3}],
            "jump": [{"frame": 7, "duration": 1}],
            "fall": [{"frame": 8, "duration": 1}],
            "climb_idle": [{"frame": 10, "duration": 1}],
            "climb_move": [{"frame": 11, "duration": 6}, {"frame": 12, "duration": 6}],
            "skid": [{"frame": 13, "duration": 1}]
        }, "idle")
        self.walk_max = 1.5
        self.walk_accel = 0.05
        self.skid = None

    def draw(self, surface):
        self.sprite.draw(surface, (self.shape.topleft[0] - 2, self.shape.topleft[1] - 8))

    def process(self):
        self.sprite.play("idle")

        if self.velocity[0] != 0:
            self.sprite.play("walk")

        if self.velocity[0] > 0:
            self.sprite.flip_h = True
        elif self.velocity[0] < 0:
            self.sprite.flip_h = False

        if self.skid == "right":
            self.sprite.play("skid")
            self.sprite.flip_h = True
        elif self.skid == "left":
            self.sprite.play("skid")
            self.sprite.flip_h = False

        if self.velocity[1] > 0:
            self.sprite.play("fall")
        elif self.velocity[1] < 0:
            self.sprite.play("jump")

        self.sprite.next()

    def input(self, events):
        self.skid = None

        if events.is_action_pressed("right"):
            self.velocity[0] = min(self.velocity[0] + self.walk_accel, self.walk_max)

        elif self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - self.walk_accel, 0)
            if events.is_action_pressed("left"):
                self.skid = "left"

        if events.is_action_pressed("left"):
            self.velocity[0] = max(self.velocity[0] - self.walk_accel, -self.walk_max)

        elif self.velocity[0] < 0:
            self.velocity[0] = min(self.velocity[0] + self.walk_accel, 0)
            if events.is_action_pressed("right"):
                self.skid = "right"

        self.velocity[1] = min(self.velocity[1] + 0.2, 10)

        if self.grounded and events.is_action_pressed("jump"):
            self.velocity[1] = -6
        if events.is_action_just_released("jump"):
            if self.velocity[1] < -3:
                self.velocity[1] = -3
