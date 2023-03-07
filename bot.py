import math
import json
import time
import discord
import logging
import requests as reqs
from discord.ext import tasks


class JSONConfig:
    def __init__(self, file_name: str) -> None:
        self.file_name = file_name
        with open(file_name) as conf:
            self.config = json.load(conf)

    def update(self, key: str, value: any):
        self.config[key] = value
        with open(self.file_name, "w") as conf:
            json.dump(self.config, conf, indent=4)


class BanTracker:
    def __init__(self) -> None:
        self.owd_bans = None
        self.ostaff_bans = None
        self.session = reqs.Session()
        self.session.headers.update({"User-Agent": "i am a professional boy kisser"}) #The user agent can be anything, plancke only blocks the default requests user agent

    def check_bans(self):
        curr_stats = self.session.get(
            'https://api.plancke.io/hypixel/v1/punishmentStats'
        ).json().get('record')
        wd_bans = curr_stats.get("watchdog_total")
        staff_bans = curr_stats.get("staff_total")
        embeds = []

        if self.owd_bans != None and self.ostaff_bans != None:
            wban_dif = wd_bans - self.owd_bans
            sban_dif = staff_bans - self.ostaff_bans

            if wban_dif > 0:
                embed = discord.Embed(
                    color=discord.Color.from_rgb(247, 57, 24),
                    description=f"<t:{math.floor(time.time())}:R>",
                ).set_author(name=f"Watchdog banned {wban_dif} player{'s'[:wban_dif^1]}!")
                embeds.append(embed)

            if sban_dif > 0:
                embed = discord.Embed(
                    color=discord.Color.from_rgb(247, 229, 24),
                    description=f"<t:{math.floor(time.time())}:R>",
                ).set_author(name=f"Staff banned {sban_dif} player{'s'[:sban_dif^1]}!")
                embeds.append(embed)

        self.owd_bans = wd_bans
        self.ostaff_bans = staff_bans
        return embeds


class BanTrackerBot(discord.Client):
    def __init__(self, intents: discord.Intents) -> None:
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)
        self.jsonconfig = JSONConfig("config.json")
        self.bantracker = BanTracker()
        self.logger = logging.getLogger('discord')

        @self.event
        async def on_ready():
            self.channel_ids = self.jsonconfig.config.get("channels")
            for guild in self.guilds:
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
            self.logger.info(f"Synced commands with {len(self.guilds)} guild{'s'[:len(self.guilds)^1]}.")
            check_loop.start()

        @self.event
        async def on_guild_join(guild):
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            self.logger.info(f"Synced commands with {guild.name}.")

        @self.tree.command()
        async def subscribe(interaction: discord.Interaction):
            """Subscribes the channel which the command is ran in to the Ban Tracker"""
            if interaction.channel_id not in self.channel_ids:
                self.channel_ids.append(interaction.channel_id)
                self.jsonconfig.update("channels", self.channel_ids)
                self.logger.info(f"{interaction.channel.name} in {interaction.guild.name} was subscribed.")
                await interaction.response.send_message("> This channel is now subscribed.")
            else:
                await interaction.response.send_message("> This channel is already subscribed.")

        @self.tree.command()
        async def unsubscribe(interaction: discord.Interaction):
            """Unsubscribes the channel which the command is ran in to the Ban Tracker"""
            self.channel_ids.remove(interaction.channel_id)
            self.jsonconfig.update("channels", self.channel_ids)
            self.logger.info(f"{interaction.channel.name} in {interaction.guild.name} was unsubscribed.")
            await interaction.response.send_message("> This channel is no longer subscribed.")

        @tasks.loop(seconds=0.1)
        async def check_loop():
            bans = self.bantracker.check_bans()
            if bans:
                [await self.get_channel(channel_id).send(embed=embed) for embed in bans for channel_id in self.channel_ids]


if __name__ == "__main__":
    discordbot = BanTrackerBot(discord.Intents.default())
    discordbot.run(discordbot.jsonconfig.config.get("token"))
