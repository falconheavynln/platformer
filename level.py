# space, name, path=None, angle=0

from copy import deepcopy
from random import randint

level_1 = [
    [[600, 480], [-2000, 2000], 20],
    [[640, 576, 64, 128], "block"],
    [[704, 640, 64, 64], "block", "mini_block"],
    [[940.8, 640, 192, 256], "block"],
    [[1088, 620.8, 192, 128], "block"],
    [[1088, 736.0, 128, 128], "block"],
    [[576, 192, 192, 192], "block"],
    [[576, 256, 192, 192], "block"],
    [[640, 256, 192, 128], "block"],
    [[1216, 704, 128, 64], "block"],
    [[1088, 160.0, 128, 192], "block"],
    [[1056.0, 352.0, 128, 64], "block"],
    [[1056.0, 256, 64, 64], "block"],
    [[1536, 640, 64, 64], "block", "mini_block"],
    [[1536, 704, 64, 64], "layer", "mini_block"],
    [[1536, 768, 64, 64], "block", "mini_block"],
    [[1536, 832, 64, 64], "block", "mini_block"],
    [[1536, 896, 64, 64], "block", "mini_block"],
    [[1664, 512, 64, 64], "block", "mini_block"],
    [[1792, 320, 64, 64], "block", "mini_block"],
    [[1728, 864.0, 64, 64], "block", "mini_block"],
    [[1664, 256, 64, 64], "block"],
    [[1728, 384, 128, 64], "block"],
    [[1664, 128, 128, 64], "block"],
    [[1600, 192, 64, 128], "block"],
    [[1792, 192, 64, 128], "block"],
    [[1920, 704, 128, 128], "block"],
    [[2304, 704, 128, 128], "block"],
    [[1984, 576, 128, 128], "block"],
    [[2240, 608.0, 128, 128], "block"],
    [[2560, 704, 64, 64], "block", "mini_block"],
    [[2752, 704, 64, 64], "block", "mini_block"],
    [[2816, 576, 64, 64], "block", "mini_block"],
    [[2752, 448, 64, 64], "block", "mini_block"],
    [[2368, 320, 256, 128], "block"],
    [[2432, 448, 128, 64], "block"],
    [[2368, 480.0, 64, 64], "block", "mini_block"],
    [[2048, 256, 128, 64], "block"],
    [[2048, 192, 64, 64], "block", "mini_block"],
    [[2112, 320, 64, 64], "block"],
    [[1408, 128, 64, 128], "block"],
    [[1344, 224.0, 64, 64], "block", "mini_block"],
    [[1408, 288.0, 64, 64], "block"],
    [[576, 128, 64, 64], "goal"],
]

level_2 = deepcopy(level_1)
level_2[-1] = [[640, 704, 64, 64], "goal"]
level_2[0][-1] *= -1

# level_2[0][0] = [600, -600]
# for i in range(len(level_2) - 1):
#     level_2[i + 1][1] = level_2[i + 1][1] * -1 - level_2[i + 1][3]


