import pygame

from os import listdir
from os.path import isfile, join

pygame.init()

CAPTION = "thing"
ANIM_DELAY = 7
WIDTH = 1500
HEIGHT = 800
FPS = 60

MSPEED = 20  # max ground speed
AGILE = 5
JUMP = 1.5
FRICTION = 3
GRAVITY = 20
TERMINALVEL = 180  # max falling speed
SCROLL_WIDTH = 400  # distance from side of screen to scroll x

BLOCKS = [[i, 11, 1, 1] for i in range(20)] + [[2, 8, 1, 1], [4, 10, 1, 1]]

for i in range(len(BLOCKS)):
    for j in range(len(BLOCKS[i])):
        BLOCKS[i][j] *= 60

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


def flip_image(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


def load_sprite_sheets(path, width, height):
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
        allsprites[image.replace(".png", "") + "_right"] = sprites
        allsprites[image.replace(".png", "") + "_left"] = flip_image(sprites)
    return allsprites


def load_block(w, h):
    path = join(PATH, "terrain", "block.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((w, h), pygame.SRCALPHA, 32)
    rect = pygame.Rect(0, 0, w, h)  # (0, 0) is top-left coords. w, h is dimensions
    surface.blit(image, (0, 0), rect)
    return surface


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.SPRITES = load_sprite_sheets(join(PATH, CHARACTER), 60, 60)
        self.rect = pygame.Rect(x, y, w, h)
        self.xvel, self.yvel, self.size = 0, 0, 60
        self.mask, self.direction = None, "right"
        self.fallcount, self.jumpcount, self.animcount = 0, 0, 0

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.yvel < 0:
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

    def draw(self, wd, offset_x):
        wd.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))

    def loop(self, fps):
        self.yvel += (self.fallcount / fps) * GRAVITY  # gravity
        self.rect.x += self.xvel
        self.rect.y += self.yvel
        # friction
        if self.xvel > FRICTION:
            self.xvel -= FRICTION / 2
        elif self.xvel < -FRICTION:
            self.xvel += FRICTION / 2
        else:
            self.xvel = 0
        self.fallcount += 1
        self.update_sprite()


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, w, h)
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.w, self.h = w, h
        self.name = name

    def draw(self, wd, offset_x):
        wd.blit(self.image, (self.rect.x - offset_x, self.rect.y))


class Block(Object):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h)
        block = load_block(w, h)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


def keys(player, blocks):
    keys = pygame.key.get_pressed()
    collided = [horizontal_collision(player, blocks, i * MSPEED) for i in [-1, 1]]
    if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and not collided[0]:
        if player.direction != "left":
            player.direction, player.animcount = "left", 0
        player.xvel = -MSPEED if player.xvel <= -MSPEED + AGILE else player.xvel - AGILE
    elif (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and not collided[1]:
        if player.direction != "right":
            player.direction, player.animcount = "right", 0
        player.xvel = MSPEED if player.xvel >= MSPEED - AGILE else player.xvel + AGILE
    elif collided[0] or collided[1]:
        player.xvel = 0
    elif (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and (
        player.fallcount == 1 and player.jumpcount < 2
    ):
        player.yvel = -GRAVITY * JUMP
        player.animcount, player.jumpcount = 0, player.jumpcount + 1
        player.fallcount = 0 if player.jumpcount == 1 else player.fallcount
    vertical_collision(player, blocks)


def horizontal_collision(player, objects, dx):
    player.rect.x += dx
    player.update()
    for object in objects:
        if pygame.sprite.collide_mask(player, object):
            player.rect.x -= dx
            player.update()
            return object
    return None


def vertical_collision(player, objects):
    collided_objects = []
    for object in objects:
        if pygame.sprite.collide_mask(player, object):
            if player.yvel > 0:
                player.rect.bottom = object.rect.top
                player.fallcount, player.yvel, player.jumpcount = 0, 0, 0
            elif player.yvel < 0:
                player.rect.top = object.rect.bottom
                player.count, player.yvel = 0, -player.yvel // 2
            collided_objects.append(object)
    return collided_objects


def draw(wd, player, TILE, objects, offset_x):
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

    for object in objects:
        object.draw(wd, offset_x)

    player.draw(wd, offset_x)
    pygame.display.update()


def scroll(player, offset_x):
    if (player.rect.right - offset_x >= WIDTH - SCROLL_WIDTH and player.xvel > 0) or (
        (player.rect.left - offset_x <= SCROLL_WIDTH) and player.xvel < 0
    ):
        return offset_x + player.xvel


def main(wd):
    clock = pygame.time.Clock()
    player = Player(530, 100, 50, 50)
    blocks = [Block(i[0], i[1], i[2], i[3]) for i in BLOCKS]
    player.loop(FPS)
    offset_x = 0

    run = True
    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

        player.loop(FPS)
        keys(player, blocks)
        draw(wd, player, TILE, blocks, offset_x)
        offset_x = scroll(player, offset_x)

    pygame.quit()
    quit()


if __name__ == "__main__":
    main(wd)
