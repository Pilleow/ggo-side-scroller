import pygame
import json
import random
import data.engine as e
import data.classes as c

from math import ceil
from random import choice

# first element in RES is the fullscreen resolution, 
# set automatically when turning on fullscreen
RES = [
    (0, 0), (1024, 576), (1152, 648), 
    (1280, 720), (1366, 768), (1600, 900), 
    (1920, 1080), (2560, 1440), (3840, 2160)
]
TRUE_RES = (480, 270)  # keep ratio same as "RES[CNT_RES]"
CNT_RES = 5 # index of item in RES
FPS = 60

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.set_num_channels(16)

clock = pygame.time.Clock()
screen = pygame.display.set_mode(RES[CNT_RES])
display = pygame.Surface(TRUE_RES)
tools = e.Tools()

pygame.display.set_caption('Unnamed Side Scroller')

''' map --------------------------------------------------------- '''
level = ['blue', 1]
new_level = None
game_map = tools.load_json(f'data/maps/{level[0]}_{level[1]}.json')

''' sounds ------------------------------------------------------ '''
sfx_path = 'audio/sfx/'
jump_sfx = tools.load_sounds(sfx_path, ['jump_1.wav', 'jump_2.wav'])
walking_sfx = tools.load_sounds(sfx_path, ['walk_1.wav', 'walk_2.wav'], 0.15)
death_sfx = tools.load_sounds(sfx_path, ['death.wav'], 0.25)
loading_screen_sfx = tools.load_sounds(sfx_path, ['loading_screen.wav'], 0.35)

pygame.mixer.music.load(f'audio/music/{level[0]}.wav')
pygame.mixer.music.set_volume(0.02)
walking_sfx_timer = 0
music_muted = True

if not music_muted:
    pygame.mixer.music.play(-1)

''' graphics ---------------------------------------------------- '''
TILE_SIZE = 16
try:
    backgrounds = [
        [0.2, tools.load_images('sprites/backgrounds/', [f'{level[0]}_3.png'], colorkey=(255, 255, 255))], 
        [0.4, tools.load_images('sprites/backgrounds/', [f'{level[0]}_2.png'], colorkey=(255, 255, 255))]
    ]
except:
    backgrounds = []

tiles = tools.load_images(f'sprites/tilesets/{game_map["type"]}', colorkey=(0, 0, 0))
ui = tools.load_images('sprites/ui', colorkey=(0, 0, 0))
pygame.display.set_icon(ui['icon'])

''' player ------------------------------------------------------ '''
player_data = {
    'x': 0,
    'y': 0,
    'width': 6,
    'height': 10,
    'velocity': 2,
    'hp': 100,
    'all_special_moves': ['double_jump', 'dash'],
    'special_move': 'dash',
    'inventory': []
}
player = c.Player(player_data)
player.load_sprites('sprites/player/')
player.change_special_move('double_jump')

''' more map ---------------------------------------------------- '''
# scan for spawnpoint horizontally
y = 0
for layer in game_map['map']:
    x = 0
    for tile in layer:
        if tile == 'P':
            player.set_pos([
                x*TILE_SIZE + (TILE_SIZE - player.rect.width)//2, 
                y*TILE_SIZE + TILE_SIZE - player.rect.height
            ])
            break
        x += 1
    if player.rect.x != 0 or player.rect.y != 0:
        break
    y += 1

