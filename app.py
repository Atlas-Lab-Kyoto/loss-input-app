import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

# --- ページ設定 ---
st.set_page_config(page_title="商品ロス購買入力", layout="centered")
st.title("📝 商品ロス購買入力")

# --- 1. スプレッドシートへの接続準備 ---
def get_sheet():
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    # Secretsから暗号鍵を読み込む
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


# --- 2. 入力フォーム ---
st.write("必要事項を入力してください。")

# 雇用形態の選択
emp_type = st.radio("雇用形態", ["正社員", "パート・アルバイト"])
name = st.text_input("お名前")

# 部門の選択（実際のお店の部門名に合わせて並び替えてください）
departments = ["鮮魚", "精肉", "青果", "惣菜", "食品", "レジ", "その他"]
department = st.selectbox("部門", departments)

# シートに合わせた「個数」と「金額」の入力欄
quantity = st.number_input("個数", min_value=1, step=1, value=1)
price = st.number_input("金額（単価）", min_value=0, step=1, value=0)

# アプリ側で「合計金額」を自動計算
total_price = quantity * price

st.markdown("---") # 画面の区切り線


# --- 3. 確認画面 ---
st.markdown("### 📋 入力内容の確認")
st.write(f"**【雇用形態】** {emp_type}")
st.write(f"**【お名前】** {name}")
st.write(f"**【部門】** {department}")
st.write(f"**【個数】** {quantity} 個")
st.write(f"**【金額】** {price:,} 円")
st.write(f"**【合計金額】** {total_price:,} 円") # カンマ区切りで綺麗に表示


# --- 4. チェックボックスと送信処理 ---
confirm = st.checkbox("入力内容に間違いがないことを確認しました")

# チェックが入ったときだけ、送信ボタンを表示
if confirm:
    if name == "":
        st.warning("⚠️ お名前を入力してください。")
    elif price == 0:
        st.warning("⚠️ 金額を入力してください。")
    else:
        if st.button("送信する", type="primary"):
            with st.spinner("スプレッドシートに送信中..."):
                try:
                    # 日本時間の現在時刻を取得
                    jst = pytz.timezone('Asia/Tokyo')
                    now = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')
                    
                    # 🚀 スプレッドシートの列（A列〜G列）の順番に完全に一致させています！
                    # 日付(A), 雇用形態(B), 名前(C), 部門(D), 個数(E), 金額(F), 合計金額(G)
                    row_data = [now, emp_type, name, department, quantity, price, total_price]
                    
                    # 書き込みの実行
                    sheet = get_sheet()
                    sheet.append_row(row_data)
                    
                    st.success("✨ 送信が完了しました！ありがとうございます。")
                    
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")