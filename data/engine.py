import pygame
import json
import os

ALLOWED_IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg']
ALLOWED_AUDIO_EXTENSIONS = ['.wav']


class Tools:
    @staticmethod
    def load_images(path: str, file_names: list=None, colorkey: tuple=None) -> dict:
        '''
        Returns dict with names of files (listed in `file_names`) without extensions as keys.\\
        If one file is loaded, return a single image (as an object).\n
        Set a `colorkey` if provided. Leave `file_names` empty to load all images from `path`.
        '''
        if not file_names:
            file_names = os.listdir(path)

        if len(file_names) == 1:
            s = pygame.image.load(f'{path}/{file_names[0]}').convert()
            if colorkey:
                s.set_colorkey(colorkey)
            return s

        sprites = {}
        for f in file_names:
            name, ext = os.path.splitext(f)
            if ext not in ALLOWED_IMAGE_EXTENSIONS:
                continue
            s = pygame.image.load(f'{path}/{f}').convert()
            if colorkey:
                s.set_colorkey(colorkey)
            sprites[name] = s
        return sprites

    @staticmethod
    def load_sounds(path: str, file_names: list=None, volume: float=1) -> list:
        '''
        Returns a list with sounds listed in `file_names`.\n
        Leave `file_names` empty to load all sounds from `path`.
        '''
        if not file_names:
            file_names = os.listdir(path)

        if len(file_names) == 1:
            s = pygame.mixer.Sound(f'{path}/{file_names[0]}')
            s.set_volume(volume)
            return s

        sounds = []
        for f in file_names:
            name, ext = os.path.splitext(f)
            if ext not in ALLOWED_AUDIO_EXTENSIONS:
                continue
            s = pygame.mixer.Sound(f'{path}/{f}')
            s.set_volume(volume)
            sounds.append(s)
        return sounds

    @staticmethod
    def load_json(path: str, mode: str='r', encoding: str='utf') -> object:
        '''
        Load a JSON file from `path`.
        '''
        with open(path, mode=mode, encoding=encoding) as f:
            game_map = json.load(f)
        return game_map

    @staticmethod
    def save_json(data, path: str, mode: str='w+', encoding: str='utf', indent: int=None) -> None:
        '''
        Save a JSON file to `path`.
        '''
        with open(path, mode=mode, encoding=encoding) as f:
            json.dump(data, f, indent=indent)


class Entity:
    def __init__(self, x: int, y: int, width: int, height: int, velocity: int) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.spawnpoint = [x, y]

        self.current_sprite = 'idle'
        self.y_momentum = 0
        self.air_timer = 0
        self.velocity = velocity
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
        1. Load all sprites from `path`,
        2. save in `self.sprites`.
        '''
        for f in os.listdir(path):
            name, ext = os.path.splitext(f)
            if ext not in ALLOWED_IMAGE_EXTENSIONS:
                continue
            self.sprites[name] = pygame.image.load(path + f)

    def set_flip_sprite(self, x_axis: bool, y_axis: bool) -> None:
        ''' 
        Set a sprite flip for current sprite.
        '''
        if self.flip[0] != x_axis:
            self.sprites[self.current_sprite] = pygame.transform.flip(self.sprites[self.current_sprite], False, True)
        if self.flip[1] != y_axis:
            self.sprites[self.current_sprite] = pygame.transform.flip(self.sprites[self.current_sprite], True, False)
        self.flip = [x_axis, y_axis]

    def move(self, movement: [int, int], tiles: list) -> {'top': bool, 'bottom': bool, 'left': bool, 'right': bool}:
        ''' 
        1. Move entity by `movement`,
        2. Check for collisions with `tiles` on X and Y axes separately.
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
        Render entity sprite on `display`.
        '''
        display.blit(self.sprites[self.current_sprite], (self.rect.x - true_scroll[0], self.rect.y - true_scroll[1]))
        if draw_rect:
            pygame.draw.rect(display, [0, 255, 0], (self.rect.x - true_scroll[0], self.rect.y - true_scroll[1], self.rect.width, self.rect.height), 1)

    def _collision_test(self, tiles: list) -> list:
        ''' 
        Get list of colliding `pygame.Rects`.
        '''
        hit_list = []
        for tile in tiles:
            if self.rect.colliderect(tile):
                hit_list.append(tile)
        return hit_list
