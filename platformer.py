import pygame

from os import listdir
from os.path import isfile, join

pygame.init()

CAPTION = "thing"
ANIM_DELAY = 7
WIDTH = 1000
HEIGHT = 800
FPS = 60

MSPEED = 10  # max ground speed
AGILE = 5  # ability to change direction
JUMP = 1
FRICTION = 4
GRAVITY = 20
TERMINALVEL = 180  # max falling speed
SCROLL = [300, 200]  # distance from side of screen to scroll x
RESP_BUFFER = 0  # secs before player goes back to start after dying
start_pos = [7, 6]


SPIKES = [[6, 10, 1, 1, ["out", 90]], [10, 8, 1, 1, ["out", 0]]]
BLOCKS = [
    [2, 8, 1, 1],
    [4, 6, 1, 1],
    [4, 10, 1, 1],
    [7, 10, 1, 1],
    [10, 9, 1, 1],
    [10, 11, 1, 1],
]

for i in range(len(BLOCKS)):
    for j in range(4):
        BLOCKS[i][j] *= 60

for i in range(len(SPIKES)):
    for j in range(4):
        SPIKES[i][j] *= 60

for i in range(len(start_pos)):
    start_pos[i] *= 60


PATH = "assets"
ICON = "earth_crust.png"
TILE = "bg_tile_lvl1.png"
CHARACTER = "square"

wd = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(CAPTION)
pygame.display.set_icon(pygame.image.load(join(PATH, ICON)))

# use extra player movements if you have time

# direction var combines direction and animcount,
# be sure to use turn direction into the animcount

# make a function for meters to pixels, the player
# is 0.25 meters tall

# x_vel is velocity to the right
# y_vel is velocity down

# pygame.Surface needs SRCALPHA as 2nd param


# returns rotation of sprite by angle for each obj in sprites
def rotate_image(sprites, angle):
    return [pygame.transform.rotate(sprite, angle) for sprite in sprites]


