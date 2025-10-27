import discord
import logging

log = logging.getLogger(__name__)

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
            return None
        
        discord_id1 = users[0].discord_id
        discord_id2 = users[1].discord_id


        discord_user1 = guild.get_member(discord_id1)
        discord_user2 = guild.get_member(discord_id2)

        if not discord_user1 or not discord_user2:
            return None

        
        channel_name = f"{discord_user1.display_name}-vs-{discord_user2.display_name}"
        text_channel = await self._base(guild, channel_name, category_id)
        if text_channel:
            return text_channel.name
        
        return None
    

    async def tournament_rewards(self, guild: discord.Guild, users: list, category_id, slug):
        if not guild:
            return
        
        text_channels = []
        
        for user in users:
            discord_user = guild.get_member(user.discord_id)
            if not discord_user:
                continue

            channel_name = f"{discord_user.display_name}-reward-{slug}"

            existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
            if existing_channel:
                text_channels.append(existing_channel)
                log.info(f"Skipping channel creation. Reason: Reward Channel already exists for user {user.username}.")
                continue 

            text_channel = await self._base(guild, channel_name, category_id)

            if text_channel:
                await text_channel.send(
                    f"🎉 Thank you for participating {discord_user.mention}! "
                    "This is your reward channel. A staff member will contact you shortly."
                )
                text_channels.append(text_channel)

        return len(text_channels)


class ChannelManager:
    def __init__(self, bot) -> None:
        self.bot = bot

    async def __get_category_channels(self, guild: discord.Guild, category_id) -> list:
        if not guild:
            return []

        discord_category = discord.utils.get(guild.categories, id=category_id)
        if not discord_category:
            return []
        
        channels = discord_category.channels

        return channels

    async def get_channel_names(self, guild: discord.Guild, category_id):
        channel_names = []

        channels = await self.__get_category_channels(guild, category_id)
        for channel in channels:
            channel_names.append(channel.name)

        return channel_names
    

class ChannelDestroyer:
    def __init__(self, bot) -> None:
        self.bot = bot

    async def __get_category_channels(self, guild: discord.Guild, category_id) -> list:
        if not guild:
            return []

        discord_category = discord.utils.get(guild.categories, id=category_id)
        if not discord_category:
            return []
        
        channels = discord_category.channels

        return channels
    
    async def delete_channels(self, guild: discord.Guild, category_id):
        channels = await self.__get_category_channels(guild, category_id)
        for channel in channels:
            if isinstance(channel, discord.TextChannel):
                await channel.delete()