import pygame as pg
import utils
from nodes import Root, Tileset, Tilemap, Kinematic, AnimatedSprite, Spritesheet, Camera, StateMachine, Font


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
        self.player.physics(dt, self.tilemap)

    def process(self):
        self.player.process()
        self.camera.process()

    def draw(self, surface):
        surface.fill((0,120,255))
        self.entities.fill((0, 0, 0, 0))
        self.player.draw(self.entities)
        self.camera.draw(surface, [self.surface, self.entities])


class PlayerSM(StateMachine):
    def __init__(self, player):
        StateMachine.__init__(self, [
            "idle", "walk", "run", "max_speed", "skid",
            "jump", "fall",
            "climb_idle", "climb_move",
            "dead"
        ], "idle")
        self.player = player

    def process(self):
        if self.state == "idle":
            if self.player.velocity[1] > 0:
                self.set_state("fall")
            elif self.player.velocity[1] < 0:
                self.set_state("jump")
            elif self.player.velocity[0] != 0:
                self.set_state("walk")
        elif self.state == "walk":
            if self.player.velocity[1] > 0:
                self.set_state("fall")
            elif self.player.velocity[1] < 0:
                self.set_state("jump")
            elif self.player.velocity[0] > 0 and self.player.input_velocity[0] < 0:
                self.set_state("skid")
            elif self.player.velocity[0] < 0 and self.player.input_velocity[0] > 0:
                self.set_state("skid")
            elif self.player.velocity[0] == 0:
                self.set_state("idle")
        elif self.state == "fall":
            if self.player.grounded:
                if self.player.velocity[0] != 0 or self.player.input_velocity[0] != 0:
                    self.set_state("walk")
                else:
                    self.set_state("idle")
            elif self.player.velocity[1] < 0:
                self.set_state("jump")
        elif self.state == "jump":
            if self.player.grounded:
                if self.player.velocity[0] != 0 or self.player.input_velocity[0] != 0:
                    self.set_state("walk")
                else:
                    self.set_state("idle")
            elif self.player.velocity[1] >= 0:
                self.set_state("fall")
        elif self.state == "skid":
            if self.player.velocity[1] > 0:
                self.set_state("fall")
            elif self.player.velocity[1] < 0:
                self.set_state("jump")
            elif self.player.velocity[0] * self.player.input_velocity[0] > 0:
                self.set_state("idle")
        elif self.state == "climb_idle":
            if "ladder" not in self.player.near:
                self.set_state("fall")
            elif self.player.velocity != [0, 0]:
                self.set_state("climb_move")
        elif self.state == "climb_move":
            if "ladder" not in self.player.near:
                self.set_state("fall")
            elif self.player.velocity == [0, 0]:
                self.set_state("climb_idle")

    def enter_state(self):
        self.player.state_label = self.player.font.write(self.state.upper())
        self.player.sprite.play(self.state)
        if self.state == "dead":
            self.player.timer = 0


