import asyncio
from datetime import date, datetime, timedelta
from itertools import groupby
import json

from sanic import Sanic, response
from sanic_jinja2 import SanicJinja2

import aiohttp
from call_list import get_calls, login
from config import UPDATE_INTERVAL_SECONDS
from filters import filter_day, filter_time

app = Sanic(__name__)
jinja = SanicJinja2(app)
jinja.add_env("day", filter_day, "filters")
jinja.add_env("time", filter_time, "filters")
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



@app.route("/calls", methods=["POST", "GET"])
@jinja.template("call_list.jinja2")
async def calls(request):
    global session, last_updated, call_list
    if request.method == "POST":
        print("Is POST")
        call_list = group_calls(await get_calls(session))
        last_updated = datetime.now()
    return {
        "last_updated": last_updated.strftime('%H:%M'),
        "calls": add_names(call_list),
        "disable_reload": "disable_reload" in request.args
    }

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

    return response.redirect("/calls")



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
