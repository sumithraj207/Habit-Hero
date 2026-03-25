"""
HabitHero — Habitica-style RPG Habit Tracker
Requires: customtkinter, Pillow
Install: pip install customtkinter pillow
"""

import customtkinter as ctk
import json, os, random, math, threading
from datetime import date, datetime
from tkinter import messagebox, simpledialog
import tkinter as tk
from PIL import Image, ImageDraw, ImageFont

# ─── COLOR EMOJI RENDERING ───────────────────────────────────────────────────

_EMOJI_FONT_PATHS = [
    "C:/Windows/Fonts/seguiemj.ttf",
    "/System/Library/Fonts/Apple Color Emoji.ttc",
    "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
    "/usr/share/fonts/noto/NotoColorEmoji.ttf",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "NotoColorEmoji.ttf"),
]
_EMOJI_FONT_FILE = next((p for p in _EMOJI_FONT_PATHS if os.path.exists(p)), None)
_EMOJI_CACHE: dict = {}

def _render_emoji_image(emoji: str, px: int):
    key = (emoji, px)
    if key in _EMOJI_CACHE:
        return _EMOJI_CACHE[key]
    if not _EMOJI_FONT_FILE:
        return None
    try:
        font_size = 109
        canvas = int(font_size * 1.2)
        font = ImageFont.truetype(_EMOJI_FONT_FILE, font_size)
        img = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((canvas // 2, canvas // 2), emoji, font=font,
                  anchor="mm", embedded_color=True)
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)
        img = img.resize((px, px), Image.LANCZOS)
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(px, px))
        _EMOJI_CACHE[key] = ctk_img
        return ctk_img
    except Exception:
        return None


class EmojiLabel(ctk.CTkLabel):
    """CTkLabel that shows a full-color emoji via Pillow rendering."""

    def __init__(self, parent, text: str = "", size: int = 32, **kwargs):
        kwargs.pop("bg", None)
        kwargs.pop("background", None)
        self._emoji = text
        self._px = size
        img = _render_emoji_image(text, size)
        if img:
            super().__init__(parent, image=img, text="", **kwargs)
        else:
            super().__init__(parent, text=text,
                             font=("Segoe UI Emoji", max(10, size - 4)), **kwargs)
        self._img = img

    def configure(self, **kwargs):
        kwargs.pop("bg", None)
        kwargs.pop("background", None)
        new_emoji = kwargs.pop("text", None)
        if new_emoji is not None and new_emoji != self._emoji:
            self._emoji = new_emoji
            img = _render_emoji_image(new_emoji, self._px)
            self._img = img
            if img:
                super().configure(image=img, text="", **kwargs)
            else:
                super().configure(text=new_emoji, **kwargs)
            return
        super().configure(**kwargs)

    def config(self, **kwargs):
        self.configure(**kwargs)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DATA_FILE = "habithero_save.json"

# ─── CONSTANTS ───────────────────────────────────────────────────────────────

CLASSES = {
    "Warrior":  {"emoji": "⚔️",  "color": "#e74c3c", "bonus": "strength",  "desc": "High HP, deals extra damage on habits"},
    "Mage":     {"emoji": "🔮",  "color": "#9b59b6", "bonus": "mana",      "desc": "Earns mana fast, powerful spells"},
    "Healer":   {"emoji": "💚",  "color": "#2ecc71", "bonus": "healing",   "desc": "Heals party, high HP recovery"},
    "Rogue":    {"emoji": "🗡️",  "color": "#f39c12", "bonus": "gold",      "desc": "Earns double gold on tasks"},
}

AVATARS = ["🧙", "🦸", "👨‍💻", "👨‍🚀", "🐉", "🦅", "🐺", "🦊", "🐼", "🐱", "🤖", "👑"]

HABIT_ICONS = ["🏃", "📚", "💧", "🥗", "🧘", "💪", "🎯", "✍️", "🎨", "🎵", "💤", "🌿", "🏋️", "🚴", "🍎"]

EQUIPMENT_SHOP = [
    {"id":"sword1",   "name":"Iron Sword",      "emoji":"⚔️",  "cost":30,  "stat":"str", "val":5,  "rarity":"common"},
    {"id":"shield1",  "name":"Wooden Shield",   "emoji":"🛡️",  "cost":25,  "stat":"def", "val":4,  "rarity":"common"},
    {"id":"hat1",     "name":"Wizard Hat",      "emoji":"🎩",  "cost":40,  "stat":"int", "val":6,  "rarity":"uncommon"},
    {"id":"sword2",   "name":"Silver Sword",    "emoji":"🗡️",  "cost":80,  "stat":"str", "val":12, "rarity":"uncommon"},
    {"id":"armor1",   "name":"Chainmail",       "emoji":"🧥",  "cost":75,  "stat":"def", "val":10, "rarity":"uncommon"},
    {"id":"ring1",    "name":"Ring of Focus",   "emoji":"💍",  "cost":100, "stat":"int", "val":15, "rarity":"rare"},
    {"id":"axe1",     "name":"Battle Axe",      "emoji":"🪓",  "cost":120, "stat":"str", "val":20, "rarity":"rare"},
    {"id":"orb1",     "name":"Crystal Orb",     "emoji":"🔮",  "cost":150, "stat":"int", "val":25, "rarity":"epic"},
    {"id":"crown1",   "name":"Hero Crown",      "emoji":"👑",  "cost":200, "stat":"def", "val":30, "rarity":"epic"},
    {"id":"wings1",   "name":"Angel Wings",     "emoji":"👼",  "cost":300, "stat":"str", "val":40, "rarity":"legendary"},
]

RARITY_COLORS = {
    "common":    "#aaaaaa",
    "uncommon":  "#2ecc71",
    "rare":      "#3498db",
    "epic":      "#9b59b6",
    "legendary": "#f39c12",
}

QUESTS = [
    {"id":"q1", "name":"Slime Hunt",       "emoji":"🟢", "reward_gold":20, "reward_xp":50,  "tasks":3,  "desc":"Complete 3 habits to defeat the slime!"},
    {"id":"q2", "name":"Dragon's Lair",    "emoji":"🐉", "reward_gold":60, "reward_xp":120, "tasks":8,  "desc":"Complete 8 habits to slay the dragon!"},
    {"id":"q3", "name":"Cave Troll",       "emoji":"👹", "reward_gold":35, "reward_xp":75,  "tasks":5,  "desc":"Complete 5 habits to defeat the troll!"},
    {"id":"q4", "name":"Phoenix Rising",   "emoji":"🔥", "reward_gold":90, "reward_xp":200, "tasks":12, "desc":"Complete 12 habits to tame the phoenix!"},
    {"id":"q5", "name":"The Lich King",    "emoji":"💀", "reward_gold":150,"reward_xp":300, "tasks":20, "desc":"Complete 20 habits to defeat the Lich King!"},
]

MOTIVATIONAL_QUOTES = [
    "Every habit is a vote for the person you want to become.",
    "Small consistent actions create massive results.",
    "Your future self is watching. Make them proud.",
    "Discipline is the bridge between goals and achievement.",
    "The secret of your future is hidden in your daily routine.",
    "Champions aren't made in gyms. They're made from habits.",
    "Be the hero of your own story.",
    "Level up every single day.",
]

ACHIEVEMENTS = [
    {"id":"first_habit",  "name":"First Step",      "emoji":"👣", "desc":"Complete your first habit",          "condition": lambda d: d["total_completions"] >= 1},
    {"id":"streak_3",     "name":"On Fire!",         "emoji":"🔥", "desc":"Reach a 3-day streak",               "condition": lambda d: d["streak"] >= 3},
    {"id":"streak_7",     "name":"Week Warrior",     "emoji":"⚔️",  "desc":"Reach a 7-day streak",               "condition": lambda d: d["streak"] >= 7},
    {"id":"level_5",      "name":"Rising Hero",      "emoji":"⭐", "desc":"Reach level 5",                      "condition": lambda d: d["level"] >= 5},
    {"id":"level_10",     "name":"Seasoned Veteran", "emoji":"🌟", "desc":"Reach level 10",                     "condition": lambda d: d["level"] >= 10},
    {"id":"rich",         "name":"Gold Hoarder",     "emoji":"💰", "desc":"Accumulate 500 gold",                "condition": lambda d: d["gold"] >= 500},
    {"id":"shopaholic",   "name":"Equipped Hero",    "emoji":"🛒", "desc":"Buy 3 items from the shop",          "condition": lambda d: len(d["inventory"]) >= 3},
    {"id":"quest_done",   "name":"Quest Completer",  "emoji":"📜", "desc":"Complete your first quest",          "condition": lambda d: d["quests_completed"] >= 1},
    {"id":"habits_5",     "name":"Habit Builder",    "emoji":"🏗️", "desc":"Have 5 habits at once",              "condition": lambda d: len(d["habits"]) >= 5},
    {"id":"completions_50","name":"Half Century",    "emoji":"🎯", "desc":"Complete 50 total habits",           "condition": lambda d: d["total_completions"] >= 50},
]

