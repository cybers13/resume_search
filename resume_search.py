import os
import fitz
import pandas as pd
import streamlit as st

PDF_FOLDER = "pdfs"
CACHE_FILE = "resume_db.csv"

os.makedirs(PDF_FOLDER, exist_ok=True)

# PDF → テキスト抽出
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text.strip()

# 名前抽出：1行目を仮の名前とする
def extract_name(text):
    lines = text.split('\n')
    for line in lines:
        if line.strip():
            return line.strip()
    return "不明"

# 履歴書データ生成（PDFから）
def generate_db_from_pdfs():
    data = []
    for filename in os.listdir(PDF_FOLDER):
        if filename.endswith(".pdf"):
            path = os.path.join(PDF_FOLDER, filename)
            text = extract_text_from_pdf(path)
            name = extract_name(text)
            data.append({
                "ファイル名": filename,
                "名前": name,
                "テキスト全文": text
            })
    df = pd.DataFrame(data)
    df.to_csv(CACHE_FILE, index=False)
    return df

# DB読み込み（CSV優先 / PDFがあれば自動生成）
def load_or_create_db():
    if os.path.exists(CACHE_FILE):
        df = pd.read_csv(CACHE_FILE)
    elif os.path.exists(PDF_FOLDER) and os.listdir(PDF_FOLDER):
        df = generate_db_from_pdfs()
    else:
        df = pd.DataFrame(columns=["ファイル名", "名前", "テキスト全文"])
    return df

# 検索処理（名前 or テキスト全文）
def filter_df(df, keyword):
    if not keyword:
        return df
    keyword = keyword.lower()
    return df[df.apply(lambda row:
        keyword in str(row.get("名前", "")).lower() or
        keyword in str(row.get("テキスト全文", "")).lower(),
        axis=1
    )]

# Streamlitアプリ本体
def main():
    st.set_page_config(page_title="履歴書検索", layout="wide")
    st.title("📄 履歴書検索システム")

    st.markdown("### 🔍 名前またはキーワードを入力してください")
    keyword = st.text_input("検索ワード", "")

    df = load_or_create_db()
    result_df = filter_df(df, keyword)

    st.markdown(f"### 結果一覧（{len(result_df)} 件）")
    for _, row in result_df.iterrows():
        with st.expander(f"👤 {row.get('名前', '不明')}｜{row.get('ファイル名', '不明')}"):
            st.write(row.get("テキスト全文", "（内容なし）")[:2000] + "...")
            if row.get("ファイル名", "").endswith(".pdf"):
                file_path = os.path.join(PDF_FOLDER, row["ファイル名"])
                if os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        st.download_button("📎 PDFをダウンロード", f.read(), file_name=row["ファイル名"])

if __name__ == "__main__":
    main()