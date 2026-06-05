import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

# --- ページ設定 ---
st.set_page_config(page_title="商品ロス購入入力", page_icon="🐱", layout="centered")
st.title("🐱 商品ロス購入入力")

# --- 1. スプレッドシートへの接続準備 ---
def get_sheet():
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    gc = gspread.authorize(credentials)
    
    # ⚠️ 【重要】ここに実際の「スプレッドシートのキー」を入れてください
    SPREADSHEET_KEY = "1PwgH2BifhLuColS8LhUpZuA_yWunfBmSiBYq3dad15c" 
    WORKSHEET_NAME = "購入商品" # 実際のシート名に変更してください
    
    worksheet = gc.open_by_key(SPREADSHEET_KEY).worksheet(WORKSHEET_NAME)
    return worksheet

# --- 2. 【設定エリア】お店の部門リスト ---
# ⚠️ 実際の24部門に書き換えてください
departments = [
    '牛肉', '豚肉', '鶏肉', '加工肉', '鮮魚', '塩干', '酒', '野菜',
    '果物', '酪農品', '乳製品', 'デザート', '飲料', '和日配',
    '冷食', '卵', '加工食品', '菓子', '幸福堂', '米', 'パティスリ',
    '惣菜', '冷菜', 'パン'
]

# --- セッション状態（一時保存用リスト）の初期化 ---
if "loss_list" not in st.session_state:
    st.session_state.loss_list = []

# --- 3. 基本情報の入力 ---
st.write("必要事項を入力してください。")

emp_type = st.radio("雇用形態", ["正社員", "パート・アルバイト"])
name = st.text_input("お名前")

st.markdown("---")

# --- 4. 商品の入力と「商品追加」ボタン ---
st.write("🛍️ ロス商品の情報を入力して、下の「商品追加」を押してください。")

department = st.selectbox("部門", departments)
quantity = st.number_input("個数（点）", min_value=1, step=1, value=1)

# 💡 修正①：単価の掛け算を廃止し、各自が合算した金額を直接入力する形に変更
total_price = st.number_input("金額（合計額）", min_value=0, step=1, value=0)

# 商品追加ボタン
if st.button("➕ 商品追加", use_container_width=True):
    if name == "":
        st.warning("⚠️ お名前を入力してください。")
    elif total_price == 0:
        st.warning("⚠️ 金額を入力してください。")
    else:
        jst = pytz.timezone('Asia/Tokyo')
        current_date = datetime.now(jst).strftime('%Y-%m-%d')
        
        item_entry = {
            "date": current_date,
            "emp_type": emp_type,
            "name": name,
            "dept": department,
            "qty": quantity,
            "total": total_price
        }
        st.session_state.loss_list.append(item_entry)
        st.success(f"「{department}」の商品（{total_price:,}円）をリストに追加しました！")

st.markdown("---")

# --- 5. 追加された商品の一覧表示（確認画面） ---
if st.session_state.loss_list:
    st.markdown("### 📋 送信待ちの商品リスト")
    
    grand_total = 0
    for idx, item in enumerate(st.session_state.loss_list):
        col1, col2 = st.columns([5, 1])
        
        with col1:
            # 💡 修正②：名前の表示を消し、文字サイズを大きく（###を使用）して視認性をアップ
            st.markdown(f"### {idx + 1}. 【{item['dept']}】 {item['qty']}点 / {item['total']:,}円")
        
        with col2:
            if st.button("🗑️ 削除", key=f"delete_{idx}"):
                st.session_state.loss_list.pop(idx)
                st.rerun()
                
        grand_total += item['total']
        
    # 総合計もさらに大きく表示
    st.markdown(f"## 📊 総合計: {grand_total:,} 円")
    
    if st.button("リストをすべて消去してやり直す"):
        st.session_state.loss_list = []
        st.rerun()

    st.markdown("---")
    
    # --- 6. チェックボックスと一括送信ボタン ---
    confirm = st.checkbox("入力内容に間違いがないことを確認しました")

    if confirm:
        if st.button("🚀 スプレッドシートに送信する", type="primary", use_container_width=True):
            with st.spinner("スプレッドシートに送信中..."):
                try:
                    rows_to_append = []
                    for item in st.session_state.loss_list:
                        rows_to_append.append([
                            item["date"],
                            item["emp_type"],
                            item["name"],
                            item["dept"],
                            item["qty"],
                            "",             # F列（単価）は使わないため空欄で送信
                            item["total"]   # G列（合計金額）に入力された合計額を送信
                        ])
                    
                    sheet = get_sheet()
                    # 前回修正した日付認識の魔法（USER_ENTERED）もそのまま維持しています
                    sheet.append_rows(rows_to_append, value_input_option='USER_ENTERED')
                    
                    st.success("✨ すべてのデータをスプレッドシートに送信しました！")
                    st.session_state.loss_list = []
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")
else:
    st.info("💡 まだ商品が追加されていません。上の「商品追加」ボタンを押してください。")