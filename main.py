import pygame
import sys
import os.path
import math


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
        self.speed = 2

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
            self.velocity_x /= 2 ** 0.5
            self.velocity_y /= 2 ** 0.5

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
        self.rect.x = 1280 - self.rect.width
        self.rect.y = 720 - self.rect.height


class Bullet(pygame.sprite.Sprite):
    image = load_image('bullet.png')

    def __init__(self, start_pos, target_pos, *group):
        super().__init__(*group)
        self.image = Bullet.image
        self.rect = self.image.get_rect(center=start_pos)
        self.speed = 5

        direction_x = target_pos[0] - start_pos[0]
        direction_y = target_pos[1] - start_pos[1]
        distance = math.hypot(direction_x, direction_y)
        self.velocity_x = direction_x / distance * self.speed
        self.velocity_y = direction_y / distance * self.speed

    def update(self):
        self.rect.x += self.velocity_x
        self.rect.y += self.velocity_y

        if self.rect.bottom < 0 or self.rect.top > 720 or self.rect.right < 0 or self.rect.left > 1280:
            self.kill()


if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("TDS")
    running = True

    all_sprites = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    player = Player(all_sprites)
    enemy = Enemy(all_sprites)

    clock = pygame.time.Clock()

    while running:
        screen.fill('black')
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    bullet = Bullet(player.rect.center, mouse_pos, all_sprites)

        all_sprites.update()
        all_sprites.draw(screen)

        pygame.display.update()
        clock.tick(60)
