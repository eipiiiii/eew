
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import websocket
import requests
import json
import threading
import time
from datetime import datetime
import sys

class AXISEarthquakeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AXIS地震情報モニター")
        self.root.geometry("800x600")

        # 変数の初期化
        self.token = tk.StringVar()
        self.connected = False
        self.ws = None
        self.data_log = []

        # デフォルトトークンを設定
        default_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjp7ImlkIjoiZWlwaWlpaWkiLCJ0eXBlIjowLCJjb25uZWN0aW9uIjoyfSwiY2hhbm5lbHMiOlsiam14LXNlaXNtb2xvZ3kiLCJxdWFrZS1vbmUiLCJlZXciXSwiZXhwIjoxNzU0MDA2Mzk5fQ.bZHDTPisDku1ObKRv7iKUOXyIdCeuUg9mypKKs_b5FI"
        self.token.set(default_token)

        self.setup_ui()

    def setup_ui(self):
        """UIのセットアップ"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # ウィンドウのリサイズ設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)

        # タイトル
        title_label = ttk.Label(main_frame, text="🏠 AXIS地震情報リアルタイムモニター", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # トークン入力
        ttk.Label(main_frame, text="アクセストークン:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        token_entry = ttk.Entry(main_frame, textvariable=self.token, width=50, show="*")
        token_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 5))

        # 接続ボタン
        self.connect_button = ttk.Button(main_frame, text="接続開始", command=self.toggle_connection)
        self.connect_button.grid(row=1, column=2, padx=(5, 0))

        # ステータス表示
        self.status_var = tk.StringVar()
        self.status_var.set("🔴 未接続")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, font=("Arial", 12))
        status_label.grid(row=2, column=0, columnspan=3, pady=(10, 5))

        # メッセージ表示エリア
        ttk.Label(main_frame, text="受信データ:", font=("Arial", 12, "bold")).grid(row=3, column=0, sticky=(tk.W, tk.N), pady=(10, 5))

        # スクロール可能なテキストエリア
        self.text_area = scrolledtext.ScrolledText(main_frame, width=80, height=25, 
                                                  font=("Consolas", 10), wrap=tk.WORD)
        self.text_area.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 10))

        # 統計情報フレーム
        stats_frame = ttk.Frame(main_frame)
        stats_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))

        self.stats_var = tk.StringVar()
        self.stats_var.set("受信データ: 0件")
        stats_label = ttk.Label(stats_frame, textvariable=self.stats_var)
        stats_label.grid(row=0, column=0, sticky=tk.W)

        # クリアボタン
        clear_button = ttk.Button(stats_frame, text="表示クリア", command=self.clear_display)
        clear_button.grid(row=0, column=1, padx=(20, 0))

        # 初期メッセージを表示
        self.log_message("🏠 AXIS地震情報モニターへようこそ！", "INFO")
        self.log_message("📱 監視チャンネル: jmx-seismology, quake-one, eew", "INFO")
        self.log_message("🔑 トークンを確認して「接続開始」ボタンを押してください", "INFO")

    def log_message(self, message, level="INFO"):
        """メッセージをログに追加"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # レベルに応じたプレフィックス
        prefixes = {
            "INFO": "ℹ️ ",
            "SUCCESS": "✅ ",
            "WARNING": "⚠️ ",
            "ERROR": "❌ ",
            "DATA": "📡 "
        }
        prefix = prefixes.get(level, "")

        formatted_message = f"[{timestamp}] {prefix}{message}\n"

        self.text_area.insert(tk.END, formatted_message)
        self.text_area.see(tk.END)  # 自動スクロール

        # 統計情報を更新
        if level == "DATA":
            self.update_stats()

    def clear_display(self):
        """表示をクリア"""
        self.text_area.delete(1.0, tk.END)
        self.log_message("表示をクリアしました", "INFO")

    def update_stats(self):
        """統計情報を更新"""
        total_count = len(self.data_log)
        channel_counts = {}

        for entry in self.data_log:
            channel = entry['channel']
            channel_counts[channel] = channel_counts.get(channel, 0) + 1

        stats_text = f"受信データ: {total_count}件"
        if channel_counts:
            channel_info = ", ".join([f"{ch}:{cnt}" for ch, cnt in channel_counts.items()])
            stats_text += f" ({channel_info})"

        self.stats_var.set(stats_text)

    def toggle_connection(self):
        """接続の開始/停止を切り替え"""
        if not self.connected:
            self.start_connection()
        else:
            self.stop_connection()

    def start_connection(self):
        """接続開始"""
        token = self.token.get().strip()

        if not token:
            messagebox.showerror("エラー", "アクセストークンを入力してください")
            return

        self.log_message("接続を開始しています...", "INFO")
        self.connect_button.config(text="接続中...", state="disabled")

        # 別スレッドで接続処理を実行
        threading.Thread(target=self._connect_websocket, args=(token,), daemon=True).start()

    def _connect_websocket(self, token):
        """WebSocket接続処理（別スレッド）"""
        try:
            # サーバーリストを取得（簡略化）
            server_url = "wss://axis.prioris.jp/socket"  # 仮のURL

            headers = [f"Authorization: Bearer {token}"]

            self.ws = websocket.WebSocketApp(
                server_url,
                header=headers,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                on_open=self.on_open
            )

            # 接続開始
            self.ws.run_forever(ping_interval=60, ping_timeout=10)

        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"接続エラー: {e}", "ERROR"))
            self.root.after(0, self._reset_connect_button)

    def _reset_connect_button(self):
        """接続ボタンをリセット"""
        self.connected = False
        self.connect_button.config(text="接続開始", state="normal")
        self.status_var.set("🔴 未接続")

    def stop_connection(self):
        """接続停止"""
        self.log_message("接続を停止しています...", "WARNING")
        self.connected = False

        if self.ws:
            self.ws.close()

        self.connect_button.config(text="接続開始", state="normal")
        self.status_var.set("🔴 未接続")

    def on_message(self, ws, message):
        """WebSocketメッセージ受信"""
        if message == "hello":
            self.root.after(0, lambda: self.log_message("サーバーに接続されました", "SUCCESS"))
            return

        if message == "hb":
            # ハートビートは表示しない
            return

        try:
            data = json.loads(message)
            channel = data.get('channel', '不明')
            content = data.get('message', data)

            # データログに追加
            self.data_log.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'channel': channel,
                'data': content
            })

            # UIに表示（メインスレッドで実行）
            self.root.after(0, lambda: self._display_earthquake_data(channel, content))

        except json.JSONDecodeError:
            self.root.after(0, lambda: self.log_message(f"JSONパースエラー: {message}", "ERROR"))
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"データ処理エラー: {e}", "ERROR"))

    def _display_earthquake_data(self, channel, data):
        """地震データを表示"""
        if channel == "jmx-seismology":
            self.log_message("=== JMX地震学情報（気象庁電文） ===", "DATA")
            if isinstance(data, dict):
                for key, value in list(data.items())[:10]:  # 最初の10項目のみ表示
                    self.log_message(f"  {key}: {value}", "DATA")
                if len(data) > 10:
                    self.log_message(f"  ... 他{len(data)-10}項目", "DATA")
            else:
                self.log_message(f"  データ: {data}", "DATA")

        elif channel == "quake-one":
            self.log_message("=== QUAKE.ONE地震情報 ===", "DATA")
            if isinstance(data, dict):
                if 'earthquake' in data:
                    eq = data['earthquake']
                    self.log_message(f"  マグニチュード: {eq.get('magnitude', 'N/A')}", "DATA")
                    self.log_message(f"  震源地: {eq.get('hypocenter', 'N/A')}", "DATA")
                    self.log_message(f"  深さ: {eq.get('depth', 'N/A')} km", "DATA")
                if 'intensity' in data:
                    self.log_message(f"  最大震度: {data['intensity'].get('max', 'N/A')}", "DATA")
            else:
                self.log_message(f"  データ: {data}", "DATA")

        elif channel == "eew":
            self.log_message("=== 🚨 緊急地震速報 (EEW) ===", "DATA")
            if isinstance(data, dict):
                important_info = []
                if 'magnitude' in data:
                    important_info.append(f"M{data['magnitude']}")
                if 'maxIntensity' in data:
                    important_info.append(f"最大震度{data['maxIntensity']}")
                if 'hypocenter' in data:
                    important_info.append(f"{data['hypocenter']}")

                if important_info:
                    self.log_message(f"  🔥 {' / '.join(important_info)}", "DATA")
            else:
                self.log_message(f"  データ: {data}", "DATA")
        else:
            self.log_message(f"=== {channel} ===", "DATA")
            self.log_message(f"  {json.dumps(data, ensure_ascii=False)[:200]}...", "DATA")

        self.log_message("", "DATA")  # 空行で区切り

    def on_error(self, ws, error):
        """WebSocketエラー"""
        self.root.after(0, lambda: self.log_message(f"WebSocketエラー: {error}", "ERROR"))

    def on_close(self, ws, close_status_code, close_msg):
        """WebSocket接続終了"""
        self.root.after(0, lambda: self.log_message(f"接続が終了しました (コード: {close_status_code})", "WARNING"))
        self.root.after(0, self._reset_connect_button)

    def on_open(self, ws):
        """WebSocket接続開始"""
        self.connected = True
        self.root.after(0, lambda: self.log_message("AXISサーバーに接続されました！", "SUCCESS"))
        self.root.after(0, lambda: self.connect_button.config(text="接続停止", state="normal"))
        self.root.after(0, lambda: self.status_var.set("🟢 接続中"))

        # ハートビート開始
        def heartbeat():
            while self.connected:
                try:
                    if ws.sock and ws.sock.connected:
                        ws.send('hb')
                    time.sleep(30)
                except:
                    break

        threading.Thread(target=heartbeat, daemon=True).start()

def main():
    """メイン関数"""
    root = tk.Tk()

    # アプリアイコンの設定（可能であれば）
    try:
        root.iconbitmap(default="earthquake.ico")  # アイコンファイルがある場合
    except:
        pass

    app = AXISEarthquakeGUI(root)

    # ウィンドウを閉じる時の処理
    def on_closing():
        if app.connected:
            app.stop_connection()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # GUIを開始
    root.mainloop()

if __name__ == "__main__":
    main()
