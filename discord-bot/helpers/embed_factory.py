import discord
from datetime import datetime, timezone

class EmbedFactory:
    def __init__(self, bot) -> None:
        self.bot = bot

    def _base(self, title, description, color) -> discord.Embed:
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.display_avatar)
        return embed

    def success(self, message: str):
        """For confirmations or positive actions"""
        return self._base("✅ Success", message, discord.Color.green())

    def error(self, message: str):
        """For errors or failed actions"""
        return self._base("❌ Error", message, discord.Color.red())

    def warning(self, message: str):
        """For risky actions or alerts"""
        return self._base("⚠️ Warning", message, discord.Color.gold())

    def info(self, message: str):
        """For neutral notifications or info"""
        return self._base("ℹ️ Information", message, discord.Color.blurple())