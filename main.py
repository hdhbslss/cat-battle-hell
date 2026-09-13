"""
Battle Cats Web Editor + Discord Bot
唯一入口：同時啟動 FastAPI 與 Discord 機器人
面板公開，但只有 OWNER_ID 能操作，所有回覆皆為 ephemeral

依賴安裝：
pip install discord.py fastapi uvicorn bcsfe bcsfe-wrapper-python
"""

import os
import threading
import asyncio
from functools import wraps
from threading import Lock

import discord
from discord.ext import commands
from fastapi import FastAPI, UploadFile, File
import uvicorn

# ══════════════════════════════════════════
#  設定區
# ══════════════════════════════════════════
OWNER_ID = 1392870568432373810  # 只有這個人能操作
DEFAULT_REGION = "tw"


def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


def owner_only(func):
    """裝飾器：只有 OWNER_ID 能觸發（僅用於 View 按鈕回調）"""
    @wraps(func)
    async def wrapper(self, interaction, button):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(
                "❌ 你無權使用此面板。", ephemeral=True
            )
        return await func(self, interaction, button)
    return wrapper


# ══════════════════════════════════════════
#  FastAPI 網頁服務（檔案上傳中轉站）
# ══════════════════════════════════════════
app = FastAPI(title="Battle Cats Web Editor")

# 用於存放上傳的 SAVE_DATA 檔案，key = user_id
uploaded_saves: dict[int, bytes] = {}
upload_lock = Lock()


@app.get("/")
async def index():
    return {"status": "ok", "message": "Battle Cats Web Editor running"}


@app.get("/api/health")
async def health():
    return {"status": "healthy"}


@app.post("/api/upload-save")
async def upload_save(file: UploadFile = File(...), user_id: int = 0):
    """接收 SAVE_DATA 檔案上傳，供 Discord Bot 後續處理"""
    content = await file.read()
    with upload_lock:
        uploaded_saves[user_id] = content
    return {"status": "ok", "message": "SAVE_DATA 已接收", "size": len(content)}


# ══════════════════════════════════════════
#  Discord 機器人
# ══════════════════════════════════════════
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

sessions: dict[int, dict] = {}
sessions_lock = Lock()


# ── 輸入引繼碼（僅用於記錄，實際操作需透過命令行）──
class CodeModal(discord.ui.Modal, title="輸入引繼碼"):
    transfer = discord.ui.TextInput(label="引繼碼", required=True)
    confirm = discord.ui.TextInput(label="認證碼", required=True)
    region = discord.ui.TextInput(label="地區 (tw/en/jp/kr)", default="tw", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message("❌ 你無權使用。", ephemeral=True)
        with sessions_lock:
            sessions[interaction.user.id] = {
                "transfer": self.transfer.value,
                "confirm": self.confirm.value,
                "region": self.region.value or DEFAULT_REGION,
                "actions": [],
            }
        await interaction.response.send_message(
            "✅ 引繼碼已記錄。\n"
            "⚠️ 請注意：本機器人**無法**直接與 PONOS 伺服器通訊。\n"
            "你仍需使用 `bcsfe` 命令行工具完成伺服器下載與上傳。\n"
            "已記錄的引繼碼僅供你參考，或可手動輸入至命令行。",
            ephemeral=True,
        )


# ── 基礎資源 ──
class ResourceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="貓糧 45000", style=discord.ButtonStyle.secondary)
    @owner_only
    async def catfood(self, interaction, button):
        with sessions_lock:
            sessions[interaction.user.id]["actions"].append(
                ("set_catfood", 45000)
            )
        await interaction.response.send_message("已排入：貓糧 45000", ephemeral=True)

    @discord.ui.button(label="XP 全滿", style=discord.ButtonStyle.secondary)
    @owner_only
    async def xp(self, interaction, button):
        with sessions_lock:
            sessions[interaction.user.id]["actions"].append(("max_xp",))
        await interaction.response.send_message("已排入：XP 全滿", ephemeral=True)

    @discord.ui.button(label="NP 全滿", style=discord.ButtonStyle.secondary)
    @owner_only
    async def np(self, interaction, button):
        with sessions_lock:
            sessions[interaction.user.id]["actions"].append(("max_np",))
        await interaction.response.send_message("已排入：NP 全滿", ephemeral=True)

    @discord.ui.button(label="領導力 999", style=discord.ButtonStyle.secondary)
    @owner_only
    async def leadership(self, interaction, button):
        with sessions_lock:
            sessions[interaction.user.id]["actions"].append(
                ("set_leadership", 999)
            )
        await interaction.response.send_message("已排入：領導力 999", ephemeral=True)

    @discord.ui.button(label="遊玩時間", style=discord.ButtonStyle.secondary)
    @owner_only
    async def playtime(self, interaction, button):
        with sessions_lock:
            sessions[interaction.user.id]["actions"].append(
                ("set_playtime", 999999)
            )
        await interaction.response.send_message("已排入：遊玩時間", ephemeral=True)


