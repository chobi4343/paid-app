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
        webview.create_window(
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

