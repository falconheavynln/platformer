import pygame
from level import LEVELS
from os import listdir
from os.path import isfile, join
from random import randint
from math import floor, ceil

pygame.init()

CAPTION = "monochrome"
CHARACTER = "plus"
ICON = "goal"

ANIM_DELAY = 7
WIDTH = 1000
HEIGHT = 800
FPS = 60

MSPEED = 15  # max ground speed
AGILE = 4  # ability to change direction
JUMP = 20
FRICTION = 3
GRAVITY = 20
TERMINALVEL = 60  # max moving speed
SCROLL = [300, 200]  # distance from side of screen to scroll x, y
RESP_BUFFER = 0.15  # secs before player goes back to start after dying
BOUNCE_STRENGTH = 60  # amount bouncepads bounce

level_num = 6

# x_vel is velocity to the right
# y_vel is velocity down

# pygame.Surface needs SRCALPHA as 2nd param

PATH = "assets"
TILES = [
    f"bg_tile_lvl{i + 1}.png" for i in range(len(listdir(join(PATH, "background"))))
]

ICON = join("objects", ICON + ".png")
JUMP *= 1 / GRAVITY

wd = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(CAPTION)
pygame.display.set_icon(pygame.image.load(join(PATH, ICON)))


# returns rotation of sprite by angle clockwise for each obj in sprites
def rotate_image(sprites, angle) -> list[pygame.Surface]:
    return [pygame.transform.rotate(sprite, angle) for sprite in sprites]


# returns list of flipped sprite for each obj in sprites (list of surfaces)
def flip_image(sprites) -> list[pygame.Surface]:
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


def load_sprite_sheets(
    path, width, height, flip=False
) -> dict[str : list[pygame.Surface]]:
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


