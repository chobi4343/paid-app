#!/bin/bash

echo "================================================"
echo "有給管理アプリ - Python版 セットアップ"
echo "================================================"
echo ""

# Python バージョンチェック
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python バージョン: $python_version"
echo ""

# 仮想環境の作成
if [ ! -d "venv" ]; then
    echo "📦 仮想環境を作成中..."
    python3 -m venv venv
    echo "✅ 仮想環境を作成しました"
else
    echo "✅ 仮想環境は既に存在します"
fi
echo ""

# 仮想環境の有効化
echo "🔄 仮想環境を有効化中..."
source venv/bin/activate
echo "✅ 仮想環境を有効化しました"
echo ""

# 依存パッケージのインストール
echo "📥 依存パッケージをインストール中..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ 依存パッケージをインストールしました"
echo ""

# Firebase設定ファイルのチェック
if [ ! -f "firebase_config.json" ]; then
    echo "⚠️  firebase_config.json が見つかりません"
    echo ""
    echo "次の手順でFirebase認証情報を設定してください："
    echo "1. Firebase Console (https://console.firebase.google.com/) にアクセス"
    echo "2. プロジェクト設定 → サービスアカウント"
    echo "3. 「新しい秘密鍵の生成」をクリック"
    echo "4. ダウンロードしたJSONファイルを firebase_config.json としてこのディレクトリに配置"
    echo ""
else
    echo "✅ firebase_config.json が見つかりました"
    echo ""
fi

echo "================================================"
echo "セットアップ完了！"
echo "================================================"
echo ""
echo "アプリを起動するには："
echo "  source venv/bin/activate  # 仮想環境の有効化（まだの場合）"
echo "  streamlit run app.py"
echo ""

