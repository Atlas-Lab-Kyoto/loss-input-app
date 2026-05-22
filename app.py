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
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    gc = gspread.authorize(credentials)
    
    # ⚠️ 【重要】ここに実際の「スプレッドシートのキー」を入れてください
    SPREADSHEET_KEY = "ここにスプレッドシートのキー（URLの一部）を入れます" 
    WORKSHEET_NAME = "シート1" # 実際のシート名に変更してください
    
    worksheet = gc.open_by_key(SPREADSHEET_KEY).worksheet(WORKSHEET_NAME)
    return worksheet


# --- セッション状態（一時保存用リスト）の初期化 ---
if "loss_list" not in st.session_state:
    st.session_state.loss_list = []


# --- 2. 基本情報の入力 ---
st.write("必要事項を入力してください。")

# 雇用形態とお名前（日付入力欄は消してスッキリさせました！）
emp_type = st.radio("雇用形態", ["正社員", "パート・アルバイト"])
name = st.text_input("お名前")

st.markdown("---")


# --- 3. 商品の入力と「商品追加」ボタン ---
st.write("🛍️ ロスにする商品の情報を入力して、下の「商品追加」を押してください。")

# 部門・個数・金額の入力
departments = ["鮮魚", "精肉", "青果", "惣菜", "食品", "レジ", "その他"]
department = st.selectbox("部門", departments)

quantity = st.number_input("個数", min_value=1, step=1, value=1)
price = st.number_input("金額（単価）", min_value=0, step=1, value=0)

# 合計金額の自動計算
total_price = quantity * price
st.write(f"現在の商品の合計: {total_price:,} 円")

# 🛠️ 商品追加ボタン
if st.button("➕ 商品追加", use_container_width=True):
    if name == "":
        st.warning("⚠️ お名前を入力してください。")
    elif price == 0:
        st.warning("⚠️ 金額を入力してください。")
    else:
        # 【自動化】商品追加を押した瞬間の「日本時間の日付」を裏で自動取得します
        jst = pytz.timezone('Asia/Tokyo')
        current_date = datetime.now(jst).strftime('%Y-%m-%d') # 「2026-05-22」の形で記録
        
        # データを一時的にリストにキープ
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
    for idx, item in enumerate(st.session_state.loss_list):
        st.write(f"**{idx + 1}. 【{item['dept']}】** {item['qty']}個 × {item['price']:,}円 ＝ **{item['total']:,}円** （入力: {item['name']}さん）")
        grand_total += item['total']
        
    st.markdown(f"📊 **現在の総合計金額: {grand_total:,} 円**")
    
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
                    # 溜まったデータをスプレッドシートの列（A列〜G列）の順に並べる
                    rows_to_append = []
                    for item in st.session_state.loss_list:
                        rows_to_append.append([
                            item["date"],       # A列に自動取得した日付が入ります
                            item["emp_type"],   # B列
                            item["name"],       # C列
                            item["dept"],       # D列
                            item["qty"],        # E列
                            item["price"],      # F列
                            item["total"]       # G列
                        ])
                    
                    # まとめて一括書き込み！
                    sheet = get_sheet()
                    sheet.append_rows(rows_to_append)
                    
                    st.success("✨ すべてのデータをスプレッドシートに送信しました！")
                    
                    # 送信が完了したらリストを空にする
                    st.session_state.loss_list = []
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")
else:
    st.info("💡 まだ商品が追加されていません。上の「商品追加」ボタンを押してください。")