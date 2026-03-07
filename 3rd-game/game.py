#!/usr/bin/env python3
"""
小朋友下樓梯 (Children Going Down Stairs)
終端機版本

遊戲規則:
- 2~4 位玩家，從第 20 階開始，目標是最先抵達第 0 階（地面）
- 每回合擲一顆骰子（1~6），向下移動對應步數
- 部分階梯有特殊事件（捷徑 / 陷阱）
- 超過第 0 階的點數會「反彈」回來
- 先踩到第 0 階者獲勝
"""

import random
import time
import os
import sys

# ─────────────────────────── 常數 ───────────────────────────

TOTAL_STEPS = 20          # 樓梯總階數（從 20 往 0 走）
PLAYER_ICONS = ["🐶", "🐱", "🐭", "🐹"]
PLAYER_COLORS = ["\033[93m", "\033[96m", "\033[92m", "\033[95m"]  # yellow/cyan/green/magenta
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
BLUE = "\033[94m"

# 特殊格子：{踩到的階數: (移動到的階數, 說明)}
SPECIAL_TILES = {
    17: (13, "🌈 彩虹滑梯！直接滑到第 13 階！"),
    14: (10, "🚀 火箭噴射！飛到第 10 階！"),
    11: ( 7, "⚡ 閃電加速！跳到第 7 階！"),
    8:  ( 4, "🎿 溜冰道！直滑到第 4 階！"),
    # 陷阱
    16: (19, "🕸️  蜘蛛網！被困住，退回第 19 階！"),
    12: (15, "🍌 香蕉皮！滑倒，退到第 15 階！"),
    6:  ( 9, "🌊 水坑！踩濕，退回第 9 階！"),
    3:  ( 5, "😈 搗蛋鬼！被推回第 5 階！"),
}

# ─────────────────────────── 工具函式 ───────────────────────────

def clear():
    os.system("cls" if os.name == "nt" else "clear")


def colored(text, color):
    return f"{color}{text}{RESET}"


def bold(text):
    return f"{BOLD}{text}{RESET}"


def roll_dice():
    return random.randint(1, 6)


def bounce(pos, steps):
    """超過 0 階時反彈"""
    new_pos = pos - steps
    if new_pos < 0:
        new_pos = abs(new_pos)  # 反彈
    return new_pos

# ─────────────────────────── 畫面繪製 ───────────────────────────

def draw_board(players):
    """繪製樓梯示意圖（右側顯示玩家位置）"""
    lines = []
    lines.append(bold("╔══════════════════════════════════════╗"))
    lines.append(bold("║       🏠  小朋友下樓梯  🏠            ║"))
    lines.append(bold("╚══════════════════════════════════════╝"))
    lines.append("")

    for step in range(TOTAL_STEPS, -1, -1):
        # 收集站在這一階的玩家
        here = [p for p in players if p["pos"] == step]

        # 特殊格子標記
        if step in SPECIAL_TILES:
            dest, _ = SPECIAL_TILES[step]
            marker = colored("★", "\033[93m") if dest < step else colored("▼", RED)
        else:
            marker = " "

        # 玩家圖示
        icons = "".join(
            colored(p["icon"], PLAYER_COLORS[p["id"]]) for p in here
        )

        if step == 0:
            label = colored("🏁 終點 [地面]", "\033[92m")
            bar = ""
        else:
            label = f"第 {step:2d} 階 {marker}"
            indent = " " * (TOTAL_STEPS - step)
            bar = indent + "█" * (step)

        player_str = f"  {icons}" if icons else ""
        lines.append(f"  {label:<22} {bar[:28]}{player_str}")

    return "\n".join(lines)


def draw_legend():
    lines = ["", bold("─── 特殊格說明 ───")]
    lines.append(f"  {colored('★', chr(27)+'[93m')} 捷徑（往下跳）")
    lines.append(f"  {colored('▼', RED)} 陷阱（往上退）")
    for step, (dest, desc) in sorted(SPECIAL_TILES.items()):
        lines.append(f"  第{step:2d}階 → {desc}")
    return "\n".join(lines)


