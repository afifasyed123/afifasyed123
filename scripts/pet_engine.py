#!/usr/bin/env python3
"""
Barbiecore Virtual Pet Engine for GitHub Profile README
Pet: Bella the Glam Poodle 🐩🎀
Authored for: afifasyed123
"""

import os
import sys
import json
import random
from datetime import datetime, timezone

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
README_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "README.md")
STATE_PATH = os.path.join(DATA_DIR, "pet_state.json")
PET_SVG_PATH = os.path.join(ASSETS_DIR, "pet-card.svg")
COMMENT_OUTPUT_PATH = os.path.join(DATA_DIR, "last_comment.md")

USERNAME = "afifasyed123"

ACTIONS = {
    "bath": {
        "title": "Bubble Bath 🛁",
        "delta": {"glamour": 25, "happiness": 10},
        "verb": "gave Bella a luxurious warm bubble bath with strawberry scented soap! 🛁🫧💖",
        "icon": "🛁"
    },
    "feed": {
        "title": "Give Macaron 🧁",
        "delta": {"snacks": 30, "energy": 5},
        "verb": "fed Bella a sweet raspberry macaron sprinkled with edible glitter! 🧁✨",
        "icon": "🧁"
    },
    "shop": {
        "title": "Go Shopping 🛍️",
        "delta": {"happiness": 25, "glamour": 20, "energy": -10},
        "verb": "took Bella on a high-fashion Barbiecore shopping spree at the mall! 🛍️👠💄",
        "icon": "🛍️"
    },
    "sleep": {
        "title": "Beauty Sleep 💤",
        "delta": {"energy": 35, "snacks": -5},
        "verb": "tucked Bella into her silk pink canopy bed for royal beauty sleep! 💤👑🌸",
        "icon": "💤"
    }
}


def load_state():
    """Load pet state or return default."""
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to parse {STATE_PATH}: {e}")

    return {
        "name": "Bella",
        "pet_type": "Glam Poodle 🐩",
        "stats": {
            "glamour": 90,
            "energy": 85,
            "happiness": 95,
            "snacks": 80
        },
        "mood": "Living her absolute best Barbie life! 💅💖✨",
        "last_action": "Initial Arrival",
        "last_caretaker": USERNAME,
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "total_interactions": 1,
        "recent_interactions": []
    }


