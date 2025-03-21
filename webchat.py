import asyncio
import logging
import aiohttp
import websockets
import names
from main import get_exchange
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK

logging.basicConfig(level=logging.INFO)


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            mes_parts = message.split(" ")
            if len(mes_parts) > 1:
                number_last_days = int(mes_parts[1])
                if int(number_last_days) <= 10:
                    currency_list = ['EUR', 'USD']
                    if len(mes_parts) > 2:
                        currency_list.extend(mes_parts[2:])
                    exchange = await get_exchange(number_last_days, currency_list)
                    await self.send_to_clients(exchange)
                else:
                    await self.send_to_clients(f"{ws.name}: {message}")
            else:
                await self.send_to_clients(f"{ws.name}: {message}")


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())
