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


class StateMachine:
    def __init__(self, states, default):
        self.states = states
        self.state = default

    def set_state(self, state):
        if self.state != state and state in self.states:
            self.exit_state()
            self.state = state
            self.enter_state()

    def enter_state(self):
        pass

    def exit_state(self):
        pass

    def process(self):
        pass


class Tile:
    def __init__(self, data):
        self.type = data.get("type")
        self.tags = []
        properties = data.get("properties")
        if properties:
            for property in properties:
                if property["type"] == "bool":
                    self.tags.append(property["name"])



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


class Tilemap:
    def __init__(self, tileset, size, tiles):
        self.width, self.height = size
        self.tileset = tileset
        self.tiles = tiles
        self.surface = pg.Surface((self.width * tileset.size, self.height * tileset.size), pg.HWSURFACE + pg.SRCALPHA)
        self.size = self.surface.get_size()

        for j in range(self.height):
            for i in range(self.width):
                id = self.tiles[i + j * self.width]
                if id != 0:
                    tile = tileset.tiles[id - 1]
                    self.surface.blit(tile, (i * tileset.size, j * tileset.size))

    def get_info_at(self, x, y):
        return self.get_info(self.get_at(x, y))

    def get_at(self, x, y):
        if 0 > x or x >= self.width or 0 > y or y >= self.height:
            return
        return self.tiles[y * self.width + x]

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

    def draw(self, surface, position = (0, 0)):
        surface.blit(pg.transform.flip(self.texture, self.flip_h, False), position)


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
    def __init__(self, shape, position = pg.Vector2(0,0)):
        self.shape = shape
        self.position = position
        self.grounded = False
        self.velocity = pg.Vector2(0, 0)
        self.colliding = []

    def move(self, dt):
        self.position.x += self.velocity[0]
        self.shape.x = int(self.position.x)
        self.position.y += self.velocity[1]
        self.shape.y = int(self.position.y)

    def move_and_collide(self, dt, tilemap):
        self.colliding = []

        self.position.x += self.velocity[0]
        self.shape.x = int(self.position.x)

        if self.velocity[0] > 0:
            points = [self.shape.topright, self.shape.midright, self.shape.bottomright]
            for point in points:
                x = point[0] // 16
                y = point[1] // 16
                tile = tilemap.get_info_at(x, y)
                if tile and tile.type == "solid":
                    if self.shape.right >= x * 16 and self.shape.bottom != y * 16 and self.shape.top != y * 16 + 16:
                        self.shape.right = x * 16
                        self.position.x = self.shape.x
                        self.velocity[0] = 0
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
                        self.velocity[0] = 0

        self.position.y += self.velocity[1]
        self.shape.y = int(self.position.y)

        colliders = []
        self.grounded = False
        if self.velocity[1] > 0:
            points = [self.shape.bottomleft, self.shape.midbottom, self.shape.bottomright]
            for point in points:
                x = point[0] // 16
                y = point[1] // 16
                tile = tilemap.get_info_at(x, y)
                if tile:
                    if tile.type == "solid" and self.shape.bottom >= y * 16 and self.shape.right != x * 16 and self.shape.left != x * 16 + 16:
                        self.shape.bottom = y * 16
                        self.grounded = True
                        self.position.y = self.shape.y
                        self.velocity[1] = 0
                    elif tile.type == "semisolid" and y * 16 + 8 >= self.shape.bottom >= y * 16 and self.shape.right != x * 16 and self.shape.left != x * 16 + 16:
                        self.shape.bottom = y * 16
                        self.grounded = True
                        self.position.y = self.shape.y
                        self.velocity[1] = 0
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
                        self.velocity[1] = 0
