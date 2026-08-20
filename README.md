# 俄罗斯方块 (Tetris)

使用 Python + [pygame-ce](https://pyga.me/) 实现的经典俄罗斯方块小游戏。

> 说明：由于本机安装的是 Python 3.14，官方 `pygame` 包目前还没有针对 3.14 的预编译安装包（从源码编译会因缺少系统级 SDL 依赖而失败），因此改用其社区维护、完全兼容的分支 `pygame-ce`（Community Edition）。代码中依然是 `import pygame`，使用方式完全一致。

## 目录结构

```
俄罗斯方块/
├── venv/               # Python 虚拟环境（已创建，包含依赖）
├── tetris.py           # 游戏主程序
├── requirements.txt    # 依赖列表
└── README.md           # 本说明文件
```

## 环境准备（已完成）

虚拟环境已经创建在 `venv/` 目录下，并已安装好依赖。如果需要在新环境中重新搭建，可执行：

```bash
cd "/Users/angela/cursor_project/俄罗斯方块"
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

## 运行游戏

```bash
cd "/Users/angela/cursor_project/俄罗斯方块"
./venv/bin/python tetris.py
```

## 操作说明

| 按键 | 功能 |
| ---- | ---- |
| ← / → | 左右移动方块 |
| ↑ | 旋转方块 |
| ↓ | 加速下落（软降，每格 +1 分） |
| 空格 | 硬降（直接落到底部，每格 +2 分） |
| C | 暂存 / 交换当前方块 |
| P | 暂停 / 继续 |
| R | 游戏结束后重新开始 |
| ESC | 退出游戏 |

## 计分规则

- 单次消除 1 / 2 / 3 / 4 行分别获得 100 / 300 / 500 / 800 分。
- 每消除 10 行提升一个等级，等级越高下落速度越快。
- 软降、硬降会额外获得少量分数。

祝你玩得开心！
