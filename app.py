import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

# --- ページ設定 ---
st.set_page_config(page_title="商品ロス購入入力", layout="centered")
st.title("🐈 商品ロス購入入力")

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


# --- セッション状態（一時保存用リスト）の初期化 ---
if "loss_list" not in st.session_state:
    st.session_state.loss_list = []


# --- 2. 基本情報の入力 ---
st.write("必要事項を入力してください。")

emp_type = st.radio("雇用形態", ["正社員", "パート・アルバイト"])
name = st.text_input("お名前")

st.markdown("---")


# --- 3. 商品の入力と「商品追加」ボタン ---
st.write("🐈 ロスにする商品の情報を入力して、下の「商品追加」を押してください。")

departments = ['牛肉', '豚肉', '鶏肉', '加工肉', '鮮魚', '塩干', '酒', '野菜',
    '果物', '酪農品', '乳製品', 'デザート', '飲料', '和日配',
    '冷食', '卵', '加工食品', '菓子', '幸福堂', '米', 'パティスリ',
    '惣菜', '冷菜', 'パン']
department = st.selectbox("部門", departments)

quantity = st.number_input("個数", min_value=1, step=1, value=1)
price = st.number_input("金額（単価）", min_value=0, step=1, value=0)

total_price = quantity * price
st.write(f"現在の商品の合計: {total_price:,} 円")

# 商品追加ボタン
if st.button("➕ 商品追加", use_container_width=True):
    if name == "":
        st.warning("⚠️ お名前を入力してください。")
    elif price == 0:
        st.warning("⚠️ 金額を入力してください。")
    else:
        # 日本時間の日付を裏で自動取得
        jst = pytz.timezone('Asia/Tokyo')
        current_date = datetime.now(jst).strftime('%Y-%m-%d')
        
        item_entry = {
            "date": current_date,
            "emp_type": emp_type,
            "name": name,
            "dept": department,
            "qty": quantity,
            "price": price,
            "total": total_price
        }
        st.session_state.loss_list.append(item_entry)
        st.success(f"「{department}」の商品（{total_price:,}円）をリストに追加しました！")

st.markdown("---")


# --- 4. 追加された商品の一覧表示（確認画面） ---
if st.session_state.loss_list:
    st.markdown("### 📋 送信待ちの商品リスト")
    
    grand_total = 0
    # 🛠️ 各商品の横に削除ボタンを並べるために、画面を横に分割（分割比率 5:1）します
    for idx, item in enumerate(st.session_state.loss_list):
        col1, col2 = st.columns([5, 1])
        
        with col1:
            # 左側に商品の詳細を表示
            st.write(f"**{idx + 1}. 【{item['dept']}】** {item['qty']}個 × {item['price']:,}円 ＝ **{item['total']:,}円** （入力: {item['name']}さん）")
        
        with col2:
            # 右側にその行専用の削除ボタンを配置（keyを1件ずつ変えるのがコツです）
            if st.button("🗑️ 削除", key=f"delete_{idx}"):
                st.session_state.loss_list.pop(idx) # リストからこの1件だけを削除
                st.rerun() # 画面をパッと再描画
                
        grand_total += item['total']
        
    st.markdown(f"📊 **現在の総合計金額: {grand_total:,} 円**")
    
    # 全消去ボタンも一応残しておきます
    if st.button("リストをすべて消去してやり直す"):
        st.session_state.loss_list = []
        st.rerun()

    st.markdown("---")
    
    # --- 5. チェックボックスと一括送信ボタン ---
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
                            item["price"],
                            item["total"]
                        ])
                    
                    sheet = get_sheet()
                    sheet.append_rows(rows_to_append)
                    
                    st.success("✨ すべてのデータをスプレッドシートに送信しました！")
                    st.session_state.loss_list = []
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")
else:
    st.info("💡 まだ商品が追加されていません。上の「商品追加」ボタンを押してください。")