import pygame as pg

class Root:
    def input(self, events):
        pass

    def physics(self, dt):
        pass

    def process(self):
        pass

    def draw(self, surface):
        pass


class Font:
    def __init__(self, file, size, characters):
        self.characters = {}
        self.size = size
        texture = pg.image.load(file).convert_alpha()
        for x, char in enumerate(characters):
            clip = pg.Rect(x * size[0], 0, size[0], size[1])
            self.characters[char] = texture.subsurface(clip)

    def write(self, text):
        surface = pg.Surface((self.size[0] * len(text), self.size[1]), pg.HWSURFACE + pg.SRCALPHA)
        for x, char in enumerate(text):
            surface.blit(self.characters[char], (x * self.size[0], 0))
        return surface


class State:
    def __init__(self, transitions, states):
        self.transitions = [state for state in states if state in transitions]

    @staticmethod
    def check(entity):
        pass

    def enter(self, entity):
        pass

    def exit(self, entity):
        pass


class StateMachine:
    def __init__(self, entity, states, state):
        self.entity = entity
        self.states = {s.__name__:s(states) for s in states}
        self.state = self.states[state]

    def process(self):
        for state in self.state.transitions:
            change_state = state.check(self.entity)
            if change_state:
                self.set(state.__name__)
                break

    def set(self, state_name):
        state = self.states.get(state_name)
        if state and self.state != state:
            self.state.exit(self.entity)
            self.state = state
            self.state.enter(self.entity)

    def current(self, state):
        if self.state == self.states.get(state):
            return True
        return False


class Tile:
    def __init__(self, data):
        self.type = data.get("type")
        self.tags = []
        properties = data.get("properties")
        if properties:
            for property in properties:
                if property["type"] == "bool":
                    self.tags.append(property["name"])
        self.points = []
        objectgroup = data.get("objectgroup")
        if objectgroup:
            for object in objectgroup["objects"]:
                x = object["x"]
                y = object["y"]
                for point in object["polyline"]:
                    point_x = point["x"]
                    point_y = point["y"]
                    point = pg.Vector2((x + point_x - 8) / 8, (y + point_y - 8) / 8)
                    self.points.append(point)

    def has(self, tag):
        return tag in self.tags


class Tileset:
    def __init__(self, texture, size, data, margin = 0, spacing = 0, colorkey = None):
        self.texture = pg.image.load(texture).convert_alpha()
        self.texture.set_colorkey(colorkey)
        self.size = size
        self.data = {}
        for tile in data:
            self.data[tile["id"]] = Tile(tile)
        self.tiles = []
        for j in range(margin, self.texture.get_height(), size + spacing):
            for i in range(margin, self.texture.get_width(), size + spacing):
                clip = pg.Rect(i, j, size, size)
                self.tiles.append(self.texture.subsurface(clip))

    @classmethod
    def from_tiled(cls, data, name):
        tileset =  next(t for t in data["tilesets"] if t["name"] == name)
        return cls(
            tileset["image"], tileset["tilewidth"],
            tileset["tiles"], tileset["margin"],
            tileset["spacing"], tileset["transparentcolor"]
        )


class Tilemap:
    def __init__(self, tileset, size, layers):
        self.width, self.height = size
        self.tileset = tileset
        self.layers = layers
        self.surface = pg.Surface((self.width * tileset.size, self.height * tileset.size), pg.HWSURFACE + pg.SRCALPHA)
        self.size = self.surface.get_size()

        for layer in range(len(layers)):
            for j in range(self.height):
                for i in range(self.width):
                    id = self.get_at(i, j, layer)
                    if id != 0:
                        tile = tileset.tiles[id - 1]
                        self.surface.blit(tile, (i * tileset.size, j * tileset.size))

    @classmethod
    def from_tiled(cls, data):
        tileset = Tileset.from_tiled(data, "Ground")
        layers = [l["data"] for l in data["layers"] if l["type"] == "tilelayer"]
        return cls(
            tileset,
            [data["width"], data["height"]],
            layers
        )

    def get_info_at(self, x, y, layer = 0):
        return self.get_info(self.get_at(x, y, layer))

    def get_at(self, x, y, layer = 0):
        if 0 > x or x >= self.width or 0 > y or y >= self.height:
            return
        return self.layers[layer][y * self.width + x]

    def get_info(self, tile):
        if tile:
            return self.tileset.data.get(tile - 1)
        else:
            return