def draw_scores(players):
    lines = ["", bold("─── 玩家狀態 ───")]
    for p in players:
        bar_done = TOTAL_STEPS - p["pos"]
        bar_left = p["pos"]
        progress = f"[{'█'*bar_done}{'░'*bar_left}]"
        lines.append(
            f"  {colored(p['icon'], PLAYER_COLORS[p['id']])} "
            f"{p['name']:<6} 位於第 {p['pos']:2d} 階  {progress}"
        )
    return "\n".join(lines)

# ─────────────────────────── 遊戲邏輯 ───────────────────────────

def setup_players():
    print(bold("\n=== 🎮 小朋友下樓梯 ===\n"))
    while True:
        try:
            n = int(input("請輸入玩家人數（2~4）："))
            if 2 <= n <= 4:
                break
            print("請輸入 2 到 4 之間的數字。")
        except ValueError:
            print("請輸入有效的數字。")

    players = []
    for i in range(n):
        default_name = f"玩家{i+1}"
        name = input(f"請輸入{default_name}的名字（直接 Enter 使用預設）：").strip()
        name = name if name else default_name
        players.append({
            "id": i,
            "name": name,
            "icon": PLAYER_ICONS[i],
            "pos": TOTAL_STEPS,   # 從最高階出發
            "wins": 0,
        })
    return players


def player_turn(player, players):
    """執行一個玩家的回合，回傳事件訊息列表"""
    messages = []
    color = PLAYER_COLORS[player["id"]]

    input(f"\n  {colored(player['icon'], color)} {player['name']} 的回合，按 Enter 擲骰子...")

    dice = roll_dice()
    messages.append(f"  🎲 擲出了 {bold(str(dice))} 點！")

    old_pos = player["pos"]
    new_pos = bounce(old_pos, dice)

    if new_pos != old_pos - dice:
        messages.append(f"  💥 超過終點，反彈回第 {new_pos} 階！")
    else:
        messages.append(f"  📍 從第 {old_pos} 階 → 第 {new_pos} 階")

    player["pos"] = new_pos

    # 特殊格子觸發
    if new_pos in SPECIAL_TILES and new_pos != 0:
        dest, desc = SPECIAL_TILES[new_pos]
        messages.append(f"  {desc}")
        player["pos"] = dest
        messages.append(f"  📍 最終位置：第 {dest} 階")

    return messages


def run_game(players):
    """執行單局遊戲，回傳獲勝者"""
    # 重置位置
    for p in players:
        p["pos"] = TOTAL_STEPS

    turn = 0
    while True:
        current = players[turn % len(players)]

        clear()
        print(draw_board(players))
        print(draw_scores(players))
        print(draw_legend())
        print()

        messages = player_turn(current, players)

        clear()
        print(draw_board(players))
        print(draw_scores(players))
        print()
        for msg in messages:
            print(msg)

        if current["pos"] == 0:
            return current

        turn += 1
        time.sleep(0.5)

# ─────────────────────────── 主程式 ───────────────────────────

def main():
    players = setup_players()
    scores = {p["id"]: 0 for p in players}

    while True:
        winner = run_game(players)
        scores[winner["id"]] += 1

        print()
        print(colored(f"\n🎉🎉 恭喜 {winner['icon']} {winner['name']} 獲勝！🎉🎉", "\033[93m"))
        print()
        print(bold("─── 累計戰績 ───"))
        for p in players:
            print(f"  {colored(p['icon'], PLAYER_COLORS[p['id']])} {p['name']}: {scores[p['id']]} 勝")

        print()
        again = input("再玩一局？(y/n)：").strip().lower()
        if again != "y":
            print("\n感謝遊玩！掰掰～ 👋\n")
            break


if __name__ == "__main__":
    main()
