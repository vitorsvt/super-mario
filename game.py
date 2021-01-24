import pygame as pg
import utils
from nodes import Root, Tileset, Tilemap


class Level(Root):
    def __init__(self, file):
        self.tilemap = self.load_tiled(file)
        self.surface = pg.Surface(self.tilemap.surface.get_size(), pg.HWSURFACE + pg.SRCALPHA)
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
        pass

    def physics(self, dt):
        pass

    def process(self):
        pass

    def draw(self, surface):
        surface.fill((0,120,255))
        surface.blit(self.surface, (0, -200))