SPELLS = {
    "Warrior": [
        {"name":"Battle Cry",   "emoji":"📣", "cost":10, "desc":"All habits give +50% XP for the rest of today", "effect":"xp_boost"},
        {"name":"Iron Will",    "emoji":"🛡️", "cost":20, "desc":"Protect your streak once (extra freeze)",        "effect":"extra_freeze"},
    ],
    "Mage": [
        {"name":"Fireball",     "emoji":"🔥", "cost":15, "desc":"Instantly complete a random habit",              "effect":"auto_complete"},
        {"name":"Time Warp",    "emoji":"⏳", "cost":30, "desc":"Double XP from all habits for 1 hour",           "effect":"xp_boost"},
    ],
    "Healer": [
        {"name":"Heal",         "emoji":"💚", "cost":10, "desc":"Restore 20 HP",                                  "effect":"heal"},
        {"name":"Blessing",     "emoji":"✨", "cost":25, "desc":"All habits give +10 bonus gold today",           "effect":"gold_boost"},
    ],
    "Rogue": [
        {"name":"Pickpocket",   "emoji":"💸", "cost":10, "desc":"Steal 15 bonus gold",                           "effect":"steal_gold"},
        {"name":"Shadow Step",  "emoji":"🌑", "cost":20, "desc":"Instantly complete a habit without using HP",    "effect":"free_complete"},
    ],
}

# ─── DATA ────────────────────────────────────────────────────────────────────

def default_data():
    return {
        "habits": {},
        "xp": 0,
        "level": 1,
        "gold": 0,
        "streak": 0,
        "freeze": 2,
        "avatar": "🧙",
        "char_class": None,
        "char_name": "Hero",
        "hp": 50,
        "max_hp": 50,
        "mana": 30,
        "max_mana": 30,
        "inventory": [],
        "equipped": [],
        "last_date": str(date.today()),
        "total_completions": 0,
        "quests_completed": 0,
        "active_quest": None,
        "quest_progress": 0,
        "achievements": [],
        "daily_tasks": [],
        "todos": [],
        "xp_boost": False,
        "gold_boost": False,
        "history": [],
    }

def load_data():
    if not os.path.exists(DATA_FILE):
        return default_data()
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        for k, v in default_data().items():
            if k not in data:
                data[k] = v
        return data
    except:
        return default_data()

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def xp_for_level(level):
    return int(100 * (1.5 ** (level - 1)))

# ─── WIDGETS ─────────────────────────────────────────────────────────────────

class StatBar(ctk.CTkFrame):
    def __init__(self, parent, label, color, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.label = label
        self.color = color
        self._build()

    def _build(self):
        self.lbl = ctk.CTkLabel(self, text=self.label, font=("Segoe UI", 10, "bold"), width=40, anchor="w")
        self.lbl.pack(side="left")
        self.bar = ctk.CTkProgressBar(self, height=12, corner_radius=6, progress_color=self.color, width=140)
        self.bar.pack(side="left", padx=4)
        self.bar.set(1.0)
        self.val_lbl = ctk.CTkLabel(self, text="", font=("Segoe UI", 10), width=50, anchor="e")
        self.val_lbl.pack(side="left")

    def update(self, current, maximum):
        pct = max(0, min(1, current / maximum)) if maximum > 0 else 0
        self.bar.set(pct)
        self.val_lbl.configure(text=f"{current}/{maximum}")


class HabitCard(ctk.CTkFrame):
    def __init__(self, parent, name, info, on_done, on_delete, on_edit, **kwargs):
        super().__init__(parent, corner_radius=12, fg_color="#1e1e2e", border_width=1, border_color="#333355", **kwargs)
        self.name = name
        self.info = info
        self._build(on_done, on_delete, on_edit)

    def _build(self, on_done, on_delete, on_edit):
        done = self.info.get("done", False)
        streak = self.info.get("streak", 0)
        icon = self.info.get("icon", "🎯")
        difficulty = self.info.get("difficulty", "medium")

        diff_colors = {"easy": "#2ecc71", "medium": "#f39c12", "hard": "#e74c3c"}
        diff_color = diff_colors.get(difficulty, "#f39c12")

        # Left icon
        icon_frame = ctk.CTkFrame(self, width=48, height=48, corner_radius=12,
                                   fg_color="#2a2a3e" if not done else "#1a3a2a")
        icon_frame.pack(side="left", padx=10, pady=10)
        icon_frame.pack_propagate(False)
        EmojiLabel(icon_frame, text=icon, size=28).place(relx=0.5, rely=0.5, anchor="center")

        # Middle content
        mid = ctk.CTkFrame(self, fg_color="transparent")
        mid.pack(side="left", fill="both", expand=True, pady=8)

        name_color = "#aaaaaa" if done else "#ffffff"
        ctk.CTkLabel(mid, text=self.name, font=("Segoe UI", 13, "bold"),
                     text_color=name_color, anchor="w").pack(anchor="w")

        meta_row = ctk.CTkFrame(mid, fg_color="transparent")
        meta_row.pack(anchor="w", pady=(2, 0))

        ctk.CTkLabel(meta_row, text=f"  {difficulty.capitalize()}",
                     font=("Segoe UI", 10), text_color=diff_color).pack(side="left")

        if streak > 0:
            ctk.CTkLabel(meta_row, text=f"  🔥 {streak}d streak",
                         font=("Segoe UI", 10), text_color="#f39c12").pack(side="left")

        xp_gain = {"easy": 10, "medium": 20, "hard": 35}[difficulty]
        gold_gain = {"easy": 3, "medium": 5, "hard": 10}[difficulty]
        ctk.CTkLabel(meta_row, text=f"  ✨{xp_gain}xp  🪙{gold_gain}g",
                     font=("Segoe UI", 10), text_color="#888899").pack(side="left")

        # Right buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(side="right", padx=10)

        if done:
            EmojiLabel(btn_frame, text="✅", size=26).pack()
        else:
            done_btn = ctk.CTkButton(btn_frame, text="Done", width=70, height=32,
                                      fg_color="#2ecc71", hover_color="#27ae60",
                                      font=("Segoe UI", 12, "bold"),
                                      command=lambda: on_done(self.name))
            done_btn.pack(pady=2)

        edit_btn = ctk.CTkButton(btn_frame, text="✏️", width=32, height=26,
                                  fg_color="transparent", hover_color="#2a2a3e",
                                  font=("Segoe UI", 12), command=lambda: on_edit(self.name))
        edit_btn.pack(pady=1)

        del_btn = ctk.CTkButton(btn_frame, text="🗑", width=32, height=26,
                                 fg_color="transparent", hover_color="#3a1a1a",
                                 font=("Segoe UI", 12), command=lambda: on_delete(self.name))
        del_btn.pack(pady=1)


class ToastNotification(ctk.CTkToplevel):
    def __init__(self, parent, message, emoji="✨", color="#2ecc71"):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color="#1e1e2e")

        # Position top-right
        pw = parent.winfo_x() + parent.winfo_width()
        py = parent.winfo_y()
        self.geometry(f"280x70+{pw-300}+{py+20}")

        frame = ctk.CTkFrame(self, fg_color="#1e1e2e", border_width=2, border_color=color, corner_radius=12)
        frame.pack(fill="both", expand=True, padx=2, pady=2)

        ctk.CTkLabel(frame, text=f"{emoji}  {message}",
                     font=("Segoe UI", 13, "bold"), text_color=color).place(relx=0.5, rely=0.5, anchor="center")

        self.after(2500, self.destroy)


