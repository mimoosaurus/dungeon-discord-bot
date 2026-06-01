import os
import csv
import io
import requests
import discord
from discord import app_commands

from flask import Flask
from threading import Thread
from discord.ext import tasks

TOKEN = os.getenv("DISCORD_TOKEN")
app = Flask(__name__)

@app.route("/")
def home():
    return "Dungeon Bot Running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(
        host="0.0.0.0",
        port=port
    )

Thread(target=run_web, daemon=True).start()
SHEET_ID = "1gCHBFS3ZgrURP8IhVzK9zO2n_aKVBX4GPC3SmwhPtsw"

RECORD_CHANNEL_ID = 1510834661822169261
SCHEDULE_CHANNEL_ID = 1510837403839893615

CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

intents = discord.Intents.default()

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


def get_record_data():
    r = requests.get(CSV_URL, timeout=30)
    r.raise_for_status()

    rows = list(csv.reader(io.StringIO(r.text)))
    return rows


@client.event
async def on_ready():
    await tree.sync()
    print(f"로그인 완료: {client.user}")


@tree.command(name="랭킹", description="던전 랭킹 조회")
@app_commands.describe(던전명="대궁둥, 신전, 신단, 폐기장 중 하나")
async def ranking(interaction: discord.Interaction, 던전명: str):

    data = get_record_data()

header_row = None

for row in data:
    if "대궁둥" in row and "신전" in row:
        header_row = row
        break

if not header_row:
    await interaction.response.send_message(
        "기록표 헤더를 찾을 수 없습니다.",
        ephemeral=True
    )
    return

headers = header_row
header_index = data.index(header_row)

    if 던전명 not in headers:
        await interaction.response.send_message(
            "던전명을 확인해주세요.\n대궁둥 / 신전 / 신단 / 폐기장",
            ephemeral=True
        )
        return

    col = headers.index(던전명)

    ranking_list = []

   for row in data[header_index + 1:]:
        try:
            name = row[0]
            value = int(row[col])

            ranking_list.append((name, value))

        except:
            pass

    ranking_list.sort(key=lambda x: x[1])

    msg = f"🏆 {던전명} 랭킹\n\n"

    medals = ["🥇", "🥈", "🥉"]

    for i, (name, score) in enumerate(ranking_list[:10]):

        if i < 3:
            prefix = medals[i]
        else:
            prefix = f"{i+1}위"

        msg += f"{prefix} {name} - {score}\n"

    await interaction.response.send_message(msg)


@tree.command(name="기록", description="내 기록 보기")
@app_commands.describe(닉네임="기록표에 있는 닉네임")
async def record(interaction: discord.Interaction, 닉네임: str):

    data = get_record_data()

    for row in data[1:]:

        if row[0] == 닉네임:

            msg = (
                f"📋 {닉네임}\n\n"
                f"대궁둥: {row[1]}\n"
                f"신전: {row[2]}\n"
                f"신단: {row[3]}\n"
                f"폐기장: {row[4]}"
            )

            await interaction.response.send_message(msg)
            return

    await interaction.response.send_message("닉네임을 찾을 수 없습니다.", ephemeral=True)


client.run(TOKEN)
