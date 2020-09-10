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
session = None


@app.route("/calls", methods=["POST", "GET"])
@jinja.template("call_list.jinja2")
async def calls(request):
    global session, last_updated, call_list
    if request.method == "POST":
        print("Is POST")
        call_list = await get_calls(session)
        last_updated = datetime.now()
    return {
        "last_updated": last_updated.strftime('%H:%M'),
        "calls": call_list,
        "disable_reload": "disable_reload" in request.args
    }


async def update_calls():
    global call_list, last_updated, session
    session = aiohttp.ClientSession()
    await login(session)
    while True:
        print("Updating calls...")
        call_list = await get_calls(session)
        print("updated calls!")
        last_updated = datetime.now()
        await asyncio.sleep(600)


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
