import pygame
import sys
import os.path
import random


SCREENSIZE = (1280, 720)


def load_image(name):
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()

    image = pygame.image.load(fullname)
    return image


class Player(pygame.sprite.Sprite):
    image = load_image('player.png')

    def __init__(self, *group):
        super().__init__(*group)
        self.image = Player.image
        self.rect = self.image.get_rect()
        self.speed = 5

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

    def move(self):
        self.rect = self.rect.move(self.velocity_x, self.velocity_y)

    def update(self):
        self.keyboard_input()
        self.move()


class Enemy(pygame.sprite.Sprite):
    image = load_image('enemy.png')

    def __init__(self, *group):
        super().__init__(*group)
        self.image = Enemy.image
        self.rect = self.image.get_rect()
        self.rect.x = SCREENSIZE[0] - self.rect.width
        self.rect.y = SCREENSIZE[1] - self.rect.height
        self.max_hp = 100
        self.hp = self.max_hp

    def update(self):
        self.draw_hp_bar(screen)

    def draw_hp_bar(self, surface):
        hp_bar_length = 50
        hp_ratio = self.hp / self.max_hp

        hp_rect = pygame.Rect(self.rect.x + self.image.get_rect().width // 2 - 25, self.rect.y - 10, hp_bar_length, 5)
        pygame.draw.rect(surface, (255, 0, 0), hp_rect)
        hp_rect[2] *= hp_ratio
        pygame.draw.rect(surface, (0, 255, 0), hp_rect)


class LineEnemy(Enemy):
    def __init__(self, *group):
        super().__init__(*group)
        self.max_hp = 150
        self.hp = self.max_hp
        self.rect.x, self.rect.y = [random.randint(0, SCREENSIZE[j]) for j in range(2)]
        self.pos = pygame.math.Vector2(self.rect.center)
        self.speed = 1
        self.move = (pygame.math.Vector2(player.rect.center) - self.rect.center).normalize() * self.speed

    def update(self):
        super().update()
        self.pos += self.move
        self.rect.center = round(self.pos.x), round(self.pos.y)

        if (self.rect.bottom < 0 or self.rect.top > SCREENSIZE[1] or
                self.rect.right < 0 or self.rect.left > SCREENSIZE[0]):
            self.kill()


class Bullet(pygame.sprite.Sprite):
    image = load_image('bullet.png')

    def __init__(self, start_pos, target_pos, *group):
        super().__init__(*group)
        self.image = Bullet.image
        self.rect = self.image.get_rect(center=start_pos)
        self.pos = pygame.math.Vector2(self.rect.center)
        self.speed = 10
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

    all_sprites = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    enemies = pygame.sprite.Group()

    player = Player(all_sprites)
    enemy = Enemy(all_sprites, enemies)

    clock = pygame.time.Clock()
    for i in range(5):
        enemy = LineEnemy(all_sprites, enemies)

    while running:
        screen.fill('black')
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    bullet = Bullet(player.rect.center, mouse_pos, all_sprites, bullets)

        all_sprites.update()

        for bullet in bullets:
            hit_enemies = pygame.sprite.spritecollide(bullet, enemies, False)
            for enemy in hit_enemies:
                enemy.hp -= 50
                bullet.kill()
                if enemy.hp <= 0:
                    enemy.kill()

        all_sprites.draw(screen)
        enemies.update()

        pygame.display.update()
        clock.tick(60)
