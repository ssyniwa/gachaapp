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
    {"name": "セリナ", "rarity": "B", "url": "images/serina.png","hp": 10,"exp": 0,"stage": 1},
    {"name": "ファイアボス", "rarity": "A", "url": "images/serina_fireboss.png","hp": 20,"exp": 0,"stage": 1},
    {"name": "アイスボス", "rarity": "S", "url": "images/serina_iceboss.png","hp": 30,"exp": 0,"stage": 1}
]
weights = [0.7, 0.25, 0.05]
# --- クエストのパターン ---
quest_scenarios = [
    ("森でスライムと遊んだ", 10, 5),    # (感想, 消費HP, 獲得EXP)
    ("洞窟で宝箱を見つけた", 20, 15),
    ("強敵と戦った", 30, 30)
]
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
        # 1. 現在のステータス取得（シートから読み込み済みとする）
        current_hp = int(char_data['hp'])
        current_exp = int(char_data['exp'])
        
        if current_hp <= 0:
            st.error("体力がありません！休憩してください。")
        else:
            # 2. クエスト実行
            scenario, hp_cost, exp_gain = random.choice(quest_scenarios)
            new_hp = max(0, current_hp - hp_cost)
            new_exp = current_exp + exp_gain
            
            # 3. 進化判定（経験値が100を超えたら進化）
            new_stage = int(char_data['stage'])
            if new_exp >= 100:
                new_stage += 1
                new_exp = 0 # 進化したら経験値リセット
                st.balloons()
                st.success("おめでとう！進化しました！")
                
            # 4. シート更新
            # 新しい行を追記（または既存行を更新する処理が必要）
            sheet.append_row([user_id, char_data['name'], new_hp, new_exp, new_stage, scenario])
            
            st.write(f"クエスト結果: {scenario}")
            st.write(f"体力: {new_hp}, 経験値: {new_exp}")
            st.rerun()
    
    if st.button("戻る"):
        st.query_params.pop("select")
        st.rerun()
    st.stop()

# 3. ガチャ＆図鑑画面 (メイン画面)
st.title(f"プレイヤー: {user_id} さん")

# ガチャ処理
if st.button("ガチャを引く！"):
    result = random.choices(characters, weights=weights, k=1)[0]
    sheet.append_row([user_id, result['name'], result['rarity'], str(date.today()), result['url'],result['hp'],result['exp'],result['stage'])
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
