from datetime import datetime, timedelta

from config import PASS, SECONDS_WITHIN_DUPLICATE_CALLS, USER
from lxml import html

LOGIN_URL = "https://my.dus.net/de/"
CALLER_LIST = "https://my.dus.net/de/kundenmenue/kundencenter/callerlist.html"
CUSTOMER_CENTER = "https://my.dus.net/de/kundenmenue/kundencenter/index.html"


class Call:
    def __init__(self, kind, date, number, duration=None):
        self.kind = kind
        self.date = date
        self.number = number
        self.duration = duration
        self.name = None

    @classmethod
    def create(cls, kind, date_string, number, duration=None):
        return cls(kind, datetime.strptime(date_string.strip(), "%d.%m.%Y %H:%M:%S"), number.strip(), duration)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return  self.kind == other.kind and \
                self.duration == other.duration and \
                self.number == other.number and \
                abs(self.date - other.date) < timedelta(seconds=SECONDS_WITHIN_DUPLICATE_CALLS)
        return False

    def __ne__(self, other):
        return not self.__eq__(other)


async def login(session):
    data = None
    async with session.get(LOGIN_URL) as response:
        parsed = html.fromstring((await response.text()).encode())
        data = {it.name: it.value for it in parsed.xpath(
            "//form[@id='login-form']//input[@type='hidden']")}
    data['username'] = USER
    data['password'] = PASS
    data['remember'] = "yes"
    async with session.post(LOGIN_URL, data=data) as response:
        pass
    session.cookie_jar.update_cookies(
        [('DUSNETCookiesConsent', '{"time":1599591086762,"list":[null,{"id":1,"name":"Funktionelle Cookies","type":"required","agree":1},{"id":2,"name":"Analytische Cookies","type":"optional","agree":1}]}')])
    # strangely, kundencenter must be loaded first
    async with session.get(CUSTOMER_CENTER) as response:
        pass


async def get_calls(session):
    calls = []
    async with session.get(CALLER_LIST) as response:
        parsed = html.fromstring((await response.text()).encode())
        for i in parsed.xpath("//div[text()='verpasste Anrufe']/following-sibling::table/tr[position()>1]"):
            datum, nummer = i.xpath("td/text()")
            calls.append(Call.create('eingehend', datum, nummer, None))
        for i in parsed.xpath("//div[text()='getätigte Anrufe']/following-sibling::table/tr[position()>1]"):
            datum, nummer, dauer = i.xpath("td/text()")
            calls.append(Call.create('ausgehend', datum, nummer, dauer))
        for i in parsed.xpath("//div[text()='angenommene Anrufe']/following-sibling::table/tr[position()>1]"):
            datum, nummer, dauer = i.xpath("td/text()")
            calls.append(Call.create('eingehend', datum, nummer, dauer))
    calls = sorted(calls, reverse=True, key=lambda x: x.date)
    # dus.net often shows the same call multiple times
    calls = [ first for first, second in zip(calls, calls[1:] + [ None ]) if first != second ]
    return calls
