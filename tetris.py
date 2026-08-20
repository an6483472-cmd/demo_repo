#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
俄罗斯方块 (Tetris)
使用 pygame 实现的经典俄罗斯方块小游戏。

操作说明：
    左方向键   : 方块左移
    右方向键   : 方块右移
    下方向键   : 加速下落（软降）
    上方向键   : 旋转方块
    空格键     : 硬降（直接落到底部）
    P 键       : 暂停 / 继续
    R 键       : 游戏结束后重新开始
    ESC / 关闭窗口 : 退出游戏
"""

import random
import sys

import pygame

# ---------------------------------------------------------------------------
# 基础配置
# ---------------------------------------------------------------------------
COLS = 10                  # 游戏区域列数
ROWS = 20                  # 游戏区域行数
CELL_SIZE = 30              # 每个格子的像素大小
BOARD_WIDTH = COLS * CELL_SIZE
BOARD_HEIGHT = ROWS * CELL_SIZE

SIDE_PANEL_WIDTH = 200       # 右侧信息面板宽度
MARGIN = 20                  # 边距

SCREEN_WIDTH = BOARD_WIDTH + SIDE_PANEL_WIDTH + MARGIN * 3
SCREEN_HEIGHT = BOARD_HEIGHT + MARGIN * 2

FPS = 60

# 下落速度相关：等级越高，下落间隔越短（毫秒）
BASE_FALL_INTERVAL = 800
MIN_FALL_INTERVAL = 100
LEVEL_SPEED_STEP = 60
LINES_PER_LEVEL = 10

# ---------------------------------------------------------------------------
# 颜色定义
# ---------------------------------------------------------------------------
BLACK = (15, 15, 20)
WHITE = (240, 240, 240)
GRAY = (60, 60, 70)
GRID_COLOR = (40, 40, 50)
RED = (255, 80, 80)
YELLOW = (255, 255, 255)

# 每种方块的颜色（索引对应 TETROMINOES 的 key）
COLORS = {
    "I": (0, 240, 240),
    "O": (240, 240, 0),
    "T": (160, 0, 240),
    "S": (0, 240, 0),
    "Z": (240, 0, 0),
    "J": (0, 0, 240),
    "L": (240, 160, 0),
}

# ---------------------------------------------------------------------------
# 方块形状定义（每种方块给出 4 种旋转状态，使用 4x4 网格坐标表示）
# ---------------------------------------------------------------------------
TETROMINOES = {
    "I": [
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        [(1, 0), (1, 1), (1, 2), (1, 3)],
    ],
    "O": [
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
    ],
    "T": [
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "S": [
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
        [(1, 1), (2, 1), (0, 2), (1, 2)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "Z": [
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (1, 2), (2, 2)],
        [(1, 0), (0, 1), (1, 1), (0, 2)],
    ],
    "J": [
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    "L": [
        [(2, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
}

SHAPE_KEYS = list(TETROMINOES.keys())


class Piece:
    """表示一个当前正在下落的方块"""

    def __init__(self, shape_key):
        self.shape_key = shape_key
        self.rotation = 0
        # 初始位置：水平居中偏上
        self.x = COLS // 2 - 2
        self.y = -2

    def cells(self, rotation=None, x=None, y=None):
        """返回当前方块占用的棋盘坐标列表"""
        rotation = self.rotation if rotation is None else rotation
        x = self.x if x is None else x
        y = self.y if y is None else y
        shape = TETROMINOES[self.shape_key][rotation % 4]
        return [(x + cx, y + cy) for cx, cy in shape]

    def color(self):
        return COLORS[self.shape_key]


class Board:
    """游戏棋盘，负责存储已落地的方块与消行逻辑"""

    def __init__(self):
        self.grid = [[None for _ in range(COLS)] for _ in range(ROWS)]

    def is_valid_position(self, cells):
        for x, y in cells:
            if x < 0 or x >= COLS:
                return False
            if y >= ROWS:
                return False
            if y >= 0 and self.grid[y][x] is not None:
                return False
        return True

    def lock_piece(self, piece):
        for x, y in piece.cells():
            if 0 <= y < ROWS and 0 <= x < COLS:
                self.grid[y][x] = piece.color()

    def clear_lines(self):
        """消除已填满的行，返回消除的行数"""
        new_grid = [row for row in self.grid if any(cell is None for cell in row)]
        cleared = ROWS - len(new_grid)
        for _ in range(cleared):
            new_grid.insert(0, [None for _ in range(COLS)])
        self.grid = new_grid
        return cleared

    def is_game_over(self):
        return any(cell is not None for cell in self.grid[0])


def random_bag():
    """使用 '7 袋随机' 算法生成方块顺序，保证公平性"""
    bag = SHAPE_KEYS[:]
    random.shuffle(bag)
    return bag


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("俄罗斯方块 Tetris")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont("Arial", 36, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 24, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 18)

        self.reset()

    def reset(self):
        self.board = Board()
        self.bag = random_bag()
        self.next_bag = random_bag()
        self.current = Piece(self._next_shape())
        self.hold_shape = None
        self.can_hold = True
        self.score = 0
        self.lines_cleared_total = 0
        self.level = 1
        self.fall_interval = BASE_FALL_INTERVAL
        self.fall_timer = 0
        self.paused = False
        self.game_over = False

    def _next_shape(self):
        if not self.bag:
            self.bag = self.next_bag
            self.next_bag = random_bag()
        return self.bag.pop(0)

    def peek_next_shape(self):
        if self.bag:
            return self.bag[0]
        return self.next_bag[0]

    def spawn_piece(self):
        self.current = Piece(self._next_shape())
        self.can_hold = True
        if not self.board.is_valid_position(self.current.cells()):
            self.game_over = True

    def try_move(self, dx, dy):
        new_cells = self.current.cells(x=self.current.x + dx, y=self.current.y + dy)
        if self.board.is_valid_position(new_cells):
            self.current.x += dx
            self.current.y += dy
            return True
        return False

    def try_rotate(self):
        new_rotation = (self.current.rotation + 1) % 4
        # 简单的踢墙（wall kick）尝试：依次尝试偏移量
        for dx in (0, -1, 1, -2, 2):
            new_cells = self.current.cells(rotation=new_rotation, x=self.current.x + dx)
            if self.board.is_valid_position(new_cells):
                self.current.rotation = new_rotation
                self.current.x += dx
                return True
        return False

    def hard_drop(self):
        drop_distance = 0
        while self.try_move(0, 1):
            drop_distance += 1
        self.score += drop_distance * 2
        self.lock_current_piece()

    def hold_piece(self):
        if not self.can_hold:
            return
        if self.hold_shape is None:
            self.hold_shape = self.current.shape_key
            self.spawn_piece()
        else:
            self.hold_shape, new_shape = self.current.shape_key, self.hold_shape
            self.current = Piece(new_shape)
        self.can_hold = False

    def lock_current_piece(self):
        self.board.lock_piece(self.current)
        cleared = self.board.clear_lines()
        if cleared:
            self.lines_cleared_total += cleared
            self.score += self._score_for_lines(cleared)
            new_level = self.lines_cleared_total // LINES_PER_LEVEL + 1
            if new_level != self.level:
                self.level = new_level
                self.fall_interval = max(
                    MIN_FALL_INTERVAL,
                    BASE_FALL_INTERVAL - (self.level - 1) * LEVEL_SPEED_STEP,
                )
        self.spawn_piece()

    @staticmethod
    def _score_for_lines(cleared):
        return {1: 100, 2: 300, 3: 500, 4: 800}.get(cleared, 0)

    def ghost_piece_y(self):
        """计算幽灵方块（落地预览）的 y 坐标偏移"""
        offset = 0
        while self.board.is_valid_position(
            self.current.cells(y=self.current.y + offset + 1)
        ):
            offset += 1
        return self.current.y + offset

    # ------------------------------------------------------------------
    # 更新与渲染
    # ------------------------------------------------------------------
    def update(self, dt):
        if self.paused or self.game_over:
            return
        self.fall_timer += dt
        if self.fall_timer >= self.fall_interval:
            self.fall_timer = 0
            if not self.try_move(0, 1):
                self.lock_current_piece()

    def draw_cell(self, surface, x, y, color, board_x, board_y):
        rect = pygame.Rect(
            board_x + x * CELL_SIZE,
            board_y + y * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE,
        )
        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, BLACK, rect, 1)

    def draw_board(self):
        board_x = MARGIN
        board_y = MARGIN

        pygame.draw.rect(
            self.screen, GRAY,
            (board_x - 2, board_y - 2, BOARD_WIDTH + 4, BOARD_HEIGHT + 4), 2
        )

        # 网格背景
        for row in range(ROWS):
            for col in range(COLS):
                rect = pygame.Rect(
                    board_x + col * CELL_SIZE,
                    board_y + row * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE,
                )
                pygame.draw.rect(self.screen, GRID_COLOR, rect, 1)

        # 已落地的方块
        for row in range(ROWS):
            for col in range(COLS):
                color = self.board.grid[row][col]
                if color is not None:
                    self.draw_cell(self.screen, col, row, color, board_x, board_y)

        if not self.game_over:
            # 幽灵方块
            ghost_y = self.ghost_piece_y()
            ghost_color = tuple(max(c - 120, 40) for c in self.current.color())
            for x, y in self.current.cells(y=ghost_y):
                if y >= 0:
                    self.draw_cell(self.screen, x, y, ghost_color, board_x, board_y)

            # 当前方块
            for x, y in self.current.cells():
                if y >= 0:
                    self.draw_cell(self.screen, x, y, self.current.color(), board_x, board_y)

    def draw_mini_shape(self, shape_key, top_left, box_size=4):
        if shape_key is None:
            return
        color = COLORS[shape_key]
        shape = TETROMINOES[shape_key][0]
        cell = 20
        for cx, cy in shape:
            rect = pygame.Rect(
                top_left[0] + cx * cell,
                top_left[1] + cy * cell,
                cell,
                cell,
            )
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, BLACK, rect, 1)

    def draw_side_panel(self):
        panel_x = MARGIN * 2 + BOARD_WIDTH
        y = MARGIN

        title = self.font_large.render("俄罗斯方块", True, WHITE)
        self.screen.blit(title, (panel_x, y))
        y += 60

        score_label = self.font_medium.render("分数", True, GRAY)
        self.screen.blit(score_label, (panel_x, y))
        y += 28
        score_val = self.font_large.render(str(self.score), True, WHITE)
        self.screen.blit(score_val, (panel_x, y))
        y += 50

        level_label = self.font_medium.render("等级", True, GRAY)
        self.screen.blit(level_label, (panel_x, y))
        y += 28
        level_val = self.font_medium.render(str(self.level), True, WHITE)
        self.screen.blit(level_val, (panel_x, y))
        y += 40

        lines_label = self.font_medium.render("消除行数", True, GRAY)
        self.screen.blit(lines_label, (panel_x, y))
        y += 28
        lines_val = self.font_medium.render(str(self.lines_cleared_total), True, WHITE)
        self.screen.blit(lines_val, (panel_x, y))
        y += 50

        next_label = self.font_medium.render("下一个", True, GRAY)
        self.screen.blit(next_label, (panel_x, y))
        y += 30
        self.draw_mini_shape(self.peek_next_shape(), (panel_x, y))
        y += 100

        hold_label = self.font_medium.render("暂存 (C)", True, GRAY)
        self.screen.blit(hold_label, (panel_x, y))
        y += 30
        self.draw_mini_shape(self.hold_shape, (panel_x, y))
        y += 100

        help_lines = [
            "← → : 移动",
            "↑   : 旋转",
            "↓   : 软降",
            "空格 : 硬降",
            "C   : 暂存",
            "P   : 暂停",
            "R   : 重新开始",
        ]
        for line in help_lines:
            help_surf = self.font_small.render(line, True, GRAY)
            self.screen.blit(help_surf, (panel_x, y))
            y += 22

    def draw_overlay_text(self, lines):
        overlay = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (MARGIN, MARGIN))

        total_height = len(lines) * 40
        start_y = MARGIN + (BOARD_HEIGHT - total_height) // 2
        for i, text in enumerate(lines):
            surf = self.font_medium.render(text, True, WHITE)
            rect = surf.get_rect(
                center=(MARGIN + BOARD_WIDTH // 2, start_y + i * 40)
            )
            self.screen.blit(surf, rect)

    def draw(self):
        self.screen.fill(BLACK)
        self.draw_board()
        self.draw_side_panel()

        if self.game_over:
            self.draw_overlay_text(["游戏结束", f"最终分数: {self.score}", "按 R 重新开始"])
        elif self.paused:
            self.draw_overlay_text(["已暂停", "按 P 继续"])

        pygame.display.flip()

    # ------------------------------------------------------------------
    # 主循环
    # ------------------------------------------------------------------
    def handle_keydown(self, key):
        if key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit(0)

        if self.game_over:
            if key == pygame.K_r:
                self.reset()
            return

        if key == pygame.K_p:
            self.paused = not self.paused
            return

        if self.paused:
            return

        if key == pygame.K_LEFT:
            self.try_move(-1, 0)
        elif key == pygame.K_RIGHT:
            self.try_move(1, 0)
        elif key == pygame.K_DOWN:
            if self.try_move(0, 1):
                self.score += 1
        elif key == pygame.K_UP:
            self.try_rotate()
        elif key == pygame.K_SPACE:
            self.hard_drop()
        elif key == pygame.K_c:
            self.hold_piece()

    def run(self):
        while True:
            dt = self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                elif event.type == pygame.KEYDOWN:
                    self.handle_keydown(event.key)

            self.update(dt)
            self.draw()


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
