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
    {"name": "アリサ", "rarity": "A", "url": "images/arisa.png","hp": 30,"exp": 0,"stage": 1},
    {"name": "サユリ", "rarity": "A", "url": "images/sayuri.png","hp": 30,"exp": 0,"stage": 1},
    {"name": "シャリー", "rarity": "S", "url": "images/shally.png","hp": 40,"exp": 0,"stage": 1}
]
weights = [0.4, 0.4, 0.2]
# --- クエストのパターン ---
# --- クエストプールの定義 ---
# ステージごとにクエストを分ける
quest_pools = {
    1: [("森を探索した", 20, 20), ("エリアボススライムを倒した", 30, 30)],
    2: [("洞窟を探索した", 30, 30), ("エリアボスコウモリを倒した", 40, 40)],
    3: [("古の遺跡を探索した", 40, 40), ("エリアボスゴーレムを倒した", 50, 50)],
    4: [("灼熱の火口を探索した", 50, 50), ("エリアボスファイアゴーレムを倒した", 60, 60)],
    5: [("極寒の地を探索した", 60, 60), ("ボスアイスフェアリーを倒した", 70, 70)],
    6: [("暴風の草原を探索した", 70, 70), ("ボスウィンドウルフを倒した", 80, 80)],
    7: [("雷撃の丘を探索した", 80, 80), ("ボスサンダーバードを倒した", 90, 90)],
    8: [("毒霧の沼を探索した", 90, 90), ("ボスポイズンフロッグを倒した", 100, 100)],
    9: [("天空の城を探索した", 100, 100), ("ボスコピーゴッドを倒した", 110, 110)],
    10: [("悪魔の拠点を探索した", 110, 110), ("ボスブラックドラゴンを倒した", 120, 120)]  
}
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
# ステージが高すぎる場合は、最大レベルのプールを参照する工夫
def get_quest_for_stage(stage):
    return quest_pools.get(stage, quest_pools[3])
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
    # 最後に更新された日を管理するための列が必要です（今回は一旦date列を流用するか、最新更新日列を追加してください）
    # 今回は簡易的に、クエストに行くたびに日付を更新する前提にします
    last_quest_date = current_data[3] # 4列目が日付と仮定
    today = str(date.today())
    
    # 日付が変わっていたらHP全回復処理
    if last_quest_date != today and int(current_data[5]) == 0: # HPが0の時または日付経過時
        sheet.update_cell(row_num, 6, 30) # 全回復（キャラの初期HPなど）
        sheet.update_cell(row_num, 4, today) # 日付を更新
        st.info("日付が変わったのでHPが全回復しました！")
        
    # 行データが [user_id, name, rarity, date, url, hp, exp, stage] の順と仮定
    # ※列の順番は適宜調整してください
    name, hp, exp, stage = current_data[1], int(current_data[5]), int(current_data[6]), int(current_data[7])

    current_stage = int(current_data[7])
    display_url = get_image_path(current_data[4], current_stage)
    st.image(display_url, width=400)# URL列
    st.write(f"キャラ: {name} | HP: {hp} | EXP: {exp} | Stage: {stage}")
    
    # クエスト実行ボタン
    if st.button("クエストに向かう！"):
        if hp <= 0:
            st.error("体力がありません！")
        else:
            # 報酬計算（例）
            # 1. ステージに応じたクエストをランダム選択
            current_pool = get_quest_for_stage(stage)
            scenario, hp_cost, exp_gain = random.choice(current_pool)
            new_hp = max(0, hp - hp_cost)
            new_exp = exp + exp_gain
            
            # 進化判定
            new_stage = stage
            if new_exp >= 500:
                new_stage += 1
                new_hp += 10
                new_exp = 0
                st.balloons()
                st.success(f"おめでとう！ステージ{new_stage}に進化しました！")
            
            # スプレッドシートを更新 (HP, EXP, Stage列を更新)
            sheet.update_cell(row_num, 6, new_hp)   # HP列
            sheet.update_cell(row_num, 7, new_exp)  # EXP列
            sheet.update_cell(row_num, 8, new_stage)# Stage列
            sheet.update_cell(row_num, 9, scenario)   # 新設: last_quest_txt列
            # 5. 結果表示
            st.write(f"クエスト結果: {scenario}")
            st.rerun()
    
    if st.button("戻る"):
        st.query_params.pop("select")
        st.rerun()
    st.stop()

# 3. ガチャ＆図鑑画面 (メイン画面)
st.title(f"プレイヤー: {user_id} さん")

# --- ガチャ処理の修正 ---
if st.button("ガチャを引く！"):
    today = str(date.today())
    
    already_drawn = False
    if not user_history.empty and 'date' in user_history.columns:
        already_drawn = today in user_history['date'].values
    
    if already_drawn:
        st.warning("今日のガチャは引き終わりました！")
    else:
        result = random.choices(characters, weights=weights, k=1)[0]
        
        # 重複チェックの修正
        # 'name'列が正しく存在するか確認
        if not user_history.empty and 'name' in user_history.columns:
            is_duplicate = result['name'] in user_history['name'].values
        else:
            is_duplicate = False
            
        if is_duplicate:
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
        st.image(display_url, width=300)
else:
    st.write("まだ何も持っていません")
