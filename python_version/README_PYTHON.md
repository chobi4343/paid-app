# 有給管理アプリ - Python版（Streamlit）

## 概要
ReactアプリをPythonのStreamlitに移植したバージョンです。

## セットアップ方法

### 1. 必要なパッケージのインストール
```bash
cd python_version
pip install -r requirements.txt
```

### 2. Firebase設定
`firebase_config.json` ファイルを作成し、Firebaseの認証情報を配置してください：

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "...",
  "client_email": "...",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "..."
}
```

**Firebase Admin SDKの認証情報取得方法**：
1. Firebase Console → プロジェクト設定
2. サービスアカウント → 新しい秘密鍵の生成
3. ダウンロードしたJSONファイルを `firebase_config.json` として保存

### 3. アプリの起動
```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` が自動的に開きます。

## 主な機能

### ✅ 実装済み
- 従業員一覧表示・検索・フィルタリング
- 従業員の新規登録・編集・削除
- 有給休暇の付与・取得履歴管理
- 法定付与の自動計算（正社員・パート対応）
- 残日数計算（FIFO方式、2年時効）
- 部署マスター管理

### 📋 元のReactアプリとの違い
- UIフレームワークがReact → Streamlitに変更
- リアルタイム更新は手動リフレッシュが必要
- モーダルダイアログの代わりにStreamlitのコンポーネントを使用

## ファイル構成
```
python_version/
├── app.py                    # メインアプリケーション
├── utils/
│   ├── firebase_client.py    # Firebase接続管理
│   ├── calculations.py       # 有給計算ロジック
│   └── data_models.py        # データ構造定義
├── requirements.txt          # 依存パッケージ
├── firebase_config.json      # Firebase認証情報（要作成）
└── README_PYTHON.md          # このファイル
```

## トラブルシューティング

### Firebase接続エラー
- `firebase_config.json` のパスが正しいか確認
- Firebase Admin SDKの権限設定を確認

### パッケージインストールエラー
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

## 他の実装オプション

### Flask/Django版（本格的なWebアプリ）
より細かいUI制御や認証機能が必要な場合は、Flask/Djangoでの実装も可能です。

### デスクトップアプリ版（Tkinter/PyQt）
オフライン動作が必要な場合は、デスクトップアプリとしての実装も検討できます。

## ライセンス
元のReactアプリと同じライセンスを適用

