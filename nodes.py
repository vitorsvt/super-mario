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


class Tileset:
    def __init__(self, texture, size, data, margin = 0, spacing = 0, colorkey = None):
        self.texture = pg.image.load(texture).convert_alpha()
        self.texture.set_colorkey(colorkey)
        self.size = size
        self.data = {tile["id"]: {"type": tile["type"]} for tile in data}
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

        for j in range(self.height):
            for i in range(self.width):
                id = self.tiles[i + j * self.width]
                if id != 0:
                    tile = tileset.tiles[id - 1]
                    self.surface.blit(tile, (i * tileset.size, j * tileset.size))