LEVELS = [
    level_1,
    level_2,
    [
        [(0, 0), [-2000, 2000], 20],
        [(0, 0, 640, 640), "block"],
        [(102.4, 224.0, 64, 64), "spike", 270],
        [(38.4, 224.0, 64, 64), "spike", 90],
        [(48.0, 518.4, 64, 64), "spike", 270],
        [(48.0, 576, 64, 64), "spike", 270],
        [(108.8, 403.2, 64, 64), "spike", 0],
        [(224.0, 480.0, 64, 64), "spike", 0],
        [(396.8, 480.0, 64, 64), "spike", 0],
        [(524.8, 480.0, 64, 64), "spike", 0],
        [(153.6, 505.6, 64, 64), "goal"],
    ],
    [
        [[930, 830], [-2000, 2000], 20],
        [(128, 512, 64, 64), "block"],
        [(256, 364.8, 64, 64), "block"],
        [(256, 640, 192, 256), "block"],
        [(448, 640, 64, 64), "block"],
        [(512, 640, 64, 64), "bouncepad", 0],
        [(512, 512, 64, 64), "bouncepad", 180],
        [(640, 576, 64, 64), "block"],
        [(256, 320, 64, 64), "goal"],
        [(768, 960, 64, 64), "block"],
        [(832, 960, 64, 64), "block"],
        [(896, 960, 64, 64), "block"],
        [(704, 960, 64, 64), "block"],
        [(640, 960, 64, 64), "block"],
        [(576, 960, 64, 64), "block"],
        [(512, 896, 64, 64), "block"],
        [(896, 896, 64, 64), "bouncepad", 270],
        [(1088, 896, 64, 64), "bouncepad", 90],
        [(896, 832, 64, 64), "bouncepad", 270],
        [(1088, 832, 64, 64), "bouncepad", 90],
        [(1024, 768, 64, 64), "bouncepad", 180],
        [(960, 768, 64, 64), "bouncepad", 180],
        [(960, 960, 64, 64), "bouncepad", 0],
        [(1024, 960, 64, 64), "bouncepad", 0],
        [(896, 768, 64, 64), "block"],
        [(1088, 768, 64, 64), "block"],
        [(576, 960, 64, 64), "block"],
        [(512, 896, 64, 64), "block"],
        [(576, 832, 64, 64), "block"],
        [(640, 512, 64, 64), "spike", 0],
    ],
    [
        [[420, 360], [-2000, 2000], 20],
        [(128, 512, 64, 64), "block"],
        [(256, 384, 64, 64), "block"],
        [(256, 640, 64, 64), "block"],
        [(448, 640, 64, 64), "block"],
        [(640, 576, 64, 64), "block"],
        [(640, 704, 64, 64), "block"],
        [(384, 640, 64, 64), "spike", 90],
        [(640, 512, 64, 64), "spike", 0],
    ],
    [
        [[60, 240], [-2000, 2000], 20],
        [(384, 736.0, 64, 64), "spike", 0],
        [(-192, 672.0, 64, 64), "bouncepad", 0],
        # [(64, 672.0, 64, 64), "layer", "vines"],
        [(512, 256, 64, 64), "layer", "suspicious"],
        [(512, 192, 64, 64), "target"],
        [(64, 608.0, 128, 64), "block"],
        [(-64, 608.0, 128, 64), "block"],
        [(-192, 723.2, 128, 64), "block"],
        [(-64, 800.0, 128, 64), "block"],
        [(64, 800.0, 128, 64), "block"],
        [(192, 800.0, 128, 64), "block"],
        [(320, 800.0, 128, 64), "block"],
        [(448, 800.0, 128, 64), "block"],
        [(576, 800.0, 128, 64), "block"],
        [(704, 800.0, 128, 64), "block"],
        [(704, 640, 128, 64), "block"],
        [(704, 512, 128, 64), "block"],
        [(704, 384, 128, 64), "block"],
        [(704, 256, 128, 64), "block"],
        [(704, 128, 128, 64), "block"],
        [(704, 0, 128, 64), "block"],
        [(192, 640, 128, 64), "block"],
        [(320, 320, 128, 64), "block"],
        [(448, 320, 128, 64), "block"],
        [(448, 384, 192, 256), "block"],
    ],
    [[[60, 600], [-2000, 2000]], 20]
    + [[(128 * i + 64, 768, 128, 64), "block"] for i in range(100)],
    [[[60, -660], [-2000, 4000], 20], [(0, 0, 3200, 3200), "block"]]
    + [[(512 + i, 512, 64, 64), "target"] for i in range(20)],
    [[[60, 600], [-2000, 2000]], 20]
    + [[(128 * i + 64, 768, 128, 64), "bouncepad", 0] for i in range(100)]
    + [
        [(i + 64, 640 - randint(0, 10) * 64, 64, 64), "bouncepad", 180]
        for i in range(100)
    ],
]

# for level in LEVELS[2:5]:
# for obj in LEVELS[5]:
#     li = []
#     # print(obj)
#     for i in obj[0]:
#         li.append(i * 64)
#     obj[0] = tuple(li)

# print(LEVELS[5])


# orig_rect = self.rect
# fx, fy = ceil(abs(self.xvel)), ceil(abs(self.yvel))
# max_speed = fx if fx > fy else fy
# if max_speed == 0:
#     self.dead = True
#     return None
# increment = [self.xvel / max_speed, self.yvel / max_speed]
# for _ in range(max_speed):
#     self.rect.x += increment[0]
#     self.rect.y += increment[1]
#     for obj in objects:
#         if not pygame.sprite.collide_mask(self, obj) and obj.name != "layer":
#             continue
#         self.dead = True
#         obj.touched = True
#         if obj.name == "target":
#             obj.hit(player)
#         if obj.name == "bouncepad":
#             self.yvel = -BOUNCE_STRENGTH
#             self.dead = False
#             self.rect = orig_rect
#             angles = [270, 90, 180, 0]
#             bounce_direction = [1, -1, 1, -1]
#             for i in range(len(angles)):
#                 if obj.angle == angles[i]:
#                     obj.bounced = 1
#                     bounce = BOUNCE_STRENGTH * bounce_direction[i]
#                     if i // 2 == 0:
#                         self.xvel = bounce
#                     else:
#                         self.yvel = bounce
#         return None
# self.rect = orig_rect