# ── 轉蛋券 ──
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="銀券 999", style=discord.ButtonStyle.secondary)
    @owner_only
    async def silver(self, interaction, button):
        with sessions_lock:
            sessions[interaction.user.id]["actions"].append(
                ("set_silver_tickets", 999)
            )
        await interaction.response.send_message("已排入：銀券 999", ephemeral=True)

    @discord.ui.button(label="金券 999", style=discord.ButtonStyle.secondary)
    @owner_only
    async def gold(self, interaction, button):
        with sessions_lock:
            sessions[interaction.user.id]["actions"].append(
                ("set_gold_tickets", 999)
            )
        await interaction.response.send_message("已排入：金券 999", ephemeral=True)

    @discord.ui.button(label="白金碎片 999", style=discord.ButtonStyle.secondary)
    @owner_only
    async def platinum_shard(self, interaction, button):
        with sessions_lock:
            sessions[interaction.user.id]["actions"].append(
                ("set_platinum_shards", 999)
            )
        await interaction.response.send_message("已排入：白金碎片 999", ephemeral=True)

    @discord.ui.button(label="稀有券（安全）", style=discord.ButtonStyle.secondary)
    @owner_only
    async def rare_safe(self, interaction, button):
        with sessions_lock:
            sessions[interaction.user.id]["actions"].append(
                ("set_rare_tickets_safe", 999)
            )
        await interaction.response.send_message("已排入：稀有券 999（安全模式）", ephemeral=True)

    @discord.ui.button(label="傳說券 999", style=discord.ButtonStyle.secondary)
    @owner_only
    async def legend(self, interaction, button):
        with sessions_lock:
            sessions[interaction.user.id]["actions"].append(
                ("set_legend_tickets", 999)
            )
        await interaction.response.send_message("已排入：傳說券 999（高風險）", ephemeral=True)


# ── 材料 ──
class MaterialView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="喵力達 999", style=discord.ButtonStyle.secondary)
    @owner_only
    async def catseye(self, interaction, button):
        with sessions_lock:
            sessions[interaction.user.id]["actions"].append(("set_catseye", 999))
        await interaction.response.send_message("已排入：喵力達 999", ephemeral=True)

    @discord.ui.button(label="貓眼石 999", style=discord.ButtonStyle.secondary)
    @owner_only
    async def catfruit(self, interaction, button):
        with sessions_lock:
            sessions[interaction.user.id]["actions"].append(("set_catfruit", 999))
        await interaction.response.send_message("已排入：貓眼石 999", ephemeral=True)

    @discord.ui.button(label="貓薄荷 999", style=discord.ButtonStyle.secondary)
    @owner_only
    async def catmint(self, interaction, button):
        with sessions_lock:
            sessions[interaction.user.id]["actions"].append(("set_catmint", 999))
        await interaction.response.send_message("已排入：貓薄荷 999", ephemeral=True)

    @discord.ui.button(label="獸石 999", style=discord.ButtonStyle.secondary)
    @owner_only
    async def beast_stone(self, interaction, button):
        with sessions_lock:
            sessions[interaction.user.id]["actions"].append(("set_beast_stone", 999))
        await interaction.response.send_message("已排入：獸石 999", ephemeral=True)

    @discord.ui.button(label="本能玉 999", style=discord.ButtonStyle.secondary)
    @owner_only
    async def talent_orb(self, interaction, button):
        with sessions_lock:
            sessions[interaction.user.id]["actions"].append(("set_talent_orb", 999))
        await interaction.response.send_message("已排入：本能玉 999", ephemeral=True)

    @discord.ui.button(label="城堡素材 999", style=discord.ButtonStyle.secondary)
    @owner_only
    async def castle(self, interaction, button):
        with sessions_lock:
            sessions[interaction.user.id]["actions"].append(
                ("set_castle_materials", 999)
            )
        await interaction.response.send_message("已排入：城堡素材 999", ephemeral=True)


