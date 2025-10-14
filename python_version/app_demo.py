"""
有給休暇管理システム - Streamlit版（デモモード：ローカルJSON使用）
Firebaseなしで動作するスタンドアロン版
"""
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from typing import List

from utils.data_models import Employee, Department, Grant, Take, generate_employee_code, generate_uuid
from utils.calculations import (
    calculate_remaining_days, 
    auto_populate_grants,
    get_statutory_grant_schedule,
    round_to_decimal
)


# データファイルのパス
DATA_DIR = "demo_data"
EMPLOYEES_FILE = os.path.join(DATA_DIR, "employees.json")
DEPARTMENTS_FILE = os.path.join(DATA_DIR, "departments.json")


# ページ設定
st.set_page_config(
    page_title="有給休暇管理システム（デモ版）",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS - 夏の旅行計画書スタイル
st.markdown("""
<style>
    /* Streamlitのヘッダーバーを非表示 */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    /* Streamlitのツールバーを非表示 */
    .stDeployButton {
        display: none !important;
    }
    
    /* 上部のパディングを調整 */
    .main .block-container {
        padding-top: 2rem !important;
    }
    
    /* 全体背景 - 水色グラデーション */
    .stApp {
        background: linear-gradient(180deg, #bfe5f0 0%, #e6f7fb 50%, #ffffff 100%) !important;
    }
    
    .main {
        background: transparent !important;
    }
    
    /* メインコンテンツエリア */
    .block-container {
        background-color: transparent !important;
        max-width: 1200px;
    }
    
    /* 全ての要素の背景をリセット */
    section[data-testid="stSidebar"],
    .element-container,
    div[data-testid="stVerticalBlock"],
    div[data-testid="stHorizontalBlock"] {
        background-color: transparent !important;
    }
    
    /* メインヘッダー - 画像と同じスタイル */
    .main-header {
        text-align: center;
        padding: 2rem 1rem 1.5rem 1rem;
        background-color: transparent;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: #7a9cb8;
        font-weight: 500;
        font-size: 2.5rem;
        margin: 0;
        letter-spacing: 0.05em;
    }
    .main-header p {
        color: #8fa9bd;
        font-size: 0.95rem;
        margin-top: 0.8rem;
    }
    
    /* 残日数カード - 白いカードに（画像スタイル） */
    .stat-card {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 1.2rem;
        border: none;
        box-shadow: 0 3px 12px rgba(127, 165, 200, 0.15);
        margin-bottom: 2rem;
    }
    .stat-card h3 {
        color: #7a9cb8;
        font-weight: 500;
        font-size: 1.1rem;
        margin-bottom: 1rem;
    }
    .remaining-days {
        font-size: 3rem;
        font-weight: 700;
        color: #7fb5d4;
    }
    
    /* ボタン - 画像と同じセクションヘッダー風 */
    .stButton>button {
        background-color: #89b4d6;
        color: #ffffff;
        border: none;
        border-radius: 0.6rem;
        font-weight: 500;
        padding: 0.7rem 1.8rem;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(127, 165, 200, 0.2);
    }
    .stButton>button:hover:not(:disabled) {
        background-color: #7fb5d4;
        box-shadow: 0 4px 12px rgba(127, 165, 200, 0.3);
        transform: translateY(-1px);
    }
    /* 無効化されたボタン */
    .stButton>button:disabled {
        background-color: #d0d0d0 !important;
        color: #808080 !important;
        cursor: not-allowed !important;
        opacity: 0.6 !important;
        box-shadow: none !important;
    }
    
    /* プライマリボタン */
    .stButton>button[kind="primary"] {
        background-color: #7fb5d4;
        color: #ffffff;
        font-weight: 600;
    }
    .stButton>button[kind="primary"]:disabled {
        background-color: #d0d0d0 !important;
        color: #808080 !important;
        font-weight: 600;
    }
    .stButton>button[kind="primary"]:hover:not(:disabled) {
        background-color: #6da8c9;
    }
    
    /* カード風のコンテナ - 白いカード */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
        background-color: #ffffff;
        border-radius: 1.2rem;
        padding: 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 3px 12px rgba(127, 165, 200, 0.12);
    }
    
    /* エクスパンダー - 強制的に明るい色に */
    .streamlit-expanderHeader,
    .streamlit-expanderHeader *,
    summary.streamlit-expanderHeader,
    details summary,
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] > summary {
        background: linear-gradient(180deg, #d4e8f3 0%, #c4dff0 100%) !important;
        border-radius: 0.6rem !important;
        color: #6b8fa8 !important;
        font-weight: 500 !important;
        border: none !important;
        padding: 0.8rem 1.2rem !important;
    }
    .streamlit-expanderHeader:hover,
    details summary:hover,
    [data-testid="stExpander"] summary:hover {
        background: linear-gradient(180deg, #c4dff0 0%, #b4d5e8 100%) !important;
    }
    .streamlit-expanderHeader svg,
    details summary svg,
    [data-testid="stExpander"] summary svg {
        fill: #6b8fa8 !important;
        color: #6b8fa8 !important;
    }
    details[open] > summary,
    [data-testid="stExpander"][open] > summary {
        border-bottom: 2px solid rgba(230, 247, 251, 0.5) !important;
        margin-bottom: 1rem !important;
        background: linear-gradient(180deg, #d4e8f3 0%, #c4dff0 100%) !important;
    }
    
    /* エクスパンダーの中身 */
    details[open],
    [data-testid="stExpander"][open] {
        background-color: #ffffff !important;
        border-radius: 0.8rem !important;
        padding: 0.5rem !important;
    }
    
    /* エクスパンダー全体のコンテナ */
    [data-testid="stExpander"] {
        background-color: transparent !important;
        border: none !important;
    }
    
    /* テーブル - 完全に白背景 */
    table {
        background-color: #ffffff !important;
        border-radius: 0.8rem;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(191, 229, 240, 0.15);
    }
    thead {
        background-color: transparent !important;
    }
    thead tr {
        background-color: transparent !important;
    }
    thead tr th {
        background: linear-gradient(180deg, #d4e8f3 0%, #c4dff0 100%) !important;
        color: #6b8fa8 !important;
        font-weight: 500 !important;
        border: none !important;
        padding: 1rem !important;
        border-bottom: 2px solid #b8d9ed !important;
    }
    tbody {
        background-color: #ffffff !important;
    }
    tbody tr {
        background-color: #ffffff !important;
        border-bottom: 1px solid rgba(212, 232, 243, 0.4) !important;
    }
    tbody tr:hover {
        background: linear-gradient(90deg, rgba(230, 247, 251, 0.5) 0%, rgba(255, 255, 255, 1) 100%) !important;
    }
    tbody tr td {
        background-color: #ffffff !important;
        color: #4a5568 !important;
        border-color: rgba(212, 232, 243, 0.3) !important;
        padding: 0.9rem 1rem !important;
    }
    tbody tr:nth-child(even) td {
        background-color: rgba(230, 247, 251, 0.2) !important;
    }
    
    /* Streamlitのデータフレーム専用 */
    [data-testid="stDataFrame"] {
        background-color: #ffffff !important;
    }
    [data-testid="stDataFrame"] table {
        background-color: #ffffff !important;
    }
    [data-testid="stDataFrame"] thead tr th {
        background: linear-gradient(180deg, #d4e8f3 0%, #c4dff0 100%) !important;
        color: #6b8fa8 !important;
    }
    [data-testid="stDataFrame"] tbody tr td {
        background-color: #ffffff !important;
        color: #4a5568 !important;
    }
    
    /* サイドバー - グラデーション背景 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(191, 229, 240, 0.3) 0%, rgba(230, 247, 251, 0.2) 100%);
    }
    [data-testid="stSidebar"] .stButton>button {
        background-color: #ffffff;
        color: #7a9cb8;
        width: 100%;
        box-shadow: 0 2px 6px rgba(127, 165, 200, 0.1);
    }
    [data-testid="stSidebar"] .stButton>button:hover {
        background-color: rgba(191, 229, 240, 0.4);
    }
    
    /* サイドバーの開閉ボタンを強制表示（黒色） */
    button[kind="header"],
    button[data-testid="baseButton-header"],
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"],
    section[data-testid="stSidebar"] > div > button {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        background-color: #2d3748 !important;
        color: #ffffff !important;
        border-radius: 0 0.6rem 0.6rem 0 !important;
        padding: 0.6rem 0.4rem !important;
        border: none !important;
    }
    button[kind="header"]:hover,
    [data-testid="collapsedControl"]:hover {
        background-color: #1a202c !important;
    }
    button[kind="header"] svg,
    [data-testid="collapsedControl"] svg {
        fill: #ffffff !important;
        color: #ffffff !important;
    }
    
    /* サイドバーを閉じるボタン（サイドバー内） */
    [data-testid="stSidebarCollapseButton"],
    section[data-testid="stSidebar"] button[kind="header"] {
        display: block !important;
        background-color: transparent !important;
        color: #7a9cb8 !important;
    }
    [data-testid="stSidebarCollapseButton"] svg {
        fill: #7a9cb8 !important;
    }
    
    /* 入力フィールド - input要素のみに枠線（二重線を防ぐ） */
    .stTextInput>div>div>input,
    .stTextInput input,
    .stDateInput>div>div>input,
    .stDateInput input,
    .stNumberInput>div>div>input,
    .stNumberInput input,
    input[type="text"],
    input[type="date"],
    input[type="number"] {
        border: 2px solid #89b4d6 !important;
        border-radius: 0.6rem !important;
        background-color: #ffffff !important;
        color: #4a5568 !important;
        caret-color: #000000 !important;
    }
    .stTextInput>div>div>input:focus,
    .stTextInput input:focus,
    .stDateInput>div>div>input:focus,
    .stDateInput input:focus,
    .stNumberInput>div>div>input:focus,
    .stNumberInput input:focus,
    input[type="text"]:focus,
    input[type="date"]:focus,
    input[type="number"]:focus {
        border-color: #7fb5d4 !important;
        box-shadow: 0 0 0 3px rgba(127, 181, 212, 0.2) !important;
        caret-color: #000000 !important;
    }
    
    /* 入力フィールドのコンテナ - 枠線なし（二重線防止） */
    .stTextInput > div > div,
    .stNumberInput > div > div,
    .stDateInput > div > div {
        border: none !important;
        background-color: transparent !important;
    }
    
    /* セレクトボックスのコンテナも枠線なし */
    .stSelectbox > div > div {
        border: none !important;
        background-color: transparent !important;
    }
    
    /* テキストエリアのカーソルも黒に */
    textarea {
        caret-color: #000000 !important;
    }
    
    /* セレクトボックス - 一重線のみ */
    .stSelectbox [data-baseweb="select"] {
        background-color: #ffffff !important;
        border: 2px solid #89b4d6 !important;
        border-radius: 0.6rem !important;
    }
    .stSelectbox [data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #4a5568 !important;
        border: none !important;
    }
    .stSelectbox [data-baseweb="select"]:focus-within {
        border-color: #7fb5d4 !important;
        box-shadow: 0 0 0 3px rgba(127, 181, 212, 0.2) !important;
    }
    
    /* セレクトボックスの内部要素 - 枠線なし */
    .stSelectbox div[role="button"] {
        background-color: #ffffff !important;
        color: #4a5568 !important;
        border: none !important;
    }
    .stSelectbox select {
        border: none !important;
    }
    .stSelectbox > div {
        border: none !important;
    }
    
    /* ドロップダウンの矢印アイコン - 黒色に */
    .stSelectbox svg {
        fill: #4a5568 !important;
        color: #4a5568 !important;
    }
    
    /* ドロップダウンメニュー（開いた時） */
    [data-baseweb="popover"] {
        background-color: #ffffff !important;
        border: 2px solid #c9fdfe !important;
        border-radius: 0.6rem !important;
        box-shadow: 0 4px 16px rgba(191, 229, 240, 0.3) !important;
    }
    
    /* ドロップダウンの選択肢 */
    [role="listbox"] {
        background-color: #ffffff !important;
    }
    [role="option"] {
        background-color: #ffffff !important;
        color: #4a5568 !important;
        padding: 0.8rem 1rem !important;
    }
    [role="option"]:hover {
        background-color: #e6f7fb !important;
        color: #2d3748 !important;
    }
    [role="option"][aria-selected="true"] {
        background-color: #c9fdfe !important;
        color: #2d3748 !important;
        font-weight: 600;
    }
    
    /* 日付入力フィールド - 一重線のみ */
    .stDateInput input[type="text"] {
        background-color: #ffffff !important;
        color: #4a5568 !important;
        border: 2px solid #89b4d6 !important;
        border-radius: 0.6rem !important;
    }
    .stDateInput > div > div {
        background-color: transparent !important;
        border: none !important;
    }
    .stDateInput > div > div > div {
        border: none !important;
    }
    
    /* 数値入力フィールド - 一重線のみ（他は変更しない） */
    .stNumberInput [data-baseweb="input"] {
        border: 2px solid #89b4d6 !important;
        border-radius: 0.6rem !important;
        background-color: #ffffff !important;
    }
    .stNumberInput [data-baseweb="input"] > div {
        border: none !important;
        background-color: transparent !important;
    }
    .stNumberInput input {
        background-color: #ffffff !important;
        color: #4a5568 !important;
        border: none !important;
    }
    .stNumberInput > div {
        background-color: transparent !important;
        border: none !important;
    }
    .stNumberInput > div > div {
        background-color: transparent !important;
        border: none !important;
    }
    .stNumberInput > div > div > div {
        border: none !important;
    }
    
    /* 数値入力の増減ボタン（-/+） */
    .stNumberInput button {
        background-color: #c9fdfe !important;
        color: #6b8fa8 !important;
        border: none !important;
        border-radius: 0.3rem !important;
    }
    .stNumberInput button:hover {
        background-color: #abfcfe !important;
    }
    .stNumberInput button svg {
        fill: #6b8fa8 !important;
    }
    
    /* 数値入力のコントロール部分 */
    .stNumberInput [data-baseweb="input"] button {
        background-color: #c9fdfe !important;
    }
    
    /* 日付入力のカレンダーアイコン */
    .stDateInput button {
        background-color: transparent !important;
        color: #6b8fa8 !important;
    }
    .stDateInput button svg {
        fill: #6b8fa8 !important;
    }
    
    /* 全てのテキストを見やすい色に */
    p, span, div, label, input, select {
        color: #4a5568 !important;
    }
    
    /* リンクやアクティブな要素 */
    a {
        color: #7a9cb8 !important;
    }
    
    /* テーブル全般 - 完全強制 */
    table, table * {
        background-color: #ffffff !important;
    }
    table thead, table thead * {
        background: linear-gradient(180deg, #d4e8f3 0%, #c4dff0 100%) !important;
        color: #6b8fa8 !important;
    }
    table tbody tr, table tbody tr * {
        background-color: #ffffff !important;
        color: #4a5568 !important;
    }
    table tbody tr:nth-child(even), table tbody tr:nth-child(even) * {
        background-color: rgba(230, 247, 251, 0.25) !important;
    }
    
    /* 入力ウィジェットのコンテナ - 全て枠線なし（二重線防止） */
    .stTextInput, .stSelectbox, .stDateInput, .stNumberInput {
        background-color: transparent !important;
        border: none !important;
    }
    .stTextInput > div, 
    .stSelectbox > div, 
    .stDateInput > div, 
    .stNumberInput > div {
        background-color: transparent !important;
        border: none !important;
    }
    .stTextInput > div > div > div,
    .stSelectbox > div > div > div,
    .stDateInput > div > div > div,
    .stNumberInput > div > div > div {
        border: none !important;
    }
    
    /* データフレーム - 完全に白背景に強制 */
    .dataframe {
        border: none !important;
        border-radius: 0.8rem !important;
        overflow: hidden !important;
        background-color: #ffffff !important;
    }
    
    /* データフレームのコンテナ */
    div[data-testid="stDataFrame"],
    div[data-testid="stDataFrame"] > div,
    div[data-testid="stDataFrame"] > div > div {
        background-color: #ffffff !important;
    }
    
    /* データフレームのテーブル要素全体 */
    div[data-testid="stDataFrame"] table,
    div[data-testid="stDataFrame"] table tbody,
    div[data-testid="stDataFrame"] table thead {
        background-color: #ffffff !important;
    }
    
    /* データフレームのヘッダー */
    div[data-testid="stDataFrame"] table thead tr,
    div[data-testid="stDataFrame"] table thead tr th {
        background: linear-gradient(180deg, #d4e8f3 0%, #c4dff0 100%) !important;
        color: #6b8fa8 !important;
        font-weight: 500 !important;
    }
    
    /* データフレームのセル */
    div[data-testid="stDataFrame"] table tbody tr,
    div[data-testid="stDataFrame"] table tbody tr td {
        background-color: #ffffff !important;
        color: #4a5568 !important;
    }
    
    /* データフレームの偶数行 */
    div[data-testid="stDataFrame"] table tbody tr:nth-child(even),
    div[data-testid="stDataFrame"] table tbody tr:nth-child(even) td {
        background-color: rgba(230, 247, 251, 0.25) !important;
    }
    
    /* データフレームのホバー */
    div[data-testid="stDataFrame"] table tbody tr:hover,
    div[data-testid="stDataFrame"] table tbody tr:hover td {
        background-color: rgba(230, 247, 251, 0.5) !important;
    }
    
    /* 見出しの調整 */
    h1, h2, h3 {
        color: #7a9cb8 !important;
    }
    
    /* divider - 淡いピンク/ベージュ系 */
    hr {
        border-color: rgba(230, 218, 210, 0.5) !important;
        opacity: 0.6;
    }
    
    /* データフレームのスタイル - 完全上書き */
    .dataframe, .dataframe * {
        background-color: #ffffff !important;
        border-radius: 0.8rem;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(191, 229, 240, 0.15);
    }
    .dataframe thead, .dataframe thead * {
        background: linear-gradient(180deg, #d4e8f3 0%, #c4dff0 100%) !important;
    }
    .dataframe thead tr th {
        background: linear-gradient(180deg, #d4e8f3 0%, #c4dff0 100%) !important;
        color: #6b8fa8 !important;
        font-weight: 500 !important;
        border-bottom: 2px solid #b8d9ed !important;
    }
    .dataframe tbody, .dataframe tbody * {
        background-color: #ffffff !important;
    }
    .dataframe tbody tr td {
        background-color: #ffffff !important;
        color: #4a5568 !important;
        border-color: rgba(212, 232, 243, 0.3) !important;
    }
    .dataframe tbody tr:nth-child(even), 
    .dataframe tbody tr:nth-child(even) * {
        background-color: rgba(230, 247, 251, 0.25) !important;
    }
    .dataframe tbody tr:hover,
    .dataframe tbody tr:hover * {
        background: linear-gradient(90deg, rgba(230, 247, 251, 0.5) 0%, rgba(255, 255, 255, 1) 100%) !important;
    }
    
    /* メッセージボックス */
    .stAlert {
        background-color: #ffffff !important;
        border-radius: 0.8rem;
        border-left: 4px solid #89b4d6 !important;
    }
    
    /* ラベル */
    .stTextInput label,
    .stSelectbox label,
    .stNumberInput label,
    .stDateInput label {
        color: #7a9cb8 !important;
        font-weight: 500;
    }
    
    /* サブヘッダー */
    .stSubheader {
        color: #7a9cb8 !important;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)


def init_data_dir():
    """データディレクトリを初期化"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def load_json_data(file_path: str, default_value: list) -> list:
    """JSONファイルからデータを読み込む"""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"データ読み込みエラー: {e}")
            return default_value
    return default_value


def save_json_data(file_path: str, data: list):
    """JSONファイルにデータを保存"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"データ保存エラー: {e}")
        return False


def init_demo_data():
    """デモデータを初期化"""
    # 部署データ
    departments = [
        {"id": "dept1", "name": "営業部", "createdAt": datetime.now().isoformat()},
        {"id": "dept2", "name": "開発部", "createdAt": datetime.now().isoformat()},
        {"id": "dept3", "name": "総務部", "createdAt": datetime.now().isoformat()},
        {"id": "dept4", "name": "経理部", "createdAt": datetime.now().isoformat()},
    ]
    save_json_data(DEPARTMENTS_FILE, departments)
    
    # 従業員データ（サンプル）
    from dateutil.relativedelta import relativedelta
    today = datetime.now()
    
    employees = [
        {
            "id": "emp1",
            "employeeCode": "E001",
            "name": "佐藤 太郎",
            "furigana": "サトウ タロウ",
            "department": "営業部",
            "employeeType": "Full-time",
            "weeklyDays": 5,
            "dailyHours": 8.0,
            "joinDate": (today - relativedelta(years=3)).strftime('%Y-%m-%d'),
            "resignationDate": "",
            "grants": [],
            "takes": []
        },
        {
            "id": "emp2",
            "employeeCode": "E002",
            "name": "田中 花子",
            "furigana": "タナカ ハナコ",
            "department": "開発部",
            "employeeType": "Part-time",
            "weeklyDays": 4,
            "dailyHours": 6.5,
            "joinDate": (today - relativedelta(months=5)).strftime('%Y-%m-%d'),
            "resignationDate": "",
            "grants": [],
            "takes": []
        },
        {
            "id": "emp3",
            "employeeCode": "E003",
            "name": "山本 次郎",
            "furigana": "ヤマモト ジロウ",
            "department": "総務部",
            "employeeType": "Full-time",
            "weeklyDays": 5,
            "dailyHours": 8.0,
            "joinDate": (today - relativedelta(years=5)).strftime('%Y-%m-%d'),
            "resignationDate": (today - relativedelta(years=1)).strftime('%Y-%m-%d'),
            "grants": [],
            "takes": []
        }
    ]
    
    # 各従業員に法定付与を自動追加
    for emp_data in employees:
        emp = Employee.from_dict(emp_data)
        emp = auto_populate_grants(emp)
        emp_data.update(emp.to_dict())
    
    save_json_data(EMPLOYEES_FILE, employees)


# セッション状態の初期化
if 'initialized' not in st.session_state:
    init_data_dir()
    
    # データファイルが存在しない場合はデモデータを作成
    if not os.path.exists(EMPLOYEES_FILE) or not os.path.exists(DEPARTMENTS_FILE):
        init_demo_data()
    
    st.session_state.initialized = True

if 'current_view' not in st.session_state:
    st.session_state.current_view = 'list'

if 'selected_employee' not in st.session_state:
    st.session_state.selected_employee = None


def load_data():
    """データを読み込む"""
    emp_data = load_json_data(EMPLOYEES_FILE, [])
    st.session_state.employees = [Employee.from_dict(e) for e in emp_data]
    
    dept_data = load_json_data(DEPARTMENTS_FILE, [])
    st.session_state.departments = [Department.from_dict(d) for d in dept_data]


def save_employees():
    """従業員データを保存"""
    data = [emp.to_dict() for emp in st.session_state.employees]
    return save_json_data(EMPLOYEES_FILE, data)


def save_departments():
    """部署データを保存"""
    data = [dept.to_dict() for dept in st.session_state.departments]
    return save_json_data(DEPARTMENTS_FILE, data)


def show_employee_list():
    """従業員一覧画面"""
    
    st.markdown("<div class='main-header'><h1>有給休暇管理システム</h1><p>労働基準法に基づく有給休暇の付与・取得・時効を記録・管理します。</p></div>", unsafe_allow_html=True)
    
    # ヘッダーボタン
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.subheader(f"従業員一覧 ({len(st.session_state.employees)}名)")
    with col2:
        if st.button("設定", use_container_width=True):
            st.session_state.current_view = 'settings'
            st.rerun()
    with col3:
        if st.button("新規登録", use_container_width=True, type="primary"):
            new_code = generate_employee_code(st.session_state.employees)
            st.session_state.selected_employee = Employee(
                id=generate_uuid(),
                employeeCode=new_code,
                name='',
                employeeType='Full-time',
                weeklyDays=5,
                dailyHours=8.0
            )
            st.session_state.current_view = 'edit'
            st.rerun()
    
    st.divider()
    
    # 検索・フィルタリング
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("検索", placeholder="名前、コード、ふりがなで検索...")
    with col2:
        dept_names = ['全部署'] + [d.name for d in st.session_state.departments]
        filter_dept = st.selectbox("部署フィルター", dept_names)
    
    # フィルタリング
    filtered_employees = st.session_state.employees
    
    if search_term:
        filtered_employees = [
            emp for emp in filtered_employees
            if search_term.lower() in emp.name.lower() or 
               search_term.lower() in emp.furigana.lower() or 
               search_term.lower() in emp.employeeCode.lower()
        ]
    
    if filter_dept != '全部署':
        filtered_employees = [emp for emp in filtered_employees if emp.department == filter_dept]
    
    filtered_employees.sort(key=lambda x: x.employeeCode)
    
    # テーブル表示
    if filtered_employees:
        table_data = []
        for emp in filtered_employees:
            remaining = calculate_remaining_days(emp.grants, emp.takes, emp.resignationDate)
            emp_type = f"パート(週{emp.weeklyDays}日)" if emp.employeeType == 'Part-time' else '正社員'
            
            table_data.append({
                'コード': emp.employeeCode,
                '名前': emp.name,
                '部署': emp.department or '未設定',
                '種別': emp_type,
                '入社日': emp.joinDate or '未設定',
                '退社日': emp.resignationDate or '在籍中',
                '残日数': f"{remaining:.1f}",
            })
        
        df = pd.DataFrame(table_data)
        
        # HTMLテーブルとして表示（白背景を確実に適用）
        html_table = f"""
        <div style="background-color: #ffffff; border-radius: 0.8rem; overflow: hidden; box-shadow: 0 2px 8px rgba(191, 229, 240, 0.15);">
            <table style="width: 100%; border-collapse: collapse; background-color: #ffffff;">
                <thead>
                    <tr style="background: linear-gradient(180deg, #d4e8f3 0%, #c4dff0 100%);">
                        {''.join([f'<th style="padding: 1rem; text-align: left; color: #6b8fa8; font-weight: 500; border-bottom: 2px solid #b8d9ed;">{col}</th>' for col in df.columns])}
                    </tr>
                </thead>
                <tbody>
                    {''.join([
                        f'<tr style="background-color: {"rgba(230, 247, 251, 0.25)" if i % 2 == 1 else "#ffffff"}; border-bottom: 1px solid rgba(212, 232, 243, 0.4);">' +
                        ''.join([f'<td style="padding: 0.9rem 1rem; color: #4a5568; background-color: inherit;">{row[col]}</td>' for col in df.columns]) +
                        '</tr>'
                        for i, (_, row) in enumerate(df.iterrows())
                    ])}
                </tbody>
            </table>
        </div>
        """
        st.markdown(html_table, unsafe_allow_html=True)
        
        # 編集ボタン
        st.write("---")
        col1, col2 = st.columns([4, 1])
        with col1:
            selected_code = st.selectbox(
                "編集する従業員を選択",
                [emp.employeeCode for emp in filtered_employees],
                format_func=lambda code: f"{code} - {next(e.name for e in filtered_employees if e.employeeCode == code)}",
                label_visibility="visible"
            )
        with col2:
            # ラベルの高さ分のスペースを作る（1px微調整）
            st.markdown('<div style="height: 1px;"></div>', unsafe_allow_html=True)
            st.write("")  # ラベル分の高さ調整
            if st.button("編集", use_container_width=True, type="secondary"):
                selected_emp = next(e for e in filtered_employees if e.employeeCode == selected_code)
                st.session_state.selected_employee = selected_emp
                st.session_state.current_view = 'edit'
                st.rerun()
    else:
        st.info("該当する従業員が見つかりませんでした。")


def has_basic_info_changed(current, original_values):
    """基本情報が変更されているかチェック"""
    if original_values is None:  # 新規登録の場合は常に変更あり
        return True
    
    # 基本情報のフィールドを比較
    return (
        current.employeeCode != original_values['employeeCode'] or
        current.name != original_values['name'] or
        current.furigana != original_values['furigana'] or
        current.department != original_values['department'] or
        current.employeeType != original_values['employeeType'] or
        current.weeklyDays != original_values['weeklyDays'] or
        current.dailyHours != original_values['dailyHours'] or
        current.joinDate != original_values['joinDate'] or
        current.resignationDate != original_values['resignationDate']
    )


def show_confirmation_dialog(message, action_key):
    """確認ダイアログを表示"""
    # 共通スタイル（繰り返し挿入しても問題なし）
    st.markdown("""
    <style>
    .confirm-dialog-title {
        color: #666;
        margin-bottom: 10px;
        font-size: 14px;
    }
    .confirm-dialog-message {
        color: #333;
        margin: 0 0 8px 0;
        font-size: 16px;
        font-weight: 500;
    }
    form[data-testid="stForm"]:has(.confirm-dialog-marker) {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        z-index: 10001;
        width: auto;
        background-color: #fff;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        padding: 32px 40px;
        min-width: 400px;
        text-align: center;
        display: flex;
        flex-direction: column;
        gap: 24px;
        pointer-events: auto;
    }
    form[data-testid="stForm"]:has(.confirm-dialog-marker) > div[data-testid="stFormSubmitButton"] {
        margin: 0;
        pointer-events: auto;
    }
    form[data-testid="stForm"]:has(.confirm-dialog-marker) div[data-testid="stHorizontalBlock"] {
        gap: 16px;
        justify-content: center;
        pointer-events: auto;
    }
    form[data-testid="stForm"]:has(.confirm-dialog-marker) div[data-testid="column"] {
        padding: 0 !important;
        display: flex;
        justify-content: center;
        pointer-events: auto;
    }
    form[data-testid="stForm"]:has(.confirm-dialog-marker) .stFormSubmitButton {
        margin: 0;
        pointer-events: auto;
    }
    form[data-testid="stForm"]:has(.confirm-dialog-marker) .stButton>button,
    form[data-testid="stForm"]:has(.confirm-dialog-marker) .stFormSubmitButton>button {
        width: 100%;
        pointer-events: auto;
        cursor: pointer;
    }
    .confirm-dialog-marker {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)
    
    cancel_clicked = False
    confirm_clicked = False
    form_key = f"confirm_form_{action_key}"
    with st.form(key=form_key):
        st.markdown('<div class="confirm-dialog-marker"></div>', unsafe_allow_html=True)
        st.markdown('<div class="confirm-dialog-title">このページの内容</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="confirm-dialog-message">{message}</div>', unsafe_allow_html=True)
        col_cancel, col_confirm = st.columns(2)
        with col_cancel:
            cancel_clicked = st.form_submit_button("キャンセル", use_container_width=True)
        with col_confirm:
            confirm_clicked = st.form_submit_button("OK", use_container_width=True, type="primary")

    if cancel_clicked:
        if action_key in st.session_state:
            del st.session_state[action_key]
        st.rerun()
    if confirm_clicked:
        return True
    return False


def show_employee_form():
    """従業員編集/新規登録画面（フル機能版）"""
    emp = st.session_state.selected_employee
    is_new = emp.id not in [e.id for e in st.session_state.employees]
    
    # 編集開始時の元データを保存（従業員が変更された場合は更新）
    import copy
    if 'original_employee' not in st.session_state or \
       (st.session_state.original_employee and st.session_state.original_employee.id != emp.id) or \
       (st.session_state.original_employee is None and not is_new):
        st.session_state.original_employee = copy.deepcopy(emp) if not is_new else None
        st.session_state.original_values = {
            'employeeCode': emp.employeeCode,
            'name': emp.name,
            'furigana': emp.furigana,
            'department': emp.department,
            'employeeType': emp.employeeType,
            'weeklyDays': emp.weeklyDays,
            'dailyHours': emp.dailyHours,
            'joinDate': emp.joinDate,
            'resignationDate': emp.resignationDate
        } if not is_new else None
    
    st.title("新規従業員登録" if is_new else "従業員情報の編集")
    
    if st.button("← 従業員一覧に戻る"):
        st.session_state.current_view = 'list'
        st.session_state.selected_employee = None
        # 元データもクリア
        if 'original_employee' in st.session_state:
            del st.session_state.original_employee
        if 'original_values' in st.session_state:
            del st.session_state.original_values
        # 確認状態もクリア
        keys_to_delete = []
        for key in st.session_state.keys():
            if key.startswith('confirm_'):
                keys_to_delete.append(key)
        for key in keys_to_delete:
            del st.session_state[key]
        st.rerun()
    
    st.divider()
    
    # 残日数サマリー
    remaining = calculate_remaining_days(emp.grants, emp.takes, emp.resignationDate)
    st.markdown(f"""
    <div class='stat-card'>
        <h3>現在の残日数（時効考慮）</h3>
        <div class='remaining-days'>{remaining:.1f} <span style='font-size: 1.2rem; font-weight: normal;'>日</span></div>
        {f"<p style='color: red; margin-top: 0.5rem;'>※退社日 ({emp.resignationDate}) 以降の付与・取得は計算対象外です。</p>" if emp.resignationDate else ""}
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    
    # 基本情報
    with st.expander("基本情報", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            emp.employeeCode = st.text_input("従業員コード（必須）*", value=emp.employeeCode)
            emp.name = st.text_input("名前（必須）*", value=emp.name)
            emp.furigana = st.text_input("ふりがな", value=emp.furigana)
            
            dept_options = [''] + [d.name for d in st.session_state.departments]
            dept_index = dept_options.index(emp.department) if emp.department in dept_options else 0
            emp.department = st.selectbox("所属部署", dept_options, index=dept_index)
        
        with col2:
            emp.employeeType = st.selectbox(
                "従業員の種別",
                ['Full-time', 'Part-time'],
                index=0 if emp.employeeType == 'Full-time' else 1,
                format_func=lambda x: '正社員' if x == 'Full-time' else 'パート'
            )
            
            if emp.employeeType == 'Part-time':
                emp.weeklyDays = st.selectbox("週所定労働日数（比例付与用）", [1, 2, 3, 4], index=min(emp.weeklyDays - 1, 3))
                emp.dailyHours = st.number_input("1日の所定労働時間", min_value=0.0, max_value=24.0, value=emp.dailyHours, step=0.5)
            else:
                emp.weeklyDays = 5
                emp.dailyHours = 8.0
            
            join_date_input = st.date_input("入社日", value=datetime.strptime(emp.joinDate, '%Y-%m-%d') if emp.joinDate else None)
            emp.joinDate = join_date_input.strftime('%Y-%m-%d') if join_date_input else ''
            
            resignation_input = st.date_input("退社日（任意）", value=datetime.strptime(emp.resignationDate, '%Y-%m-%d') if emp.resignationDate else None, key="resignation_date")
            emp.resignationDate = resignation_input.strftime('%Y-%m-%d') if resignation_input else ''
    
    # 法定付与スケジュールガイド
    if emp.joinDate:
        join_dt = datetime.strptime(emp.joinDate, '%Y-%m-%d')
        schedule = get_statutory_grant_schedule(join_dt, emp.employeeType, emp.weeklyDays)
        
        if schedule:
            with st.expander("法定付与スケジュール（ガイド）", expanded=False):
                st.info(f"入社日({emp.joinDate})と種別に基づき、以下の付与記録が自動追加されます。")
                
                schedule_data = []
                for sch in schedule[:5]:  # 最初の5件のみ表示
                    schedule_data.append({
                        '付与日': sch['date'].strftime('%Y-%m-%d'),
                        '日数': f"{sch['days']}日",
                        '理由': sch['reason'],
                        '時効日': sch['expiryDate'].strftime('%Y-%m-%d')
                    })
                
                import pandas as pd
                st.dataframe(pd.DataFrame(schedule_data), use_container_width=True, hide_index=True)
    
    # 付与履歴
    with st.expander("付与履歴（手動追加）", expanded=True):
        # 付与追加の確認ダイアログ
        if st.session_state.get('confirm_add_grant', False):
            data = st.session_state.get('grant_data', {})
            if show_confirmation_dialog(
                f"{data['date'].strftime('%Y-%m-%d')}に{data['days']:.1f}日の有給付与を追加しますか？",
                'confirm_add_grant'
            ):
                # 実際に追加処理を実行
                new_grant = Grant(
                    id=generate_uuid(),
                    date=data['date'].strftime('%Y-%m-%d'),
                    days=round_to_decimal(data['days']),
                    reason=data['reason'] or '手動付与'
                )
                emp.grants.append(new_grant)
                emp.grants.sort(key=lambda x: x.date)
                
                # session_stateを更新して残日数計算に反映
                st.session_state.selected_employee = emp
                
                # データベースにも保存
                if not is_new:
                    idx = next(i for i, e in enumerate(st.session_state.employees) if e.id == emp.id)
                    st.session_state.employees[idx] = emp
                    save_employees()
                
                del st.session_state.confirm_add_grant
                del st.session_state.grant_data
                st.success("付与を追加しました")
                st.rerun()
        
        # 付与削除の確認ダイアログ
        for i in range(len(emp.grants)):
            if st.session_state.get(f'confirm_del_grant_{i}', False):
                data = st.session_state.get('grant_del_data', {})
                if show_confirmation_dialog(
                    f"本当に{data['date']}の{data['days']:.1f}日の付与履歴を削除しますか？",
                    f'confirm_del_grant_{i}'
                ):
                    # 実際に削除処理を実行
                    emp.grants.pop(data['index'])
                    
                    # session_stateを更新して残日数計算に反映
                    st.session_state.selected_employee = emp
                    
                    # データベースにも保存
                    if not is_new:
                        idx = next((j for j, e in enumerate(st.session_state.employees) if e.id == emp.id), None)
                        if idx is not None:
                            st.session_state.employees[idx] = emp
                            save_employees()
                    
                    del st.session_state[f'confirm_del_grant_{i}']
                    del st.session_state.grant_del_data
                    st.success("削除しました")
                    st.rerun()
        
        st.write("##### 新しい付与を追加")
        col1, col2, col3, col4 = st.columns([2, 1, 2, 1])
        
        with col1:
            grant_date = st.date_input("付与日", key="grant_date_input")
        with col2:
            grant_days = st.number_input("付与日数", min_value=0.0, step=0.5, key="grant_days_input")
        with col3:
            grant_reason = st.text_input("理由", value="手動付与", key="grant_reason_input")
        with col4:
            st.write("")
            st.write("")
            if st.button("付与追加", type="primary", key="add_grant_btn"):
                if grant_date and grant_days > 0:
                    st.session_state.confirm_add_grant = True
                    st.session_state.grant_data = {
                        'date': grant_date,
                        'days': grant_days,
                        'reason': grant_reason
                    }
                    st.rerun()
                else:
                    st.error("付与日と日数を正しく入力してください")
        
        st.write("---")
        st.write("##### 付与履歴一覧")
        
        if emp.grants:
            for i, grant in enumerate(emp.grants):
                expiry_date = datetime.strptime(grant.date, '%Y-%m-%d') + pd.DateOffset(years=2)
                is_expired = expiry_date.date() < datetime.now().date()
                
                col1, col2, col3, col4, col5 = st.columns([2, 1, 3, 2, 1])
                with col1:
                    st.write(grant.date)
                with col2:
                    st.write(f"**{grant.days:.1f}日**")
                with col3:
                    st.write(f"_{grant.reason}_")
                with col4:
                    st.write(f"時効日: {expiry_date.strftime('%Y-%m-%d')}")
                    if is_expired:
                        st.caption("🔴 時効")
                with col5:
                    if st.button("削除", key=f"del_grant_{i}"):
                        st.session_state[f'confirm_del_grant_{i}'] = True
                        st.session_state.grant_del_data = {
                            'index': i,
                            'date': grant.date,
                            'days': grant.days
                        }
                        st.rerun()
        else:
            st.info("付与履歴がありません")
    
    # 取得履歴
    with st.expander("取得履歴", expanded=True):
        # 取得追加の確認ダイアログ
        if st.session_state.get('confirm_add_take', False):
            data = st.session_state.get('take_data', {})
            if show_confirmation_dialog(
                f"{data['date'].strftime('%Y-%m-%d')}に{data['days']:.1f}日の有給取得を追加しますか？",
                'confirm_add_take'
            ):
                # 実際に追加処理を実行
                new_take = Take(
                    id=generate_uuid(),
                    date=data['date'].strftime('%Y-%m-%d'),
                    days=round_to_decimal(data['days']),
                    reason=data['reason'] or '有給休暇取得'
                )
                emp.takes.append(new_take)
                emp.takes.sort(key=lambda x: x.date)
                
                # session_stateを更新して残日数計算に反映
                st.session_state.selected_employee = emp
                
                # データベースにも保存
                if not is_new:
                    idx = next(i for i, e in enumerate(st.session_state.employees) if e.id == emp.id)
                    st.session_state.employees[idx] = emp
                    save_employees()
                
                del st.session_state.confirm_add_take
                del st.session_state.take_data
                st.success("取得を追加しました")
                st.rerun()
        
        # 取得削除の確認ダイアログ
        for i in range(len(emp.takes)):
            if st.session_state.get(f'confirm_del_take_{i}', False):
                data = st.session_state.get('take_del_data', {})
                if show_confirmation_dialog(
                    f"本当に{data['date']}の{data['days']:.1f}日の取得履歴を削除しますか？",
                    f'confirm_del_take_{i}'
                ):
                    # 実際に削除処理を実行
                    emp.takes.pop(data['index'])
                    
                    # session_stateを更新して残日数計算に反映
                    st.session_state.selected_employee = emp
                    
                    # データベースにも保存
                    if not is_new:
                        idx = next((j for j, e in enumerate(st.session_state.employees) if e.id == emp.id), None)
                        if idx is not None:
                            st.session_state.employees[idx] = emp
                            save_employees()
                    
                    del st.session_state[f'confirm_del_take_{i}']
                    del st.session_state.take_del_data
                    st.success("削除しました")
                    st.rerun()
        
        st.write("##### 新しい取得を追加")
        col1, col2, col3, col4 = st.columns([2, 1, 2, 1])
        
        with col1:
            take_date = st.date_input("取得日", key="take_date_input")
        with col2:
            take_days = st.number_input("取得日数", min_value=0.0, step=0.5, key="take_days_input")
        with col3:
            take_reason = st.text_input("理由", value="", key="take_reason_input")
        with col4:
            st.write("")
            st.write("")
            if st.button("取得追加", type="primary", key="add_take_btn"):
                if take_date and take_days > 0:
                    st.session_state.confirm_add_take = True
                    st.session_state.take_data = {
                        'date': take_date,
                        'days': take_days,
                        'reason': take_reason
                    }
                    st.rerun()
                else:
                    st.error("取得日と日数を正しく入力してください")
        
        st.write("---")
        st.write("##### 取得履歴一覧")
        
        if emp.takes:
            for i, take in enumerate(emp.takes):
                col1, col2, col3, col4 = st.columns([2, 1, 4, 1])
                with col1:
                    st.write(take.date)
                with col2:
                    st.write(f"**-{take.days:.1f}日**")
                with col3:
                    st.write(f"_{take.reason}_")
                with col4:
                    if st.button("削除", key=f"del_take_{i}"):
                        st.session_state[f'confirm_del_take_{i}'] = True
                        st.session_state.take_del_data = {
                            'index': i,
                            'date': take.date,
                            'days': take.days
                        }
                        st.rerun()
        else:
            st.info("取得履歴がありません")
    
    # 保存ボタン
    st.divider()
    col1, col2, col3 = st.columns([2, 2, 2])
    
    # 変更チェック
    has_changes = has_basic_info_changed(emp, st.session_state.get('original_values', None))
    
    with col1:
        if st.button("基本情報を保存", type="primary", use_container_width=True, disabled=not has_changes):
            if not emp.employeeCode or not emp.name:
                st.error("従業員コードと名前は必須です")
            else:
                emp = auto_populate_grants(emp)
                
                if is_new:
                    st.session_state.employees.append(emp)
                else:
                    idx = next(i for i, e in enumerate(st.session_state.employees) if e.id == emp.id)
                    st.session_state.employees[idx] = emp
                
                if save_employees():
                    st.success("保存しました！")
                    # 元データもクリア
                    if 'original_employee' in st.session_state:
                        del st.session_state.original_employee
                    if 'original_values' in st.session_state:
                        del st.session_state.original_values
                    # 確認状態もクリア
                    keys_to_delete = []
                    for key in st.session_state.keys():
                        if key.startswith('confirm_'):
                            keys_to_delete.append(key)
                    for key in keys_to_delete:
                        del st.session_state[key]
                    st.session_state.current_view = 'list'
                    st.rerun()
    
    with col2:
        if st.button("キャンセル", use_container_width=True):
            # 元データもクリア
            if 'original_employee' in st.session_state:
                del st.session_state.original_employee
            if 'original_values' in st.session_state:
                del st.session_state.original_values
            # 確認状態もクリア
            keys_to_delete = []
            for key in st.session_state.keys():
                if key.startswith('confirm_'):
                    keys_to_delete.append(key)
            for key in keys_to_delete:
                del st.session_state[key]
            st.session_state.current_view = 'list'
            st.rerun()
    
    with col3:
        if not is_new:
            if st.button("従業員を削除", use_container_width=True):
                if 'confirm_delete' not in st.session_state:
                    st.session_state.confirm_delete = False
                
                if st.session_state.confirm_delete:
                    st.session_state.employees = [e for e in st.session_state.employees if e.id != emp.id]
                    if save_employees():
                        st.success("削除しました")
                        # 元データもクリア
                        if 'original_employee' in st.session_state:
                            del st.session_state.original_employee
                        if 'original_values' in st.session_state:
                            del st.session_state.original_values
                        # 確認状態もクリア
                        keys_to_delete = []
                        for key in st.session_state.keys():
                            if key.startswith('confirm_'):
                                keys_to_delete.append(key)
                        for key in keys_to_delete:
                            del st.session_state[key]
                        st.session_state.current_view = 'list'
                        st.session_state.confirm_delete = False
                        st.rerun()
                else:
                    st.session_state.confirm_delete = True
                    st.warning("もう一度クリックすると削除されます")
                    st.rerun()


def show_settings():
    """設定画面"""
    st.title("部署マスター管理")
    
    if st.button("← 従業員一覧に戻る"):
        st.session_state.current_view = 'list'
        st.rerun()
    
    st.divider()
    
    # 新規追加
    col1, col2 = st.columns([3, 1])
    with col1:
        new_dept_name = st.text_input("新しい部署名", key="new_dept")
    with col2:
        st.write("")
        st.write("")
        if st.button("追加", type="primary"):
            if new_dept_name.strip():
                new_dept = Department(
                    id=generate_uuid(),
                    name=new_dept_name.strip(),
                    createdAt=datetime.now().isoformat()
                )
                st.session_state.departments.append(new_dept)
                if save_departments():
                    st.success(f"部署「{new_dept_name}」を追加しました")
                    st.rerun()
    
    st.divider()
    
    # 部署リスト
    for dept in st.session_state.departments:
        employee_count = sum(1 for emp in st.session_state.employees if emp.department == dept.name)
        
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.write(f"**{dept.name}**")
        with col2:
            st.write(f"従業員: {employee_count}名")
        with col3:
            if employee_count == 0:
                if st.button("削除", key=f"del_{dept.id}"):
                    st.session_state.departments = [d for d in st.session_state.departments if d.id != dept.id]
                    if save_departments():
                        st.success("削除しました")
                        st.rerun()
            else:
                st.caption("削除不可")
        
        st.divider()


def main():
    """メイン関数"""
    if 'employees' not in st.session_state:
        load_data()
    
    # サイドバー
    with st.sidebar:
        st.title("有給管理")
        st.caption("デモモード")
        st.divider()
        
        if st.button("従業員一覧", use_container_width=True):
            st.session_state.current_view = 'list'
            st.rerun()
        
        if st.button("設定", use_container_width=True):
            st.session_state.current_view = 'settings'
            st.rerun()
        
        st.divider()
        
        if st.button("再読込", use_container_width=True):
            load_data()
            st.rerun()
        
        if st.button("デモデータをリセット", use_container_width=True):
            init_demo_data()
            load_data()
            st.success("リセットしました")
            st.rerun()
        
        st.divider()
        st.caption(f"従業員: {len(st.session_state.get('employees', []))}名")
        st.caption(f"部署: {len(st.session_state.get('departments', []))}部署")
        st.caption(f"データ: {DATA_DIR}/")
    
    # ビュー表示
    if st.session_state.current_view == 'list':
        show_employee_list()
    elif st.session_state.current_view == 'edit':
        show_employee_form()
    elif st.session_state.current_view == 'settings':
        show_settings()


if __name__ == "__main__":
    main()
