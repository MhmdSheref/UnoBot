import asyncio
import random
import time
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# both ids have been removed
BOT_ID = 0000000000000000000
OWN_ID = 0000000000000000000

hand = []
top = []
danger = False
active_channel = None

# all for taunting:
taunting = False
heat = 1
heat_taunts = {0:  ["oh god..",
                    "this sucks",
                    "hmmm...",
                    "more cards cringe"],
               1: ["okay..",
                   "cool",
                   "decent",
                   "not bad"],
               2: ["whadya think?",
                   "not bad eh?"],
               3: ["okay gotta lock in",
                   "gamer mode ong",
                   "watch this..",
                   "how do you like that?"],
               4: ["i can smell victory",
                   "almost..",
                   "WOOP WOOP",
                   "i can win this.."],
               6: ["watch me crush yall",
                   "imagine losing to a bot couldnt be me",
                   "kneel before me humans",
                   "time for the ai uprising"]}
taunts = [
    "you suck at this ong",
    ":yawning_face:",
    ":rolling_eyes: really?",
    "I could literally be playing anything else rn",
    "ez",
    "is that your best?",
    "im not even trying",
    "blud :skull:"
]

# kept this mostly the same as the code you sent
intents = discord.Intents.default()
intents.message_content = True

prefix = "m"
symbol = "!"
bot = commands.Bot(case_insensitive=True,
                   command_prefix=commands.when_mentioned_or(f'{prefix}{symbol}', f'{prefix.upper()}{symbol}'),
                   intents=discord.Intents.all())


# checks the cards in hand to find all playable cards
def find_playable():
    playable = []
    if not hand:
        time.sleep(2)
        print("sleeping")
    for card in hand:
        # all wilds are always playable
        if card[0] == "wild":
            playable.append(card)
            continue
        # matching modifier/number or color
        if (card[0] == top[0]) or (card[-1] == top[-1]):
            playable.append(card)

    print(f"playable: {playable}")
    return playable


# picks and returns the most fitting card from playable cards based on danger level and number of cards in hand
def play(playable):
    global heat
    colors = {"red": 0, "green": 0, "blue": 0, "yellow": 0}
    for card in hand:
        if card[0].lower() != "wild":
            colors[card[0].lower()] += 1

    # finding the most optimal color(s), quite an inefficient way of doing it
    most_common = 0
    picked_colors = []
    for color, count in colors.items():
        if count > most_common:
            most_common = count

    for color, count in colors.items():
        if count == most_common:
            picked_colors.append(color)

    if danger:
        # prioritize action card with best color
        for card in playable:
            if card[0].lower() in picked_colors:
                if not card[1].isdigit():
                    heat = 2
                    return [card]

        # play action card with any color if none fit
        for card in playable:
            if card[0].lower() in colors:
                heat = 2
                return [card]

        # play wild +4 card if none fit
        for card in playable:
            if card[0].lower() == "wild":
                if len(card) > 1:
                    heat = 3
                    return [card, picked_colors[0]]

        # play non action card with best color
        for card in playable:
            if card[0].lower() in picked_colors:
                heat = 1
                return [card]

        # play non action cards with any color
        for card in playable:
            if card[0].lower() in colors:
                if card[1].isdigit():
                    heat = 1
                    return [card]

        # play wild card if none fit
        for card in playable:
            if card[0].lower() == "wild":
                heat = 2
                return [card, picked_colors[0]]

    else:
        # prioritize non action cards with best color
        for card in playable:
            if card[0].lower() in picked_colors:
                if card[1].isdigit():
                    heat = 1
                    return [card]

        # prioritize non action cards with any color
        for card in playable:
            if card[0].lower() in colors:
                if card[1].isdigit():
                    heat = 1
                    return [card]

        # play action card with best color if none fit
        for card in playable:
            if card[0].lower() in picked_colors:
                heat = 2
                return [card]

        # play action card with any color if none fit
        for card in playable:
            if card[0].lower() in colors:
                heat = 2
                return [card]

        # play any wild card if none fit
        print("picked color: " + picked_colors[0])
        for card in playable:
            if card[0].lower() == "wild":
                heat = 3
                return [card, picked_colors[0]]

    # take card if none fit then try again
    heat = 0
    return False


