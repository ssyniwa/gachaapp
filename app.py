import streamlit as st
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import date

# --- Google Sheetsの設定 ---
# SecretにJSONの中身を保存することをお勧めします
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
client = gspread.authorize(creds)
sheet = client.open("Gacha_DB").sheet1 # スプレッドシート名

# --- ゲーム設定 ---
characters = [
    {"name": "スライム", "rarity": "Normal", "emoji": "💧"},
    {"name": "勇者", "rarity": "Rare", "emoji": "🛡️"},
    {"name": "ドラゴン", "rarity": "Super Rare", "emoji": "🐲"}
]
weights = [0.7, 0.25, 0.05]

st.title("スプレッドシート連動ガチャ 🎲")

# 1. データの読み込み
data = sheet.get_all_records()
df = pd.DataFrame(data)

# 2. ガチャボタン (1日1回制限のロジック)
today = str(date.today())
last_draw_date = df[df['user_id'] == 'me']['date'].max() if not df.empty else None

if last_draw_date == today:
    st.warning("今日のガチャは引き終わりました！")
else:
    if st.button("ガチャを引く！"):
        result = random.choices(characters, weights=weights, k=1)[0]
        # スプレッドシートに追記
        sheet.append_row(['me', result['name'], today])
        st.success(f"結果: {result['name']} {result['emoji']} が出た！")
        if result['rarity'] == "Super Rare":
            st.balloons()
        st.rerun()

# 3. 図鑑表示
st.subheader("あなたの図鑑")
if not df.empty:
    st.table(df[['name', 'date']])
else:
    st.write("まだ引いていません")
