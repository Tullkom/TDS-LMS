import pygame
import sys
import os.path
import random
import math


SCREENSIZE = (1280, 720)


money = 0
difficulty = 0


def load_image(name):
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()

    image = pygame.image.load(fullname)
    return image

def money_draw(money):
    font = pygame.font.Font(None, 50)
    text = font.render(str(money), True, (255, 255, 255))
    screen.blit(text, (10, 10))


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
                bullet = Bullet(player.rect.center, mouse_pos, all_sprites, bullets)
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
        self.rect.x, self.rect.y = [random.randint(0, SCREENSIZE[j]) for j in range(2)]
        self.max_hp = 100
        self.hp = self.max_hp
        self.pos = pygame.math.Vector2(self.rect.center)
        self.cost = 10
        self.dmg = 1

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
        self.dmg = 2
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
        self.rect.x, self.rect.y = [random.choice([random.randint(-100, 0),
                                                   random.randint(SCREENSIZE[j], SCREENSIZE[j] + 100)])
                                    for j in range(2)]
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


class Bullet(pygame.sprite.Sprite):
    image = load_image('bullet.png')

    def __init__(self, start_pos, target_pos, *group):
        super().__init__(*group)
        self.rect = self.image.get_rect(center=start_pos)
        angle = math.degrees(math.atan2(target_pos[0] - self.rect.center[0], target_pos[1] - self.rect.center[1]))
        self.image = pygame.transform.rotate(Bullet.image, int(angle))
        self.pos = pygame.math.Vector2(self.rect.center)
        self.speed = 5
        self.move = (pygame.math.Vector2(target_pos) - start_pos).normalize() * self.speed

    def update(self):
        self.pos += self.move
        self.rect.center = round(self.pos.x), round(self.pos.y)

        if (self.rect.bottom < 0 or self.rect.top > SCREENSIZE[1] or
                self.rect.right < 0 or self.rect.left > SCREENSIZE[0]):
            self.kill()


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

    while running:
        screen.fill('black')
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == DIFFEVENT:
                difficulty += 1
                font = pygame.font.Font(None, 250)
                text = font.render(str(difficulty + 1), True, (255, 255, 255))
                screen.blit(text, (SCREENSIZE[0] // 2 - text.get_rect().width // 2,
                                   SCREENSIZE[1] // 2 - text.get_rect().height // 2))
                pygame.display.update()
                pygame.time.delay(1000)
            elif event.type == DIRECTSPAWN:
                for i in range(3 + difficulty * 2):
                    enemy = DirectedEnemy(all_sprites, enemies)
            elif event.type == LINESPAWN:
                for i in range(math.floor(1 + difficulty // 2)):
                    enemy = LineEnemy(all_sprites, enemies)
                    pygame.time.set_timer(LINEGO, 500)
            elif event.type == STILLSPAWN:
                for i in range(1 + difficulty):
                    enemy = StillEnemy(all_sprites, enemies)
            elif event.type == LINEGO:
                for enemy in enemies:
                    if enemy.__class__.__name__ == 'LineEnemy':
                        enemy.go = True
                pygame.time.set_timer(LINEGO, 0)

        for enemy in enemies:
            distance = pygame.math.Vector2(enemy.rect.center).distance_to(pygame.math.Vector2(player.rect.center))
            if distance < 30:
                if enemy.__class__.__name__ == 'LineEnemy' and enemy.go:
                    player.take_damage(50)
                    enemy.kill()
                else:
                    player.take_damage(enemy.dmg)

        for bullet in bullets:
            hit_enemies = pygame.sprite.spritecollide(bullet, enemies, False)
            for enemy in hit_enemies:
                enemy.hp -= 50
                bullet.kill()
                if enemy.hp <= 0:
                    enemy.kill()
                    money += enemy.cost

        all_sprites.update()
        enemies.update()
        all_sprites.draw(screen)
        money_draw(money)

        pygame.display.update()
        clock.tick(60)
