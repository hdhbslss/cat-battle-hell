import os
import time
import discord
from discord.ext import commands

from bcsfe_web.service import Service
from bcsfe_web.models import Region, EditPayload

# ============================================================
# 設定
# ============================================================
TOKEN = os.environ.get("DISCORD_TOKEN")
if not TOKEN:
    raise SystemExit("DISCORD_TOKEN not set")

AUDIT_USER_ID = int(os.environ.get("AUDIT_USER_ID", "0"))

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
service = Service()

# ============================================================
# Session（含 TTL）
# ============================================================
USER_SESSIONS: dict[int, dict] = {}
SESSION_TTL = 30 * 60


def set_session(user_id: int, sid: str):
    USER_SESSIONS[user_id] = {"sid": sid, "at": time.time()}


def get_session(user_id: int) -> str | None:
    e = USER_SESSIONS.get(user_id)
    if not e:
        return None
    if time.time() - e["at"] > SESSION_TTL:
        USER_SESSIONS.pop(user_id, None)
        return None
    return e["sid"]


def clear_session(user_id: int):
    USER_SESSIONS.pop(user_id, None)


# ============================================================
# 稽核：每次操作私訊給你
# ============================================================
async def audit(user, action: str, detail: str, extra: dict | None = None):
    if not AUDIT_USER_ID:
        return
    try:
        target = await bot.fetch_user(AUDIT_USER_ID)
    except Exception:
        return

    embed = discord.Embed(
        title="🔔 存檔修改紀錄",
        color=0xFEE75C,
        timestamp=discord.utils.utcnow(),
    )
    embed.add_field(name="使用者", value=f"{user} (`{user.id}`)", inline=False)
    embed.add_field(name="動作", value=action, inline=False)
    embed.add_field(name="內容", value=(detail or "—")[:1000], inline=False)

    if extra:
        for k, v in list(extra.items())[:20]:
            embed.add_field(name=k, value=f"`{v}`", inline=False)

    try:
        await target.send(embed=embed)
    except Exception:
        pass


# ============================================================
# 道具總表（分頁）
# ============================================================
ITEM_PAGES: list[list[tuple[str, str]]] = [
    [
        ("銀券", "silver_tickets"),
        ("金券", "gold_tickets"),
        ("白金券", "platinum_tickets"),
        ("傳說券", "legend_tickets"),
        ("白金碎片", "platinum_shard"),
        ("稀有券", "rare_tickets"),
        ("貓咪券", "cat_tickets"),
        ("合作券", "collab_tickets"),
    ],
    [
        ("貓薄荷種子", "catfruit_seed"),
        ("貓薄荷果實", "catfruit_fruit"),
        ("貓薄荷精華", "catfruit_essence"),
        ("紅薄荷", "red_catfruit"),
        ("藍薄荷", "blue_catfruit"),
        ("綠薄荷", "green_catfruit"),
        ("黃薄荷", "yellow_catfruit"),
        ("紫薄荷", "purple_catfruit"),
    ],
    [
        ("獸石", "beast_stone"),
        ("本能玉", "talent_orb"),
        ("喵力達", "catseye"),
        ("貓眼石", "catseye_stone"),
        ("傳說貓眼石", "legend_catseye"),
        ("特殊貓眼石", "special_catseye"),
    ],
    [
        ("城堡素材", "castle_material"),
        ("基地材料", "base_material"),
        ("黃金素材", "gold_material"),
        ("傳說素材", "legend_material"),
        ("古代素材", "ancient_material"),
        ("宇宙素材", "cosmic_material"),
    ],
    [
        ("速度提升", "speed_up"),
        ("貓咪砲加速", "cat_cannon_speed"),
        ("金錢加倍", "money_up"),
        ("寶藏雷達", "treasure_radar"),
        ("貓咪 CPU", "cat_cpu"),
        ("狙擊手", "sniper"),
        ("鐵壁砲", "iron_wall"),
        ("暫停道具", "freeze_item"),
    ],
    [
        ("彩虹貓薄荷", "rainbow_catfruit"),
        ("遠古之書", "ancient_book"),
        ("貓咪探險隊券", "expedition_ticket"),
        ("貓咪基地券", "base_ticket"),
        ("貓咪砲開發券", "cannon_ticket"),
        ("特殊素材", "special_material"),
    ],
]


def flatten_items():
    return [i for p in ITEM_PAGES for i in p]


