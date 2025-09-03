@echo off
setlocal

REM templates 配下のすべての内容を
REM %APPDATA%\onecomme\templates\custom にコピーします。

set "SRC=%~dp0templates"
set "DEST=%APPDATA%\onecomme\templates\custom"

echo [INFO] 宛先フォルダを確認しています: "%DEST%"
if not exist "%DEST%" (
    echo [INFO] 宛先フォルダが存在しないため作成します...
    mkdir "%DEST%" 2>nul
    if errorlevel 1 (
        echo [ERROR] 宛先フォルダの作成に失敗しました: "%DEST%"
        exit /b 1
    )
)

if not exist "%SRC%" (
    echo [ERROR] ソースフォルダが見つかりません: "%SRC%"
    exit /b 2
)

echo [INFO] コピー中... "%SRC%" -> "%DEST%"

REM robocopy を使用してサブフォルダ含めすべてコピー
REM /E: 空ディレクトリ含む /COPY:DAT: データ・属性・時刻 /R:0 /W:0: リトライ無し
robocopy "%SRC%" "%DEST%" /E /COPY:DAT /R:0 /W:0 /NFL /NDL /NP /NJH /NJS >nul
set "RC=%ERRORLEVEL%"

REM robocopy の戻り値 0〜7 は成功とみなす
if %RC% lss 8 (
    echo [DONE] コピーが完了しました。
    exit /b 0
) else (
    echo [ERROR] コピーに失敗しました。ERRORLEVEL=%RC%
    exit /b %RC%
)
