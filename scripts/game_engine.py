#!/usr/bin/env python3
"""
Neon Cyber Pac-Man: Contribution Grid Edition
Automated 24-Hour Retro Arcade Simulation for GitHub Profile README
Authored for: afifasyed123
"""

import os
import sys
import json
import math
import random
from datetime import datetime, timezone

# Maze dimensions (21 columns x 11 rows)
# # = Wall
# . = Cyber Pellet (10 pts)
# * = Power Energizer Pellet (50 pts, frightens ghosts)
# C = Cyber Cherry Bonus (100 pts)
#   = Empty space
DEFAULT_MAZE = [
    "#####################",
    "#.........#.........#",
    "#.###.###.#.###.###.#",
    "#*# #.# #.#.# #.# #*#",
    "#.....###...###.....#",
    "###.#.#   G   #.#.###",
    "#.....###...###.....#",
    "#*# #.# #.#.# #.# #*#",
    "#.###.###.#.###.###.#",
    "#.........#.........#",
    "#####################"
]

GHOST_HOUSE = [(9, 5), (10, 5), (11, 5)]

DIRECTIONS = {
    "UP": (0, -1),
    "DOWN": (0, 1),
    "LEFT": (-1, 0),
    "RIGHT": (1, 0)
}

GHOST_CONFIGS = [
    {"name": "Blinky", "color": "#FF0055", "start": (9, 5), "scatter": (19, 1)},
    {"name": "Pinky",  "color": "#FF1493", "start": (10, 5), "scatter": (1, 1)},
    {"name": "Inky",   "color": "#00F5D4", "start": (11, 5), "scatter": (19, 9)},
    {"name": "Clyde",  "color": "#FFAA00", "start": (10, 4), "scatter": (1, 9)}
]

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
README_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "README.md")
STATE_PATH = os.path.join(DATA_DIR, "game_state.json")
BOARD_SVG_PATH = os.path.join(ASSETS_DIR, "game-board.svg")


def create_initial_state():
    """Build fresh initial state for Level 1."""
    maze = [list(row) for row in DEFAULT_MAZE]
    # Place bonus cherry at center entrance
    maze[4][10] = 'C'

    return {
        "level": 1,
        "score": 0,
        "high_score": 0,
        "day_streak": 0,
        "last_played": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "pacman": {
            "x": 10,
            "y": 9,
            "dir": "LEFT",
            "lives": 3
        },
        "ghosts": [
            {
                "name": g["name"],
                "color": g["color"],
                "x": g["start"][0],
                "y": g["start"][1],
                "dir": "UP",
                "scatter": g["scatter"],
                "frightened": False
            }
            for g in GHOST_CONFIGS
        ],
        "frightened_timer": 0,
        "maze": ["".join(row) for row in maze],
        "pellets_total": sum(row.count('.') + row.count('*') for row in maze),
        "recent_logs": [
            "🚀 Simulation booted! Pac-Man spawned in Neon Cyber Grid.",
            "🎮 AI BFS pathfinding initialized with 4 autonomous ghosts."
        ]
    }


def load_state():
    """Load state from JSON or initialize new one."""
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                state = json.load(f)
                return state
        except Exception as e:
            print(f"Warning: Failed to parse {STATE_PATH}: {e}. Initializing fresh state.")
    return create_initial_state()


