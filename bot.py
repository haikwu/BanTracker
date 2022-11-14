import math
import time
import json
import requests as reqs
from colorama import Fore

import discord
from discord.ext import tasks
from discord.ext import commands

bot = commands.Bot(command_prefix="nya~", intents=discord.Intents.default())

with open("config.json") as conf:
    config = json.load(conf)
    channel_id = config["Channel"]
    api_keys = config["API-Keys"]
    bot_token = config["Token"]

# API Key checks
for key in api_keys:
    key_check = reqs.get(
        "https://api.hypixel.net/punishmentstats", headers={"API-Key": key}
    ).json()
    if "cause" in key_check:
        print(f"{Fore.YELLOW}{key} is an invalid API Key! It is no longer being used.{Fore.RESET}")
        api_keys.remove(key)

if not api_keys:
    print(f"{Fore.RED}No usable API Keys were found. The bot will not attempt to run without API Keys.{Fore.RESET}")
    exit()

global owd_bans, ostaff_bans, update_delay
owd_bans = None
ostaff_bans = None
update_delay = (1 / len(api_keys)) * 0.5


#Startup
@bot.event
async def on_ready():
    global channel
    channel = bot.get_channel(channel_id)
    print(f"Logging channel set to {channel.name}")
    checkloop.start()
    print(f"{Fore.LIGHTGREEN_EX}Checker has started!{Fore.RESET}")


# The actual checker
@tasks.loop(seconds=0.1)
async def checkloop():
    global update_delay
    for key in api_keys:
        global owd_bans, ostaff_bans
        curr_stats = reqs.get(
            "https://api.hypixel.net/punishmentstats", headers={"API-Key": key}
        ).json()
        wd_bans = curr_stats["watchdog_total"]
        staff_bans = curr_stats["staff_total"]
        if owd_bans != None and ostaff_bans != None:
            wban_dif = wd_bans - owd_bans
            sban_dif = staff_bans - ostaff_bans

            if wban_dif > 0:
                embed = discord.Embed(
                    color=discord.Color.from_rgb(247, 57, 24),
                    description=f"<t:{math.floor(time.time())}:R>",
                ).set_author(name=f"Watchdog banned {wban_dif} player(s)!")
                await channel.send(embed=embed)

            if sban_dif > 0:
                embed = discord.Embed(
                    color=discord.Color.from_rgb(247, 229, 24),
                    description=f"<t:{math.floor(time.time())}:R>",
                ).set_author(name=f"Staff banned {sban_dif} player(s)!")
                await channel.send(embed=embed)

        owd_bans = wd_bans
        ostaff_bans = staff_bans

        time.sleep(update_delay)


bot.run(bot_token)
