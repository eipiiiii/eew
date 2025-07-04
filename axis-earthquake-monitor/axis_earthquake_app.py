import tkinter as tk
from tkinter import messagebox
import sys
import os

# 同じディレクトリ内のモジュールをインポート
from axis_earthquake_model import EarthquakeModel
from axis_earthquake_gui import EarthquakeGUI

class EarthquakeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AXIS地震情報モニター")

        # ModelとViewに渡すコールバック関数を定義
        self.model_callbacks = {
            'log_message': self.on_model_log_message,
            'status_update': self.on_model_status_update,
            'data_received': self.on_model_data_received,
            'stats_update': self.on_model_stats_update,
            'connection_established': self.on_model_connection_established,
            'connection_reset': self.on_model_connection_reset
        }

        self.gui_callbacks = {
            'toggle_connection': self.on_gui_toggle_connection
        }

        self.model = EarthquakeModel(callbacks=self.model_callbacks)
        self.gui = EarthquakeGUI(root, callbacks=self.gui_callbacks)

        # アプリアイコンの設定（可能であれば）
        try:
            # スクリプトのディレクトリを取得
            script_dir = os.path.dirname(__file__)
            icon_path = os.path.join(script_dir, "earthquake.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(default=icon_path)
            else:
                # アイコンファイルがない場合は警告をログに出すなど
                self.on_model_log_message(f"アイコンファイルが見つかりません: {icon_path}", "WARNING")
        except Exception as e:
            self.on_model_log_message(f"アプリアイコン設定エラー: {e}", "ERROR")
            pass

        # ウィンドウを閉じる時の処理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def run(self):
        """アプリケーションを開始"""
        self.root.mainloop()

    # --- GUIからのイベントハンドラ (Controllerの役割) ---
    def on_gui_toggle_connection(self, token):
        """GUIの接続ボタンがクリックされたときにModelに通知"""
        self.model.set_token(token) # Modelにトークンを設定
        self.model.toggle_connection()

    # --- Modelからの通知ハンドラ (Controllerの役割) ---
    def on_model_log_message(self, message, level):
        """ModelからのログメッセージをGUIに表示"""
        self.root.after(0, lambda: self.gui.append_log_message(message, level))

    def on_model_status_update(self, status_text):
        """Modelからのステータス更新をGUIに表示"""
        self.root.after(0, lambda: self.gui.update_status_label(status_text))

    def on_model_data_received(self, channel, data):
        """Modelからのデータ受信をGUIに表示"""
        self.root.after(0, lambda: self.gui.display_earthquake_data(channel, data))

    def on_model_stats_update(self, total_count, channel_counts):
        """Modelからの統計情報更新をGUIに表示"""
        self.root.after(0, lambda: self.gui.update_stats_label(total_count, channel_counts))

    def on_model_connection_established(self):
        """Modelからの接続確立通知"""
        # GUIのボタン状態はstatus_updateで更新されるため、ここでは特に何もしない
        pass

    def on_model_connection_reset(self):
        """Modelからの接続リセット通知"""
        # GUIのボタン状態はstatus_updateで更新されるため、ここでは特に何もしない
        pass

    def on_closing(self):
        """ウィンドウを閉じる時の処理"""
        if self.model.connected:
            self.model.stop_websocket_connection()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = EarthquakeApp(root)
    app.run()