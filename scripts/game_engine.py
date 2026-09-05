#!/usr/bin/env python3
"""
Neon Arcade: Autonomous Cyber Pac-Man
Real-time animated retro arcade simulation for GitHub Profile README.
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
    """Build fresh initial state for Stage 1."""
    maze = [list(row) for row in DEFAULT_MAZE]
    maze[4][10] = 'C'

    return {
        "level": 1,
        "score": 140,
        "high_score": 1280,
        "streak": 1,
        "last_played": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
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
            "🎮 Pac-Man executing autonomous patrol across Sector Alpha.",
            "⚡ AI BFS pathfinding tracking active pellets & power energizers."
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
    """Simulate round progression."""
    maze = [list(row) for row in state["maze"]]
    pac = state["pacman"]
    ghosts = state["ghosts"]
    frightened_timer = state.get("frightened_timer", 0)

    turn_pellets_eaten = 0
    turn_points = 0
    step_events = []

    remaining_pellets = sum(row.count('.') + row.count('*') + row.count('C') for row in maze)
    if remaining_pellets < 15:
        state["level"] = state.get("level", 1) + 1
        level_bonus = 500 * state["level"]
        state["score"] = state.get("score", 0) + level_bonus
        fresh = create_initial_state()
        maze = [list(row) for row in fresh["maze"]]
        pac["x"], pac["y"] = fresh["pacman"]["x"], fresh["pacman"]["y"]
        step_events.append(f"🏆 Sector Cleared! Stage {state['level']} Unlocked (+{level_bonus} bonus pts)!")

    for _ in range(steps):
        targets = []
        for y, row in enumerate(maze):
            for x, ch in enumerate(row):
                if ch in ('.', '*', 'C'):
                    targets.append((x, y))

        path = bfs_find_path(maze, (pac["x"], pac["y"]), targets)
        if path and len(path) > 0:
            next_dir, next_x, next_y = path[0]
            pac["dir"] = next_dir
            pac["x"] = next_x
            pac["y"] = next_y

        cell_item = maze[pac["y"]][pac["x"]]
        if cell_item == '.':
            maze[pac["y"]][pac["x"]] = ' '
            state["score"] = state.get("score", 0) + 10
            turn_points += 10
            turn_pellets_eaten += 1
        elif cell_item == '*':
            maze[pac["y"]][pac["x"]] = ' '
            state["score"] = state.get("score", 0) + 50
            turn_points += 50
            frightened_timer = 12
            for g in ghosts:
                g["frightened"] = True
            step_events.append("🌟 Power Energizer activated! Cyber-Ghosts dispersed!")
        elif cell_item == 'C':
            maze[pac["y"]][pac["x"]] = ' '
            state["score"] = state.get("score", 0) + 100
            turn_points += 100
            step_events.append("🍒 Cyber Cherry collected (+100 pts)!")

    if state["score"] > state.get("high_score", 0):
        state["high_score"] = state["score"]

    state["frightened_timer"] = frightened_timer
    state["maze"] = ["".join(row) for row in maze]
    state["streak"] = state.get("streak", 1) + 1
    state["last_played"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    summary = (
        f"Round {state['streak']}: 🤖 AI Agent navigated Sector {state.get('level', 1)} | "
        f"Collected {turn_pellets_eaten} pellets (+{turn_points} pts). Score: {state['score']}."
    )

    new_logs = [summary] + step_events + state.get("recent_logs", [])
    state["recent_logs"] = new_logs[:5]

    return state


def render_animated_svg(state):
    """Render a fully animated Retro Arcade Cyber Pac-Man SVG."""
    width = 860
    height = 470
    cols = len(state["maze"][0])
    rows = len(state["maze"])

    tile_w = 36
    tile_h = 28
    maze_ox = (width - (cols * tile_w)) // 2
    maze_oy = 92

    score = state.get("score", 140)
    high_score = state.get("high_score", 1280)
    level = state.get("level", 1)
    streak = state.get("streak", 1)
    last_log = state.get("recent_logs", ["Game active."])[0]

    # Clean text for XML
    clean_log = last_log.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="auto">')

    # Styles & Animations
    svg.append("""
  <defs>
    <!-- Background Gradient -->
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#080712" />
      <stop offset="50%" stop-color="#100C22" />
      <stop offset="100%" stop-color="#070612" />
    </linearGradient>

    <!-- Neon Cyber Border Gradient -->
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

    <!-- Neon Filters -->
    <filter id="neonGlow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="3.5" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <filter id="softGlow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="1.8" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <!-- Background Grid Pattern -->
    <pattern id="cyberGrid" width="20" height="20" patternUnits="userSpaceOnUse">
      <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#FFFFFF" stroke-width="0.3" stroke-opacity="0.05" />
    </pattern>
  </defs>

  <style>
    .arcade-font { font-family: 'Courier New', Courier, monospace, system-ui; font-weight: 800; letter-spacing: 1px; }
    .hud-text { font-family: system-ui, -apple-system, sans-serif; font-weight: 700; }
    
    @keyframes blink {
      0%, 49% { opacity: 1; }
      50%, 100% { opacity: 0.2; }
    }
    .blinking-1up {
      animation: blink 1s infinite;
    }
    
    @keyframes pulseGlow {
      0%, 100% { r: 6px; opacity: 0.8; }
      50% { r: 8px; opacity: 1; }
    }
    .pulsing-pellet {
      animation: pulseGlow 1.4s infinite ease-in-out;
    }
  </style>
