import pygame
from level import LEVELS

from os import listdir
from os.path import isfile, join

from math import floor, ceil

pygame.init()

CAPTION = "monochrome"
ANIM_DELAY = 7
WIDTH = 1000
HEIGHT = 800
FPS = 60
GRADIENT = 3

MSPEED = 10  # max ground speed
AGILE = 5  # ability to change direction
JUMP = 1
FRICTION = 1.4
GRAVITY = 20
TERMINALVEL = 25  # max falling speed
SCROLL = [300, 200]  # distance from side of screen to scroll x, y
RESP_BUFFER = 0.15  # secs before player goes back to start after dying
BOUNCE_STRENGTH = 35  # amount bouncepads bounce

PATH = "assets"
ICON = join("objects", "goal.png")
TILES = [f"bg_tile_lvl{i + 1}.png" for i in range(4)]
CHARACTER = "anyshape_collision_test"


wd = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(CAPTION)
pygame.display.set_icon(pygame.image.load(join(PATH, ICON)))

# use extra player movements if you have time

# x_vel is velocity to the right
# y_vel is velocity down

# pygame.Surface needs SRCALPHA as 2nd param


def process_levels(levels):
    start_pos = []
    objects = [Layer, Spike, Block, Bouncepad, Goal]
    obj_names = ["layer", "spike", "block", "bouncepad", "goal"]
    for level_index in range(len(levels)):
        for obj_index in range(len(levels[level_index])):
            if obj_index == 0:
                start_pos.append([(60 * levels[level_index][0][i]) for i in [0, 1]])
            else:
                obj_info = levels[level_index][obj_index]
                for obj_name_index in range(len(obj_names)):
                    if obj_info[4][0] == obj_names[obj_name_index]:
                        obj = obj_name_index
                if obj in [2, 4, 5]:
                    levels[level_index][obj_index] = objects[obj](
                        [obj_info[i] * 60 for i in range(4)]
                    )
                elif obj == 0:
                    levels[level_index][obj_index] = objects[obj](
                        [obj_info[i] * 60 for i in range(4)],
                        join(PATH, "layers", obj_info[-1][1] + ".png"),
                    )
                else:
                    levels[level_index][obj_index] = objects[obj](
                        [obj_info[i] * 60 for i in range(4)], obj_info[4][1]
                    )
        levels[level_index] = levels[level_index][1:]
    return levels, start_pos


