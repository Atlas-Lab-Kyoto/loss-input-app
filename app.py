import streamlit as st
from datetime import datetime
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import time

# =============================================================================
# ページ設定
# =============================================================================
st.set_page_config(
    page_title="商品ロス購買入力", 
    page_icon="🌸", 
    layout="centered"
)

# ⚠️ ご自身のGoogleスプレッドシートIDに書き換えてください
SPREADSHEET_ID = "1PwgH2BifhLuColS8LhUpZuA_yWunfBmSiBYq3dad15c"

# =============================================================================
# メイン画面の構築
# =============================================================================
st.title("🌱 商品ロス購入入力フォーム 🌱")
st.markdown("<p style='text-align: center;'>買う商品をえらんで、最後に「送信」を押してください。</p>", unsafe_allow_html=True)
st.write("")

# 送信完了フラグのチェックと表示
if "show_success" in st.session_state and st.session_state.show_success:
    st.success("✨【送信完了】スプレッドシートへの保存が正常に完了しました！")
    st.balloons()
    st.session_state.show_success = False

# 1. セッション状態の初期化
if "form_rows" not in st.session_state:
    st.session_state.form_rows = [{"id": 0, "dept": "選択してください", "qty": 1, "price": 0}]
if "row_counter" not in st.session_state:
    st.session_state.row_counter = 1

# 手書き伝票に合わせた24部門
departments = [
    '牛肉', '豚肉', '鶏肉', '加工肉', '鮮魚', '塩干', '酒', '野菜', 
    '果物', '酪農品', '乳製品', 'デザート', '飲料', '和日配', 
    '冷食', '卵', '加工食品', '菓子', '幸福堂', '米', 'パティスリ', 
    '惣菜', '冷菜', 'パン'
]

# 2. 基本情報の入力エリア
col_date, col_name = st.columns(2)
with col_date:
    date_val = st.date_input("日付", datetime.now())
with col_name:
    name_val = st.text_input("名前（フルネーム）", placeholder="例：山田 太郎")

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<h4>📋 購入商品の入力</h4>", unsafe_allow_html=True)

valid_rows = []
total_amount = 0

# 商品入力行のループ
for i, row in enumerate(st.session_state.form_rows):
    row_id = row["id"]
    
    c1, c2, c3, c4 = st.columns([3, 1.5, 2, 1])
    
    with c1:
        try:
            default_idx = departments.index(row["dept"]) + 1
        except ValueError:
            default_idx = 0
            
        dept = st.selectbox(
            "部門", ["選択してください"] + departments, 
            index=default_idx, key=f"dept_{row_id}",
            label_visibility="visible" if i == 0 else "collapsed"
        )
    
    with c2:
        qty = st.number_input(
            "個数", min_value=1, value=row["qty"], step=1, key=f"qty_{row_id}",
            label_visibility="visible" if i == 0 else "collapsed"
        )
    
    with c3:
        price = st.number_input(
            "金額 (円)", min_value=0, value=row["price"], step=10, key=f"price_{row_id}",
            label_visibility="visible" if i == 0 else "collapsed"
        )
        
    with c4:
        if len(st.session_state.form_rows) > 1:
            if st.button("❌", key=f"del_{row_id}"):
                st.session_state.form_rows.pop(i)
                st.rerun()
        else:
            st.write("")

    # 入力値の即時反映
    row["dept"] = dept
    row["qty"] = qty
    row["price"] = price

    # 有効な行の計算
    if dept != "選択してください" and price > 0:
        row_total = price * qty  # この行の合計金額を計算
        total_amount += row_total
        
        # スプレッドシートに送るデータ（最後に合計金額を追加しました！）
        valid_rows.append([
            date_val.strftime("%Y-%m-%d"),
            name_val,
            dept,
            int(qty),
            int(price),
            int(row_total)  # 📊 ここで合計金額も一緒にリストに入れます
        ])

# 「商品を追加」ボタン
if st.button("➕ 商品を追加する"):
    st.session_state.form_rows.append({
        "id": st.session_state.row_counter, 
        "dept": "選択してください", 
        "qty": 1, 
        "price": 0
    })
    st.session_state.row_counter += 1
    st.rerun()

st.markdown("<hr>", unsafe_allow_html=True)

# リアルタイム合計金額
st.metric(label="💰 現在の合計金額", value=f"¥ {total_amount:,}")

confirmed = st.checkbox("入力内容に間違いがないことを確認しました。")

# 送信ボタン
submit_button = st.button("🚀 データの送信を完了する")

# 送信ボタンが押された時の処理
if submit_button:
    if not name_val:
        st.error("名前を入力してください。")
    elif len(valid_rows) == 0:
        st.error("購入商品の部門と金額を正しく入力してください。")
    elif not confirmed:
        st.error("「入力内容の確認チェック」を入れてください。")
    else:
        try:
            with st.spinner("🔄 現在、スプレッドシートへデータを送信しています。画面を閉じずに少々お待ちください..."):
                
                # secrets.toml から Google の認証情報を読み込む
                secret_dict = dict(st.secrets["gcp_service_account"])
                
                scopes = ["https://www.googleapis.com/auth/spreadsheets"]
                creds = Credentials.from_service_account_info(secret_dict, scopes=scopes)
                
                # スプレッドシートに接続
                client = gspread.authorize(creds)
                sheet = client.open_by_key(SPREADSHEET_ID).sheet1
                
                # データの追記を実行
                sheet.append_rows(valid_rows, value_input_option="USER_ENTERED")
                
                time.sleep(0.5)
            
            # 完了フラグを立てて画面を再起動
            st.session_state.show_success = True
            st.session_state.form_rows = [{"id": 0, "dept": "選択してください", "qty": 1, "price": 0}]
            st.rerun()
            
        except Exception as e:
            st.error(f"スプレッドシートへの保存中にエラーが発生しました: {e}")