import pygame
import sys
import random
from GAME_SETTINGS import *

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
bullet_img = pygame.image.load('img/bullet/bullet.png')
bullet_img = pygame.transform.scale(bullet_img, (
    int(bullet_img.get_width() * bullet_scale), int(bullet_img.get_height() * bullet_scale)))
grenade_img = pygame.image.load('img/grenade/grenade.png')
grenade_img = pygame.transform.scale(grenade_img,
                                     (int(grenade_img.get_width() * grenade_scale),
                                      int(grenade_img.get_height() * grenade_scale)))
# collectible items
ammo_box_img = pygame.image.load('img/ItemBox/ammo_box.png')
ammo_box_img = pygame.transform.scale(ammo_box_img, (
    int(ammo_box_img.get_width() * box_scale), int(ammo_box_img.get_height() * box_scale)))
grenade_box_img = pygame.image.load('img/ItemBox/grenade_box.png')
grenade_box_img = pygame.transform.scale(grenade_box_img, (
    int(grenade_box_img.get_width() * box_scale), int(grenade_box_img.get_height() * box_scale)))
health_box_img = pygame.image.load('img/ItemBox/health_box.png')
health_box_img = pygame.transform.scale(health_box_img, (
    int(health_box_img.get_width() * box_scale), int(health_box_img.get_height() * box_scale)))
item_boxes = {
    'ammo_box': ammo_box_img,
    'grenade_box': grenade_box_img,
    'health_box': health_box_img,
}

explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

# level images
level_img_list = []
for tile in range(TILE_TYPES):
    img = pygame.image.load(f'img/Tile/{tile}.png')
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    level_img_list.append(img)


