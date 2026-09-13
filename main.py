"""
Battle Cats Web Editor + Discord Bot
唯一入口：同時啟動 FastAPI 與 Discord 機器人
面板公開，但只有 OWNER_ID 能操作，所有回覆皆為 ephemeral
"""

import os
import threading
from functools import wraps

import discord
from discord.ext import commands
from fastapi import FastAPI
import uvicorn

# ══════════════════════════════════════════
#  設定區
# ══════════════════════════════════════════
OWNER_ID = 1392870568432373810  # 只有這個人能操作
DEFAULT_REGION = "tw"


def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


def owner_only(func):
    """裝飾器：只有 OWNER_ID 能觸發"""
    @wraps(func)
    async def wrapper(self, interaction, button):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(
                "❌ 你無權使用此面板。", ephemeral=True
            )
        return await func(self, interaction, button)
    return wrapper


# ══════════════════════════════════════════
#  FastAPI 網頁服務
# ══════════════════════════════════════════
app = FastAPI(title="Battle Cats Web Editor")


@app.get("/")
async def index():
    return {"status": "ok", "message": "Battle Cats Web Editor running"}


@app.get("/api/health")
async def health():
    return {"status": "healthy"}


# ══════════════════════════════════════════
#  Discord 機器人
# ══════════════════════════════════════════
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

sessions = {}


# ── 輸入引繼碼 ──
class CodeModal(discord.ui.Modal, title="輸入引繼碼"):
    transfer = discord.ui.TextInput(label="引繼碼", required=True)
    confirm = discord.ui.TextInput(label="認證碼", required=True)
    region = discord.ui.TextInput(label="地區 (tw/en/jp/kr)", default="tw", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message("❌ 你無權使用。", ephemeral=True)
        sessions[interaction.user.id] = {
            "transfer": self.transfer.value,
            "confirm": self.confirm.value,
            "region": self.region.value or DEFAULT_REGION,
            "actions": [],
        }
        await interaction.response.send_message("✅ 引繼碼已記錄。", ephemeral=True)


# ── 基礎資源 ──
class ResourceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="貓糧 45000", style=discord.ButtonStyle.secondary)
    @owner_only
    async def catfood(self, interaction, button):
        sessions[interaction.user.id]["actions"].append(lambda s: s.set_catfood(45000))
        await interaction.response.send_message("已排入：貓糧 45000", ephemeral=True)

    @discord.ui.button(label="XP 全滿", style=discord.ButtonStyle.secondary)
    @owner_only
    async def xp(self, interaction, button):
        sessions[interaction.user.id]["actions"].append(lambda s: s.max_xp())
        await interaction.response.send_message("已排入：XP 全滿", ephemeral=True)

    @discord.ui.button(label="NP 全滿", style=discord.ButtonStyle.secondary)
    @owner_only
    async def np(self, interaction, button):
        sessions[interaction.user.id]["actions"].append(lambda s: s.max_np())
        await interaction.response.send_message("已排入：NP 全滿", ephemeral=True)

    @discord.ui.button(label="領導力 999", style=discord.ButtonStyle.secondary)
    @owner_only
    async def leadership(self, interaction, button):
        sessions[interaction.user.id]["actions"].append(lambda s: s.set_leadership(999))
        await interaction.response.send_message("已排入：領導力 999", ephemeral=True)

    @discord.ui.button(label="遊玩時間", style=discord.ButtonStyle.secondary)
    @owner_only
    async def playtime(self, interaction, button):
        sessions[interaction.user.id]["actions"].append(lambda s: s.set_playtime(999999))
        await interaction.response.send_message("已排入：遊玩時間", ephemeral=True)


