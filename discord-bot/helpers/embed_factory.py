import discord
from datetime import datetime, timezone
from .datetime_helper import convert_datetime

class EmbedFactory:
    def __init__(self, bot) -> None:
        self.bot = bot

    def _base(self, title, description=None, color=None, show_footer=True) -> discord.Embed:
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        
        if show_footer:
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
    
    def giveaway_embed(self, prize: str, end_time: datetime, participants: int = 0, winners: int=1):
        """Create a simple giveaway-style embed."""
        end_abs = convert_datetime(end_time, "f")  # e.g. November 2, 2025 at 8:39 PM
        end_rel = convert_datetime(end_time, "R")  # e.g. (in 2 days)

        embed = self._base(
            title=prize,
            color=discord.Color.red(),
            show_footer=False
        )

        # 🧩 Compact single-line layout
        embed.description = (
            f"🏆 **Winners:** {winners}\n"
            f"🎯 **Ends:** {end_abs} ({end_rel})\n"
            f"👥 **Participants:** {participants}"
        )
        
        return embed