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
    {"name": "アリサ", "rarity": "B", "url": "images/arisa.png","hp": 30,"exp": 0,"stage": 1},
    {"name": "サユリ", "rarity": "A", "url": "images/sayuri.png","hp": 40,"exp": 0,"stage": 1},
    {"name": "シャリー", "rarity": "S", "url": "images/shally.png","hp": 50,"exp": 0,"stage": 1}
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
# --- レベルに応じた画像パス生成関数 ---
def get_image_path(base_url, stage):
    # base_urlが 'images/serina.png' なら、ディレクトリとファイル名に分解してLvを結合
    # 例: images/serina_lv1.png
    base = base_url.rsplit('.', 1)[0] # 拡張子を除去
    return f"{base}_lv{stage}.png"
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
if selected_char_index and selected_char_index.isdigit():
    st.title("育成画面")
    idx = int(selected_char_index)
    
    # DataFrameのインデックス(0始まり)とスプレッドシートの行番号(1始まり+ヘッダー分)を合わせる
    # sheet.get_all_records() はヘッダーを除いた行をリスト化するため、
    # スプレッドシートの実際の行番号は idx + 2 になります
    row_num = idx + 2 
    
    # 現在のステータスを取得（スプレッドシートから最新を再取得）
    current_data = sheet.row_values(row_num)
    # 行データが [user_id, name, rarity, date, url, hp, exp, stage] の順と仮定
    # ※列の順番は適宜調整してください
    name, hp, exp, stage = current_data[1], int(current_data[5]), int(current_data[6]), int(current_data[7])

    current_stage = int(current_data[7])
    display_url = get_image_path(current_data[4], current_stage)
    st.image(display_url, width=200)# URL列
    st.write(f"キャラ: {name} | HP: {hp} | EXP: {exp} | Stage: {stage}")
    
    # クエスト実行ボタン
    if st.button("クエストに向かう！"):
        if hp <= 0:
            st.error("体力がありません！")
        else:
            # 報酬計算（例）
            hp_lost = random.randint(5, 15)
            exp_gain = random.randint(10, 20)
            new_hp = max(0, hp - hp_lost)
            new_exp = exp + exp_gain
            
            # 進化判定
            new_stage = stage
            if new_exp >= 100:
                new_stage += 1
                new_exp = 0
                st.success("レベルアップ！")
            
            # スプレッドシートを更新 (HP, EXP, Stage列を更新)
            sheet.update_cell(row_num, 6, new_hp)   # HP列
            sheet.update_cell(row_num, 7, new_exp)  # EXP列
            sheet.update_cell(row_num, 8, new_stage)# Stage列
            
            st.rerun() # 画面を更新して新しい数値を反映
    
    if st.button("戻る"):
        st.query_params.pop("select")
        st.rerun()
    st.stop()

# 3. ガチャ＆図鑑画面 (メイン画面)
st.title(f"プレイヤー: {user_id} さん")

# ガチャ処理
if st.button("ガチャを引く！"):
    today = str(date.today())
    # 今日のガチャ履歴を確認
    already_drawn = any(user_history['date'] == today)
    
    if already_drawn:
        st.warning("今日のガチャは引き終わりました！")
    else:
        result = random.choices(characters, weights=weights, k=1)[0]
        # 重複チェック：同じキャラ名が既に図鑑にあるか
        if result['name'] in user_history['name'].values:
            st.info(f"{result['name']} は既に持っています！")
        else:
            sheet.append_row([user_id, result['name'], result['rarity'], today, result['url'], result['hp'], result['exp'], result['stage']])
            st.success(f"新しい仲間: {result['name']} を引きました！")
            st.rerun()

st.subheader("コレクション (タップして育成)")
if not user_history.empty:
    for i, row in user_history.iterrows():
        # 各キャラをボタンにして、押すとパラメータが更新される
        if st.button(f"育成する: {row['name']}", key=f"btn_{i}"):
            st.query_params["select"] = i
            st.rerun()
        # 図鑑でもレベルに応じた画像を表示
        display_url = get_image_path(row['url'], row['stage'])
        st.image(display_url, width=150)
else:
    st.write("まだ何も持っていません")
