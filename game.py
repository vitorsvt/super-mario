import pygame as pg
import utils
from nodes import Root, Tileset, Tilemap, Kinematic, AnimatedSprite, Spritesheet, Camera, StateMachine, Font
from states import Walk, Idle, Jump, Fall, ClimbIdle, ClimbMove, Skid, Dead


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
        self.tilemap, player = self.load_tiled(file)
        self.player = Player((player[0], player[1]))
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
        player = data["layers"][1]["objects"][0]
        return tilemap, (player["x"], player["y"])

    def input(self, events):
        self.player.input(events)

    def physics(self, dt):
        self.player.apply_gravity()
        self.player.physics(dt, self.tilemap)

    def process(self):
        self.player.process()
        self.camera.process()

    def draw(self, surface):
        surface.fill((0,120,255))
        self.entities.fill((0, 0, 0, 0))
        self.player.draw(self.entities)
        self.camera.draw(surface, [self.surface, self.entities])


class Player(Kinematic):
    def __init__(self, position):
        Kinematic.__init__(self, (12, 16), position)
        self.sprite = AnimatedSprite(Spritesheet("assets/mario.png", (16, 24)), {
            "idle": [{"frame": 0, "duration": 1}],
            "walk": [{"frame": 3, "duration": 6}, {"frame": 4, "duration": 6}],
            "run": [{"frame": 3, "duration": 3}, {"frame": 4, "duration": 3}],
            "max_speed": [{"frame": 3, "duration": 3}, {"frame": 4, "duration": 3}],
            "jump": [{"frame": 7, "duration": 1}],
            "fall": [{"frame": 8, "duration": 1}],
            "climb_idle": [{"frame": 10, "duration": 1}],
            "climb_move": [{"frame": 11, "duration": 6}, {"frame": 12, "duration": 6}],
            "skid": [{"frame": 13, "duration": 1}],
            "dead": [{"frame": 14, "duration": 6}, {"frame": 15, "duration": 6}]
        }, "idle")
        self.state = StateMachine(self, [Idle, Walk, Skid, Jump, Fall, ClimbIdle, ClimbMove, Dead], "Idle")
        self.near = []
        self.input_velocity = pg.Vector2(0, 0)
        self.timer = None
        self.walk_max_speed = 1.5
        self.walk_acceleration = 0.05

    def process(self):
        self.state.process()
        self.sprite.next()

    def physics(self, dt, tilemap):
        if not self.state.current("Dead"):
            self.move_and_collide(dt, tilemap)
            self.get_near(tilemap)
        else:
            self.move(dt)

    def input(self, events):
        self.input_velocity.update(0)

        if self.state.current("ClimbIdle") or self.state.current("ClimbMove"):
            self.velocity.update(0)
            if events.is_action_pressed("right"): self.velocity.x = 1
            if events.is_action_pressed("left"): self.velocity.x = -1
            if events.is_action_pressed("down"): self.velocity.y = 1
            if events.is_action_pressed("up"): self.velocity.y = -1
            if events.is_action_just_pressed("jump"):
                self.state.set("Jump")
                self.input_velocity.y = -6
        elif self.state.current("Dead"):
            self.gravity = False
            self.timer += 1
            if self.timer == 60:
                self.input_velocity.y = -4
            elif self.timer > 60:
                self.gravity = True
            else:
                self.sprite.frame = 0
                self.velocity.update(0)
        else:
            if events.is_action_pressed("right"):
                self.input_velocity.x = self.walk_acceleration
                self.sprite.flip_h = True
            elif self.velocity.x > 0:
                self.velocity.x = max(self.velocity.x - self.walk_acceleration, 0)

            if events.is_action_pressed("left"):
                self.input_velocity.x = -self.walk_acceleration
                self.sprite.flip_h = False
            elif self.velocity.x < 0:
                self.velocity.x = min(self.velocity.x + self.walk_acceleration, 0)

            if self.grounded and events.is_action_just_pressed("jump"):
                self.input_velocity.y = -6
            if events.is_action_just_released("jump"):
                if self.velocity.y < -3:
                    self.velocity.y = -3

            if events.is_action_pressed("up") or events.is_action_pressed("down"):
                if self.is_near("ladder"):
                    self.state.set("ClimbIdle")

        self.velocity += self.input_velocity
        self.velocity.x = utils.clamp(
            self.velocity[0],
            -self.walk_max_speed, self.walk_max_speed
        )

    def draw(self, surface):
        x = self.shape.x - (self.sprite.texture.get_width() - self.shape.w) / 2
        y = self.shape.y - (self.sprite.texture.get_height() - self.shape.h)
        self.sprite.draw(surface, (x, y))

    def is_near(self, tag):
        return tag in self.near

    def get_near(self, tilemap):
        self.near = []
        points = [
            self.shape.midtop, self.shape.midbottom,
            self.shape.topleft, self.shape.midleft, self.shape.bottomleft,
            self.shape.topright, self.shape.midright, self.shape.bottomright
        ]

        for point in points:
            x = point[0] // 16
            y = point[1] // 16
            tile = tilemap.get_info_at(x, y)
            if tile:
                if tile.has("ladder"):
                    self.near.append("ladder")
                if tile.has("damage"):
                    self.state.set("Dead")
        if self.shape.top > tilemap.size[1]:
            self.state.set("Dead")