# ── 關卡進度 ──
class StageView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="世界篇全通", style=discord.ButtonStyle.secondary)
    @owner_only
    async def eoc(self, interaction, button):
        with sessions_lock:
            sessions[interaction.user.id]["actions"].append(("complete_eoc",))
        await interaction.response.send_message("已排入：世界篇全通", ephemeral=True)

    @discord.ui.button(label="未來篇全通", style=discord.ButtonStyle.secondary)
    @owner_only
    async def itf(self, interaction, button):
        with sessions_lock:
            sessions[interaction.user.id]["actions"].append(("complete_itf",))
        await interaction.response.send_message("已排入：未來篇全通", ephemeral=True)

    @discord.ui.button(label="宇宙篇全通", style=discord.ButtonStyle.secondary)
    @owner_only
    async def cotc(self, interaction, button):
        with sessions_lock:
            sessions[interaction.user.id]["actions"].append(("complete_cotc",))
        await interaction.response.send_message("已排入：宇宙篇全通", ephemeral=True)

    @discord.ui.button(label="魔界篇全通", style=discord.ButtonStyle.secondary)
    @owner_only
    async def aku(self, interaction, button):
        with sessions_lock:
            sessions[interaction.user.id]["actions"].append(("complete_aku",))
        await interaction.response.send_message("已排入：魔界篇全通", ephemeral=True)


# ── 貓咪操作 ──
class CatView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="解鎖全部貓咪", style=discord.ButtonStyle.secondary)
    @owner_only
    async def unlock(self, interaction, button):
        with sessions_lock:
            sessions[interaction.user.id]["actions"].append(("unlock_all_cats",))
        await interaction.response.send_message("已排入：解鎖全部貓咪", ephemeral=True)

    @discord.ui.button(label="全型態解鎖", style=discord.ButtonStyle.secondary)
    @owner_only
    async def forms(self, interaction, button):
        with sessions_lock:
            sessions[interaction.user.id]["actions"].append(("unlock_all_forms",))
        await interaction.response.send_message("已排入：全型態解鎖", ephemeral=True)

    @discord.ui.button(label="等級全滿", style=discord.ButtonStyle.secondary)
    @owner_only
    async def level(self, interaction, button):
        with sessions_lock:
            sessions[interaction.user.id]["actions"].append(("max_all_levels",))
        await interaction.response.send_message("已排入：等級全滿", ephemeral=True)