class AddHabitDialog(ctk.CTkToplevel):
    """Styled dialog for adding/editing habits."""

    def __init__(self, parent, existing=None, on_save=None, on_cancel=None):
        super().__init__(parent)
        self.on_save   = on_save
        self.on_cancel = on_cancel
        self.existing  = existing or {}
        self.result    = None

        title = "Edit Habit" if existing else "Add Habit"
        self.title(title)
        self.configure(fg_color="#1e1e2e")
        self.resizable(False, False)
        self.grab_set()
        self.lift()
        self.focus_force()

        # Centre on parent
        self.update_idletasks()
        pw = parent.winfo_x() + parent.winfo_width() // 2
        ph = parent.winfo_y() + parent.winfo_height() // 2
        self.geometry(f"460x480+{pw-230}+{ph-240}")

        self._build()

    def _build(self):
        title_text = "✏️  Edit Habit" if self.existing.get("name") else "➕  Add New Habit"
        ctk.CTkLabel(self, text=title_text,
                     font=("Segoe UI", 16, "bold")).pack(padx=24, pady=(20,4), anchor="w")
        ctk.CTkFrame(self, height=1, fg_color="#333355").pack(fill="x", padx=20, pady=(0,12))

        # Name
        ctk.CTkLabel(self, text="Habit Name", font=("Segoe UI", 12),
                     text_color="#aaaacc").pack(padx=24, anchor="w")
        self.name_entry = ctk.CTkEntry(self, placeholder_text="e.g. Morning Run",
                                        height=40, font=("Segoe UI", 13))
        self.name_entry.pack(padx=24, pady=(4,14), fill="x")
        if self.existing.get("name"):
            self.name_entry.insert(0, self.existing["name"])
        self.name_entry.focus_set()

        # Difficulty
        ctk.CTkLabel(self, text="Difficulty", font=("Segoe UI", 12),
                     text_color="#aaaacc").pack(padx=24, anchor="w")
        self.diff_var = ctk.StringVar(value=self.existing.get("difficulty", "medium"))
        diff_row = ctk.CTkFrame(self, fg_color="transparent")
        diff_row.pack(padx=24, pady=(4,14), fill="x")
        for d, col in [("easy","#2ecc71"),("medium","#f39c12"),("hard","#e74c3c")]:
            ctk.CTkRadioButton(diff_row, text=d.capitalize(), variable=self.diff_var,
                               value=d, font=("Segoe UI", 12),
                               fg_color=col).pack(side="left", padx=12)

        # Icon
        ctk.CTkLabel(self, text="Icon", font=("Segoe UI", 12),
                     text_color="#aaaacc").pack(padx=24, anchor="w")
        self.icon_var = ctk.StringVar(value=self.existing.get("icon", "🎯"))
        icon_wrap = ctk.CTkFrame(self, fg_color="#12121f", corner_radius=10)
        icon_wrap.pack(padx=24, pady=(4,14), fill="x")
        icon_row = ctk.CTkFrame(icon_wrap, fg_color="transparent")
        icon_row.pack(padx=8, pady=8)
        self._icon_btns = {}
        for ic in HABIT_ICONS:
            img = _render_emoji_image(ic, 26)
            if img:
                btn = ctk.CTkButton(icon_row, image=img, text="", width=38, height=38,
                                    fg_color="transparent", hover_color="#2a2a4a",
                                    corner_radius=8,
                                    command=lambda i=ic: self._select_icon(i))
            else:
                btn = ctk.CTkButton(icon_row, text=ic, width=38, height=38,
                                    font=("Segoe UI", 18), fg_color="transparent",
                                    hover_color="#2a2a4a", corner_radius=8,
                                    command=lambda i=ic: self._select_icon(i))
            btn.pack(side="left", padx=2)
            self._icon_btns[ic] = btn
        self._select_icon(self.icon_var.get())

        # Category
        ctk.CTkLabel(self, text="Category", font=("Segoe UI", 12),
                     text_color="#aaaacc").pack(padx=24, anchor="w")
        self.cat_var = ctk.StringVar(value=self.existing.get("category", "Health"))
        ctk.CTkOptionMenu(self, values=["Health","Mind","Work","Social","Creative","Finance"],
                          variable=self.cat_var, height=36,
                          font=("Segoe UI", 12)).pack(padx=24, pady=(4,16), fill="x")

        # Buttons
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(padx=24, pady=(0,20), fill="x")
        ctk.CTkButton(btn_row, text="Cancel", height=40, width=100,
                       fg_color="#2a2a3e", hover_color="#3a3a5e",
                       font=("Segoe UI", 12),
                       command=self._cancel).pack(side="left")
        ctk.CTkButton(btn_row, text="💾  Save Habit", height=40,
                       fg_color="#7b1fa2", hover_color="#9c27b0",
                       font=("Segoe UI", 13, "bold"),
                       command=self._save).pack(side="right", fill="x",
                                                expand=True, padx=(10,0))

        self.name_entry.bind("<Return>", lambda e: self._save())
        self.bind("<Escape>", lambda e: self._cancel())

    def _select_icon(self, icon):
        self.icon_var.set(icon)
        for ic, btn in self._icon_btns.items():
            btn.configure(fg_color="#2a1a4a" if ic == icon else "transparent")

    def _save(self):
        name = self.name_entry.get().strip()
        if not name:
            self.name_entry.configure(border_color="#e74c3c", border_width=2)
            return
        self.result = {
            "name": name,
            "difficulty": self.diff_var.get(),
            "icon": self.icon_var.get(),
            "category": self.cat_var.get(),
        }
        self.destroy()
        if self.on_save:
            self.on_save(self.result)

    def _cancel(self):
        self.destroy()
        if self.on_cancel:
            self.on_cancel()



# ─── MAIN APP ────────────────────────────────────────────────────────────────

class HabitHeroApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("HabitHero ⚔️")
        self.minsize(1000, 700)
        self.configure(fg_color="#0d0d1a")
        # Reliable cross-platform maximize: set a base geometry, then maximize after mainloop starts
        self.geometry("1200x780")
        self.after(10, self._maximize)

        self.data = load_data()
        self.daily_reset()

        if not self.data.get("char_class"):
            self._show_character_creation_inline()
        else:
            self.build_ui()
            self.refresh_all()

    def _maximize(self):
        """Maximize window — works on Windows, macOS, and Linux."""
        try:
            self.state("zoomed")        # Windows
        except Exception:
            try:
                self.attributes("-zoomed", True)  # Linux
            except Exception:
                w = self.winfo_screenwidth()
                h = self.winfo_screenheight()
                self.geometry(f"{w}x{h}+0+0")    # macOS fallback

    # ─── CHARACTER CREATION (inline — no second window) ─────────────────────

    def _show_character_creation_inline(self):
        """Build character creation directly inside the main window — no CTkToplevel."""
        self.cc_frame = ctk.CTkScrollableFrame(self, fg_color="#0d0d1a", corner_radius=0)
        self.cc_frame.pack(fill="both", expand=True)

        # Centre column
        centre = ctk.CTkFrame(self.cc_frame, fg_color="transparent")
        centre.pack(expand=True, pady=40)

        ctk.CTkLabel(centre, text="⚔️  Create Your Hero  ⚔️",
                     font=("Segoe UI", 28, "bold"), text_color="#f39c12").pack(pady=(0, 24))

        ctk.CTkLabel(centre, text="Hero Name", font=("Segoe UI", 13),
                     text_color="#cccccc").pack(pady=(0, 4))
        self.cc_name = ctk.CTkEntry(centre, width=320, height=42, font=("Segoe UI", 14),
                                     placeholder_text="Enter your hero name...")
        self.cc_name.pack()

        ctk.CTkLabel(centre, text="Choose Your Class",
                     font=("Segoe UI", 16, "bold")).pack(pady=(28, 10))

        self.cc_class = ctk.StringVar(value="Warrior")
        grid = ctk.CTkFrame(centre, fg_color="transparent")
        grid.pack()

        for i, (cls_name, cls_info) in enumerate(CLASSES.items()):
            frame = ctk.CTkFrame(grid, fg_color="#1e1e2e", border_width=2, border_color="#333355",
                                  corner_radius=14, width=130, height=150)
            frame.grid(row=0, column=i, padx=10, pady=4)
            frame.pack_propagate(False)
            EmojiLabel(frame, text=cls_info["emoji"], size=36).pack(pady=(14, 2))
            ctk.CTkLabel(frame, text=cls_name, font=("Segoe UI", 13, "bold"),
                         text_color=cls_info["color"]).pack()
            ctk.CTkLabel(frame, text=cls_info["desc"], font=("Segoe UI", 9),
                         text_color="#888899", wraplength=110).pack(padx=6)
            ctk.CTkRadioButton(frame, text="", variable=self.cc_class, value=cls_name).pack(pady=8)

        ctk.CTkLabel(centre, text="Choose Your Avatar",
                     font=("Segoe UI", 14)).pack(pady=(24, 8))
        self.cc_avatar = ctk.StringVar(value="🧙")
        av_frame = ctk.CTkFrame(centre, fg_color="#1a1a2a", corner_radius=10)
        av_frame.pack(padx=20)
        av_inner = ctk.CTkFrame(av_frame, fg_color="transparent")
        av_inner.pack(padx=8, pady=8)
        for av in AVATARS:
            img = _render_emoji_image(av, 32)
            if img:
                btn = ctk.CTkButton(av_inner, image=img, text="", width=46, height=46,
                                    fg_color="transparent", hover_color="#2a2a3e",
                                    command=lambda a=av: self.cc_avatar.set(a))
            else:
                btn = ctk.CTkButton(av_inner, text=av, width=46, height=46,
                                    font=("Segoe UI", 22), fg_color="transparent",
                                    hover_color="#2a2a3e",
                                    command=lambda a=av: self.cc_avatar.set(a))
            btn.pack(side="left", padx=3)

        ctk.CTkButton(centre, text="⚔️  Begin Your Journey!", height=50, width=320,
                       fg_color="#7b1fa2", hover_color="#9c27b0",
                       font=("Segoe UI", 16, "bold"),
                       command=self._finish_creation).pack(pady=28)

    def _finish_creation(self):
        name = self.cc_name.get().strip() or "Hero"
        cls = self.cc_class.get()
        avatar = self.cc_avatar.get()
        self.data["char_name"] = name
        self.data["char_class"] = cls
        self.data["avatar"] = avatar
        if cls == "Warrior":
            self.data["max_hp"] = 70; self.data["hp"] = 70
        elif cls == "Mage":
            self.data["max_mana"] = 60; self.data["mana"] = 60
        elif cls == "Healer":
            self.data["max_hp"] = 60; self.data["hp"] = 60
        elif cls == "Rogue":
            self.data["gold"] += 20
        save_data(self.data)
        # Tear down inline CC frame, then build the real UI
        self.cc_frame.destroy()
        self.build_ui()
        self.refresh_all()

    # ─── BUILD MAIN UI ───────────────────────────────────────────────────────

    def build_ui(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#12121f")
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Main content
        self.main = ctk.CTkFrame(self, corner_radius=0, fg_color="#0d0d1a")
        self.main.pack(side="left", fill="both", expand=True)


        self._build_sidebar()
        self._build_topbar()

        # Page container
        self.page_frame = ctk.CTkFrame(self.main, corner_radius=0, fg_color="transparent")
        self.page_frame.pack(fill="both", expand=True, padx=16, pady=8)

        # Pages
        self.pages = {}
        self._build_habits_page()
        self._build_character_page()
        self._build_shop_page()
        self._build_quests_page()
        self._build_achievements_page()

        self.show_page("habits")

    def _build_sidebar(self):
        # Logo
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="#0d0d1a", corner_radius=0, height=70)
        logo_frame.pack(fill="x")
        logo_frame.pack_propagate(False)
        ctk.CTkLabel(logo_frame, text="⚔️ HabitHero", font=("Segoe UI", 18, "bold"),
                     text_color="#f39c12").place(relx=0.5, rely=0.5, anchor="center")

        # Character mini-card
        self.sb_char_frame = ctk.CTkFrame(self.sidebar, fg_color="#1a1a2a", corner_radius=12)
        self.sb_char_frame.pack(padx=12, pady=8, fill="x")

        self.sb_avatar = EmojiLabel(self.sb_char_frame, text="🧙", size=48)
        self.sb_avatar.pack(pady=(10, 0))

        self.sb_name = ctk.CTkLabel(self.sb_char_frame, text="Hero",
                                     font=("Segoe UI", 13, "bold"), text_color="#ffffff")
        self.sb_name.pack()

        self.sb_class = ctk.CTkLabel(self.sb_char_frame, text="Warrior",
                                      font=("Segoe UI", 11), text_color="#888899")
        self.sb_class.pack()

        self.sb_level = ctk.CTkLabel(self.sb_char_frame, text="Lvl 1",
                                      font=("Segoe UI", 11, "bold"), text_color="#f39c12")
        self.sb_level.pack(pady=(2, 4))

        # HP bar
        self.sb_hp = StatBar(self.sb_char_frame, "HP", "#e74c3c")
        self.sb_hp.pack(padx=10, pady=2, fill="x")

        # Mana bar
        self.sb_mana = StatBar(self.sb_char_frame, "MP", "#3498db")
        self.sb_mana.pack(padx=10, pady=2, fill="x")

        # XP bar
        self.sb_xp = StatBar(self.sb_char_frame, "XP", "#9b59b6")
        self.sb_xp.pack(padx=10, pady=(2, 10), fill="x")

        # Currency
        cur_frame = ctk.CTkFrame(self.sb_char_frame, fg_color="transparent")
        cur_frame.pack(pady=(0, 10))
        self.sb_gold = ctk.CTkLabel(cur_frame, text="🪙 0 gold",
                                     font=("Segoe UI", 11, "bold"), text_color="#f39c12")
        self.sb_gold.pack(side="left", padx=8)
        self.sb_streak = ctk.CTkLabel(cur_frame, text="🔥 0",
                                       font=("Segoe UI", 11, "bold"), text_color="#e67e22")
        self.sb_streak.pack(side="left")

        # Nav buttons
        nav_items = [
            ("🗡️  Daily Habits", "habits"),
            ("🧙  Character",    "character"),
            ("🏪  Shop",         "shop"),
            ("📜  Quests",       "quests"),
            ("🏆  Achievements", "achievements"),
        ]
        ctk.CTkLabel(self.sidebar, text="NAVIGATION", font=("Segoe UI", 9, "bold"),
                     text_color="#555577").pack(padx=16, pady=(12, 4), anchor="w")

        self.nav_btns = {}
        for label, page in nav_items:
            btn = ctk.CTkButton(self.sidebar, text=label, height=40, anchor="w",
                                 fg_color="transparent", hover_color="#1e1e3a",
                                 font=("Segoe UI", 13), corner_radius=8,
                                 command=lambda p=page: self.show_page(p))
            btn.pack(padx=8, pady=2, fill="x")
            self.nav_btns[page] = btn

        # Streak freeze display
        self.sb_freeze = ctk.CTkLabel(self.sidebar, text="🧊 Streak Freeze: 2",
                                       font=("Segoe UI", 10), text_color="#3498db")
        self.sb_freeze.pack(pady=4)

        # Quote
        quote_frame = ctk.CTkFrame(self.sidebar, fg_color="#1a1a2a", corner_radius=8)
        quote_frame.pack(padx=12, pady=8, side="bottom", fill="x")
        self.quote_lbl = ctk.CTkLabel(quote_frame, text=random.choice(MOTIVATIONAL_QUOTES),
                                       font=("Segoe UI", 10, "italic"), text_color="#888899",
                                       wraplength=180)
        self.quote_lbl.pack(padx=8, pady=8)

    def _build_topbar(self):
        topbar = ctk.CTkFrame(self.main, height=54, fg_color="#12121f", corner_radius=0)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        self.page_title = ctk.CTkLabel(topbar, text="Daily Habits",
                                        font=("Segoe UI", 18, "bold"), text_color="#ffffff")
        self.page_title.pack(side="left", padx=20)

        self.date_lbl = ctk.CTkLabel(topbar,
                                      text=date.today().strftime("%A, %B %d, %Y"),
                                      font=("Segoe UI", 12), text_color="#888899")
        self.date_lbl.pack(side="right", padx=20)

    # ─── HABITS PAGE ─────────────────────────────────────────────────────────

    def _build_habits_page(self):
        page = ctk.CTkFrame(self.page_frame, fg_color="transparent")
        self.pages["habits"] = page

        # Today's progress card
        prog_card = ctk.CTkFrame(page, fg_color="#1e1e2e", corner_radius=14, border_width=1, border_color="#333355")
        prog_card.pack(fill="x", pady=(0, 12))

        prog_top = ctk.CTkFrame(prog_card, fg_color="transparent")
        prog_top.pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkLabel(prog_top, text="Today's Progress", font=("Segoe UI", 13, "bold")).pack(side="left")
        self.progress_pct_lbl = ctk.CTkLabel(prog_top, text="0%", font=("Segoe UI", 13, "bold"),
                                              text_color="#2ecc71")
        self.progress_pct_lbl.pack(side="right")

        self.daily_progress_bar = ctk.CTkProgressBar(prog_card, height=14, corner_radius=7,
                                                       progress_color="#2ecc71")
        self.daily_progress_bar.pack(fill="x", padx=16, pady=(0, 8))
        self.daily_progress_bar.set(0)

        self.progress_sub_lbl = ctk.CTkLabel(prog_card, text="0 of 0 habits completed",
                                              font=("Segoe UI", 11), text_color="#888899")
        self.progress_sub_lbl.pack(padx=16, pady=(0, 10), anchor="w")

        # Active quest progress (if any)
        self.quest_progress_card = ctk.CTkFrame(page, fg_color="#1a1a2e", corner_radius=12,
                                                  border_width=1, border_color="#2a2a5e")
        self.quest_progress_lbl = ctk.CTkLabel(self.quest_progress_card, text="",
                                                font=("Segoe UI", 12), text_color="#a78bfa")
        self.quest_progress_lbl.pack(side="left", padx=12, pady=8)
        self.quest_prog_bar = ctk.CTkProgressBar(self.quest_progress_card, height=10,
                                                   progress_color="#a78bfa", width=200)
        self.quest_prog_bar.pack(side="left", padx=8)
        self.quest_prog_bar.set(0)
        self.quest_pct_lbl = ctk.CTkLabel(self.quest_progress_card, text="",
                                           font=("Segoe UI", 10), text_color="#888899")
        self.quest_pct_lbl.pack(side="left", padx=4)

        # Add button row
        btn_row = ctk.CTkFrame(page, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 8))

        ctk.CTkButton(btn_row, text="+ Add Habit", height=38, width=140,
                       fg_color="#7b1fa2", hover_color="#9c27b0",
                       font=("Segoe UI", 13, "bold"),
                       command=self.open_add_habit).pack(side="left")

        # Filter tabs
        self.habit_filter = ctk.StringVar(value="All")
        for cat in ["All", "Health", "Mind", "Work", "Creative"]:
            btn = ctk.CTkButton(btn_row, text=cat, width=70, height=32,
                                 fg_color="#1e1e2e", hover_color="#2a2a3e",
                                 font=("Segoe UI", 11),
                                 command=lambda c=cat: (self.habit_filter.set(c), self.refresh_habits()))
            btn.pack(side="left", padx=4)

        # Spells button
        ctk.CTkButton(btn_row, text="✨ Spells", height=32, width=90,
                       fg_color="#1a1040", hover_color="#2a1060",
                       font=("Segoe UI", 11), text_color="#a78bfa",
                       command=self.open_spells).pack(side="right")

        # Habits list
        self.habits_scroll = ctk.CTkScrollableFrame(page, fg_color="transparent", label_text="")
        self.habits_scroll.pack(fill="both", expand=True)

    def _build_character_page(self):
        page = ctk.CTkScrollableFrame(self.page_frame, fg_color="transparent")
        self.pages["character"] = page

        # Hero card
        hero_card = ctk.CTkFrame(page, fg_color="#1e1e2e", corner_radius=16, border_width=1, border_color="#333355")
        hero_card.pack(fill="x", pady=(0, 16))

        hero_top = ctk.CTkFrame(hero_card, fg_color="transparent")
        hero_top.pack(fill="x", padx=20, pady=20)

        self.char_avatar_lbl = EmojiLabel(hero_top, text="🧙", size=72)
        self.char_avatar_lbl.pack(side="left", padx=(0, 20))

        info_col = ctk.CTkFrame(hero_top, fg_color="transparent")
        info_col.pack(side="left", fill="x", expand=True)

        self.char_name_lbl = ctk.CTkLabel(info_col, text="Hero", font=("Segoe UI", 22, "bold"))
        self.char_name_lbl.pack(anchor="w")

        self.char_class_lbl = ctk.CTkLabel(info_col, text="Warrior", font=("Segoe UI", 14), text_color="#888899")
        self.char_class_lbl.pack(anchor="w")

        self.char_level_lbl = ctk.CTkLabel(info_col, text="Level 1", font=("Segoe UI", 16, "bold"), text_color="#f39c12")
        self.char_level_lbl.pack(anchor="w", pady=(4, 8))

        stats_row = ctk.CTkFrame(info_col, fg_color="transparent")
        stats_row.pack(anchor="w")
        self.char_hp_bar = StatBar(stats_row, "HP", "#e74c3c")
        self.char_hp_bar.pack(side="left", padx=(0, 12))
        self.char_mana_bar = StatBar(stats_row, "MP", "#3498db")
        self.char_mana_bar.pack(side="left", padx=(0, 12))
        self.char_xp_bar = StatBar(stats_row, "XP", "#9b59b6")
        self.char_xp_bar.pack(side="left")

        # Change avatar btn
        ctk.CTkButton(hero_top, text="Change Avatar", width=120, height=34,
                       fg_color="#1a1a2a", hover_color="#2a2a3a",
                       command=self.open_avatar_change).pack(side="right", anchor="n")

        # Stats grid
        stats_card = ctk.CTkFrame(page, fg_color="#1e1e2e", corner_radius=14, border_width=1, border_color="#333355")
        stats_card.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(stats_card, text="Character Stats", font=("Segoe UI", 14, "bold")).pack(padx=16, pady=(12, 8), anchor="w")

        stats_grid = ctk.CTkFrame(stats_card, fg_color="transparent")
        stats_grid.pack(padx=16, pady=(0, 12), fill="x")

        self.stat_labels = {}
        stat_defs = [
            ("total_completions", "Total Completions", "✅", "#2ecc71"),
            ("streak",            "Best Streak",       "🔥", "#f39c12"),
            ("gold",              "Total Gold Earned", "🪙", "#f1c40f"),
            ("quests_completed",  "Quests Done",       "📜", "#a78bfa"),
        ]
        for i, (key, name, emoji, color) in enumerate(stat_defs):
            card = ctk.CTkFrame(stats_grid, fg_color="#12121f", corner_radius=10, width=140, height=80)
            card.grid(row=0, column=i, padx=6, pady=4, sticky="ew")
            card.grid_propagate(False)
            stats_grid.columnconfigure(i, weight=1)
            ctk.CTkLabel(card, text=emoji, font=("Segoe UI", 20)).place(relx=0.5, rely=0.25, anchor="center")
            lbl = ctk.CTkLabel(card, text="0", font=("Segoe UI", 18, "bold"), text_color=color)
            lbl.place(relx=0.5, rely=0.6, anchor="center")
            ctk.CTkLabel(card, text=name, font=("Segoe UI", 9), text_color="#666688").place(relx=0.5, rely=0.85, anchor="center")
            self.stat_labels[key] = lbl

        # Equipment
        equip_card = ctk.CTkFrame(page, fg_color="#1e1e2e", corner_radius=14, border_width=1, border_color="#333355")
        equip_card.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(equip_card, text="Equipment", font=("Segoe UI", 14, "bold")).pack(padx=16, pady=(12, 8), anchor="w")
        self.equip_frame = ctk.CTkFrame(equip_card, fg_color="transparent")
        self.equip_frame.pack(padx=16, pady=(0, 12), fill="x")

        # Activity log
        log_card = ctk.CTkFrame(page, fg_color="#1e1e2e", corner_radius=14, border_width=1, border_color="#333355")
        log_card.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(log_card, text="Recent Activity", font=("Segoe UI", 14, "bold")).pack(padx=16, pady=(12, 4), anchor="w")
        self.log_frame = ctk.CTkFrame(log_card, fg_color="transparent")
        self.log_frame.pack(padx=16, pady=(0, 12), fill="x")

    def _build_shop_page(self):
        page = ctk.CTkFrame(self.page_frame, fg_color="transparent")
        self.pages["shop"] = page

        shop_header = ctk.CTkFrame(page, fg_color="#1a1a2a", corner_radius=12, border_width=1, border_color="#333355")
        shop_header.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(shop_header, text="🏪  Equipment Shop",
                     font=("Segoe UI", 18, "bold"), text_color="#f39c12").pack(side="left", padx=16, pady=12)
        self.shop_gold_lbl = ctk.CTkLabel(shop_header, text="🪙 0 gold",
                                           font=("Segoe UI", 14, "bold"), text_color="#f39c12")
        self.shop_gold_lbl.pack(side="right", padx=16)

        # Filter by rarity
        filter_row = ctk.CTkFrame(page, fg_color="transparent")
        filter_row.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(filter_row, text="Filter:", font=("Segoe UI", 11), text_color="#888899").pack(side="left")
        for rarity in ["All", "Common", "Uncommon", "Rare", "Epic", "Legendary"]:
            color = RARITY_COLORS.get(rarity.lower(), "#aaaaaa")
            btn = ctk.CTkButton(filter_row, text=rarity, width=80, height=28,
                                 fg_color="#1e1e2e", hover_color="#2a2a3e",
                                 font=("Segoe UI", 10), text_color=color)
            btn.pack(side="left", padx=3)

        self.shop_scroll = ctk.CTkScrollableFrame(page, fg_color="transparent")
        self.shop_scroll.pack(fill="both", expand=True)

        self._populate_shop()

    def _populate_shop(self):
        for w in self.shop_scroll.winfo_children():
            w.destroy()

        grid_frame = ctk.CTkFrame(self.shop_scroll, fg_color="transparent")
        grid_frame.pack(fill="x")

        for i, item in enumerate(EQUIPMENT_SHOP):
            col = i % 3
            row = i // 3
            rarity_color = RARITY_COLORS[item["rarity"]]
            owned = item["id"] in self.data["inventory"]
            equipped = item["id"] in self.data["equipped"]

            card = ctk.CTkFrame(grid_frame, fg_color="#1e1e2e", corner_radius=14,
                                 border_width=2, border_color=rarity_color if not owned else "#2a3a2a",
                                 width=200, height=200)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="ew")
            card.pack_propagate(False)
            grid_frame.columnconfigure(col, weight=1)

            EmojiLabel(card, text=item["emoji"], size=40).pack(pady=(14, 4))
            ctk.CTkLabel(card, text=item["name"], font=("Segoe UI", 12, "bold")).pack()
            ctk.CTkLabel(card, text=item["rarity"].capitalize(), font=("Segoe UI", 10),
                         text_color=rarity_color).pack()
            ctk.CTkLabel(card, text=f"+{item['val']} {item['stat'].upper()}",
                         font=("Segoe UI", 11), text_color="#a78bfa").pack()

            if equipped:
                ctk.CTkLabel(card, text="✅ Equipped", font=("Segoe UI", 10), text_color="#2ecc71").pack()
                ctk.CTkButton(card, text="Unequip", width=100, height=28,
                               fg_color="#1a3a1a", hover_color="#2a5a2a",
                               font=("Segoe UI", 11),
                               command=lambda iid=item["id"]: self.unequip_item(iid)).pack(pady=4)
            elif owned:
                ctk.CTkLabel(card, text="✓ Owned", font=("Segoe UI", 10), text_color="#2ecc71").pack()
                ctk.CTkButton(card, text="Equip", width=100, height=28,
                               fg_color="#1e3a1e", hover_color="#2a5a2a",
                               font=("Segoe UI", 11),
                               command=lambda iid=item["id"]: self.equip_item(iid)).pack(pady=4)
            else:
                ctk.CTkButton(card, text=f"🪙 {item['cost']}", width=100, height=28,
                               fg_color="#2a1a0a" if self.data["gold"] < item["cost"] else "#7b1fa2",
                               hover_color="#9c27b0",
                               font=("Segoe UI", 11, "bold"),
                               state="disabled" if self.data["gold"] < item["cost"] else "normal",
                               command=lambda it=item: self.buy_item(it)).pack(pady=4)

    def _build_quests_page(self):
        page = ctk.CTkScrollableFrame(self.page_frame, fg_color="transparent")
        self.pages["quests"] = page

        ctk.CTkLabel(page, text="📜  Quests", font=("Segoe UI", 18, "bold"), text_color="#a78bfa").pack(anchor="w", pady=(0, 12))

        self.quests_frame = ctk.CTkFrame(page, fg_color="transparent")
        self.quests_frame.pack(fill="x")
        self._populate_quests()

    def _populate_quests(self):
        for w in self.quests_frame.winfo_children():
            w.destroy()

        active_id = self.data.get("active_quest")

        for quest in QUESTS:
            is_active = active_id == quest["id"]
            completed = quest["id"] in [q for q in self.data.get("completed_quests", [])]

            card = ctk.CTkFrame(self.quests_frame, fg_color="#1e1e2e", corner_radius=14,
                                 border_width=2, border_color="#a78bfa" if is_active else "#333355")
            card.pack(fill="x", pady=6)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=12)

            EmojiLabel(row, text=quest["emoji"], size=40).pack(side="left", padx=(0, 12))

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(info, text=quest["name"], font=("Segoe UI", 14, "bold")).pack(anchor="w")
            ctk.CTkLabel(info, text=quest["desc"], font=("Segoe UI", 11), text_color="#888899").pack(anchor="w")
            ctk.CTkLabel(info, text=f"Reward: 🪙{quest['reward_gold']}  ✨{quest['reward_xp']} XP  |  Tasks needed: {quest['tasks']}",
                         font=("Segoe UI", 10), text_color="#a78bfa").pack(anchor="w", pady=(4, 0))

            if is_active:
                prog = self.data.get("quest_progress", 0)
                pct = min(1.0, prog / quest["tasks"])
                ctk.CTkProgressBar(card, height=8, progress_color="#a78bfa",
                                    corner_radius=4).pack(fill="x", padx=16, pady=(0, 4))
                ctk.CTkLabel(card, text=f"{prog} / {quest['tasks']} tasks",
                             font=("Segoe UI", 10), text_color="#888899").pack(padx=16, pady=(0, 8), anchor="w")

                bar = ctk.CTkProgressBar(card, height=8, progress_color="#a78bfa", corner_radius=4)
                bar.pack(fill="x", padx=16, pady=(0, 4))
                bar.set(pct)

                ctk.CTkButton(row, text="Active ✓", width=100, height=34,
                               fg_color="#1a1040", text_color="#a78bfa",
                               state="disabled").pack(side="right")
            elif not completed:
                ctk.CTkButton(row, text="Start Quest", width=100, height=34,
                               fg_color="#7b1fa2", hover_color="#9c27b0",
                               font=("Segoe UI", 11, "bold"),
                               state="disabled" if active_id else "normal",
                               command=lambda q=quest: self.start_quest(q)).pack(side="right")
            else:
                ctk.CTkLabel(row, text="✅ Done", font=("Segoe UI", 11), text_color="#2ecc71").pack(side="right")

    def _build_achievements_page(self):
        page = ctk.CTkScrollableFrame(self.page_frame, fg_color="transparent")
        self.pages["achievements"] = page

        ctk.CTkLabel(page, text="🏆  Achievements", font=("Segoe UI", 18, "bold"), text_color="#f39c12").pack(anchor="w", pady=(0, 12))

        self.ach_grid = ctk.CTkFrame(page, fg_color="transparent")
        self.ach_grid.pack(fill="x")

    # ─── PAGE NAVIGATION ─────────────────────────────────────────────────────


    # ─── ANIMATIONS ──────────────────────────────────────────────────────────

    def _animate_bar(self, bar, from_val, to_val, steps=20, delay=12, callback=None):
        """Smoothly animate a CTkProgressBar from from_val to to_val."""
        diff = to_val - from_val
        def _step(i):
            if i > steps:
                bar.set(max(0.0, min(1.0, to_val)))
                if callback:
                    callback()
                return
            # Ease-out cubic
            t = i / steps
            ease = 1 - (1 - t) ** 3
            bar.set(max(0.0, min(1.0, from_val + diff * ease)))
            self.after(delay, lambda: _step(i + 1))
        _step(0)

    def _animate_streak(self, old_val, new_val):
        """Count up the streak number with a bounce effect."""
        if old_val >= new_val:
            return
        def _step(current):
            if current > new_val:
                self.sb_streak.configure(text=f"🔥 {new_val}")
                # Flash orange
                self.sb_streak.configure(text_color="#ff4500")
                self.after(300, lambda: self.sb_streak.configure(text_color="#e67e22"))
                return
            self.sb_streak.configure(text=f"🔥 {current}")
            self.after(80, lambda: _step(current + 1))
        _step(old_val)

    def _float_popup(self, text, color, widget_ref):
        """Show a +XP / +Gold floating label that drifts up and fades out."""
        try:
            x = widget_ref.winfo_rootx() - self.winfo_rootx() + widget_ref.winfo_width() // 2
            y = widget_ref.winfo_rooty() - self.winfo_rooty()
        except Exception:
            x, y = self.winfo_width() // 2, self.winfo_height() // 2

        lbl = ctk.CTkLabel(self, text=text, font=("Segoe UI", 14, "bold"),
                           text_color=color, fg_color="transparent")
        lbl.place(x=x, y=y)

        steps = 30
        def _step(i):
            if i > steps:
                lbl.destroy()
                return
            t = i / steps
            new_y = y - int(60 * t)
            # Fade by blending color toward bg (#0d0d1a)
            lbl.place(x=x, y=new_y)
            self.after(18, lambda: _step(i + 1))
        _step(0)

    def _pulse_widget(self, widget, color_on, color_off, times=3):
        """Flash a widget border color to signal completion."""
        def _toggle(n, on):
            if n <= 0:
                try:
                    widget.configure(border_color=color_off)
                except Exception:
                    pass
                return
            try:
                widget.configure(border_color=color_on if on else color_off)
            except Exception:
                return
            self.after(140, lambda: _toggle(n - 1, not on))
        _toggle(times * 2, True)

    def _levelup_celebration(self):
        """Full-screen flash + big level text that zooms in then fades."""
        overlay = ctk.CTkFrame(self, fg_color="#f39c12", corner_radius=0)
        overlay.place(x=0, y=0, relwidth=1, relheight=1)

        lbl = ctk.CTkLabel(overlay,
                           text=f"⭐  LEVEL UP!  ⭐\nNow Level {self.data['level']}",
                           font=("Segoe UI", 44, "bold"), text_color="#0d0d1a")
        lbl.place(relx=0.5, rely=0.5, anchor="center")

        sub = ctk.CTkLabel(overlay, text="You're getting stronger!",
                           font=("Segoe UI", 18), text_color="#1a1a1a")
        sub.place(relx=0.5, rely=0.62, anchor="center")

        def _fade(step):
            if step <= 0:
                overlay.destroy()
                return
            alpha = step / 15
            # Simulate fade by cycling through dark bg color
            r = int(13 + (243 - 13) * alpha)
            g = int(13 + (156 - 13) * alpha)
            b = int(26 + (18  - 26) * alpha)
            try:
                overlay.configure(fg_color=f"#{r:02x}{g:02x}{b:02x}")
            except Exception:
                pass
            self.after(60, lambda: _fade(step - 1))

        self.after(1200, lambda: _fade(15))

    def _page_slide_in(self, page):
        """Slide page content in from right."""
        steps = 8
        def _step(i):
            if i > steps:
                page.place_forget()
                page.pack(fill="both", expand=True)
                return
            t = i / steps
            ease = 1 - (1 - t) ** 2
            offset = int((1 - ease) * 40)
            page.place(x=offset, y=0, relwidth=1, relheight=1)
            self.after(14, lambda: _step(i + 1))
        _step(0)

    def show_page(self, name):
        for p in self.pages.values():
            p.pack_forget()
        page = self.pages[name]
        self._page_slide_in(page)

        titles = {"habits":"Daily Habits","character":"Character","shop":"Equipment Shop",
                  "quests":"Quests","achievements":"Achievements"}
        self.page_title.configure(text=titles.get(name, name.capitalize()))

        for k, btn in self.nav_btns.items():
            btn.configure(fg_color="#1e1e3a" if k == name else "transparent")

        if name == "shop":
            self._populate_shop()
        elif name == "quests":
            self._populate_quests()
        elif name == "achievements":
            self._refresh_achievements()
        elif name == "character":
            self._refresh_character()

    # ─── DAILY RESET ─────────────────────────────────────────────────────────

    def daily_reset(self):
        today = str(date.today())
        if self.data["last_date"] != today:
            habits = self.data["habits"]
            all_done = all(h["done"] for h in habits.values()) if habits else False
            if all_done:
                self.data["streak"] += 1
            else:
                if self.data["freeze"] > 0:
                    self.data["freeze"] -= 1
                else:
                    self.data["streak"] = 0
            for h in habits.values():
                h["done"] = False
            self.data["last_date"] = today
            # Regen some HP/mana
            self.data["hp"] = min(self.data["max_hp"], self.data["hp"] + 10)
            self.data["mana"] = min(self.data["max_mana"], self.data["mana"] + 5)
            save_data(self.data)

    # ─── REFRESH ─────────────────────────────────────────────────────────────

    def refresh_all(self):
        d = self.data
        cls_info = CLASSES.get(d.get("char_class", "Warrior"), CLASSES["Warrior"])

        # Sidebar
        self.sb_avatar.configure(text=d["avatar"])
        self.sb_name.configure(text=d["char_name"])
        self.sb_class.configure(text=f"{cls_info['emoji']} {d.get('char_class','')}")
        self.sb_level.configure(text=f"Lvl {d['level']}")
        self.sb_hp.update(d["hp"], d["max_hp"])
        self.sb_mana.update(d["mana"], d["max_mana"])
        self.sb_gold.configure(text=f"🪙 {d['gold']}")
        self.sb_freeze.configure(text=f"🧊 Streak Freeze: {d['freeze']}")

        # ── Animated XP bar ──
        xp_need = xp_for_level(d["level"])
        old_xp = self.sb_xp.bar.get()
        new_xp = max(0.0, min(1.0, d["xp"] / xp_need))
        self.sb_xp.val_lbl.configure(text=f"{d['xp']}/{xp_need}")
        self._animate_bar(self.sb_xp.bar, old_xp, new_xp)

        # ── Animated streak counter ──
        try:
            old_streak = int(self.sb_streak.cget("text").replace("🔥 ", ""))
        except Exception:
            old_streak = 0
        if d["streak"] > old_streak:
            self._animate_streak(old_streak, d["streak"])
        else:
            self.sb_streak.configure(text=f"🔥 {d['streak']}")

        self.refresh_habits()
        self.check_achievements()

    def refresh_habits(self):
        for w in self.habits_scroll.winfo_children():
            w.destroy()

        habits = self.data["habits"]
        total = len(habits)
        done = sum(1 for h in habits.values() if h["done"])
        pct = done / total if total else 0

        old_pct = self.daily_progress_bar.get()
        self._animate_bar(self.daily_progress_bar, old_pct, pct)
        self.progress_pct_lbl.configure(text=f"{int(pct*100)}%",
                                         text_color="#2ecc71" if pct == 1 else "#f39c12")
        self.progress_sub_lbl.configure(text=f"{done} of {total} habits completed")

        # Quest progress
        if self.data.get("active_quest"):
            q = next((q for q in QUESTS if q["id"] == self.data["active_quest"]), None)
            if q:
                prog = self.data.get("quest_progress", 0)
                self.quest_progress_card.pack(fill="x", pady=(0, 8))
                self.quest_progress_lbl.configure(text=f"{q['emoji']} {q['name']}")
                self.quest_prog_bar.set(min(1.0, prog / q["tasks"]))
                self.quest_pct_lbl.configure(text=f"{prog}/{q['tasks']}")
        else:
            self.quest_progress_card.pack_forget()

        # Filter
        filt = self.habit_filter.get()
        shown = 0
        for name, info in habits.items():
            if filt != "All" and info.get("category", "Health") != filt:
                continue
            card = HabitCard(self.habits_scroll, name, info,
                             on_done=self.complete_habit,
                             on_delete=self.delete_habit,
                             on_edit=self.edit_habit)
            card.pack(fill="x", pady=4)
            shown += 1

        if shown == 0:
            empty = ctk.CTkFrame(self.habits_scroll, fg_color="#1e1e2e", corner_radius=12)
            empty.pack(fill="x", pady=20)
            ctk.CTkLabel(empty, text="🎯  No habits yet!\nClick '+ Add Habit' to begin your journey.",
                         font=("Segoe UI", 14), text_color="#888899").pack(pady=30)

    def _refresh_character(self):
        d = self.data
        cls_info = CLASSES.get(d.get("char_class", "Warrior"), CLASSES["Warrior"])
        self.char_avatar_lbl.configure(text=d["avatar"])
        self.char_name_lbl.configure(text=d["char_name"])
        self.char_class_lbl.configure(text=f"{cls_info['emoji']} {d.get('char_class','')} · {cls_info['bonus'].capitalize()} bonus")
        self.char_level_lbl.configure(text=f"Level {d['level']}")
        self.char_hp_bar.update(d["hp"], d["max_hp"])
        self.char_mana_bar.update(d["mana"], d["max_mana"])
        xp_need = xp_for_level(d["level"])
        self.char_xp_bar.update(d["xp"], xp_need)

        for key, lbl in self.stat_labels.items():
            lbl.configure(text=str(d.get(key, 0)))

        # Equipment
        for w in self.equip_frame.winfo_children():
            w.destroy()
        if self.data["equipped"]:
            for item_id in self.data["equipped"]:
                item = next((i for i in EQUIPMENT_SHOP if i["id"] == item_id), None)
                if item:
                    chip = ctk.CTkFrame(self.equip_frame, fg_color="#1a2a1a", corner_radius=8,
                                         border_width=1, border_color=RARITY_COLORS[item["rarity"]])
                    chip.pack(side="left", padx=4, pady=4)
                    ctk.CTkLabel(chip, text=f"{item['emoji']} {item['name']}", font=("Segoe UI", 11),
                                 text_color=RARITY_COLORS[item["rarity"]]).pack(padx=8, pady=4)
        else:
            ctk.CTkLabel(self.equip_frame, text="No equipment. Visit the Shop!",
                         font=("Segoe UI", 11), text_color="#888899").pack(anchor="w")

        # Activity log
        for w in self.log_frame.winfo_children():
            w.destroy()
        history = self.data.get("history", [])[-10:]
        for entry in reversed(history):
            ctk.CTkLabel(self.log_frame, text=entry, font=("Segoe UI", 11),
                         text_color="#888899", anchor="w").pack(anchor="w", pady=1)

    def _refresh_achievements(self):
        for w in self.ach_grid.winfo_children():
            w.destroy()
        unlocked = self.data.get("achievements", [])
        for i, ach in enumerate(ACHIEVEMENTS):
            earned = ach["id"] in unlocked
            col, row = i % 3, i // 3
            card = ctk.CTkFrame(self.ach_grid, fg_color="#1e1e2e" if earned else "#141420",
                                 corner_radius=12, border_width=2,
                                 border_color="#f39c12" if earned else "#333355",
                                 width=180, height=120)
            card.grid(row=row, column=col, padx=6, pady=6, sticky="ew")
            card.grid_propagate(False)
            self.ach_grid.columnconfigure(col, weight=1)

            EmojiLabel(card, text=ach["emoji"] if earned else "🔒", size=32).place(relx=0.5, rely=0.28, anchor="center")
            ctk.CTkLabel(card, text=ach["name"] if earned else "???",
                         font=("Segoe UI", 11, "bold"),
                         text_color="#f39c12" if earned else "#555577").place(relx=0.5, rely=0.6, anchor="center")
            ctk.CTkLabel(card, text=ach["desc"],
                         font=("Segoe UI", 9), text_color="#888899" if earned else "#333355",
                         wraplength=160).place(relx=0.5, rely=0.82, anchor="center")

    # ─── ACTIONS ─────────────────────────────────────────────────────────────

    def complete_habit(self, name):
        habit = self.data["habits"].get(name)
        if not habit or habit["done"]:
            return
        # Pulse the card green before refreshing
        for w in self.habits_scroll.winfo_children():
            if hasattr(w, 'name') and w.name == name:
                self._pulse_widget(w, "#2ecc71", "#333355", times=3)
                break

        difficulty = habit.get("difficulty", "medium")
        xp_gain = {"easy": 10, "medium": 20, "hard": 35}[difficulty]
        gold_gain = {"easy": 3, "medium": 5, "hard": 10}[difficulty]
        mana_gain = 5

        if self.data.get("xp_boost"):
            xp_gain = int(xp_gain * 1.5)
        if self.data.get("gold_boost"):
            gold_gain += 10
        if self.data.get("char_class") == "Rogue":
            gold_gain *= 2
        if self.data.get("char_class") == "Mage":
            mana_gain = 10

        self.data["xp"] += xp_gain
        self.data["gold"] += gold_gain
        self.data["mana"] = min(self.data["max_mana"], self.data["mana"] + mana_gain)
        self.data["total_completions"] += 1
        habit["done"] = True
        habit["streak"] = habit.get("streak", 0) + 1

        # Quest progress
        if self.data.get("active_quest"):
            self.data["quest_progress"] = self.data.get("quest_progress", 0) + 1
            quest = next((q for q in QUESTS if q["id"] == self.data["active_quest"]), None)
            if quest and self.data["quest_progress"] >= quest["tasks"]:
                self._complete_quest(quest)

        # Level up
        leveled = False
        while self.data["xp"] >= xp_for_level(self.data["level"]):
            self.data["xp"] -= xp_for_level(self.data["level"])
            self.data["level"] += 1
            self.data["max_hp"] += 5
            self.data["hp"] = self.data["max_hp"]
            leveled = True

        log_entry = f"{datetime.now().strftime('%m/%d %H:%M')} — Completed '{name}' (+{xp_gain}xp, +{gold_gain}g)"
        self.data["history"] = self.data.get("history", [])
        self.data["history"].append(log_entry)
        if len(self.data["history"]) > 50:
            self.data["history"] = self.data["history"][-50:]

        save_data(self.data)
        self.refresh_all()

        # ── Floating +XP / +Gold popup ──
        self.after(50, lambda: self._float_popup(
            f"+{xp_gain} XP   +{gold_gain}g", "#2ecc71", self.sb_xp.bar))

        if leveled:
            # ── Level up celebration overlay ──
            self.after(200, self._levelup_celebration)
        else:
            ToastNotification(self, f"+{xp_gain} XP  +{gold_gain} Gold", "✨", "#2ecc71")

    def _complete_quest(self, quest):
        self.data["gold"] += quest["reward_gold"]
        self.data["xp"] += quest["reward_xp"]
        self.data["quests_completed"] += 1
        self.data["active_quest"] = None
        self.data["quest_progress"] = 0
        completed = self.data.get("completed_quests", [])
        completed.append(quest["id"])
        self.data["completed_quests"] = completed
        ToastNotification(self, f"Quest Complete! +{quest['reward_gold']}g +{quest['reward_xp']}xp", "📜", "#a78bfa")

    def delete_habit(self, name):
        if messagebox.askyesno("Delete Habit", f"Delete '{name}'?", parent=self):
            del self.data["habits"][name]
            save_data(self.data)
            self.refresh_habits()

    def edit_habit(self, name):
        info = self.data["habits"][name].copy()
        info["name"] = name
        def _on_save(result):
            new_name = result["name"]
            old_info = self.data["habits"].pop(name)
            old_info.update(result)
            del old_info["name"]
            self.data["habits"][new_name] = old_info
            save_data(self.data)
            self.refresh_habits()
        AddHabitDialog(self, existing=info, on_save=_on_save)

    def open_add_habit(self):
        def _on_save(result):
            name = result.pop("name")
            if name not in self.data["habits"]:
                result["done"] = False
                result["streak"] = 0
                self.data["habits"][name] = result
                save_data(self.data)
                self.refresh_habits()
        AddHabitDialog(self, on_save=_on_save)

    def open_avatar_change(self):
        win = ctk.CTkToplevel(self)
        win.title("Change Avatar")
        win.geometry("360x160")
        win.grab_set()
        ctk.CTkLabel(win, text="Choose Avatar", font=("Segoe UI", 14, "bold")).pack(pady=10)
        row = ctk.CTkFrame(win, fg_color="transparent")
        row.pack()
        for av in AVATARS:
            img = _render_emoji_image(av, 32)
            if img:
                ctk.CTkButton(row, image=img, text="", width=44, height=44,
                              fg_color="transparent", hover_color="#2a2a3e",
                              command=lambda a=av: (self.data.update({"avatar": a}), save_data(self.data),
                                                    self.refresh_all(), win.destroy())).pack(side="left", padx=2)
            else:
                ctk.CTkButton(row, text=av, width=44, height=44, font=("Segoe UI", 22),
                              fg_color="transparent", hover_color="#2a2a3e",
                              command=lambda a=av: (self.data.update({"avatar": a}), save_data(self.data),
                                                    self.refresh_all(), win.destroy())).pack(side="left", padx=2)

    def open_spells(self):
        cls = self.data.get("char_class", "Warrior")
        spells = SPELLS.get(cls, [])
        win = ctk.CTkToplevel(self)
        win.title("Spells")
        win.geometry("400x320")
        win.grab_set()
        ctk.CTkLabel(win, text=f"✨ {cls} Spells", font=("Segoe UI", 16, "bold")).pack(pady=12)
        ctk.CTkLabel(win, text=f"Mana: {self.data['mana']} / {self.data['max_mana']}",
                     font=("Segoe UI", 12), text_color="#3498db").pack()
        for spell in spells:
            card = ctk.CTkFrame(win, fg_color="#1e1e2e", corner_radius=10, border_width=1, border_color="#333355")
            card.pack(padx=16, pady=6, fill="x")
            row2 = ctk.CTkFrame(card, fg_color="transparent")
            row2.pack(fill="x", padx=12, pady=8)
            EmojiLabel(row2, text=spell["emoji"], size=28).pack(side="left")
            info = ctk.CTkFrame(row2, fg_color="transparent")
            info.pack(side="left", padx=8, fill="x", expand=True)
            ctk.CTkLabel(info, text=spell["name"], font=("Segoe UI", 12, "bold")).pack(anchor="w")
            ctk.CTkLabel(info, text=spell["desc"], font=("Segoe UI", 10), text_color="#888899").pack(anchor="w")
            can_cast = self.data["mana"] >= spell["cost"]
            ctk.CTkButton(row2, text=f"Cast ({spell['cost']} MP)", width=110, height=30,
                          fg_color="#1a1040" if can_cast else "#1a1a1a",
                          hover_color="#2a1060", state="normal" if can_cast else "disabled",
                          command=lambda s=spell, w=win: self._cast_spell(s, w)).pack(side="right")

    def _cast_spell(self, spell, win):
        self.data["mana"] -= spell["cost"]
        effect = spell["effect"]
        msg = ""
        if effect == "xp_boost":
            self.data["xp_boost"] = True
            msg = "XP boost active for today!"
        elif effect == "extra_freeze":
            self.data["freeze"] += 1
            msg = "Extra streak freeze added!"
        elif effect == "heal":
            heal = 20
            self.data["hp"] = min(self.data["max_hp"], self.data["hp"] + heal)
            msg = f"Healed {heal} HP!"
        elif effect == "gold_boost":
            self.data["gold_boost"] = True
            msg = "Gold boost active!"
        elif effect == "steal_gold":
            g = 15
            self.data["gold"] += g
            msg = f"Stole {g} gold!"
        elif effect in ("auto_complete", "free_complete"):
            undone = [n for n, h in self.data["habits"].items() if not h["done"]]
            if undone:
                target = random.choice(undone)
                self.data["habits"][target]["done"] = True
                self.data["total_completions"] += 1
                msg = f"Auto-completed '{target}'!"
        save_data(self.data)
        self.refresh_all()
        win.destroy()
        ToastNotification(self, msg, spell["emoji"], "#a78bfa")

    def buy_item(self, item):
        if self.data["gold"] < item["cost"]:
            return
        self.data["gold"] -= item["cost"]
        self.data["inventory"].append(item["id"])
        save_data(self.data)
        self.refresh_all()
        self._populate_shop()
        ToastNotification(self, f"Bought {item['name']}!", item["emoji"], RARITY_COLORS[item["rarity"]])

    def equip_item(self, item_id):
        if item_id not in self.data["equipped"]:
            self.data["equipped"].append(item_id)
        save_data(self.data)
        self._populate_shop()

    def unequip_item(self, item_id):
        if item_id in self.data["equipped"]:
            self.data["equipped"].remove(item_id)
        save_data(self.data)
        self._populate_shop()

    def start_quest(self, quest):
        self.data["active_quest"] = quest["id"]
        self.data["quest_progress"] = 0
        save_data(self.data)
        self._populate_quests()
        self.refresh_habits()
        ToastNotification(self, f"Quest started: {quest['name']}!", quest["emoji"], "#a78bfa")

    def check_achievements(self):
        unlocked = self.data.get("achievements", [])
        for ach in ACHIEVEMENTS:
            if ach["id"] not in unlocked:
                try:
                    if ach["condition"](self.data):
                        unlocked.append(ach["id"])
                        self.data["achievements"] = unlocked
                        save_data(self.data)
                        ToastNotification(self, f"Achievement: {ach['name']}!", ach["emoji"], "#f39c12")
                except:
                    pass






# ─── ENTRY POINT ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = HabitHeroApp()
    app.mainloop()