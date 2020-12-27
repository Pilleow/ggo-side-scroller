import pygame
from .engine import *


class Button:
    def __init__(self, x, y, sprite_clicked, sprite_idle, tile_type):
        self.rect = pygame.Rect(x, y, sprite_idle.get_width(), sprite_idle.get_height())
        self.sprites = {"idle": sprite_idle, "clicked": sprite_clicked}
        self.tile_type = tile_type
        self.clicked = False

    def check_if_hovering(self, mouse_pos) -> bool:
        if pygame.Rect(mouse_pos[0], mouse_pos[1], 1, 1).colliderect(self.rect):
            return True
        return False

    def render(self, display):
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
    def __init__(self, player_data):
        self.hp = player_data['hp']
        self.special_move = player_data['special_move']
        self.inventory = player_data['inventory']
        
        super().__init__(player_data['x'], player_data['y'], player_data['width'], player_data['height'], player_data['velocity'])