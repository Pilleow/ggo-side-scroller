import pygame
import json
import os

tile_parse_values = {
    'floor': '8',
    'floor_left': '7',
    'floor_right': '9',
    'inside': '5',
    'inside_skull': 'x',
    'block': 'B',
    'player_spawn': 'P'
}


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


def load_image(path):
    img = pygame.image.load(path).convert()
    img.set_colorkey(COLORKEY)
    return img


def load_game_map(path):
    with open(path, mode='r', encoding='utf') as f:
        game_map = json.load(f)
    MAP_DIMENSIONS = [len(game_map['map'][0]), len(game_map['map'])]

    # parse map to match tile naming convention in level editor
    for layer_int in range(MAP_DIMENSIONS[1]):
        for tile_int in range(MAP_DIMENSIONS[0]):
            tile = game_map['map'][layer_int][tile_int]
            for parsed_tile in tile_parse_values:
                if tile == tile_parse_values[parsed_tile]:
                    game_map['map'][layer_int][tile_int] = parsed_tile

    return game_map


def parse_and_save_map():
    # parse map to match tile naming convention in game
    for layer_int in range(MAP_DIMENSIONS[1]):
        for tile_int in range(MAP_DIMENSIONS[0]):
            tile = game_map['map'][layer_int][tile_int]
            if tile in tile_parse_values:
                game_map['map'][layer_int][tile_int] = tile_parse_values[tile]

    # save to json at the same directory
    with open('map.json', mode='w+', encoding='utf') as f:
        json.dump(game_map, f)


RES = (1600, 900)
COLORKEY = (255, 255, 255)
FPS = 60

pygame.init()

clock = pygame.time.Clock()
screen = pygame.display.set_mode(RES, 0, 32)
pygame.display.set_caption('Level Editor')

