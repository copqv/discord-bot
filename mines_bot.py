import discord
from discord import app_commands
import hashlib, os, time, random, asyncio

# =========================
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise Exception("❌ TOKEN not found in Railway Variables")

MINES_ROLE = "mines"
TOWERS_ROLE = "towers"

SAFE = "<:safe:1499548265102839949>"
MINE = "<:BombShock:1499540896658755834>"

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

balances = {}
streaks = {}

# =========================
def get_balance(uid):
    return balances.get(uid, 1000)

def set_balance(uid, amount):
    balances[uid] = amount

def has_role(user, role_name):
    return any(role.name.lower() == role_name.lower() for role in user.roles)

def generate_mines(seed, mines):
    h = hashlib.sha256(seed.encode()).hexdigest()
    vals = [(i, int(h[i*2:i*2+2], 16)) for i in range(25)]
    vals.sort(key=lambda x: x[1])
    return [x[0] for x in vals[:mines]]

# =========================
# 🎬 ANIMATION SYSTEM
async def animate_embed(msg, embed, steps, delay=0.35):
    for step in steps:
        embed.description = f"🧠 {step}..."
        try:
            await msg.edit(embed=embed)
        except:
            pass
        await asyncio.sleep(delay)

# =========================
# 💣 MINES GAME
class MinesGame(discord.ui.View):
    def __init__(self, mines_pos, user_id, bet):
        super().__init__(timeout=120)
        self.mines_pos = mines_pos
        self.user_id = user_id
        self.bet = bet
        self.clicked = set()
        self.multiplier = 1.0

        for i in range(25):
            self.add_item(MineButton(i, self))

        self.add_item(CashoutButton(self))

