import pygame
import random
import math

from .engine import *


class Button:
    def __init__(self, x: int, y: int, sprite_clicked: object, sprite_idle: object, tile_type: str):
        self.rect = pygame.Rect(x, y, sprite_idle.get_width(), sprite_idle.get_height())
        self.sprites = {"idle": sprite_idle, "clicked": sprite_clicked}
        self.tile_type = tile_type
        self.clicked = False

    def check_if_hovering(self, mouse_pos: list) -> bool:
        '''
        Check if `mouse_pos = [float, float]` coordinates overlap the button. \\
        If both X and Y do, return `True`. Else, return `False`.
        '''
        if pygame.Rect(mouse_pos[0], mouse_pos[1], 1, 1).colliderect(self.rect):
            return True
        return False

    def render(self, display: object) -> None:
        ''' 
        Render button on `display`.
        '''
        if self.clicked:
            if type(self.sprites['clicked']) == list:
                pygame.draw.rect(display, self.sprites['clicked'], self.rect)
            else:
                display.blit(self.sprites['clicked'], (self.rect.x, self.rect.y))
        else:
            if type(self.sprites['idle']) == list:
                pygame.draw.rect(display, self.sprites['idle'], self.rect)
            else:
                display.blit(self.sprites['idle'], (self.rect.x, self.rect.y))


class Player(Entity):
    def __init__(self, player_data: dict):
        self.hp = player_data['hp']
        self.all_special_moves = player_data['all_special_moves']
        self.special_move = player_data['special_move']
        self.inventory = player_data['inventory']
        super().__init__(
            player_data['x'], player_data['y'], 
            player_data['width'], player_data['height'], 
            player_data['velocity']
        )

        self.current_weapon = None  # Weapon object or None
        self.additional_jumps = 0  # double jump
        self.dash_cooldown = 0  # dash

    def change_special_move(self, change_to: str) -> None:
        '''
        Change special move to `change_to` string. \\
        Additionally, restart some stats to match the new special move.
        '''
        self.special_move = change_to
        if change_to == 'dash':
            self.additional_jumps = 0
            self.jump_mod = 2.2
        elif change_to == 'double_jump':
            self.jump_mod = 1.9


class Enemy(Entity):
    def __init__(self, enemy_data: dict, path: list, tile_size: int=16):
        self.hp = enemy_data['hp']
        super().__init__(
            enemy_data['x']*tile_size + (tile_size - enemy_data['width'])//2, 
            enemy_data['y']*tile_size + tile_size - enemy_data['height'], 
            enemy_data['width'], 
            enemy_data['height'], 
            enemy_data['velocity']
        )

        self.current_weapon = None  # Weapon object or None
        self.path = path
        self.current_point = self.path[self.path.index([enemy_data['x'], enemy_data['y']])]
        self.target_point = self.current_point
        self.moving_chance = 0

    def move_randomly(self, increase: float=0.001, tile_size: int=16) -> None: # fuck this thing
        '''
        This piece of shit is stupid. It does a lot of things and is dumb. \\
        I hate it and I won't tell you anything about it. Fuck this. \n
        If you want to know anything about this, look it up, though I don't recommend doing it.
        '''
        if self.target_point == self.current_point and random.uniform(0, 1) < self.moving_chance: # set new target tile to move to
            self.target_point = self.path[random.randint(0, len(self.path)-1)]
            self.moving_chance = 0
        
        elif self.target_point == self.current_point:  # increase chance of moving in the next frame
            self.moving_chance += increase

        else:  # move
            if self.current_point[0] < self.target_point[0]:
                if self.rect.x + self.velocity < self.target_point[0]*tile_size + (tile_size - self.rect.width)//2:
                    self.rect.x += self.velocity
                else:
                    self.rect.x = self.target_point[0]*tile_size + (tile_size - self.rect.width)//2
                    self.current_point = self.target_point
            elif self.current_point[0] > self.target_point[0]:
                if self.rect.x + self.velocity > self.target_point[0]*tile_size + (tile_size - self.rect.width)//2:
                    self.rect.x -= self.velocity
                else:
                    self.rect.x = self.target_point[0]*tile_size + (tile_size - self.rect.width)//2
                    self.current_point = self.target_point

    def is_detected(self, coords: list, game_map: list, transp_blcks: list, tile_accuracy: int=16, tile_size: int=16) -> bool:
        '''
        Combination of `is_in_range` and `is_blocked`. Abstracts these two away.
        If both methods return True, return True, else return False.
        '''
        if not self.is_in_range(coords):
            return False
        if self.is_vision_blocked(coords, game_map, transp_blcks, tile_accuracy, tile_size):
            return False
        return True

    def is_in_range(self, coords: list) -> bool:
        '''
        Checks if `coords = [int, int]` are in range. \\
        If distance <= range, return True. Else, return `False`.
        '''
        _range = 96 # !!! TEMPORARY !!! Change to self.current_weapon.range when Weapons are implemented!
        if _range >= self.get_distance_to(coords):
            return True
        return False

    def is_vision_blocked(self, coords: list, game_map: list, transp_blcks: list, tile_accuracy: int=4, tile_size: int=16) -> bool:
        '''
        Check if any blocks are in the way to `coords = [int, int]`.
        '''
        x_center = self.rect.center[0]
        y_center = self.rect.center[1]

        if coords[0] < x_center:
            range_x = range(coords[0], x_center, tile_accuracy)
        elif coords[0] == x_center:
            range_x = [coords[0]]
        else:
            range_x = range(x_center, coords[0], tile_accuracy)
        if coords[1] < y_center:
            range_y = range(coords[1], y_center, tile_accuracy)
        elif coords[1] == y_center:
            range_y = [coords[1]]
        else:
            range_y = range(y_center, coords[1], tile_accuracy)

        for x in range_x:
            print(x)
            for y in range_y:
                if game_map[int(y/tile_size)][int(x/tile_size)] not in transp_blcks:
                    return True
        return False