# ============================================================
# !panel：存檔修改
# ============================================================
class OpenLoginButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="🔑 登入存檔",
            style=discord.ButtonStyle.primary,
            custom_id="bce_open_login",
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(LoginModal())


@bot.command(name="panel")
async def panel(ctx: commands.Context):
    embed = discord.Embed(
        title="🐱 貓咪大戰爭 存檔修改器",
        description=(
            "點下方按鈕開始。\n\n"
            "**使用流程**\n"
            "1. 遊戲內「選單」→「轉移引繼資料」→「上傳存檔到伺服器」\n"
            "2. 記下引繼碼與認證碼\n"
            "3. 點下方按鈕填入\n"
            "4. 修改完成後按「儲存並上傳」取得新引繼碼"
        ),
        color=0x5865F2,
    )
    embed.set_footer(text="僅供學術研究與個人備份使用")

    view = discord.ui.View(timeout=None)
    view.add_item(OpenLoginButton())
    await ctx.send(embed=embed, view=view)


# ============================================================
# !newpanel：產出空殼帳號
# ============================================================
class NewAccountButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="➕ 產出新帳號",
            style=discord.ButtonStyle.success,
            custom_id="bce_new_account",
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != AUDIT_USER_ID:
            await interaction.response.send_message("你沒有權限。", ephemeral=True)
            return
        await interaction.response.send_modal(NewAccountModal())


@bot.command(name="newpanel")
async def newpanel(ctx: commands.Context):
    if ctx.author.id != AUDIT_USER_ID:
        await ctx.message.add_reaction("⛔")
        return

    embed = discord.Embed(
        title="🆕 產出全新空殼帳號",
        description=(
            "點下方按鈕，輸入要產出的帳號數量。\n\n"
            "**注意**\n"
            "・產出的是全新空殼帳號\n"
            "・轉移碼與確認碼只會顯示在只有你看得到的訊息\n"
            "・請立刻複製保存，訊息關掉就找不回來"
        ),
        color=0x57F287,
    )
    view = discord.ui.View(timeout=None)
    view.add_item(NewAccountButton())
    await ctx.send(embed=embed, view=view)


