#!/usr/bin/env python3
"""
Pink Fashion Wordle Engine for GitHub Profile README
Authored for: afifasyed123
"""

import os
import sys
import json
import re
import random
from datetime import datetime, timezone

# Root directory of the repository
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_PATH = os.path.join(ROOT_DIR, ".github", "wordle_state.json")
README_PATH = os.path.join(ROOT_DIR, "README.md")
COMMENT_PATH = os.path.join(ROOT_DIR, ".github", "last_wordle_comment.md")

USERNAME = "afifasyed123"
WORDS_PATH = os.path.join(ROOT_DIR, "data", "words.json")

# Curated chic fashion, beauty, and Barbiecore 5-letter vocabulary
DEFAULT_WORDS = [
    "GLAMS", "TIARA", "HEELS", "SATIN", "DENIM", "PEARL", "GLOSS", "BLUSH",
    "STYLE", "FLAIR", "GOWNS", "POSES", "RINGS", "CHICS", "SILKS", "PURSE",
    "DRESS", "SCENT", "MODEL", "LIPPY", "TREND", "SHINE", "JEWEL", "STRUT",
    "CHARM", "SPARK", "SUITS", "BOOTS", "GLOWS", "FROCK", "LINEN", "BEADS",
    "LACES", "CREAM", "SHADE", "PRADA", "VOGUE", "CORAL", "FANCY", "CROWN",
    "QUEEN", "ROYAL", "LOVES", "SWEET", "PINKY", "HAUTE", "BEAUT", "LOOKS",
    "GLITZ", "MODES"
]

