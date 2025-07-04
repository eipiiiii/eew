# AXIS地震情報リアルタイムモニター

🏠 AXISサーバーから地震情報をリアルタイムで取得・表示するPythonアプリケーション

## 📋 概要

このアプリケーションは、[AXIS by Prioris](https://axis.prioris.jp/)のWebSocket APIを使用して、以下の3つの地震情報チャンネルからデータを受信・表示します：

- **jmx-seismology**: 気象庁電文の地震関係情報
- **quake-one**: QUAKE.ONEで提供される地震概要、震源・震度情報(GeoJSON)
- **eew**: 緊急地震速報（Emergency Earthquake Warning）

## 🎯 対象ユーザー

- WebSocketについて詳しくない個人ユーザー
- パソコンの中で地震情報を監視したい方
- 地震情報をリアルタイムで受信したい開発者

## 📦 ファイル構成

```
axis-earthquake-monitor/
├── README.md                          # このファイル
├── requirements.txt                   # 必要なライブラリ
├── axis_earthquake_monitor.py         # 基本版コンソールアプリ
├── axis_earthquake_monitor_improved.py # 改良版コンソールアプリ
├── axis_earthquake_gui.py             # GUI版アプリケーション
└── server_list.py                     # サーバーリスト取得用
```

## 🛠️ セットアップ

### 1. 必要なライブラリのインストール

```bash
pip install -r requirements.txt
```

または、個別にインストール：

```bash
pip install websocket-client==1.8.0
pip install requests==2.31.0
```

### 2. AXISアクセストークンの準備

- [AXIS by Prioris](https://axis.prioris.jp/)でアカウントを作成
- アクセストークンを取得
- 提供されたサンプルトークンも利用可能

## 🚀 使用方法

### コンソール版（推奨）

最も安定した改良版を使用：

```bash
python axis_earthquake_monitor_improved.py
```

### GUI版

グラフィカルなインターフェースを使用：

```bash
python axis_earthquake_gui.py
```

### 基本版

シンプルなコンソール版：

```bash
python axis_earthquake_monitor.py
```

## 📱 アプリケーションの特徴

### コンソール版

- 🔄 **リアルタイム監視**: WebSocketでライブデータ受信
- 🔗 **自動再接続**: 接続が切れた場合の自動復旧
- 💓 **ハートビート機能**: 接続維持のための生存確認
- 📊 **統計情報**: 受信データの要約表示
- 🎨 **見やすい表示**: チャンネル別の整理された情報表示

### GUI版

- 🖥️ **使いやすいインターフェース**: Tkinterベースの直感的なUI
- 📺 **リアルタイム表示**: スクロール可能なログ表示
- 🔴🟢 **接続状態表示**: 視覚的な接続ステータス
- 📈 **統計情報**: 受信データ数の表示
- 🧹 **表示クリア**: ログのクリア機能

## 📡 データ形式

### jmx-seismology（気象庁電文）
```json
{
  "channel": "jmx-seismology",
  "message": {
    "EventID": "20250704123456",
    "InfoType": "発表",
    "Title": "震源・震度に関する情報",
    "DateTime": "2025-07-04T12:34:56+09:00"
  }
}
```

### quake-one（QUAKE.ONE地震情報）
```json
{
  "channel": "quake-one",
  "message": {
    "earthquake": {
      "magnitude": 5.2,
      "hypocenter": "千葉県東方沖",
      "depth": 30,
      "time": "2025-07-04T12:34:56+09:00"
    },
    "intensity": {
      "max": "4"
    }
  }
}
```

### eew（緊急地震速報）
```json
{
  "channel": "eew",
  "message": {
    "magnitude": 6.1,
    "maxIntensity": "5弱",
    "hypocenter": "茨城県沖",
    "origin_time": "2025-07-04T12:34:56+09:00",
    "arrival_time": "2025-07-04T12:35:10+09:00"
  }
}
```

## ⚙️ 設定とカスタマイズ

### トークンの設定

アプリケーション内でトークンを変更する場合：

```python
token = "あなたのトークンをここに入力"
```

### サーバーURLの変更

実際のAXISサーバーURLが判明した場合：

```python
server_url = "wss://実際のサーバーURL/socket"
```

## 🔧 トラブルシューティング

### 接続エラー

- ネットワーク接続を確認
- トークンの有効性を確認
- ファイアウォール設定を確認

### モジュールが見つからないエラー

```bash
pip install websocket-client requests
```

### SSL証明書エラー

```python
# SSL証明書の検証を無効化する場合（非推奨）
ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
```

## 📚 技術詳細

### 使用技術

- **WebSocket**: リアルタイム通信用プロトコル
- **Python 3.7+**: 基本実行環境
- **websocket-client**: WebSocketクライアントライブラリ
- **Tkinter**: GUI作成（標準ライブラリ）
- **requests**: HTTP通信用ライブラリ

### アーキテクチャ

```
┌─────────────────┐    WebSocket    ┌─────────────────┐
│                 │ ←─────────────→ │                 │
│  Pythonアプリ    │     WSS://      │  AXISサーバー   │
│                 │                 │                 │
└─────────────────┘                 └─────────────────┘
        │                                    │
        ▼                                    ▼
┌─────────────────┐                 ┌─────────────────┐
│  地震情報表示    │                 │ jmx-seismology  │
│                 │                 │ quake-one       │
│ - コンソール版   │                 │ eew             │
│ - GUI版         │                 │                 │
└─────────────────┘                 └─────────────────┘
```

## ⚠️ 注意事項

- このアプリケーションは**個人利用**を想定しています
- AXISサービスの利用規約を遵守してください
- 緊急地震速報は**参考情報**として扱い、公式情報を優先してください
- 継続的な監視により、データ通信量が発生する可能性があります

## 📜 ライセンス

このプロジェクトは教育・個人利用目的で作成されています。
AXISサービス自体の利用は[AXIS by Prioris](https://axis.prioris.jp/)の利用規約に従ってください。

## 🤝 サポート

- **AXIS公式サイト**: https://axis.prioris.jp/
- **ドキュメント**: https://axis.prioris.jp/docs/stream/subscriber/

## 📊 プロジェクト統計

- **開発言語**: Python 3.7+
- **コード行数**: 約800行
- **対応OS**: Windows, macOS, Linux
- **GUI**: Tkinter（標準ライブラリ）
- **通信**: WebSocket over TLS

## 🔮 今後の機能拡張

- [ ] 地震データのCSV出力機能
- [ ] 通知音の追加
- [ ] 地図表示機能
- [ ] データの統計分析機能
- [ ] 複数サーバーからの並行受信

---

**最終更新**: 2025年7月4日
**作成者**: AI Assistant (Claude)
**対象**: Python初心者〜中級者