#!/bin/bash
# 競馬データ閲覧ツール - Linux/Mac用シェルスクリプト

if [ $# -eq 0 ]; then
    echo "競馬データ閲覧ツール"
    echo ""
    echo "使い方:"
    echo "  ./view_data.sh list              - レース一覧を表示"
    echo "  ./view_data.sh race [レースID]   - レース詳細を表示"
    echo "  ./view_data.sh horse [馬ID]      - 馬の過去成績を表示"
    echo "  ./view_data.sh stats             - データベース統計を表示"
    echo ""
    echo "例:"
    echo "  ./view_data.sh list"
    echo "  ./view_data.sh race 201506010101"
    echo "  ./view_data.sh horse 2012104324"
    echo ""
    exit 1
fi

python3 view_data.py "$@"