# ── 轉蛋券 ──
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="銀券 999", style=discord.ButtonStyle.secondary)
    @owner_only
    async def silver(self, interaction, button):
        sessions[interaction.user.id]["actions"].append(lambda s: s.set_silver_tickets(999))
        await interaction.response.send_message("已排入：銀券 999", ephemeral=True)

    @discord.ui.button(label="金券 999", style=discord.ButtonStyle.secondary)
    @owner_only
    async def gold(self, interaction, button):
        sessions[interaction.user.id]["actions"].append(lambda s: s.set_gold_tickets(999))
        await interaction.response.send_message("已排入：金券 999", ephemeral=True)

    @discord.ui.button(label="白金碎片 999", style=discord.ButtonStyle.secondary)
    @owner_only
    async def platinum_shard(self, interaction, button):
        sessions[interaction.user.id]["actions"].append(lambda s: s.set_platinum_shards(999))
        await interaction.response.send_message("已排入：白金碎片 999（安全）", ephemeral=True)

    @discord.ui.button(label="稀有券（安全）", style=discord.ButtonStyle.secondary)
    @owner_only
    async def rare_safe(self, interaction, button):
        sessions[interaction.user.id]["actions"].append(lambda s: s.set_rare_tickets_safe(999))
        await interaction.response.send_message("已排入：稀有券 999（安全模式）", ephemeral=True)

    @discord.ui.button(label="傳說券 999", style=discord.ButtonStyle.secondary)
    @owner_only
    async def legend(self, interaction, button):
        sessions[interaction.user.id]["actions"].append(lambda s: s.set_legend_tickets(999))
        await interaction.response.send_message("已排入：傳說券 999（高風險）", ephemeral=True)


# ── 材料 ──
class MaterialView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="喵力達 999", style=discord.ButtonStyle.secondary)
    @owner_only
    async def catseye(self, interaction, button):
        sessions[interaction.user.id]["actions"].append(lambda s: s.set_catseye(999))
        await interaction.response.send_message("已排入：喵力達 999", ephemeral=True)

    @discord.ui.button(label="貓眼石 999", style=discord.ButtonStyle.secondary)
    @owner_only
    async def catfruit(self, interaction, button):
        sessions[interaction.user.id]["actions"].append(lambda s: s.set_catfruit(999))
        await interaction.response.send_message("已排入：貓眼石 999", ephemeral=True)

    @discord.ui.button(label="貓薄荷 999", style=discord.ButtonStyle.secondary)
    @owner_only
    async def catmint(self, interaction, button):
        sessions[interaction.user.id]["actions"].append(lambda s: s.set_catmint(999))
        await interaction.response.send_message("已排入：貓薄荷 999", ephemeral=True)

    @discord.ui.button(label="獸石 999", style=discord.ButtonStyle.secondary)
    @owner_only
    async def beast_stone(self, interaction, button):
        sessions[interaction.user.id]["actions"].append(lambda s: s.set_beast_stone(999))
        await interaction.response.send_message("已排入：獸石 999", ephemeral=True)

    @discord.ui.button(label="本能玉 999", style=discord.ButtonStyle.secondary)
    @owner_only
    async def talent_orb(self, interaction, button):
        sessions[interaction.user.id]["actions"].append(lambda s: s.set_talent_orb(999))
        await interaction.response.send_message("已排入：本能玉 999", ephemeral=True)

    @discord.ui.button(label="城堡素材 999", style=discord.ButtonStyle.secondary)
    @owner_only
    async def castle(self, interaction, button):
        sessions[interaction.user.id]["actions"].append(lambda s: s.set_castle_materials(999))
        await interaction.response.send_message("已排入：城堡素材 999", ephemeral=True)


# ── 關卡進度 ──
class StageView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="世界篇全通", style=discord.ButtonStyle.secondary)
    @owner_only
    async def eoc(self, interaction, button):
        sessions[interaction.user.id]["actions"].append(lambda s: s.complete_eoc())
        await interaction.response.send_message("已排入：世界篇全通", ephemeral=True)

    @discord.ui.button(label="未來篇全通", style=discord.ButtonStyle.secondary)
    @owner_only
    async def itf(self, interaction, button):
        sessions[interaction.user.id]["actions"].append(lambda s: s.complete_itf())
        await interaction.response.send_message("已排入：未來篇全通", ephemeral=True)

    @discord.ui.button(label="宇宙篇全通", style=discord.ButtonStyle.secondary)
    @owner_only
    async def cotc(self, interaction, button):
        sessions[interaction.user.id]["actions"].append(lambda s: s.complete_cotc())
        await interaction.response.send_message("已排入：宇宙篇全通", ephemeral=True)

    @discord.ui.button(label="魔界篇全通", style=discord.ButtonStyle.secondary)
    @owner_only
    async def aku(self, interaction, button):
        sessions[interaction.user.id]["actions"].append(lambda s: s.complete_aku())
        await interaction.response.send_message("已排入：魔界篇全通", ephemeral=True)