def save_state(state):
    """Save state to JSON."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def clamp(val, low=0, high=100):
    return max(low, min(high, val))


def compute_mood(stats):
    """Determine cute Barbiecore mood based on stats."""
    g = stats["glamour"]
    e = stats["energy"]
    h = stats["happiness"]
    s = stats["snacks"]
    avg = (g + e + h + s) / 4.0

    if e <= 20:
        return "Taking a beauty nap, do not disturb! 💤👑"
    if s <= 20:
        return "Craving sweet strawberry macarons ASAP! 🧁🥺"
    if g <= 20:
        return "Fashion emergency! Needs styling immediately! 💄👠"
    if h <= 25:
        return "Pouting... Needs hugs and shopping right now! 🛍️💔"

    if avg >= 85:
        return "Living her absolute best Barbie life! 💅💖✨"
    if avg >= 70:
        return "Serving pure glam, sparkles & sweetness! 🎀✨"
    if avg >= 50:
        return "Feeling cute, might go shopping later! 🛍️🧁"
    if avg >= 30:
        return "Drama queen alert! Needs pampering ASAP 🛍️"
    return "Exhausted beauty queen... send macarons & bubble baths! 🥺🛁"


def apply_action(state, action_key, user):
    """Apply an interaction action from user."""
    action_key = action_key.lower().strip()
    if action_key.startswith("pet:"):
        action_key = action_key[4:].strip()

    if action_key not in ACTIONS:
        # Fallback check substrings
        matched = None
        for k in ACTIONS:
            if k in action_key:
                matched = k
                break
        action_key = matched if matched else "bath"

    config = ACTIONS[action_key]
    stats = state["stats"]

    for stat, delta in config["delta"].items():
        stats[stat] = clamp(stats.get(stat, 50) + delta)

    state["mood"] = compute_mood(stats)
    state["last_action"] = config["title"]
    state["last_caretaker"] = user if user else USERNAME
    state["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    state["total_interactions"] = state.get("total_interactions", 0) + 1

    interaction_entry = {
        "user": state["last_caretaker"],
        "action": config["title"],
        "timestamp": state["last_updated"]
    }
    history = state.get("recent_interactions", [])
    state["recent_interactions"] = [interaction_entry] + history[:4]

    # Generate thank-you comment for GitHub issue
    comment_text = (
        f"### 🎀 Ooh la la! Thank you @{state['last_caretaker']}! ✨\n\n"
        f"You {config['verb']}\n\n"
        f"**Bella's New Stats:**\n"
        f"- 💖 **Glamour:** {stats['glamour']}%\n"
        f"- ⚡ **Energy:** {stats['energy']}%\n"
        f"- ✨ **Happiness:** {stats['happiness']}%\n"
        f"- 🧁 **Snacks:** {stats['snacks']}%\n\n"
        f"> *\"{state['mood']}\"* 💅🌸\n\n"
        f"Check her live status on the [Profile README](https://github.com/{USERNAME}/{USERNAME})! 💕"
    )
    
    with open(COMMENT_OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(comment_text)

    return state, config


def apply_decay(state):
    """Hourly decay simulating time passing."""
    stats = state["stats"]
    decay_amounts = {
        "glamour": random.randint(3, 5),
        "energy": random.randint(3, 5),
        "happiness": random.randint(3, 5),
        "snacks": random.randint(3, 5)
    }

    for k in stats:
        stats[k] = clamp(stats[k] - decay_amounts[k])

    state["mood"] = compute_mood(stats)
    state["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return state


def render_svg(state):
    """Generate stunning Barbiecore SVG card."""
    width = 860
    height = 420
    stats = state["stats"]
    mood = state["mood"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    caretaker = state.get("last_caretaker", USERNAME)
    total = state.get("total_interactions", 1)

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="auto">')
    
    # Defs & Gradients
    svg.append("""
  <defs>
    <!-- Background Barbie Gradient -->
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#21081A" />
      <stop offset="40%" stop-color="#3A0D2E" />
      <stop offset="80%" stop-color="#24071D" />
      <stop offset="100%" stop-color="#14020F" />
    </linearGradient>

    <!-- Border Hot Pink Gradient -->
    <linearGradient id="barbieBorder" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FF1493" />
      <stop offset="50%" stop-color="#FF69B4" />
      <stop offset="100%" stop-color="#FFD700" />
    </linearGradient>

    <!-- Meter Gradients -->
    <linearGradient id="glamourGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#FF1493" />
      <stop offset="100%" stop-color="#FF69B4" />
    </linearGradient>

    <linearGradient id="energyGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#FF007F" />
      <stop offset="100%" stop-color="#FFAA00" />
    </linearGradient>

    <linearGradient id="happinessGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#FF69B4" />
      <stop offset="100%" stop-color="#00F5D4" />
    </linearGradient>

    <linearGradient id="snacksGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#7928CA" />
      <stop offset="100%" stop-color="#FF1493" />
    </linearGradient>

    <!-- Glow Filter -->
    <filter id="pinkGlow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <filter id="softGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="1.5" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <!-- Sparkle Pattern -->
    <pattern id="sparkleGrid" width="30" height="30" patternUnits="userSpaceOnUse">
      <circle cx="15" cy="15" r="0.8" fill="#FFB6C1" opacity="0.25" />
    </pattern>
  </defs>

  <style>
    .barbie-title { font-family: system-ui, -apple-system, sans-serif; font-weight: 800; letter-spacing: 1px; }
    .barbie-font { font-family: system-ui, -apple-system, sans-serif; font-weight: 700; }
    .body-font { font-family: system-ui, -apple-system, sans-serif; font-weight: 600; }
    
    @keyframes sparkleRotate {
      0% { transform: rotate(0deg) scale(0.85); opacity: 0.7; }
      50% { transform: rotate(180deg) scale(1.15); opacity: 1; }
      100% { transform: rotate(360deg) scale(0.85); opacity: 0.7; }
    }
    .sparkle-icon {
      transform-origin: center;
      animation: sparkleRotate 4s infinite linear;
    }

    @keyframes earBob {
      0%, 100% { transform: translateY(0px); }
      50% { transform: translateY(-3px); }
    }
    .bouncing-pet {
      animation: earBob 2.5s infinite ease-in-out;
    }
  </style>
