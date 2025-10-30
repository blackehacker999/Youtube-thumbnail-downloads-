import logging
import requests
import sqlite3
import os
import re
import json
import time
import sys
import random
from urllib.parse import urlparse, parse_qs
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from datetime import datetime, timedelta
import asyncio

# ===================[ 🎨 Terminal Colors ]===================
class Colors:
    GREEN = '\033[92m'
    LIGHT_GREEN = '\033[92m'
    DARK_GREEN = '\033[32m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


# ===================[ 🔐 TOKEN LOADER ]===================
def read_token_from_txt():
    """Read Telegram Bot Token securely from token.txt"""
    try:
        if os.path.exists('token.txt'):
            with open('token.txt', 'r') as f:
                token = f.read().strip()
                if token:
                    print(f"{Colors.GREEN}✅ Token loaded from token.txt{Colors.END}")
                    return token

        print(f"{Colors.YELLOW}⚠️ token.txt not found! Creating new one...{Colors.END}")
        token = input(f"{Colors.GREEN}🤖 Enter your Telegram Bot Token: {Colors.END}").strip()

        with open('token.txt', 'w') as f:
            f.write(token)

        print(f"{Colors.GREEN}✅ token.txt created successfully!{Colors.END}")
        return token

    except Exception as e:
        print(f"{Colors.RED}❌ Error reading token: {e}{Colors.END}")
        sys.exit(1)


# ===================[ ⚙️ CONFIGURATION ]===================
BOT_TOKEN = read_token_from_txt()
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB Telegram upload limit
USER_REQUESTS = {}
MAX_REQUESTS_PER_MINUTE = 5
MAX_REQUESTS_PER_HOUR = 30
VOTES_DB = 'votes.db'
os.makedirs('temp_thumbnails', exist_ok=True)


# ===================[ 🎬 BANNER DISPLAY ]===================
def show_green_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"""{Colors.GREEN}{Colors.BOLD}
  █████╗ ███╗   ███╗ █████╗ ██████╗      ██╗██╗████████╗
 ██╔══██╗████╗ ████║██╔══██╗██╔══██╗     ██║██║╚══██╔══╝
 ███████║██╔████╔██║███████║██████╔╝     ██║██║   ██║   
 ██╔══██║██║╚██╔╝██║██╔══██║██╔══██╗██   ██║██║   ██║   
 ██║  ██║██║ ╚═╝ ██║██║  ██║██║  ██║╚█████╔╝██║   ██║   
 ╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚════╝ ╚═╝   ╚═╝   
{Colors.END}

{Colors.LIGHT_GREEN}{Colors.BOLD}
     🎬 ADVANCED YOUTUBE THUMBNAIL BOT PRO 🎬
{Colors.END}

{Colors.DARK_GREEN}
    ✨ Created by Cyber Amarjit ✨
    😈 Black Devil | Ultimate Edition
{Colors.END}

{Colors.YELLOW}
    📊 Version: 5.0 ULTRA PRO
    🔧 System: Termux/PC Compatible
    🕐 Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
{Colors.END}
""")


# ===================[ 🧩 MAIN BOT CLASS ]===================
class AdvancedYouTubeBot:
    def __init__(self):
        self.quality_names = {
            'maxres': '🎨 Max Resolution (1280x720)',
            'sd': '📺 SD Quality (640x480)',
            'hq': '🖼️ HQ (480x360)',
            'mq': '📱 MQ (320x180)',
            'default': '⚡ Default (120x90)'
        }
        self.init_databases()

    def init_databases(self):
        """Initialize SQLite DBs"""
        conn = sqlite3.connect('bot_stats.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    total_requests INTEGER DEFAULT 0,
                    last_activity TEXT,
                    created_at TEXT)''')
        conn.commit()
        conn.close()

        conn = sqlite3.connect(VOTES_DB)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS votes (
                    user_id INTEGER PRIMARY KEY,
                    vote_count INTEGER DEFAULT 0,
                    last_vote_time TEXT,
                    total_votes INTEGER DEFAULT 0)''')
        conn.commit()
        conn.close()

    def extract_video_id(self, url):
        """Extract video ID"""
        patterns = [
            r'youtube\.com/watch\?v=([^&#]+)',
            r'youtu\.be/([^&#]+)',
            r'youtube\.com/embed/([^&#]+)'
        ]
        for p in patterns:
            m = re.search(p, url)
            if m:
                return m.group(1)
        return None

    def get_youtube_thumbnails(self, video_id):
        base = "https://img.youtube.com/vi/"
        return {k: f"{base}{video_id}/{k}default.jpg" for k in self.quality_names}

    def download_thumbnail(self, url, path):
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                with open(path, 'wb') as f:
                    f.write(r.content)
                return True
            return False
        except Exception:
            return False


bot = AdvancedYouTubeBot()


# ===================[ 🔹 HANDLERS ]===================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = f"""
🎬 *Welcome {user.first_name}!*  

Send any YouTube video link to download its thumbnail.

✅ Example:
`https://youtu.be/dQw4w9WgXcQ`

🔥 Features:
• Multiple quality thumbnails  
• Fast download system  
• Secure and premium performance  
"""
    await update.message.reply_text(text, parse_mode='Markdown')


async def handle_youtube(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    user = update.effective_user
    video_id = bot.extract_video_id(url)
    if not video_id:
        await update.message.reply_text("❌ Invalid YouTube link.")
        return
    thumbs = bot.get_youtube_thumbnails(video_id)
    keyboard = [
        [InlineKeyboardButton(name, url=link)]
        for name, link in thumbs.items()
    ]
    await update.message.reply_text(
        f"🎞️ Thumbnails for `{video_id}`:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ===================[ 🚀 MAIN FUNCTION ]===================
def main():
    show_green_banner()
    print(f"{Colors.GREEN}🚀 Starting Advanced YouTube Thumbnail Bot...{Colors.END}")
    time.sleep(1)

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_youtube))

    logging.basicConfig(level=logging.INFO)
    print(f"{Colors.GREEN}✅ BOT STARTED SUCCESSFULLY! Ready to serve.{Colors.END}")
    app.run_polling()


if __name__ == "__main__":
    main()
