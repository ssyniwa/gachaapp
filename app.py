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

st.title(f"ようこそ、{user_id}さん！ 2属性キャラクターガチャ＆放置育成！")

# --- キャラクター定義 ---
characters = [
    {"name": "セリナ", "rarity": "B", "url": "images/serina.png"},
    {"name": "ファイアボス", "rarity": "A", "url": "images/serina_fireboss.png"},
    {"name": "アイスボス", "rarity": "S", "url": "images/serina_iceboss.png"}
]
weights = [0.7, 0.25, 0.05]

# --- ユーザー認証画面 ---
query_params = st.query_params
user_id = query_params.get("user")

if not user_id:
    st.title("ようこそ！")
    name_input = st.text_input("プレイヤー名を入力してください")
    if st.button("ゲーム開始"):
        if name_input:
            # URLを更新して再読み込み
            st.query_params["user"] = name_input
            st.rerun()
        else:
            st.error("名前を入力してください")
    st.stop() # 名前がない場合はここで処理を止める

# --- ログイン後のゲーム画面 ---
st.title(f"プレイヤー: {user_id} さん")

# データの読み込み
data = sheet.get_all_records()
df = pd.DataFrame(data)
user_history = df[df['user_id'] == user_id] if not df.empty else pd.DataFrame()

# ガチャ処理
today = str(date.today())
already_drawn = not user_history.empty and today in user_history['date'].values

if already_drawn:
    st.warning("今日のガチャは引き終わりました！")
else:
    if st.button("ガチャを引く！"):
        result = random.choices(characters, weights=weights, k=1)[0]
        sheet.append_row([user_id, result['name'], result['rarity'], today, result['url']])
        st.success(f"{result['name']} を引きました！")
        st.rerun()

# 図鑑表示
st.subheader("コレクション")
# 図鑑表示部分のループを変更
if not user_history.empty:
    cols = st.columns(3)
    for i, row in user_history.iterrows():
        # レア度に応じたボーダーカラーの設定
        rarity_colors = {
            "B": "blue",
            "A": "red",
            "S": "gold"
        }
        color = rarity_colors.get(row['rarity'], "black")
        
        with cols[i % 3]:
            # 枠線用のdiv開始（HTMLタグ）
            st.markdown(
                f"""
                <div style="border: 3px solid {color}; padding: 10px; border-radius: 15px; 
                            display: flex; flex-direction: column; align-items: center; background-color: #f9f9f9;">
                """,
                unsafe_allow_html=True
            )
            
            st.image(row['url'], width=300) # ここで表示
            st.write(row['name'])
            
            st.markdown("</div>", unsafe_allow_html=True)
else:
    st.write("まだ何も持っていません")

if st.button("別のユーザーで遊ぶ"):
    st.query_params.clear()
    st.rerun()
