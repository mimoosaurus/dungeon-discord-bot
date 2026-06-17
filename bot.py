import os
import csv
import io
import requests
import discord
from discord import app_commands
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route("/")
def home():
    return "Dungeon Bot Running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_web, daemon=True).start()

TOKEN = os.getenv("DISCORD_TOKEN")

SHEET_ID = "1gCHBFS3ZgrURP8IhVzK9zO2n_aKVBX4GPC3SmwhPtsw"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=725445831"

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

def get_record_data():
    r = requests.get(CSV_URL, timeout=30)
    r.raise_for_status()
    r.encoding = "utf-8"
    return list(csv.reader(io.StringIO(r.text)))


def format_time(value):
    minutes, seconds = divmod(value, 100)
    return f"{minutes}분 {seconds:02d}초"

@client.event
async def on_ready():
    await tree.sync()
    print(f"로그인 완료: {client.user}")

@tree.command(name="랭킹", description="던전 랭킹 조회")
async def ranking(interaction: discord.Interaction, 던전명: str, 닉네임: str = None):

    data = get_record_data()

    header_row = None
    header_index = None

    for i, row in enumerate(data):
        if len(row) < 3 or not row[2].strip():
            continue
        try:
            int(row[2])
        except ValueError:
            header_row = row
            header_index = i
            break

    if header_row is None:
        await interaction.response.send_message("헤더를 찾을 수 없습니다.")
        return

    headers = header_row

    if header_index + 1 >= len(data):
        await interaction.response.send_message("데이터 행이 없습니다.")
        return

    first_data = data[header_index + 1]

    name_col = None
    for i, val in enumerate(first_data):
        if not val.strip():
            continue
        try:
            int(val)
        except ValueError:
            name_col = i
            break
    if name_col is None:
        await interaction.response.send_message("닉네임 컬럼을 찾을 수 없습니다.")
        return

    dungeon_names = []
    for i, h in enumerate(headers):
        if i == name_col or not h.strip():
            continue
        for row in data[header_index + 1:]:
            if i >= len(row) or not row[i].strip():
                continue
            try:
                int(row[i])
                dungeon_names.append(h)
                break
            except ValueError:
                continue

    if 던전명 not in dungeon_names:
        await interaction.response.send_message(
            f"사용 가능한 던전: {', '.join(dungeon_names)}"
        )
        return

    col = headers.index(던전명)

    ranking_list = []

    for row in data[header_index + 1:]:

        try:
            ranking_list.append(
                (row[name_col], int(row[col]))
            )
        except (ValueError, IndexError):
            pass

    ranking_list.sort(key=lambda x: x[1])

    if 닉네임 is not None:
        for rank, (name, value) in enumerate(ranking_list, start=1):
            if name == 닉네임:
                await interaction.response.send_message(
                    f"🏆 {던전명} - {닉네임}\n{rank}위 - {format_time(value)}"
                )
                return
        await interaction.response.send_message(
            f"{닉네임}님의 {던전명} 기록이 없습니다."
        )
        return

    msg = f"🏆 {던전명} 랭킹\n\n"

    for i, (name, value) in enumerate(ranking_list, start=1):
        msg += f"{i}위 {name} - {format_time(value)}\n"

    await interaction.response.send_message(msg)

client.run(TOKEN)
