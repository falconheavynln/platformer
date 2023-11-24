import os
import random
import math
import pygame
from os import listdir 
from os.path import isfile, join
pygame.init()

CAPTION = ""
WIDTH = 1300
HEIGHT = 900
FPS = 60
PLAYER_VEL = 5

path_assets = "C:/Users/falco/OneDrive/python/Adrian/tech_with_tim/platformer"
# "C:\Users\falco\OneDrive\python\Adrian\tech_with_tim\platfromer\Icon.png"
print(join("assets", "Background"))
ICON = "Icon.png"
pygame.image.load(join(path_assets, ICON))

# name = pygame.image.load("circle.png")
# tile_img = pygame.image.load(join("assets", "Background", name))