class Spritesheet:
    def __init__(self, texture, size):
        self.texture = pg.image.load(texture).convert_alpha()
        self.sprites = []
        width, height = size
        for j in range(0, self.texture.get_height(), height):
            for i in range(0, self.texture.get_width(), width):
                clip = pg.Rect(i, j, width, height)
                self.sprites.append(self.texture.subsurface(clip))


class Sprite:
    def __init__(self, texture):
        self.texture = pg.image.load(texture).convert_alpha() if texture else None
        self.flip_h = False
        self.flip_v = False

    def draw(self, surface, position = (0, 0)):
        surface.blit(pg.transform.flip(self.texture, self.flip_h, self.flip_v), position)


class AnimatedSprite(Sprite):
    def __init__(self, spritesheet, frames, default):
        Sprite.__init__(self, None)
        self.spritesheet = spritesheet
        self.animations = {}
        self.current = None
        self.queue = default
        self.frame = 0

        for animation, data in frames.items():
            self.animations[animation] = []
            for section in data:
                self.animations[animation].extend([section["frame"]] * section["duration"])

    def next(self):
        if self.queue != self.current:
            self.current = self.queue
            self.frame = 0
        elif self.frame >= len(self.animations[self.current]):
            self.frame = 0
        self.texture = self.spritesheet.sprites[self.animations[self.current][self.frame]]
        self.frame += 1

    def play(self, animation):
        self.queue = animation


class Camera:
    def __init__(self, size, limits):
        self.shape = pg.Rect(0, 200, size[0], size[1])
        self.limits = limits

    def snap_limits(self):
        h_limit = False
        v_limit = False
        if self.shape.x < 0:
            self.shape.x = 0
            h_limit = True
        elif self.shape.right > self.limits[0]:
            self.shape.right = self.limits[0]
            h_limit = True
        if self.shape.y < 0:
            self.shape.y = 0
            v_limit = True
        elif self.shape.bottom > self.limits[1]:
            self.shape.bottom = self.limits[1]
            v_limit = True
        return h_limit, v_limit

    def draw(self, surface, layers):
        for layer in layers:
            surface.blit(layer.subsurface(self.shape), (0,0))