""")

    # Main Card Body
    svg.append(f'  <!-- Card Frame -->')
    svg.append(f'  <rect x="2" y="2" width="{width-4}" height="{height-4}" rx="18" fill="url(#bgGrad)" stroke="url(#borderGrad)" stroke-width="2.5" />')
    svg.append(f'  <rect x="2" y="2" width="{width-4}" height="{height-4}" rx="18" fill="url(#cyberGrid)" />')

    # Top HUD Bar
    svg.append(f'  <!-- Header Section -->')
    svg.append(f'  <g transform="translate(25, 24)">')
    
    # 1UP Blinking Retro Arcade Indicator & Title
    svg.append(f'    <text x="0" y="16" fill="#FF0055" class="arcade-font blinking-1up" font-size="13">1UP</text>')
    svg.append(f'    <text x="0" y="36" fill="#FF1493" class="arcade-font" font-size="20" filter="url(#softGlow)">🕹️ NEON CYBER PAC-MAN</text>')
    svg.append(f'    <text x="0" y="52" fill="#8E8BA7" class="hud-text" font-size="11.5">Autonomous Retro Arcade • Real-Time AI Simulation</text>')

    # Stats Badges
    hud_x = width - 50
    # Streak Badge
    svg.append(f'    <rect x="{hud_x-465}" y="8" width="105" height="38" rx="8" fill="#FF1493" fill-opacity="0.15" stroke="#FF1493" stroke-width="1.2"/>')
    svg.append(f'    <text x="{hud_x-412}" y="24" text-anchor="middle" fill="#FF69B4" class="hud-text" font-size="10">ROUND</text>')
    svg.append(f'    <text x="{hud_x-412}" y="39" text-anchor="middle" fill="#FFFFFF" class="arcade-font" font-size="14">🔥 #{streak}</text>')

    # Level Badge
    svg.append(f'    <rect x="{hud_x-348}" y="8" width="95" height="38" rx="8" fill="#7928CA" fill-opacity="0.2" stroke="#7928CA" stroke-width="1.2"/>')
    svg.append(f'    <text x="{hud_x-300}" y="24" text-anchor="middle" fill="#B794F4" class="hud-text" font-size="10">STAGE</text>')
    svg.append(f'    <text x="{hud_x-300}" y="39" text-anchor="middle" fill="#00F5D4" class="arcade-font" font-size="14">LVL {level}</text>')

    # Score Badge
    svg.append(f'    <rect x="{hud_x-240}" y="8" width="115" height="38" rx="8" fill="#00F5D4" fill-opacity="0.15" stroke="#00F5D4" stroke-width="1.2"/>')
    svg.append(f'    <text x="{hud_x-182}" y="24" text-anchor="middle" fill="#00F5D4" class="hud-text" font-size="10">SCORE</text>')
    svg.append(f'    <text x="{hud_x-182}" y="39" text-anchor="middle" fill="#FFE600" class="arcade-font" font-size="14">{score:05d}</text>')

    # High Score Badge
    svg.append(f'    <rect x="{hud_x-112}" y="8" width="115" height="38" rx="8" fill="#FFE600" fill-opacity="0.15" stroke="#FFE600" stroke-width="1.2"/>')
    svg.append(f'    <text x="{hud_x-55}" y="24" text-anchor="middle" fill="#FFE600" class="hud-text" font-size="10">HIGH SCORE</text>')
    svg.append(f'    <text x="{hud_x-55}" y="39" text-anchor="middle" fill="#FFFFFF" class="arcade-font" font-size="14">🏆 {high_score:05d}</text>')

    svg.append(f'  </g>')

    # Maze Container
    svg.append(f'  <!-- Maze Container -->')
    svg.append(f'  <g transform="translate({maze_ox}, {maze_oy})">')

    maze_w = cols * tile_w
    maze_h = rows * tile_h
    svg.append(f'    <rect x="-6" y="-6" width="{maze_w+12}" height="{maze_h+12}" rx="12" fill="#05040B" stroke="#251B40" stroke-width="2" />')

    # Draw Walls and Static/Pulsing Elements
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
                # Power Energizer Pellet with animation
                svg.append(f'    <circle cx="{cx}" cy="{cy}" r="6.5" fill="#FF1493" class="pulsing-pellet" filter="url(#neonGlow)">')
                svg.append(f'      <animate attributeName="r" values="5.5; 8; 5.5" dur="1.2s" repeatCount="indefinite" />')
                svg.append(f'      <animate attributeName="opacity" values="0.75; 1; 0.75" dur="1.2s" repeatCount="indefinite" />')
                svg.append(f'    </circle>')
                svg.append(f'    <circle cx="{cx}" cy="{cy}" r="2.8" fill="#FFFFFF" opacity="0.9" />')
            elif cell == 'C':
                # Animated Floating Cherry Bonus
                svg.append(f'    <g transform="translate({cx-8}, {cy-8})">')
                svg.append(f'      <animateTransform attributeName="transform" type="translate" values="{cx-8},{cy-10}; {cx-8},{cy-6}; {cx-8},{cy-10}" dur="2s" repeatCount="indefinite" />')
                svg.append(f'      <circle cx="5" cy="11" r="4.5" fill="#FF0055" />')
                svg.append(f'      <circle cx="11" cy="11" r="4.5" fill="#FF0055" />')
                svg.append(f'      <path d="M 5 7 Q 8 2 11 7" fill="none" stroke="#00F5D4" stroke-width="1.5" />')
                svg.append(f'      <path d="M 8 2 L 12 1" fill="none" stroke="#00F5D4" stroke-width="1.5" />')
                svg.append(f'    </g>')

    # Center Ghost House Door
    gh_x = 9 * tile_w + 3
    gh_y = 5 * tile_h + 3
    svg.append(f'    <rect x="{gh_x}" y="{gh_y}" width="{tile_w*3-6}" height="{tile_h-6}" rx="4" fill="#0A0618" stroke="#FF1493" stroke-dasharray="4,4" stroke-width="1" opacity="0.6"/>')

    # =========================================================================
    # ANIMATED ACTORS: REAL-TIME MOVING PAC-MAN & GHOSTS
    # =========================================================================

    # Main patrol path through the maze:
    # Starts at bottom-left (54, 266) -> right to (342, 266) -> up to (342, 182) ->
    # right past center (414, 182) -> down to (414, 266) -> right to (702, 266) ->
    # up to (702, 126) -> left to (558, 126) -> up to (558, 42) ->
    # left to (198, 42) -> down to (198, 126) -> left to (54, 126) -> down back to (54, 266).
    main_patrol_path = "M 54,266 L 342,266 L 342,182 L 414,182 L 414,266 L 702,266 L 702,126 L 558,126 L 558,42 L 198,42 L 198,126 L 54,126 Z"

    # Ghost 1: Blinky (Red) chases Pac-Man on the patrol route, offset behind
    svg.append(f'    <!-- Animated Ghost: Blinky (Red) -->')
    svg.append(f'    <g>')
    svg.append(f'      <animateMotion path="{main_patrol_path}" dur="16s" begin="-2.2s" repeatCount="indefinite" rotate="none" />')
    svg.append(f'      <g transform="translate(-11, -11)" filter="url(#softGlow)">')
    svg.append(f'        <!-- Fluttering Tentacles -->')
    svg.append(f'        <path fill="#FF0055">')
    svg.append(f'          <animate attributeName="d"')
    svg.append(f'            values="M 1 10 C 1 3 21 3 21 10 L 21 18 L 18 15 L 14 18 L 11 15 L 7 18 L 4 15 L 1 18 Z;')
    svg.append(f'                    M 1 10 C 1 3 21 3 21 10 L 21 16 L 18 19 L 14 16 L 11 19 L 7 16 L 4 19 L 1 16 Z;')
    svg.append(f'                    M 1 10 C 1 3 21 3 21 10 L 21 18 L 18 15 L 14 18 L 11 15 L 7 18 L 4 15 L 1 18 Z"')
    svg.append(f'            dur="0.35s" repeatCount="indefinite" />')
    svg.append(f'        </path>')
    svg.append(f'        <!-- Eyes -->')
    svg.append(f'        <ellipse cx="7" cy="8" rx="2.8" ry="3.5" fill="#FFFFFF" />')
    svg.append(f'        <ellipse cx="15" cy="8" rx="2.8" ry="3.5" fill="#FFFFFF" />')
    svg.append(f'        <circle cx="8" cy="8" r="1.5" fill="#0B0D19" />')
    svg.append(f'        <circle cx="16" cy="8" r="1.5" fill="#0B0D19" />')
    svg.append(f'      </g>')
    svg.append(f'    </g>')

    # Ghost 2: Pinky (Pink) patrols top-center circuit
    pinky_loop = "M 198,42 L 558,42 L 558,126 L 198,126 Z"
    svg.append(f'    <!-- Animated Ghost: Pinky (Pink) -->')
    svg.append(f'    <g>')
    svg.append(f'      <animateMotion path="{pinky_loop}" dur="9s" repeatCount="indefinite" rotate="none" />')
    svg.append(f'      <g transform="translate(-11, -11)" filter="url(#softGlow)">')
    svg.append(f'        <path fill="#FF1493">')
    svg.append(f'          <animate attributeName="d"')
    svg.append(f'            values="M 1 10 C 1 3 21 3 21 10 L 21 18 L 18 15 L 14 18 L 11 15 L 7 18 L 4 15 L 1 18 Z;')
    svg.append(f'                    M 1 10 C 1 3 21 3 21 10 L 21 16 L 18 19 L 14 16 L 11 19 L 7 16 L 4 19 L 1 16 Z;')
    svg.append(f'                    M 1 10 C 1 3 21 3 21 10 L 21 18 L 18 15 L 14 18 L 11 15 L 7 18 L 4 15 L 1 18 Z"')
    svg.append(f'            dur="0.35s" repeatCount="indefinite" />')
    svg.append(f'        </path>')
    svg.append(f'        <ellipse cx="7" cy="8" rx="2.8" ry="3.5" fill="#FFFFFF" />')
    svg.append(f'        <ellipse cx="15" cy="8" rx="2.8" ry="3.5" fill="#FFFFFF" />')
    svg.append(f'        <circle cx="6" cy="8" r="1.5" fill="#0B0D19" />')
    svg.append(f'        <circle cx="14" cy="8" r="1.5" fill="#0B0D19" />')
    svg.append(f'      </g>')
    svg.append(f'    </g>')

    # Ghost 3: Inky (Cyan) patrols right perimeter
    inky_loop = "M 702,42 L 702,266 L 558,266 L 558,182 L 702,182 Z"
    svg.append(f'    <!-- Animated Ghost: Inky (Cyan) -->')
    svg.append(f'    <g>')
    svg.append(f'      <animateMotion path="{inky_loop}" dur="11s" repeatCount="indefinite" rotate="none" />')
    svg.append(f'      <g transform="translate(-11, -11)" filter="url(#softGlow)">')
    svg.append(f'        <path fill="#00F5D4">')
    svg.append(f'          <animate attributeName="d"')
    svg.append(f'            values="M 1 10 C 1 3 21 3 21 10 L 21 18 L 18 15 L 14 18 L 11 15 L 7 18 L 4 15 L 1 18 Z;')
    svg.append(f'                    M 1 10 C 1 3 21 3 21 10 L 21 16 L 18 19 L 14 16 L 11 19 L 7 16 L 4 19 L 1 16 Z;')
    svg.append(f'                    M 1 10 C 1 3 21 3 21 10 L 21 18 L 18 15 L 14 18 L 11 15 L 7 18 L 4 15 L 1 18 Z"')
    svg.append(f'            dur="0.35s" repeatCount="indefinite" />')
    svg.append(f'        </path>')
    svg.append(f'        <ellipse cx="7" cy="8" rx="2.8" ry="3.5" fill="#FFFFFF" />')
    svg.append(f'        <ellipse cx="15" cy="8" rx="2.8" ry="3.5" fill="#FFFFFF" />')
    svg.append(f'        <circle cx="7" cy="9" r="1.5" fill="#0B0D19" />')
    svg.append(f'        <circle cx="15" cy="9" r="1.5" fill="#0B0D19" />')
    svg.append(f'      </g>')
    svg.append(f'    </g>')

    # Ghost 4: Clyde (Orange) patrols bottom-left corner
    clyde_loop = "M 54,126 L 342,126 L 342,266 L 54,266 Z"
    svg.append(f'    <!-- Animated Ghost: Clyde (Orange) -->')
    svg.append(f'    <g>')
    svg.append(f'      <animateMotion path="{clyde_loop}" dur="12s" begin="-4s" repeatCount="indefinite" rotate="none" />')
    svg.append(f'      <g transform="translate(-11, -11)" filter="url(#softGlow)">')
    svg.append(f'        <path fill="#FFAA00">')
    svg.append(f'          <animate attributeName="d"')
    svg.append(f'            values="M 1 10 C 1 3 21 3 21 10 L 21 18 L 18 15 L 14 18 L 11 15 L 7 18 L 4 15 L 1 18 Z;')
    svg.append(f'                    M 1 10 C 1 3 21 3 21 10 L 21 16 L 18 19 L 14 16 L 11 19 L 7 16 L 4 19 L 1 16 Z;')
    svg.append(f'                    M 1 10 C 1 3 21 3 21 10 L 21 18 L 18 15 L 14 18 L 11 15 L 7 18 L 4 15 L 1 18 Z"')
    svg.append(f'            dur="0.35s" repeatCount="indefinite" />')
    svg.append(f'        </path>')
    svg.append(f'        <ellipse cx="7" cy="8" rx="2.8" ry="3.5" fill="#FFFFFF" />')
    svg.append(f'        <ellipse cx="15" cy="8" rx="2.8" ry="3.5" fill="#FFFFFF" />')
    svg.append(f'        <circle cx="8" cy="7" r="1.5" fill="#0B0D19" />')
    svg.append(f'        <circle cx="16" cy="7" r="1.5" fill="#0B0D19" />')
    svg.append(f'      </g>')
    svg.append(f'    </g>')

    # ACTIVE MOVING PAC-MAN WITH 60FPS MOUTH CHOMPING & AUTO-ROTATION
    svg.append(f'    <!-- Animated Hero: Pac-Man (Chomping & Traversing Maze) -->')
    svg.append(f'    <g id="animated-pacman">')
    # rotate="auto" automatically points Pac-Man in the direction of the corridor!
    svg.append(f'      <animateMotion path="{main_patrol_path}" dur="16s" repeatCount="indefinite" rotate="auto" />')
    svg.append(f'      <g filter="url(#neonGlow)">')
    # Upper Jaw chomping
    svg.append(f'        <path d="M 0 0 L 13 0 A 13 13 0 0 0 -13 0 Z" fill="#FFE600">')
    svg.append(f'          <animateTransform attributeName="transform" type="rotate" values="0; -32; 0" dur="0.25s" repeatCount="indefinite" />')
    svg.append(f'        </path>')
    # Lower Jaw chomping
    svg.append(f'        <path d="M 0 0 L 13 0 A 13 13 0 0 1 -13 0 Z" fill="#FFE600">')
    svg.append(f'          <animateTransform attributeName="transform" type="rotate" values="0; 32; 0" dur="0.25s" repeatCount="indefinite" />')
    svg.append(f'        </path>')
    # Eye tracking
    svg.append(f'        <circle cx="2" cy="-6" r="1.5" fill="#0B0D19">')
    svg.append(f'          <animateTransform attributeName="transform" type="rotate" values="0; -32; 0" dur="0.25s" repeatCount="indefinite" />')
    svg.append(f'        </circle>')
    svg.append(f'      </g>')
    svg.append(f'    </g>')

    svg.append(f'  </g>')

    # Bottom Ticker Section (Clean, Discreet, Arcade Themed)
    svg.append(f'  <!-- Footer Ticker -->')
    svg.append(f'  <g transform="translate(25, {height-38})">')
    svg.append(f'    <rect x="0" y="0" width="{width-50}" height="28" rx="8" fill="#120D26" stroke="#3D2963" stroke-width="1" />')
    svg.append(f'    <circle cx="14" cy="14" r="4.5" fill="#00F5D4" filter="url(#softGlow)" />')
    svg.append(f'    <text x="28" y="18" fill="#E2E8F0" class="hud-text" font-size="11.5">{clean_log}</text>')
    svg.append(f'    <text x="{width-64}" y="18" text-anchor="end" fill="#FF1493" class="hud-text" font-size="10.5">Simulation: Active 🟢</text>')
    svg.append(f'  </g>')

    svg.append('</svg>')
    return "\n".join(svg)


def generate_readme_section(state):
    """Generate clean, stylish markdown block to embed into README.md."""
    last_log = state.get("recent_logs", ["Game active."])[0]
    score = state.get("score", 140)
    high_score = state.get("high_score", 1280)
    streak = state.get("streak", 1)
    level = state.get("level", 1)
    last_played = state.get("last_played", "Just now")

    section = f"""<!-- DAILY-GAME:START -->
