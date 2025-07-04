#!/bin/bash

echo "====================================="
echo " AXIS地震情報リアルタイムモニター"
echo "====================================="
echo

echo "必要なライブラリをインストールしています..."
pip3 install -r requirements.txt

echo
echo "アプリケーションを起動しています..."
echo "終了するには Ctrl+C を押してください"
echo

python3 axis_earthquake_monitor_improved.py
