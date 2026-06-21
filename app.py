import streamlit as st
import random
import gspread
import pandas as pd
from datetime import date
from oauth2client.service_account import ServiceAccountCredentials

# --- Google Sheets接続 ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
client = gspread.authorize(creds)
sheet = client.open("Gacha_DB").sheet1 

# --- クエリパラメータからユーザーを取得 (URL末尾に ?user=名前) ---
query_params = st.query_params
user_id = query_params.get("user", "guest") # 指定がなければguest

st.title(f"ようこそ、{user_id}さん！ 🎲")

# --- キャラクター定義 ---
characters = [
    {"name": "スライム", "rarity": "Normal", "url": "https://example.com/slime.png"},
    {"name": "勇者", "rarity": "Rare", "url": "https://example.com/hero.png"},
    {"name": "ドラゴン", "rarity": "Super Rare", "url": "https://example.com/dragon.png"}
]
weights = [0.7, 0.25, 0.05]

# --- データ読み込み ---
data = sheet.get_all_records()
df = pd.DataFrame(data)

# --- 1日1回制限ロジック ---
today = str(date.today())
# 指定ユーザーの今日の記録があるか
user_history = df[df['user_id'] == user_id] if not df.empty else pd.DataFrame()
already_drawn = not user_history.empty and today in user_history['date'].values

if already_drawn:
    st.warning("今日のガチャは引き終わりました！")
else:
    if st.button("ガチャを引く！"):
        result = random.choices(characters, weights=weights, k=1)[0]
        sheet.append_row([user_id, result['name'], result['rarity'], today, result['url']])
        st.success(f"{result['name']} を引きました！")
        st.rerun()

# --- 図鑑表示 ---
st.subheader("あなたのコレクション")
if not user_history.empty:
    cols = st.columns(3) # 3列で表示
    for i, row in user_history.iterrows():
        with cols[i % 3]:
            st.image(row['image_url'], width=100)
            st.caption(row['name'])
else:
    st.write("まだ何も持っていません")
