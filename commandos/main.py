import pygame
import sys
import csv
from GAME_SETTINGS import *

from pygame.sprite import Group, Sprite, Group

from entities import *

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
level = 1

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

pygame.display.set_caption("Commandos v 1.0")
clock = pygame.time.Clock()
FPS = 60
clock.tick(FPS)

jump = False
run = True
shoot = False
grenade = False
grenade_thrown = False
start_game = False

screen_scroll = 0
background_scroll = 0

font = pygame.font.SysFont(' Comic Sans', 20)
MENU_COLOR = (34, 65, 169)


# loading levels
def load_level(current_level=1):
    world_data = []
    for row in range(ROWS):
        r = [-1] * COLS
        world_data.append(r)

    with open(f'levels/{current_level}.csv', newline='') as csvfile:
        read = csv.reader(csvfile, delimiter=',')
        for x, row in enumerate(read):
            for y, tile in enumerate(row):
                world_data[x][y] = int(tile)
    player = world.process_data(world_data)
    return player


def empty_level():
    # empty groups for level restart
    bullet_group.empty()
    item_box_group.empty()
    grenade_group.empty()
    explosion_group.empty()
    decoration_group.empty()
    water_group.empty()
    exit_group.empty()
    enemy_group.empty()
    player.kill()
    world.empty()


# world_data = load_level(level)

# player = world.process_data(world_data)
player = load_level(level)

# load background images
wall_img = pygame.image.load('img/background/wall.png').convert_alpha()
city_img = pygame.image.load('img/background/city.png').convert_alpha()
sky_img = pygame.image.load('img/background/sky.png').convert_alpha()


def draw_bg():
    # screen.fill((235, 235, 225))
    for x in range(10):
        screen.blit(sky_img, (x * sky_img.get_width() - background_scroll - SCROLL_THRESHOLD, 0))
        screen.blit(city_img, (
            x * city_img.get_width() - background_scroll - SCROLL_THRESHOLD,
            SCREEN_HEIGHT - city_img.get_height() - 200))
        screen.blit(wall_img, (
            x * wall_img.get_width() - background_scroll - SCROLL_THRESHOLD, SCREEN_HEIGHT - wall_img.get_height() -20))


def draw_text(text, text_font, textw_color, x, y):
    img = font.render(text, True, textw_color)
    screen.blit(img, (x, y))


while run:
    if start_game == False:
        # game menu
        screen.fill(MENU_BG)
        draw_text("CONTROLS:", font, MENU_COLOR, 10, 10)
        draw_text("W,A,S,D - move", font, MENU_COLOR, 10, 40)
        draw_text("Q - throw grenade", font, MENU_COLOR, 10, 60)
        draw_text("SPACE - shoot", font, MENU_COLOR, 10, 80)
        draw_text("PRESS ENTER TO START THE GAME", font, MENU_COLOR, SCREEN_WIDTH // 2 - 190, SCREEN_HEIGHT // 2)
        draw_text("PRESS 'R' TO RESTART LEVEL", font, MENU_COLOR, SCREEN_WIDTH // 2 - 190, SCREEN_HEIGHT // 2 + 20)
    else:
        draw_bg()
        # draw world
        world.draw(screen_scroll)
        draw_text(f'Health: {player.health} %', font, MENU_COLOR, SCREEN_WIDTH - 150, 10)
        draw_text(f'Ammo: {player.ammo}', font, MENU_COLOR, SCREEN_WIDTH - 150, 50)
        draw_text(f'Grenades: {player.grenades}', font, MENU_COLOR, SCREEN_WIDTH - 150, 30)

        clock.tick(FPS)
        # draw decorations before other groups
        decoration_group.update(screen_scroll)
        decoration_group.draw(screen)

        player.update()
        if player.alive:
            screen_scroll, level_complete = player.move()
            if level_complete:
                level += 1
                empty_level()
                player = load_level(level)
            background_scroll -= screen_scroll
            endgame_cooldown = pygame.time.get_ticks()
        else:
            screen_scroll = 0
            if pygame.time.get_ticks() - endgame_cooldown > ANIMATION_COOLDOWN * 6:
                background_scroll = 0
                start_game = False

        for enemy in enemy_group:
            enemy.update(screen_scroll)
            if enemy.alive:
                enemy.ai(player, screen_scroll)
            else:
                enemy.draw()
                enemy.update_animation()

        # update and draw groups
        bullet_group.draw(screen)
        bullet_group.update(player, enemy_group, bullet_group, screen_scroll)

        item_box_group.draw(screen)
        item_box_group.update(player, screen_scroll)

        grenade_group.draw(screen)
        grenade_group.update(enemy_group, player, screen_scroll)

        explosion_group.draw(screen)
        explosion_group.update(screen_scroll)

        exit_group.draw(screen)
        exit_group.update(screen_scroll)

        water_group.update(screen_scroll)
        water_group.draw(screen)
    # shooting
    if shoot:
        player.shoot()
    elif grenade and not grenade_thrown and player.grenades:
        player.throw_grenade()
        grenade_group.add(player.grenade)
        grenade_thrown = True
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        # press button
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a or event.key == pygame.K_LEFT:
                player.move_left = True
            if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                player.move_right = True
            if event.key == pygame.K_w:
                player.jump = True
            if event.key == pygame.K_SPACE:
                shoot = True
            if event.key == pygame.K_q:
                grenade = True
                grenade_thrown = False
        # release button
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a or event.key == pygame.K_LEFT:
                player.move_left = False
            if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                player.move_right = False
            if event.key == pygame.K_SPACE:
                shoot = False
            if event.key == pygame.K_q:
                grenade = False
            if event.key == pygame.K_RETURN:
                start_game = True
            if event.key == pygame.K_ESCAPE:
                start_game = not start_game
            if event.key == pygame.K_r:
                empty_level()
                player = load_level(level)
                start_game = True
    pygame.display.update()

pygame.quit()
sys.exit()
