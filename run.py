import asyncio
from datetime import datetime

import aiohttp

from call_list import get_calls, login
from sanic import Blueprint, Sanic, response
from sanic_jinja2 import SanicJinja2

app = Sanic(__name__)
jinja = SanicJinja2(app)
call_list = []
last_updated = datetime.now()


@app.route("/calls")
@jinja.template("call_list.jinja2")
async def calls(request):
    return {"last_updated": last_updated.strftime('%H:%M'), "calls": call_list}


async def update_calls():
    global call_list, last_updated
    async with aiohttp.ClientSession() as session:
        await login(session)
        while True:
            print("Updating calls...")
            call_list = await get_calls(session)
            print("updated calls!")
            last_updated = datetime.now()
            await asyncio.sleep(60)


def main():
    loop = asyncio.get_event_loop()
    server = app.create_server(
        host='127.0.0.1',
        port=8000,
        return_asyncio_server=True
    )
    loop.create_task(server)
    loop.create_task(update_calls())
    loop.run_forever()


if __name__ == '__main__':
    main()
