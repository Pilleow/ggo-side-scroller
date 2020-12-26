import pygame
import os

ALLOWED_SPRITE_EXTENSIONS = ['.png', '.jpg', '.jpeg']


class Entity:
    def __init__(self, x: int, y: int, width: int, height: int, velocity: int = 2) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.spawnpoint = [x, y]

        self.current_sprite = 'idle'
        self.y_momentum = 0
        self.air_timer = 0
        self.velocity = 2
        self.moving_right = False
        self.moving_left = False
        self.flip = [False, False]
        self.sprites = {}

    def respawn(self):
        self.rect.x = self.spawnpoint[0]
        self.rect.y = self.spawnpoint[1]
        self.y_momentum = 0
        self.air_timer = 0

    def load_sprites(self, path: str) -> None:
        ''' 
        Scan and load all sprites from "path" 
        -> save in "self.sprites" 
        '''
        for f in os.listdir(path):
            f_split = os.path.splitext(f)
            if f_split[-1] in ALLOWED_SPRITE_EXTENSIONS:
                self.sprites[f_split[0]] = pygame.image.load(path + f)

    def set_flip_sprite(self, x_axis: bool, y_axis: bool) -> None:
        ''' 
        set a sprite flip for current sprite 
        '''
        if self.flip[0] != x_axis:
            self.sprites[self.current_sprite] = pygame.transform.flip(self.sprites[self.current_sprite], False, True)
        if self.flip[1] != y_axis:
            self.sprites[self.current_sprite] = pygame.transform.flip(self.sprites[self.current_sprite], True, False)
        self.flip = [x_axis, y_axis]

    def move(self, movement: [int, int], tiles: list) -> {'top': bool, 'bottom': bool, 'left': bool, 'right': bool}:
        ''' 
        Check for collisions with "tiles" on X and Y axes separately 
        -> move entity by "movement" 
        '''
        collision_types = {'top': False, 'bottom': False,
                    'left': False, 'right': False}

        # X collision check
        self.rect.x += movement[0]
        hit_list = self._collision_test(tiles)
        for tile in hit_list:
            if movement[0] > 0:
                self.rect.right = tile.left
                collision_types['right'] = True
            elif movement[0] < 0:
                self.rect.left = tile.right
                collision_types['left'] = True

        # Y collision check
        self.rect.y += movement[1]
        hit_list = self._collision_test(tiles)
        for tile in hit_list:
            if movement[1] > 0:
                self.rect.bottom = tile.top
                collision_types['bottom'] = True
            elif movement[1] < 0:
                self.rect.top = tile.bottom
                collision_types['top'] = True

        return collision_types

    def render(self, display: object, true_scroll: [int, int], draw_rect: bool=False) -> None:
        ''' 
        render entity sprite on "display" 
        '''
        display.blit(self.sprites[self.current_sprite], (self.rect.x - true_scroll[0], self.rect.y - true_scroll[1]))
        if draw_rect:
            pygame.draw.rect(display, [0, 255, 0], (self.rect.x - true_scroll[0], self.rect.y - true_scroll[1], self.rect.width, self.rect.height), 1)

    def _collision_test(self, tiles: list) -> list:
        ''' 
        get list of colliding pygame.Rects 
        '''
        hit_list = []
        for tile in tiles:
            if self.rect.colliderect(tile):
                hit_list.append(tile)
        return hit_list
