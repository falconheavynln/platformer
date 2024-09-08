import pygame
from level import LEVELS
from layer import LAYERS

from os import listdir
from os.path import isfile, join

pygame.init()

CAPTION = "monochrome"
ANIM_DELAY = 7
WIDTH = 1000
HEIGHT = 800
FPS = 60

MSPEED = 10  # max ground speed
AGILE = 5  # ability to change direction
JUMP = 1
FRICTION = 2.5
GRAVITY = 20
TERMINALVEL = 180  # max falling speed
SCROLL = [300, 200]  # distance from side of screen to scroll x, y
RESP_BUFFER = 0.15  # secs before player goes back to start after dying
BOUNCE_STRENGTH = 35  # amount bouncepads bounce

PATH = "assets"
ICON = join("objects", "goal.png")
TILES = [f"bg_tile_lvl{i + 1}.png" for i in range(4)]
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


def process_levels(levels):
    start_pos = []
    objects = [Spike, Block, Bouncepad, Goal]
    obj_names = ["spike", "block", "bouncepad", "goal"]
    for level_index in range(len(levels)):
        for obj_index in range(len(levels[level_index])):
            if obj_index == 0:
                start_pos.append([(60 * levels[level_index][0][i]) for i in [0, 1]])
            else:
                obj_info = levels[level_index][obj_index]
                for obj_name_index in range(len(obj_names)):
                    if obj_info[4][0] == obj_names[obj_name_index]:
                        obj = obj_name_index
                levels[level_index][obj_index] = (
                    objects[obj]([obj_info[i] * 60 for i in range(4)])
                    if obj not in [0, 2]
                    else objects[obj](
                        [obj_info[i] * 60 for i in range(4)], obj_info[4][1]
                    )
                )
        levels[level_index] = levels[level_index][1:]
    print(levels, start_pos)
    return levels, start_pos


def process_layers(layers):
    classed_layers = []
    for lvl_layers in layers:
        classed_layers.append([])
        if lvl_layers:
            classed_layers[-1].append(
                [
                    Layer(
                        [layer[0][i] * 60 for i in range(4)],
                        join(PATH, "layers", layer[1] + ".png"),
                    )
                    for layer in lvl_layers
                ]
            )
        else:
            classed_layers[-1].append(None)

    print(classed_layers, "ffffffffffffffffffffffffff")
    return classed_layers


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


class Layer:
    def __init__(self, space, path):
        self.space = space
        print(self.space)
        self.path = path
        self.rect = pygame.Rect(space[0], space[1], space[2], space[3])
        self.image = pygame.Surface((space[2], space[3]), pygame.SRCALPHA, 32)
        self.image.blit(pygame.image.load(path).convert_alpha(), (0, 0), self.rect)

    def draw(self, offset):
        wd.blit(self.image, (self.space[0] - offset[0], self.space[1] - offset[1]))


class Player(pygame.sprite.Sprite):
    def __init__(self, start, w, h):
        super().__init__()
        self.SPRITES = load_sprite_sheets(join(PATH, CHARACTER), w, h, True)
        self.rect = pygame.Rect(start[0][0], start[0][1], w, h)
        self.xvel, self.yvel, self.size = 0, 0, w
        self.mask, self.direction = None, "right"
        self.fallcount, self.animcount = 0, 0
        self.hit_count, self.start = 0, start

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
        return center(self)

    def loop(self, fps, offset, level_num):
        if self.yvel == 1:
            self.yvel = 0
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
            return self.respawn(level_num)
        elif self.rect.y >= HEIGHT + 200:
            return self.respawn(level_num)
        return offset


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


