"""OneComme コメントに連番を付与してブロードキャストするクライアント。"""

import asyncio
import datetime
import json
import os
import re
import sys
import traceback
from typing import Optional

import websockets
from websockets.client import WebSocketClientProtocol


file_time = datetime.datetime.now()
file_name = "log/" + file_time.strftime("%Y%m%d%H%M%S") + ".txt"

# 入力/出力の URI は環境変数で上書き可能
IN_URI = os.getenv("IN_URI", "ws://127.0.0.1:11180/sub")
OUT_URI = os.getenv("OUT_URI", "ws://127.0.0.2:11181/")

# すでにタグ済みかを厳密に判定（例: 【123コメ】）
TAGGED_RE = re.compile(r"【\d+コメ】$")


async def counter() -> None:
    send_ws: Optional[WebSocketClientProtocol] = None
    counter_val = 1

    # 受信側に接続
    async with websockets.connect(IN_URI, ping_interval=20, ping_timeout=20) as recv_ws:
        # 送信側は使い回す（失敗したら都度再接続）
        send_ws = await _ensure_send_ws(send_ws)

        while True:
            try:
                raw_data = await recv_ws.recv()
                data = json.loads(raw_data)

                if data.get("type") == "meta.clear":
                    _append_log("正常終了しました\n")
                    break

                if data.get("type") == "comments":
                    comments = data.get("data", {}).get("comments", [])
                    for i, c in enumerate(comments):
                        try:
                            comment: str = c["data"]["comment"]
                        except Exception:
                            # 期待外フォーマットはスキップ
                            continue

                        if TAGGED_RE.search(comment):
                            continue

                        tagged = f"{comment}【{counter_val}コメ】"

                        # 一時的に差し替えて送信、終わったら元に戻す
                        original = c["data"]["comment"]
                        c["data"]["comment"] = tagged
                        post_body = json.dumps(data, ensure_ascii=False)

                        # 送信（失敗時は一度だけ再接続してリトライ）
                        try:
                            send_ws = await _ensure_send_ws(send_ws)
                            await send_ws.send(post_body)
                        except Exception:
                            send_ws = None
                            _append_exception_to_log()
                            # 再接続して 1 回だけ再送
                            try:
                                send_ws = await _ensure_send_ws(send_ws)
                                await send_ws.send(post_body)
                            except Exception:
                                _append_exception_to_log()
                                # 送信できなければ諦めて次へ
                        finally:
                            # 状態を元に戻す（累積書き換えを避ける）
                            c["data"]["comment"] = original

                        counter_val += 1

                    _append_log(json.dumps({"sent": len(comments), "counter": counter_val - 1}, ensure_ascii=False) + "\n")

            except websockets.ConnectionClosed:
                _append_log("受信側接続が切断されました\n")
                break
            except Exception:
                _append_exception_to_log()
                break

    # 後処理
    if send_ws and not send_ws.closed:
        await send_ws.close()


async def _ensure_send_ws(ws: Optional[WebSocketClientProtocol]) -> WebSocketClientProtocol:
    """送信側 WS を確立して返す（既に有効ならそのまま）。"""
    if ws and not ws.closed:
        return ws
    return await websockets.connect(OUT_URI, ping_interval=20, ping_timeout=20)


def _append_log(text: str) -> None:
    try:
        with open(file_name, "a", encoding="utf-8") as f:
            f.write(text)
    except Exception:
        # ログに失敗しても処理は続ける
        pass


def _append_exception_to_log() -> None:
    try:
        with open(file_name, "a", encoding="utf-8") as f:
            traceback.print_exc(file=f)
    except Exception:
        pass


if __name__ == '__main__':
    # ログディレクトリを確実に作成
    if not os.path.isdir("log"):
        os.makedirs("log", exist_ok=True)
    asyncio.run(counter())
