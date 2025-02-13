import pygame
import sys
import os.path
import random
import math
import sqlite3
from datetime import datetime

pygame.mixer.init()
all_sprites = pygame.sprite.Group()
bullets = pygame.sprite.Group()
enemies = pygame.sprite.Group()
enemy_bullets = pygame.sprite.Group()
player_sprite = pygame.sprite.Group()
particles = pygame.sprite.Group()

SCREENSIZE = (1280, 720)
money = 0
difficulty = 0
score = 0
wave_seconds = 0

player_shot_sounds = [pygame.mixer.Sound(os.path.join('data', 'shot' + str(i) + '.wav')) for i in range(1, 5)]
shot_sounds = [pygame.mixer.Sound(os.path.join('data', 'player_shoot' + str(i) + '.wav')) for i in range(1, 9)]
wave_sound = pygame.mixer.Sound(os.path.join('data', 'wave.wav'))
button_sound = pygame.mixer.Sound(os.path.join('data', 'button.mp3'))
buying_sound = pygame.mixer.Sound(os.path.join('data', 'buying.mp3'))
score_sound = pygame.mixer.Sound(os.path.join('data', 'score.wav'))

pygame.init()
font = pygame.font.Font(None, 50)
screen = pygame.display.set_mode((SCREENSIZE[0], SCREENSIZE[1]))
pygame.display.set_caption("TDS")

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
    cursor.execute('INSERT INTO game_history (timestamp, waves, score) VALUES (?, ?, ?)', (timestamp, waves + 1, score))
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

def fade_out(player_only):
    fade_surface = pygame.Surface(SCREENSIZE)
    fade_surface.fill((0, 0, 0))

    for alpha in range(255, -1, -5):
        screen.fill('black')
        fade_surface.set_alpha(alpha)
        if player_only:
            all_sprites.update()
            all_sprites.draw(screen)
            screen.blit(fade_surface, (0, 0))
        else:
            money_draw(0)
            score_draw(0)
            wave_bar_draw()
            screen.blit(fade_surface, (0, 0))
            all_sprites.update()
            all_sprites.draw(screen)
        pygame.time.delay(1)
        pygame.display.update()

def fade_in(money, score):
    fade_surface = pygame.Surface(SCREENSIZE)
    fade_surface.fill((0, 0, 0))

    for alpha in range(0, 255, 1):
        fade_surface.set_alpha(alpha)
        money_draw(money)
        score_draw(score)
        wave_bar_draw()
        all_sprites.update()
        all_sprites.draw(screen)
        particles.update()
        screen.blit(fade_surface, (0, 0))
        pygame.time.delay(5)
        pygame.display.update()
        if money > 0:
            money -= 1
    return True

class Button:
    def __init__(self, text, x, y, width, height):
        self.text = text
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.rect.Rect(x, y, width, height)

    def draw(self, screen, font):
        text_surface = font.render(self.text, True, 'white')
        text_rect = text_surface.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
        screen.blit(text_surface, text_rect)

