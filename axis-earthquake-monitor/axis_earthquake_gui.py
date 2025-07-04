import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
import json # データ表示のために必要

class EarthquakeGUI:
    def __init__(self, root, callbacks=None):
        self.root = root
        self.root.title("AXIS地震情報モニター")
        self.root.geometry("800x600")
        self.callbacks = callbacks if callbacks else {}

        # 変数の初期化 (GUI表示用)
        self.token_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.stats_var = tk.StringVar()

        # デフォルトトークンを設定 (GUIが初期表示する値)
        default_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjp7ImlkIjoiZWlwaWlpaWkiLCJ0eXBlIjowLCJjb25uZWN0aW9uIjoyfSwiY2hhbm5lbHMiOlsiam14LXNlaXNtb2xvZ3kiLCJxdWFrZS1vbmUiLCJlZXciXSwiZXhwIjoxNzU0MDA2Mzk5fQ.bZHDTPisDku1ObKRv7iKUOXyIdCeuUg9mypKKs_b5FI"
        self.token_var.set(default_token)
        self.status_var.set("🔴 未接続")
        self.stats_var.set("受信データ: 0件")

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
        token_entry = ttk.Entry(main_frame, textvariable=self.token_var, width=50, show="*")
        token_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 5))

        # 接続ボタン
        self.connect_button = ttk.Button(main_frame, text="接続開始", command=self._on_connect_button_click)
        self.connect_button.grid(row=1, column=2, padx=(5, 0))

        # ステータス表示
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

        stats_label = ttk.Label(stats_frame, textvariable=self.stats_var)
        stats_label.grid(row=0, column=0, sticky=tk.W)

        # クリアボタン
        clear_button = ttk.Button(stats_frame, text="表示クリア", command=self.clear_display)
        clear_button.grid(row=0, column=1, padx=(20, 0))

        # 初期メッセージを表示
        self.append_log_message("🏠 AXIS地震情報モニターへようこそ！", "INFO")
        self.append_log_message("📱 監視チャンネル: jmx-seismology, quake-one, eew", "INFO")
        self.append_log_message("🔑 トークンを確認して「接続開始」ボタンを押してください", "INFO")

    def _on_connect_button_click(self):
        """接続ボタンクリック時のコールバック (Controllerに通知)"""
        token = self.token_var.get().strip()
        if not token:
            messagebox.showerror("エラー", "アクセストークンを入力してください")
            return
        
        if 'toggle_connection' in self.callbacks:
            self.callbacks['toggle_connection'](token)

    def append_log_message(self, message, level="INFO"):
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

    def clear_display(self):
        """表示をクリア"""
        self.text_area.delete(1.0, tk.END)
        self.append_log_message("表示をクリアしました", "INFO")

    def update_status_label(self, status_text):
        """ステータス表示を更新"""
        self.status_var.set(status_text)
        # 接続ボタンのテキストと状態も更新
        if "接続中" in status_text:
            self.connect_button.config(text="接続停止", state="normal")
        elif "未接続" in status_text:
            self.connect_button.config(text="接続開始", state="normal")
        else: # 例: "接続中..." の場合
            self.connect_button.config(text=status_text, state="disabled")

    def update_stats_label(self, total_count, channel_counts):
        """統計情報を更新"""
        stats_text = f"受信データ: {total_count}件"
        if channel_counts:
            channel_info = ", ".join([f"{ch}:{cnt}" for ch, cnt in channel_counts.items()])
            stats_text += f" ({channel_info})"
        self.stats_var.set(stats_text)

    def display_earthquake_data(self, channel, data):
        """地震データを表示"""
        self.append_log_message(f"\n{'='*80}", "DATA")
        self.append_log_message(f"🕐 受信時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "DATA")
        self.append_log_message(f"📡 チャンネル: {channel}", "DATA")
        self.append_log_message(f"{'='*80}", "DATA")

        if channel == "jmx-seismology":
            self.append_log_message("📡 JMX地震学情報（気象庁電文）", "DATA")
            self.append_log_message("-" * 40, "DATA")
            if isinstance(data, dict):
                important_keys = ['EventID', 'InfoType', 'Title', 'DateTime', 'Status']
                for key in important_keys:
                    if key in data:
                        self.append_log_message(f"  🔹 {key}: {data[key]}", "DATA")
                for key, value in data.items():
                    if key not in important_keys:
                        if isinstance(value, (dict, list)):
                            self.append_log_message(f"  🔸 {key}: {json.dumps(value, ensure_ascii=False)}", "DATA")
                        else:
                            self.append_log_message(f"  🔸 {key}: {value}", "DATA")
            else:
                self.append_log_message(f"  📄 データ: {data}", "DATA")

        elif channel == "quake-one":
            self.append_log_message("🌍 QUAKE.ONE地震情報", "DATA")
            self.append_log_message("-" * 40, "DATA")
            if isinstance(data, dict):
                if 'earthquake' in data:
                    eq_info = data['earthquake']
                    self.append_log_message("  🏔️  震源情報:", "DATA")
                    self.append_log_message(f"    📏 マグニチュード: {eq_info.get('magnitude', 'N/A')}", "DATA")
                    self.append_log_message(f"    📍 震源地: {eq_info.get('hypocenter', 'N/A')}", "DATA")
                    self.append_log_message(f"    🕳️  深さ: {eq_info.get('depth', 'N/A')} km", "DATA")
                    self.append_log_message(f"    🕐 発生時刻: {eq_info.get('time', 'N/A')}", "DATA")
                if 'intensity' in data:
                    intensity_info = data['intensity']
                    self.append_log_message("  📊 震度情報:", "DATA")
                    self.append_log_message(f"    🔥 最大震度: {intensity_info.get('max', 'N/A')}", "DATA")
                    if 'regions' in intensity_info:
                        self.append_log_message("    🗾 地域別震度:", "DATA")
                        for region in intensity_info['regions'][:5]:
                            self.append_log_message(f"      - {region}", "DATA")
                for key, value in data.items():
                    if key not in ['earthquake', 'intensity']:
                        if isinstance(value, (dict, list)):
                            self.append_log_message(f"  🔸 {key}: {json.dumps(value, ensure_ascii=False)}", "DATA")
                        else:
                            self.append_log_message(f"  🔸 {key}: {value}", "DATA")
            else:
                self.append_log_message(f"  📄 データ: {data}", "DATA")

        elif channel == "eew":
            self.append_log_message("🚨 緊急地震速報 (EEW)", "DATA")
            self.append_log_message("-" * 40, "DATA")
            if isinstance(data, dict):
                if 'magnitude' in data:
                    self.append_log_message(f"  🔥 マグニチュード: {data['magnitude']}", "DATA")
                if 'maxIntensity' in data or 'max_intensity' in data:
                    intensity = data.get('maxIntensity', data.get('max_intensity', 'N/A'))
                    self.append_log_message(f"  🔥 最大予想震度: {intensity}", "DATA")
                if 'origin_time' in data:
                    self.append_log_message(f"  ⏰ 発生時刻: {data['origin_time']}", "DATA")
                if 'hypocenter' in data:
                    self.append_log_message(f"  📍 震源地: {data['hypocenter']}", "DATA")
                if 'arrival_time' in data:
                    self.append_log_message(f"  ⚡ 到達予想時刻: {data['arrival_time']}", "DATA")
                if 'warning_time' in data:
                    self.append_log_message(f"  ⏰ 警報発表時刻: {data['warning_time']}", "DATA")
                
                for key, value in data.items():
                    important_keys = ['magnitude', 'maxIntensity', 'max_intensity', 'origin_time', 'hypocenter', 'arrival_time', 'warning_time']
                    if key not in important_keys:
                        if isinstance(value, (dict, list)):
                            self.append_log_message(f"  🔸 {key}: {json.dumps(value, ensure_ascii=False)}", "DATA")
                        else:
                            self.append_log_message(f"  🔸 {key}: {value}", "DATA")
            else:
                self.append_log_message(f"  📄 データ: {data}", "DATA")
        else:
            self.append_log_message(f"📄 メッセージ内容:", "DATA")
            self.append_log_message(json.dumps(data, ensure_ascii=False, indent=2), "DATA")

# main関数はaxis_earthquake_app.pyに移動
