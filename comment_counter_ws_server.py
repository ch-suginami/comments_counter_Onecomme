"""Simple WebSocket broadcast server.

環境変数でホスト/ポートを変更できます:
  - WS_HOST (default: 127.0.0.2)
  - WS_PORT (default: 11181)
"""

import asyncio
import logging
import os
from typing import Set

from websockets.exceptions import ConnectionClosed
from websockets.server import WebSocketServerProtocol, serve


# 接続中のクライアントを保持
connected_clients: Set[WebSocketServerProtocol] = set()


async def handler(websocket: WebSocketServerProtocol) -> None:
    """各クライアント接続を処理し、受信メッセージを全員に配信。"""
    connected_clients.add(websocket)
    peer = getattr(websocket, "remote_address", None)
    logging.info("Client connected: %s", peer)
    try:
        async for message in websocket:
            # 受け取ったメッセージを全クライアントに配信
            if connected_clients:
                await _broadcast(message)
    except ConnectionClosed as e:
        logging.info("Connection closed: %s", e)
    except Exception:  # 予期しない例外もログに残す
        logging.exception("Unexpected error in handler")
    finally:
        # discard は存在しなくてもエラーにしない
        connected_clients.discard(websocket)
        logging.info("Client disconnected: %s", peer)


async def _broadcast(message: str) -> None:
    """全クライアントへメッセージを送信（クローズ済みは除外）。"""
    if not connected_clients:
        return
    # クローズ済みを先に掃除
    for ws in list(connected_clients):
        if ws.closed:
            connected_clients.discard(ws)

    if not connected_clients:
        return

    tasks = [ws.send(message) for ws in connected_clients]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    # 送信失敗の接続は取り除く
    for ws, res in zip(list(connected_clients), results):
        if isinstance(res, Exception):
            logging.debug("Dropping client due to send error: %s", res)
            connected_clients.discard(ws)

async def main() -> None:
    host = os.getenv("WS_HOST", "127.0.0.2")
    port = int(os.getenv("WS_PORT", "11181"))

    # ping 間隔/タイムアウト等を適度に設定
    async with serve(
        handler,
        host,
        port,
        ping_interval=20,
        ping_timeout=20,
        max_size=2**20,  # 1 MiB
    ):
        logging.info("WebSocket server listening on ws://%s:%s", host, port)
        # 永久待機
        await asyncio.Future()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    asyncio.run(main())
