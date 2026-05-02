import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from typing import Optional

# ===== KEEP ALIVE =====
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "OK", 200

def run_web():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web, daemon=True)
    t.start()

# ===== BOT SETUP =====

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "name.json"
IMAGE_DIR = "img"

os.makedirs(IMAGE_DIR, exist_ok=True)

# ------------------ JSON ------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "servers": {}}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"users": {}, "servers": {}}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_user(data, uid):
    uid = str(uid)
    data["users"].setdefault(uid, {"profiles": {}, "channels": []})
    return data["users"][uid]


def get_server(data, gid):
    gid = str(gid)
    data["servers"].setdefault(gid, {"profiles": {}, "channels": []})
    return data["servers"][gid]


def resolve_profile(data, name, uid, gid):
    user = data["users"].get(str(uid), {})
    if name in user.get("profiles", {}):
        return user["profiles"][name]

    if gid:
        server = data["servers"].get(str(gid), {})
        if name in server.get("profiles", {}):
            return server["profiles"][name]

    return None


async def save_image(att, owner, name):
    safe = name.replace("/", "_").replace("\\", "_").replace("@", "")
    ext = os.path.splitext(att.filename)[1] or ".png"
    path = f"{IMAGE_DIR}/{owner}_{safe}{ext}"
    await att.save(path)
    return path


# ------------------ CREATE ------------------

@bot.hybrid_command()
async def create(ctx, name: str, scope: Optional[str] = "user", avatar: Optional[discord.Attachment] = None):
    scope = scope.lower()

    if scope == "server":
        if not ctx.guild:
            return await ctx.send("❌ ใช้ในเซิร์ฟเวอร์เท่านั้น")
        if not ctx.author.guild_permissions.manage_guild:
            return await ctx.send("❌ ต้องมีสิทธิ์ Manage Server")

    att = avatar or (ctx.message.attachments[0] if ctx.message.attachments else None)
    if not att:
        return await ctx.send("❌ แนบรูปด้วย")

    data = load_data()

    if scope == "user":
        bucket = get_user(data, ctx.author.id)
        owner = f"u{ctx.author.id}"
    else:
        bucket = get_server(data, ctx.guild.id)
        owner = f"g{ctx.guild.id}"

    if name in bucket["profiles"]:
        old = bucket["profiles"][name]["avatar"]
        if os.path.exists(old):
            os.remove(old)
        await ctx.send(f"⚠️ ชื่อ `{name}` ซ้ำ ลบของเก่าแล้ว")

    path = await save_image(att, owner, name)

    bucket["profiles"][name] = {"name": name, "avatar": path}
    save_data(data)

    await ctx.send(f"✅ สร้าง `{name}` แล้ว")


# ------------------ ROOM ------------------

@bot.hybrid_command()
async def addroom(ctx, scope: Optional[str] = "user"):
    data = load_data()

    if scope == "server":
        if not ctx.guild:
            return
        bucket = get_server(data, ctx.guild.id)
    else:
        bucket = get_user(data, ctx.author.id)

    if ctx.channel.id not in bucket["channels"]:
        bucket["channels"].append(ctx.channel.id)

    save_data(data)
    await ctx.send("✅ เพิ่มห้องแล้ว")


# ------------------ WEBHOOK ------------------

async def get_webhook(channel):
    hooks = await channel.webhooks()
    for h in hooks:
        if h.name == "PersonaBot":
            return h
    return await channel.create_webhook(name="PersonaBot")


# ------------------ MESSAGE ------------------

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    data = load_data()

    uid = str(message.author.id)
    gid = str(message.guild.id) if message.guild else None

    user = data["users"].get(uid, {"channels": []})
    server = data["servers"].get(gid, {"channels": []}) if gid else {"channels": []}

    if message.channel.id not in user.get("channels", []) and message.channel.id not in server.get("channels", []):
        return await bot.process_commands(message)

    if ":" not in message.content:
        return await bot.process_commands(message)

    name, text = message.content.split(":", 1)
    name = name.strip()
    text = text.strip()

    profile = resolve_profile(data, name, uid, gid)
    if not profile:
        return await bot.process_commands(message)

    if not text and not message.attachments:
        return await message.channel.send("❌ ข้อความว่าง")

    webhook = await get_webhook(message.channel)
    files = [await a.to_file() for a in message.attachments]

    temp_webhook = None
    if profile.get("avatar") and os.path.exists(profile["avatar"]):
        with open(profile["avatar"], "rb") as f:
            avatar_bytes = f.read()
        temp_webhook = await message.channel.create_webhook(
            name="temp",
            avatar=avatar_bytes
        )
        webhook = temp_webhook

    await webhook.send(
        content=text,
        username=profile["name"],
        files=files if files else discord.utils.MISSING,
        allowed_mentions=discord.AllowedMentions.none()
    )

    if temp_webhook:
        try:
            await temp_webhook.delete()
        except:
            pass

    try:
        await message.delete()
    except:
        pass


# ------------------ READY ------------------

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ {bot.user} ready")


@bot.event
async def on_disconnect():
    print("⚠️ Bot disconnected จาก Discord กำลัง reconnect...")


@bot.event
async def on_resumed():
    print("🔄 Bot reconnected แล้ว")


# ------------------ RUN ------------------

import time

token = os.getenv("DISCORD_BOT_TOKEN")

if not token:
    raise Exception("❌ ไม่พบ TOKEN")

keep_alive()

while True:
    try:
        bot.run(token, reconnect=True)
    except Exception as e:
        print(f"❌ Bot crash: {e}")
        print("🔁 รอ 5 วินาทีแล้ว restart...")
        time.sleep(5)
        bot = commands.Bot(command_prefix="!", intents=intents)
