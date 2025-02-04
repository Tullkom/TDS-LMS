import pygame
import sys
import os.path
import random
import math
import sqlite3
from datetime import datetime

all_sprites = pygame.sprite.Group()
bullets = pygame.sprite.Group()
enemies = pygame.sprite.Group()
enemy_bullets = pygame.sprite.Group()
player_sprite = pygame.sprite.Group()


SCREENSIZE = (1280, 720)
money = 0
difficulty = 0
score = 0

pygame.init()
screen = pygame.display.set_mode((SCREENSIZE[0], SCREENSIZE[1]))
pygame.display.set_caption("TDS")

font = pygame.font.Font(None, 50)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

def initialize_database():
    try:
        conn = sqlite3.connect('game_history.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                waves INTEGER,
                score INTEGER
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error initializing database: {e}")

def save_game_data(waves, score):
    conn = sqlite3.connect('game_history.db')
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('INSERT INTO game_history (timestamp, waves, score) VALUES (?, ?, ?)', (timestamp, waves, score))
    conn.commit()
    conn.close()

def show_history():
    try:
        conn = sqlite3.connect('game_history.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM game_history ORDER BY id DESC LIMIT 10')
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"Error fetching history: {e}")
        return []

class Button:
    def __init__(self, text, x, y, width, height, color, hover_color, action=None):
        self.text = text
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.hover_color = hover_color
        self.action = action

    def draw(self, screen, font):
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()

        if self.x < mouse[0] < self.x + self.width and self.y < mouse[1] < self.y + self.height:
            pygame.draw.rect(screen, self.hover_color, (self.x, self.y, self.width, self.height))
            if click[0] == 1 and self.action is not None:
                self.action()
        else:
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        text_surface = font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
        screen.blit(text_surface, text_rect)


