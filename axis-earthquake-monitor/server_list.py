
import requests
import json

class AXISServerList:
    def __init__(self, token):
        self.token = token
        self.base_url = "https://axis.prioris.jp"  # 推測されるベースURL

    def get_available_servers(self):
        """利用可能なサーバーリストを取得"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        # APIエンドポイント（ドキュメントから推測）
        api_url = f"{self.base_url}/api/servers"  # 実際のURLは調整が必要

        try:
            response = requests.get(api_url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                return data.get('servers', [])
            else:
                print(f"サーバーリスト取得エラー: {response.status_code}")
                print(f"レスポンス: {response.text}")
                return []

        except requests.exceptions.RequestException as e:
            print(f"ネットワークエラー: {e}")
            return []

    def test_connection(self, server_url):
        """指定されたサーバーへの接続テスト"""
        import websocket
        import time

        try:
            headers = [f"Authorization: Bearer {self.token}"]

            def on_message(ws, message):
                print(f"受信: {message}")
                ws.close()

            def on_error(ws, error):
                print(f"エラー: {error}")

            def on_close(ws, close_status_code, close_msg):
                print("接続終了")

            def on_open(ws):
                print(f"✅ {server_url} への接続成功")
                # すぐに切断
                ws.close()

            ws = websocket.WebSocketApp(
                server_url,
                header=headers,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open
            )

            # 短時間でテスト
            ws.run_forever()
            return True

        except Exception as e:
            print(f"❌ {server_url} への接続失敗: {e}")
            return False

# 使用例
if __name__ == "__main__":
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjp7ImlkIjoiZWlwaWlpaWkiLCJ0eXBlIjowLCJjb25uZWN0aW9uIjoyfSwiY2hhbm5lbHMiOlsiam14LXNlaXNtb2xvZ3kiLCJxdWFrZS1vbmUiLCJlZXciXSwiZXhwIjoxNzU0MDA2Mzk5fQ.bZHDTPisDku1ObKRv7iKUOXyIdCeuUg9mypKKs_b5FI"

    server_list = AXISServerList(token)
    servers = server_list.get_available_servers()

    if servers:
        print("利用可能なサーバー:")
        for i, server in enumerate(servers, 1):
            print(f"{i}. {server}")
    else:
        print("サーバーリストを取得できませんでした")
