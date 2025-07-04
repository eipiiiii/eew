
import websocket
import json
import threading
import time
from datetime import datetime

class AXISEarthquakeMonitor:
    def __init__(self, token):
        self.token = token
        self.ws = None
        self.connected = False
        self.data_log = []

    def on_message(self, ws, message):
        """WebSocketからメッセージを受信した時の処理"""
        if message == "hello":
            print(f"[{datetime.now().strftime('%H:%M:%S')}] サーバーに接続されました")
            return

        if message == "hb":
            # ハートビート（生存確認）メッセージ
            return

        try:
            # JSONデータをパース
            data = json.loads(message)
            channel = data.get('channel', '不明')
            content = data.get('message', {})

            # 受信時刻を記録
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            print(f"\n{'='*60}")
            print(f"受信時刻: {timestamp}")
            print(f"チャンネル: {channel}")

            if channel == "jmx-seismology":
                self.display_jmx_seismology(content)
            elif channel == "quake-one":
                self.display_quake_one(content)
            elif channel == "eew":
                self.display_eew(content)
            else:
                print(f"メッセージ内容: {json.dumps(content, ensure_ascii=False, indent=2)}")

            # データをログに保存
            self.data_log.append({
                'timestamp': timestamp,
                'channel': channel,
                'data': content
            })

        except json.JSONDecodeError as e:
            print(f"JSONパースエラー: {e}")
            print(f"受信データ: {message}")
        except Exception as e:
            print(f"データ処理エラー: {e}")

    def display_jmx_seismology(self, data):
        """JMX地震学データの表示"""
        print("📡 JMX地震学情報")
        if isinstance(data, dict):
            for key, value in data.items():
                print(f"  {key}: {value}")
        else:
            print(f"  データ: {data}")

    def display_quake_one(self, data):
        """QUAKE.ONE データの表示"""
        print("🌍 QUAKE.ONE地震情報")
        if isinstance(data, dict):
            # 震源情報
            if 'earthquake' in data:
                eq_info = data['earthquake']
                print(f"  マグニチュード: {eq_info.get('magnitude', 'N/A')}")
                print(f"  震源地: {eq_info.get('hypocenter', 'N/A')}")
                print(f"  深さ: {eq_info.get('depth', 'N/A')} km")
                print(f"  発生時刻: {eq_info.get('time', 'N/A')}")

            # 震度情報
            if 'intensity' in data:
                print(f"  最大震度: {data['intensity'].get('max', 'N/A')}")

            # その他の情報を表示
            for key, value in data.items():
                if key not in ['earthquake', 'intensity']:
                    print(f"  {key}: {value}")
        else:
            print(f"  データ: {data}")

    def display_eew(self, data):
        """緊急地震速報(EEW)データの表示"""
        print("🚨 緊急地震速報 (EEW)")
        if isinstance(data, dict):
            # 重要な情報を強調表示
            if 'magnitude' in data:
                print(f"  🔥 マグニチュード: {data['magnitude']}")
            if 'maxIntensity' in data:
                print(f"  🔥 最大予想震度: {data['maxIntensity']}")
            if 'origin_time' in data:
                print(f"  ⏰ 発生時刻: {data['origin_time']}")
            if 'hypocenter' in data:
                print(f"  📍 震源地: {data['hypocenter']}")
            if 'arrival_time' in data:
                print(f"  ⚡ 到達予想時刻: {data['arrival_time']}")

            # その他の情報
            for key, value in data.items():
                if key not in ['magnitude', 'maxIntensity', 'origin_time', 'hypocenter', 'arrival_time']:
                    print(f"  {key}: {value}")
        else:
            print(f"  データ: {data}")

    def on_error(self, ws, error):
        """エラー発生時の処理"""
        print(f"❌ WebSocketエラー: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        """接続終了時の処理"""
        self.connected = False
        print("\n🔌 サーバーとの接続が終了しました")
        print("再接続を試みます...")

    def on_open(self, ws):
        """接続開始時の処理"""
        self.connected = True
        print("🌐 AXISサーバーに接続しました")
        print("地震情報の受信を開始します...")
        print("終了するには Ctrl+C を押してください")

        # ハートビート送信用のスレッドを開始
        def heartbeat():
            while self.connected:
                try:
                    if ws.sock and ws.sock.connected:
                        ws.send('hb')
                    time.sleep(30)  # 30秒間隔でハートビート送信
                except:
                    break

        hb_thread = threading.Thread(target=heartbeat, daemon=True)
        hb_thread.start()

    def start(self):
        """監視開始"""
        # AXISサーバのWebSocketエンドポイントを設定
        # 実際のサーバー情報は提供されたドキュメントから取得する必要があります

        print("📱 AXIS地震情報モニター開始")
        print(f"トークン: {self.token[:20]}...")

        # WebSocketアプリケーションを作成
        websocket.enableTrace(True)  # デバッグ用

        headers = [f"Authorization: Bearer {self.token}"]

        # 実際のAXISサーバーURLが必要（ドキュメントから取得）
        server_url = "wss://axis-server-url/socket"  # 実際のURLに置き換える必要があります

        self.ws = websocket.WebSocketApp(
            server_url,
            header=headers,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )

        try:
            # 接続開始（永続化）
            self.ws.run_forever(ping_interval=60, ping_timeout=10)
        except KeyboardInterrupt:
            print("\n⚠️  終了シグナルを受信しました")
            self.stop()
        except Exception as e:
            print(f"❌ 接続エラー: {e}")

    def stop(self):
        """監視停止"""
        print("📱 監視を停止しています...")
        self.connected = False
        if self.ws:
            self.ws.close()
        print("✅ 停止完了")

    def get_log_summary(self):
        """受信データのサマリーを取得"""
        if not self.data_log:
            return "受信データはありません"

        summary = {
            'total_messages': len(self.data_log),
            'channels': {},
            'latest_message': self.data_log[-1]['timestamp'] if self.data_log else None
        }

        for entry in self.data_log:
            channel = entry['channel']
            if channel not in summary['channels']:
                summary['channels'][channel] = 0
            summary['channels'][channel] += 1

        return summary

# 使用例
if __name__ == "__main__":
    # 提供されたトークンを使用
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjp7ImlkIjoiZWlwaWlpaWkiLCJ0eXBlIjowLCJjb25uZWN0aW9uIjoyfSwiY2hhbm5lbHMiOlsiam14LXNlaXNtb2xvZ3kiLCJxdWFrZS1vbmUiLCJlZXciXSwiZXhwIjoxNzU0MDA2Mzk5fQ.bZHDTPisDku1ObKRv7iKUOXyIdCeuUg9mypKKs_b5FI"

    # モニターを作成・開始
    monitor = AXISEarthquakeMonitor(token)
    monitor.start()
