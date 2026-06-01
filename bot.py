import os
import csv
import io
import requests
import discord
from discord import app_commands

from flask import Flask
from threading import Thread

# =========================
# Render 웹서버
# =========================

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

# =========================
# 설정
# =========================

TOKEN = os.getenv("DISCORD_TOKEN")

SHEET_ID = "1gCHBFS3ZgrURP8IhVzK9zO2n_aKVBX4GPC3SmwhPtsw"

CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

# =========================
# 디스코드
# =========================

intents = discord.Intents.default()

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# =========================
# 시트 읽기
# =========================

def get_record_data():

    r = requests.get(CSV_URL, timeout=30)
    r.raise_for_status()

    rows = list(csv.reader(io.StringIO(r.text)))
    return rows

# =========================
# 봇 시작
# =========================

@client.event
async def on_ready():

    await tree.sync()

    print("================================")
    print(f"로그인 완료: {client.user}")
    print("================================")

# =========================
# 랭킹
# =========================

@tree.command(name="랭킹", description="던전 랭킹 조회")
@app_commands.describe(
    던전명="대궁둥, 신전, 신단, 폐기장"
)
async def ranking(
    interaction: discord.Interaction,
    던전명: str
):

    data = get_record_data()

    header_row = None

    for row in data:

        if "대궁둥" in row and "신전" in row:
            header_row = row
            break

    if header_row is None:

        await interaction.response.send_message(
            "기록표 헤더를 찾을 수 없습니다.",
            ephemeral=True
        )
        return

    headers = header_row

    if 던전명 not in headers:

        await interaction.response.send_message(
            f"던전명을 확인해주세요.\n사용 가능: {', '.join(headers[:5])}",
            ephemeral=True
        )
        return

    col = headers.index(던전명)

    header_index = data.index(header_row)

    ranking_list = []

    for row in data[header_index + 1:]:

        try:

            name = row[0].strip()

            if not name:
                continue

            value = int(row[col])

            ranking_list.append(
                (name, value)
            )

        except:
            continue

    ranking_list.sort(
        key=lambda x: x[1]
    )

    medals = ["🥇", "🥈", "🥉"]

    msg = f"🏆 {던전명} 랭킹\n\n"

    for i, (name, value) in enumerate(ranking_list):

        if i < 3:
            prefix = medals[i]
        else:
            prefix = f"{i+1}위"

        msg += f"{prefix} {name} - {value}\n"

    await interaction.response.send_message(msg)

# =========================
# 개인 기록 조회
# =========================

@tree.command(name="기록", description="캐릭터 기록 조회")
@app_commands.describe(
    닉네임="기록표의 닉네임"
)
async def record(
    interaction: discord.Interaction,
    닉네임: str
):

    data = get_record_data()

    header_row = None

    for row in data:

        if "대궁둥" in row and "신전" in row:
            header_row = row
            break

    if header_row is None:

        await interaction.response.send_message(
            "기록표를 찾을 수 없습니다.",
            ephemeral=True
        )
        return

    header_index = data.index(header_row)

    for row in data[header_index + 1:]:

        try:

            if row[0].strip() == 닉네임:

                msg = (
                    f"📋 {닉네임}\n\n"
                    f"대궁둥 : {row[1]}\n"
                    f"신전 : {row[2]}\n"
                    f"신단 : {row[3]}\n"
                    f"폐기장 : {row[4]}"
                )

                await interaction.response.send_message(msg)
                return

        except:
            continue

    await interaction.response.send_message(
        "닉네임을 찾을 수 없습니다.",
        ephemeral=True
    )

# =========================
# 실행
# =========================

client.run(TOKEN)