def keys(player, objects, level_num, bounced):
    boing = False
    v_collide = vertical_collision(player, objects)
    h_collide = [horizontal_collision(player, objects, i * MSPEED) for i in [-1, 1]]
    for obj in h_collide + v_collide:
        if obj and obj != "non-bounce":
            if obj.name == "spike":
                player.hit_count += 1
            elif obj.name == "goal":
                level_num += 1
                player.respawn(level_num)
            elif obj.name == "bouncepad":
                obj.bounced += 1
                boing = True
                if obj.angle == 0:
                    player.yvel = -BOUNCE_STRENGTH
                elif obj.angle == 90:
                    player.xvel = -BOUNCE_STRENGTH
                elif obj.angle == 180:
                    player.yvel = BOUNCE_STRENGTH
                elif obj.angle == 270:
                    player.xvel = BOUNCE_STRENGTH

    keys = pygame.key.get_pressed()
    if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and (not h_collide[0]):
        if player.direction != "left":
            player.direction, player.animcount = "left", 0
        player.xvel = -MSPEED if player.xvel <= -MSPEED + AGILE else player.xvel - AGILE
    elif (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and (not h_collide[1]):
        if player.direction != "right":
            player.direction, player.animcount = "right", 0
        player.xvel = MSPEED if player.xvel >= MSPEED - AGILE else player.xvel + AGILE
    elif not boing and h_collide[0] != "non-bounce" and h_collide[1] != "non-bounce":
        if h_collide[0]:
            player.xvel, player.rect.x = 0, h_collide[0].rect.right
        if h_collide[1]:
            player.xvel, player.rect.x = 0, h_collide[1].rect.left - player.rect.w
    if (keys[pygame.K_UP] or keys[pygame.K_w]) and player.fallcount == 0:
        player.yvel, player.animcount, player.fallcount = -GRAVITY * JUMP, 0, 0
    return level_num, bounced


def horizontal_collision(player, objects, dx):
    def check_pos(direction):
        player.rect.x = player.rect.x + dx * direction
        player.update()

    check_pos(1)
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if not (
                obj.name == "bouncepad"
                and (
                    (
                        obj.rect.x
                        in [
                            player.rect.x + i
                            for i in range(player.rect.w - MSPEED, player.rect.w + 1)
                        ]
                        and obj.angle == 270
                    )
                    or (
                        obj.rect.x
                        in [
                            player.rect.x - i
                            for i in range(player.rect.w - MSPEED, player.rect.w + 1)
                        ]
                        and obj.angle == 90
                    )
                )
            ):
                check_pos(-1)
                return obj
            else:
                check_pos(-1)
                return "non-bounce"
    check_pos(-1)
    return None


def vertical_collision(player, objects):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj) and not (
            obj.name == "spike"
            and (
                (
                    obj.rect.right
                    in [
                        col_obj.rect.x
                        for col_obj in collided_objects
                        if col_obj.name in ["block", "bouncepad"]
                    ]
                )
                or obj.rect.x - 60
                in [
                    col_obj.rect.x
                    for col_obj in collided_objects
                    if col_obj.name in ["block", "bouncepad"]
                ]
            )
        ):
            if not (
                obj.name == "bouncepad"
                and (
                    (
                        (
                            obj.rect.y
                            in [player.rect.y + i for i in range(player.rect.h)]
                            or player.yvel == 1
                        )
                        and obj.angle == 180
                    )
                    or (
                        obj.rect.y in [player.rect.y - i for i in range(player.rect.h)]
                        and obj.angle == 0
                    )
                )
            ):
                collided_objects.append(obj)
            if player.yvel > 0:
                player.rect.bottom = obj.rect.top  # moves player to top of RECT
                player.fallcount, player.yvel = 0, 1
            elif player.yvel < 0:
                player.rect.top = obj.rect.bottom  # not top of mask
                player.yvel = -player.yvel // 2
    return collided_objects


def draw(wd, player, tile, objects, layers, offset):
    tile_image = pygame.image.load(join(PATH, tile))
    _, _, tile_width, tile_height = tile_image.get_rect()
    _ = [
        [
            wd.blit(tile_image, (i * tile_width, j * tile_height))
            for j in range(HEIGHT // tile_height + 10)
        ]
        for i in range(WIDTH // tile_width + 10)
    ]
    _ = [obj.draw(offset) for obj in objects]
    _ = [layer[0].draw(offset) for layer in layers]
    player.draw(offset)

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
    layers = process_layers(LAYERS)
    print(layers)
    clock = pygame.time.Clock()
    player = Player(start_pos, 60, 60)
    level_num, bounced, offset = 4, 0, center(player)  # offset amount up, left

    run = True
    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

        level = levels[level_num - 1]
        lvl_layers = layers[level_num - 1]
        leveltile = join("background", TILES[level_num - 1])
        offset = player.loop(FPS, offset, level_num)
        _ = [obj.loop() for obj in level if obj.name == "bouncepad"]
        level_num, bounced = keys(player, level, level_num, bounced)
        draw(wd, player, leveltile, level, lvl_layers, offset)
        offset = scroll(player, offset)

    pygame.quit()
    quit()


if __name__ == "__main__":
    main(wd)