def save_state(state):
    """Save game state to JSON."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def is_wall(maze, x, y):
    """Check if (x, y) is out of bounds or wall."""
    if y < 0 or y >= len(maze) or x < 0 or x >= len(maze[0]):
        return True
    return maze[y][x] == '#'


def get_neighbors(maze, x, y, allow_ghost_house=False):
    """Get valid adjacent walkable cells."""
    neighbors = []
    for dname, (dx, dy) in DIRECTIONS.items():
        nx, ny = x + dx, y + dy
        if not is_wall(maze, nx, ny):
            if not allow_ghost_house and (nx, ny) in GHOST_HOUSE:
                continue
            neighbors.append((dname, nx, ny))
    return neighbors


def bfs_find_path(maze, start, targets, allow_ghost_house=False):
    """Find shortest path from start to closest target using BFS."""
    if not targets:
        return None
    target_set = set(targets)
    queue = [(start[0], start[1], [])]
    visited = {(start[0], start[1])}

    while queue:
        cx, cy, path = queue.pop(0)
        if (cx, cy) in target_set:
            return path

        for dname, nx, ny in get_neighbors(maze, cx, cy, allow_ghost_house):
            if (nx, ny) not in visited:
                visited.add((nx, ny))
                queue.append((nx, ny, path + [(dname, nx, ny)]))

    return None


def simulate_turn(state, steps=7):
    """Simulate a daily mini-round with intelligent AI behaviors."""
    maze = [list(row) for row in state["maze"]]
    pac = state["pacman"]
    ghosts = state["ghosts"]
    frightened_timer = state.get("frightened_timer", 0)

    turn_pellets_eaten = 0
    turn_ghosts_eaten = 0
    turn_points = 0
    step_events = []

    # Count remaining pellets
    remaining_pellets = sum(row.count('.') + row.count('*') + row.count('C') for row in maze)
    if remaining_pellets == 0:
        # Reset maze for next level!
        state["level"] += 1
        level_bonus = 500 * state["level"]
        state["score"] += level_bonus
        fresh = create_initial_state()
        maze = [list(row) for row in fresh["maze"]]
        pac["x"], pac["y"], pac["dir"] = fresh["pacman"]["x"], fresh["pacman"]["y"], fresh["pacman"]["dir"]
        for i, g in enumerate(ghosts):
            g["x"], g["y"] = fresh["ghosts"][i]["x"], fresh["ghosts"][i]["y"]
            g["frightened"] = False
        frightened_timer = 0
        step_events.append(f"🏆 MAZE CLEARED! Level {state['level']} Unlocked (+{level_bonus} bonus pts)!")

    for step_num in range(steps):
        # Update frightened countdown
        if frightened_timer > 0:
            frightened_timer -= 1
            if frightened_timer == 0:
                for g in ghosts:
                    g["frightened"] = False
                step_events.append("⚡ Ghost Energizer wore off!")

        # 1. Target selection for Pac-Man
        # If energized and ghosts nearby, hunt frightened ghosts!
        targets = []
        if frightened_timer > 0:
            frightened_coords = [(g["x"], g["y"]) for g in ghosts if g.get("frightened", False)]
            if frightened_coords:
                targets = frightened_coords

        if not targets:
            # Find all pellets, energizers, cherries
            for y, row in enumerate(maze):
                for x, ch in enumerate(row):
                    if ch in ('.', '*', 'C'):
                        targets.append((x, y))

        if not targets:
            # Fallback: explore any open cell
            for y, row in enumerate(maze):
                for x, ch in enumerate(row):
                    if ch == ' ' and (x, y) not in GHOST_HOUSE:
                        targets.append((x, y))

        # BFS path to closest target
        path = bfs_find_path(maze, (pac["x"], pac["y"]), targets)
        if path and len(path) > 0:
            next_dir, next_x, next_y = path[0]
            pac["dir"] = next_dir
            pac["x"] = next_x
            pac["y"] = next_y
        else:
            # Random legal move
            valid = get_neighbors(maze, pac["x"], pac["y"])
            if valid:
                next_dir, next_x, next_y = random.choice(valid)
                pac["dir"] = next_dir
                pac["x"] = next_x
                pac["y"] = next_y

        # Consume item on cell
        cell_item = maze[pac["y"]][pac["x"]]
        if cell_item == '.':
            maze[pac["y"]][pac["x"]] = ' '
            state["score"] += 10
            turn_points += 10
            turn_pellets_eaten += 1
        elif cell_item == '*':
            maze[pac["y"]][pac["x"]] = ' '
            state["score"] += 50
            turn_points += 50
            frightened_timer = 12
            for g in ghosts:
                g["frightened"] = True
            step_events.append("🌟 Power Energizer consumed! Ghosts became Frightened!")
        elif cell_item == 'C':
            maze[pac["y"]][pac["x"]] = ' '
            state["score"] += 100
            turn_points += 100
            step_events.append("🍒 Cyber Cherry collected (+100 pts)!")

        # 2. Ghost Movement
        for g in ghosts:
            g_neighbors = get_neighbors(maze, g["x"], g["y"], allow_ghost_house=True)
            if not g_neighbors:
                continue

            if g.get("frightened", False):
                # Wander away or randomly
                chosen_move = random.choice(g_neighbors)
                g["dir"], g["x"], g["y"] = chosen_move
            else:
                # Target: Blinky targets Pac-Man directly, Pinky targets 2 tiles ahead, others wander/scatter
                if g["name"] == "Blinky":
                    g_target = (pac["x"], pac["y"])
                elif g["name"] == "Pinky":
                    dx, dy = DIRECTIONS.get(pac["dir"], (0, 0))
                    g_target = (pac["x"] + dx * 2, pac["y"] + dy * 2)
                else:
                    g_target = g["scatter"]

                # Pick neighbor closest to target (Euclidean distance)
                best_neighbor = min(
                    g_neighbors,
                    key=lambda n: math.dist((n[1], n[2]), g_target)
                )
                g["dir"], g["x"], g["y"] = best_neighbor

            # Check collision with Pac-Man
            if g["x"] == pac["x"] and g["y"] == pac["y"]:
                if g.get("frightened", False):
                    # Pac-Man eats ghost!
                    state["score"] += 200
                    turn_points += 200
                    turn_ghosts_eaten += 1
                    g["x"], g["y"] = 10, 5  # Respawn in ghost house
                    g["frightened"] = False
                    step_events.append(f"💥 Pac-Man chomped {g['name']} in blue mode (+200 pts)!")
                else:
                    # Ghost catches Pac-Man
                    step_events.append(f"⚠️ Close encounter with {g['name']}! Shield activated.")
                    # Respawn Pac-Man safely
                    pac["x"], pac["y"] = 10, 9

    # Update High Score
    if state["score"] > state.get("high_score", 0):
        state["high_score"] = state["score"]

    state["frightened_timer"] = frightened_timer
    state["maze"] = ["".join(row) for row in maze]
    state["day_streak"] = state.get("day_streak", 0) + 1
    state["last_played"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Format summary log
    summary = (
        f"Day {state['day_streak']} Turn: 🤖 BFS traversed {steps} nodes | "
        f"Consolidated {turn_pellets_eaten} pellets"
    )
    if turn_ghosts_eaten > 0:
        summary += f" & defeated {turn_ghosts_eaten} ghosts"
    summary += f" (+{turn_points} pts). Score: {state['score']}."

    new_logs = [summary] + step_events + state.get("recent_logs", [])
    state["recent_logs"] = new_logs[:5]

    return state


def render_svg(state):
    """Render a high-definition Neon Cyber Pac-Man SVG board."""
    width = 860
    height = 470
    cols = len(state["maze"][0])
    rows = len(state["maze"])

    tile_w = 36
    tile_h = 28
    maze_ox = (width - (cols * tile_w)) // 2
    maze_oy = 92

    pac = state["pacman"]
    ghosts = state["ghosts"]
    frightened_timer = state.get("frightened_timer", 0)
    score = state["score"]
    high_score = state.get("high_score", score)
    level = state.get("level", 1)
    streak = state.get("day_streak", 1)
    last_log = state.get("recent_logs", ["Game active."])[0]

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="auto">')
    
    # CSS & Defs
    svg.append("""
  <defs>
    <!-- Background Gradient -->
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#080711" />
      <stop offset="50%" stop-color="#0F0C20" />
      <stop offset="100%" stop-color="#070611" />
    </linearGradient>

    <!-- Neon Pink to Purple Border Gradient -->
    <linearGradient id="borderGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FF1493" />
      <stop offset="50%" stop-color="#7928CA" />
      <stop offset="100%" stop-color="#00F5D4" />
    </linearGradient>

    <!-- Wall Conduit Gradient -->
    <linearGradient id="wallGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FF007F" />
      <stop offset="50%" stop-color="#9900FF" />
      <stop offset="100%" stop-color="#4361EE" />
    </linearGradient>

    <!-- Neon Glow Filter -->
    <filter id="neonGlow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <filter id="softGlow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="1.5" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <!-- Grid Pattern -->
    <pattern id="cyberGrid" width="20" height="20" patternUnits="userSpaceOnUse">
      <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#FFFFFF" stroke-width="0.3" stroke-opacity="0.05" />
    </pattern>
  </defs>

  <style>
    .arcade-font { font-family: 'Courier New', Courier, monospace, system-ui; font-weight: 800; letter-spacing: 1px; }
    .neon-text { font-family: system-ui, -apple-system, sans-serif; font-weight: 700; }
    .pulse-dot { animation: pulse 2s infinite alternate ease-in-out; }
    @keyframes pulse { from { r: 5px; opacity: 0.8; } to { r: 7.5px; opacity: 1; } }
  </style>