""")

    # Main Card Base
    svg.append(f'  <!-- Card Background -->')
    svg.append(f'  <rect x="2" y="2" width="{width-4}" height="{height-4}" rx="22" fill="url(#bgGrad)" stroke="url(#barbieBorder)" stroke-width="2.5" />')
    svg.append(f'  <rect x="2" y="2" width="{width-4}" height="{height-4}" rx="22" fill="url(#sparkleGrid)" />')

    # Header
    svg.append(f'  <!-- Header -->')
    svg.append(f'  <g transform="translate(30, 24)">')
    svg.append(f'    <text x="0" y="22" fill="#FF69B4" class="barbie-title" font-size="22" filter="url(#softGlow)">🎀 BARBIE WORLD VIRTUAL PET</text>')
    svg.append(f'    <text x="0" y="44" fill="#FFB6C1" class="body-font" font-size="12">Interactive GitHub Profile Companion • Click buttons below to interact!</text>')
    
    # Top Badges
    svg.append(f'    <rect x="{width-310}" y="6" width="125" height="34" rx="10" fill="#FF1493" fill-opacity="0.2" stroke="#FF1493" stroke-width="1.2" />')
    svg.append(f'    <text x="{width-248}" y="28" text-anchor="middle" fill="#FF69B4" class="barbie-font" font-size="12">✨ TREATS: {total}</text>')

    svg.append(f'    <rect x="{width-175}" y="6" width="125" height="34" rx="10" fill="#FFD700" fill-opacity="0.15" stroke="#FFD700" stroke-width="1.2" />')
    svg.append(f'    <text x="{width-113}" y="28" text-anchor="middle" fill="#FFD700" class="barbie-font" font-size="12">💖 PAMPERED</text>')
    svg.append(f'  </g>')

    # Left Section: Bella The Glam Poodle Illustration
    svg.append(f'  <!-- Pet Portrait & Avatar Section -->')
    svg.append(f'  <g transform="translate(45, 90)">')
    
    # Portrait Frame Backdrop
    svg.append(f'    <rect x="0" y="0" width="230" height="240" rx="18" fill="#1C0617" stroke="#FF69B4" stroke-width="1.5" />')
    svg.append(f'    <circle cx="115" cy="115" r="95" fill="#FF1493" fill-opacity="0.08" />')

    # POODLE VECTOR ART
    svg.append(f'    <g class="bouncing-pet" transform="translate(115, 120)">')
    
    # Body & Chest Fluff
    svg.append(f'      <ellipse cx="0" cy="55" rx="42" ry="32" fill="#FF85C1" />')
    svg.append(f'      <ellipse cx="0" cy="45" rx="36" ry="24" fill="#FFB6D9" />')
    svg.append(f'      <circle cx="-20" cy="48" r="14" fill="#FF99CC" />')
    svg.append(f'      <circle cx="20" cy="48" r="14" fill="#FF99CC" />')
    svg.append(f'      <circle cx="0" cy="52" r="16" fill="#FFC2E2" />')

    # Sparkling Diamond Heart Collar
    svg.append(f'      <rect x="-24" y="24" width="48" height="7" rx="3.5" fill="#FF1493" />')
    svg.append(f'      <path d="M 0 35 L -7 28 A 4 4 0 0 1 -1 24 L 0 26 L 1 24 A 4 4 0 0 1 7 28 Z" fill="#FFD700" stroke="#FFFFFF" stroke-width="0.8" filter="url(#softGlow)" />')

    # Poodle Head
    svg.append(f'      <circle cx="0" cy="0" r="38" fill="#FFA3D0" />')
    # Cheeks / Face Muzzle
    svg.append(f'      <ellipse cx="0" cy="10" rx="22" ry="17" fill="#FFD1E8" />')

    # Cute Fluffy Poodle Ears (Puffs)
    svg.append(f'      <!-- Fluffy Left Ear -->')
    svg.append(f'      <g transform="translate(-36, -5)">')
    svg.append(f'        <circle cx="0" cy="0" r="18" fill="#FF69B4" />')
    svg.append(f'        <circle cx="-5" cy="12" r="14" fill="#FF85C1" />')
    svg.append(f'        <circle cx="2" cy="22" r="12" fill="#FF99CC" />')
    svg.append(f'      </g>')

    # Fluffy Right Ear
    svg.append(f'      <!-- Fluffy Right Ear -->')
    svg.append(f'      <g transform="translate(36, -5)">')
    svg.append(f'        <circle cx="0" cy="0" r="18" fill="#FF69B4" />')
    svg.append(f'        <circle cx="5" cy="12" r="14" fill="#FF85C1" />')
    svg.append(f'        <circle cx="-2" cy="22" r="12" fill="#FF99CC" />')
    svg.append(f'      </g>')

    # Head Puff (Topknot)
    svg.append(f'      <circle cx="0" cy="-35" r="22" fill="#FF85C1" />')
    svg.append(f'      <circle cx="-10" cy="-32" r="15" fill="#FFA3D0" />')
    svg.append(f'      <circle cx="10" cy="-32" r="15" fill="#FFA3D0" />')

    # Royal Golden Crown / Tiara
    svg.append(f'      <g transform="translate(0, -48)" filter="url(#softGlow)">')
    svg.append(f'        <path d="M -16 6 L -18 -4 L -9 0 L 0 -10 L 9 0 L 18 -4 L 16 6 Z" fill="#FFD700" stroke="#FFF" stroke-width="0.7" />')
    svg.append(f'        <circle cx="0" cy="-7" r="2.2" fill="#FF1493" />')
    svg.append(f'        <circle cx="-9" cy="2" r="1.8" fill="#00F5D4" />')
    svg.append(f'        <circle cx="9" cy="2" r="1.8" fill="#00F5D4" />')
    svg.append(f'      </g>')

    # Big Sparkling Anime Eyes
    svg.append(f'      <!-- Eyes -->')
    svg.append(f'      <ellipse cx="-13" cy="2" rx="7" ry="9" fill="#3D002E" />')
    svg.append(f'      <ellipse cx="13" cy="2" rx="7" ry="9" fill="#3D002E" />')
    svg.append(f'      <!-- Sparkle Iris -->')
    svg.append(f'      <circle cx="-13" cy="3" r="5.5" fill="#FF1493" />')
    svg.append(f'      <circle cx="13" cy="3" r="5.5" fill="#FF1493" />')
    # Big Eye Highlights
    svg.append(f'      <circle cx="-15" cy="-1" r="2.5" fill="#FFFFFF" />')
    svg.append(f'      <circle cx="11" cy="-1" r="2.5" fill="#FFFFFF" />')
    svg.append(f'      <circle cx="-11" cy="5" r="1.2" fill="#FFFFFF" />')
    svg.append(f'      <circle cx="15" cy="5" r="1.2" fill="#FFFFFF" />')

    # Cute Little Pink Nose & Smile
    svg.append(f'      <ellipse cx="0" cy="11" rx="4" ry="3" fill="#FF1493" />')
    svg.append(f'      <path d="M -5 16 Q 0 20 5 16" fill="none" stroke="#660040" stroke-width="1.6" stroke-linecap="round" />')

    # Pink Blush
    svg.append(f'      <ellipse cx="-20" cy="12" rx="6" ry="3.5" fill="#FF69B4" opacity="0.6" />')
    svg.append(f'      <ellipse cx="20" cy="12" rx="6" ry="3.5" fill="#FF69B4" opacity="0.6" />')

    svg.append(f'    </g>') # End Poodle Art

    # Pet Name Badge Under Art
    svg.append(f'    <text x="115" y="210" text-anchor="middle" fill="#FFFFFF" class="barbie-font" font-size="15">🐩 BELLA</text>')
    svg.append(f'    <text x="115" y="226" text-anchor="middle" fill="#FF69B4" class="body-font" font-size="11">Princess of Barbie World</text>')
    svg.append(f'  </g>')

    # Right Section: Dynamic Mood Bubble & 4 Progress Meters
    svg.append(f'  <!-- Right Section: Mood Bubble & Meters -->')
    svg.append(f'  <g transform="translate(305, 90)">')

    # Speech Bubble for Current Mood
    svg.append(f'    <!-- Mood Bubble -->')
    svg.append(f'    <rect x="0" y="0" width="510" height="42" rx="12" fill="#FF1493" fill-opacity="0.15" stroke="#FF69B4" stroke-width="1.4" />')
    svg.append(f'    <text x="16" y="26" fill="#FFF0F5" class="barbie-font" font-size="13">💬 "{mood}"</text>')

    # 4 Stat Meters
    meter_specs = [
        ("💖 Glamour", stats["glamour"], "url(#glamourGrad)", 62),
        ("⚡ Energy", stats["energy"], "url(#energyGrad)", 108),
        ("✨ Happiness", stats["happiness"], "url(#happinessGrad)", 154),
        ("🧁 Snacks", stats["snacks"], "url(#snacksGrad)", 200)
    ]

    meter_w = 410
    meter_h = 16

    for label, val, grad, ypos in meter_specs:
        fill_w = int((val / 100.0) * meter_w)
        svg.append(f'    <!-- Stat: {label} -->')
        svg.append(f'    <g transform="translate(0, {ypos})">')
        svg.append(f'      <text x="0" y="12" fill="#FFE4E1" class="barbie-font" font-size="13">{label}</text>')
        svg.append(f'      <text x="{meter_w+90}" y="12" text-anchor="end" fill="#FFD700" class="barbie-font" font-size="13">{val}%</text>')
        # Meter Background
        svg.append(f'      <rect x="0" y="20" width="{meter_w+90}" height="{meter_h}" rx="8" fill="#1A0717" stroke="#4A1038" stroke-width="1.2" />')
        # Filled Bar
        if fill_w > 0:
            svg.append(f'      <rect x="1" y="21" width="{max(fill_w+90*val//100, 10)}" height="{meter_h-2}" rx="7" fill="{grad}" filter="url(#softGlow)" />')
        svg.append(f'    </g>')

    svg.append(f'  </g>')

    # Bottom Footer Bar: Last Caretaker
    svg.append(f'  <!-- Footer Bar -->')
    svg.append(f'  <g transform="translate(30, {height-32})">')
    svg.append(f'    <rect x="0" y="0" width="{width-60}" height="24" rx="6" fill="#1C0617" stroke="#FF69B4" stroke-width="0.8" />')
    svg.append(f'    <text x="14" y="16" fill="#FFB6C1" class="body-font" font-size="11">👑 Last Pampered by: <tspan fill="#FF69B4" font-weight="700">@{caretaker}</tspan> with {state.get("last_action", "Love")} 💕</text>')
    svg.append(f'    <text x="{width-74}" y="16" text-anchor="end" fill="#FFD700" class="body-font" font-size="10.5">Barbiecore Companion Engine 🎀</text>')
    svg.append(f'  </g>')

    svg.append('</svg>')
    return "\n".join(svg)


def make_bar(val, length=10):
    """Generate a clean text progress bar [████████░░]."""
    filled = int(round((val / 100.0) * length))
    filled = max(0, min(length, filled))
    return "█" * filled + "░" * (length - filled)


def generate_readme_snippet(state):
    """Generate the Markdown block for README.md."""
    stats = state["stats"]
    mood = state["mood"]
    caretaker = state.get("last_caretaker", USERNAME)
    action = state.get("last_action", "Bubble Bath 🛁")
    total = state.get("total_interactions", 1)

    game_url = f"https://{USERNAME}.github.io/{USERNAME}/"

    glamour_bar = make_bar(stats["glamour"])
    energy_bar = make_bar(stats["energy"])
    happiness_bar = make_bar(stats["happiness"])
    snacks_bar = make_bar(stats["snacks"])

    snippet = f"""<!-- PET:START -->
