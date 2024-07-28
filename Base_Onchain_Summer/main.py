import random
import datetime
import time
from loguru import logger
import pandas as pd

from help import Account, send_message, sleeping_between_wallets, intro, outro
from settings import bot_status, shuffle, bot_id, bot_token, rotes_modules
from module import Onchain_Summer

day_now = int(datetime.datetime.now(datetime.timezone.utc).strftime("%d"))

def main():
    with open('accounts_data.xlsx', 'rb') as file: # login:password@ip:port в файл proxy.txt
        exel = pd.read_excel(file)

    data = []
    for index, row in exel.iterrows():
        proxy = (row["Proxy"] if isinstance(row["Proxy"], str) else None)
        data.append((row["Private Key"], proxy, int(index)+1))

    send_list = []
    intro(len(data))
    count_wallets = len(data)

    def start():
        global day_now
        if shuffle:
            random.shuffle(data)
        for idx, (private_key, proxy, id) in enumerate(data, start=1):
            try:
                account = Account(id, private_key, proxy, "Base")
                logger.info(f'{idx}/{count_wallets} | {id} - {account.address} | {proxy if proxy is not None else "Прокси отсутствуют"}')
                send_list.append(f'{idx}/{count_wallets} : [{account.address}]({"https://debank.com/profile/" + account.address})')
                work = Onchain_Summer(id=account.id, private_key=account.private_key, proxy=account.proxy, rpc="Base")
                if rotes_modules[0][0] != 'registration':
                    send_list.append(work.login())
                for function_name in rotes_modules:
                    if len(function_name) > 1:
                        random.shuffle(function_name)
                        for function_in_list in function_name:
                            function = getattr(work, function_in_list[0])
                            send_list.append(function())
                    else:
                        function = getattr(work, function_name[0])
                        send_list.append(function())

            except Exception as e:
                logger.error(f'{idx}/{count_wallets} Failed: {str(e)}')
                sleeping_between_wallets()

            if bot_status == True:
                if account.id == count_wallets:
                    send_list.append(f'\nSubscribe: https://t.me/CryptoMindYep')
                send_message(bot_token, bot_id, send_list)
                send_list.clear()

            if idx != count_wallets:
                sleeping_between_wallets()
                print()
        if 'speen_the_weel' == rotes_modules[0][0]:
            print()
            time.sleep(0.3)
            logger.info(f'Waiting next day...')
            time.sleep(0.3)
            print()
            while int(datetime.datetime.now(datetime.timezone.utc).strftime("%d")) == day_now and int(datetime.datetime.now(datetime.timezone.utc).strftime("%H")) < 10:
                time.sleep(1300)
            day_now = int(datetime.datetime.now(datetime.timezone.utc).strftime("%d"))
            start()

    start()

    outro()
main()