### 🕹️ Neon Arcade: Cyber Pac-Man Bot
<p align="left">
  <em>An autonomous retro arcade agent exploring a neon cyber grid in real time. Powered by AI search algorithms, the agent hunts power pellets, clears sectors, and outsmarts cyber ghosts. 👾⚡</em>
</p>

<p align="center">
  <img src="./assets/game-board.svg" width="100%" alt="Neon Cyber Pac-Man Board" />
</p>

<div align="center">

| 🏆 High Score | ⭐ Current Score | ⚡ Stage | 🎯 Round | 🕒 Last Updated |
| :---: | :---: | :---: | :---: | :---: |
| **`{high_score:05d}`** | **`{score:05d}`** | **Stage {level}** | **Round #{streak}** | `{last_played}` |

<br/>

<a href="https://github.com/afifasyed123/afifasyed123/actions/workflows/daily_game.yml">
  <img src="https://img.shields.io/badge/Arcade%20Engine-Simulate%20Turn-FF1493?style=for-the-badge&logo=retroarch&logoColor=white" alt="Simulate Turn" />
</a>
&nbsp;&nbsp;
<a href="https://github.com/afifasyed123/afifasyed123/blob/main/data/game_state.json">
  <img src="https://img.shields.io/badge/Telemetry-game__state.json-00F5D4?style=for-the-badge&logo=json&logoColor=black" alt="View State" />