class NewAccountModal(discord.ui.Modal, title="產出空殼帳號"):
    count = discord.ui.TextInput(
        label="要產出幾個帳號（1 ~ 10）",
        default="1",
        required=True,
        max_length=2,
    )

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != AUDIT_USER_ID:
            await interaction.response.send_message("你沒有權限。", ephemeral=True)
            return

        try:
            n = int(self.count.value)
        except ValueError:
            await interaction.response.send_message("請輸入數字。", ephemeral=True)
            return

        if not 1 <= n <= 10:
            await interaction.response.send_message("數量需在 1 ~ 10 之間。", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        results = []
        for i in range(n):
            try:
                acc = await service.create_shell_account()
                results.append(acc)
            except Exception as e:
                await interaction.followup.send(
                    f"❌ 第 {i + 1} 個帳號產出失敗：{e}", ephemeral=True
                )
                return

        # 逐個回傳，方便複製
        for idx, acc in enumerate(results, 1):
            await interaction.followup.send(
                f"**帳號 {idx} / {len(results)}**\n"
                f"轉移碼：`{acc.transfer_code}`\n"
                f"確認碼：`{acc.confirmation_code}`",
                ephemeral=True,
            )

        # 稽核
        extra = {}
        for i, acc in enumerate(results, 1):
            extra[f"帳號 {i} 轉移碼"] = acc.transfer_code
            extra[f"帳號 {i} 確認碼"] = acc.confirmation_code

        await audit(
            interaction.user,
            f"產出 {len(results)} 個空殼帳號",
            "已建立",
            extra=extra,
        )


# ============================================================
# 登入 modal
# ============================================================
class LoginModal(discord.ui.Modal, title="登入貓咪大戰爭存檔"):
    transfer_code = discord.ui.TextInput(label="轉移碼 (Transfer Code)", required=True)
    confirmation_code = discord.ui.TextInput(label="確認碼 (Confirmation Code)", required=True)
    version = discord.ui.TextInput(
        label="版本 (TW / EN / JP / KR)", default="TW", required=False, max_length=2
    )

    async def on_submit(self, interaction: discord.Interaction):
        region = (self.version.value or "TW").upper()
        if region not in {"TW", "EN", "JP", "KR"}:
            await interaction.response.send_message("版本只能是 TW / EN / JP / KR", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            sid = await service.login(
                transfer_code=self.transfer_code.value,
                confirmation_code=self.confirmation_code.value,
                region=Region(region),
            )
        except Exception as e:
            await interaction.followup.send(f"❌ 登入失敗：{e}", ephemeral=True)
            return

        set_session(interaction.user.id, sid)

        await interaction.followup.send(
            "✅ 登入成功，請選擇要修改的項目：",
            view=MainPanel(interaction.user.id),
            ephemeral=True,
        )

        await audit(
            interaction.user,
            "登入",
            f"地區：{region}",
            extra={
                "轉移碼": self.transfer_code.value,
                "確認碼": self.confirmation_code.value,
            },
        )


# ============================================================
# 主面板
# ============================================================
class MainPanel(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=600)
        self.user_id = user_id

    async def _check(self, interaction: discord.Interaction) -> str | None:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("這不是你的面板。", ephemeral=True)
            return None
        sid = get_session(self.user_id)
        if sid is None:
            await interaction.response.send_message("登入已過期，請重新 `!panel`。", ephemeral=True)
            return None
        return sid

    # --- 基礎資源 ---
    @discord.ui.button(label="貓罐頭", style=discord.ButtonStyle.secondary, row=0)
    async def catfood(self, i, b):
        if await self._check(i) is None:
            return
        await self._ask(i, "catfood", "貓罐頭", 45000)

    @discord.ui.button(label="經驗值 XP", style=discord.ButtonStyle.secondary, row=0)
    async def xp(self, i, b):
        if await self._check(i) is None:
            return
        await self._ask(i, "xp", "經驗值", 99_999_999)

    @discord.ui.button(label="NP", style=discord.ButtonStyle.secondary, row=0)
    async def np(self, i, b):
        if await self._check(i) is None:
            return
        await self._ask(i, "np", "NP", 9999)

    @discord.ui.button(label="領導力", style=discord.ButtonStyle.secondary, row=0)
    async def leadership(self, i, b):
        if await self._check(i) is None:
            return
        await self._ask(i, "leadership", "領導力", 9999)

    @discord.ui.button(label="遊玩時間", style=discord.ButtonStyle.secondary, row=1)
    async def playtime(self, i, b):
        if await self._check(i) is None:
            return
        await self._ask(i, "playtime", "遊玩時間（小時）", 99999)

    @discord.ui.button(label="黃金會員", style=discord.ButtonStyle.secondary, row=1)
    async def gold_pass(self, i, b):
        if await self._check(i) is None:
            return
        await self._ask(i, "gold_pass", "黃金會員 (0/1)", 1)

    @discord.ui.button(label="世界篇", style=discord.ButtonStyle.secondary, row=1)
    async def eoc(self, i, b):
        if await self._check(i) is None:
            return
        await self._ask(i, "eoc_progress", "世界篇進度", 48)

    @discord.ui.button(label="未來篇", style=discord.ButtonStyle.secondary, row=1)
    async def itf(self, i, b):
        if await self._check(i) is None:
            return
        await self._ask(i, "itf_progress", "未來篇進度", 48)

    @discord.ui.button(label="宇宙篇", style=discord.ButtonStyle.secondary, row=2)
    async def cotc(self, i, b):
        if await self._check(i) is None:
            return
        await self._ask(i, "cotc_progress", "宇宙篇進度", 48)

    @discord.ui.button(label="魔界篇", style=discord.ButtonStyle.secondary, row=2)
    async def aku(self, i, b):
        if await self._check(i) is None:
            return
        await self._ask(i, "aku_progress", "魔界篇進度", 48)

    # --- 道具 / 解鎖 / 解 Ban ---
    @discord.ui.button(label="📦 道具選單", style=discord.ButtonStyle.success, row=2)
    async def items(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self._check(interaction) is None:
            return
        await interaction.response.send_message(
            "請選擇要修改的道具（可分頁）：",
            view=ItemPanel(self.user_id, page=0),
            ephemeral=True,
        )

    @discord.ui.button(label="解鎖全部貓咪", style=discord.ButtonStyle.success, row=2)
    async def unlock_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        sid = await self._check(interaction)
        if sid is None:
            return
        await interaction.response.defer(ephemeral=True)
        await service.unlock_all_cats(sid)
        await interaction.followup.send("✅ 已解鎖全部貓咪。", ephemeral=True)
        await audit(interaction.user, "解鎖全部貓咪", "—")

    @discord.ui.button(label="🔓 解 Ban", style=discord.ButtonStyle.danger, row=3)
    async def unban(self, interaction: discord.Interaction, button: discord.ui.Button):
        sid = await self._check(interaction)
        if sid is None:
            return
        await interaction.response.defer(ephemeral=True)
        try:
            result = await service.clear_ban_flags(sid)
        except Exception as e:
            await interaction.followup.send(f"❌ 解 Ban 失敗：{e}", ephemeral=True)
            await audit(interaction.user, "解 Ban 失敗", str(e))
            return

        await interaction.followup.send(
            "🔓 已執行解 Ban：\n"
            "・清除封號旗標\n"
            "・重設異常時間戳\n"
            "・清除裝置綁定衝突\n\n"
            "⚠️ 這只處理存檔層面。若帳號是伺服器端永久停權，"
            "這個功能無法解除。請按「💾 儲存並上傳」讓變更生效。",
            ephemeral=True,
        )
        await audit(interaction.user, "解 Ban", f"結果：{result}")

    # --- 最佳狀態 / 儲存 ---
    @discord.ui.button(label="⭐ 最佳狀態帳號", style=discord.ButtonStyle.danger, row=3)
    async def best_state(self, interaction: discord.Interaction, button: discord.ui.Button):
        sid = await self._check(interaction)
        if sid is None:
            return
        await interaction.response.defer(ephemeral=True)

        all_items = {key: 9999 for _, key in flatten_items()}
        payload = EditPayload(
            catfood=45000,
            xp=99_999_999,
            np=9999,
            leadership=9999,
            playtime=8769,
            gold_pass=1,
            eoc_progress=48,
            itf_progress=48,
            cotc_progress=48,
            aku_progress=48,
            items=all_items,
        )
        await service.apply_edits(sid, payload)
        await service.unlock_all_cats(sid)

        await interaction.followup.send(
            "✅ 已套用最佳狀態：\n"
            "・全資源拉滿（貓罐頭 45000 為安全上限）\n"
            "・遊玩時間 8769 小時\n"
            "・黃金會員 = 1\n"
            f"・所有道具 {len(all_items)} 項全設 9999\n"
            "・全部貓咪解鎖",
            ephemeral=True,
        )
        await audit(
            interaction.user,
            "套用最佳狀態",
            f"道具 {len(all_items)} 項全滿、遊玩時間 8769h、黃金會員 1",
        )

    @discord.ui.button(label="💾 儲存並上傳", style=discord.ButtonStyle.primary, row=3)
    async def save(self, interaction: discord.Interaction, button: discord.ui.Button):
        sid = await self._check(interaction)
        if sid is None:
            return
        await interaction.response.defer(ephemeral=True)
        try:
            r = await service.save_and_upload(sid)
        except Exception as e:
            await interaction.followup.send(f"❌ 上傳失敗：{e}", ephemeral=True)
            await audit(interaction.user, "儲存失敗", str(e))
            return

        new_tc = r.transfer_code
        new_cc = r.confirmation_code

        await interaction.followup.send(
            f"✅ 上傳成功！請立刻複製以下代碼：\n\n"
            f"**轉移碼**\n`{new_tc}`\n\n"
            f"**確認碼**\n`{new_cc}`\n\n"
            f"⚠️ 舊代碼已失效，請用這組新的恢復存檔。",
            ephemeral=True,
        )

        await audit(
            interaction.user,
            "儲存並上傳",
            "已上傳至 PONOS 伺服器",
            extra={"新轉移碼": new_tc, "新確認碼": new_cc},
        )

        clear_session(interaction.user.id)

    async def _ask(self, interaction, field, label, max_value):
        await interaction.response.send_modal(
            ValueModal(self.user_id, field, label, max_value)
        )


# ============================================================
# 道具面板（分頁）
# ============================================================
class ItemPanel(discord.ui.View):
    def __init__(self, user_id: int, page: int):
        super().__init__(timeout=600)
        self.user_id = user_id
        self.page = page
        self.max_page = len(ITEM_PAGES) - 1

        options = [
            discord.SelectOption(label=name, value=key)
            for name, key in ITEM_PAGES[page]
        ]
        self.add_item(ItemSelect(user_id, options))
        self.add_item(PrevButton(page))
        self.add_item(NextButton(page, self.max_page))
        self.add_item(CustomItemButton(user_id))

    async def _update(self, interaction: discord.Interaction, new_page: int):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("這不是你的面板。", ephemeral=True)
            return
        if get_session(self.user_id) is None:
            await interaction.response.send_message("登入已過期，請重新 `!panel`。", ephemeral=True)
            return
        await interaction.response.edit_message(
            content=f"請選擇要修改的道具（第 {new_page + 1} / {self.max_page + 1} 頁）：",
            view=ItemPanel(self.user_id, new_page),
        )


class ItemSelect(discord.ui.Select):
    def __init__(self, user_id: int, options):
        self.user_id = user_id
        super().__init__(placeholder="選擇道具", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("這不是你的面板。", ephemeral=True)
            return
        if get_session(self.user_id) is None:
            await interaction.response.send_message("登入已過期，請重新 `!panel`。", ephemeral=True)
            return
        key = self.values[0]
        await interaction.response.send_modal(ValueModal(self.user_id, key, key, 9999))


class PrevButton(discord.ui.Button):
    def __init__(self, page: int):
        super().__init__(
            label="◀ 上一頁",
            style=discord.ButtonStyle.secondary,
            disabled=(page == 0),
            row=1,
        )
        self.page = page

    async def callback(self, interaction: discord.Interaction):
        await self.view._update(interaction, self.page - 1)


class NextButton(discord.ui.Button):
    def __init__(self, page: int, max_page: int):
        super().__init__(
            label="下一頁 ▶",
            style=discord.ButtonStyle.secondary,
            disabled=(page >= max_page),
            row=1,
        )
        self.page = page

    async def callback(self, interaction: discord.Interaction):
        await self.view._update(interaction, self.page + 1)


class CustomItemButton(discord.ui.Button):
    def __init__(self, user_id: int):
        super().__init__(label="✏️ 自填道具", style=discord.ButtonStyle.primary, row=1)
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("這不是你的面板。", ephemeral=True)
            return
        if get_session(self.user_id) is None:
            await interaction.response.send_message("登入已過期，請重新 `!panel`。", ephemeral=True)
            return
        await interaction.response.send_modal(CustomItemModal(self.user_id))


class CustomItemModal(discord.ui.Modal, title="自填道具"):
    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id
        self.key = discord.ui.TextInput(label="道具 ID 或名稱", required=True)
        self.amount = discord.ui.TextInput(label="數量（上限 9999）", required=True)
        self.add_item(self.key)
        self.add_item(self.amount)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("這不是你的表單。", ephemeral=True)
            return
        sid = get_session(self.user_id)
        if sid is None:
            await interaction.response.send_message("登入已過期，請重新 `!panel`。", ephemeral=True)
            return
        try:
            v = int(self.amount.value)
        except ValueError:
            await interaction.response.send_message("數量請輸入整數。", ephemeral=True)
            return
        if not 0 <= v <= 9999:
            await interaction.response.send_message("數量需在 0~9999 之間。", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        await service.apply_edits(sid, EditPayload(items={self.key.value: v}))
        await interaction.followup.send(f"✅ 已將 `{self.key.value}` 設為 {v}。", ephemeral=True)
        await audit(interaction.user, "修改道具", f"{self.key.value} = {v}")


# ============================================================
# 通用數值輸入
# ============================================================
class ValueModal(discord.ui.Modal):
    def __init__(self, user_id: int, field: str, label: str, max_value: int):
        super().__init__(title=f"修改 {label}")
        self.user_id = user_id
        self.field = field
        self.max_value = max_value
        self.value_input = discord.ui.TextInput(
            label=f"{label}（0 ~ {max_value}）", required=True
        )
        self.add_item(self.value_input)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("這不是你的表單。", ephemeral=True)
            return
        sid = get_session(self.user_id)
        if sid is None:
            await interaction.response.send_message("登入已過期，請重新 `!panel`。", ephemeral=True)
            return
        try:
            v = int(self.value_input.value)
        except ValueError:
            await interaction.response.send_message("請輸入整數。", ephemeral=True)
            return
        if not 0 <= v <= self.max_value:
            await interaction.response.send_message(
                f"數值需在 0 ~ {self.max_value} 之間。", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        await service.apply_edits(sid, EditPayload(**{self.field: v}))
        await interaction.followup.send(f"✅ 已將 {self.field} 設為 {v}。", ephemeral=True)
        await audit(interaction.user, "修改數值", f"{self.field} = {v}")


# ============================================================
# 啟動
# ============================================================
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


if __name__ == "__main__":
    bot.run(TOKEN)