""")

    # Main Card Body
    svg.append(f'  <!-- Card Frame -->')
    svg.append(f'  <rect x="2" y="2" width="{width-4}" height="{height-4}" rx="18" fill="url(#bgGrad)" stroke="url(#borderGrad)" stroke-width="2.5" />')
    svg.append(f'  <rect x="2" y="2" width="{width-4}" height="{height-4}" rx="18" fill="url(#cyberGrid)" />')

    # Top HUD Bar
    svg.append(f'  <!-- Header Section -->')
    svg.append(f'  <g transform="translate(25, 24)">')
    
    # Title & Icon
    svg.append(f'    <text x="0" y="22" fill="#FF1493" class="arcade-font" font-size="20" filter="url(#softGlow)">🕹️ NEON CYBER PAC-MAN</text>')
    svg.append(f'    <text x="0" y="44" fill="#8E8BA7" class="neon-text" font-size="12">Daily Autonomous AI Arcade • Powered by 24h Cron Sync</text>')

    # Stats Badges
    hud_x = width - 50
    # Streak Badge
    svg.append(f'    <rect x="{hud_x-465}" y="2" width="105" height="38" rx="8" fill="#FF1493" fill-opacity="0.15" stroke="#FF1493" stroke-width="1.2"/>')
    svg.append(f'    <text x="{hud_x-412}" y="18" text-anchor="middle" fill="#FF69B4" class="neon-text" font-size="10">DAY STREAK</text>')
    svg.append(f'    <text x="{hud_x-412}" y="33" text-anchor="middle" fill="#FFFFFF" class="arcade-font" font-size="14">🔥 {streak}</text>')

    # Level Badge
    svg.append(f'    <rect x="{hud_x-348}" y="2" width="95" height="38" rx="8" fill="#7928CA" fill-opacity="0.2" stroke="#7928CA" stroke-width="1.2"/>')
    svg.append(f'    <text x="{hud_x-300}" y="18" text-anchor="middle" fill="#B794F4" class="neon-text" font-size="10">LEVEL</text>')
    svg.append(f'    <text x="{hud_x-300}" y="33" text-anchor="middle" fill="#00F5D4" class="arcade-font" font-size="14">STAGE {level}</text>')

    # Score Badge
    svg.append(f'    <rect x="{hud_x-240}" y="2" width="115" height="38" rx="8" fill="#00F5D4" fill-opacity="0.15" stroke="#00F5D4" stroke-width="1.2"/>')
    svg.append(f'    <text x="{hud_x-182}" y="18" text-anchor="middle" fill="#00F5D4" class="neon-text" font-size="10">SCORE</text>')
    svg.append(f'    <text x="{hud_x-182}" y="33" text-anchor="middle" fill="#FFE600" class="arcade-font" font-size="14">{score:05d}</text>')

    # High Score Badge
    svg.append(f'    <rect x="{hud_x-112}" y="2" width="115" height="38" rx="8" fill="#FFE600" fill-opacity="0.15" stroke="#FFE600" stroke-width="1.2"/>')
    svg.append(f'    <text x="{hud_x-55}" y="18" text-anchor="middle" fill="#FFE600" class="neon-text" font-size="10">HIGH SCORE</text>')
    svg.append(f'    <text x="{hud_x-55}" y="33" text-anchor="middle" fill="#FFFFFF" class="arcade-font" font-size="14">🏆 {high_score:05d}</text>')

    svg.append(f'  </g>')

    # Maze Render
    svg.append(f'  <!-- Maze Container -->')
    svg.append(f'  <g transform="translate({maze_ox}, {maze_oy})">')
    
    # Maze backdrop
    maze_w = cols * tile_w
    maze_h = rows * tile_h
    svg.append(f'    <rect x="-6" y="-6" width="{maze_w+12}" height="{maze_h+12}" rx="12" fill="#05040B" stroke="#251B40" stroke-width="2" />')

    # Draw Walls
    for y, row in enumerate(state["maze"]):
        for x, cell in enumerate(row):
            cx = x * tile_w + tile_w // 2
            cy = y * tile_h + tile_h // 2
            if cell == '#':
                svg.append(f'    <rect x="{x*tile_w+2}" y="{y*tile_h+2}" width="{tile_w-4}" height="{tile_h-4}" rx="6" fill="#140D2D" stroke="url(#wallGrad)" stroke-width="1.8" />')
            elif cell == '.':
                # Cyber Pellet
                svg.append(f'    <circle cx="{cx}" cy="{cy}" r="3.2" fill="#00F5D4" opacity="0.85" filter="url(#softGlow)" />')
            elif cell == '*':
                # Energizer Pellet
                svg.append(f'    <circle cx="{cx}" cy="{cy}" r="6.5" fill="#FF1493" filter="url(#neonGlow)" />')
                svg.append(f'    <circle cx="{cx}" cy="{cy}" r="3" fill="#FFFFFF" opacity="0.9" />')
            elif cell == 'C':
                # Cyber Cherry
                svg.append(f'    <g transform="translate({cx-8}, {cy-8})">')
                svg.append(f'      <circle cx="5" cy="11" r="4.5" fill="#FF0055" />')
                svg.append(f'      <circle cx="11" cy="11" r="4.5" fill="#FF0055" />')
                svg.append(f'      <path d="M 5 7 Q 8 2 11 7" fill="none" stroke="#00F5D4" stroke-width="1.5" />')
                svg.append(f'      <path d="M 8 2 L 12 1" fill="none" stroke="#00F5D4" stroke-width="1.5" />')
                svg.append(f'    </g>')

    # Ghost House Center Marker
    gh_x = 9 * tile_w + 3
    gh_y = 5 * tile_h + 3
    svg.append(f'    <rect x="{gh_x}" y="{gh_y}" width="{tile_w*3-6}" height="{tile_h-6}" rx="4" fill="#0A0618" stroke="#FF1493" stroke-dasharray="4,4" stroke-width="1" opacity="0.6"/>')

    # Draw Ghosts
    for g in ghosts:
        gx = g["x"] * tile_w + tile_w // 2
        gy = g["y"] * tile_h + tile_h // 2
        is_frightened = g.get("frightened", False)
        gcolor = "#3A86FF" if is_frightened else g["color"]

        svg.append(f'    <!-- Ghost {g["name"]} -->')
        svg.append(f'    <g transform="translate({gx-11}, {gy-11})" filter="url(#softGlow)">')
        # Ghost body
        svg.append(f'      <path d="M 1 10 C 1 3 21 3 21 10 L 21 18 L 18 15 L 14 18 L 11 15 L 7 18 L 4 15 L 1 18 Z" fill="{gcolor}" />')
        if is_frightened:
            # Scared face
            svg.append(f'      <circle cx="7" cy="8" r="1.8" fill="#FFFFFF" />')
            svg.append(f'      <circle cx="15" cy="8" r="1.8" fill="#FFFFFF" />')
            svg.append(f'      <path d="M 5 13 Q 8 11 11 13 Q 14 11 17 13" fill="none" stroke="#FFE600" stroke-width="1.2" />')
        else:
            # Normal eyes looking in dir
            eye_offset_x = 0
            eye_offset_y = 0
            if g.get("dir") == "LEFT": eye_offset_x = -1.5
            elif g.get("dir") == "RIGHT": eye_offset_x = 1.5
            elif g.get("dir") == "UP": eye_offset_y = -1.5
            elif g.get("dir") == "DOWN": eye_offset_y = 1.5

            svg.append(f'      <ellipse cx="7" cy="8" rx="2.8" ry="3.5" fill="#FFFFFF" />')
            svg.append(f'      <ellipse cx="15" cy="8" rx="2.8" ry="3.5" fill="#FFFFFF" />')
            svg.append(f'      <circle cx="{7+eye_offset_x}" cy="{8+eye_offset_y}" r="1.5" fill="#0B0D19" />')
            svg.append(f'      <circle cx="{15+eye_offset_x}" cy="{8+eye_offset_y}" r="1.5" fill="#0B0D19" />')
        svg.append(f'    </g>')

    # Draw Pac-Man
    px = pac["x"] * tile_w + tile_w // 2
    py = pac["y"] * tile_h + tile_h // 2
    rotation = 0
    if pac["dir"] == "DOWN": rotation = 90
    elif pac["dir"] == "LEFT": rotation = 180
    elif pac["dir"] == "UP": rotation = 270

    svg.append(f'    <!-- Pac-Man Hero -->')
    svg.append(f'    <g transform="translate({px}, {py}) rotate({rotation})" filter="url(#neonGlow)">')
    # Pac-Man open wedge body
    svg.append(f'      <path d="M 0 0 L 11 -7 A 13 13 0 1 0 11 7 Z" fill="#FFE600" />')
    svg.append(f'      <circle cx="2" cy="-6" r="1.6" fill="#0B0D19" />')
    svg.append(f'    </g>')

    svg.append(f'  </g>')

    # Bottom Ticker Section
    svg.append(f'  <!-- Footer Ticker -->')
    svg.append(f'  <g transform="translate(25, {height-38})">')
    svg.append(f'    <rect x="0" y="0" width="{width-50}" height="28" rx="8" fill="#120D26" stroke="#3D2963" stroke-width="1" />')
    svg.append(f'    <circle cx="14" cy="14" r="4.5" fill="#00F5D4" filter="url(#softGlow)" />')
    
    clean_log = last_log.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    svg.append(f'    <text x="28" y="18" fill="#E2E8F0" class="neon-text" font-size="11.5">{clean_log}</text>')
    svg.append(f'    <text x="{width-64}" y="18" text-anchor="end" fill="#FF1493" class="neon-text" font-size="10.5">Auto-Commit 24h Active 🟢</text>')
    svg.append(f'  </g>')

    svg.append('</svg>')
    return "\n".join(svg)


def generate_readme_section(state):
    """Generate markdown block to embed into README.md."""
    last_log = state.get("recent_logs", ["Game active."])[0]
    score = state["score"]
    high_score = state.get("high_score", score)
    streak = state.get("day_streak", 1)
    level = state.get("level", 1)
    last_played = state.get("last_played", "Just now")

    section = f"""<!-- DAILY-GAME:START -->