def draw_texts(buttons, history_data, mode=None):
    title_font = pygame.font.Font(None, 100)
    title_text = title_font.render("Top Down Shooter", True, 'white')
    title_rect = title_text.get_rect(center=(buttons[0].x + 100, buttons[0].y - 150))
    screen.blit(title_text, title_rect)
    if mode == 'history':
        title_font = pygame.font.Font(None, 70)
        title_text = title_font.render("Game History", True, 'white')
        title_rect = title_text.get_rect(center=(SCREENSIZE[0] // 2 + buttons[3].x - 50, 100))
        screen.blit(title_text, title_rect)
        y_offset = 150
        if history_data:
            for row in history_data:
                entry_text = f"{row[1]} | Wave: {row[2]} | Score: {row[3]}"
                text_surface = font.render(entry_text, True, 'white')
                screen.blit(text_surface, (buttons[3].x, y_offset))
                y_offset += 40
        else:
            no_data_text = font.render("No game history available.", True, 'white')
            screen.blit(no_data_text, (buttons[3].x, y_offset))

def draw_gameover_texts(floor_score, text_y):
    font_big = pygame.font.Font(None, 150)

    game_over_text = font_big.render(f"Game Over", True, (255, 255, 255))
    screen.blit(game_over_text,
                game_over_text.get_rect(topleft=(SCREENSIZE[0] // 14, text_y - 200)))

    font = pygame.font.Font(None, 100)

    score_text = font.render("Score:", True, (255, 255, 255))
    screen.blit(score_text, score_text.get_rect(topleft=(SCREENSIZE[0] // 14, text_y)))
    score_text = font_big.render(str(floor_score), True, (255, 255, 255))
    screen.blit(score_text, score_text.get_rect(center=(SCREENSIZE[0] // 2 + 250, text_y + 38)))

    play_again_text = font.render("Play Again", True, (255, 255, 255))
    play_again_rect = play_again_text.get_rect(topleft=(SCREENSIZE[0] // 14, text_y + 150))
    screen.blit(play_again_text, play_again_rect)

    go_to_menu_text = font.render("Go to Menu", True, (255, 255, 255))
    go_to_menu_rect = go_to_menu_text.get_rect(topleft=(SCREENSIZE[0] // 14, text_y + 250))
    screen.blit(go_to_menu_text, go_to_menu_rect)
    return play_again_rect, go_to_menu_rect

def menu(menu_part, score=0):
    initialize_database()
    font = pygame.font.Font(None, 50)
    menu_part = menu_part
    score_temp = 0
    last_score = -1
    score_showed = False
    game_over_text_y = SCREENSIZE[1] * 3 // 2 - 50

    init_buttons = [Button("Start", SCREENSIZE[0] // 2 - 100, 300, 200, 50),
               Button("History", SCREENSIZE[0] // 2 - 100, 370, 200, 50),
               Button("Exit", SCREENSIZE[0] // 2 - 100, 440, 200, 50),
               Button("Back", 1330, 50, 100, 50)]
    buttons = init_buttons

    while True:
        history_data = show_history()
        while menu_part == 'main':
            font = pygame.font.Font(None, 50)
            screen.fill('black')
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()
                    if buttons[0].rect.collidepoint(x, y):
                        menu_part = 'game'
                        button_sound.play()
                    elif buttons[1].rect.collidepoint(x, y):
                        menu_part = 'history'
                        button_sound.play()
                    elif buttons[2].rect.collidepoint(x, y):
                        pygame.quit()
                        sys.exit()

            if buttons[0].x < SCREENSIZE[0] // 2 - 101:
                for button in buttons[:3]:
                    button.x += (SCREENSIZE[0] // 2 - 100 - button.x) / 100
                    button.rect = pygame.rect.Rect(button.x, button.y, button.width, button.height)
            if buttons[3].x < 1329:
                buttons[3].x -= (buttons[3].x - 1329) / 100
                buttons[3].rect = pygame.rect.Rect(buttons[3].x, buttons[3].y, buttons[3].width, buttons[3].height)

            for button in buttons:
                button.draw(screen, font)
            draw_texts(buttons, history_data, 'history')

            pygame.display.flip()

        while menu_part == 'history':
            screen.fill('black')

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    menu_part = 'main'
                    button_sound.play()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()
                    if buttons[3].rect.collidepoint(x, y):
                        menu_part = 'main'
                        button_sound.play()

            if buttons[3].x > 51:
                buttons[3].x -= (buttons[3].x - 50) / 100
                buttons[3].rect = pygame.rect.Rect(buttons[3].x, buttons[3].y, buttons[3].width, buttons[3].height)
            if buttons[0].x > -739:
                for button in buttons[:3]:
                    button.x -= (button.x + 739) / 100
                    button.rect = pygame.rect.Rect(button.x, button.y, button.width, button.height)

            for button in buttons:
                button.draw(screen, font)

            draw_texts(buttons, history_data, 'history')
            pygame.display.flip()

        while menu_part == 'game':
            screen.fill('black')
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            if buttons[0].y < 1019:
                for button in buttons[:3]:
                    button.y += (1020 - button.y) / 100
                    button.rect = pygame.rect.Rect(button.x, button.y, button.width, button.height)
            else:
                start_game()
                menu_part = 'main'
                buttons = [Button("Start", SCREENSIZE[0] // 2 - 100, 300, 200, 50),
                           Button("History", SCREENSIZE[0] // 2 - 100, 370, 200, 50),
                           Button("Exit", SCREENSIZE[0] // 2 - 100, 440, 200, 50),
                           Button("Back", 1330, 50, 100, 50)]

            for button in buttons:
                button.draw(screen, font)
            draw_texts(buttons, history_data)

            pygame.display.flip()

        while menu_part == 'game_over':
            screen.fill((0, 0, 0))
            floor_score = math.floor(score_temp)
            play_again_rect, go_to_menu_rect = draw_gameover_texts(floor_score, game_over_text_y)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    button_sound.play()
                    menu_part = 'main'

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()
                    if score_showed:
                        if play_again_rect.collidepoint(x, y):
                            menu_part = 'game_over_to_game'
                            button_sound.play()

                        elif go_to_menu_rect.collidepoint(x, y):
                            button_sound.play()
                            buttons = [Button("Start", SCREENSIZE[0] // 2 - 100, 1020, 200, 50),
                                       Button("History", SCREENSIZE[0] // 2 - 100, 1090, 200, 50),
                                       Button("Exit", SCREENSIZE[0] // 2 - 100, 1160, 200, 50),
                                       Button("Back", 1330, 50, 100, 50)]
                            font = pygame.font.Font(None, 50)
                            menu_part = 'game_over_to_main'
                    else:
                        score_temp = score

            if game_over_text_y > 311:
                game_over_text_y -= (game_over_text_y - 310) / 100

            if score_temp < score:
                score_temp += score_update(score - score_temp)
            elif not score_showed:
                score_showed = True
            if last_score != floor_score:
                pygame.mixer.stop()
                score_sound.play()

            pygame.display.update()
            last_score = floor_score

        while menu_part == 'game_over_to_main':
            screen.fill('black')
            if buttons[0].y > 301:
                for i in range(3):
                    buttons[i].y -= (buttons[i].y - init_buttons[i].y) / 100
                    buttons[i].rect = pygame.rect.Rect(buttons[i].x, buttons[i].y, buttons[i].width, buttons[i].height)
            else:
                menu_part = 'main'
                buttons = init_buttons

            if game_over_text_y > -969:
                game_over_text_y -= (game_over_text_y + 970) / 100

            for button in buttons:
                button.draw(screen, font)
            draw_texts(buttons, history_data)
            draw_gameover_texts(floor_score, game_over_text_y)

            pygame.display.flip()

        while menu_part == 'game_over_to_game':
            screen.fill('black')

            if game_over_text_y < 1589:
                game_over_text_y += (1590 - game_over_text_y) / 100
            else:
                start_game()
                game_over_text_y = SCREENSIZE[1] * 3 // 2 - 50

            draw_gameover_texts(floor_score, game_over_text_y)

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

def wave_bar_draw():
    wave_ratio = wave_seconds / 1080
    wave_rect = pygame.Rect(100, 700, 1080, 5)
    pygame.draw.rect(screen, (56, 56, 56), wave_rect)
    wave_rect[2] *= wave_ratio
    pygame.draw.rect(screen, (224, 224, 224), wave_rect)

def score_update(score):
    if score <= 10:
        return 0.01
    else:
        return score / 1000

def menu_update(coord):
    if coord <= 10:
        return 1
    else:
        return coord / 100


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
        self.cooldown = 25
        self.cd = self.cooldown
        self.multi = 0
        self.able = False

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

            random.choice(player_shot_sounds).play()

            self.cd = self.cooldown

    def update(self):
        if self.able:
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
        self.cooldown = 200
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
        self.image = pygame.transform.rotate(Bullet.image, int(angle) - rot)
        if angle <= 45:
            correction_angle = abs(angle - 45)
        else:
            correction_angle = -(angle - 45)
        self.pos = (pygame.math.Vector2(self.rect.center) +
                    pygame.math.Vector2(17, 17).rotate(correction_angle))
        self.speed = 5
        self.move = (pygame.math.Vector2(target_pos) - start_pos).rotate(rot).normalize() * self.speed
        self.rect.center = round(self.pos.x), round(self.pos.y)
        for _ in range(random.randint(2, 4)):
            PlayerParticle(self, particles)

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


class PlayerParticle(pygame.sprite.Sprite):
    def __init__(self, bullet, *groups):
        super().__init__(*groups)
        self.size = random.randint(2, 4)
        self.pos = bullet.rect.center
        self.velocity = bullet.move.rotate(random.randint(-45, 45)) * random.uniform(0.3, 0.45)

    def update(self):
        self.pos += self.velocity
        self.size -= 0.1
        pygame.draw.circle(screen, (255, 255, 255), self.pos, self.size)
        if self.size <= 0:
            self.kill()


class DeathParticle(pygame.sprite.Sprite):
    def __init__(self, player_c, *groups):
        super().__init__(*groups)
        self.size = random.randint(8, 12)
        self.pos = player_c
        self.velocity = (pygame.math.Vector2(3, 4).rotate(random.randint(-180, 180)) * random.uniform(0.6, 0.9))

    def update(self):
        self.pos += self.velocity
        self.size -= 0.2
        pygame.draw.circle(screen, (255, 255, 255), self.pos, self.size)
        if self.size <= 0:
            self.kill()


class EnemyParticle(pygame.sprite.Sprite):
    def __init__(self, bullet, *groups):
        super().__init__(*groups)
        self.size = random.randint(4, 6)
        self.pos = bullet.rect.center
        self.velocity = bullet.move.rotate(180 + random.randint(-90, 90)) * random.uniform(0.6, 0.9)

    def update(self):
        self.pos += self.velocity
        self.size -= 0.1
        pygame.draw.circle(screen, (237, 28, 36), self.pos, self.size)
        if self.size <= 0:
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
                                buying_sound.play()
                        elif 145 <= y <= 185:
                            if money >= self.current_bullet_damage_price:
                                money -= self.current_bullet_damage_price
                                Bullet.damage += self.bullet_damage_upgrade_amount
                                self.current_bullet_damage_price = int(
                                    self.current_bullet_damage_price * self.bullet_damage_price_multiplier)
                                buying_sound.play()
                        elif 195 <= y <= 235:
                            if money >= self.current_speed_price:
                                money -= self.current_speed_price
                                player.speed += self.speed_upgrade_amount
                                self.current_speed_price = int(
                                    self.current_speed_price * self.speed_price_multiplier)
                                buying_sound.play()
                        elif 245 <= y <= 285:
                            if money >= self.current_reload_price:
                                money -= self.current_reload_price
                                self.player.cooldown -= self.reload_upgrade_amount
                                self.current_reload_price = int(
                                    self.current_reload_price * self.reload_price_multiplier)
                                buying_sound.play()
                        elif 295 <= y <= 335 and player.multi < 2:
                            if money >= self.current_multi_price:
                                money -= self.current_multi_price
                                self.player.multi += self.multi_upgrade_amount
                                self.current_multi_price = int(
                                    self.current_multi_price * self.multi_price_multiplier)
                                buying_sound.play()
                        elif 445 <= y <= 500:
                            return


def initialize_game_state():
    global money, difficulty, score, all_sprites, bullets, enemies, particles, player, store, Bullet, wave_seconds
    money = 0
    difficulty = 0
    score = 0
    wave_seconds = 0
    all_sprites.empty()
    bullets.empty()
    enemies.empty()
    particles.empty()
    enemy_bullets.empty()
    player = Player(all_sprites, player_sprite)
    store = Store(player)
    Bullet.damage = 50

def exit_game():
    pygame.quit()
    sys.exit()

def start_game():
    global money, difficulty, score, all_sprites, bullets, enemies, particles, player, store, Bullet, wave_seconds

    initialize_game_state()
    fade_out(True)
    pygame.time.delay(500)
    fade_out(False)

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
    player.able = True
    game_ended = False

    while running:
        screen.fill('black')

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game_data(difficulty, score)
                menu('game_over', score=score)
                pygame.time.set_timer(GAMEOVER, 0)
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    store.open_store()

            elif event.type == DIFFEVENT:
                difficulty += 1
                font = pygame.font.Font(None, 250)
                wave_sound.play()
                text = font.render(str(difficulty + 1), True, (255, 255, 255))
                screen.blit(text, (SCREENSIZE[0] // 2 - text.get_rect().width // 2,
                                   SCREENSIZE[1] // 2 - text.get_rect().height // 2))
                pygame.display.update()
                wave_seconds = 0
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
                    for i in range(math.floor(difficulty / 2) - 1):
                        ShootingEnemy(all_sprites, enemies)
            elif difficulty > 2 and event.type == FATSPAWN:
                for i in range(math.floor(difficulty // 2)):
                    FatEnemy(all_sprites, enemies)

        for enemy in enemies:
            distance = pygame.math.Vector2(enemy.rect.center).distance_to(pygame.math.Vector2(player.rect.center))
            if distance < 30:
                player_coords = player.rect.center
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
                for i in range(random.randint(3, 5)):
                    EnemyParticle(bullet, particles)
                bullet.kill()
                random.choice(shot_sounds).play()

        for enemy_bullet in enemy_bullets:
            hit_player = pygame.sprite.spritecollide(enemy_bullet, player_sprite, False)
            if player in hit_player:
                player.take_damage(20 * (1 + difficulty / 2))
                player_coords = player.rect.center
                enemy_bullet.kill()


        if not player.alive() and not game_ended:
            save_game_data(difficulty, score)
            for _ in range(30):
                DeathParticle(player_coords, particles)
            game_ended = True

        if game_ended:
            fade_in(money, score)
            running = False
            menu('game_over', score=score)

        all_sprites.update()
        enemies.update()
        all_sprites.draw(screen)
        particles.update()
        money_draw(money)
        score_draw(score)
        wave_bar_draw()
        pygame.display.update()
        clock.tick(60)
        wave_seconds += 0.6

menu('main')