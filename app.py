import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

# --- ページ設定 ---
st.set_page_config(page_title="商品ロス購入入力", page_icon="🐱", layout="centered")
st.title("🐱 商品ロス購入入力")


st.markdown("""
    <style>
    /* 名前・個数・金額の入力ボックス */
    .stTextInput input, .stNumberInput input {
        font-size: 28px !important;
        height: 65px !important;  
        font-weight: 500;
    }
    
    /* 部門選択（セレクトボックス）の微調整 */
    .stSelectbox div[data-baseweb="select"] > div {
        min-height: 60px !important; 
    }
    .stSelectbox div[data-baseweb="select"] * {
        font-size: 28px !important; 
    }

    /* 雇用形態（ラジオボタン）の選択肢 */
    div[data-testid="stRadio"] label p {
        font-size: 24px !important;
    }
    
    /* 「商品追加」や「送信」ボタン */
    .stButton button {
        font-size: 24px !important;
        height: 65px !important;
    }

    /* ☑️ 送信確認チェックボックスの枠と文字を大きく */
    div[data-testid="stCheckbox"] label p {
        font-size: 24px !important; /* 文字を大きく */
    }
    div[data-testid="stCheckbox"] div[role="checkbox"] {
        transform: scale(1.5); /* 四角いチェック枠を1.5倍に拡大 */
        margin-right: 15px;    /* 枠と文字の間に少し余裕を持たせる */
    }
    </style>
""", unsafe_allow_html=True)


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
st.markdown("## 👤 担当者情報")

st.markdown("### 雇用形態")
emp_type = st.radio("雇用形態", ["正社員", "パート・アルバイト"], label_visibility="collapsed")

st.markdown("### お名前")
name = st.text_input("お名前", label_visibility="collapsed")

st.markdown("---")

# --- 4. 商品の入力と「商品追加」ボタン ---
st.markdown("## 🛍️ 商品情報の入力")

st.markdown("### 🏷️ 部門")
department = st.selectbox("部門", departments, label_visibility="collapsed")

st.markdown("### 📦 個数（点）")
quantity = st.number_input("個数（点）", min_value=1, step=1, value=1, label_visibility="collapsed")

st.markdown("### 💰 金額（合計額）")
total_price = st.number_input("金額（合計額）", min_value=0, step=1, value=0, label_visibility="collapsed")

st.write("") # 隙間調整

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
    st.markdown("## 📋 送信待ちリスト")
    
    grand_total = 0
    for idx, item in enumerate(st.session_state.loss_list):
        col1, col2 = st.columns([5, 1])
        
        with col1:
            st.markdown(f"### {idx + 1}. 【{item['dept']}】 {item['qty']}点 / {item['total']:,}円")
        
        with col2:
            if st.button("🗑️ 削除", key=f"delete_{idx}"):
                st.session_state.loss_list.pop(idx)
                st.rerun()
                
        grand_total += item['total']
        
    st.markdown(f"## 📊 総合計: {grand_total:,} 円")
    
    if st.button("リストをすべて消去してやり直す"):
        st.session_state.loss_list = []
        st.rerun()

    st.markdown("---")
    
    # --- 6. チェックボックスと一括送信ボタン ---
    st.markdown("### 送信確認")
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
                            "",             
                            item["total"]   
                        ])
                    
                    sheet = get_sheet()
                    sheet.append_rows(rows_to_append, value_input_option='USER_ENTERED')
                    
                    st.success("✨ すべてのデータをスプレッドシートに送信しました！")
                    st.session_state.loss_list = []
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")
else:
    st.info("💡 まだ商品が追加されていません。上の「商品追加」ボタンを押してください。")