</a>
&nbsp;&nbsp;
<a href="https://github.com/afifasyed123/afifasyed123/blob/main/scripts/game_engine.py">
  <img src="https://img.shields.io/badge/AI%20Core-Python%20BFS-7928CA?style=for-the-badge&logo=python&logoColor=white" alt="Engine Code" />
</a>

</div>

<br/>

> **🤖 Latest Turn Telemetry:** `{last_log}`  
> **🎮 Game Rules:** The agent navigates the cyber grid seeking pellets (`.`) for `10 pts`, energizers (`*`) for `50 pts` which activate frightened ghost mode (`+200 pts`), and cherries (`🍒`) for `100 pts`. Clearing a sector advances to the next stage!

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
        before = content.split(start_tag)[0]
        after = content.split(end_tag)[1]
        updated_content = before + new_section + after
    else:
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
        print("Resetting game state to initial Stage 1...")
        state = create_initial_state()
    else:
        print("Loading game state...")
        state = load_state()

    print(f"Simulating turn ({steps} steps)...")
    state = simulate_turn(state, steps=steps)

    print("Saving updated game state...")
    save_state(state)

    print("Rendering animated SVG board...")
    os.makedirs(ASSETS_DIR, exist_ok=True)
    svg_content = render_animated_svg(state)
    with open(BOARD_SVG_PATH, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"Animated SVG board written to {BOARD_SVG_PATH}")

    print("Updating README.md...")
    update_readme(state)

    print("Done! Game turn successfully executed.")


if __name__ == "__main__":
    main()
