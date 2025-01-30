import pygame
import sys
import os.path
import random
import math

SCREENSIZE = (1280, 720)
money = 0
difficulty = 0
score = 0


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
        self.velocity_x = 0
        self.velocity_y = 0
        keys = pygame.key.get_pressed()

        if keys[pygame.K_w]:
            self.velocity_y = -self.speed
        if keys[pygame.K_s]:
            self.velocity_y = self.speed
        if keys[pygame.K_d]:
            self.velocity_x = self.speed
        if keys[pygame.K_a]:
            self.velocity_x = -self.speed

        if self.velocity_x != 0 and self.velocity_y != 0:
            self.velocity_x = self.velocity_x / 2 * 2 ** 0.5
            self.velocity_y = self.velocity_y / 2 * 2 ** 0.5

        if pygame.mouse.get_pressed() == (1, 0, 0):
            if not self.cd:
                mouse_pos = pygame.mouse.get_pos()
                bullet = Bullet(self.rect.center, mouse_pos, 0,  all_sprites, bullets)
                if self.multi >= 1:
                    bullet = Bullet(self.rect.center, mouse_pos, 15, all_sprites, bullets)
                    bullet = Bullet(self.rect.center, mouse_pos, -15, all_sprites, bullets)
                if self.multi > 1:
                    bullet = Bullet(self.rect.center, mouse_pos, 30, all_sprites, bullets)
                    bullet = Bullet(self.rect.center, mouse_pos, -30, all_sprites, bullets)
                self.cd = self.cooldown

    def move(self):
        self.rect = self.rect.move(self.velocity_x, self.velocity_y)

    def update(self):
        self.keyboard_input()
        self.move()
        self.draw_hp_bar(screen)
        if self.cd:
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
        hp_rect[2] *= hp_ratio
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
        self.max_hp = 100 * (1 + difficulty / 3)
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


def game_over_screen(score):
    while True:
        screen.fill((0, 0, 0))
        font = pygame.font.Font(None, 100)
        text = font.render(f"Game Over", True, (255, 0, 0))
        screen.blit(text, (SCREENSIZE[0] // 2 - text.get_rect().width // 2, SCREENSIZE[1] // 2 - 150))

        score_text = font.render(f"Your Score: {score}", True, (255, 255, 255))
        screen.blit(score_text, (SCREENSIZE[0] // 2 - score_text.get_rect().width // 2, SCREENSIZE[1] // 2 - 50))

        play_again_text = font.render("Play Again", True, (0, 255, 0))
        screen.blit(play_again_text,
                    (SCREENSIZE[0] // 2 - play_again_text.get_rect().width // 2, SCREENSIZE[1] // 2 + 50))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if SCREENSIZE[0] // 2 - play_again_text.get_rect().width // 2 <= x <= SCREENSIZE[
                    0] // 2 + play_again_text.get_rect().width // 2 and \
                        SCREENSIZE[1] // 2 + 50 <= y <= SCREENSIZE[1] // 2 + 50 + play_again_text.get_rect().height:
                    return True


def initialize_game_state():
    global money, difficulty, score, all_sprites, bullets, enemies, player, store, Bullet
    money = 0
    difficulty = 0
    score = 0
    all_sprites.empty()
    bullets.empty()
    enemies.empty()
    player = Player(all_sprites)
    store = Store(player)
    Bullet.damage = 50


if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((SCREENSIZE[0], SCREENSIZE[1]))
    pygame.display.set_caption("TDS")
    running = True
    screen.fill('black')
    font = pygame.font.Font(None, 250)
    text = font.render(str(difficulty + 1), True, (255, 255, 255))
    screen.blit(text, (SCREENSIZE[0] // 2 - text.get_rect().width // 2,
                       SCREENSIZE[1] // 2 - text.get_rect().height // 2))
    pygame.display.update()
    pygame.time.delay(1000)
    all_sprites = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    player = Player(all_sprites)
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
                    enemy = DirectedEnemy(all_sprites, enemies)
            elif event.type == LINESPAWN:
                for i in range(math.floor(1 + difficulty // 2)):
                    enemy = LineEnemy(all_sprites, enemies)
                pygame.time.set_timer(LINEGO, 500)
            elif event.type == LINEGO:
                for enemy in enemies:
                    if isinstance(enemy, LineEnemy):
                        enemy.go = True
                pygame.time.set_timer(LINEGO, 0)
            elif event.type == STILLSPAWN:
                for i in range(math.floor(1 + difficulty // 2)):
                    enemy = StillEnemy(all_sprites, enemies)
            elif difficulty > 2 and event.type == FATSPAWN:
                for i in range(math.floor(difficulty // 2)):
                    enemy = FatEnemy(all_sprites, enemies)

        for enemy in enemies:
            distance = pygame.math.Vector2(enemy.rect.center).distance_to(pygame.math.Vector2(player.rect.center))
            if distance < 30:
                if isinstance(enemy, LineEnemy) and enemy.go:
                    player.take_damage(50)
                    enemy.kill()
                else:
                    player.take_damage(enemy.dmg)

        for bullet in bullets:
            hit_enemies = pygame.sprite.spritecollide(bullet, enemies, False)
            for enemy in hit_enemies:
                enemy.hp -= Bullet.damage
                bullet.kill()
                if enemy.hp <= 0:
                    enemy.kill()
                    money += enemy.cost
                    score += math.floor(enemy.points * (1 + difficulty / 2))

        if not player.alive():
            if game_over_screen(score):
                initialize_game_state()
                continue

        all_sprites.update()
        enemies.update()
        all_sprites.draw(screen)
        money_draw(money)
        score_draw(score)
        pygame.display.update()
        clock.tick(60)

    pygame.quit()