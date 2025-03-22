import aiohttp
import asyncio
import platform
import sys
from datetime import datetime, timedelta


class HttpError(Exception):
    pass


async def request(url: str):
    """Request from aiohttp client"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result
                else:
                    raise HttpError(f"Error status: {resp.status} for {url}")
        except (aiohttp.ClientConnectorError, aiohttp.InvalidURL) as err:
            raise HttpError(f'Connection error: {url}', str(err))


async def get_exchange(number_days: int, curr_list: list):
    result = []
    responses = []
    for index_day in range(1,number_days+1):
        dt = datetime.now() - timedelta(days=index_day)
        day_str = dt.strftime("%d.%m.%Y")
        try:
            responses.append(request(f'https://api.privatbank.ua/p24api/exchange_rates?date={day_str}'))
        except HttpError as err:
            print(err)
            return None
    result_responses = await asyncio.gather(*responses)
    for response in result_responses:
        res_dict = []
        curr_item = {}
        for curr in curr_list:
            res_dict.append(res_for_currency(curr, response))
        curr_its = await asyncio.gather(*res_dict)
        for i in range(len(curr_list)):
            curr_item[curr_list[i]] = curr_its[i]
        date_dict = {response['date']: curr_item}
        result.append(date_dict)
    return await list_dict_to_str(result,"")


async def res_for_currency(currency, response):
    """Exchange rate for a given currency"""
    await asyncio.sleep(0)
    try:
        return list(filter(lambda x: x['currency'] == currency, response['exchangeRate']))[0]
    except IndexError:
        return f"Currency {currency} not found!"


async def list_dict_to_str(l:list, spaces: str) -> str:
    """Formatting for convenient display of dictionary lists"""
    res = "[\n"
    res_list = []
    for d in l:
        res_list.append(await dict_to_str(d, spaces + " "))
    res += ",\n".join(res_list)
    res += "\n]\n"
    return res


async def dict_to_str(d:dict, spaces: str) -> str:
    """Formatting for convenient display of dictionary"""
    res = " {\n"
    res_dict = []
    for key in d:
        if type(d[key]) == dict:
            res_dict.append(spaces + f" {key}:" + await dict_to_str(d[key],spaces+" "))
        else:
            await asyncio.sleep(0)
            res_dict.append(spaces + f" {key}: {d[key]}")
    res += ",\n".join(res_dict)
    res += "\n" + spaces + "}"
    return res


if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    if len(sys.argv)>1:
        number_last_days = int(sys.argv[1])
        if int(number_last_days) <= 10:
            currency_list = ['EUR', 'USD']
            if len(sys.argv)>2:
                currency_list.extend(sys.argv[2:])
            r = asyncio.run(get_exchange(number_last_days, currency_list))
            if r:
                print(r)
        else:
            print("You can find out the exchange rate for no more than the last 10 days")
    else:
        print("Enter the number of recent days for which you want to know the exchange rate")
