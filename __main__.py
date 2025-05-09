import pygame
from level import LEVELS
from os import listdir
from os.path import isfile, join
from random import randint
from math import floor, ceil, cos, sin, sqrt, pi

pygame.init()

CAPTION = "monochrome"
CHARACTER = "plus"
ICON = "goal"

ANIM_DELAY = 7
WIDTH = 1000
HEIGHT = 800
DIMS = [WIDTH, HEIGHT]
FPS = 60

MSPEED = 15  # max ground speed
AGILE = 4  # ability to change direction
JUMP = 20
FRICTION = 3
GRAVITY = 20
TERMINALVEL = 60  # max moving speed
SCROLL = [250, 175]  # distance from side of screen to scroll x, y
RESP_BUFFER = 0.15  # secs before player goes back to start after dying
BOUNCE_STRENGTH = 60  # amount bouncepads bounce

# reload(ticks), recoil(fraction of bullet_speed), bullet_speed, bullet_mass, perception, damage
STATS = [10, 0.3, 20, 0.3, 0.7, 1]
GUN = "goon"
AMMO = "sus"

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
    path = join(PATH, "terrain", f"block{w//64}x{h//64}.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((w, h), pygame.SRCALPHA, 32)
    rect = pygame.Rect(0, 0, w, h)  # w, h is dimensions
    surface.blit(image, (0, 0), rect)
    return surface


def process_levels(level):
    data = []
    objects = [Layer, Spike, Saw, Block, Target, Bouncepad, Goal]
    obj_names = ["layer", "spike", "saw", "block", "target", "bouncepad", "goal"]
    load_text = load_sprite_sheets(join(PATH, "load"), 256, 64)["load"][0]

    wd.fill([randint(0, 255) for _ in range(3)])
    wd.blit(load_text, (WIDTH // 2 - 128, HEIGHT // 2 - 32))
    pygame.display.update()

    for obj_index in range(len(level)):
        if obj_index == 0:
            data = [i for i in level[0]]
            continue
        obj_info = level[obj_index]
        obj_rect = [obj_info[i] * 64 for i in range(4)]
        for obj_name_index in range(len(obj_names)):
            if obj_info[4][0] == obj_names[obj_name_index]:
                obj = obj_name_index
        if obj in [3, 4, 6]:
            final_obj = objects[obj](obj_rect)
        elif obj == 0:
            final_obj = objects[obj](
                obj_rect,
                join(PATH, "layers", obj_info[-1][1] + ".png"),
            )
        elif obj in [1, 2, 5]:
            final_obj = objects[obj](obj_rect, obj_info[4][1])
        level[obj_index] = final_obj
    level = level[1:]
    return data, level


class Player(pygame.sprite.Sprite):
    def __init__(self, start, stats, gun, bullet, w, h) -> None:
        super().__init__()
        self.SPRITES = load_sprite_sheets(
            join(PATH, "characters", CHARACTER), w, h, True
        )
        self.float_rect = [start[0], start[1], w, h]
        self.xvel, self.yvel = 0, 0
        self.mask, self.direction = None, "right"
        self.fallcount, self.animcount = 0, 0
        self.hit_count = 0
        self.loaded = 0
        self.stats = stats
        self.bullets = []
        self.gun = gun
        self.bullet = bullet
        self.collide = [None] * 4
        self.update_sprite()
        self.respawn(start)

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
        self.image = sprites[(self.animcount // ANIM_DELAY) % len(sprites)]
        self.animcount += 1
        self.update()

    def update(self) -> None:
        self.rect = self.image.get_rect(
            topleft=(round(self.float_rect[0]), round(self.float_rect[1]))
        )
        self.mask = pygame.mask.from_surface(self.image)

    def draw(self) -> None:
        image_pos = [self.float_rect[i] - offset[i] - look_offset[i] for i in [0, 1]]
        wd.blit(self.image, [floor(image_pos[i]) for i in [0, 1]])
        wd.blit(
            self.gun_image, [floor(image_pos[i] - self.rotation_offset) for i in [0, 1]]
        )

    def respawn(self, start) -> list[float, float]:
        self.float_rect[0], self.float_rect[1] = start
        global offset, look_offset
        offset = [
            self.float_rect[i] + (self.float_rect[i + 2] - DIMS[i]) // 2 for i in [0, 1]
        ]
        look_offset = [WIDTH / 2, HEIGHT / 2]
        self.xvel, self.yvel = 0, 0
        self.collide = [None] * 4
        self.fallcount = 1
        self.update()

    def loop(self, fps, objects, data) -> list[float, float]:
        self.adjust_speed()
        self.collision(objects)
        self.update_sprite()
        self.shoot(objects)

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

    def shoot(self, objects):
        bullet_rect = pygame.rect.Rect(
            self.rect.centerx - 32, self.rect.centery - 32, 64, 64
        )
        if pygame.mouse.get_pressed(num_buttons=3)[0] and self.loaded >= 0:
            bullet = Bullet(
                self,
                objects,
                offset,
                look_offset,
                bullet_rect,
                self.bullet,
            )
            self.bullets.append(bullet)
            self.xvel -= bullet.xvel * self.stats[1] * self.stats[3]
            self.yvel -= bullet.yvel * self.stats[1] * self.stats[3]
            self.loaded = -self.stats[0]
        elif self.loaded < 0:
            self.loaded += 1

        for bullet in self.bullets:
            if bullet.dead:
                self.bullets.remove(bullet)
            else:
                bullet.loop(self, objects)

        mouse_pos = pygame.mouse.get_pos()
        self.vector = pygame.Vector2(
            mouse_pos[0] - (self.rect.centerx - offset[0] - look_offset[0]),
            mouse_pos[1] - (self.rect.centery - offset[1] - look_offset[1]),
        )
        self.polar = self.vector.as_polar()
        self.angle = (-self.polar[1] + 360) % 360
        self.rads = (self.angle / 360 * 2 * pi) % (pi / 2)
        # self.rotation_offset = self.rect.w * abs(sin(2 * self.rads)) * sqrt(2) / 7.5
        self.rotation_offset = self.rect.w / 2 * (cos(self.rads) + sin(self.rads) - 1)
        self.gun_image = pygame.transform.rotate(
            pygame.image.load(join(PATH, "guns", self.gun + ".png")).convert_alpha(),
            self.angle,
        )

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
            same_coll[:1] = self.collide[:1]
        if self.yvel == 0:
            same_coll[1:] = self.collide[1:]
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


class Bullet(pygame.sprite.Sprite):
    def __init__(self, player, objects, offset, look_offset, rect, path) -> None:
        super().__init__()
        self.angle = 0
        self.name = "bullet"
        self.speed, self.mass = player.stats[2], player.stats[3]
        self.rotation_speed = randint(int(0.4 * self.speed), int(2 * self.speed))
        self.path, self.rect = path, rect
        self.fallcount, self.dead = 0, False
        x_dist, y_dist = (
            (
                pygame.mouse.get_pos()[i]
                - (player.float_rect[i] + player.float_rect[i + 2] / 2)
                + offset[i]
                + look_offset[i]
            )
            for i in range(2)
        )
        total_dist = sqrt(abs(x_dist * x_dist) + abs(y_dist * y_dist))
        if total_dist == 0:
            self.dead = True
            return None
        else:
            self.xvel, self.yvel = (
                self.speed * i / total_dist for i in [x_dist, y_dist]
            )

        self.loop(player, objects)
        # self.rect.x -= self.xvel
        # self.rect.y -= self.yvel

    def update_mask(self):
        self.mask = pygame.mask.from_surface(self.rotated_image)

    def draw(self):
        pos = [self.rect.x, self.rect.y]
        wd.blit(
            self.rotated_image,
            tuple(
                pos[i] - offset[i] - look_offset[i] - self.rotation_offset
                for i in range(2)
            ),
        )

    def loop(self, player, objects) -> None:
        self.fallcount += 1
        self.yvel += (self.fallcount / FPS) * GRAVITY * self.mass
        self.rect.x += self.xvel
        self.rect.y += self.yvel

        perception_corr = (3 / 2 * WIDTH * player.stats[4]), (
            3 / 2 * HEIGHT * player.stats[4]
        )
        pos_diffs = [self.rect.x - player.rect.x, self.rect.y - player.rect.y]
        if pos_diffs[0] > perception_corr[0] or pos_diffs[1] > perception_corr[1]:
            self.dead = True

        self.angle += self.rotation_speed
        self.angle %= 360
        self.image = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        self.bullet_image = pygame.image.load(
            join(PATH, "bullets", self.path + ".png")
        ).convert_alpha()
        self.image.blit(self.bullet_image, (0, 0))
        self.rotated_image = pygame.transform.rotate(self.image, self.angle)
        self.rotation_offset = (
            self.rect.w * abs(sin(2 * self.angle / 180 * pi)) * sqrt(2) / 7.5
        )

        for obj in objects:
            if not obj:
                continue
            if pygame.sprite.collide_mask(self, obj):
                self.dead = True
                if obj.name == "target":
                    obj.hp -= player.stats[5]
                    if obj.hp <= 0:
                        obj.image = load_sprite_sheets(
                            join(PATH, "objects"),
                            obj.rect.w,
                            obj.rect.h,
                        )["target_shot"][0]
                        obj.update_mask()

        # bad performance, especially with many objs & bullets
        self.update_mask()
        orig_rect = self.rect
        fx, fy = ceil(abs(self.xvel)), ceil(abs(self.yvel))
        max_speed = fx if fx > fy else fy
        increment = [self.xvel / max_speed, self.yvel / max_speed]
        for _ in range(max_speed):
            self.rect.x += increment[0]
            self.rect.y += increment[1]
            for obj in objects:
                if pygame.sprite.collide_mask(self, obj) and obj.name != "layer":
                    self.dead = True
                    return None
        self.rect = orig_rect


class Object(pygame.sprite.Sprite):
    def __init__(self, space, name=None) -> None:  # space = x, y, w, h
        super().__init__()
        self.rect = pygame.Rect(space[0], space[1], space[2], space[3])
        self.image = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        self.name = name
        self.touched = False

    def draw(self) -> None:
        if not self.touched:
            pos = [self.rect.x, self.rect.y]
            wd.blit(
                self.image,
                tuple(pos[i] - offset[i] - look_offset[i] for i in range(2)),
            )

    def update_mask(self) -> None:
        self.mask = pygame.mask.from_surface(self.image)


class Layer(Object):
    def __init__(self, space, path) -> None:
        super().__init__(space, "layer")
        self.space = space
        self.path = path
        self.image.blit(pygame.image.load(path).convert_alpha(), (0, 0))

    def draw(self) -> None:
        pos = [self.rect.x, self.rect.y]
        wd.blit(
            self.image, tuple(pos[i] - offset[i] - look_offset[i] for i in range(2))
        )


class Block(Object):
    def __init__(self, space) -> None:
        super().__init__(space, "block")
        self.pos = space
        self.image.blit(load_block(space[2], space[3]), (0, 0))
        self.update_mask()


class Target(Object):
    def __init__(self, space) -> None:
        super().__init__(space, "target")
        self.hp = 100
        self.image = load_sprite_sheets(
            join(PATH, "objects"),
            self.rect.w,
            self.rect.h,
        )["target"][0]
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


class Saw(Object):
    def __init__(self, space, angle) -> None:
        super().__init__(space, "saw")
        self.angle = angle
        self.image = rotate_image(
            load_sprite_sheets(
                join(PATH, "objects"),
                self.rect.w,
                self.rect.h,
            )["saw"],
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


def obj_interaction(player, level_num, data, level, offset) -> bool:
    for obj in player.collide:
        if not obj:
            continue
        if obj.name in ["spike", "saw"]:
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
                        obj.bounced = 0
        elif obj.name == "goal":
            level_num += 1
            data, level = process_levels(LEVELS[level_num - 1])
            player.respawn(data[0])
            offset = []
            break
    return level_num, data, level, offset


def keys(player, start) -> None:
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
        player.yvel = -GRAVITY * JUMP * (GRAVITY // abs(GRAVITY))
        player.animcount = 0
        player.fallcount = 0


def draw(wd, player, objects) -> None:
    tile_image = pygame.image.load(join(PATH, "background", TILES[level_num - 1]))
    _, _, tile_width, tile_height = tile_image.get_rect()
    _ = [
        [
            wd.blit(tile_image, (i * tile_width, j * tile_height))
            for j in range(HEIGHT // tile_height + 10)
        ]
        for i in range(WIDTH // tile_width + 10)
    ]
    coral = (255, 96, 96)
    # lime = (196, 255, 14)
    wd.fill(coral)
    # pygame.draw.rect(
    #     wd,
    #     "black",
    #     (SCROLL[0], SCROLL[1], WIDTH - 2 * SCROLL[0], HEIGHT - 2 * SCROLL[1]),
    # )
    # [
    for obj in objects:
        offscreen = False
        for i in [0, 1]:
            screen_pos = obj.rect[i] - offset[i] - look_offset[i]
            if not (0 < screen_pos + obj.rect[i + 2] and screen_pos < DIMS[i]):
                offscreen = True
        if (not offscreen) or obj.name == "bullet":
            obj.draw()
    player.draw()
    pygame.display.update()


def scroll(player) -> list[float, float]:
    mouse_pos = pygame.mouse.get_pos()  # offset amount up, left
    if 0 <= mouse_pos[0] <= WIDTH and 0 <= mouse_pos[1] <= HEIGHT:
        look_offset = [
            floor((mouse_pos[i] - DIMS[i] // 2) * player.stats[4]) for i in [0, 1]
        ]
    for i in [0, 1]:
        border = [
            player.float_rect[i] + player.float_rect[i + 2] - DIMS[i] + SCROLL[i],
            player.float_rect[i] - SCROLL[i],
        ]
        offset[i] = border[0] if offset[i] <= border[0] else offset[i]
        offset[i] = border[1] if offset[i] >= border[1] else offset[i]
    return offset, look_offset


def main(wd, level_num) -> None:
    print("\n --- RUNNING --- \n")
    data, level = process_levels(LEVELS[level_num - 1])
    clock = pygame.time.Clock()
    global offset, look_offset
    offset, look_offset = [0, 0], [0, 0]
    player = Player(data[0], STATS, GUN, AMMO, 128, 128)

    run = True
    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

        offset, look_offset = scroll(player)
        player.loop(FPS, level, data)
        [obj.loop() for obj in level if obj.name == "bouncepad"]
        level_num, data, level, offset = obj_interaction(
            player, level_num, data, level, offset
        )
        keys(player, data[0])
        draw(wd, player, level + player.bullets)

    print("\n --- QUITTING --- \n")
    pygame.quit()


if __name__ == "__main__":
    main(wd, level_num)
