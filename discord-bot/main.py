import discord
from discord.ext import commands
import logging
import os
import asyncio
from flask import Flask
import threading

# Load environment variables
BOT_TOKEN = str(os.getenv("DISCORD_TOKEN"))
GUILD_ID = os.getenv("GUILD_ID")

# Flask web server setup
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive!"

def run_webserver():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w"),
        logging.StreamHandler()
    ]
)

logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Bot setup
intents = discord.Intents.all()
bot = commands.Bot(
    command_prefix="/",
    intents=intents
)

@bot.event
async def on_ready():
    """Handles the event when the Discord bot has successfully connected and is ready."""
    logging.info("Loaded cogs: %s", list(bot.cogs.keys()))
    logging.info(f"We have successfully logged in as {bot.user}")
    logging.info("------------------------------------------------")

    await bot.change_presence(activity=discord.Game(name="Pokemon Blaze Online"))
    print(f"\nWe have successfully logged in as {bot.user}.\n------------------------------------------------")
    
    # Sync the command tree for slash commands
    await bot.tree.sync()
    print("Slash commands synced")
    logging.info("Slash commands synced")

async def load_all_extensions():
    """Loads all Python files ending with '.py' in the 'cogs' directory as extensions."""
    if not os.path.exists("./cogs"):
        logging.warning("No 'cogs' directory found. Skipping extension loading.")
        return

    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                logging.info(f"Successfully loaded extension: {filename}")
            except Exception as e:
                logging.error(f"Failed to load extension {filename}: {e}")

async def main():
    """Starts the Discord bot by loading all extensions and then running the bot with the given token."""
    # Start Flask web server in a new thread
    threading.Thread(target=run_webserver).start()

    async with bot:
        await load_all_extensions()
        await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