class Player(Kinematic):
    def __init__(self):
        Kinematic.__init__(self, pg.Rect(0, 0, 12, 16))
        spritesheet = Spritesheet("assets/mario.png", (16, 24))
        self.font = Font("assets/font.png", (8,8), "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ.,*_")
        self.sprite = AnimatedSprite(spritesheet, {
            "idle": [{"frame": 0, "duration": 1}],
            "walk": [{"frame": 3, "duration": 6}, {"frame": 4, "duration": 6}],
            "run": [{"frame": 3, "duration": 3}, {"frame": 4, "duration": 3}],
            "max_speed": [{"frame": 3, "duration": 3}, {"frame": 4, "duration": 3}],
            "jump": [{"frame": 7, "duration": 1}],
            "fall": [{"frame": 8, "duration": 1}],
            "climb_idle": [{"frame": 10, "duration": 1}],
            "climb_move": [{"frame": 11, "duration": 6}, {"frame": 12, "duration": 6}],
            "skid": [{"frame": 13, "duration": 1}],
            "dead": [{"frame": 14, "duration": 6, "frame": 15, "duration": 6}]
        }, "idle")

        self.collisions = []
        self.near = []

        self.input_velocity = [0, 0]
        self.state = PlayerSM(self)
        self.state_label = None
        self.timer = None
        self.walk_max = 1.5
        self.walk_accel = 0.05

    def get_collisions(self, tilemap):
        self.collisions = []
        points = [
            self.shape.midtop, self.shape.midbottom,
            self.shape.topleft, self.shape.midleft, self.shape.bottomleft,
            self.shape.topright, self.shape.midright, self.shape.bottomright
        ]

        for point in points:
            x = point[0] // 16
            y = point[1] // 16
            tile = tilemap.get_info_at(x, y)
            if tile and tile not in self.collisions:
                self.collisions.append(tile)

    def check_out_of_bounds(self, tilemap):
        if self.shape.top > tilemap.size[1]:
            self.state.set_state("dead")

    def draw(self, surface):
        self.sprite.draw(surface, (self.shape.topleft[0] - 2, self.shape.topleft[1] - 8))

        if self.state_label:
            surface.blit(self.state_label, (self.shape.midtop[0] - self.state_label.get_width() / 2, self.shape.midtop[1] - self.state_label.get_height() - 2))

    def check_collisions(self):
        self.near = []
        for tile in self.collisions:
            if "damage" in tile.tags:
                self.state.set_state("dead")
            if "ladder" in tile.tags and "ladder" not in self.near:
                self.near.append("ladder")
        print(self.near, self.collisions)

    def physics(self, dt, tilemap):
        if self.state.state != "dead":
            self.move_and_collide(dt, tilemap)
            self.get_collisions(tilemap)
            self.check_out_of_bounds(tilemap)
            self.check_collisions()
        else:
            self.move(dt)

    def process(self):
        self.state.process()
        self.sprite.next()

    def apply_gravity(self):
        self.velocity[1] = min(self.velocity[1] + 0.2, 10)

    def input(self, events):
        self.input_velocity = [0, 0]

        if self.state.state in ["climb_idle", "climb_move"]:
            self.velocity = [0, 0]
            if events.is_action_pressed("right"):
                self.velocity[0] = 1
            if events.is_action_pressed("left"):
                self.velocity[0] = -1
            if events.is_action_pressed("down"):
                self.velocity[1] = 1
            if events.is_action_pressed("up"):
                self.velocity[1] = -1
            if events.is_action_just_pressed("jump"):
                self.state.set_state("jump")
                self.input_velocity[1] = -6
        elif self.state.state == "dead":
            self.timer += 1
            if self.timer == 60:
                self.input_velocity[1] = -6
            elif self.timer > 60:
                self.apply_gravity()
            else:
                self.velocity = [0, 0]
        else:
            if events.is_action_pressed("right"):
                self.input_velocity[0] = self.walk_accel
                self.sprite.flip_h = True
            elif self.velocity[0] > 0:
                self.velocity[0] = max(self.velocity[0] - self.walk_accel, 0)

            if events.is_action_pressed("left"):
                self.input_velocity[0] = -self.walk_accel
                self.sprite.flip_h = False
            elif self.velocity[0] < 0:
                self.velocity[0] = min(self.velocity[0] + self.walk_accel, 0)

            self.apply_gravity()

            if self.grounded and events.is_action_just_pressed("jump"):
                self.input_velocity[1] = -6
            if events.is_action_just_released("jump"):
                if self.velocity[1] < -3:
                    self.velocity[1] = -3

            if events.is_action_pressed("up") or events.is_action_pressed("down"):
                if "ladder" in self.near:
                    self.state.set_state("climb_idle")


        self.velocity[0] += self.input_velocity[0]
        self.velocity[0] = utils.clamp(self.velocity[0], -self.walk_max, self.walk_max)
        self.velocity[1] += self.input_velocity[1]