class MineButton(discord.ui.Button):
    def __init__(self, index, game):
        super().__init__(style=discord.ButtonStyle.secondary, emoji="⬛", row=index//5)
        self.index = index
        self.game = game

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.game.user_id:
            return await interaction.response.send_message("❌ Not your game", ephemeral=True)

        if self.index in self.game.clicked:
            return await interaction.response.defer()

        self.game.clicked.add(self.index)

        # 💥 MINE
        if self.index in self.game.mines_pos:
            self.emoji = MINE
            self.style = discord.ButtonStyle.danger

            for item in self.view.children:
                item.disabled = True

            streaks[self.game.user_id] = 0

            return await interaction.response.edit_message(
                content="💥 BOOM!\n❌ Game Over",
                view=self.view
            )

        # ✅ SAFE
        self.emoji = SAFE
        self.style = discord.ButtonStyle.success

        self.game.multiplier += random.uniform(0.25, 0.55)

        await interaction.response.edit_message(
            content=f"✨ Safe!\n💰 Multiplier → **x{self.game.multiplier:.2f}**",
            view=self.view
        )

class CashoutButton(discord.ui.Button):
    def __init__(self, game):
        super().__init__(label="💸 Cashout", style=discord.ButtonStyle.success, row=4)
        self.game = game

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.game.user_id:
            return await interaction.response.send_message("❌ Not your game", ephemeral=True)

        winnings = int(self.game.bet * self.game.multiplier)

        set_balance(self.game.user_id, get_balance(self.game.user_id) + winnings)
        streaks[self.game.user_id] = streaks.get(self.game.user_id, 0) + 1

        for item in self.view.children:
            item.disabled = True

        await interaction.response.edit_message(
            content=f"💸 Cashed out **{winnings}** (x{self.game.multiplier:.2f})",
            view=self.view
        )

# =========================
# 🗼 TOWERS GAME
class TowersGame(discord.ui.View):
    def __init__(self, path, user_id, bet):
        super().__init__(timeout=120)
        self.path = path
        self.user_id = user_id
        self.bet = bet
        self.level = 0
        self.multiplier = 1.0
        self.build_row()

    def build_row(self):
        self.clear_items()
        for i in range(3):
            self.add_item(TowerButton(i, self))

class TowerButton(discord.ui.Button):
    def __init__(self, index, game):
        super().__init__(style=discord.ButtonStyle.secondary, emoji="⬛")
        self.index = index
        self.game = game

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.game.user_id:
            return await interaction.response.send_message("❌ Not your game", ephemeral=True)

        correct = self.game.path[self.game.level]

        # ❌ FAIL
        if self.index != correct:
            self.emoji = MINE
            self.style = discord.ButtonStyle.danger

            for item in self.view.children:
                item.disabled = True

            streaks[self.game.user_id] = 0

            return await interaction.response.edit_message(
                content="💥 Wrong path!\n❌ You fell",
                view=self.view
            )

        # ✅ SUCCESS
        self.emoji = SAFE
        self.style = discord.ButtonStyle.success

        self.game.level += 1
        self.game.multiplier += random.uniform(0.4, 0.8)

        if self.game.level >= 8:
            winnings = int(self.game.bet * self.game.multiplier)
            set_balance(self.game.user_id, get_balance(self.game.user_id) + winnings)
            streaks[self.game.user_id] = streaks.get(self.game.user_id, 0) + 1

            return await interaction.response.edit_message(
                content=f"🏆 Finished!\n💸 Won {winnings}",
                view=None
            )

        self.game.build_row()

        await interaction.response.edit_message(
            content=f"✨ Correct!\n🗼 Level {self.game.level}\n💰 x{self.game.multiplier:.2f}",
            view=self.game
        )

# =========================
@tree.command(name="mines")
async def mines(interaction: discord.Interaction, bet: int, mines: int):

    if not has_role(interaction.user, MINES_ROLE):
        return await interaction.response.send_message("❌ Need mines role", ephemeral=True)

    uid = interaction.user.id
    bal = get_balance(uid)

    if bet > bal:
        return await interaction.response.send_message("❌ Not enough balance", ephemeral=True)

    set_balance(uid, bal - bet)

    mines_pos = generate_mines(str(time.time()), mines)

    embed = discord.Embed(title="⚡ Cop Predictor", color=0x1e1f22)

    await interaction.response.send_message(embed=embed)
    msg = await interaction.original_response()

    await animate_embed(msg, embed, [
        "Connecting to engine",
        "Fetching round data",
        "Analyzing grid",
        "Calculating safe zones",
        "Finalizing prediction"
    ])

    await msg.edit(
        embed=discord.Embed(
            title="🎯 Mines Started",
            description="Click tiles & cashout before hitting a mine",
            color=0x1e1f22
        ),
        view=MinesGame(mines_pos, uid, bet)
    )

# =========================
@tree.command(name="towers")
async def towers(interaction: discord.Interaction, bet: int):

    if not has_role(interaction.user, TOWERS_ROLE):
        return await interaction.response.send_message("❌ Need towers role", ephemeral=True)

    uid = interaction.user.id
    bal = get_balance(uid)

    if bet > bal:
        return await interaction.response.send_message("❌ Not enough balance", ephemeral=True)

    set_balance(uid, bal - bet)

    path = [random.randint(0,2) for _ in range(8)]

    embed = discord.Embed(title="🗼 Cop Predictor", color=0x1e1f22)

    await interaction.response.send_message(embed=embed)
    msg = await interaction.original_response()

    await animate_embed(msg, embed, [
        "Connecting to tower engine",
        "Mapping safe routes",
        "Scanning climb paths",
        "Locking prediction"
    ])

    await msg.edit(
        embed=discord.Embed(
            title="🗼 Towers Started",
            description="🎯 Pick the correct path",
            color=0x1e1f22
        ),
        view=TowersGame(path, uid, bet)
    )

# =========================
@tree.command(name="balance")
async def balance(interaction: discord.Interaction):
    await interaction.response.send_message(f"💰 Balance: {get_balance(interaction.user.id)}", ephemeral=True)

# =========================
@client.event
async def on_ready():
    await tree.sync()
    await client.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="Cop Predictions")
    )
    print(f"Logged in as {client.user}")

# =========================
# 🔁 AUTO RESTART LOOP
async def run_bot():
    while True:
        try:
            await client.start(TOKEN)
        except Exception as e:
            print(f"Crash: {e}")
            await asyncio.sleep(5)

asyncio.run(run_bot())
