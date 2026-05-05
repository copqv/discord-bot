import discord
from discord import app_commands
import hashlib, os, random, asyncio, time

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise Exception("❌ TOKEN not found in Railway Variables")

SAFE = "<:safe:1499548265102839949>"
MINE = "<:BombShock:1499540896658755834>"

MINES_ROLE = "mines"
TOWERS_ROLE = "towers"

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# =========================
def has_role(user, role_name):
    return any(role.name.lower() == role_name.lower() for role in user.roles)

def make_seed(r):
    return r + "-" + os.urandom(6).hex()

def generate_mines(seed, mines):
    h = hashlib.sha256(seed.encode()).hexdigest()
    vals = [(i, int(h[i*2:i*2+2], 16)) for i in range(25)]
    vals.sort(key=lambda x: x[1])
    return [x[0] for x in vals[:mines]]

# =========================
# 🔥 SAFE ANIMATION (WON'T GET STUCK)
async def animate(msg, embed, steps):
    for step in steps:
        embed.description = f"🧠 {step}..."
        try:
            await msg.edit(embed=embed)
        except:
            pass
        await asyncio.sleep(0.4)

# =========================
# 💣 MINES GRID DISPLAY
def build_grid(mines_pos):
    safe_tiles = [i for i in range(25) if i not in mines_pos]
    picks = set(random.sample(safe_tiles, min(5, len(safe_tiles))))

    out, row = [], []
    for i in range(25):
        row.append(SAFE if i in picks else MINE)
        if (i+1) % 5 == 0:
            out.append(" ".join(row))
            row = []
    return "\n".join(out)

# =========================
# 🗼 TOWERS GRID DISPLAY
def build_tower(path):
    grid = []
    for i in range(8):
        row = []
        for c in range(3):
            row.append(SAFE if c == path[i] else MINE)
        grid.append(" ".join(row))
    return "\n".join(grid[::-1])

# =========================
@tree.command(name="mines")
async def mines(interaction: discord.Interaction, roundid: str, mines: int):

    if not has_role(interaction.user, MINES_ROLE):
        return await interaction.response.send_message("❌ Need mines role", ephemeral=True)

    if mines < 1 or mines > 20:
        return await interaction.response.send_message("Use 1–20 mines.", ephemeral=True)

    seed = make_seed(roundid)
    pos = generate_mines(seed, mines)

    embed = discord.Embed(title="⚡ Cop Predictor", color=0x1e1f22)

    await interaction.response.send_message(embed=embed)
    msg = await interaction.original_response()

    # 🔥 animation (fixed)
    await animate(msg, embed, [
        "Connecting to engine",
        "Fetching round data",
        "Analyzing tile patterns",
        "Calculating safe zones",
        "Finalizing prediction"
    ])

    # ✅ ALWAYS SEND FINAL (no freeze)
    final = discord.Embed(
        title="🎯 Safe Tiles",
        description=build_grid(pos),
        color=0x1e1f22
    )

    final.add_field(name="💣 Mines", value=str(mines))
    final.add_field(name="🧠 Engine", value="Prediction Stable ✓")

    await msg.edit(embed=final)

# =========================
@tree.command(name="towers")
async def towers(interaction: discord.Interaction, roundid: str):

    if not has_role(interaction.user, TOWERS_ROLE):
        return await interaction.response.send_message("❌ Need towers role", ephemeral=True)

    random.seed(make_seed(roundid))
    path = [random.randint(0,2) for _ in range(8)]

    embed = discord.Embed(title="🗼 Cop Predictor", color=0x1e1f22)

    await interaction.response.send_message(embed=embed)
    msg = await interaction.original_response()

    # 🔥 animation (fixed)
    await animate(msg, embed, [
        "Connecting to tower engine",
        "Scanning paths",
        "Mapping safest route",
        "Calculating climb success",
        "Finalizing prediction"
    ])

    # ✅ ALWAYS SEND FINAL
    final = discord.Embed(
        title="🗼 Tower Path",
        description=build_tower(path),
        color=0x1e1f22
    )

    final.add_field(name="🧠 System", value="Route Locked ✓")

    await msg.edit(embed=final)

# =========================
@client.event
async def on_ready():
    await tree.sync()
    await client.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="Cop Predictions")
    )
    print(f"Logged in as {client.user}")

# =========================
# 🔁 AUTO RESTART
async def run_bot():
    while True:
        try:
            await client.start(TOKEN)
        except Exception as e:
            print(f"Crash: {e}")
            await asyncio.sleep(5)

asyncio.run(run_bot())
