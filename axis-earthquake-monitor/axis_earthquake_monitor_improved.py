import websocket
import requests
import json
import threading
import time
from datetime import datetime
import sys

class AXISEarthquakeMonitor:
    def __init__(self, token):
        self.token = token
        self.ws = None
        self.connected = False
        self.data_log = []
        self.server_url = None

    def get_server_list(self):
        """AXISサーバーリストを取得"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        # 推測されるAPIエンドポイント
        possible_urls = [
            "https://axis.prioris.jp/api/server/list/"
        ]

        for api_url in possible_urls:
            try:
                print(f"サーバーリスト取得試行: {api_url}")
                response = requests.get(api_url, headers=headers, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    servers = data.get('servers', [])
                    if servers:
                        print(f"✅ サーバーリスト取得成功: {len(servers)}個のサーバー")
                        return servers
                else:
                    print(f"❌ エラー {response.status_code}: {response.text}")

            except requests.exceptions.RequestException as e:
                print(f"❌ 接続エラー: {e}")
            except Exception as e:
                print(f"❌ その他のエラー: {e}")

        # フォールバック: ドキュメントから推測されるサーバー
        print("⚠️  サーバーリストAPIが利用できません。推測サーバーを使用します。")
        return ["wss://axis.prioris.jp/socket"]

    def on_message(self, ws, message):
        """WebSocketからメッセージを受信した時の処理"""
        if message == "hello":
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🟢 サーバーに接続されました")
            return

        if message == "hb":
            # ハートビート（生存確認）メッセージ - 通常は表示しない
            return

        try:
            # JSONデータをパース
            data = json.loads(message)
            channel = data.get('channel', '不明')
            content = data.get('message', data)  # messageキーがない場合はdata全体を使用

            # 受信時刻を記録
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            print(f"\n{'='*80}")
            print(f"🕐 受信時刻: {timestamp}")
            print(f"📡 チャンネル: {channel}")
            print(f"{'='*80}")

            if channel == "jmx-seismology":
                self.display_jmx_seismology(content)
            elif channel == "quake-one":
                self.display_quake_one(content)
            elif channel == "eew":
                self.display_eew(content)
            else:
                print(f"📄 メッセージ内容:")
                print(json.dumps(content, ensure_ascii=False, indent=2))

            # データをログに保存
            self.data_log.append({
                'timestamp': timestamp,
                'channel': channel,
                'data': content
            })

        except json.JSONDecodeError as e:
            print(f"❌ JSONパースエラー: {e}")
            print(f"📄 受信データ: {message}")
        except Exception as e:
            print(f"❌ データ処理エラー: {e}")

    def display_jmx_seismology(self, data):
        """JMX地震学データの表示"""
        print("📡 JMX地震学情報（気象庁電文）")
        print("-" * 40)
        if isinstance(data, dict):
            # 重要な情報を優先表示
            important_keys = ['EventID', 'InfoType', 'Title', 'DateTime', 'Status']
            for key in important_keys:
                if key in data:
                    print(f"  🔹 {key}: {data[key]}")

            # その他の情報
            for key, value in data.items():
                if key not in important_keys:
                    if isinstance(value, (dict, list)):
                        print(f"  🔸 {key}: {json.dumps(value, ensure_ascii=False)}")
                    else:
                        print(f"  🔸 {key}: {value}")
        else:
            print(f"  📄 データ: {data}")

    def display_quake_one(self, data):
        """QUAKE.ONE データの表示"""
        print("🌍 QUAKE.ONE地震情報")
        print("-" * 40)
        if isinstance(data, dict):
            # 震源情報
            if 'earthquake' in data:
                eq_info = data['earthquake']
                print("  🏔️  震源情報:")
                print(f"    📏 マグニチュード: {eq_info.get('magnitude', 'N/A')}")
                print(f"    📍 震源地: {eq_info.get('hypocenter', 'N/A')}")
                print(f"    🕳️  深さ: {eq_info.get('depth', 'N/A')} km")
                print(f"    🕐 発生時刻: {eq_info.get('time', 'N/A')}")

            # 震度情報
            if 'intensity' in data:
                intensity_info = data['intensity']
                print("  📊 震度情報:")
                print(f"    🔥 最大震度: {intensity_info.get('max', 'N/A')}")
                if 'regions' in intensity_info:
                    print("    🗾 地域別震度:")
                    for region in intensity_info['regions'][:5]:  # 最初の5件のみ表示
                        print(f"      - {region}")

            # その他の情報を表示
            for key, value in data.items():
                if key not in ['earthquake', 'intensity']:
                    if isinstance(value, (dict, list)):
                        print(f"  🔸 {key}: {json.dumps(value, ensure_ascii=False)}")
                    else:
                        print(f"  🔸 {key}: {value}")
        else:
            print(f"  📄 データ: {data}")

    def display_eew(self, data):
        """緊急地震速報(EEW)データの表示"""
        print("🚨 緊急地震速報 (EEW)")
        print("-" * 40)
        if isinstance(data, dict):
            # 重要な情報を強調表示
            if 'magnitude' in data:
                print(f"  🔥 マグニチュード: {data['magnitude']}")
            if 'maxIntensity' in data or 'max_intensity' in data:
                intensity = data.get('maxIntensity', data.get('max_intensity', 'N/A'))
                print(f"  🔥 最大予想震度: {intensity}")
            if 'origin_time' in data:
                print(f"  ⏰ 発生時刻: {data['origin_time']}")
            if 'hypocenter' in data:
                print(f"  📍 震源地: {data['hypocenter']}")
            if 'arrival_time' in data:
                print(f"  ⚡ 到達予想時刻: {data['arrival_time']}")
            if 'warning_time' in data:
                print(f"  ⏰ 警報発表時刻: {data['warning_time']}")

            # その他の情報
            for key, value in data.items():
                important_keys = ['magnitude', 'maxIntensity', 'max_intensity', 'origin_time', 'hypocenter', 'arrival_time', 'warning_time']
                if key not in important_keys:
                    if isinstance(value, (dict, list)):
                        print(f"  🔸 {key}: {json.dumps(value, ensure_ascii=False)}")
                    else:
                        print(f"  🔸 {key}: {value}")
        else:
            print(f"  📄 データ: {data}")

    def on_error(self, ws, error):
        """エラー発生時の処理"""
        print(f"❌ WebSocketエラー: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        """接続終了時の処理"""
        self.connected = False
        print(f"\n🔌 サーバーとの接続が終了しました (コード: {close_status_code})")
        if close_msg:
            print(f"理由: {close_msg}")

    def on_open(self, ws):
        """接続開始時の処理"""
        self.connected = True
        print("\n" + "="*80)
        print("🌐 AXISサーバーに正常に接続しました！")
        print("📡 地震情報の受信を開始します...")
        print("📱 監視中のチャンネル: jmx-seismology, quake-one, eew")
        print("⚠️  終了するには Ctrl+C を押してください")
        print("="*80)

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
        print("🚀 AXIS地震情報モニター開始")
        print(f"🔑 トークン: {self.token[:20]}...")
        print("")

        # サーバーリストを取得
        servers = self.get_server_list()

        if not servers:
            print("❌ 利用可能なサーバーが見つかりません")
            return

        # 最初のサーバーを使用
        self.server_url = servers[0] + "/socket"
        print(f"🌐 接続先サーバー: {self.server_url}")

        # WebSocketアプリケーションを作成
        websocket.enableTrace(False)  # デバッグログを無効化

        headers = [f"Authorization: Bearer {self.token}"]

        self.ws = websocket.WebSocketApp(
            self.server_url,
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
        print("🛑 監視を停止しています...")
        self.connected = False
        if self.ws:
            self.ws.close()

        # 統計情報を表示
        if self.data_log:
            summary = self.get_log_summary()
            print("\n📊 受信データ統計:")
            print(f"  総メッセージ数: {summary['total_messages']}")
            print("  チャンネル別:")
            for channel, count in summary['channels'].items():
                print(f"    - {channel}: {count}件")
            print(f"  最終受信時刻: {summary['latest_message']}")

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

# 使用例とメイン処理
if __name__ == "__main__":
    print("="*80)
    print("🏠 AXIS地震情報リアルタイムモニター")
    print("="*80)
    print("📱 このアプリケーションは以下の地震情報をリアルタイムで監視します:")
    print("   - jmx-seismology: 気象庁の地震関係電文")
    print("   - quake-one: QUAKE.ONEの地震概要・震源震度情報")
    print("   - eew: 緊急地震速報")
    print("")
    print("⚠️  注意: このアプリケーションは個人利用を想定しています")
    print("")

    # 提供されたトークンを使用
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjp7ImlkIjoiZWlwaWlpaWkiLCJ0eXBlIjowLCJjb25uZWN0aW9uIjoyfSwiY2hhbm5lbHMiOlsiam14LXNlaXNtb2xvZ3kiLCJxdWFrZS1vbmUiLCJlZXciXSwiZXhwIjoxNzU0MDA2Mzk5fQ.bZHDTPisDku1ObKRv7iKUOXyIdCeuUg9mypKKs_b5FI"

    try:
        # モニターを作成・開始
        monitor = AXISEarthquakeMonitor(token)
        monitor.start()
    except KeyboardInterrupt:
        print("\n👋 プログラムを終了します")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 予期しないエラーが発生しました: {e}")
        sys.exit(1)