# returns rotation of sprite by angle clockwise for each obj in sprites
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
    path = join(PATH, "terrain", f"block{w//60}x{h//60}.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((w, h), pygame.SRCALPHA, 32)
    rect = pygame.Rect(0, 0, w, h)  # w, h is dimensions
    surface.blit(image, (0, 0), rect)
    return surface


class Player(pygame.sprite.Sprite):
    def __init__(self, start, level_num, w, h):
        super().__init__()
        self.SPRITES = load_sprite_sheets(
            join(PATH, "characters", CHARACTER), w, h, True
        )
        self.rect = pygame.Rect(start[level_num - 1][0], start[level_num - 1][1], w, h)
        self.xvel, self.yvel, self.size = 0, 0, w
        self.mask, self.direction = None, "right"
        self.fallcount, self.animcount = 0, 0
        self.hit_count, self.start = 0, start
        self.ground, self.horiz = [None, None], [None, None]
        self.collide = [None] * 4

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit_count:
            sprite_sheet = "hit"
        elif self.yvel < 0:
            sprite_sheet = "jump"
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

    def draw(self, offset):
        wd.blit(self.sprite, (self.rect.x - offset[0], self.rect.y - offset[1]))

    def respawn(self, level_num):
        self.rect.x, self.rect.y = (
            self.start[level_num - 1][0],
            self.start[level_num - 1][1],
        )
        self.xvel, self.yvel = 0, 0
        self.ground, self.horiz = [None, None], [None, None]
        self.collide = [None] * 4
        self.fallcount = 0
        return center(self)

    def loop(self, fps, objects, offset, level_num):
        self.fallcount += 1
        self.collision(objects)
        if not self.collide[3]:
            self.yvel += (self.fallcount / FPS) * GRAVITY  # gravity
        # print(self.xvel, self.yvel)

        # friction
        if self.xvel > FRICTION:
            self.xvel -= FRICTION / 2
        elif self.xvel < -FRICTION:
            self.xvel += FRICTION / 2
        else:
            self.xvel = 0
        self.update_sprite()

        if self.hit_count:
            self.hit_count += 1
        if self.hit_count > fps * RESP_BUFFER + 2:
            self.hit_count = 0
            return self.respawn(level_num)
        elif self.rect.y >= 2000:
            return self.respawn(level_num)
        return offset

    def collision(self, objects):
        def add_incr(x, y):
            self.rect.x += x
            self.rect.y += y
            self.update()

        def try_direction(x, y, object):
            add_incr(x, y)
            collided = (
                pygame.sprite.collide_mask(self, object) and object.name != "layer"
            )
            add_incr(-x, -y)
            return object if collided else None

        def find_non_collision(obj, incr, max_speed):
            orig = [self.rect.x, self.rect.y]
            for _ in range(max_speed):
                add_incr(-incr[0], -incr[1])
                if not pygame.sprite.collide_mask(self, obj):
                    return
            # print("nopp")
            self.rect.x, self.rect.y = orig[0], orig[1]

        max_speed = (
            abs(self.xvel) if abs(self.xvel) >= abs(self.yvel) else abs(self.yvel)
        )
        if max_speed == 0:
            return
        increment = [self.xvel / max_speed, self.yvel / max_speed]
        max_speed = ceil(max_speed) if max_speed < 0 else floor(max_speed)
        self.collide = [None] * 4
        direction = [i / i if i else 0 for i in [self.xvel, self.yvel]]
        # orig = self.rect
        for _ in range(max_speed):
            add_incr(increment[0], increment[1])
            for obj in objects:
                if not (pygame.sprite.collide_mask(self, obj) and obj.name != "layer"):
                    continue

                find_non_collision(obj, increment, max_speed)
                coll = [
                    try_direction(i[0], i[1], obj)
                    for i in [[-1, 0], [1, 0], [0, -1], [0, 1]]
                ]
                # print(coll)
                self.collide = [
                    obj if (coll[0] and (direction[0] <= 0)) else None,
                    obj if (coll[1] and (direction[0] >= 0)) else None,
                    obj if (coll[2] and (direction[1] <= 0)) else None,
                    obj if (coll[3] and (direction[1] >= 0)) else None,
                ]  # left, right, top, bottom
                # print(self.rect, increment, pygame.sprite.collide_mask(self, obj))
                # adjust_fracts(self.collide)
                if self.collide[0] or self.collide[1]:
                    self.xvel = 0
                    # print("horiz", self.xvel, self.yvel)
                if self.collide[2]:
                    # print("upp")
                    self.yvel = -10
                    self.fallcount = 0
                elif self.collide[3]:
                    # print("vert", self.xvel, self.yvel)
                    self.yvel = 0.001
                    self.fallcount = 0


class Object(pygame.sprite.Sprite):
    def __init__(self, space, name=None):  # space = x, y, w, h
        super().__init__()
        self.rect = pygame.Rect(space[0], space[1], space[2], space[3])
        self.image = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        self.name = name

    def draw(self, offset):
        wd.blit(self.image, (self.rect.x - offset[0], self.rect.y - offset[1]))

    def update_mask(self):
        self.mask = pygame.mask.from_surface(self.image)


class Layer(Object):
    def __init__(self, space, path):
        super().__init__(space, "layer")
        self.space = space
        self.path = path
        self.image.blit(pygame.image.load(path).convert_alpha(), (0, 0))

    def draw(self, offset):
        wd.blit(self.image, (self.rect.x - offset[0], self.rect.y - offset[1]))


class Block(Object):
    def __init__(self, space):
        super().__init__(space, "block")
        block = load_block(space[2], space[3])
        self.image.blit(block, (0, 0))
        self.update_mask()


class Spike(Object):
    def __init__(self, space, angle):
        super().__init__(space, "spike")
        self.angle = angle
        self.image = rotate_image(
            load_sprite_sheets(
                join(PATH, "objects"),
                self.rect.w,
                self.rect.h,
            )["spike"],
            self.angle,
        )[0]
        self.update_mask()


class Bouncepad(Object):
    def __init__(self, space, angle):
        super().__init__(space, "bouncepad")
        self.sprites = rotate_image(
            load_sprite_sheets(join(PATH, "objects"), self.rect.w, self.rect.h)[
                "bouncepad"
            ],
            angle,
        )
        self.image, self.animnum = self.sprites[-1], 0
        self.angle, self.bounced = angle, 0
        self.update_mask()

    def loop(self):
        self.update_mask()
        if self.bounced != 0 and self.bounced <= 5:
            self.bounced += 1
            self.image = self.sprites[(self.animnum // 2) % len(self.sprites)]
            if self.animnum // 2 > len(self.sprites):
                self.animnum = 0
            else:
                self.animnum += 1
        else:
            self.animnum, self.bounced, self.image = 0, 0, self.sprites[-1]


class Goal(Object):
    def __init__(self, space):
        super().__init__(space, "goal")
        self.image = load_sprite_sheets(
            join(PATH, "objects"), self.rect.w, self.rect.h
        )["goal"][0]
        self.update_mask()


def keys(player, level_num, bounced):
    # print(player.collide)
    for obj in player.collide:
        if obj and obj != "non-bounce":
            if obj.name == "spike":
                player.hit_count += 1
            elif obj.name == "goal":
                level_num += 1
                player.respawn(level_num)
            elif obj.name == "bouncepad":
                obj.bounced += 1
                if obj.angle == 0:
                    player.yvel = -BOUNCE_STRENGTH
                elif obj.angle == 90:
                    player.xvel = -BOUNCE_STRENGTH
                elif obj.angle == 180:
                    player.yvel = BOUNCE_STRENGTH
                elif obj.angle == 270:
                    player.xvel = BOUNCE_STRENGTH

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] or keys[pygame.K_a] and (not player.collide[0]):
        if player.direction != "left":
            player.direction, player.animcount = "left", 0
        player.xvel = -MSPEED if player.xvel <= -MSPEED + AGILE else player.xvel - AGILE
    elif keys[pygame.K_RIGHT] or keys[pygame.K_d] and (not player.collide[1]):
        if player.direction != "right":
            player.direction, player.animcount = "right", 0
        player.xvel = MSPEED if player.xvel >= MSPEED - AGILE else player.xvel + AGILE
    if (keys[pygame.K_UP] or keys[pygame.K_w]) and player.fallcount == 0:
        player.yvel, player.animcount, player.fallcount = -GRAVITY * JUMP, 0, 0
    return level_num, bounced


def t(obj):
    return min([i[1] for i in obj.mask.outline()]) + obj.rect.y


def b(obj):
    return max([i[1] for i in obj.mask.outline()]) + obj.rect.y


def l_(obj):
    return min([i[0] for i in obj.mask.outline()]) + obj.rect.x


def r(obj):
    return max([i[0] for i in obj.mask.outline()]) + obj.rect.x


def w(obj):
    return r(obj) - l_(obj)


def h(obj):
    return t(obj) - b(obj)


def draw(wd, player, tile, objects, offset):
    tile_image = pygame.image.load(join(PATH, tile))
    _, _, tile_width, tile_height = tile_image.get_rect()
    _ = [
        [
            wd.blit(tile_image, (i * tile_width, j * tile_height))
            for j in range(HEIGHT // tile_height + 10)
        ]
        for i in range(WIDTH // tile_width + 10)
    ]
    _ = [obj.draw(offset) for obj in objects + [player]]
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


def center(player):
    scroll = [0, 0]
    if not (SCROLL[0] <= player.rect.x <= WIDTH - SCROLL[0]):
        scroll[0] = player.rect.x - WIDTH / 2
    if not (SCROLL[1] <= player.rect.y <= HEIGHT - SCROLL[1]):
        scroll[1] = player.rect.y - HEIGHT / 2
    return scroll


def main(wd):
    levels, start_pos = process_levels(LEVELS)
    level_num, bounced = 4, 0  # offset amount up, left
    clock = pygame.time.Clock()
    player = Player(start_pos, level_num, 60, 60)
    offset = center(player)

    run = True
    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

        level = levels[level_num - 1]
        leveltile = join("background", TILES[level_num - 1])
        offset = player.loop(FPS, level, offset, level_num)
        _ = [obj.loop() for obj in level if obj.name == "bouncepad"]
        level_num, bounced = keys(player, level_num, bounced)
        draw(wd, player, leveltile, level, offset)
        offset = scroll(player, offset)

    pygame.quit()
    quit()


if __name__ == "__main__":
    main(wd)