class Soldier(pygame.sprite.Sprite):
    def __init__(self, unit_type, x, y, scale, speed, ammo, grenades):
        pygame.sprite.Sprite.__init__(self)
        self.bullet = None
        self.grenade = None
        self.alive = True
        self.move_left = False
        self.move_right = False
        self.unit_type = unit_type  # player or bot
        self.index = 0
        self.speed_y = 0
        self.max_health = 100
        self.health = self.max_health
        # player image and animation
        self.action_type = 0  # Idle Run Jump Dead
        self.animation_list = []
        self.temp_list = []
        self.image_index = 0
        self.animation_time = pygame.time.get_ticks()
        self.animation_types = ['Idle', 'Run', 'Jump', 'Dead']
        for animation in self.animation_types:
            self.temp_list = []
            for i in range(5):
                img = pygame.image.load(f"img/{self.unit_type}/{animation}/{i}.png").convert_alpha()
                img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
                self.temp_list.append(img)
            self.animation_list.append(self.temp_list)
        self.image = self.animation_list[self.action_type][self.image_index]
        self.rect = self.image.get_rect()
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.direction = 1
        self.flip = False
        self.speed = speed
        self.jump = False
        self.in_air = False
        # players_ammo
        self.ammo = ammo
        self.start_ammo = ammo
        # players_grenades
        self.grenades = grenades
        self.start_grenades = grenades

        self.rect.center = (x, y)
        self.shoot_cooldown = 0
        # ai specific attributes
        self.move_counter = 0
        self.ai_direction = 1
        self.idling = False
        self.idling_counter = 0
        self.vision_rect = pygame.Rect(0, 0, 200, 20)

    def update(self, screen_scroll=0):
        self.check_alive()
        self.update_animation()
        self.draw()
        # update cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        # scroll
        if self.unit_type == 'bot':
            self.rect.x += screen_scroll

    def check_alive(self):
        if self.health <= 0:
            self.alive = False
            self.speed = 0
            self.update_action(3)

    def move(self):
        # reset movement variables
        dx = 0
        dy = 0
        screen_scroll = 0
        # update animation for different actions
        if self.in_air:
            self.update_action(2)  # 2 - Jump animation
        elif self.move_left or self.move_right:
            self.update_action(1)  # 1 - Run animation
        else:
            self.update_action(0)  # 0 - Idle animation
        if self.move_left:
            dx = -self.speed
            self.flip = True
            self.direction = -1
        if self.move_right:
            dx = self.speed
            self.flip = False
            self.direction = 1

        # jump
        if self.jump and not self.in_air:
            self.speed_y = -25
            self.jump = False
            self.in_air = True

        # apply gravity
        self.speed_y += GRAVITY
        if self.speed_y > 10:
            self.speed_y = 10
        dy += self.speed_y

        # check collision
        for obstacle in world.obstacle_list:
            # vertical collision
            if obstacle[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                if obstacle[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                    if self.unit_type == 'bot':
                        self.direction *= -1
                # check if in the air
                if self.speed_y < 0:
                    self.speed_y = 0
                    dy = 0
                elif self.speed_y >= 0:
                    self.speed_y = 0
                    self.in_air = False
                    dy = obstacle[1].top - self.rect.bottom
            # horizontal collision
            if obstacle[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0

        # update position
        self.rect.x += dx
        self.rect.y += dy
        # collision with water
        if pygame.sprite.spritecollide(self, water_group, False):
            self.health -= 1
        # out of screen
        if self.rect.top > SCREEN_HEIGHT:
            self.health = 0
        # collision with exit
        level_complete = False
        if pygame.sprite.spritecollide(self, exit_group, False):
            level_complete = True

            pass
        # screen scrolling for player
        if self.unit_type == 'player':
            if self.rect.right > SCREEN_WIDTH - SCROLL_THRESHOLD or self.rect.left < SCROLL_THRESHOLD:
                self.rect.x -= dx
                screen_scroll = -dx
        return screen_scroll, level_complete

    def update_animation(self):
        # update animation timer
        self.image = self.animation_list[self.action_type][self.image_index]
        if pygame.time.get_ticks() - self.animation_time > ANIMATION_COOLDOWN:
            self.animation_time = pygame.time.get_ticks()
            self.image_index += 1
            # reset animation loop
            if self.image_index >= len(self.animation_list[self.action_type]):
                if self.action_type == 3:
                    self.image_index = len(self.animation_list[self.action_type]) - 1
                else:
                    self.image_index = 0

    def update_action(self, new_action):
        # Idle Run Jump Dead
        if new_action != self.action_type:
            self.action_type = new_action
            # update animation settings
            self.image_index = 0
            self.animation_time = pygame.time.get_ticks()

    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)

    def shoot(self):
        if self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = 10
            self.bullet = Bullet(self.rect.centerx + (0.7 * self.rect.size[0] * self.direction), (self.rect.centery + 0.1 * self.rect.size[1]),
                                 self.direction)
            self.ammo -= 1
            print(self.unit_type, self.ammo, " bullets left")
            bullet_group.add(self.bullet)
        return self.bullet

    def got_shot(self, damage):
        self.health -= damage
        print(self.unit_type, self.health)

    def throw_grenade(self):
        if self.grenades > 0:
            self.grenade = Grenade(self.rect.centerx + (0.2 * self.rect.size[0] * self.direction),
                                   self.rect.centery - (0.2 * self.rect.size[1]), self.direction)
            self.grenades -= 1
            # print(self.grenades, "grenades left")
        else:
            pass
        return self.grenade

    def ai(self, player, screen_scroll):
        # # scroll
        # self.rect.x += screen_scroll

        if self.alive:
            # collide vision_rect and shoot player
            if self.vision_rect.colliderect(player.rect):
                self.update_action(0)
                self.shoot()
            else:
                if random.randint(1, 200) == 1:
                    self.idling = True
                    self.update_action(0)
                    self.idling_counter = 50
                if not self.idling:
                    if self.ai_direction == 1:
                        self.move_right = True
                        self.move_left = not self.move_right
                    else:
                        self.move_left = True
                        self.move_right = not self.move_left
                    self.move()
                    self.vision_rect.center = (self.rect.centerx + (self.direction * 100), self.rect.centery)
                    # pygame.draw.rect(screen, RED, self.vision_rect)
                    self.move_counter += 1
                    if self.move_counter > TILE_SIZE * 2:
                        self.ai_direction *= -1
                        self.move_counter *= -1
                else:
                    self.idling_counter -= 1
                    if self.idling_counter < 0:
                        self.idling = False


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 7
        self.image = bullet_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction

    def update(self, soldier, enemy_group, bullet_group, screen_scroll):
        # move bullet + screen scroll
        self.rect.x += self.speed * self.direction + screen_scroll
        # check if out of screen
        if self.rect.left > (SCREEN_WIDTH + 150) or self.rect.right < -150:
            self.kill()
        # check collision with charecters
        if pygame.sprite.spritecollide(soldier, bullet_group, False):
            if soldier.alive:
                self.kill()
                soldier.got_shot(5)
        for enemy in enemy_group:
            if pygame.sprite.spritecollide(enemy, bullet_group, False):
                if enemy.alive:
                    self.kill()
                    enemy.got_shot(20)
        # check collision with obstacles
        for obstacle in world.obstacle_list:
            # horizontal collision
            if obstacle[1].colliderect(self.rect):
                self.kill()


class Grenade(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.timer = 100
        self.speed_y = -20
        self.speed_x = 10
        self.image = grenade_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def explode_grenade(self):
        explosion = Explosion(self.rect.x, self.rect.y)
        explosion_group.add(explosion)

    def update(self, enemy_group, player, screen_scroll):
        self.speed_y += GRAVITY
        dx = self.direction * self.speed_x
        dy = self.speed_y

        # check collision with walls
        for obstacle in world.obstacle_list:
            if obstacle[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                # check collision with walls
                self.direction *= -1
            elif obstacle[1].colliderect(self.rect.x + dx, self.rect.y + dy, self.width, self.height):
                # check collision with floor
                if self.speed_y >= 0:
                    self.speed_y = 0
                    dy = obstacle[1].top - self.rect.bottom
                    dx = 0
                # moves up and hits bottom of obstacle
                else:
                    self.speed_y = 0
                    dy = obstacle[1].bottom - self.rect.top

        self.rect.x += dx + screen_scroll
        self.rect.y += dy
        self.timer -= 1
        if self.timer <= 0:
            self.kill()
            print("BOOM")
            self.explode_grenade()
            # do explosion damage
            for enemy in enemy_group:
                if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE * 2 and abs(
                        self.rect.centery - enemy.rect.centery) <= TILE_SIZE * 2:
                    enemy.health -= 80
                    print(f'enemy health: ', enemy.health)
            # do damage to player
            if abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 2 and abs(
                    self.rect.centery - player.rect.centery) <= TILE_SIZE * 2:
                player.health -= 30
                print(f'player health: ', player.health)


class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        for i in range(5):
            img = pygame.image.load(f"img/explosion/{i}.png").convert_alpha()
            img = pygame.transform.scale(img, (
                int(img.get_width() * EXPLOSION_SCALE), int(img.get_height() * EXPLOSION_SCALE)))
            self.images.append(img)
        self.frame_index = 0
        self.image = self.images[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.counter = 0

    def update(self, screen_scroll):
        self.rect.x += screen_scroll
        self.counter += 1
        # explosion animation
        if self.counter >= EXPLOSION_SPEED:
            self.counter = 0
            self.frame_index += 1
            # if animation is complete
            if self.frame_index >= len(self.images):
                self.kill()
            else:
                self.image = self.images[self.frame_index]


class ItemBox(pygame.sprite.Sprite):
    def __init__(self, item_type, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.item_type = item_type
        self.image = item_boxes[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.center = (x + TILE_SIZE // 2, y + TILE_SIZE // 2)

    def update(self, player, screen_scroll):
        if pygame.sprite.collide_rect(self, player):
            print(self)
            # check collision with player
            if self.item_type == 'ammo_box':
                player.ammo += 30
                # print(f'ammo box collected')
                print(f'{player.ammo} bullets left')
                self.kill()
            elif self.item_type == 'grenade_box':
                player.grenades += 5
                # print(f'grenade box collected')
                print(f'{player.grenades} grenades left')
                self.kill()
            elif self.item_type == 'health_box':
                player.health += 60
                # print(f'health box collected')
                if player.health > player.max_health:
                    player.health = player.max_health
                print(f'{player.health} health')
                self.kill()

        self.rect.x += screen_scroll

    def __str__(self):
        return f'{self.item_type} collected'


class World:
    def __init__(self):
        self.level_length = None
        self.obstacle_list = []

    def process_data(self, data):
        self.level_length = len(data[0])
        # iterate through  level data
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    img = level_img_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * TILE_SIZE
                    img_rect.y = y * TILE_SIZE
                    tile_data = (img, img_rect)
                    if 0 <= tile <= 8:
                        self.obstacle_list.append(tile_data)
                    elif 0 <= tile <= 10:
                        water = Water(img, x * TILE_SIZE, y * TILE_SIZE)
                        water_group.add(water)
                    elif 11 <= tile <= 14:
                        decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
                        decoration_group.add(decoration)
                    elif tile == 17:
                        item = ItemBox('ammo_box', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item)
                    elif tile == 18:
                        item = ItemBox('grenade_box', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item)
                    elif tile == 19:
                        item = ItemBox('health_box', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item)
                    elif tile == 20:
                        exit = Exit(img, x * TILE_SIZE, y * TILE_SIZE)
                        exit_group.add(exit)
                    elif tile == 15:
                        # create player
                        player_soldier = Soldier('player', x * TILE_SIZE, y * TILE_SIZE - 1, 0.2, 3, 30, 5)
                    elif tile == 16:
                        # create enemies
                        bot = Soldier('bot', x * TILE_SIZE, y * TILE_SIZE - 1, 0.2, 1, 300, 0)
                        enemy_group.add(bot)
        return player_soldier

    def empty(self):
        self.obstacle_list = []

    def draw(self, screen_scroll):
        for tile in self.obstacle_list:
            tile[1][0] += screen_scroll
            screen.blit(tile[0], tile[1])


class Decoration(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + TILE_SIZE - self.image.get_height())

    def update(self, screen_scroll):
        self.rect.x += screen_scroll


class Water(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + TILE_SIZE - self.image.get_height())

    def update(self, screen_scroll):
        self.rect.x += screen_scroll


class Exit(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + TILE_SIZE - self.image.get_height())

    def update(self, screen_scroll):
        self.rect.x += screen_scroll


world = World()
