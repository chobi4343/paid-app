"""
有給休暇管理システム - デスクトップ版（Streamlit + pywebview）
Streamlitの見た目をそのままデスクトップアプリとして起動
ブラウザ不要！
"""
import webview
import threading
import time
import socket
import subprocess
import sys
import os


def find_free_port():
    """空いているポートを見つける"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


def run_streamlit(port):
    """Streamlitアプリを起動"""
    # 現在のディレクトリを取得
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(current_dir, 'app_demo.py')
    
    # Streamlitを起動
    cmd = [
        sys.executable,
        '-m', 'streamlit', 'run',
        app_path,
        '--server.port', str(port),
        '--server.headless', 'true',
        '--browser.serverAddress', 'localhost',
        '--server.enableXsrfProtection', 'false',
        '--server.enableCORS', 'false'
    ]
    
    subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


def wait_for_streamlit(url, timeout=30):
    """Streamlitが起動するまで待つ"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            import urllib.request
            urllib.request.urlopen(url, timeout=1)
            return True
        except:
            time.sleep(0.5)
    return False


def cleanup_old_backups(backup_dir: str, prefix: str, keep_count: int):
    """古いバックアップファイルを削除（最新keep_count件のみ保持）"""
    try:
        if not os.path.exists(backup_dir):
            return
        
        backup_files = sorted(
            [f for f in os.listdir(backup_dir) if f.startswith(prefix) and f.endswith('.json')],
            reverse=True
        )
        
        for old_backup in backup_files[keep_count:]:
            old_backup_path = os.path.join(backup_dir, old_backup)
            if os.path.exists(old_backup_path):
                os.remove(old_backup_path)
                print(f"  ✓ 古いバックアップを削除: {old_backup}")
    except Exception as e:
        print(f"古いバックアップ削除エラー: {e}")


def create_backup_on_close():
    """アプリ終了時にバックアップを作成（個別＋全データエクスポート）"""
    import json
    from datetime import datetime
    
    print("\n終了時バックアップを作成中...")
    
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(current_dir, 'demo_data')
        backup_dir = os.path.join(current_dir, '@backups')
        
        # バックアップディレクトリが存在しない場合は作成
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        emp_data = None
        dept_data = None
        
        # 従業員データのバックアップ
        employees_file = os.path.join(data_dir, 'employees.json')
        if os.path.exists(employees_file):
            with open(employees_file, 'r', encoding='utf-8') as f:
                emp_data = json.load(f)
            backup_emp_file = os.path.join(backup_dir, f'employees_backup_{timestamp}.json')
            with open(backup_emp_file, 'w', encoding='utf-8') as f:
                json.dump(emp_data, f, ensure_ascii=False, indent=2)
            print(f"  ✓ 従業員データをバックアップ: {os.path.basename(backup_emp_file)}")
        
        # 部署データのバックアップ
        departments_file = os.path.join(data_dir, 'departments.json')
        if os.path.exists(departments_file):
            with open(departments_file, 'r', encoding='utf-8') as f:
                dept_data = json.load(f)
            backup_dept_file = os.path.join(backup_dir, f'departments_backup_{timestamp}.json')
            with open(backup_dept_file, 'w', encoding='utf-8') as f:
                json.dump(dept_data, f, ensure_ascii=False, indent=2)
            print(f"  ✓ 部署データをバックアップ: {os.path.basename(backup_dept_file)}")
        
        # 全データをエクスポート（従業員+部署を1ファイルに）
        if emp_data is not None or dept_data is not None:
            export_data = {
                'employees': emp_data if emp_data else [],
                'departments': dept_data if dept_data else [],
                'exported_at': datetime.now().isoformat()
            }
            export_file = os.path.join(backup_dir, f'all_data_export_{timestamp}.json')
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            print(f"  ✓ 全データをエクスポート: {os.path.basename(export_file)}")
        
        # 古いバックアップを削除（最新5件のみ保持）
        cleanup_old_backups(backup_dir, 'employees_backup', 5)
        cleanup_old_backups(backup_dir, 'departments_backup', 5)
        cleanup_old_backups(backup_dir, 'all_data_export', 5)
        
        print("バックアップ完了！")
        
    except Exception as e:
        print(f"バックアップエラー: {e}")


def on_closing():
    """ウィンドウが閉じられる時の処理"""
    create_backup_on_close()


def main():
    """メイン関数"""
    print("=" * 60)
    print("有給休暇管理システム - デスクトップ版")
    print("Streamlitの見た目をそのままデスクトップアプリで起動")
    print("=" * 60)
    
    # 空いているポートを見つける
    port = find_free_port()
    url = f'http://localhost:{port}'
    
    print(f"\nStreamlitアプリを起動中... (ポート: {port})")
    
    # Streamlitをバックグラウンドで起動
    threading.Thread(target=run_streamlit, args=(port,), daemon=True).start()
    
    print("アプリの起動を待っています...")
    
    # Streamlitが起動するまで待つ
    if wait_for_streamlit(url):
        print("アプリが起動しました！")
        print(f"URL: {url}")
        print("\nデスクトップウィンドウを開きます...")
        
        # pywebviewでネイティブウィンドウを開く
        window = webview.create_window(
            title='有給休暇管理システム',
            url=url,
            width=1400,
            height=900,
            resizable=True,
            fullscreen=False,
            min_size=(1000, 700),
            confirm_close=True,
            background_color='#FFFFFF'
        )
        
        print("\nウィンドウを開きました！")
        print("ウィンドウを閉じるとアプリが終了します")
        
        # 終了イベントハンドラを設定
        window.events.closing += on_closing
        
        # ウィンドウを起動
        webview.start()
        
    else:
        print("エラー: アプリの起動に失敗しました")
        print(f"   手動で確認: {url}")
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nアプリを終了しました")
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        print("\nトラブルシューティング:")
        print("1. pywebviewがインストールされているか確認:")
        print("   pip3 install pywebview")
        print("\n2. Streamlitがインストールされているか確認:")
        print("   pip3 install streamlit")
        print("\n3. 直接Streamlit版を起動:")
        print("   streamlit run app_demo.py")