def load_block(w, h) -> pygame.Surface:
    path = join(PATH, "terrain", f"block{w//60}x{h//60}.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((w, h), pygame.SRCALPHA, 32)
    rect = pygame.Rect(0, 0, w, h)  # w, h is dimensions
    surface.blit(image, (0, 0), rect)
    return surface


def process_levels(level):
    data = []
    objects = [Layer, Spike, Block, Bouncepad, Goal]
    obj_names = ["layer", "spike", "block", "bouncepad", "goal"]
    load_text = load_sprite_sheets(join(PATH, "load"), 256, 64)["load"][0]

    wd.fill([randint(0, 255) for _ in range(3)])
    wd.blit(load_text, (WIDTH // 2 - 128, HEIGHT // 2 - 32))
    pygame.display.update()

    for obj_index in range(len(level)):
        if obj_index == 0:
            data = [i for i in level[0]]
            continue
        obj_info = level[obj_index]
        obj_rect = [obj_info[i] * 60 for i in range(4)]
        for obj_name_index in range(len(obj_names)):
            if obj_info[4][0] == obj_names[obj_name_index]:
                obj = obj_name_index
        if obj in [2, 4, 5]:
            final_obj = objects[obj](obj_rect)
        elif obj == 0:
            final_obj = objects[obj](
                obj_rect,
                join(PATH, "layers", obj_info[-1][1] + ".png"),
            )
        else:
            final_obj = objects[obj](obj_rect, obj_info[4][1])
        level[obj_index] = final_obj
    level = level[1:]
    return data, level


class Player(pygame.sprite.Sprite):
    def __init__(self, start, w, h) -> None:
        super().__init__()
        self.SPRITES = load_sprite_sheets(
            join(PATH, "characters", CHARACTER), w, h, True
        )
        self.float_rect = [start[0], start[1], w, h]
        self.xvel, self.yvel, self.size = 0, 0, w
        self.mask, self.direction = None, "right"
        self.fallcount, self.animcount = 0, 0
        self.hit_count = 0
        self.collide = [None] * 4
        self.update_sprite()

    def update_sprite(self) -> None:
        sprite_sheet = "idle"
        if self.hit_count:
            sprite_sheet = "hit"
        elif self.yvel < 0:
            sprite_sheet = "jump"
        elif self.yvel > GRAVITY:
            sprite_sheet = "fall"
        elif self.xvel != 0:
            sprite_sheet = "run"

        sprites = self.SPRITES[sprite_sheet + "_" + self.direction]
        self.sprite = sprites[(self.animcount // ANIM_DELAY) % len(sprites)]
        self.animcount += 1
        self.update()

    def update(self) -> None:
        self.rect = self.sprite.get_rect(
            topleft=(round(self.float_rect[0]), round(self.float_rect[1]))
        )
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self) -> None:
        wd.blit(self.sprite, [floor(self.float_rect[i] - offset[i]) for i in [0, 1]])

    def respawn(self, start) -> list[float, float]:
        self.float_rect[0], self.float_rect[1] = start
        self.xvel, self.yvel = 0, 0
        self.collide = [None] * 4
        self.fallcount = 1
        self.update()

    def loop(self, fps, objects, data) -> list[float, float]:
        self.adjust_speed()
        self.collision(objects)
        self.update_sprite()

        if self.hit_count:
            self.hit_count += 1
        if self.hit_count > fps * RESP_BUFFER + 2:
            self.hit_count = 0
            self.respawn(data[0])
        elif not (data[1][0] <= self.float_rect[1] <= data[1][1]):
            self.respawn(data[0])

    def adjust_speed(self) -> None:
        if self.xvel > FRICTION:
            self.xvel -= FRICTION / 2
        elif self.xvel < -FRICTION:
            self.xvel += FRICTION / 2
        else:
            self.xvel = 0

        if self.yvel > TERMINALVEL:
            self.yvel = TERMINALVEL
        elif self.yvel < -TERMINALVEL:
            self.yvel = -TERMINALVEL

        self.fallcount += 1
        if not ((self.collide[2] and GRAVITY < 0) or (self.collide[3] and GRAVITY > 0)):
            self.yvel += (self.fallcount / FPS) * GRAVITY  # gravity

    def collision(self, objects) -> None:
        def add_incr(x, y) -> None:
            self.float_rect[0] += x
            self.float_rect[1] += y
            self.update()

        def try_direction(direction, obj) -> Object:
            add_incr(direction[0], direction[1])
            collided = has_collided(obj)
            add_incr(-direction[0], -direction[1])
            return obj if collided else None

        def has_collided(obj) -> bool:
            return pygame.sprite.collide_mask(self, obj) and obj.name != "layer"

        def try_mask(direction) -> bool:
            orig_direction = self.direction
            self.direction = direction
            self.update_sprite()
            for obj in objects:
                if has_collided(obj):
                    self.direction = orig_direction
                    self.update_sprite()
                    return False
            return True

        def end() -> None:
            for same in range(4):
                if same_coll[same]:
                    self.collide[same] = same_coll[same]
            for i in range(4):
                self.float_rect[i] = round(self.float_rect[i])
            if self.collide[0] or self.collide[1]:
                self.xvel = 0
            if self.collide[2] or self.collide[3]:
                self.yvel = 0
            if (self.collide[2] and GRAVITY < 0) or (self.collide[3] and GRAVITY > 0):
                self.fallcount = 0
            if self.xvel < 0:
                try_mask("left")
            elif self.xvel > 0:
                try_mask("right")

        axes = [[-1, 0], [1, 0], [0, -1], [0, 1]]
        for i in range(4):
            changed_coll = False
            if not self.collide[i]:
                continue
            for obj in objects:
                if try_direction(axes[i], obj):
                    self.collide[i] = obj
                    changed_coll = True
                    break
            if not changed_coll:
                self.collide[i] = None
        fx, fy = ceil(abs(self.xvel)), ceil(abs(self.yvel))
        max_speed = fx if fx > fy else fy
        same_coll = [None] * 4
        if max_speed == 0:
            end()
            return None
        if self.xvel == 0:
            same_coll[0], same_coll[1] = self.collide[0], self.collide[1]
        if self.yvel == 0:
            same_coll[2], same_coll[3] = self.collide[2], self.collide[3]
        increment = [self.xvel / max_speed, self.yvel / max_speed]
        direction = [abs(i) / i if i else 0 for i in [self.xvel, self.yvel]]
        for _ in range(max_speed):
            add_incr(increment[0], increment[1])
            for obj in objects:
                if not has_collided(obj):
                    continue

                add_incr(-increment[0], -increment[1])
                coll = [try_direction(i, obj) for i in axes]
                self.collide = [
                    obj if (coll[i] and (direction[i // 2] in axes[i % 2])) else None
                    for i in range(4)
                ]  # left, right, top, bottom
                end()
                return None
        end()


class Object(pygame.sprite.Sprite):
    def __init__(self, space, name=None) -> None:  # space = x, y, w, h
        super().__init__()
        self.rect = pygame.Rect(space[0], space[1], space[2], space[3])
        self.image = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        self.name = name
        self.touched = False

    def draw(self) -> None:
        if not self.touched:
            wd.blit(self.image, (self.rect.x - offset[0], self.rect.y - offset[1]))

    def update_mask(self) -> None:
        self.mask = pygame.mask.from_surface(self.image)


class Layer(Object):
    def __init__(self, space, path) -> None:
        super().__init__(space, "layer")
        self.space = space
        self.path = path
        self.image.blit(pygame.image.load(path).convert_alpha(), (0, 0))

    def draw(self) -> None:
        wd.blit(self.image, (self.rect.x - offset[0], self.rect.y - offset[1]))


class Block(Object):
    def __init__(self, space) -> None:
        super().__init__(space, "block")
        block = load_block(space[2], space[3])
        self.image.blit(block, (0, 0))
        self.update_mask()


class Spike(Object):
    def __init__(self, space, angle) -> None:
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
    def __init__(self, space, angle) -> None:
        super().__init__(space, "bouncepad")
        self.sprites = rotate_image(
            load_sprite_sheets(join(PATH, "objects"), self.rect.w, self.rect.h)[
                "bouncepad"
            ],
            angle,
        )
        self.image = self.sprites[-1]
        self.animnum = 0
        self.angle = angle
        self.bounced = 0
        self.update_mask()

    def loop(self) -> None:
        self.update_mask()
        if 0 < self.bounced <= 5:
            self.bounced += 1
            self.image = self.sprites[(self.animnum // 2) % len(self.sprites)]
            if self.animnum // 2 > len(self.sprites):
                self.animnum = 0
            else:
                self.animnum += 1
        else:
            self.animnum = 0
            self.bounced = 0
            self.image = self.sprites[-1]


class Goal(Object):
    def __init__(self, space) -> None:
        super().__init__(space, "goal")
        self.image = load_sprite_sheets(
            join(PATH, "objects"), self.rect.w, self.rect.h
        )["goal"][0]
        self.update_mask()


def obj_interaction(player, level_num, data, level) -> bool:
    for obj in player.collide:
        if obj and obj != "non-bounce":
            if obj.name == "spike":
                player.hit_count += 1
            elif obj.name == "bouncepad" and not obj.bounced == -1:
                angles = [270, 90, 180, 0]
                bounce_direction = [1, -1, 1, -1]
                for i in range(len(angles)):
                    if obj.angle == angles[i]:
                        if player.collide[i] is obj:
                            obj.bounced += 1
                            bounce = BOUNCE_STRENGTH * bounce_direction[i]
                            if i // 2 == 0:
                                player.xvel = bounce
                            else:
                                player.yvel = bounce
                        else:
                            obj.bounced = -1
            elif obj.name == "goal":
                level_num += 1
                data, level = process_levels[level_num - 1]
                player.respawn(data[0])
    return level_num, data, level


def keys(player, start) -> None:
    print(
        player.collide,
        player.xvel,
        player.yvel,
        player.fallcount,
        sep=" | ",
    )

    keys = pygame.key.get_pressed()
    if keys[pygame.K_r]:
        player.respawn(start)
        return None
    if keys[pygame.K_p]:
        pygame.display.toggle_fullscreen()
        pygame.display.set_icon(pygame.image.load(join(PATH, ICON)))
        pygame.display.update()
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        if not player.collide[0]:
            if player.direction != "left":
                player.animcount = 0
            if player.xvel <= -MSPEED + AGILE:
                player.xvel = -MSPEED
            else:
                player.xvel -= AGILE
    elif keys[pygame.K_RIGHT] or keys[pygame.K_d] and (not player.collide[1]):
        if player.direction != "right":
            player.animcount = 0
        if player.xvel >= MSPEED - AGILE:
            player.xvel = MSPEED
        else:
            player.xvel += AGILE
    if (keys[pygame.K_UP] or keys[pygame.K_w]) and player.fallcount == 0:
        player.yvel = -GRAVITY * JUMP
        player.animcount = 0
        player.fallcount = 0


def draw(wd, player, tile, objects) -> None:
    tile_image = pygame.image.load(join(PATH, tile))
    _, _, tile_width, tile_height = tile_image.get_rect()
    _ = [
        [
            wd.blit(tile_image, (i * tile_width, j * tile_height))
            for j in range(HEIGHT // tile_height + 10)
        ]
        for i in range(WIDTH // tile_width + 10)
    ]
    _ = [obj.draw() for obj in objects + [player]]
    pygame.display.update()


def scroll(player, offset=[0, 0]) -> list[float, float]:
    if player.float_rect[0] + player.float_rect[2] - offset[0] >= WIDTH - SCROLL[0]:
        offset[0] = player.float_rect[0] + player.float_rect[2] - (WIDTH - SCROLL[0])
    elif player.float_rect[0] - offset[0] <= SCROLL[0]:
        offset[0] = player.float_rect[0] - SCROLL[0]
    if player.float_rect[1] + player.float_rect[3] - offset[1] >= HEIGHT - SCROLL[1]:
        offset[1] = player.float_rect[1] + player.float_rect[3] - (HEIGHT - SCROLL[1])
    elif player.float_rect[1] - offset[1] <= SCROLL[1]:
        offset[1] = player.float_rect[1] - SCROLL[1]
    return offset


def main(wd, level_num) -> None:
    data, level = process_levels(LEVELS[level_num - 1])
    clock = pygame.time.Clock()
    player = Player(data[0], 60, 60)
    global offset

    run = True
    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

        offset = scroll(player)  # offset amount up, left
        leveltile = join("background", TILES[level_num - 1])
        player.loop(FPS, level, data)
        _ = [obj.loop() for obj in level if obj.name == "bouncepad"]
        level_num, data, level = obj_interaction(player, level_num, data, level)
        keys(player, data[0])
        draw(wd, player, leveltile, level)

    pygame.quit()


if __name__ == "__main__":
    main(wd, level_num)