map_bottom_color = tiles['5'].get_at((TILE_SIZE//2, TILE_SIZE-1))

''' camera ------------------------------------------------------ '''
BG_COLOR = (146, 244, 255)

true_scroll = [player.rect.x - TRUE_RES[0]//2, player.rect.y - TRUE_RES[1]//2]

''' more sounds ------------------------------------------------- '''
special_moves = tools.load_sounds(sfx_path, ['dash.wav','change_move.wav'], 0.25, True)

''' other tings ------------------------------------------------- '''


def load_enemies() -> list:
    enemies = []
    for path in game_map['paths']:
        spawn = choice(path)
        e = c.Enemy({'x': spawn[0], 'y': spawn[1], 'width': 6, 'height': 10, 'velocity': 1, 'hp': 100}, path)
        e.load_sprites('sprites/enemy/small/')
        enemies.append(e)
    return enemies


def display_reinit() -> None:
    pygame.display.quit()
    pygame.display.init()


def load_level(level: list) -> list:
    try:
        backgrounds = [
            [0.2, tools.load_images('sprites/backgrounds/', [f'{level[0]}_3.png'], colorkey=(255, 255, 255))], 
            [0.4, tools.load_images('sprites/backgrounds/', [f'{level[0]}_2.png'], colorkey=(255, 255, 255))]
        ]
    except:
        backgrounds = []
    tiles = tools.load_images(f'sprites/tilesets/{game_map["type"]}', colorkey=(0, 0, 0))

    return tiles, backgrounds


def change_level(direction: str, current_lvl: list) -> list:
    new_lvl = current_lvl.copy()
    spawn = [0, 0]

    # set new map zone
    new_lvl[0] = get_next_map_zone(direction, current_lvl[0])
    if new_lvl [0] == '':
        return None, None
    
    # required for scan
    game_map = tools.load_json(f'data/maps/{new_lvl[0]}_{new_lvl[1]}.json')

    # scan for spawnpoint vertically
    for x in range(len(game_map['map'][0])):
        if direction == 'L':
            x = len(game_map['map'][0]) - (x + 1)
        for y in range(len(game_map['map'])):
            if game_map['map'][y][x] == 'P':
                spawn = [x*TILE_SIZE, y*TILE_SIZE]
                break
        if spawn != [0, 0]:
            break

    return game_map, new_lvl, spawn


zone_queue = ['green', 'blue', 'orange', 'red']
def get_next_map_zone(direction: str, current_zone: str) -> str:
    next_zone = ''
    current_zone_index = zone_queue.index(current_zone)
    if direction == 'R' and current_zone_index < len(zone_queue)-1:
        next_zone = zone_queue[current_zone_index+1]
    if direction == 'L' and current_zone_index > 0:
        next_zone = zone_queue[current_zone_index-1]
    return next_zone

''' enemies ----------------------------------------------------- '''
enemies = load_enemies()

''' animations -------------------------------------------------- '''
ZONE_CHANGE_ANIM_TIMER_DEFAULT = random.randint(190, 230)
LOADING_SCREEN_CLR = [20, 20, 20]
ANIM_DURATION = 30
zone_change_anim_timer = 0

''' game loop --------------------------------------------------- '''
while True:
    display.fill(BG_COLOR)

    ''' tings ------------------------------------------------------------- '''
    player.movement = [0, 0]

    ''' camera update ----------------------------------------------------- '''
    true_scroll[0] += (player.rect.x - true_scroll[0] - (TRUE_RES[0] + player.rect.width)/2)/20
    true_scroll[1] += (player.rect.y - true_scroll[1] - (TRUE_RES[1] + player.rect.height)/2)/20
    scroll = list(map(int, true_scroll.copy()))

    ''' rendering background ---------------------------------------------- '''
    for i, bg in enumerate(backgrounds):
        x_value = (-scroll[0] * bg[0]) % bg[1].get_width()

        display.blit(bg[1], (x_value, TRUE_RES[1]//2 - 100 + (75 * i) - scroll[1] * bg[0]//2))
        display.blit(bg[1], (x_value - bg[1].get_width(), TRUE_RES[1]//2 - 100 + (75 * i) - scroll[1] * bg[0]//2))

        pygame.draw.rect(
            display, bg[1].get_at((0, bg[1].get_height()-1)), 
            (0, 
            TRUE_RES[1]//2 - 100 + (75 * i) - scroll[1] * bg[0]//2 + bg[1].get_height(), 
            TRUE_RES[0], 
            TRUE_RES[1])
            )

    ''' rendering tiles --------------------------------------------------- '''
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

    ''' mouse handling ---------------------------------------------------- '''
    mouse_pos = pygame.mouse.get_pos()
    if (
        player.rect.x + player.rect.width * (TRUE_RES[0]/RES[CNT_RES][0]) 
        > mouse_pos[0] * (TRUE_RES[0]/RES[CNT_RES][0]) + scroll[0]
        ):
        player.set_flip_sprite(False, True)
    else:
        player.set_flip_sprite(False, False)

    ''' event handling, key input ----------------------------------------- '''
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
                    player.change_special_move(
                        player.all_special_moves[
                            player.all_special_moves.index(player.special_move) + 1
                        ]
                    )
            elif event.key == pygame.K_F12: # cycle resolutions
                display_reinit()
                if CNT_RES == len(RES)-1:
                    CNT_RES = 1
                else:
                    CNT_RES += 1
                screen = pygame.display.set_mode(RES[CNT_RES])
            elif event.key == pygame.K_F11:  # toggle fullscreen
                display_reinit()
                if CNT_RES == 0:
                    CNT_RES += 1
                    screen = pygame.display.set_mode(RES[CNT_RES])
                else:
                    CNT_RES = 0
                    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    RES[CNT_RES] = (screen.get_width(), screen.get_height())

                pygame.display.set_caption('Unnamed Side Scroller')
                pygame.display.set_icon(ui['icon'])

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_d:  # stop going right
                player.moving_right = False
            elif event.key == pygame.K_a:  # stop going left
                player.moving_left = False

    ''' applying movement to player (not moving him) ---------------------- '''
    l_shift_pressed = pygame.key.get_mods() & pygame.KMOD_LSHIFT
    if player.moving_right:
        player.movement[0] += player.velocity # walk right

        # dash special move
        if l_shift_pressed and player.special_move == 'dash' and player.dash_cooldown == 0:
            special_moves['dash'].play()
            player.dash_cooldown = 120
        if player.dash_cooldown > 100:
            player.movement[0] += player.velocity * ((player.dash_cooldown - 100)/15)**2 + 1

    if player.moving_left:
        player.movement[0] -= player.velocity # walk left

        # dash special move
        if l_shift_pressed and player.special_move == 'dash' and player.dash_cooldown == 0:
            special_moves['dash'].play()
            player.dash_cooldown = 120
        if player.dash_cooldown > 100:
            player.movement[0] -= player.velocity * ((player.dash_cooldown - 100)/15)**2 + 1

    ''' gravity ----------------------------------------------------------- '''
    if tools.is_visible(scroll, TRUE_RES, player.rect):
        player.y_momentum += 0.2
        player.movement[1] += player.y_momentum
        if player.y_momentum > 5:
            player.y_momentum = 5

    ''' moving the player ------------------------------------------------- '''
    if not zone_change_anim_timer:
        collisions = player.move(player.movement, tile_rects)

    ''' checking player position ------------------------------------------ '''
    # check if change map
    left_crossed = (player.rect.x + player.rect.width <= 0 
                    and not level[0] == zone_queue[0])
    right_crossed = (player.rect.x >= len(game_map['map'][0]) * TILE_SIZE 
                    and not level[0] == zone_queue[-1])

    if  (left_crossed or right_crossed) and zone_change_anim_timer == 0:
        ZONE_CHANGE_ANIM_TIMER_DEFAULT = random.randint(190, 230)
        zone_change_anim_timer = ZONE_CHANGE_ANIM_TIMER_DEFAULT

    ''' corrections, miscellanous ----------------------------------------- '''
    if player.dash_cooldown > 0:  # dash cooldown cooling down
        player.dash_cooldown -= 1
    if walking_sfx_timer > 0:  # walking sfx timer
        walking_sfx_timer -= 1
    if player.rect.y > len(game_map['map']) * TILE_SIZE:  # respawn after fall
        player.respawn()
        death_sfx.play()
    if collisions['top']:  # collision with ceiling
        player.y_momentum = 0
    if collisions['bottom']:  # jumping, collisions, walking sfx
        player.y_momentum = 0
        player.air_timer = 0
        if player.special_move == 'double_jump':
            player.additional_jumps = 1
        if (
            player.movement[0] != 0 and walking_sfx_timer == 0 
            and not collisions['left'] and not collisions['right'] 
            and abs(player.movement[0]) <= player.velocity
            ):
            walking_sfx_timer = 20 // player.velocity
            choice(walking_sfx).play()
    else:
        player.air_timer += 1

    ''' enemy mechanics, all in one loop *so it's faster* ----------------- '''
    for e in enemies:
        e.movement = [0, 0]  # setting movement

        coords = [player.rect.center[0], player.rect.center[1]]
        if e.is_detected(coords, game_map['map'], ['', 'p_p', 'S']):
            pass  # attacking
        else:
            e.move_randomly()  # moving

        e.render(display, scroll)  # displaying

    ''' displaying -------------------------------------------------------- '''
    player.render(display, scroll)

    # rendering border rects
    pygame.draw.rect(
        display, map_bottom_color, 
        [0, len(game_map['map'])*TILE_SIZE-scroll[1], TRUE_RES[0], TRUE_RES[1]]
    )
    pygame.draw.rect(
        display, map_bottom_color, 
        [-scroll[0]+len(game_map['map'][0])*TILE_SIZE, 0, TRUE_RES[0], TRUE_RES[1]]
    )
    pygame.draw.rect(
        display, map_bottom_color, 
        [-scroll[0]-TRUE_RES[0], 0, TRUE_RES[0], TRUE_RES[1]]
    )

    ''' all the hud things ------------------------------------------------ '''
    tools.blit_alpha(display, ui['hud_bottom'], [0, TRUE_RES[1]-29], 240)  # lower hud bg

    if player.hp > 0:
        pygame.draw.polygon(display, [252, 126, 124], [  # health bar
            [132, TRUE_RES[1] - 23], [139, TRUE_RES[1] - 16],
            [128 + int(228 * player.hp / 100), TRUE_RES[1] - 16], 
            [121 + int(228 * player.hp / 100), TRUE_RES[1] - 23]
        ])
    if player.special_move:
        tools.blit_alpha(display, ui[player.special_move+'_sm'], [20, TRUE_RES[1]//2 - 13], 240)  # special move icon
 
    ''' loading screen animations ----------------------------------------- '''
    if zone_change_anim_timer > 0: # swipe out to the left
        if zone_change_anim_timer > ZONE_CHANGE_ANIM_TIMER_DEFAULT - ANIM_DURATION:
            # stop music
            if zone_change_anim_timer == ZONE_CHANGE_ANIM_TIMER_DEFAULT:
                pygame.mixer.music.fadeout(500)

            i = ZONE_CHANGE_ANIM_TIMER_DEFAULT - ANIM_DURATION
            points = [
                [TRUE_RES[0], 0],
                [TRUE_RES[0], TRUE_RES[1]],
                [TRUE_RES[0] * (zone_change_anim_timer - i)/ANIM_DURATION, TRUE_RES[1]],
                [TRUE_RES[0] * (zone_change_anim_timer - i)/ANIM_DURATION, 0]
            ]
            pygame.draw.polygon(display, LOADING_SCREEN_CLR, points)

        elif zone_change_anim_timer > ANIM_DURATION:
            # set new level, reset some stuff
            if zone_change_anim_timer == ZONE_CHANGE_ANIM_TIMER_DEFAULT - ANIM_DURATION:
                if player.rect.x >= len(game_map['map'][0]) * TILE_SIZE:
                    game_map, level, spawn = change_level('R', level)
                else:
                    game_map, level, spawn = change_level('L', level)
                tiles, backgrounds = load_level(level)
                enemies = load_enemies()
                player.set_pos(
                    (spawn[0] + (TILE_SIZE - player.rect.width)//2,
                    spawn[1] + TILE_SIZE - player.rect.height)
                )
                map_bottom_color = tiles['5'].get_at((0, TILE_SIZE-1))
                true_scroll = [player.rect.x - TRUE_RES[0]//2, player.rect.y - TRUE_RES[1]//2]
                loading_screen_sfx.play() # sfx

            display.fill(LOADING_SCREEN_CLR)
            icon_size = ui['loading_icon'].get_size()
            rotated_icon = pygame.transform.rotate(ui['loading_icon'], zone_change_anim_timer*3)
            rotated_icon_size = rotated_icon.get_size()
            display.blit(
                pygame.transform.rotate(ui['loading_icon'], zone_change_anim_timer*3), 
                [
                    TRUE_RES[0]-icon_size[0]-25-rotated_icon_size[0]//2, 
                    TRUE_RES[1]-icon_size[1]-25-rotated_icon_size[1]//2
                ]
            )

        else: # swipe in from the right
            # start music
            if zone_change_anim_timer == ANIM_DURATION and not music_muted:
                pygame.mixer.music.load(f'audio/music/{level[0]}.wav')
                pygame.mixer.music.set_volume(0.02)
                pygame.mixer.music.play(-1)

            points = [
                [0, 0],
                [0, TRUE_RES[1]],
                [TRUE_RES[0] * zone_change_anim_timer/ANIM_DURATION, TRUE_RES[1]],
                [TRUE_RES[0] * zone_change_anim_timer/ANIM_DURATION, 0]
            ]
            pygame.draw.polygon(display, LOADING_SCREEN_CLR, points)
        zone_change_anim_timer -= 1

    ''' things ------------------------------------------------------------ '''
    screen.blit(pygame.transform.scale(display, RES[CNT_RES]), (0, 0))
    pygame.display.update()
    clock.tick(FPS)
