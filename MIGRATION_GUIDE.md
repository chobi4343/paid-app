# React → Python 移植ガイド

## 📋 概要

このドキュメントでは、gemini Canvasで作成したReact版の有給申請アプリをPythonに移植する方法を説明します。

## 🎯 移植方法の比較

| 方式 | 開発難易度 | UI品質 | パフォーマンス | 推奨用途 |
|------|----------|--------|--------------|---------|
| **Streamlit** ⭐ | ★☆☆☆☆ | ★★★☆☆ | ★★★☆☆ | 社内ツール、プロトタイプ |
| **Flask/Django** | ★★★★☆ | ★★★★★ | ★★★★☆ | 本番環境、外部公開 |
| **Tkinter/PyQt** | ★★★☆☆ | ★★☆☆☆ | ★★★★★ | デスクトップアプリ |
| **FastAPI + React** | ★★★★★ | ★★★★★ | ★★★★★ | 本格的なWebサービス |

---

## ✅ 推奨：Streamlit版（実装済み）

### メリット
- ✅ **簡単**: わずか数百行で実装可能
- ✅ **高速開発**: UIコンポーネントが豊富
- ✅ **Firebase対応**: Firebase Admin SDKで完全互換
- ✅ **デモモード**: Firebaseなしでも動作可能

### デメリット
- ❌ リアルタイム更新は手動リフレッシュが必要
- ❌ 細かいUIカスタマイズに制限あり
- ❌ 大規模トラフィックには不向き

---

## 🚀 クイックスタート

### 1. Streamlit版（Firebase連携）

```bash
cd python_version

# セットアップ
bash setup.sh

# Firebase設定ファイルを配置
# firebase_config.json を作成（README_PYTHON.md参照）

# アプリ起動
source venv/bin/activate
streamlit run app.py
```

### 2. デモ版（Firebaseなし）

```bash
cd python_version

# パッケージインストール
pip install -r requirements.txt

# デモモード起動（Firebase不要）
streamlit run app_demo.py
```

ブラウザで `http://localhost:8501` が自動的に開きます。

---

## 📊 機能比較表

| 機能 | React版 | Streamlit版 | デモ版 |
|------|---------|------------|--------|
| 従業員管理 | ✅ | ✅ | ✅ |
| 有給付与・取得 | ✅ | ✅ | ✅ |
| 法定付与自動計算 | ✅ | ✅ | ✅ |
| 時効計算（2年） | ✅ | ✅ | ✅ |
| 部署マスター | ✅ | ✅ | ✅ |
| Firebase連携 | ✅ | ✅ | ❌ |
| リアルタイム更新 | ✅ | ❌（手動） | ❌ |
| モーダルダイアログ | ✅ | ⚠️（別形式） | ⚠️ |
| デプロイ | Vercel等 | Streamlit Cloud | ローカル |

---

## 🔧 技術的な移植のポイント

### 1. **状態管理**
- React: `useState`, `useEffect`
- Python: `st.session_state`

```python
# React
const [employees, setEmployees] = useState([]);

# Python (Streamlit)
if 'employees' not in st.session_state:
    st.session_state.employees = []
```

### 2. **データフェッチ**
- React: `onSnapshot`（リアルタイム）
- Python: 関数呼び出し（オンデマンド）

```python
# React
onSnapshot(collection, (snapshot) => { ... });

# Python
def load_data():
    docs = db.collection(...).stream()
    return [doc.to_dict() for doc in docs]
```

### 3. **計算ロジック**
- JavaScript → Python への直訳が可能
- 日付計算: `Date` → `datetime` + `dateutil`

```javascript
// React
const grantDate = new Date(baseDate);
grantDate.setFullYear(grantDate.getFullYear() + years);

# Python
from dateutil.relativedelta import relativedelta
grant_date = base_date + relativedelta(years=years)
```

### 4. **UIコンポーネント**

| React | Streamlit |
|-------|-----------|
| `<input>` | `st.text_input()` |
| `<select>` | `st.selectbox()` |
| `<button>` | `st.button()` |
| `<table>` | `st.dataframe()` |
| Modal | `st.expander()` / カスタム |

---

## 📂 ディレクトリ構造

```
python_version/
├── app.py                      # Streamlit版メインアプリ（Firebase使用）
├── app_demo.py                 # デモ版（ローカルJSON使用）
├── requirements.txt            # 依存パッケージ
├── setup.sh                    # セットアップスクリプト
├── firebase_config.json        # Firebase認証情報（要作成）
├── firebase_config.json.example # サンプル
├── utils/
│   ├── __init__.py
│   ├── data_models.py          # データ構造定義
│   ├── firebase_client.py      # Firebase接続
│   └── calculations.py         # 有給計算ロジック
└── demo_data/                  # デモモード用データ（自動生成）
    ├── employees.json
    └── departments.json
```