display = pygame.Surface((RES[0]//2, RES[1]//2))

# camera
BG_COLOR = (146, 244, 255)
CAMERA_MOVE_PAD = RES[1]//5

true_scroll = [0, 0]

# loading tiles
TILE_TYPE = 'wasteland'
EMPTY_TILE_COLOR = list(map(abs, [BG_COLOR[0]-15, BG_COLOR[1]-15, BG_COLOR[2]-15]))
ALLOWED_SPRITE_EXTENSIONS = ['.png', '.jpg', '.jpeg']
TILE_SIZE = 16

tiles = {}
for p in [f'sprites/tilesets/{TILE_TYPE}/', 'sprites/level_editor/']:
    for f in os.listdir(p):
        f_split = os.path.splitext(f)
        if f_split[-1] in ALLOWED_SPRITE_EXTENSIONS:
            tiles[f_split[0]] = load_image(p + f)

# creating buttons, tile menu
''' 
wasteland only (can be changed)

y = 6 ; initially
y += 19 ; every tile
12 tiles max per column
'''
buttons = []
x = 6
y = 6
for tile in tiles:
    if y > RES[1]//2 - 12:
        y = 6
        x += TILE_SIZE + 3
    c1 = tiles[tile].get_at((TILE_SIZE//2, TILE_SIZE//2))
    c2 = tiles[tile].get_at((TILE_SIZE//4, 0))
    final_color = [(c1.r + c2.r)//2 - 20, (c1.g + c2.g)//2 - 20, (c1.b + c2.b)//2 - 20]
    final_color = list(map(abs, final_color))
    if tile != 'eraser':
        buttons.append(Button(x, y, final_color, tiles[tile], tile))
    else:
        buttons.append(Button(x, y, final_color, tiles[tile], ''))
    y += TILE_SIZE + 3

tile_menu = pygame.Surface((x + 9 + TILE_SIZE, RES[1]//2))
tile_menu.set_alpha(128)
tile_menu.fill((255,255,255))

# map
MAP_DIMENSIONS = [64, 24]

game_map = {
    'type': TILE_TYPE,
    'map': []
}
for layer in range(MAP_DIMENSIONS[1]):
    game_map['map'].append([])
    for tile in range(MAP_DIMENSIONS[0]):
        game_map['map'][layer].append('')

# other stuff
current_tile = None
camera_move_active = False
draw_mode_active = False

# mainloop ---------------------------------------------- #
while True:
    display.fill(BG_COLOR)
    mouse_pos = pygame.mouse.get_pos()
    mouse_pos = (mouse_pos[0]/2, mouse_pos[1]/2)  # adjust values to "display" rather than "screen" resolution

    # event handling
    for event in pygame.event.get():
            if event.type == pygame.QUIT:  # exit game (turn off window)
                pygame.quit()
                raise SystemExit

            elif event.type == pygame.MOUSEBUTTONDOWN:
                for btn in buttons:
                    if btn.check_if_hovering((mouse_pos[0], mouse_pos[1])):  # clicking buttons
                        btn.clicked = True
                        current_tile = btn
                        break

            elif event.type == pygame.MOUSEBUTTONUP:
                for btn in buttons:
                    btn.clicked = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:  # toggle camera movement
                    camera_move_active = not camera_move_active
                if event.key == pygame.K_d:  # turn on draw mode
                    draw_mode_active = True
                if event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_LCTRL: # save map to map.json
                    parse_and_save_map()
                if event.key == pygame.K_l and pygame.key.get_mods() & pygame.KMOD_LCTRL: # load map
                    game_map = load_game_map('map.json')

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_d:  # turn off draw mode
                    draw_mode_active = False

    # drawing when in draw mode
    if draw_mode_active:
        coords = list(map(lambda x: int(x/TILE_SIZE), [mouse_pos[0]+true_scroll[0], mouse_pos[1]+true_scroll[1]]))
        x_valid = coords[0] >= 0 and coords[0] < MAP_DIMENSIONS[0]
        y_valid = coords[1] >= 0 and coords[1] < MAP_DIMENSIONS[1]
        if not x_valid or not y_valid or not current_tile:
            continue
        game_map['map'][coords[1]][coords[0]] = current_tile.tile_type

    # moving the camera by mouse pos
    if pygame.mouse.get_focused() and camera_move_active:
        if mouse_pos[0] < CAMERA_MOVE_PAD:  # X left
            true_scroll[0] -= (CAMERA_MOVE_PAD - mouse_pos[0])/20
        if mouse_pos[0] > RES[0]/2 - CAMERA_MOVE_PAD:  # X right
            true_scroll[0] += (mouse_pos[0] - (RES[0]/2 - CAMERA_MOVE_PAD))/20
        if mouse_pos[1] < CAMERA_MOVE_PAD:  # Y up
            true_scroll[1] -= (CAMERA_MOVE_PAD - mouse_pos[1])/20
        if mouse_pos[1] > RES[1]/2 - CAMERA_MOVE_PAD:  # Y down
            true_scroll[1] += (mouse_pos[1] - (RES[1]/2 - CAMERA_MOVE_PAD))/20

    scroll = list(map(int, true_scroll.copy()))

    # rendering game map (tiles)
    y = 0
    for layer in game_map['map']:
        x = 0
        for tile in layer:
            if tile in tiles:
                display.blit(tiles[tile], (x*TILE_SIZE - scroll[0], y*TILE_SIZE-scroll[1]))
            else:
                pygame.draw.rect(display, EMPTY_TILE_COLOR, (x*TILE_SIZE-scroll[0], y*TILE_SIZE-scroll[1], TILE_SIZE, TILE_SIZE), 1)
            x += 1
        y += 1

    # rendering tile menu and buttons
    display.blit(tile_menu, (0,0))
    for btn in buttons:
        btn.render(display)

    # displaying
    screen.blit(pygame.transform.scale(display, RES), (0, 0))
    pygame.display.update()
    clock.tick(FPS)
