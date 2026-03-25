# ⚔️ HabitHero

A **Habitica-style RPG habit tracker** built in Python with `customtkinter`. Build real habits, level up your character, complete quests, and unlock achievements — all wrapped in a dark RPG aesthetic.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Mac%20%7C%20Linux-lightgrey)

---

## ✨ Features

- 🗡️ **Daily Habits** — Add habits with difficulty, icons, and categories. Complete them to earn XP and gold
- 🧙 **RPG Classes** — Choose Warrior, Mage, Healer, or Rogue — each with unique bonuses
- 📊 **XP & Leveling** — Smooth animated XP bar, level-up celebration overlay
- 🔥 **Streak System** — Daily streaks with streak freeze protection
- 🏪 **Equipment Shop** — Buy and equip gear across 5 rarity tiers (common → legendary)
- 📜 **Quests** — Complete habit-driven quests for bonus gold and XP
- 🏆 **Achievements** — 10 unlockable achievements
- ✨ **Spells** — Class-specific spells that cost mana
- 🎨 **Animations** — Floating +XP popups, habit card pulses, smooth bars, page slides, level-up overlay

---

## 🚀 Quick Start

### 1. Install dependencies
\`\`\`bash
pip install customtkinter pillow
\`\`\`

### 2. Run
\`\`\`bash
python habithero.py
\`\`\`

On first launch you'll see character creation — pick your name, class, and avatar. That's it!

---

## 📁 Project Structure

\`\`\`
HabitHero/
├── habithero.py           # Main application (single file)
├── habithero_save.json    # Save data — auto-created, gitignored
├── habithero_config.json  # Config — auto-created, gitignored
├── .gitignore
└── README.md
\`\`\`

---

## 🔄 Resetting Progress

Delete these files and restart:
\`\`\`bash
del habithero_save.json
del habithero_config.json
\`\`\`

---

## 🛠️ Requirements

- Python 3.10+
- \`customtkinter\`
- \`pillow\`

---

## 📄 License

MIT — free to use, modify, and share.