---

## 🔐 Firebase設定方法

### 1. Firebase Admin SDK認証情報の取得

1. [Firebase Console](https://console.firebase.google.com/) にアクセス
2. プロジェクト設定 → **サービスアカウント**
3. 「**新しい秘密鍵の生成**」をクリック
4. ダウンロードしたJSONファイルを `firebase_config.json` として保存

### 2. Firestoreデータベースの設定

1. Firebase Console → **Firestore Database**
2. データベースを作成（テストモードでOK）
3. コレクション構造:
   ```
   artifacts/
     └── {app_id}/
         └── public/
             └── data/
                 ├── employees/
                 └── departments/
   ```

---

## 🎨 他の実装オプション

### オプション1: Flask + Firebase

より細かいUI制御が必要な場合：

```python
# app_flask.py
from flask import Flask, render_template, request
import firebase_admin

app = Flask(__name__)
# Firebase初期化
# ...

@app.route('/')
def index():
    employees = get_employees()
    return render_template('index.html', employees=employees)

if __name__ == '__main__':
    app.run(debug=True)
```

**メリット**: 完全なUIカスタマイズ、テンプレートエンジン使用可
**デメリット**: HTML/CSS/JSの知識が必要

### オプション2: デスクトップアプリ（Tkinter）

オフライン動作が必要な場合：

```python
# app_tkinter.py
import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("有給管理システム")

# UIコンポーネントを配置
# ...

root.mainloop()
```

**メリット**: インターネット不要、ネイティブな速度
**デメリット**: UI実装が煩雑、マルチプラットフォーム対応が必要

### オプション3: FastAPI + React（ハイブリッド）

元のReactフロントエンドを再利用：

```python
# backend/main.py
from fastapi import FastAPI
from firebase_admin import firestore

app = FastAPI()

@app.get("/api/employees")
def get_employees():
    # Firebaseからデータ取得
    return {"employees": [...]}
```

**メリット**: 既存のReact UIを再利用、高パフォーマンス
**デメリット**: フロントエンド/バックエンドの両方を管理

---

## 🧪 テスト方法

### デモ版で動作確認

```bash
cd python_version
streamlit run app_demo.py
```

1. 従業員一覧が表示されることを確認
2. 新規従業員を登録
3. 有給付与・取得を記録
4. 残日数が正しく計算されることを確認

### Firebase版で本番テスト

```bash
streamlit run app.py
```

Firebase Consoleで Firestore のデータが更新されることを確認

---

## 💡 カスタマイズ例

### 1. 会社ロゴを追加

```python
# app.py の main() 関数内
with st.sidebar:
    st.image("path/to/logo.png", use_column_width=True)
```

### 2. カラーテーマ変更

`.streamlit/config.toml` を作成：

```toml
[theme]
primaryColor = "#4F46E5"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

### 3. データエクスポート機能

```python
# 従業員一覧画面に追加
if st.button("CSVエクスポート"):
    df = pd.DataFrame([emp.to_dict() for emp in st.session_state.employees])
    csv = df.to_csv(index=False)
    st.download_button("ダウンロード", csv, "employees.csv", "text/csv")
```

---

## ❓ FAQ

### Q1: Streamlit版はリアルタイム更新に対応していますか？
**A**: デフォルトでは非対応です。`st.rerun()` で手動リフレッシュするか、`st.experimental_rerun()` を定期的に呼び出すことで疑似的に実現可能です。

### Q2: 既存のFirebaseデータを移行できますか？
**A**: はい。`artifacts/{app_id}/public/data/` のパスを合わせることで、既存データをそのまま使用できます。

### Q3: 認証機能は追加できますか？
**A**: Streamlit-Authenticatorライブラリを使用することで、ログイン機能を追加できます。

### Q4: デプロイ方法は？
**A**: Streamlit Cloudに無料でデプロイ可能です。GitHubリポジトリと連携するだけでOK。

---

## 📚 参考リンク

- [Streamlit公式ドキュメント](https://docs.streamlit.io/)
- [Firebase Admin SDK (Python)](https://firebase.google.com/docs/admin/setup)
- [Streamlit Cloud](https://streamlit.io/cloud)

---

## 🤝 サポート

問題が発生した場合は、以下を確認してください：

1. Python 3.8以上がインストールされているか
2. `requirements.txt` のパッケージが正しくインストールされているか
3. `firebase_config.json` のパスと内容が正しいか

---

**作成日**: 2025年10月7日
**バージョン**: 1.0.0

