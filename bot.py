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
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

def get_record_data():
    r = requests.get(CSV_URL, timeout=30)
    r.raise_for_status()
    return list(csv.reader(io.StringIO(r.text)))

@client.event
async def on_ready():
    await tree.sync()
    print(f"로그인 완료: {client.user}")

@tree.command(name="랭킹", description="던전 랭킹 조회")
async def ranking(interaction: discord.Interaction, 던전명: str):

    data = get_record_data()

    header_row = None

    for row in data:
        if "대궁둥" in row and "신전" in row:
            header_row = row
            break

    if header_row is None:
        await interaction.response.send_message(던전명, "헤더를 찾을 수 없습니다.")
        return

    headers = header_row

    if 던전명 not in headers:
        await interaction.response.send_message(
            f"사용 가능한 던전: {', '.join(headers[:5])}"
        )
        return

    col = headers.index(던전명)
    header_index = data.index(header_row)

    ranking_list = []

    for row in data[header_index + 1:]:

        try:
            ranking_list.append(
                (row[0], int(row[col]))
            )
        except:
            pass

    ranking_list.sort(key=lambda x: x[1])

    msg = f"🏆 {던전명} 랭킹\n\n"

    for i, (name, value) in enumerate(ranking_list, start=1):
        msg += f"{i}위 {name} - {value}\n"

    await interaction.response.send_message(msg)

client.run(TOKEN)