## 🐩🎀 Barbiecore Virtual Pet: Bella The Glam Poodle

<p align="left">
  <em>Welcome to Bella's Glam Salon! Bella is my autonomous Barbiecore virtual pet living directly on GitHub. Click the play button below to pamper her, feed her macarons, take her shopping, or tuck her in for beauty sleep in real time! 💅💖✨</em>
</p>

<div align="center">

<table width="100%" border="0">
<tr>
<td width="35%" align="center" valign="middle">

```
     /\\_/\\  
    ( o.o )  👑
    =( I )=  🎀
     /     \\ 
    (  "  " )
```
**🐩 BELLA**  
*Princess of Barbie World* 💖  
**Mood:** *"{mood}"* 💅✨  
*Last pampered by **@{caretaker}***  

</td>
<td width="65%" valign="middle">

### 📊 Live Pet Vitals (Direct in README)

| Stat | Meter | Score | Status |
| :--- | :--- | :---: | :---: |
| 💖 **Glamour** | `[{glamour_bar}]` | **`{stats['glamour']}%`** | ✨ Glowing |
| ⚡ **Energy** | `[{energy_bar}]` | **`{stats['energy']}%`** | ⚡ Vibrant |
| ✨ **Happiness** | `[{happiness_bar}]` | **`{stats['happiness']}%`** | 🌸 Pure Joy |
| 🧁 **Snacks** | `[{snacks_bar}]` | **`{stats['snacks']}%`** | 🍓 Satisfied |

