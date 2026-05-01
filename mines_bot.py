import discord
from discord import app_commands
import hashlib, os, time, random, asyncio

# ===== TOKEN FROM RAILWAY =====
TOKEN = os.getenv("TOKEN")

OWNER_ID = 632993587994296323
GUILD_ID = 1495420238743863528
CATEGORY_ID = 1499570366350360687

SAFE = "<:safe:1499548265102839949>"
MINE = "<:BombShock:1499540896658755834>"
SCAN = "<:Ticks:1499558562861678633>"
EMPTY = "<a:Loading:1499558187714478232>"

intents = discord.Intents.default()
intents.guilds = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

cooldowns = {}

# =========================
class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🗑️ Closing...", ephemeral=True)
        await asyncio.sleep(1)
        await interaction.channel.delete()

# =========================
class ShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def create_ticket(self, interaction, plan, price):
        guild = interaction.guild
        user = interaction.user

        category = guild.get_channel(CATEGORY_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True)
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{user.id}",
            overwrites=overwrites,
            category=category
        )

        await channel.send(
            f"🎫 {user.mention} Welcome!\n💳 Plan: **{plan} ({price})**",
            view=CloseTicketView()
        )

        await interaction.response.send_message(f"✅ {channel.mention}", ephemeral=True)

    @discord.ui.button(label="Buy Mines Access 250 Robux", style=discord.ButtonStyle.danger, emoji="💣")
    async def monthly(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "Buy Mines", "250 Robux")

    @discord.ui.button(label="Buy Mines + Tower Access 350 Robux", style=discord.ButtonStyle.primary, emoji="💎")
    async def lifetime(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "Buy Mines + Towers", "350 Robux")

# =========================
def generate_mines(seed, mines):
    h = hashlib.sha256(seed.encode()).hexdigest()
    vals = [(i, int(h[i*2:i*2+2], 16)) for i in range(25)]
    vals.sort(key=lambda x: x[1])
    return [x[0] for x in vals[:mines]]

def build_final_grid(mines_pos):
    safe_tiles = [i for i in range(25) if i not in mines_pos]
    chosen = set(random.sample(safe_tiles, min(5, len(safe_tiles))))

    out, row = [], []
    for i in range(25):
        row.append(SAFE if i in chosen else MINE)
        if (i+1)%5==0:
            out.append(" ".join(row))
            row=[]
    return "\n".join(out)

def build_scan_frame(step):
    grid = [(SCAN if i<=step else EMPTY) for i in range(25)]
    out, row = [], []
    for i in range(25):
        row.append(grid[i])
        if (i+1)%5==0:
            out.append(" ".join(row))
            row=[]
    return "\n".join(out)

def progress_bar(p):
    return "█"*int(p*10)+"░"*(10-int(p*10))

def make_seed(r): 
    return r+"-"+os.urandom(8).hex()

# =========================
@tree.command(name="mines")
async def mines(interaction: discord.Interaction, roundid: str, mines: int):

    uid = interaction.user.id
    now = time.time()

    if uid in cooldowns and now - cooldowns[uid] < 2:
        return await interaction.response.send_message("⏳ Slow down...", ephemeral=True)

    cooldowns[uid] = now

    if mines < 1 or mines > 20:
        return await interaction.response.send_message("Use 1–20 mines.")

    seed = make_seed(roundid)
    pos = generate_mines(seed, mines)

    embed = discord.Embed(title="⚡Cop Predictor", color=0x1e1f22)
    embed.description = "Initializing..."

    await interaction.response.send_message(embed=embed)
    msg = await interaction.original_response()

    for i in range(25):
        p = (i+1)/25
        embed.description = build_scan_frame(i)
        embed.set_footer(text=f"{int(p*100)}% | {progress_bar(p)}")

        try:
            await msg.edit(embed=embed)
        except:
            pass

        await asyncio.sleep(0.05)

    embed = discord.Embed(
        title="🎯 Safe Tiles Revealed",
        description=build_final_grid(pos),
        color=0x1e1f22
    )

    embed.add_field(name=f"{MINE} Mines", value=f"**{mines}**", inline=True)
    embed.add_field(name=f"{SAFE} Safe", value="**Max 5**", inline=True)

    embed.add_field(
        name="🧠 System",
        value="Scan Complete\nPattern Match ✓\nGrid Stabilized ✓",
        inline=False
    )

    embed.set_footer(text="Cop Predictor • Developed by cop")

    await msg.edit(embed=embed)

# =========================
@tree.command(name="towers")
@app_commands.choices(mode=[
    app_commands.Choice(name="Easy",value="easy"),
    app_commands.Choice(name="Hard",value="hard"),
])
async def towers(interaction: discord.Interaction, roundid: str, mode: app_commands.Choice[str]):

    random.seed(make_seed(roundid))
    path=[random.randint(0,2) for _ in range(8)]

    await interaction.response.send_message("⚡ Initializing...")
    msg = await interaction.original_response()

    temp=[["⬛"]*3 for _ in range(8)]

    for i in range(8):
        for c in range(3):
            temp[i][c]=SCAN

        grid="\n".join(" ".join(r) for r in temp[::-1])
        await msg.edit(embed=discord.Embed(title="🗼 Scan",description=grid))
        await asyncio.sleep(0.1)

    reveal=[["⬛"]*3 for _ in range(8)]

    for i in range(8):
        for c in range(3):
            reveal[i][c]=SAFE if c==path[i] else MINE

        grid="\n".join(" ".join(r) for r in reveal[::-1])
        await msg.edit(embed=discord.Embed(title="🎯 Reveal",description=grid))
        await asyncio.sleep(0.12)

    final="\n".join(" ".join(r) for r in reveal[::-1])

    embed=discord.Embed(title="🗼 Complete",description=final)
    embed.add_field(name="Mode",value=mode.value.capitalize())

    await msg.edit(embed=embed)

# =========================
@tree.command(name="shop")
async def shop(interaction: discord.Interaction):

    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ You can't use this command.", ephemeral=True)

    embed = discord.Embed(
        title="🛒 Cop Predictor Shop",
        description=(
            "Purchase The Cop Predictor Here!\n"
            "Click a button down below.\n"
            "Select wich version you would like.\n\n"
            "📅 **Mines Access — 250 Robux**\n"
            "💎 **Mines + Towers Access — 350 Robux**\n"
            "└ 📌 Boosted accuracy on both!\n\n"
            "💳 Click a button below to select a payment method."
        ),
        color=0x2b0d0d
    )

    embed.set_footer(text="Cop Predictor • Developed By Cop")

    await interaction.response.send_message(embed=embed, view=ShopView())

# =========================
@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")

client.run(TOKEN)
# update