# returns list of flipped sprite for each obj in sprites (list of surfaces)
def flip_image(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


def load_sprite_sheets(path, width, height, flip=False):
    images = [f for f in listdir(path) if isfile(join(path, f))]
    allsprites = {}
    for image in images:
        spritesheet = pygame.image.load(join(path, image)).convert_alpha()
        sprites = []
        for i in range(spritesheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(spritesheet, (0, 0), rect)
            sprites.append(surface)
        if flip:
            allsprites[image.replace(".png", "") + "_right"] = sprites
            allsprites[image.replace(".png", "") + "_left"] = flip_image(sprites)
        else:
            allsprites[image.replace(".png", "")] = sprites
    return allsprites


def load_block(w, h):
    path = join(PATH, "terrain", "block.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((w, h), pygame.SRCALPHA, 32)
    rect = pygame.Rect(0, 0, w, h)  # w, h is dimensions
    surface.blit(image, (0, 0), rect)
    return surface


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.SPRITES = load_sprite_sheets(join(PATH, CHARACTER), 60, 60, True)
        self.rect = pygame.Rect(x, y, w, h)
        self.xvel, self.yvel, self.size = 0, 0, 60
        self.mask, self.direction = None, "right"
        self.fallcount, self.jumpcount, self.animcount = 0, 0, 0
        self.hit_count = 0

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit_count:
            sprite_sheet = "hit"
        elif self.yvel < 0:
            if self.jumpcount == 1:
                sprite_sheet = "jump"
            elif self.jumpcount == 2:
                sprite_sheet = "double_jump"
        elif self.yvel > GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.xvel != 0:
            sprite_sheet = "run"

        sprites = self.SPRITES[sprite_sheet + "_" + self.direction]
        self.sprite = sprites[(self.animcount // ANIM_DELAY) % len(sprites)]
        self.animcount += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, wd, offset):
        wd.blit(self.sprite, (self.rect.x - offset[0], self.rect.y - offset[1]))

    def respawn(self):
        self.rect.x, self.rect.y = start_pos[0], start_pos[1]
        self.xvel, self.yvel = 0, 0
        return 0

    def loop(self, fps, offset):
        self.yvel += (self.fallcount / fps) * GRAVITY  # gravity
        self.rect.x += self.xvel
        self.rect.y += self.yvel  # yvel is 1 iff on ground

        # friction
        if self.xvel > FRICTION:
            self.xvel -= FRICTION / 2
        elif self.xvel < -FRICTION:
            self.xvel += FRICTION / 2
        else:
            self.xvel = 0
        self.fallcount += 1
        self.update_sprite()

        if self.hit_count:
            self.hit_count += 1
        if self.hit_count > fps * RESP_BUFFER + 2:
            self.hit_count = 0
            self.respawn()
            return [0, 0]
        elif self.rect.y >= HEIGHT + 200:
            self.respawn()
            return [0, 0]
        return offset


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, w, h)
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.w, self.h = w, h
        self.name = name

    def draw(self, wd, offset):
        wd.blit(self.image, (self.rect.x - offset[0], self.rect.y - offset[1]))


class Block(Object):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h)
        block = load_block(w, h)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class Spike(Object):
    def __init__(self, x, y, w, h, pose):
        super().__init__(x, y, w, h, "spike")
        self.spike = load_sprite_sheets(join(PATH, "obstacles", "spike"), w, h)
        self.image = self.spike[pose[0]][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animcount = 0
        self.anim_name = pose

    def loop(self):
        sprites = rotate_image(self.spike[self.anim_name[0]], self.anim_name[1])
        self.image = sprites[(self.animcount // ANIM_DELAY) % len(sprites)]
        self.animcount += 1
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animcount // ANIM_DELAY > len(sprites):
            self.animcount = 0


def keys(player, objects):
    v_collide = vertical_collision(player, objects)
    h_collide = [horizontal_collision(player, objects, i * MSPEED) for i in [-1, 1]]
    for obj in [h_collide + v_collide][0]:
        if obj and obj.name == "spike":
            player.hit_count += 1

    keys = pygame.key.get_pressed()
    if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and not h_collide[0]:
        if player.direction != "left":
            player.direction, player.animcount = "left", 0
        player.xvel = -MSPEED if player.xvel <= -MSPEED + AGILE else player.xvel - AGILE
    elif (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and not h_collide[1]:
        if player.direction != "right":
            player.direction, player.animcount = "right", 0
        player.xvel = MSPEED if player.xvel >= MSPEED - AGILE else player.xvel + AGILE
    elif h_collide[0] or h_collide[1]:
        player.xvel = 0
    if (
        (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w])
        and player.fallcount == 0
        and player.jumpcount < 2
    ):
        player.yvel = -GRAVITY * JUMP
        player.animcount, player.jumpcount = 0, player.jumpcount + 1
        player.fallcount = 0 if player.jumpcount == 1 else player.fallcount


def horizontal_collision(player, objects, dx):
    player.rect.x += dx
    player.update()
    collided = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided = obj

    player.rect.x -= dx
    player.update()
    return collided


def vertical_collision(player, objects):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj) and not (
            obj.name == "spike"
            and (player.rect.y + 59 == obj.rect.y or player.rect.y - 59 == obj.rect.y)
        ):
            if player.yvel > 0:
                player.rect.bottom = obj.rect.top  # moves player to top of RECT
                player.fallcount, player.yvel, player.jumpcount = 0, 1, 0
            elif player.yvel < 0:
                player.rect.top = obj.rect.bottom  # not top of mask
                player.yvel = -player.yvel // 2
            collided_objects.append(obj)
    return collided_objects


def draw(wd, player, TILE, objects, offset):
    # background
    tile_image = pygame.image.load(join(PATH, TILE))
    _, _, tile_width, tile_height = tile_image.get_rect()
    tile_pos = []
    for i in range(WIDTH // tile_width + 10):
        for j in range(HEIGHT // tile_height + 10):
            pos = (i * tile_width, j * tile_height)
            tile_pos.append(pos)
    for TILE in tile_pos:
        wd.blit(tile_image, TILE)

    for obj in objects:
        obj.draw(wd, offset)

    player.draw(wd, offset)
    pygame.display.update()


def scroll(player, offset):
    if (player.rect.right - offset[0] >= WIDTH - SCROLL[0] and player.xvel > 0) or (
        (player.rect.left - offset[0] <= SCROLL[0]) and player.xvel < 0
    ):
        offset[0] += player.xvel
    if (player.rect.bottom - offset[1] >= HEIGHT - SCROLL[1] and player.yvel > 0) or (
        (player.rect.top - offset[1] <= SCROLL[1]) and player.yvel < 0
    ):
        offset[1] += player.yvel
    return offset


def main(wd):
    clock = pygame.time.Clock()
    player = Player(start_pos[0], start_pos[1], 60, 60)
    spikes = [Spike(i[0], i[1], i[2], i[3], i[4]) for i in SPIKES]
    blocks = [Block(j[0], j[1], j[2], j[3]) for j in BLOCKS]
    objects = spikes + blocks
    offset = [0, 0]  # offset amount up, left
    player.loop(FPS, offset)

    run = True
    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

        offset = player.loop(FPS, offset)
        for spike in spikes:
            spike.loop()
        keys(player, objects)
        draw(wd, player, TILE, objects, offset)
        offset = scroll(player, offset)

    pygame.quit()
    quit()


if __name__ == "__main__":
    main(wd)