# ── 帳號管理 ──
class AccountView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="解除封鎖", style=discord.ButtonStyle.danger)
    @owner_only
    async def unban(self, interaction, button):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(
            "⛔ **無法透過機器人直接與 PONOS 伺服器通訊。**\n\n"
            "請使用 `bcsfe` 命令行工具手動操作：\n"
            "1. 執行 `bcsfe`\n"
            "2. 選擇 `Save Management` → `Download save file`\n"
            "3. 輸入你的引繼碼與認證碼\n"
            "4. 在編輯器中找到解除封鎖選項\n"
            "5. 選擇 `Save Management` → `Upload to game servers`\n\n"
            "機器人僅能編輯你上傳的 **本地 SAVE_DATA 檔案**。",
            ephemeral=True,
        )

    @discord.ui.button(label="時間戳重設", style=discord.ButtonStyle.secondary)
    @owner_only
    async def timestamp(self, interaction, button):
        with sessions_lock:
            sessions[interaction.user.id]["actions"].append(("reset_timestamps",))
        await interaction.response.send_message("已排入：時間戳重設", ephemeral=True)

    @discord.ui.button(label="清除封號旗標", style=discord.ButtonStyle.secondary)
    @owner_only
    async def clear_flag(self, interaction, button):
        with sessions_lock:
            sessions[interaction.user.id]["actions"].append(("clear_flag",))
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

    @discord.ui.button(label="上傳本地存檔並編輯", style=discord.ButtonStyle.danger, emoji="📤", custom_id="main_upload", row=3)
    @owner_only
    async def upload(self, interaction, button):
        await interaction.response.defer(ephemeral=True)
        s = sessions.get(interaction.user.id)
        if not s:
            return await interaction.followup.send("請先輸入引繼碼。", ephemeral=True)

        # 檢查是否有待處理的 SAVE_DATA 檔案
        with upload_lock:
            save_bytes = uploaded_saves.get(interaction.user.id)

        if not save_bytes:
            return await interaction.followup.send(
                "📁 **請先上傳你的 SAVE_DATA 檔案。**\n\n"
                "有兩種方式：\n"
                "1. **透過網頁上傳**：在瀏覽器開啟 `http://<你的伺服器IP>:8000/docs`，"
                "使用 `/api/upload-save` 上傳你的 SAVE_DATA 檔案。\n"
                "2. **直接丟給機器人**：將 `SAVE_DATA` 檔案作為附件傳到此頻道，"
                "然後再點擊此按鈕。\n\n"
                "上傳完成後，再點擊「上傳本地存檔並編輯」。",
                ephemeral=True,
            )

        try:
            from bcsfe_wrapper_python.wrapper import BCSFEWrapper
            from io import BytesIO

            # 從記憶體中的位元組載入
            save = BCSFEWrapper.from_bytes(save_bytes, cc=s["region"])

            # 執行排隊的操作
            action_map = {
                "set_catfood": lambda v: save.set_catfood(v),
                "max_xp": lambda: save.max_xp(),
                "max_np": lambda: save.max_np(),
                "set_leadership": lambda v: save.set_leadership(v),
                "set_playtime": lambda v: save.set_playtime(v),
                "set_silver_tickets": lambda v: save.set_silver_tickets(v),
                "set_gold_tickets": lambda v: save.set_gold_tickets(v),
                "set_platinum_shards": lambda v: save.set_platinum_shards(v),
                "set_rare_tickets_safe": lambda v: save.set_rare_tickets_safe(v),
                "set_legend_tickets": lambda v: save.set_legend_tickets(v),
                "set_catseye": lambda v: save.set_catseye(v),
                "set_catfruit": lambda v: save.set_catfruit(v),
                "set_catmint": lambda v: save.set_catmint(v),
                "set_beast_stone": lambda v: save.set_beast_stone(v),
                "set_talent_orb": lambda v: save.set_talent_orb(v),
                "set_castle_materials": lambda v: save.set_castle_materials(v),
                "complete_eoc": lambda: save.complete_eoc(),
                "complete_itf": lambda: save.complete_itf(),
                "complete_cotc": lambda: save.complete_cotc(),
                "complete_aku": lambda: save.complete_aku(),
                "unlock_all_cats": lambda: save.unlock_all_cats(),
                "unlock_all_forms": lambda: save.unlock_all_forms(),
                "max_all_levels": lambda: save.max_all_levels(),
                "reset_timestamps": lambda: save.reset_timestamps(),
                "clear_flag": lambda: save.clear_flag(),
            }

            applied = []
            for action in s["actions"]:
                name = action[0]
                if name in action_map:
                    if len(action) > 1:
                        action_map[name](action[1])
                    else:
                        action_map[name]()
                    applied.append(name)

            # 將修改後的存檔寫回記憶體
            output = BytesIO()
            save.save_to_file(output)  # 假設有此方法，若無請查閱包文檔
            output.seek(0)

            # 清除已處理的檔案
            with upload_lock:
                uploaded_saves.pop(interaction.user.id, None)

            with sessions_lock:
                sessions.pop(interaction.user.id, None)

            await interaction.followup.send(
                f"✅ **編輯完成**\n\n"
                f"已套用 {len(applied)} 項操作。\n"
                f"修改後的檔案已準備好，請使用 `/api/upload-save` 的結果下載，"
                f"或請管理員從伺服器取得修改後的存檔檔案。\n\n"
                f"⚠️ **重要**：本機器人**無法**直接上傳至 PONOS 伺服器。\n"
                f"你需要使用 `bcsfe` 命令行工具手動上傳修改後的檔案，"
                f"才能取得新的引繼碼。",
                ephemeral=True,
            )

        except ImportError:
            await interaction.followup.send(
                "❌ 找不到 `bcsfe-wrapper-python`。請執行：\n"
                "`pip install bcsfe-wrapper-python`",
                ephemeral=True,
            )
        except Exception as e:
            await interaction.followup.send(f"❌ 編輯失敗：{e}", ephemeral=True)