# ── 貓咪操作 ──
class CatView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="解鎖全部貓咪", style=discord.ButtonStyle.secondary)
    @owner_only
    async def unlock(self, interaction, button):
        sessions[interaction.user.id]["actions"].append(lambda s: s.unlock_all_cats())
        await interaction.response.send_message("已排入：解鎖全部貓咪", ephemeral=True)

    @discord.ui.button(label="全型態解鎖", style=discord.ButtonStyle.secondary)
    @owner_only
    async def forms(self, interaction, button):
        sessions[interaction.user.id]["actions"].append(lambda s: s.unlock_all_forms())
        await interaction.response.send_message("已排入：全型態解鎖", ephemeral=True)

    @discord.ui.button(label="等級全滿", style=discord.ButtonStyle.secondary)
    @owner_only
    async def level(self, interaction, button):
        sessions[interaction.user.id]["actions"].append(lambda s: s.max_all_levels())
        await interaction.response.send_message("已排入：等級全滿", ephemeral=True)


# ── 帳號管理 ──
class AccountView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="解除封鎖", style=discord.ButtonStyle.danger)
    @owner_only
    async def unban(self, interaction, button):
        await interaction.response.defer(ephemeral=True)
        s = sessions.get(interaction.user.id)
        if not s:
            return await interaction.followup.send("請先輸入引繼碼。", ephemeral=True)
        try:
            import bcsfe
            save = bcsfe.core.SaveFile()
            save.load_from_server(s["transfer"], s["confirm"], region=s["region"])
            save.unban_account()  # 實際函式名請對照 BCSFE 原始碼
            new_t, new_c = save.upload_to_server()
            await interaction.followup.send(
                f"✅ 已嘗試解除封鎖\n新引繼碼：`{new_t}`\n新認證碼：`{new_c}`",
                ephemeral=True,
            )
            sessions.pop(interaction.user.id, None)
        except Exception as e:
            await interaction.followup.send(f"❌ 失敗：{e}", ephemeral=True)

    @discord.ui.button(label="時間戳重設", style=discord.ButtonStyle.secondary)
    @owner_only
    async def timestamp(self, interaction, button):
        sessions[interaction.user.id]["actions"].append(lambda s: s.reset_timestamps())
        await interaction.response.send_message("已排入：時間戳重設", ephemeral=True)

    @discord.ui.button(label="清除封號旗標", style=discord.ButtonStyle.secondary)
    @owner_only
    async def clear_flag(self, interaction, button):
        sessions[interaction.user.id]["actions"].append(lambda s: s.clear_flag())
        await interaction.response.send_message("已排入：清除封號旗標", ephemeral=True)


