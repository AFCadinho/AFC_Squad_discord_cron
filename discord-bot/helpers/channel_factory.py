import discord

class ChannelFactory:
    def __init__(self, bot) -> None:
        self.bot = bot

    async def _base(self, guild: discord.Guild, name, category_id=None) -> discord.TextChannel | None:
        channel_name = name
        discord_category = None
        text_channel = None

        if not guild:
            return None

        if category_id:
            discord_category = discord.utils.get(guild.categories, id=category_id)
            text_channel = await guild.create_text_channel(channel_name, category=discord_category)
        else:
            return

        return text_channel

    async def tournament_match(self, guild: discord.Guild, users: list, category_id):
        if len(users) != 2:
            return False
        
        if not guild:
            return
        
        discord_id1 = users[0].discord_id
        discord_id2 = users[1].discord_id


        discord_user1 = guild.get_member(discord_id1)
        discord_user2 = guild.get_member(discord_id2)

        if not discord_user1 or not discord_user2:
            return

        
        channel_name = f"{discord_user1.display_name}-vs-{discord_user2.display_name}"
        text_channel = await self._base(guild, channel_name, category_id)
        if text_channel:
            return text_channel.name
        
        return None
