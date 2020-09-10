from lxml import html

from config import PASS, USER

LOGIN_URL = "https://www.dus.net/de/"
CALLER_LIST = "https://www.dus.net/de/kundenmenue/kundencenter/callerlist.html"
CUSTOMER_CENTER = "https://www.dus.net/de/kundenmenue/kundencenter/index.html"


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
            calls.append(('eingehend', datum, nummer, None))
        for i in parsed.xpath("//div[text()='getätigte Anrufe']/following-sibling::table/tr[position()>1]"):
            datum, nummer, dauer = i.xpath("td/text()")
            calls.append(('ausgehend', datum, nummer, dauer))
        for i in parsed.xpath("//div[text()='angenommene Anrufe']/following-sibling::table/tr[position()>1]"):
            datum, nummer, dauer = i.xpath("td/text()")
            calls.append(('eingehend', datum, nummer, dauer))
    return sorted(calls, reverse=True, key=lambda x: x[1])
