import os
import discord
import requests
from typing import Optional
from discord.ext import commands
from io import BytesIO
from PIL import Image
from cards import draw_cards
from helpers import (load_data, save_data, get_user, can_draw,
                     remaining_cooldown, add_card)
from flask import Flask
from threading import Thread

app = Flask("")


@app.route("/")
def home():
    return "Bot is alive!"


def run():
    app.run(host="0.0.0.0", port=8080)


Thread(target=run).start()
# ----------------------------
print("### NEW CODE LOADED ###")
# -------- BOT SETUP --------
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


# -------- EVENTS --------
@bot.event
async def on_ready():
    print("READY AS", bot.user)
    print("Commands loaded:", [c.name for c in bot.commands])


# -------- DRAW --------
RARITY_EMOJI = {
    "Legendary": "✨",
    "Epic": "🔮",
    "Rare": "💎",
    "Uncommon": "🟢",
    "Common": "⚪",
    "Secret Rare": "🔒"
}


@bot.command(help="Draw 5 cards with a 4-hour cooldown.")
async def draw(ctx):
    data = load_data()
    user = get_user(data, ctx.author.id)
    """
    # -----------------------
    # Cooldown check (optional)
    # -----------------------

    from helpers import can_draw, remaining_cooldown
    if not can_draw(user):
        remaining = remaining_cooldown(user)
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        seconds = remaining % 60
        await ctx.send(
            f"⏳ You can only draw once every 4 hours! You must wait **{hours}h {minutes}m {seconds}s** before drawing again."
        )
        return
    """
    # -----------------------
    # Draw 5 cards
    # -----------------------
    pulls = draw_cards(5)  # returns list of tuples: (card_dict, rarity)
    user["last_draw"] = int(__import__("time").time())

    summary_list = []

    pil_images = []
    for i, (card, rarity) in enumerate(pulls, start=1):
        add_card(user, card)

        # Build summary line with emoji
        summary_list.append(
            f"{card['id']:03d} | {card['name']:<20} | {RARITY_EMOJI[rarity]} {rarity}"
        )

        # Download image
        response = requests.get(card["image"])
        img = Image.open(BytesIO(response.content)).convert("RGBA")
        pil_images.append(img)

    save_data(data)

    # -----------------------
    # Combine images horizontally
    # -----------------------
    widths, heights = zip(*(i.size for i in pil_images))
    total_width = sum(widths)
    max_height = max(heights)

    gallery = Image.new("RGBA", (total_width, max_height), (0, 0, 0, 0))
    x_offset = 0
    for img in pil_images:
        gallery.paste(img, (x_offset, 0))
        x_offset += img.width

    buffer = BytesIO()
    gallery.save(buffer, format="PNG")
    buffer.seek(0)
    discord_file = discord.File(fp=buffer, filename="draw_gallery.png")

    # -----------------------
    # Send combined image and summary embed in a single reply
    # -----------------------
    embed = discord.Embed(title=f"{ctx.author.display_name}'s Draw",
                          description="```\n" + "\n".join(summary_list) +
                          "\n```",
                          color=discord.Color.gold())
    await ctx.reply(file=discord_file, embed=embed)


# -------- CARDS --------
@bot.command(
    help="View your cards of a specific rarity (e.g., !cards common).")
async def cards(ctx, rarity: Optional[str] = None):
    from cards import CARDS, RARITY_EMOJI
    from helpers import load_data, get_user

    data = load_data()
    user = get_user(data, ctx.author.id)

    if not user["inventory"]:
        await ctx.reply("You have no cards yet.")
        return

    # Disable the command if no argument is provided
    if rarity is None:
        await ctx.reply(
            "⚠️ Invalid command!\n"
            "Use `!cards common` or `!cards uncommon` etc. instead.")
        return

    rarity = rarity.capitalize()
    if rarity not in CARDS:
        await ctx.reply(f"❌ Unknown rarity: {rarity}")
        return

    cards_list = []
    for card in CARDS[rarity]:  # Only iterate the chosen rarity!
        cid_str = str(card["id"])
        count = user["inventory"].get(cid_str, 0)
        if count > 0:
            cards_list.append(
                f"{card['id']:03d} | {card['name']:<20} | {count}x")

    if not cards_list:
        await ctx.reply(f"❌ You have no cards of rarity {rarity}.")
        return

    emoji = RARITY_EMOJI.get(rarity, "")
    embed = discord.Embed(
        title=f"{ctx.author.display_name}'s Collection — {emoji} {rarity}",
        description="```\n" + "\n".join(cards_list) + "\n```",
        color=discord.Color.green())

    await ctx.reply(embed=embed)


# -------- STATS --------
@bot.command(help="Show the rarity percentages for card draws.")
async def stats(ctx):
    from cards import RARITY_CHANCES, RARITY_EMOJI

    stats_list = []
    for rarity, chance in RARITY_CHANCES.items():
        if rarity != "Secret Rare":  # Keep Secret Rare secret
            emoji = RARITY_EMOJI.get(rarity, "")
            stats_list.append(f"{emoji} {rarity}: {chance / 1000:.3f}%")

    embed = discord.Embed(title="Rarity Percentages",
                          description="\n".join(stats_list),
                          color=discord.Color.blue())

    await ctx.reply(embed=embed)


# -------- HELP --------
@bot.command(help="Show this help message with command descriptions.")
async def help(ctx):
    embed = discord.Embed(title="Bot Commands",
                          description="Here are the available commands:",
                          color=discord.Color.purple())

    for command in bot.commands:
        if command.name != "help":  # Avoid recursion
            embed.add_field(name=f"!{command.name}",
                            value=command.help or "No description available.",
                            inline=False)

    await ctx.reply(embed=embed)


# -------- RUN --------
bot.run(os.environ["TOKEN"])