</td>
</tr>
</table>

<br/>

<p align="center">
  <img src="./assets/pet-card.svg" width="100%" alt="Bella the Glam Poodle" />
</p>

<br/>

<a href="{game_url}" target="_blank">
  <img src="https://img.shields.io/badge/🎮%20PAMPER%20BELLA%20IN%20BROWSER-Click%20to%20Play-FF1493?style=for-the-badge&logo=sparkles&logoColor=white" alt="Pamper Bella Online" />
</a>

</div>

<br/>

> **👑 Current Mood:** *"{mood}"*  
> **🎮 How to Play:** Click **PAMPER BELLA IN BROWSER** above to open the real-time interactive salon in your browser! Feed her macarons, take her shopping, and hear sounds as her vitals update live! 💕  
> **👑 Current Caretaker:** **@{caretaker}** with `{action}` • **Total Treats Given:** `{total}` ✨

<!-- PET:END -->"""
    return snippet
    return snippet


def update_readme(state):
    """Place or update pet section directly above ## 📊 GitHub Analytics & Insights in README.md."""
    if not os.path.exists(README_PATH):
        print(f"Error: {README_PATH} not found.")
        return

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    new_section = generate_readme_snippet(state)

    if "<!-- PET:START -->" in content and "<!-- PET:END -->" in content:
        before = content.split("<!-- PET:START -->")[0]
        after = content.split("<!-- PET:END -->")[1]
        updated_content = before + new_section + after
    else:
        target_marker = "## 📊 GitHub Analytics & Insights"
        if target_marker in content:
            updated_content = content.replace(target_marker, f"{new_section}\n\n---\n\n{target_marker}")
        else:
            updated_content = content + f"\n\n---\n\n{new_section}\n"

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated_content)
    print("README.md updated with Barbiecore Pet above GitHub Analytics!")


def main():
    state = load_state()

    action = None
    user = None

    if "--action" in sys.argv:
        try:
            idx = sys.argv.index("--action")
            action = sys.argv[idx + 1]
        except Exception:
            action = None

    if "--user" in sys.argv:
        try:
            idx = sys.argv.index("--user")
            user = sys.argv[idx + 1]
        except Exception:
            user = None

    if "--decay" in sys.argv:
        print("Applying hourly stat decay...")
        state = apply_decay(state)
    elif action:
        print(f"Applying action '{action}' from user '{user}'...")
        state, _ = apply_action(state, action, user)
    else:
        print("Rendering current pet state...")

    save_state(state)

    os.makedirs(ASSETS_DIR, exist_ok=True)
    svg_content = render_svg(state)
    with open(PET_SVG_PATH, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"Pet card SVG written to {PET_SVG_PATH}")

    update_readme(state)
    print("Done! Barbiecore Pet Engine completed.")


if __name__ == "__main__":
    main()
