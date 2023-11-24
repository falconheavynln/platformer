import os
import random
import math
import pygame
from os import listdir 
from os.path import isfile, join

pygame.init()

CAPTION = "thing"
COLOR = (57, 24, 0)
WIDTH = 1300
HEIGHT = 900
FPS = 60

MAXSPEED = 25
AGILITY = 5
JUMP = 25
FRICTION = 4
GRAVITY = 40
TERMINALVEL = 180

# FILE = join('C:','Users','falco','OneDrive - Lake Washington School District','python','tech_with_tim','platformer')
FILE = '.'
ICON = "earth_crust.png"
TILE = "bg_tile_lvl1.png"
PLAYER_LEFT = "player_left.png"
PLAYER_RIGHT = "player_right.png"

wd = pygame.display.set_mode(flags=(pygame.RESIZABLE))
pygame.display.set_caption(CAPTION)
pygame.display.set_icon(pygame.image.load(join(FILE, ICON)))

# use extra player movements if you have time

# pose var combines direction and animation_count,
# be sure to use turn pose into the animation_count

# make a function for meters to pixels, the player
# is 0.25 meters tall

# x_vel is velocity to the right

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        self.entity = pygame.image.load(join(FILE, PLAYER_RIGHT))
        print(self.entity)
        self.xvel = 0
        self.yvel = 0
        self.xpos = x
        self.ypos = y
        self.width = 60
        self.height = 60
        self.grounded = False
        self.mask = None
        self.pose = "right"
        self.fallcount = 0
    
    def m_move(self, xdis, ydis):
        self.xpos += xdis
        self.ypos += ydis

    def m_left(self, vel):
        self.xvel = -vel
        if self.pose != "left":
            self.pose = "left"

    def m_right(self, vel):
        self.xvel = vel
        if self.pose != "right":
            self.pose = "right"

    def m_walljump(self):
        pass

    def m_crouchleft(self):
        pass

    def crouchright(self):
        pass

    def meters_pixels(self, n):
        return self.entity.w
    
    def keylink(self):
        keys = pygame.key.get_pressed()
        self.x_vel = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.entity = pygame.image.load(join(FILE, PLAYER_LEFT))
            if self.xvel <= -MAXSPEED + AGILITY:
                self.xvel = -MAXSPEED
            else:
                self.xvel -= AGILITY
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.entity = pygame.image.load(join(FILE, PLAYER_RIGHT))
            if self.xvel >= MAXSPEED - AGILITY:
                self.xvel = MAXSPEED
            else:
                self.xvel += AGILITY
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.fallcount == 0:
            self.yvel -= JUMP

    def loop(self, fps):
        if self.ypos >= 600:
            self.fallcount = 0
        else:
            self.fallcount += 1
        if self.fallcount != 0:
            self.yvel += (self.fallcount / fps) * GRAVITY # gravity
        else:
            self.yvel = 0
        self.keylink()
        self.m_move(self.xvel, self.yvel)
# friction
        if self.xvel > 0 + FRICTION / 2:
            self.xvel -= FRICTION
        elif self.xvel < 0 - FRICTION / 2:
            self.xvel += FRICTION
        else:
            self.xvel = 0
    
    def draw(self, wd):
        wd.blit(self.entity, (self.xpos, self.ypos))

def get_background(tile_name, wd):
    tile_img = pygame.image.load(join(FILE, "assets", "Background", tile_name))
    _, _, tile_width, tile_height = tile_img.get_rect()
    tile_pos = []
    for i in range(WIDTH // tile_width + 10):
        for j in range(HEIGHT // tile_height + 10):
            pos = (i * tile_width, j * tile_height)
            tile_pos.append(pos)
    return tile_pos, tile_img

def draw(wd, bg, bg_img, player):
    for TILE in bg:
        wd.blit(bg_img, TILE)
    
    player.draw(wd)
    pygame.draw.line(wd, (0,0,0),(0,600), (600, 600))
    pygame.display.update()

def main(wd):
    clock = pygame.time.Clock()
    bg, bg_img = get_background(TILE, wd)
    player = Player(100, 100, 50, 50)
    run = True
    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break
        
        player.loop(FPS)
        draw(wd, bg, bg_img, player)
    pygame.quit()
    quit()

if __name__ == "__main__":
    main(wd)