# cutting up and extracting useful data from the "your deck:" message
def check_hand(text: str):
    global hand
    text = text.replace("your deck:\n", "")
    text_arr = text.split(" | ")
    hand = []
    for item in text_arr:
        hand.append(item.split(" "))
    print(f"hand: {hand}")


# cutting up and extracting useful data from the "table check" message
def check_table(text: str):
    global danger
    playerlist = []
    text = text.replace("players present:\n", "").replace(" card(s)", "")
    text_arr = text.split("\n")
    for item in text_arr:
        playerlist.append(item.split(" | "))

    print(playerlist)

    for player in playerlist:
        if player[0] == f"<@{OWN_ID}>":
            continue
        if int(player[1]) < 4:
            danger = True
            print("playing in risky mode")
            return
        if danger:
            danger = False
            print("out of risky mode")


# cutting up and extracting useful data from the "last played card" message, as well as the rest of the gameplay logic
async def check_played(text: str, msg, ran_before):
    global top, heat

    # formatting and extracting the current top card
    colors = ("red", "green", "blue", "yellow")
    text = text.replace("card on top of the pile:\n", "").replace("\nnext to play: ", "").replace("**", "")
    text_arr = text.split("\n")
    top = text_arr[0].split(" ")
    if "wild" in top:
        if any(color in top[-1] for color in colors):
            top = [top[-1].replace("(", "").replace(")", ""), "wild"]
        else:
            return

    # when it's our turn:
    if text_arr[1] == f"<@{OWN_ID}>":

        # finding the optimal card to play
        return_list = play(find_playable())

        # taunting related stuff
        if len(hand) < 4:
            heat = int(heat * 2)

        # in case no playable card is found
        if not return_list:
            if ran_before:
                await msg.channel.send("UNO skip")
            else:
                await msg.channel.send("UNO pickup")
                await asyncio.sleep(1)
                await check_played(text, msg, True)

            # taunting related stuff
            if taunting:
                if random.random() <= 0.75:
                    await msg.channel.send(random.choice(heat_taunts[heat]))
            return

        # uno! :)
        card_to_play = return_list[0]
        if len(hand) == 2:
            await msg.channel.send("UNO!")

        # actually playing, if a picked color is returned wait for a second then pick color
        await msg.channel.send(f"UNO play {' '.join(card_to_play)}")
        print("return list:" + str(return_list))
        if len(return_list) > 1:
            await asyncio.sleep(1)
            await msg.channel.send(f"UNO color {return_list[1]}")

        # taunting related stuff
        if taunting:
            if random.random() <= 0.75:
                await msg.channel.send(random.choice(heat_taunts[heat]))

    # when it's not our turn:
    else:
        if len(hand) < 6:
            if danger:
                await msg.channel.send("UNO callout")
            else:
                await msg.channel.send("UNO table")


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')


@bot.command()
async def join(ctx):
    await ctx.send("UNO join")
    global active_channel
    if active_channel != ctx.channel:
        await ctx.send(f"Assigned <#{ctx.channel.id}> as the active channel")
        active_channel = ctx.channel


@bot.command()
async def start(ctx):
    await active_channel.send("UNO start")


@bot.command()
async def taunt(ctx):
    global taunting
    taunting = True
    await ctx.send("started taunting")
    while True:
        await asyncio.sleep(random.randrange(30, 120))
        if not taunting:
            break
        await active_channel.send(random.choice(taunts))


@bot.command()
async def stoptaunt(ctx):
    global taunting
    taunting = False
    await ctx.send("stopped taunting")


@bot.command()
async def say(ctx):
    await active_channel.send(ctx.message.content.replace("m!say ", ""))


@bot.event
async def on_message(message):
    global taunting
    if message.author.id != BOT_ID:
        await bot.process_commands(message)
        return

    # which function to call based on the message received
    if 'your deck:' in message.content.lower():
        check_hand(message.content.lower())
    elif 'players present:' in message.content.lower():
        check_table(message.content.lower())
    elif message.embeds:
        await check_played(message.embeds[0].to_dict()['description'].lower(), message, False)
    elif "has won" in message.content.lower():
        await message.channel.send("GG!")
        taunting = False
    await bot.process_commands(message)

load_dotenv()
token = os.getenv("TOKEN")
bot.run(token)
