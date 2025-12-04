@echo off
REM 競馬データ閲覧ツール - Windows用バッチファイル

if "%1"=="" (
    echo 競馬データ閲覧ツール
    echo.
    echo 使い方:
    echo   view_data.bat list              - レース一覧を表示
    echo   view_data.bat race [レースID]   - レース詳細を表示
    echo   view_data.bat horse [馬ID]      - 馬の過去成績を表示
    echo   view_data.bat stats             - データベース統計を表示
    echo.
    echo 例:
    echo   view_data.bat list
    echo   view_data.bat race 201506010101
    echo   view_data.bat horse 2012104324
    echo.
    pause
    exit /b
)

python view_data.py %*
