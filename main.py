import pygame
import json
import data.engine as e
import data.classes as c

from math import ceil
from random import choice

RES = (1600, 900)
TRUE_RES = (480, 270)  # lower to increase FPS (keep ratio same as "RES")
FPS = 60

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.set_num_channels(16)

clock = pygame.time.Clock()
screen = pygame.display.set_mode(RES, 0, 32)
pygame.display.set_caption('Unnamed Side Scroller')
display = pygame.Surface(TRUE_RES)
tools = e.Tools()

# camera
BG_COLOR = (146, 244, 255)

true_scroll = [0, 0]

# sounds
sfx_path = 'audio/sfx/'
jump_sfx = tools.load_sounds(sfx_path, ['jump_1.wav', 'jump_2.wav'])
walking_sfx = tools.load_sounds(sfx_path, ['walk_1.wav', 'walk_2.wav'], 0.15)
death_sfx = tools.load_sounds(sfx_path, ['death.wav'], 0.25)
pygame.mixer.music.load('audio/music/wasteland.wav')
pygame.mixer.music.set_volume(0.02)
walking_sfx_timer = 0
music_muted = True

if not music_muted:
    pygame.mixer.music.play(-1)

# tiles
COLORKEY = (255, 255, 255)
TILE_SIZE = 16

backgrounds = [
    [0.2, tools.load_images('sprites/backgrounds/', ['wasteland_3.png'], colorkey=COLORKEY)], 
    [0.4, tools.load_images('sprites/backgrounds/', ['wasteland_2.png'], colorkey=COLORKEY)]
]

tiles = tools.load_images('sprites/tilesets/wasteland', colorkey=COLORKEY)

# map
CURRENT_MAP = 'wasteland_1'

game_map = tools.load_json(f'data/maps/{CURRENT_MAP}.json')
spawnpoint = [0, 0]
y = 0
for layer in game_map['map']:
    x = 0
    for tile in layer:
        if tile == 'P':
            spawnpoint = [x*TILE_SIZE, y*TILE_SIZE]
            break
        x += 1
    if spawnpoint != [0, 0]:
        break
    y += 1