def get_word_list():
    if os.path.exists(WORDS_PATH):
        try:
            with open(WORDS_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                valid = [w.strip().upper() for w in loaded if len(w.strip()) == 5 and w.strip().isalpha()]
                if valid:
                    return valid
        except Exception:
            pass
    return DEFAULT_WORDS

WORDS = get_word_list()
MAX_ATTEMPTS = 6


def load_state():
    """Load current state or initialize a fresh game."""
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load {STATE_PATH}: {e}")

    return {
        "round": 1,
        "target_word": random.choice(WORDS),
        "attempts": [],
        "status": "in_progress",
        "winner": None,
        "last_guesser": None,
        "last_guess": None,
        "last_feedback": None,
        "total_rounds": 1,
        "total_wins": 0
    }


def save_state(state):
    """Save game state to JSON."""
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def evaluate_guess(guess, target):
    """
    Standard Wordle 2-pass evaluation:
    💖 = Correct letter in correct spot
    🌸 = Correct letter in wrong spot
    🤍 = Letter not in word
    """
    feedback = ["🤍"] * 5
    target_counts = {}
    for ch in target:
        target_counts[ch] = target_counts.get(ch, 0) + 1

    # Pass 1: exact matches
    for i in range(5):
        if guess[i] == target[i]:
            feedback[i] = "💖"
            target_counts[guess[i]] -= 1

    # Pass 2: wrong spot matches
    for i in range(5):
        if feedback[i] == "🤍" and guess[i] in target_counts and target_counts[guess[i]] > 0:
            feedback[i] = "🌸"
            target_counts[guess[i]] -= 1

    return feedback


def build_keyboard_tracker(attempts):
    """Track keyboard letters: Correct (💖), Present (🌸), Absent (🤍 / struck)."""
    letter_status = {}
    for att in attempts:
        guess = att["guess"]
        feedback = att["feedback"]
        for ch, fb in zip(guess, feedback):
            curr = letter_status.get(ch)
            if fb == "💖":
                letter_status[ch] = "💖"
            elif fb == "🌸" and curr != "💖":
                letter_status[ch] = "🌸"
            elif fb == "🤍" and curr not in ("💖", "🌸"):
                letter_status[ch] = "🤍"

    rows = [
        "Q W E R T Y U I O P".split(),
        "A S D F G H J K L".split(),
        "Z X C V B N M".split()
    ]

    kb_lines = []
    for r in rows:
        formatted_row = []
        for ch in r:
            st = letter_status.get(ch)
            if st == "💖":
                formatted_row.append(f"**`{ch}`**💖")
            elif st == "🌸":
                formatted_row.append(f"**`{ch}`**🌸")
            elif st == "🤍":
                formatted_row.append(f"~~`{ch}`~~")
            else:
                formatted_row.append(f"`{ch}`")
        kb_lines.append(" ".join(formatted_row))

    return "<br/>\n".join(kb_lines)


def render_markdown(state):
    """Generate the Markdown grid, tracker, and click-to-play link."""
    round_num = state.get("round", 1)
    attempts = state.get("attempts", [])
    num_attempts = len(attempts)
    status = state.get("status", "in_progress")
    winner = state.get("winner")
    target = state.get("target_word", "TIARA")

    issue_url = (
        f"https://github.com/{USERNAME}/{USERNAME}/issues/new"
        f"?title=wordle:+YOURWORD&body=Replace+YOURWORD+with+your+5-letter+guess!"
    )

    # Status Banner
    if status == "won":
        status_banner = f"🎉 **Round #{round_num} SOLVED by @{winner}!** 👑 The glam word was **{target}**! 💕"
    elif status == "lost":
        status_banner = f"💔 **Round #{round_num} Game Over!** The glam word was **{target}**. Fresh round ready! 🥺"
    else:
        status_banner = f"💅 **Round #{round_num}** — **Attempt {num_attempts}/6** | *Guess the 5-letter glam fashion word!* ✨"

    # 6-Row x 5-Column Grid Table
    grid_rows = []
    for row_idx in range(MAX_ATTEMPTS):
        row_num = row_idx + 1
        if row_idx < num_attempts:
            att = attempts[row_idx]
            g = att["guess"]
            fb = att["feedback"]
            user = att["user"]
            tiles = " ".join(fb)
            letters = f"`{g[0]}` `{g[1]}` `{g[2]}` `{g[3]}` `{g[4]}`"
            player = f"@{user}"
        else:
            tiles = "⬜ ⬜ ⬜ ⬜ ⬜"
            letters = "`·` `·` `·` `·` `·`"
            player = "—"

        grid_rows.append(f"| **{row_num}** | {letters} | {tiles} | {player} |")

    grid_table = "\n".join(grid_rows)
    keyboard_display = build_keyboard_tracker(attempts)

    snippet = f"""<!-- WORDLE:START -->
### 🎀 Pink Fashion Wordle
<p align="left">
  <em>An interactive Barbiecore &amp; chic fashion Wordle running directly in this README! Guess the hidden 5-letter glam word (e.g. <code>TIARA</code>, <code>GLAMS</code>, <code>HEELS</code>, <code>SATIN</code>). Click the button below to play! 💅💖✨</em>
</p>

<div align="center">

{status_banner}

<br/>

| Row | Word Guess | Tile Feedback | Caretaker / Guesser |
| :-: | :-: | :-: | :--- |
{grid_table}

<br/>

<a href="{issue_url}">
  <img src="https://img.shields.io/badge/🎀%20Click%20Here%20to%20Submit%20a%205--Letter%20Guess-FF1493?style=for-the-badge&logo=sparkles&logoColor=white" alt="Submit Guess" />
</a>

<br/><br/>

**⌨️ Available Letters Tracker:**  
{keyboard_display}

</div>

<br/>

> **✨ Tile Legend:** 💖 = Correct letter in correct spot | 🌸 = Correct letter, wrong spot | 🤍 = Letter not in word  
> **💡 How to Play:** Click the pink button above, replace `YOURWORD` in the title with your 5-letter fashion guess, and hit **"Submit new issue"**! Our GitHub Action will automatically evaluate your guess, update the board in this README, and comment back! 💕

<!-- WORDLE:END -->"""
    return snippet


def update_readme(snippet):
    """
    IN-PLACE INJECTION:
    Only replaces content between <!-- WORDLE:START --> and <!-- WORDLE:END -->.
    If tags do not exist yet, inserts directly above '## 📊 GitHub Analytics & Insights'.
    """
    if not os.path.exists(README_PATH):
        print(f"Error: {README_PATH} not found.")
        return

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    start_tag = "<!-- WORDLE:START -->"
    end_tag = "<!-- WORDLE:END -->"

    pattern = re.compile(rf"{re.escape(start_tag)}.*?{re.escape(end_tag)}", re.DOTALL)

    if pattern.search(content):
        updated_content = pattern.sub(snippet.strip(), content)
    else:
        # Initial insertion: directly above GitHub Analytics
        target_marker = "## 📊 GitHub Analytics & Insights"
        if target_marker in content:
            updated_content = content.replace(target_marker, f"{snippet.strip()}\n\n---\n\n{target_marker}")
        else:
            updated_content = content + f"\n\n---\n\n{snippet.strip()}\n"

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated_content)
    print("README.md updated in-place with Pink Fashion Wordle!")