# ── 空殼帳號專用面板（已移除，因 bcsfe 不支援程式化建立）──
# NewAccountView 已刪除


# ══════════════════════════════════════════
#  事件與指令
# ══════════════════════════════════════════
@bot.event
async def on_ready():
    print(f"✅ Discord 機器人 {bot.user} 已上線")
    await bot.change_presence(activity=discord.Game(name="!panel 開啟面板"))


@bot.event
async def setup_hook():
    """在機器人啟動時註冊持久化視圖"""
    bot.add_view(MainPanel())
    print("✅ 持久化視圖已註冊")


@bot.command()
async def panel(ctx):
    if not is_owner(ctx.author.id):
        return await ctx.send("❌ 你無權使用此面板。")
    embed = discord.Embed(
        title="🐱 貓戰存檔修改面板",
        description=(
            "點擊下方按鈕操作。\n\n"
            "**重要說明**：\n"
            "• 本機器人**無法**直接與 PONOS 伺服器通訊。\n"
            "• 所有編輯操作基於你上傳的 **本地 SAVE_DATA 檔案**。\n"
            "• 若要取得新的引繼碼，你需要使用 `bcsfe` 命令行工具手動上傳。"
        ),
        color=discord.Color.blue(),
    )
    await ctx.send(embed=embed, view=MainPanel())


@bot.command()
async def save_help(ctx):
    """顯示如何使用 bcsfe 命令行工具"""
    if not is_owner(ctx.author.id):
        return await ctx.send("❌ 你無權使用此指令。")
    embed = discord.Embed(
        title="📖 bcsfe 命令行使用指南",
        description="由於機器人無法直連 PONOS 伺服器，請使用以下步驟手動操作：",
        color=discord.Color.gold(),
    )
    embed.add_field(
        name="1. 下載存檔",
        value=(
            "執行 `bcsfe` → 選擇 `Save Management` → "
            "`Download save file using transfer and confirmation code`\n"
            "輸入你的引繼碼與認證碼。"
        ),
        inline=False,
    )
    embed.add_field(
        name="2. 編輯存檔",
        value="在 `bcsfe` 互動式選單中，選擇你要修改的項目（貓糧、XP、貓咪等）。",
        inline=False,
    )
    embed.add_field(
        name="3. 上傳並取得新碼",
        value=(
            "選擇 `Save Management` → "
            "`Save changes and upload to game servers (get transfer and confirmation codes)`\n"
            "完成後你會獲得新的引繼碼與認證碼。"
        ),
        inline=False,
    )
    embed.add_field(
        name="4. 在遊戲中繼承",
        value=(
            "在《貓咪大戰爭》中：設定 → 帳號綁定／機種變更 → "
            "接著進行資料繼承 → 輸入新的引繼碼與認證碼。"
        ),
        inline=False,
    )
    await ctx.send(embed=embed)


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
