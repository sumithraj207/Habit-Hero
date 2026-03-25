# ─── HabitHero AI Configuration ───────────────────────────────────────────────
#
# The AI Mentor (Aldric) uses Groq's FREE API to power habit suggestions,
# progress analysis, and custom quest generation.
#
# HOW TO SET UP (takes ~30 seconds, no credit card needed):
#   1. Go to https://console.groq.com and sign up for free
#   2. Click "API Keys" → "Create API Key"
#   3. Copy your key (starts with gsk_...)
#   4. Copy this file:   cp .env.example .env
#   5. Paste your key below and save
#   6. Restart HabitHero — Aldric will greet you!
#
# Your .env file is gitignored — it NEVER gets uploaded to GitHub.
# ──────────────────────────────────────────────────────────────────────────────

GROQ_API_KEY=your_groq_api_key_here