class Kinematic:
    def __init__(self, size, position, gravity = True):
        self.shape = pg.Rect(position[0], position[1], size[0], size[1])
        self.position = pg.Vector2(position[0], position[1])
        self.velocity = pg.Vector2(0)
        self.grounded = False
        self.gravity = gravity
        self.colliding = {}
        self.enabled_collisions = True

    def apply_gravity(self):
        if self.gravity:
            self.velocity.y = min(self.velocity.y + 0.2, 10)

    def move(self, dt):
        self.position += self.velocity
        self.shape.x = int(self.position.x)
        self.shape.y = int(self.position.y)

    def move_and_collide(self, dt, tilemap, entities = []):
        self.colliding = {}
        rects = [entity.shape.copy() if entity.shape is not self.shape and entity.enabled_collisions else pg.Rect(0,0,0,0) for entity in entities]

        self.position.x += self.velocity.x
        self.shape.x = int(self.position.x)

        if self.velocity.x > 0:
            points = [self.shape.topright, self.shape.midright, self.shape.bottomright]
            for point in points:
                x = point[0] // 16
                y = point[1] // 16
                tile = tilemap.get_info_at(x, y)
                if tile and tile.type == "solid":
                    if self.shape.right >= x * 16 and self.shape.bottom != y * 16 and self.shape.top != y * 16 + 16:
                        self.shape.right = x * 16
                        self.position.x = self.shape.x
                        self.velocity.x = 0

        else:
            points = [self.shape.topleft, self.shape.midleft, self.shape.bottomleft]
            for point in points:
                x = point[0] // 16
                y = point[1] // 16
                tile = tilemap.get_info_at(x, y)
                if tile and tile.type == "solid":
                    if self.shape.left <= x * 16 + 16 and self.shape.bottom != y * 16 and self.shape.top != y * 16 + 16:
                        self.shape.left = x * 16 + 16
                        self.position.x = self.shape.x
                        self.velocity.x = 0

        shape = self.shape.copy()
        shape.y += 4
        shape.h -= 8
        index = shape.collidelist(rects)
        if index != -1:
            rect = rects[index]
            entity = entities[index]
            if entity.velocity.x > 0:
                if self.shape.x > rect.x:
                    self.shape.left = rect.right
                    self.position.x = self.shape.x
                    if self.velocity.x <= 0:
                        self.velocity.x = 0
                    else:
                        self.velocity.x = entity.velocity.x
                    self.colliding["left"] = entity
                else:
                    self.shape.right = rect.left
                    self.position.x = self.shape.x
                    self.velocity.x = entity.velocity.x
                    self.colliding["right"] = entity
            elif entity.velocity.x < 0:
                if self.shape.x > rect.x:
                    self.shape.left = rect.right
                    self.position.x = self.shape.x
                    self.velocity.x = entity.velocity.x
                    self.colliding["left"] = entity
                else:
                    self.shape.right = rect.left
                    self.position.x = self.shape.x
                    if self.velocity.x >= 0:
                        self.velocity.x = 0
                    else:
                        self.velocity.x = entity.velocity.x
                    self.colliding["right"] = entity
            else:
                if self.shape.x > rect.x:
                    self.shape.left = rect.right
                    self.position.x = self.shape.x
                    self.velocity.x = 0
                    self.colliding["left"] = entity
                else:
                    self.shape.right = rect.left
                    self.position.x = self.shape.x
                    self.velocity.x = 0
                    self.colliding["right"] = entity

        self.position.y += self.velocity.y
        self.shape.y = int(self.position.y)
        snap = self.grounded
        self.grounded = False

        if self.velocity.y > 0:
            points = [self.shape.bottomleft, self.shape.midbottom, self.shape.bottomright]
            for point in points:
                x = point[0] // 16
                if snap:
                    y = (point[1] + 4) // 16
                    bottom = self.shape.bottom + 4
                else:
                    y = point[1] // 16
                    bottom = self.shape.bottom
                tile = tilemap.get_info_at(x, y)
                if tile:
                    if tile.type == "solid" and bottom >= y * 16 and self.shape.right != x * 16 and self.shape.left != x * 16 + 16:
                        self.shape.bottom = y * 16
                        self.grounded = True
                        self.position.y = self.shape.y
                        self.velocity.y = 0
                    elif tile.type == "semisolid" and y * 16 + 8 >= bottom >= y * 16 and self.shape.right != x * 16 and self.shape.left != x * 16 + 16:
                        self.shape.bottom = y * 16
                        self.grounded = True
                        self.position.y = self.shape.y
                        self.velocity.y = 0

        else:
            points = [self.shape.topleft, self.shape.midtop, self.shape.topright]
            for point in points:
                x = point[0] // 16
                y = point[1] // 16
                tile = tilemap.get_info_at(x, y)
                if tile and tile.type == "solid":
                    if self.shape.top <= y * 16 + 16 and self.shape.right != x * 16 and self.shape.left != x * 16 + 16:
                        self.shape.top = y * 16 + 16
                        self.position.y = self.shape.y
                        self.velocity.y = 1

        shape = self.shape.copy()
        shape.x += 4
        shape.w -= 8
        if snap: shape.h += 4
        index = shape.collidelist(rects)
        if index != -1:
            rect = rects[index]
            entity = entities[index]
            if entity.velocity.y > 0:
                if self.shape.y > rect.y:
                    self.shape.top = rect.bottom
                    self.position.y = self.shape.y
                    if self.velocity.y <= 0:
                        self.velocity.y = 0
                    else:
                        self.velocity.y = entity.velocity.y
                    self.colliding["top"] = entity
                else:
                    self.shape.bottom = rect.top
                    self.position.y = self.shape.y
                    self.grounded = True
                    self.velocity.y = entity.velocity.y
                    self.colliding["bottom"] = entity
            elif entity.velocity.y < 0:
                if self.shape.y > rect.y:
                    self.shape.top = rect.bottom
                    self.position.y = self.shape.y
                    self.velocity.y = entity.velocity.y
                    self.colliding["top"] = entity
                else:
                    self.shape.bottom = rect.top
                    self.position.y = self.shape.y
                    self.grounded = True
                    if self.velocity.y >= 0:
                        self.velocity.y = 0
                    else:
                        self.velocity.y = entity.velocity.y
                    self.colliding["bottom"] = entity
            else:
                if self.shape.y > rect.y:
                    self.shape.top = rect.bottom
                    self.position.y = self.shape.y
                    self.velocity.y = 0
                    self.colliding["top"] = entity
                else:
                    self.shape.bottom = rect.top
                    self.position.y = self.shape.y
                    self.grounded = True
                    self.velocity.y = 0
                    self.colliding["bottom"] = entity
            if self.grounded:
                self.position.x += entity.velocity.x
                self.shape.x = int(self.position.x)
