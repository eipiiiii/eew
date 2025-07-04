import websocket
import requests
import json
import threading
import time
from datetime import datetime

class EarthquakeModel:
    def __init__(self, callbacks=None):
        self.callbacks = callbacks if callbacks else {}
        self.connected = False
        self.ws = None
        self.data_log = []
        self.server_url = None
        self.token = None # トークンはModelで保持する

    def set_token(self, token):
        self.token = token

    def get_server_list(self):
        """AXISサーバーリストを取得"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        possible_urls = [
            "https://axis.prioris.jp/api/server/list/"
        ]

        for api_url in possible_urls:
            try:
                self._notify_log_message(f"サーバーリスト取得試行: {api_url}", "INFO")
                response = requests.get(api_url, headers=headers, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    servers = data.get('servers', [])
                    if servers:
                        self._notify_log_message(f"サーバーリスト取得成功: {len(servers)}個のサーバー", "SUCCESS")
                        return servers
                else:
                    self._notify_log_message(f"エラー {response.status_code}: {response.text}", "ERROR")

            except requests.exceptions.RequestException as e:
                self._notify_log_message(f"接続エラー: {e}", "ERROR")
            except Exception as e:
                self._notify_log_message(f"その他のエラー: {e}", "ERROR")

        self._notify_log_message("サーバーリストAPIが利用できません。推測サーバーを使用します。", "WARNING")
        return ["wss://axis.prioris.jp/socket"]

    def toggle_connection(self):
        """接続の開始/停止を切り替え"""
        if not self.connected:
            self.start_websocket_connection()
        else:
            self.stop_websocket_connection()

    def start_websocket_connection(self):
        """WebSocket接続開始"""
        if not self.token:
            self._notify_log_message("アクセストークンが設定されていません。", "ERROR")
            return

        self._notify_log_message("接続を開始しています...", "INFO")
        self._notify_status_update("接続中...") # GUIに接続中であることを通知

        # 別スレッドで接続処理を実行
        threading.Thread(target=self._connect_websocket, daemon=True).start()

    def _connect_websocket(self):
        """WebSocket接続処理（別スレッド）"""
        try:
            servers = self.get_server_list()
            if not servers:
                self._notify_log_message("利用可能なサーバーが見つかりません", "ERROR")
                self._reset_connection_state()
                return

            self.server_url = servers[0] + "/socket"
            self._notify_log_message(f"接続先サーバー: {self.server_url}", "INFO")

            websocket.enableTrace(False)  # デバッグログを無効化
            headers = [f"Authorization: Bearer {self.token}"]

            self.ws = websocket.WebSocketApp(
                self.server_url,
                header=headers,
                on_message=self.on_websocket_message,
                on_error=self.on_websocket_error,
                on_close=self.on_websocket_close,
                on_open=self.on_websocket_open
            )

            # 接続開始
            self.ws.run_forever(ping_interval=60, ping_timeout=10)

        except Exception as e:
            self._notify_log_message(f"接続エラー: {e}", "ERROR")
            self._reset_connection_state()

    def _reset_connection_state(self):
        """接続状態をリセット"""
        self.connected = False
        self._notify_status_update("🔴 未接続")
        self._notify_connection_reset() # Controllerに接続リセットを通知

    def stop_websocket_connection(self):
        """接続停止"""
        self._notify_log_message("接続を停止しています...", "WARNING")
        self.connected = False

        if self.ws:
            self.ws.close()
            self.ws = None # WebSocketAppオブジェクトをクリア

        self._reset_connection_state()

    def on_websocket_message(self, ws, message):
        """WebSocketメッセージ受信"""
        if message == "hello":
            self._notify_log_message("サーバーに接続されました", "SUCCESS")
            return

        if message == "hb":
            # ハートビートは表示しない
            return

        try:
            data = json.loads(message)
            channel = data.get('channel', '不明')
            content = data.get('message', data) # messageキーがない場合はdata全体を使用

            # データログに追加
            self.data_log.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'channel': channel,
                'data': content
            })

            # Controllerにデータ受信を通知
            self._notify_data_received(channel, content)
            self._notify_stats_update() # 統計情報更新を通知

        except json.JSONDecodeError:
            self._notify_log_message(f"JSONパースエラー: {message}", "ERROR")
        except Exception as e:
            self._notify_log_message(f"データ処理エラー: {e}", "ERROR")

    def on_websocket_error(self, ws, error):
        """WebSocketエラー"""
        self._notify_log_message(f"❌ WebSocketエラー: {error}", "ERROR")

    def on_websocket_close(self, ws, close_status_code, close_msg):
        """WebSocket接続終了"""
        self.connected = False
        self._notify_log_message(f"🔌 サーバーとの接続が終了しました (コード: {close_status_code})", "WARNING")
        if close_msg:
            self._notify_log_message(f"理由: {close_msg}", "WARNING")
        self._reset_connection_state()

    def on_websocket_open(self, ws):
        """WebSocket接続開始"""
        self.connected = True
        self._notify_log_message("🌐 AXISサーバーに正常に接続しました！", "SUCCESS")
        self._notify_status_update("🟢 接続中")
        self._notify_connection_established() # Controllerに接続確立を通知
        self._notify_log_message("📡 地震情報の受信を開始します...", "INFO")
        self._notify_log_message("📱 監視中のチャンネル: jmx-seismology, quake-one, eew", "INFO")
        self._notify_log_message("⚠️  終了するにはウィンドウを閉じるか「接続停止」ボタンを押してください", "INFO")

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

    def get_data_log(self):
        """現在のデータログを返す"""
        return self.data_log

    # --- 通知メソッド (Controllerへのコールバック呼び出し) ---
    def _notify_log_message(self, message, level):
        if 'log_message' in self.callbacks:
            self.callbacks['log_message'](message, level)

    def _notify_status_update(self, status_text):
        if 'status_update' in self.callbacks:
            self.callbacks['status_update'](status_text)

    def _notify_data_received(self, channel, data):
        if 'data_received' in self.callbacks:
            self.callbacks['data_received'](channel, data)

    def _notify_stats_update(self):
        if 'stats_update' in self.callbacks:
            total_count = len(self.data_log)
            channel_counts = {}
            for entry in self.data_log:
                channel = entry['channel']
                channel_counts[channel] = channel_counts.get(channel, 0) + 1
            self.callbacks['stats_update'](total_count, channel_counts)

    def _notify_connection_established(self):
        if 'connection_established' in self.callbacks:
            self.callbacks['connection_established']()

    def _notify_connection_reset(self):
        if 'connection_reset' in self.callbacks:
            self.callbacks['connection_reset']()