### 🕹️ Neon Cyber Pac-Man: Contribution Grid Edition
<p align="left">
  <em>An autonomous retro arcade simulation running directly on GitHub! Every <b>24 hours</b>, the AI engine uses <b>BFS Graph Pathfinding</b> to compute the next turns, eat energy pellets, evade cyber-ghosts, and push an automated commit to keep my contribution graph glowing green. 🟢⚡</em>
</p>

<p align="center">
  <img src="./assets/game-board.svg" width="100%" alt="Neon Cyber Pac-Man Board" />
</p>

<div align="center">

| 🏆 High Score | ⭐ Current Score | ⚡ Level | 🔥 Active Streak | 🕒 Last Cycle (UTC) |
| :---: | :---: | :---: | :---: | :---: |
| **`{high_score:05d}`** | **`{score:05d}`** | **Stage {level}** | **{streak} Days** | `{last_played}` |

<br/>

<a href="https://github.com/afifasyed123/afifasyed123/actions/workflows/daily_game.yml">
  <img src="https://img.shields.io/badge/GitHub%20Actions-Run%20Manual%20Turn-FF1493?style=for-the-badge&logo=githubactions&logoColor=white" alt="Run Manual Turn" />
</a>
&nbsp;&nbsp;
<a href="https://github.com/afifasyed123/afifasyed123/blob/main/data/game_state.json">
  <img src="https://img.shields.io/badge/Telemetry-game__state.json-00F5D4?style=for-the-badge&logo=json&logoColor=black" alt="View State" />
