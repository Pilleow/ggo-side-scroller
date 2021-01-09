import pygame
import json
import os
import data.engine as e
import data.classes as c

from math import ceil

RES = (1600, 900)
TRUE_RES = (480, 270)
FPS = 60

pygame.init()

clock = pygame.time.Clock()
screen = pygame.display.set_mode(RES, 0, 32)
pygame.display.set_caption('Level Editor')
display = pygame.Surface(TRUE_RES)
tools = e.Tools()

# camera
BG_COLOR = (146, 244, 255)
CAMERA_MOVE_PAD = RES[1]//5

true_scroll = [0, 0]

# tiles
COLORKEY = (0, 0, 0)
TILE_TYPE = 'orange'
EMPTY_TILE_COLOR = list(map(abs, [BG_COLOR[0]-15, BG_COLOR[1]-15, BG_COLOR[2]-15]))
TILE_SIZE = 16

tiles = tools.load_images(f'sprites/tilesets/{TILE_TYPE}/', colorkey=COLORKEY)
tiles.update(tools.load_images(f'sprites/level_editor/', colorkey=COLORKEY))

# creating buttons, tile menu
buttons = []
x = 6
y = 6
for tile in tiles:
    if y > TRUE_RES[1] - 12:
        y = 6
        x += TILE_SIZE + 3
    c1 = tiles[tile].get_at((TILE_SIZE//2, TILE_SIZE//2))
    c2 = tiles[tile].get_at((TILE_SIZE//4, 0))
    final_color = [(c1.r + c2.r)//2 - 20, (c1.g + c2.g)//2 - 20, (c1.b + c2.b)//2 - 20]
    final_color = list(map(abs, final_color))
    buttons.append(c.Button(x, y, final_color, tiles[tile], tile))
    if tile == 'ERASE':
        buttons[-1].tile_type = ''
    y += TILE_SIZE + 3

tile_menu = pygame.Surface((x + 9 + TILE_SIZE, TRUE_RES[1]))
tile_menu.set_alpha(128)
tile_menu.fill((255,255,255))

# map
MAP_DIMENSIONS = [48, 32]

game_map = {
    'type': TILE_TYPE,
    'paths': [],
    'map': []
}
for layer in range(MAP_DIMENSIONS[1]):
    game_map['map'].append([])
    for tile in range(MAP_DIMENSIONS[0]):
        game_map['map'][layer].append('')

# other stuff
paths = []
new_path = []
current_tile = None
camera_move_active = False
draw_mode_active = False

# mainloop ---------------------------------------------- #
while True:
    display.fill(BG_COLOR)
    mouse_pos = pygame.mouse.get_pos()
    mouse_pos = (mouse_pos[0]/(RES[0]/TRUE_RES[0]), mouse_pos[1]/(RES[0]/TRUE_RES[0]))  # adjust values to "display" rather than "screen" resolution

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
                        if current_tile.tile_type == 'p_p':
                            new_path = []
                        elif len(new_path) != 0:
                            paths.append(new_path)
                        break

            elif event.type == pygame.MOUSEBUTTONUP:
                if current_tile:
                    current_tile.clicked = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:  # toggle camera movement
                    camera_move_active = not camera_move_active

                if event.key == pygame.K_d:  # turn on draw mode
                    draw_mode_active = True
                
                if event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_LCTRL: # save map to map.json
                    all_paths = paths
                    if len(new_path) != 0:
                        all_paths = paths + [new_path]

                    game_map['paths'] = all_paths
                    tools.save_json(game_map, 'map.json')

                if event.key == pygame.K_l and pygame.key.get_mods() & pygame.KMOD_LCTRL: # load map
                    game_map = tools.load_json('map.json')
                    MAP_DIMENSIONS = [len(game_map['map'][0]), len(game_map['map'])]

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
        if current_tile.tile_type == 'p_p' and coords not in new_path: # "p_p" stands for "path point"
                new_path.append([coords[0], coords[1]])
        else:
            game_map['map'][coords[1]][coords[0]] = current_tile.tile_type
        if current_tile.tile_type == '':  # erase path
            for path in paths:
                for point in path:
                    if point == coords:
                        paths[paths.index(path)].remove(point)

    # moving the camera by mouse pos
    if pygame.mouse.get_focused() and camera_move_active:
        if mouse_pos[0] < CAMERA_MOVE_PAD:  # X left
            true_scroll[0] -= (CAMERA_MOVE_PAD - mouse_pos[0])/20
        if mouse_pos[0] > TRUE_RES[0] - CAMERA_MOVE_PAD:  # X right
            true_scroll[0] += (mouse_pos[0] - (TRUE_RES[0] - CAMERA_MOVE_PAD))/20
        if mouse_pos[1] < CAMERA_MOVE_PAD:  # Y up
            true_scroll[1] -= (CAMERA_MOVE_PAD - mouse_pos[1])/20
        if mouse_pos[1] > TRUE_RES[1] - CAMERA_MOVE_PAD:  # Y down
            true_scroll[1] += (mouse_pos[1] - (TRUE_RES[1] - CAMERA_MOVE_PAD))/20

    scroll = list(map(int, true_scroll.copy()))

    # rendering game map (tiles)
    for y in range(ceil(TRUE_RES[1]/TILE_SIZE) + 1):
        y = y + int(scroll[1]/TILE_SIZE)
        if y < 0 or y >= len(game_map['map']):
            continue

        for x in range(ceil(TRUE_RES[0]/TILE_SIZE) + 1):
            x = x + int(scroll[0]/TILE_SIZE)
            if x < 0 or x >= len(game_map['map'][0]):
                continue

            tile = game_map['map'][y][x]
            if tile in tiles:
                display.blit(tiles[tile], (x*TILE_SIZE - scroll[0], y*TILE_SIZE-scroll[1]))
            else:
                pygame.draw.rect(display, EMPTY_TILE_COLOR, (x*TILE_SIZE-scroll[0], y*TILE_SIZE-scroll[1], TILE_SIZE, TILE_SIZE), 1)

    # rendering paths
    all_paths = paths
    if len(new_path) != 0:
        all_paths = paths + [new_path]

    for path in all_paths:
        if len(path) == 0:  # remove path if empty
            paths.remove(path)
            continue

        prev_point = path[0]
        for point in path[1:]:
            point_1 = TILE_SIZE//2 + point[0]*TILE_SIZE - scroll[0], TILE_SIZE//2 + point[1]*TILE_SIZE-scroll[1]
            point_2 = TILE_SIZE//2 + prev_point[0]*TILE_SIZE - scroll[0], TILE_SIZE//2 + prev_point[1]*TILE_SIZE-scroll[1]
            pygame.draw.line(display, [255, 0, 0], point_1, point_2, 3)
            prev_point = point

        display.blit(tiles['p_p'], (path[0][0]*TILE_SIZE - scroll[0], path[0][1]*TILE_SIZE-scroll[1]))
        for point in path[1:]:
            display.blit(tiles['p_p'], (point[0]*TILE_SIZE - scroll[0], point[1]*TILE_SIZE-scroll[1]))
            
    # rendering tile menu and buttons
    display.blit(tile_menu, (0,0))
    for btn in buttons:
        btn.render(display)

    # displaying
    screen.blit(pygame.transform.scale(display, RES), (0, 0))
    pygame.display.update()
    clock.tick(FPS)