MAP_BOTTOM_COLOR = tiles['8'].get_at((TILE_SIZE//2, TILE_SIZE-1))
MAP_BOTTOM_Y = len(game_map['map']) * TILE_SIZE
MAP_WIDTH = len(game_map['map'][0]) * TILE_SIZE

# player
player_data = {
    'x': spawnpoint[0],
    'y': spawnpoint[1],
    'width': 6,
    'height': 10,
    'velocity': 2,
    'hp': 100,
    'all_special_moves': ['double_jump', 'dash'],
    'special_move': 'double_jump',
    'inventory': []
}
player = c.Player(player_data)
player.load_sprites('sprites/player/')
player.change_special_move('double_jump')

# enemies
enemies = []
for path in game_map['paths']:
    spawn = list(map(lambda x: x*TILE_SIZE, choice(path)))
    e = c.Enemy({'x': spawn[0], 'y': spawn[1], 'width': 6, 'height': 10, 'velocity': 2, 'hp': 100})
    e.load_path(path)
    e.load_sprites('sprites/enemy/small/')
    enemies.append(e)

# more sounds
special_moves = tools.load_sounds(sfx_path, ['dash.wav','change_move.wav'], 0.25, True)

# game loop --------------------------------------------- #
while True:
    display.fill(BG_COLOR)

    # things
    player.movement = [0, 0]
    for e in enemies:
        e.movement = [0, 0]

    # camera update
    true_scroll[0] += (player.rect.x - true_scroll[0] - (TRUE_RES[0] + player.rect.width)/2)/20
    true_scroll[1] += (player.rect.y - true_scroll[1] - (TRUE_RES[1] + player.rect.height)/2)/20
    scroll = list(map(int, true_scroll.copy()))

    # rendering background
    for i, bg in enumerate(backgrounds):
        x_value = (-scroll[0] * bg[0]) % bg[1].get_width()


        display.blit(bg[1], (x_value, TRUE_RES[1]//2 - 100 + (75 * i) - scroll[1] * bg[0]//2))
        display.blit(bg[1], (x_value - bg[1].get_width(), TRUE_RES[1]//2 - 100 + (75 * i) - scroll[1] * bg[0]//2))

        pygame.draw.rect(display, bg[1].get_at((0, bg[1].get_height()-1)), (0, TRUE_RES[1]//2 - 100 + (75 * i) - scroll[1] * bg[0]//2 + bg[1].get_height(), TRUE_RES[0], TRUE_RES[1]))

    # rendering tiles
    tile_rects = []
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
                display.blit(tiles[tile], (x*TILE_SIZE - scroll[0], y*TILE_SIZE - scroll[1]))
                tile_rects.append(pygame.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE))

    # mouse handling
    mouse_pos = pygame.mouse.get_pos()
    if player.rect.x + player.rect.width * (TRUE_RES[0]/RES[0]) > mouse_pos[0] * (TRUE_RES[0]/RES[0]) + scroll[0]:
        player.set_flip_sprite(False, True)
    else:
        player.set_flip_sprite(False, False)

    # event handling, key input
    for event in pygame.event.get():
        if event.type == pygame.QUIT:  # exit game (turn off window)
            pygame.quit()
            raise SystemExit

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:  # mute/unmute music
                if music_muted:
                    pygame.mixer.music.play(-1)
                else:
                    pygame.mixer.music.fadeout(500)
                music_muted = not music_muted

            elif event.key == pygame.K_d:  # go right
                player.moving_right = True

            elif event.key == pygame.K_a:  # go left
                player.moving_left = True

            elif event.key == pygame.K_w:  # jump
                if player.air_timer < 6:
                    choice(jump_sfx).play()
                    player.y_momentum = -player.velocity * player.jump_mod
                elif player.additional_jumps > 0:
                    choice(jump_sfx).play()
                    player.y_momentum = -player.velocity * player.jump_mod
                    player.additional_jumps -= 1

            elif event.key == pygame.K_q:  # change special move
                special_moves['change_move'].play()
                if player.special_move == player.all_special_moves[-1]:
                    player.change_special_move(player.all_special_moves[0])
                else:
                    player.change_special_move(player.all_special_moves[player.all_special_moves.index(player.special_move) + 1])

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_d:  # stop going right
                player.moving_right = False

            elif event.key == pygame.K_a:  # stop going left
                player.moving_left = False

    # moving player
    if player.moving_right:
        player.movement[0] += player.velocity # walk right

        # dash special move
        if pygame.key.get_mods() & pygame.KMOD_LSHIFT and player.special_move == 'dash' and player.dash_cooldown == 0:
            special_moves['dash'].play()
            player.dash_cooldown = 120
        if player.dash_cooldown > 100:
            player.movement[0] += player.velocity * ((player.dash_cooldown - 100)/15)**2 + 1

    if player.moving_left:
        player.movement[0] -= player.velocity # walk left

        # dash special move
        if pygame.key.get_mods() & pygame.KMOD_LSHIFT and player.special_move == 'dash' and player.dash_cooldown == 0:
            special_moves['dash'].play()
            player.dash_cooldown = 120
        if player.dash_cooldown > 100:
            player.movement[0] -= player.velocity * ((player.dash_cooldown - 100)/15)**2 + 1

    # gravity
    player.y_momentum += 0.2
    player.movement[1] += player.y_momentum
    if player.y_momentum > 5:
        player.y_momentum = 5

    for e in enemies: # apply gravity to enemies
        if not tools.is_visible(scroll, TRUE_RES, e):
            continue

        e.y_momentum += 0.2
        e.movement[1] += e.y_momentum
        if e.y_momentum > 5:
            e.y_momentum = 5
        e.move(e.movement, tile_rects) # moving enemies here

    # moving the player
    collisions = player.move(player.movement, tile_rects)

    # corrections, miscellanous
    if player.dash_cooldown > 0:  # dash cooldown cooling down
        player.dash_cooldown -= 1
    if walking_sfx_timer > 0:  # walking sfx timer
        walking_sfx_timer -= 1
    if player.rect.y > 500:  # respawn after fall
        player.respawn()
        death_sfx.play()
    if collisions['top']:  # collision with ceiling
        player.y_momentum = 0
    if collisions['bottom']:  # jumping, collisions, walking sfx
        player.y_momentum = 0
        player.air_timer = 0
        if player.special_move == 'double_jump':
            player.additional_jumps = 1
        if player.movement[0] != 0 and walking_sfx_timer == 0 and not collisions['left'] and not collisions['right'] and abs(player.movement[0]) <= player.velocity:
            walking_sfx_timer = 20 // player.velocity
            choice(walking_sfx).play()
    else:
        player.air_timer += 1

    # displaying
    player.render(display, scroll)
    for e in enemies:
        e.render(display, scroll)

    # things
    screen.blit(pygame.transform.scale(display, RES), (0, 0))
    pygame.display.update()
    clock.tick(FPS)