# ── 主面板 ──
class MainPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="輸入引繼碼", style=discord.ButtonStyle.primary, emoji="🔑", custom_id="main_login", row=0)
    @owner_only
    async def login(self, interaction, button):
        await interaction.response.send_modal(CodeModal())

    @discord.ui.button(label="基礎資源", style=discord.ButtonStyle.success, emoji="💰", custom_id="main_resources", row=1)
    @owner_only
    async def resources(self, interaction, button):
        if interaction.user.id not in sessions:
            return await interaction.response.send_message("請先輸入引繼碼。", ephemeral=True)
        await interaction.response.send_message("基礎資源：", view=ResourceView(), ephemeral=True)

    @discord.ui.button(label="轉蛋券", style=discord.ButtonStyle.success, emoji="🎫", custom_id="main_tickets", row=1)
    @owner_only
    async def tickets(self, interaction, button):
        if interaction.user.id not in sessions:
            return await interaction.response.send_message("請先輸入引繼碼。", ephemeral=True)
        await interaction.response.send_message("轉蛋券：", view=TicketView(), ephemeral=True)

    @discord.ui.button(label="材料", style=discord.ButtonStyle.success, emoji="🧪", custom_id="main_materials", row=1)
    @owner_only
    async def materials(self, interaction, button):
        if interaction.user.id not in sessions:
            return await interaction.response.send_message("請先輸入引繼碼。", ephemeral=True)
        await interaction.response.send_message("材料：", view=MaterialView(), ephemeral=True)

    @discord.ui.button(label="關卡進度", style=discord.ButtonStyle.success, emoji="🗺️", custom_id="main_stages", row=2)
    @owner_only
    async def stages(self, interaction, button):
        if interaction.user.id not in sessions:
            return await interaction.response.send_message("請先輸入引繼碼。", ephemeral=True)
        await interaction.response.send_message("關卡進度：", view=StageView(), ephemeral=True)

    @discord.ui.button(label="貓咪操作", style=discord.ButtonStyle.success, emoji="🐱", custom_id="main_cats", row=2)
    @owner_only
    async def cats(self, interaction, button):
        if interaction.user.id not in sessions:
            return await interaction.response.send_message("請先輸入引繼碼。", ephemeral=True)
        await interaction.response.send_message("貓咪操作：", view=CatView(), ephemeral=True)

    @discord.ui.button(label="帳號管理", style=discord.ButtonStyle.success, emoji="🔓", custom_id="main_account", row=2)
    @owner_only
    async def account(self, interaction, button):
        if interaction.user.id not in sessions:
            return await interaction.response.send_message("請先輸入引繼碼。", ephemeral=True)
        await interaction.response.send_message("帳號管理：", view=AccountView(), ephemeral=True)

    @discord.ui.button(label="上傳並取得新碼", style=discord.ButtonStyle.danger, emoji="📤", custom_id="main_upload", row=3)
    @owner_only
    async def upload(self, interaction, button):
        await interaction.response.defer(ephemeral=True)
        s = sessions.get(interaction.user.id)
        if not s:
            return await interaction.followup.send("請先輸入引繼碼。", ephemeral=True)
        try:
            import bcsfe
            save = bcsfe.core.SaveFile()
            save.load_from_server(s["transfer"], s["confirm"], region=s["region"])
            for action in s["actions"]:
                action(save)
            new_t, new_c = save.upload_to_server()
            await interaction.followup.send(
                f"✅ 完成\n新引繼碼：`{new_t}`\n新認證碼：`{new_c}`",
                ephemeral=True,
            )
            sessions.pop(interaction.user.id, None)
        except Exception as e:
            await interaction.followup.send(f"❌ 失敗：{e}", ephemeral=True)


# ── 空殼帳號專用面板 ──
class NewAccountView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="建立空殼帳號", style=discord.ButtonStyle.primary, emoji="🆕", custom_id="new_shell")
    @owner_only
    async def create(self, interaction, button):
        await interaction.response.defer(ephemeral=True)
        try:
            import bcsfe
            code, confirm = bcsfe.core.create_new_account()
            await interaction.followup.send(
                f"✅ 空殼帳號已建立\n\n"
                f"**轉移碼：** `{code}`\n"
                f"**確認碼：** `{confirm}`",
                ephemeral=True,
            )
        except Exception as e:
            await interaction.followup.send(f"❌ 失敗：{e}", ephemeral=True)


# ══════════════════════════════════════════
#  事件與指令
# ══════════════════════════════════════════
@bot.event
async def on_ready():
    print(f"✅ Discord 機器人 {bot.user} 已上線")
    await bot.change_presence(activity=discord.Game(name="!panel 開啟面板"))
    bot.add_view(MainPanel())
    bot.add_view(NewAccountView())


@bot.command()
async def panel(ctx):
    if not is_owner(ctx.author.id):
        return await ctx.send("❌ 你無權使用此面板。")
    embed = discord.Embed(
        title="🐱 貓戰存檔修改面板",
        description="點擊下方按鈕操作。首次使用請先「輸入引繼碼」。",
        color=discord.Color.blue(),
    )
    await ctx.send(embed=embed, view=MainPanel())


@bot.command()
async def newpanel(ctx):
    if not is_owner(ctx.author.id):
        return await ctx.send("❌ 你無權使用此面板。")
    embed = discord.Embed(
        title="🆕 建立空殼帳號",
        description="點擊下方按鈕，機器人會自動在 PONOS 伺服器註冊全新帳號。",
        color=discord.Color.green(),
    )
    await ctx.send(embed=embed, view=NewAccountView())


# ══════════════════════════════════════════
#  啟動
# ══════════════════════════════════════════
def run_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    threading.Thread(target=run_fastapi, daemon=True).start()

    TOKEN = os.environ.get('DISCORD_TOKEN')
    if not TOKEN:
        raise SystemExit("DISCORD_TOKEN not set")

    bot.run(TOKEN)