def main():
    state = load_state()

    if len(sys.argv) < 2:
        print("No guess provided. Rendering current board...")
        snippet = render_markdown(state)
        update_readme(snippet)
        return

    raw_title = sys.argv[1]
    actor = sys.argv[2] if len(sys.argv) > 2 else "anonymous"

    # Extract word from title (e.g. "wordle: TIARA" -> "TIARA")
    clean_guess = re.sub(r"(?i)^wordle\s*:\s*", "", raw_title).strip().upper()
    # Remove any stray punctuation
    clean_guess = re.sub(r"[^A-Z]", "", clean_guess)

    # Validate 5-letter alphabetic word
    if len(clean_guess) != 5:
        err_msg = (
            f"### ⚠️ Oops @{actor}! 🥺\n\n"
            f"Your guess **`{clean_guess}`** is not a valid **5-letter word**!\n\n"
            f"Please submit a valid 5-letter fashion/beauty word (e.g., `TIARA`, `GLAMS`, `HEELS`, `SATIN`). 💕"
        )
        with open(COMMENT_PATH, "w", encoding="utf-8") as f:
            f.write(err_msg)
        print(f"Invalid guess '{clean_guess}'. Aborting board update.")
        return

    # If the previous round was already completed, start fresh round for this new guess
    if state.get("status") in ("won", "lost"):
        state["round"] = state.get("round", 1) + 1
        state["target_word"] = random.choice(WORDS)
        state["attempts"] = []
        state["status"] = "in_progress"
        state["winner"] = None

    target = state.get("target_word", "TIARA")
    feedback = evaluate_guess(clean_guess, target)
    feedback_str = "".join(feedback)

    state["attempts"].append({
        "guess": clean_guess,
        "feedback": feedback,
        "user": actor
    })
    state["last_guesser"] = actor
    state["last_guess"] = clean_guess
    state["last_feedback"] = feedback_str

    is_win = (clean_guess == target)
    is_loss = (len(state["attempts"]) >= MAX_ATTEMPTS and not is_win)

    if is_win:
        state["status"] = "won"
        state["winner"] = actor
        state["total_wins"] = state.get("total_wins", 0) + 1
        result_text = f"🎉 **BINGO! You solved the glam word: `{target}`!** 👑💅✨"
    elif is_loss:
        state["status"] = "lost"
        result_text = f"💔 **Round Over!** The glam word was **`{target}`**. Better luck next round! 🥺"
    else:
        result_text = f"Keep going! **{MAX_ATTEMPTS - len(state['attempts'])}** attempts remaining in this round. 🌸"

    # Prepare issue reply comment
    comment_text = (
        f"### 🎀 Fabulous Guess, @{actor}! ✨\n\n"
        f"Your guess: **`{clean_guess}`**\n"
        f"Your tiles: **{feedback_str}**\n\n"
        f"{result_text}\n\n"
        f"Check the live board on the [Profile README](https://github.com/{USERNAME}/{USERNAME})! 💕"
    )
    with open(COMMENT_PATH, "w", encoding="utf-8") as f:
        f.write(comment_text)

    # Save state
    save_state(state)

    # Render & in-place inject into README.md
    snippet = render_markdown(state)
    update_readme(snippet)

    # If game ended, prepare the next target word in state so the next guess starts fresh seamlessly
    if is_win or is_loss:
        # Next round will start on next incoming guess
        pass

    print("Wordle guess processed and README updated!")


if __name__ == "__main__":
    main()
