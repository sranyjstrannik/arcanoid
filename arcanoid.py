import pygame
from pygame.locals import *
from math import pi
import os
import time
import random
import numpy as np


M_SPEED = 10
SIZE_X, SIZE_Y = 480, 640
TSIZE_X, TSIZE_Y = 15, 13
BLOCK_COUNT = 300


def load_image(name):
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname)
        if image.get_alpha is None:
            image = image.convert()
        else:
            image = image.convert_alpha()
    except:
        print('Cannot load image:', fullname)
        raise SystemExit
    return image, image.get_rect()


class Ball(pygame.sprite.Sprite):
    def __init__(self, postiton):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('ball.png')
        screen = pygame.display.get_surface()
        self.speed = (0, 0)
        self.rect = self.rect.move(*postiton)
        self.area = screen.get_rect()
        self.original_image = self.image
        self.angle = 0
        self.dangle = 1
        self.garbage_needed = False
        self.last_position = self.rect.center
        self.just_bounced = False
        self.just_bounced_timer = pygame.time.get_ticks()

    def speed_up(self, coeff):
        self.speed = tuple(min(x*coeff, M_SPEED) for x in self.speed)
        self.dangle *= coeff
        self.dangle = min(self.dangle, M_SPEED)

    def update(self):
        """Calculates new position of the ball
            and checks whenever it hits the walls
            if so, transforms it's speed vector
        """
        # TODO: нормально высчитывать столкновения
        new_position = self.rect.move(*self.speed)
        if not self.area.contains(new_position): # шарик стукнулся
            x = self.rect.move(*self.speed)
            a,b,c,d = map(self.area.collidepoint, (x.topleft, x.topright, x.bottomleft, x.bottomright))
            if (not a and not b) or (not c and not d):
                self.speed = (self.speed[0], -self.speed[1])
            if (not a and not c) or (not d and not b):
                self.speed = (-self.speed[0], self.speed[1])
            if not c and not d:
                print('Игра окончена :(')
                exit()    
        self.last_position = self.rect.center
        self.rect = self.rect.move(*self.speed)
        self.rotate(self.dangle)

    def start(self, speed=(-2, -2)):
        self.speed = speed       

    def rotate(self, angle):
        self.angle = (self.angle + angle) % 360
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        centerx = self.image.get_rect().width / 2
        centery = self.image.get_rect().width / 2
        dx = dy = self.rect.width / 2
        self.image = self.image.subsurface((centerx-dx, centery-dy, centerx+dx, centery+dy))

    def bounce(self, vertical=True, debug = False):
        self.just_bounced = pygame.time.get_ticks() - self.just_bounced_timer < 200
        if self.just_bounced: return
        self.just_bounced_timer = pygame.time.get_ticks()
        if debug: print(self.speed, vertical)
        if vertical:
            self.speed = (self.speed[0], -self.speed[1])
        else: self.speed = (-self.speed[0], self.speed[1])
        if debug: print(self.speed, vertical)



class Platform(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('platform.png')
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.speed = 0
        self.timer = pygame.time.get_ticks()
        self.rect = pygame.Rect((SIZE_X-self.rect.width, SIZE_Y-self.rect.height, self.rect.width, self.rect.height))
        self.garbage_needed = False

    def update(self):
        new_position = self.rect.move((self.speed, 0))
        if not self.area.contains(new_position.inflate((-10, 0))):
            self.stop()
            return
        self.rect = new_position
        if pygame.time.get_ticks() - self.timer > 100: self.stop()

    def left(self):
        self.speed = -10
        self.timer = pygame.time.get_ticks()

    def right(self):
        self.speed = +10
        self.timer = pygame.time.get_ticks()

    def stop(self):
        self.speed = 0


class Target(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        image, rect = load_image('targets.png')
        dx = rect.width // TSIZE_X
        dy = rect.height // TSIZE_Y
        nx = SIZE_X // dx
        ny = SIZE_Y // dy
        self.destroyed, self.destroyed_rect = load_image('regularExplosion01.png')
        self.destroyed = pygame.transform.scale(self.destroyed, (dx, dy))
        self.destroyed_rect = self.destroyed.get_rect()
        self.rect = pygame.Rect(random.uniform(1, nx-1)*dx, random.uniform(1, ny//2)*dy, dx, dy)
        self.image = image.subsurface(dx*random.uniform(0, TSIZE_X-1), dy*random.uniform(0, TSIZE_Y-1), dx, dy)
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.timer = pygame.time.get_ticks()
        self.alive = True
        self.garbage_needed = False

    def update(self):
        if not self.alive and pygame.time.get_ticks() - self.timer > 300:
            self.garbage_needed = True
        if pygame.time.get_ticks() - self.timer > 20000:
            self.rect = self.rect.move((0, 10))
            self.timer = pygame.time.get_ticks()

    def destroy(self):
        self.timer = pygame.time.get_ticks()
        self.alive = False
        self.image = self.destroyed
        self.rect = self.destroyed_rect.move(self.rect.topleft)


def main():
    pygame.init()
    screen = pygame.display.set_mode((SIZE_X, SIZE_Y))
    pygame.display.set_caption('Test text')
    pygame.mouse.set_visible(False)
    background = pygame.Surface(screen.get_size()).convert()
    background.fill((0, 0, 0))
    screen.blit(background, (0,0))
    pygame.display.flip()

    all_sprites = pygame.sprite.Group()
    targets = pygame.sprite.Group()
    ball = Ball((320, 240))
    all_sprites.add(ball)
    platform = Platform()
    all_sprites.add(platform)

    for _ in range(BLOCK_COUNT):
        t = Target()
        all_sprites.add(t)
        targets.add(t)

    clock = pygame.time.Clock()
    all_sprites.draw(screen)

    while True:
        clock.tick(120)
        if pygame.key.get_pressed()[pygame.K_LEFT] != 0:
            platform.left()
        if pygame.key.get_pressed()[pygame.K_RIGHT] != 0:
            platform.right()    
        for event in pygame.event.get():
            if event.type == QUIT:
                return
            if event.type == KEYDOWN: 
                if event.key == K_SPACE: ball.start()
                if event.key in [K_EQUALS, K_PLUS]: ball.speed_up(1.1)
                if event.key in [K_MINUS, K_UNDERSCORE]: ball.speed_up(0.9)

        for s in all_sprites:
            if s.garbage_needed: s.remove(all_sprites, targets)
        all_sprites.update()        
        hit = pygame.sprite.spritecollideany(ball, targets)
        if hit and hit.alive:
            FLAG = False
            b = ball.rect
            t = hit.rect.inflate((3,3))
            if t.collidepoint(b.topleft) and t.collidepoint(b.topright) or \
                t.collidepoint(b.bottomleft) and t.collidepoint(b.bottomright):
                ball.bounce()
            elif t.collidepoint(b.topleft) and t.collidepoint(b.bottomleft) or \
                t.collidepoint(b.topright) and t.collidepoint(b.bottomright):
                ball.bounce(vertical=False)
            else:
                FLAG = True
            if not FLAG: hit.destroy()

        if pygame.sprite.collide_rect(ball, platform):
            print('hmmm')
            ball.bounce(debug=True)

        screen.blit(background, (0,0))
        all_sprites.draw(screen)
        pygame.display.flip()


if __name__ == '__main__':
    main()