import pygame
import sys
import os.path


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

        if self.velocity_x != 0 and self.velocity_y != 0: # moving diagonally
            self.velocity_x /= 2 ** 0.5
            self.velocity_y /= 2 ** 0.5

    def move(self):
        self.rect = self.rect.move(self.velocity_x, self.velocity_y)

    def update(self):
        self.keyboard_input()
        self.move()


if __name__ == '__main__':
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("TDS")
    running = True
    all_sprites = pygame.sprite.Group()
    player = Player(all_sprites)
    clock = pygame.time.Clock()
    while running:
        screen.fill('black')
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            all_sprites.update()
        screen.blit(player.image, player.rect)
        player.update()

        pygame.display.update()
        clock.tick(60)
