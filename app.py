import streamlit as st
import random
import gspread
import pandas as pd
from datetime import date
from oauth2client.service_account import ServiceAccountCredentials

# --- Google Sheets接続 ---
# 接続設定は既存のものを利用
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
client = gspread.authorize(creds)
sheet = client.open("Gacha_DB").sheet1 

# --- キャラクター定義 ---
characters = [
    {"name": "セリナ", "rarity": "B", "url": "images/serina.png"},
    {"name": "ファイアボス", "rarity": "A", "url": "images/serina_fireboss.png"},
    {"name": "アイスボス", "rarity": "S", "url": "images/serina_iceboss.png"}
]
weights = [0.7, 0.25, 0.05]

# --- クエリパラメータ取得 ---
query_params = st.query_params
user_id = query_params.get("user")
selected_char_index = query_params.get("select") # 選択中のキャラの行番号

# 1. ログイン処理
if not user_id:
    st.title("ログイン")
    name_input = st.text_input("プレイヤー名を入力")
    if st.button("ゲーム開始"):
        if name_input:
            st.query_params["user"] = name_input
            st.rerun()
    st.stop()

# データの読み込み
df = pd.DataFrame(sheet.get_all_records())
user_history = df[df['user_id'] == user_id] if not df.empty else pd.DataFrame()

# 2. 育成画面 (selectパラメータがある場合)
if selected_char_index:
    st.title("育成画面")
    idx = int(selected_char_index)
    char_data = user_history.iloc[idx]
    
    st.image(char_data['url'], width=200)
    st.write(f"キャラ: {char_data['name']}")
    
    # 簡易的な育成ボタン
    if st.button("クエストに向かう！"):
        st.write("クエストに行ってきました！（ここをロジック追加）")
    
    if st.button("戻る"):
        st.query_params.pop("select")
        st.rerun()
    st.stop()

# 3. ガチャ＆図鑑画面 (メイン画面)
st.title(f"プレイヤー: {user_id} さん")

# ガチャ処理
if st.button("ガチャを引く！"):
    result = random.choices(characters, weights=weights, k=1)[0]
    sheet.append_row([user_id, result['name'], result['rarity'], str(date.today()), result['url']])
    st.rerun()

st.subheader("コレクション (タップして育成)")
if not user_history.empty:
    for i, row in user_history.iterrows():
        # 各キャラをボタンにして、押すとパラメータが更新される
        if st.button(f"育成する: {row['name']}", key=f"btn_{i}"):
            st.query_params["select"] = i
            st.rerun()
        st.image(row['url'], width=150)
else:
    st.write("まだ何も持っていません")
