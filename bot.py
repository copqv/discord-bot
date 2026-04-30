import discord
from discord import app_commands
import random
import time

# ⚠️ TEMP ONLY (for testing)
TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"

GUILD_ID = 1495420238743863528

intents = discord.Intents.default()

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print("Commands synced")

client = MyClient()

@client.tree.command(name="ping", description="Check bot")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!")

@client.tree.command(name="mines", description="Mines grid")
async def mines(interaction: discord.Interaction, tile_amt: int, round_id: str):

    if len(round_id) != 36:
        return await interaction.response.send_message("❌ Invalid round ID")

    grid = ["❌"] * 25
    for i in random.sample(range(25), tile_amt):
        grid[i] = "✅"

    grid_str = "\n".join(["".join(grid[i:i+5]) for i in range(0, 25, 5)])

    embed = discord.Embed(title="Mines", color=0x2b2d31)
    embed.add_field(name="Grid", value=f"```{grid_str}```", inline=False)

    await interaction.response.send_message(embed=embed)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

client.run(TOKEN)