def start_menu():
    initialize_database()
    buttons = [
        Button("Start", SCREENSIZE[0] // 2 - 100, 300, 200, 50, GREEN, (0, 150, 0), start_game),
        Button("History", SCREENSIZE[0] // 2 - 100, 370, 200, 50, (0, 128, 255), (0, 96, 224), show_game_history),
        Button("Exit", SCREENSIZE[0] // 2 - 100, 440, 200, 50, RED, (150, 0, 0), exit_game)
    ]
    while True:
        screen.fill(BLACK)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        title_font = pygame.font.Font(None, 100)
        title_text = title_font.render("Top Down Shooter", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREENSIZE[0] // 2, 150))
        screen.blit(title_text, title_rect)

        for button in buttons:
            button.draw(screen, font)

        pygame.display.flip()


def show_game_history():
    back_button = Button("Back", 50, 50, 100, 50, (0, 128, 255), (0, 96, 224), start_menu)

    while True:
        screen.fill(BLACK)

        history_data = show_history()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                start_menu()
                return

            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()

                if back_button.x < x < back_button.x + back_button.width and \
                        back_button.y < y < back_button.y + back_button.height:
                    start_menu()

        title_font = pygame.font.Font(None, 70)
        title_text = title_font.render("Game History", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREENSIZE[0] // 2, 100))
        screen.blit(title_text, title_rect)

        back_button.draw(screen, font)

        y_offset = 150
        if history_data:
            for row in history_data:
                entry_text = f"{row[1]} | Waves: {row[2]} | Score: {row[3]}"
                text_surface = font.render(entry_text, True, WHITE)
                screen.blit(text_surface, (50, y_offset))
                y_offset += 40
        else:
            no_data_text = font.render("No game history available.", True, WHITE)
            screen.blit(no_data_text, (50, y_offset))

        pygame.display.flip()

def load_image(name):
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    return image

def money_draw(money):
    font = pygame.font.Font(None, 50)
    text = font.render('Money: ' + str(money), True, (255, 255, 255))
    screen.blit(text, (10, 10))

def score_draw(score):
    font = pygame.font.Font(None, 50)
    text = font.render('Score: ' + str(score), True, (255, 255, 255))
    screen.blit(text, (SCREENSIZE[0] - 10 - text.get_rect().width, 10))


class Player(pygame.sprite.Sprite):
    image = load_image('player.png')

    def __init__(self, *group):
        super().__init__(*group)
        self.image = Player.image
        self.rect = self.image.get_rect()
        self.rect.x = SCREENSIZE[0] // 2 - self.rect.width // 2
        self.rect.y = SCREENSIZE[1] // 2 - self.rect.height // 2
        self.speed = 3
        self.max_hp = 100
        self.hp = self.max_hp
        self.cooldown = 20
        self.cd = self.cooldown
        self.multi = 0

    def keyboard_input(self):
        keys = pygame.key.get_pressed()
        velocity_x = 0
        velocity_y = 0

        if keys[pygame.K_w]:
            velocity_y = -self.speed
        if keys[pygame.K_s]:
            velocity_y = self.speed
        if keys[pygame.K_d]:
            velocity_x = self.speed
        if keys[pygame.K_a]:
            velocity_x = -self.speed

        if velocity_x != 0 and velocity_y != 0:
            velocity_x /= math.sqrt(2)
            velocity_y /= math.sqrt(2)

        self.rect.x += velocity_x
        self.rect.y += velocity_y

        self.rect.clamp_ip(screen.get_rect())

    def shoot(self):
        if pygame.mouse.get_pressed()[0] and self.cd <= 0:
            mouse_pos = pygame.mouse.get_pos()

            Bullet(self.rect.center, mouse_pos, 0, all_sprites, bullets)

            if self.multi >= 1:
                Bullet(self.rect.center, mouse_pos, 15, all_sprites, bullets)
                Bullet(self.rect.center, mouse_pos, -15, all_sprites, bullets)
            if self.multi > 1:
                Bullet(self.rect.center, mouse_pos, 30, all_sprites, bullets)
                Bullet(self.rect.center, mouse_pos, -30, all_sprites, bullets)

            self.cd = self.cooldown

    def update(self):
        self.keyboard_input()

        self.shoot()

        self.draw_hp_bar(screen)

        if self.cd > 0:
            self.cd -= 1

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.kill()

    def draw_hp_bar(self, surface):
        hp_bar_length = 50
        hp_ratio = self.hp / self.max_hp
        hp_rect = pygame.Rect(self.rect.x + self.image.get_rect().width // 2 - 25, self.rect.y - 10, hp_bar_length, 5)
        pygame.draw.rect(surface, (255, 0, 0), hp_rect)
        hp_rect.width *= hp_ratio
        pygame.draw.rect(surface, (0, 255, 0), hp_rect)


class Enemy(pygame.sprite.Sprite):
    def __init__(self, *group):
        super().__init__(*group)
        self.image = load_image('enemy.png')
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = [random.randint(50, SCREENSIZE[j] - 50) for j in range(2)]
        self.max_hp = 100
        self.hp = self.max_hp
        self.pos = pygame.math.Vector2(self.rect.center)
        self.cost = 10
        self.dmg = 1
        self.points = 1

    def update(self):
        self.draw_hp_bar(screen)

    def draw_hp_bar(self, surface):
        hp_bar_length = 50
        hp_ratio = self.hp / self.max_hp
        hp_rect = pygame.Rect(self.rect.x + self.image.get_rect().width // 2 - 25, self.rect.y - 10, hp_bar_length, 5)
        pygame.draw.rect(surface, (255, 0, 0), hp_rect)
        hp_rect[2] *= hp_ratio
        pygame.draw.rect(surface, (0, 255, 0), hp_rect)


class StillEnemy(Enemy):
    def __init__(self, *group):
        super().__init__(*group)
        self.image = load_image('still_enemy.png')
        self.max_hp = 200 * (1 + difficulty / 2)
        self.hp = self.max_hp
        self.cost = 20
        self.points = 2
        self.dmg = 2 * (1 + difficulty)
        self.image = pygame.transform.rotate(self.image, random.randint(0, 360))

    def update(self):
        super().update()


class LineEnemy(Enemy):
    def __init__(self, *group):
        super().__init__(*group)
        self.max_hp = 50
        self.hp = self.max_hp
        self.speed = 3 * (1 + difficulty / 5)
        self.move = (pygame.math.Vector2(player.rect.center) - self.rect.center).normalize() * self.speed
        self.cost = 30
        self.points = 3
        self.go = False

    def update(self):
        super().update()
        if self.go:
            self.pos += self.move
            self.rect.center = round(self.pos.x), round(self.pos.y)
            if (self.rect.bottom < 0 or self.rect.top > SCREENSIZE[1] or
                    self.rect.right < 0 or self.rect.left > SCREENSIZE[0]):
                self.kill()


class DirectedEnemy(Enemy):
    def __init__(self, *group):
        super().__init__(*group)
        self.rect.x, self.rect.y = random.choice([
            (random.randint(-100, 0), random.randint(-100, SCREENSIZE[1] + 100)),
            (random.randint(SCREENSIZE[0], SCREENSIZE[0] + 100), random.randint(-100, SCREENSIZE[1] + 100)),
            (random.randint(-100, SCREENSIZE[0] + 100), random.randint(-100, 0)),
            (random.randint(-100, SCREENSIZE[0] + 100), random.randint(SCREENSIZE[1], SCREENSIZE[1] + 100))
        ])
        self.pos = pygame.math.Vector2(self.rect.center)
        self.max_hp = 100 * (1 + difficulty / 10)
        self.hp = self.max_hp
        self.speed = 1 * (1 + difficulty / 8)
        self.cost = 5

    def update(self):
        super().update()
        move = pygame.math.Vector2(player.rect.center) - self.rect.center
        if move:
            move = move.normalize() * self.speed
            self.pos += move
            self.rect.center = round(self.pos.x), round(self.pos.y)


class FatEnemy(DirectedEnemy):
    def __init__(self, *group):
        super().__init__(*group)
        self.image = load_image('fat_enemy.png')
        self.max_hp = 200 * (1 + difficulty / 2)
        self.hp = self.max_hp
        self.speed = 0.2 * (1 + difficulty / 8)
        self.cost = 30
        self.points = 5
        self.dmg = 2 * (1 + difficulty)

    def update(self):
        super().update()
        move = pygame.math.Vector2(player.rect.center) - self.rect.center
        if move:
            move = move.normalize() * self.speed
            self.pos += move
            self.rect.center = round(self.pos.x), round(self.pos.y)


class ShootingEnemy(Enemy):
    def __init__(self, *group):
        super().__init__(*group)
        self.image = load_image('shooting_enemy.png')
        self.max_hp = 50 * (1 + difficulty / 10)
        self.hp = self.max_hp
        self.cost = 20
        self.points = 2
        self.image = pygame.transform.rotate(self.image, random.randint(0, 360))
        self.cooldown = 150
        self.cd = self.cooldown
        self.shoot_intervals = (120, 100, 80)

    def update(self):
        super().update()
        if not self.cd:
            self.cd = self.cooldown
        elif self.cd in self.shoot_intervals:
            enemy_bullet = EnemyBullet(self.rect.center, player.rect.center, all_sprites, enemy_bullets)
        self.cd -= 1


class Bullet(pygame.sprite.Sprite):
    image = load_image('bullet.png')
    damage = 50

    def __init__(self, start_pos, target_pos, rot, *group):
        super().__init__(*group)
        self.rect = self.image.get_rect(center=start_pos)
        angle = math.degrees(math.atan2(target_pos[0] - self.rect.center[0], target_pos[1] - self.rect.center[1]))
        self.image = pygame.transform.rotate(Bullet.image, int(angle))
        self.pos = pygame.math.Vector2(self.rect.center)
        self.speed = 5
        self.move = (pygame.math.Vector2(target_pos) - start_pos).rotate(rot).normalize() * self.speed

    def update(self):
        self.pos += self.move
        self.rect.center = round(self.pos.x), round(self.pos.y)

        if (self.rect.bottom < 0 or self.rect.top > SCREENSIZE[1] or
                self.rect.right < 0 or self.rect.left > SCREENSIZE[0]):
            self.kill()


class EnemyBullet(pygame.sprite.Sprite):
    image = load_image('enemy_bullet.png')

    def __init__(self, start_pos, target_pos, *group):
        super().__init__(*group)
        self.rect = self.image.get_rect(center=start_pos)
        angle = math.degrees(math.atan2(target_pos[0] - self.rect.center[0], target_pos[1] - self.rect.center[1]))
        self.image = pygame.transform.rotate(EnemyBullet.image, int(angle))
        self.pos = pygame.math.Vector2(self.rect.center)
        self.move = (pygame.math.Vector2(target_pos) - start_pos).normalize() * 5 * (1 + difficulty / 5)

    def update(self):
        self.pos += self.move
        self.rect.center = round(self.pos.x), round(self.pos.y)

        if (self.rect.bottom < 0 or self.rect.top > SCREENSIZE[1] or
                self.rect.right < 0 or self.rect.left > SCREENSIZE[0]):
            self.kill()

class Store:
    def __init__(self, player):
        self.player = player

        self.base_health_price = 50
        self.health_price_multiplier = 1.5
        self.current_health_price = self.base_health_price
        self.health_upgrade_amount = 50

        self.base_bullet_damage_price = 50
        self.bullet_damage_price_multiplier = 1.5
        self.current_bullet_damage_price = self.base_bullet_damage_price
        self.bullet_damage_upgrade_amount = 20

        self.base_speed_price = 25
        self.speed_price_multiplier = 1.5
        self.current_speed_price = self.base_speed_price
        self.speed_upgrade_amount = 0.5

        self.base_reload_price = 50
        self.reload_price_multiplier = 1.5
        self.current_reload_price = self.base_reload_price
        self.reload_upgrade_amount = 1

        self.base_multi_price = 350
        self.multi_price_multiplier = 3
        self.current_multi_price = self.base_multi_price
        self.multi_upgrade_amount = 1

    def open_store(self):
        global money
        while True:
            screen.fill((0, 0, 0))
            money_draw(money)
            font = pygame.font.Font(None, 50)
            text = font.render("Store", True, (255, 255, 255))
            screen.blit(text, (SCREENSIZE[0] // 2 - text.get_rect().width // 2, 50))

            buy_health_text = font.render(f"Buy Health ({self.current_health_price} $)", True, (255, 255, 255))
            screen.blit(buy_health_text, (SCREENSIZE[0] // 2 - buy_health_text.get_rect().width // 2, 100))

            buy_bullet_damage_text = font.render(f"Buy Bullet Damage ({self.current_bullet_damage_price} $)", True,
                                                 (255, 255, 255))
            screen.blit(buy_bullet_damage_text,
                        (SCREENSIZE[0] // 2 - buy_bullet_damage_text.get_rect().width // 2, 150))

            buy_speed_text = font.render(f"Buy Speed ({self.current_speed_price} $)", True,
                                                 (255, 255, 255))
            screen.blit(buy_speed_text,
                        (SCREENSIZE[0] // 2 - buy_speed_text.get_rect().width // 2, 200))

            buy_reload_text = font.render(f"Buy Reload ({self.current_reload_price} $)", True,
                                         (255, 255, 255))
            screen.blit(buy_reload_text,
                        (SCREENSIZE[0] // 2 - buy_reload_text.get_rect().width // 2, 250))

            if player.multi != 2:
                buy_multi_text = font.render(f"Buy Multishot ({self.current_multi_price} $)", True,
                                              (255, 255, 255))
            else:
                buy_multi_text = font.render(f"Multishot Max lvl", True,
                                              (255, 255, 255))
            screen.blit(buy_multi_text,
                        (SCREENSIZE[0] // 2 - buy_multi_text.get_rect().width // 2, 300))

            back_text = font.render("Back", True, (255, 255, 255))
            screen.blit(back_text, (SCREENSIZE[0] // 2 - back_text.get_rect().width // 2, 450))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()
                    if 360 <= x <= 920:
                        if 95 <= y <= 135:
                            if money >= self.current_health_price:
                                money -= self.current_health_price
                                self.player.max_hp += self.health_upgrade_amount
                                self.player.hp = self.player.max_hp
                                self.current_health_price = int(self.current_health_price * self.health_price_multiplier)
                        elif 145 <= y <= 185:
                            if money >= self.current_bullet_damage_price:
                                money -= self.current_bullet_damage_price
                                Bullet.damage += self.bullet_damage_upgrade_amount
                                self.current_bullet_damage_price = int(
                                    self.current_bullet_damage_price * self.bullet_damage_price_multiplier)
                        elif 195 <= y <= 235:
                            if money >= self.current_speed_price:
                                money -= self.current_speed_price
                                player.speed += self.speed_upgrade_amount
                                self.current_speed_price = int(
                                    self.current_speed_price * self.speed_price_multiplier)
                        elif 245 <= y <= 285:
                            if money >= self.current_reload_price:
                                money -= self.current_reload_price
                                self.player.cooldown -= self.reload_upgrade_amount
                                self.current_reload_price = int(
                                    self.current_reload_price * self.reload_price_multiplier)
                        elif 295 <= y <= 335 and player.multi < 2:
                            if money >= self.current_multi_price:
                                money -= self.current_multi_price
                                self.player.multi += self.multi_upgrade_amount
                                self.current_multi_price = int(
                                    self.current_multi_price * self.multi_price_multiplier)
                        elif 445 <= y <= 500:
                            return


def initialize_game_state():
    global money, difficulty, score, all_sprites, bullets, enemies, player, store, Bullet
    money = 0
    difficulty = 0
    score = 0
    all_sprites.empty()
    bullets.empty()
    enemies.empty()
    enemy_bullets.empty()
    player = Player(all_sprites)
    store = Store(player)
    Bullet.damage = 50

def exit_game():
    pygame.quit()
    sys.exit()

def start_game():
    global money, difficulty, score, all_sprites, bullets, enemies, player, store, Bullet

    initialize_game_state()

    running = True
    clock = pygame.time.Clock()

    DIFFEVENT = pygame.USEREVENT + 1
    pygame.time.set_timer(DIFFEVENT, 30000)
    DIRECTSPAWN = pygame.USEREVENT + 2
    pygame.time.set_timer(DIRECTSPAWN, 6000)
    LINESPAWN = pygame.USEREVENT + 3
    pygame.time.set_timer(LINESPAWN, 10000)
    LINEGO = pygame.USEREVENT + 4
    pygame.time.set_timer(LINEGO, 0)
    STILLSPAWN = pygame.USEREVENT + 5
    pygame.time.set_timer(STILLSPAWN, 15000)
    FATSPAWN = pygame.USEREVENT + 6
    pygame.time.set_timer(FATSPAWN, 15000)

    store = Store(player)

    test_enemy = ShootingEnemy(all_sprites, enemies)

    while running:
        screen.fill('black')

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    store.open_store()

            elif event.type == DIFFEVENT:
                difficulty += 1
                font = pygame.font.Font(None, 250)
                text = font.render(str(difficulty + 1), True, (255, 255, 255))
                screen.blit(text, (SCREENSIZE[0] // 2 - text.get_rect().width // 2,
                                   SCREENSIZE[1] // 2 - text.get_rect().height // 2))
                pygame.display.update()
                pygame.time.delay(1000)

            elif event.type == DIRECTSPAWN:
                for i in range(3 + math.floor(difficulty * 1.5)):
                    DirectedEnemy(all_sprites, enemies)

            elif event.type == LINESPAWN:
                for i in range(math.floor(1 + difficulty // 2)):
                    LineEnemy(all_sprites, enemies)
                pygame.time.set_timer(LINEGO, 500)

            elif event.type == LINEGO:
                for enemy in enemies:
                    if isinstance(enemy, LineEnemy):
                        enemy.go = True
                pygame.time.set_timer(LINEGO, 0)

            elif event.type == STILLSPAWN:
                for i in range(math.floor(1 + difficulty // 2)):
                    StillEnemy(all_sprites, enemies)
                if difficulty > 5:
                    ShootingEnemy(all_sprites, enemies)
            elif difficulty > 2 and event.type == FATSPAWN:
                for i in range(math.floor(difficulty // 2)):
                    FatEnemy(all_sprites, enemies)

        for enemy in enemies:
            distance = pygame.math.Vector2(enemy.rect.center).distance_to(pygame.math.Vector2(player.rect.center))
            if distance < 30:
                if isinstance(enemy, LineEnemy) and enemy.go:
                    player.take_damage(50 * (1 + difficulty / 4))
                    enemy.kill()
                else:
                    player.take_damage(enemy.dmg)

        for bullet in bullets:
            hit_enemies = pygame.sprite.spritecollide(bullet, enemies, False)
            for enemy in hit_enemies:
                enemy.hp -= Bullet.damage
                if enemy.hp <= 0:
                    enemy.kill()
                    money += enemy.cost
                    score += math.floor(enemy.points * (1 + difficulty / 2))
                bullet.kill()

        for enemy_bullet in enemy_bullets:
            hit_player = pygame.sprite.spritecollide(enemy_bullet, player_sprite, False)
            if player in hit_player:
                player.take_damage(20 * (1 + difficulty / 2))
                enemy_bullet.kill()


        if not player.alive():
            save_game_data(difficulty, score)
            if game_over_screen(score):
                initialize_game_state()
                continue
            else:
                running = False

        all_sprites.update()
        enemies.update()
        all_sprites.draw(screen)
        money_draw(money)
        score_draw(score)
        pygame.display.update()
        clock.tick(60)

def game_over_screen(score):
    while True:
        screen.fill((0, 0, 0))
        font = pygame.font.Font(None, 100)

        text = font.render(f"Game Over", True, (255, 0, 0))
        screen.blit(text, (SCREENSIZE[0] // 2 - text.get_rect().width // 2, SCREENSIZE[1] // 2 - 150))

        score_text = font.render(f"Your Score: {score}", True, (255, 255, 255))
        screen.blit(score_text, (SCREENSIZE[0] // 2 - score_text.get_rect().width // 2, SCREENSIZE[1] // 2 - 50))

        play_again_text = font.render("Play Again", True, (0, 255, 0))
        play_again_rect = play_again_text.get_rect(center=(SCREENSIZE[0] // 2, SCREENSIZE[1] // 2 + 100))
        screen.blit(play_again_text, play_again_rect)

        go_to_menu_text = font.render("Go to Menu", True, (255, 255, 0))
        go_to_menu_rect = go_to_menu_text.get_rect(center=(SCREENSIZE[0] // 2, SCREENSIZE[1] // 2 + 200))
        screen.blit(go_to_menu_text, go_to_menu_rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                continue

            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()

                if play_again_rect.collidepoint(x, y):
                    return True

                elif go_to_menu_rect.collidepoint(x, y):
                    pygame.time.wait(0)
                    start_menu()

start_menu()