</a>
&nbsp;&nbsp;
<a href="https://github.com/afifasyed123/afifasyed123/blob/main/scripts/game_engine.py">
  <img src="https://img.shields.io/badge/Engine-Python%20BFS%20AI-7928CA?style=for-the-badge&logo=python&logoColor=white" alt="Engine Code" />
</a>

</div>

<br/>

> **🤖 Latest Turn Telemetry:** `{last_log}`  
> **🎮 Game Rules:** Pac-Man moves across a cyber grid powered by Breadth-First Search pathfinding. Eating regular pellets (`.`) rewards `10 pts`, energizers (`*`) reward `50 pts` and trigger frightened ghost mode (`+200 pts`), and cherries (`🍒`) reward `100 pts`. Clearing the entire grid triggers **Level Progression** with bonus score!

<!-- DAILY-GAME:END -->"""
    return section


def update_readme(state):
    """Insert or update the daily game section in README.md."""
    if not os.path.exists(README_PATH):
        print(f"Error: {README_PATH} not found.")
        return

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    new_section = generate_readme_section(state)
    start_tag = "<!-- DAILY-GAME:START -->"
    end_tag = "<!-- DAILY-GAME:END -->"

    if start_tag in content and end_tag in content:
        # Replace existing section
        before = content.split(start_tag)[0]
        after = content.split(end_tag)[1]
        updated_content = before + new_section + after
    else:
        # Insert before "## 💖 Show Some Love!" or at the bottom
        insert_marker = "## 💖 **Show Some Love!**"
        if insert_marker in content:
            updated_content = content.replace(insert_marker, f"{new_section}\n\n---\n\n{insert_marker}")
        else:
            updated_content = content + f"\n\n---\n\n{new_section}\n"

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated_content)
    print("README.md updated successfully!")


def main():
    steps = 7
    if "--steps" in sys.argv:
        try:
            idx = sys.argv.index("--steps")
            steps = int(sys.argv[idx + 1])
        except Exception:
            steps = 7

    if "--reset" in sys.argv:
        print("Resetting game state to initial Level 1...")
        state = create_initial_state()
    else:
        print("Loading game state...")
        state = load_state()

    print(f"Simulating daily turn ({steps} steps)...")
    state = simulate_turn(state, steps=steps)

    print("Saving updated game state...")
    save_state(state)

    print("Rendering SVG board...")
    os.makedirs(ASSETS_DIR, exist_ok=True)
    svg_content = render_svg(state)
    with open(BOARD_SVG_PATH, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"SVG board written to {BOARD_SVG_PATH}")

    print("Updating README.md...")
    update_readme(state)

    print("Done! Game turn successfully executed.")


if __name__ == "__main__":
    main()
