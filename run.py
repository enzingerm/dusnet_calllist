import asyncio
from datetime import date, datetime, timedelta
from itertools import groupby
import json
import uvloop

from sanic import Sanic, response
from jinja2 import Environment, PackageLoader


import aiohttp
from .call_list import get_calls, login
from .config import UPDATE_INTERVAL_SECONDS
from .filters import filter_day, filter_time

env = Environment(loader=PackageLoader('dusnet_calllist', 'templates'))
env.filters['day'] = filter_day
env.filters['time'] = filter_time

app = Sanic('dusnet_calllist', strict_slashes=True)
call_list = []
last_updated = datetime.now()
session = None
session_created_at = None


def group_calls(calls):
    grouped = [ (k, [*g]) for k, g in groupby(calls, key=lambda x: x.date.date()) ]
    return sorted(grouped, reverse=True, key=lambda x: x[0])

def add_names(call_list):
    try:
        with open("phonebook.json", "r") as f:
            book = json.loads(f.read())
        for date, calls in call_list:
            for call in calls:
                if call.number in book:
                    call.name = book[call.number]
                else:
                    call.name = None
    except IOError as e:
        pass

    return call_list

def get_query_string(request):
    return f"?{request.query_string}" if len(request.query_string) > 0 else ""


@app.route("/calls", methods=["POST", "GET"])
async def calls(request):
    global session, last_updated, call_list
    if request.method == "POST":
        print("Is POST")
        call_list = group_calls(await get_calls(session))
        last_updated = datetime.now()
    data = {
        "last_updated": last_updated.strftime('%H:%M'),
        "calls": add_names(call_list),
        "disable_reload": "disable_reload" in request.args,
        "query_string": get_query_string(request)
    }
    template = env.get_template('call_list.jinja2')
    return response.html(template.render(**data))


@app.route("/set_name", methods=["POST"])
async def set_name(request):
    name = request.form.get("name")
    number = request.form.get("number")
    try:
        with open("phonebook.json", "r") as f:
            phonebook = json.loads(f.read())
            phonebook[number] = name
    except IOError:
        phonebook = {number: name}
    with open("phonebook.json", "w+") as f:
        f.write(json.dumps(phonebook))

    return response.redirect("/calls" + get_query_string(request))



async def update_calls():
    global call_list, last_updated, session, session_created_at
    while True:
        try:
            if (session_created_at or datetime.min) + timedelta(days=1) < datetime.now():
                session = aiohttp.ClientSession()
                await login(session)
                session_created_at = datetime.now()
            print("Updating calls...")
            call_list = group_calls(await get_calls(session))
            print("Updated calls!")
            last_updated = datetime.now()
            await asyncio.sleep(UPDATE_INTERVAL_SECONDS)
        except Exception as e:
            print(e)


async def main():
    server = await app.create_server(
        host='127.0.0.1',
        port=8000,
        return_asyncio_server=True
    )
    await server.startup()
    asyncio.create_task(update_calls())
    await server.serve_forever()


if __name__ == '__main__':
    asyncio.set_event_loop(uvloop.new_event_loop())
    asyncio.run(main())
