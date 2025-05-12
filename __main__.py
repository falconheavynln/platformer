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
FRICTION = 0.5
STOP = 1
TVEL = 60  # max falling speed
SCROLL = [250, 175]  # distance from side of screen to scroll x, y
RESP_BUFFER = 0.15  # secs before player goes back to start after dying
BOUNCE_STRENGTH = 30  # amount bouncepads bounce
# coral = (255, 96, 96)
# lime = (196, 255, 14)
BGCOLOR = "random"

# reload(ticks), recoil(fraction of bullet_speed), bullet_speed, bullet_mass, perception, damage
STATS = [10, 0.3, 20, 0.3, 0.7, 1]
GUN = "goon"
AMMO = "sus"

level_num = 2

# x_vel is velocity to the right
# y_vel is velocity down

# pygame.Surface needs SRCALPHA as 2nd param

PATH = "assets"
TILES = [
    f"bg_tile_lvl{i + 1}.png" for i in range(len(listdir(join(PATH, "background"))))
]

ICON = join("objects", ICON + ".png")

wd = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(CAPTION)
pygame.display.set_icon(pygame.image.load(join(PATH, ICON)))


def random_color():
    return tuple([randint(0, 255) for _ in range(3)])


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


def process_levels(level, color):
    wd.fill([randint(0, 255) for _ in range(3)])
    wd.blit(
        load_sprite_sheets(join(PATH, "load"), 256, 64)["load"][0],
        (WIDTH // 2 - 128, HEIGHT // 2 - 32),
    )
    pygame.display.update()
    all_objects = []
    for obj in level[1:]:
        args = len(obj)
        if obj[1] == "bouncepad":
            if args == 2:
                all_objects.append(Bouncepad(obj[0]))
            elif args == 3:
                all_objects.append(Bouncepad(obj[0], obj[2]))
            elif args == 4:
                all_objects.append(Bouncepad(obj[0], obj[2], obj[3]))
        elif obj[1] == "target":
            if args == 2:
                all_objects.append(Target(obj[0]))
            elif args == 3:
                all_objects.append(Target(obj[0], obj[2]))
            elif args == 4:
                all_objects.append(Target(obj[0], obj[2], obj[3]))
        elif obj[1] == "spike":
            if args == 2:
                all_objects.append(Object(obj[0], obj[1]))
            elif args == 3:
                all_objects.append(Object(obj[0], obj[1], None, obj[2]))
            elif args == 4:
                all_objects.append(Object(obj[0], obj[1], obj[2], obj[3]))
        else:
            if args == 2:
                all_objects.append(Object(obj[0], obj[1]))
            elif args == 3:
                all_objects.append(Object(obj[0], obj[1], obj[2]))
            elif args == 4:
                all_objects.append(Object(obj[0], obj[1], obj[2], obj[3]))
    return (
        level[0],
        all_objects,
        random_color() if color == "random" else color,
    )


class Player(pygame.sprite.Sprite):
    def __init__(self, start, stats, gun, bullet, w, h) -> None:
        super().__init__()
        self.SPRITES = load_sprite_sheets(
            join(PATH, "characters", CHARACTER), w, h, True
        )
        self.float_rect = [start[0], start[1], w, h]
        self.xvel, self.yvel = 0, 0
        self.mask, self.direction, self.walking = None, "right", False
        self.fallcount, self.animcount = 0, 0
        self.hit_count, self.loaded = 0, 0
        self.stats, self.bullets = stats, []
        self.gun, self.bullet = gun, bullet
        self.collide = [None] * 4
        self.update_sprite()
        self.respawn(start)

    def update_sprite(self) -> None:
        sprite_sheet = "idle"
        if self.hit_count:
            sprite_sheet = "hit"
        elif self.yvel < 0:
            sprite_sheet = "jump"
        elif self.yvel > gravity:
            sprite_sheet = "fall"
        elif self.xvel != 0:
            sprite_sheet = "run"

        sprites = self.SPRITES[sprite_sheet + "_" + self.direction]
        self.image = sprites[(self.animcount // ANIM_DELAY) % len(sprites)]
        self.animcount += 1
        self.update()

    def update(self) -> None:
        self.rect = self.image.get_rect(
            topleft=tuple([round(self.float_rect[i]) for i in [0, 1]])
        )
        self.mask = pygame.mask.from_surface(self.image)

    def draw(self) -> None:
        image_pos = [self.float_rect[i] - t_offset[i] for i in [0, 1]]
        wd.blit(self.image, [floor(image_pos[i]) for i in [0, 1]])
        wd.blit(
            self.gun_image, [floor(image_pos[i] - self.rotation_offset) for i in [0, 1]]
        )

    def respawn(self, start) -> list[float, float]:
        self.float_rect[0], self.float_rect[1] = start
        global offset, look_offset, t_offset
        offset = [
            self.float_rect[i] + (self.float_rect[i + 2] - DIMS[i]) // 2 for i in [0, 1]
        ]
        look_offset = [WIDTH / 2, HEIGHT / 2]
        t_offset = [offset[i] + look_offset[i] for i in [0, 1]]
        self.collide, self.fallcount = [None] * 4, 1
        self.xvel, self.yvel = 0, 0
        self.bullets = []
        self.update()

    def loop(self, fps, objects, data) -> list[float, float]:
        self.adjust_speed()
        self.collision(objects)
        self.update_sprite()
        self.shoot(objects)

        if self.hit_count:
            self.hit_count += 1
        if self.hit_count > fps * RESP_BUFFER:
            self.hit_count = 0
            self.respawn(data[0])
        elif not (data[1][0] <= self.float_rect[1] <= data[1][1]):
            self.respawn(data[0])

    def adjust_speed(self) -> None:
        if not self.walking:
            if self.xvel != 0:
                self.xvel *= FRICTION
            if -STOP <= self.xvel <= STOP:
                self.xvel = 0
        self.walking = False

        self.yvel = (
            TVEL if self.yvel > TVEL else -TVEL if self.yvel < -TVEL else self.yvel
        )

        self.fallcount += 1
        if not ((self.collide[2] and gravity < 0) or (self.collide[3] and gravity > 0)):
            self.yvel += (self.fallcount / FPS) * gravity  # gravity

    def shoot(self, objs):
        bullet_rect = pygame.rect.Rect(
            self.rect.centerx - 32, self.rect.centery - 32, 64, 64
        )
        if pygame.mouse.get_pressed(num_buttons=3)[0] and self.loaded >= 0:
            bullet = Bullet(self, objs, bullet_rect, self.bullet)
            self.bullets.append(bullet)
            push = self.stats[1] * self.stats[3]
            self.xvel -= bullet.xvel * push
            self.yvel -= bullet.yvel * push
            self.loaded = -self.stats[0]
        elif self.loaded < 0:
            self.loaded += 1

        for bullet in self.bullets:
            if bullet.dead:
                self.bullets.remove(bullet)
            else:
                bullet.loop(self, objs)

        center = [self.rect.centerx, self.rect.centery]
        vector = [mouse[i] - center[i] + t_offset[i] for i in [0, 1]]
        self.polar = pygame.Vector2(vector[0], vector[1]).as_polar()
        self.angle = (-self.polar[1] + 360) % 360
        self.rads = (self.angle / 360 * 2 * pi) % (pi / 2)
        self.rotation_offset = self.rect.w / 2 * (cos(self.rads) + sin(self.rads) - 1)
        load = pygame.image.load(join(PATH, "guns", self.gun + ".png")).convert_alpha()
        self.gun_image = pygame.transform.rotate(load, self.angle)

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
            orig_direction, self.direction = self.direction, direction
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
            if (self.collide[2] and gravity < 0) or (self.collide[3] and gravity > 0):
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
        max_speed, same_coll = fx if fx > fy else fy, [None] * 4
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
    def __init__(self, player, objects, rect, path) -> None:
        super().__init__()
        self.angle, self.name = 0, "bullet"
        self.speed, self.mass = player.stats[2], player.stats[3]
        self.rotation_speed = randint(int(0.4 * self.speed), int(2 * self.speed))
        self.path, self.rect = path, rect
        self.fallcount, self.dead = 0, False
        center = [player.float_rect[i] + player.float_rect[i + 2] / 2 for i in [0, 1]]
        x_dist, y_dist = ((mouse[i] - center[i] + t_offset[i]) for i in [0, 1])
        total_dist = sqrt(abs(x_dist * x_dist) + abs(y_dist * y_dist))
        if total_dist == 0:
            self.dead = True
            return None
        self.xvel, self.yvel = (self.speed * i / total_dist for i in [x_dist, y_dist])
        self.loop(player, objects)

    def update_mask(self):
        self.mask = pygame.mask.from_surface(self.image)

    def draw(self):
        pos = [self.rect.x, self.rect.y]
        screen_pos = [pos[i] - t_offset[i] - self.rotation_offset for i in [0, 1]]
        wd.blit(self.image, tuple(screen_pos))

    def loop(self, player, objects) -> None:
        self.fallcount += 1
        self.yvel += (self.fallcount / FPS) * gravity * self.mass
        self.rect.x += self.xvel
        self.rect.y += self.yvel

        perception_corr = [i * 3 / 2 * player.stats[4] for i in DIMS]
        pos_diffs = [self.rect.x - player.rect.x, self.rect.y - player.rect.y]
        if pos_diffs[0] > perception_corr[0] or pos_diffs[1] > perception_corr[1]:
            self.dead = True

        self.angle = (self.angle + self.rotation_speed) % 360
        self.rads = (self.angle / 360 * 2 * pi) % (pi / 2)
        image_unrotated = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        load = pygame.image.load(join(PATH, "bullets", self.path + ".png"))
        image_unrotated.blit(load.convert_alpha(), (0, 0))
        self.image = pygame.transform.rotate(image_unrotated, self.angle)
        self.rotation_offset = self.rect.w / 2 * (cos(self.rads) + sin(self.rads) - 1)

        # bad performance, especially with many objs & bullets
        self.update_mask()
        for obj in objects:
            if pygame.sprite.collide_mask(self, obj) and obj.name != "layer":
                self.dead = True
                if obj.name == "target":
                    obj.hit(player)


class Object(pygame.sprite.Sprite):
    def __init__(self, space, name, path=None, angle=0) -> None:  # space = x, y, w, h
        super().__init__()
        if name == "block" and path is None:
            path = f"block{space[2]//64}x{space[3]//64}"
        path = name if path is None else path
        if type(path) is int:
            angle, path = path, name

        self.rect = pygame.Rect(space[0], space[1], space[2], space[3])
        self.image = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        self.image = load_sprite_sheets(join(PATH, "objects"), space[2], space[3])[path]
        self.image, self.name = rotate_image(self.image, angle)[0], name
        self.update_mask()

    def draw(self) -> None:
        pos = [self.rect.x, self.rect.y]
        wd.blit(self.image, tuple(pos[i] - t_offset[i] for i in [0, 1]))

    def update_mask(self) -> None:
        self.mask = pygame.mask.from_surface(self.image)


class Target(Object):
    def __init__(self, space, hp=100, paths=["target", "target_shot"]) -> None:
        super().__init__(space, paths[0])
        self.hp, self.paths = hp, paths

    def hit(self, player):
        self.hp -= player.stats[5]
        if self.hp <= 0:
            self.image = load_sprite_sheets(
                join(PATH, "objects"), self.rect.w, self.rect.h
            )[self.paths[1]][0]
            self.update_mask()


class Bouncepad(Object):
    def __init__(self, space, angle=0, path="bouncepad") -> None:
        super().__init__(space, "bouncepad")
        sprite_sheet = load_sprite_sheets(join(PATH, "objects"), space[2], space[3])
        self.sprites = rotate_image(sprite_sheet[path], angle)
        self.anim, self.bounced, self.angle = 0, 0, angle

    def loop(self) -> None:
        self.update_mask()
        if 0 < self.bounced <= 2 * len(self.sprites):
            self.bounced += 1
            self.image = self.sprites[(self.anim // 2) % len(self.sprites)]
            self.anim = 0 if self.anim // 2 > len(self.sprites) else self.anim + 1
        else:
            self.anim, self.bounced = 0, 0
            self.image = self.sprites[-1]


def obj_interaction(player, level_num, data, level, color) -> bool:
    for obj in player.collide:
        if not obj:
            continue
        if obj.name == "spike":
            player.hit_count += 1
        elif obj.name == "bouncepad":
            angles, bounce = [3, 1, 2, 0], [BOUNCE_STRENGTH, -BOUNCE_STRENGTH] * 2
            for i in range(4):
                if obj.angle == angles[i] * 90 and player.collide[i] == obj:
                    obj.bounced = 1
                    if i // 2 == 0:
                        player.xvel = bounce[i]
                    else:
                        player.yvel = bounce[i]
        elif obj.name == "goal":
            level_num += 1
            data, level, color = process_levels(LEVELS[level_num - 1], BGCOLOR)
            global gravity
            gravity = data[-1]
            player.respawn(data[0])
            break
    return level_num, data, level, color


def keys(player, start) -> None:
    keys = pygame.key.get_pressed()
    if keys[pygame.K_r]:
        player.respawn(start)
        scroll(player, look_offset)
        return None
    if keys[pygame.K_p]:
        pygame.display.toggle_fullscreen()
        pygame.display.set_icon(pygame.image.load(join(PATH, ICON)))
        pygame.display.update()
    if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and (not player.collide[0]):
        player.walking = True
        if player.direction != "left":
            player.animcount = 0
        player.xvel = -MSPEED if player.xvel <= AGILE - MSPEED else player.xvel - AGILE
    elif (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and (not player.collide[1]):
        player.walking = True
        if player.direction != "right":
            player.animcount = 0
        player.xvel = MSPEED if player.xvel >= MSPEED - AGILE else player.xvel + AGILE
    if (
        keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_SPACE]
    ) and player.fallcount == 0:
        player.yvel = -JUMP * (gravity // abs(gravity))
        player.animcount, player.fallcount = 0, 0


def draw(wd, player, objects, color) -> None:
    tile_image = pygame.image.load(join(PATH, "background", TILES[level_num - 1]))
    tile_dims = tile_image.get_rect()[2:]
    ranges = [range(DIMS[i] // tile_dims[i] + 10) for i in [0, 1]]
    [
        [wd.blit(tile_image, (i * tile_dims[0], j * tile_dims[1])) for j in ranges[1]]
        for i in ranges[0]
    ]
    wd.fill(color)
    for obj in objects:
        offscreen = False
        for i in [0, 1]:
            screen_pos = obj.rect[i] - t_offset[i]
            if not (0 < screen_pos + obj.rect[i + 2] and screen_pos < DIMS[i]):
                offscreen = True
        if (not offscreen) or obj.name == "bullet":
            obj.draw()
    player.draw()
    pygame.display.update()


def scroll(player, look_offset) -> list[float, float]:  # offset amount up, left
    if 0 <= mouse[0] <= WIDTH and 0 <= mouse[1] <= HEIGHT:
        look_offset = [
            floor((mouse[i] - DIMS[i] // 2) * player.stats[4]) for i in [0, 1]
        ]
    for i in [0, 1]:
        border = [
            player.float_rect[i] + 128 - DIMS[i] + SCROLL[i],
            player.float_rect[i] - SCROLL[i],
        ]
        offset[i] = border[0] if offset[i] <= border[0] else offset[i]
        offset[i] = border[1] if offset[i] >= border[1] else offset[i]
    return offset, look_offset


def main(wd, level_num) -> None:
    print("\n --- RUNNING --- \n")
    data, level, color = process_levels(LEVELS[level_num - 1], BGCOLOR)
    clock = pygame.time.Clock()
    global offset, look_offset, t_offset, mouse, gravity
    gravity = data[2]
    offset, look_offset = [0, 0], [0, 0]
    player = Player(data[0], STATS, GUN, AMMO, 128, 128)

    run = True
    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

        mouse = pygame.mouse.get_pos()
        offset, look_offset = scroll(player, look_offset)
        t_offset = [offset[i] + look_offset[i] for i in [0, 1]]
        player.loop(FPS, level, data)
        [obj.loop() for obj in level if obj.name == "bouncepad"]
        level_num, data, level, color = obj_interaction(
            player, level_num, data, level, color
        )
        draw(wd, player, level + player.bullets, color)
        keys(player, data[0])

    print("\n --- QUITTING --- \n")
    pygame.quit()


if __name__ == "__main__":
    main(wd, level_num)
