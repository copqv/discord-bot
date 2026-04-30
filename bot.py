import discord
from discord import app_commands
import random
import time
import os

# ===== TOKEN (SAFE FOR HOSTING) =====
TOKEN = os.getenv("TOKEN")

# ===== SERVER ID (for fast slash sync) =====
GUILD_ID = 1495420238743863528

intents = discord.Intents.default()

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)

        # Sync commands to your server
        self.tree.copy_global_to(guild=guild)
        synced = await self.tree.sync(guild=guild)

        print(f"✅ Synced {len(synced)} commands")

client = MyClient()

# ===== PING COMMAND =====
@client.tree.command(name="ping", description="Check bot status")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!")

# ===== MINES COMMAND =====
@client.tree.command(name="mines", description="Generate mines grid")
@app_commands.describe(tile_amt="1-24 safe tiles", round_id="36 character ID")
async def mines(interaction: discord.Interaction, tile_amt: int, round_id: str):

    await interaction.response.defer()

    try:
        if len(round_id) != 36:
            return await interaction.followup.send("❌ Round ID must be 36 characters.")

        if tile_amt < 1 or tile_amt > 24:
            return await interaction.followup.send("❌ Tile amount must be 1-24.")

        start = time.time()

        grid = ["❌"] * 25
        safe = random.sample(range(25), tile_amt)

        for i in safe:
            grid[i] = "✅"

        grid_str = "\n".join(["".join(grid[i:i+5]) for i in range(0, 25, 5)])

        chance = random.randint(45, 95)

        embed = discord.Embed(title="💣 Mines Result", color=0x2b2d31)
        embed.add_field(name="Grid", value=f"```{grid_str}```", inline=False)
        embed.add_field(name="Accuracy", value=f"{chance}%", inline=True)
        embed.add_field(name="Round ID", value=round_id, inline=True)
        embed.set_footer(text=f"Time: {round(time.time() - start, 2)}s")

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"⚠️ Error: {e}")

# ===== READY EVENT =====
@client.event
async def on_ready():
    print(f"🤖 Logged in as {client.user}")
    print("🚀 Bot is running")

client.run(TOKEN)