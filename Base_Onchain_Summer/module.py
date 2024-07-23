import random
import time
import requests
import json
from loguru import logger
from requests import Session
from pyuseragents import random as random_ua
from eth_account.messages import encode_defunct

from help import Account, retry, sign_and_send_transaction, SUCCESS, FAILED, check_gas, get_tx_data, sleeping_between_transactions, get_token_price
from settings import  use_only_list_invite_code, donate_amount


class Onchain_Summer(Account):
    def __init__(self, id, private_key, proxy, rpc):
        super().__init__(id=id, private_key=private_key, proxy=proxy, rpc=rpc)
        self.session = Session()
        self.session.headers['user-agent'] = random_ua()
        self.proxy = proxy
        self.send_list = ''
        if self.proxy != None:
            self.session.proxies.update({'http': f"http://{self.proxy}"})

    @retry
    def login(self):
        self.session.headers.update({
            'authority': 'basehunt.xyz',
            'accept': '*/*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'origin': 'https://wallet.coinbase.com',
            'referer': 'https://wallet.coinbase.com/',
            'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
        })
        json_data = {
            'gameId': 2,
            'userAddress': self.address,
            'referralId': '',
        }

        response = self.session.post('https://basehunt.xyz/api/profile/opt-in', headers=self.session.headers,
                                     json=json_data).json()
        if response['success']:
            logger.success(f'Успешно залогинился...')

    @retry
    def get_statistics(self):
        params = {
            'userAddress': self.address,
            'gameId': '2',
        }
        response = self.session.get('https://basehunt.xyz/api/profile/state', params=params,
                                    headers=self.session.headers).json()

        referralCode = response['referralData']['referralCode']
        numReferrals = response['referralData']['numReferrals']
        currentScore = response['scoreData']['currentScore']
        numChallengesCompleted = response['numChallengesCompleted']
        badges = ''
        badges_list = response['badges']
        if len(badges_list) > 0:
            for badge in badges_list:
                badges += f'{badge["name"]}, '
        response = self.session.get('https://basehunt.xyz/api/leaderboard/rank', params=params, headers=self.session.headers).json()
        rank = response['rank']

        logger.info(f'\nСтатистика по аккаунту:\nrank: {rank} \nreferralCode: {referralCode} \nnumReferrals: {numReferrals} \ncurrentScore: {currentScore} \nnumChallengesCompleted: {numChallengesCompleted} \nbadges: {badges}')

    # @retry
    def complete_quest(self, challengeId, name):
        json_data = {
            'gameId': 2,
            'userAddress': self.address,
            'challengeId': challengeId,
        }

        response = self.session.post('https://basehunt.xyz/api/challenges/complete', headers=self.session.headers,
                                     json=json_data).json()
        if response['success']:
            logger.success(f'Quest {name}: Успешно завершил задание')
            self.send_list += (f'\n{SUCCESS}Quest {name}: Успешно завершил задание')

    @retry
    def speen_the_weel(self):
        self.send_list = ''
        json_data = {
            'gameId': '2',
            'userAddress': self.address,
        }
        response = requests.get('https://basehunt.xyz/api/spin-the-wheel', params=json_data, headers=self.session.headers).json()
        if response['spinData']['hasAvailableSpin']:
            response = self.session.post('https://basehunt.xyz/api/spin-the-wheel/execute', headers=self.session.headers, json=json_data).json()
            logger.success(f'Выпало {response["spinData"]["lastSpinResult"]["points"]} поинтов...')
            self.send_list += (f'\n{SUCCESS}Speen the weel: Выпало {response["spinData"]["lastSpinResult"]["points"]} поинтов...')
        else:
            logger.info(f'Нет доступных спинов, ждем до завтра...')
            self.send_list += (f'\n{SUCCESS}Нет доступных спинов, ждем до завтра...')
        return self.send_list

    # @retry
    def check_quest(self, challengeId, name):
        json_data = {
            'gameId': 2,
            'userAddress': self.address,
            'challengeId': challengeId,
        }

        response = self.session.post('https://basehunt.xyz/api/challenges/complete', headers=self.session.headers,
                                     json=json_data).json()
        if response['success']:
            logger.success(f'Quest {name}: Выполнено')
            self.send_list += (f'\n{SUCCESS}Quest {name}: Выполнено')
            return False

        else:
            return True

    # @retry
    def send_tx(self, name, to, data, value):
        value = int(self.w3.to_wei(value, 'ether')) if type(value) == float else value
        tx_data = get_tx_data(self, data=data, to=to, value=value)

        logger.info(f'Quest {name}: send txs...')
        # gas = random.randit(100000, 120000)

        txstatus, tx_hash = sign_and_send_transaction(self, tx_data)

        if txstatus == 1:
            logger.success(f'Quest {name}: send txs: {self.scan + tx_hash}')
            self.send_list += (f'\n{SUCCESS}Quest {name}: send txs - [tx hash]({self.scan + tx_hash})')

        else:
            logger.error(f'Quest {name}: send txs: {self.scan + tx_hash}')
            self.send_list += (f'\n{FAILED}Quest {name}: send txs - [tx hash]({self.scan + tx_hash})')

    # @retry
    def get_tx_data(self, address_nft, tokenId=None):
        json_data = {
            'bypassSimulation': True,
            'mintAddress': address_nft,
            'network': 'networks/base-mainnet',
            'quantity': '1',
            'takerAddress': self.address,
            # 'tokenId': '0',
        }
        if tokenId is not None:
            json_data['tokenId'] = tokenId

        response = self.session.post('https://api.wallet.coinbase.com/rpc/v3/creators/mintToken', headers=self.session.headers, json=json_data).json()
        to = response['callData']['to']
        value = int(response['callData']['value'], 16)
        data = response['callData']['data']
        return to, value, data

    @retry
    def registration(self):
        with open('invites.txt', 'r') as file:
            invites = [row.strip().lower() for row in file]
        random_code = random.choice(invites)
        self.session.headers.update({
            'authority': 'basehunt.xyz',
            'accept': '*/*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'origin': 'https://wallet.coinbase.com',
            'referer': 'https://wallet.coinbase.com/',
            'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
        })

        data = ('{"metrics":[{'
                '"metric_name":"perf_web_vitals_tbt_poor",'
                f'"page_path":"/ocs?referral_id={random_code}",'
                '"value":1,'
                '"tags":{"authed":"false","platform":"web","is_low_end_device":true,"is_low_end_experience":true,"page_key":"ocs","save_data":false,"service_worker":"supported","is_perf_metric":true,"locale":"ru-RU","project_name":"wallet_dapp","version_name":null},"type":"count"}'
                ']}')

        response = self.session.post('https://as.coinbase.com/metrics', headers=self.session.headers, data=data)

        json_data = {
            'gameId': 2,
            'userAddress': self.address,
            'referralId': random_code,
        }

        response = self.session.post('https://basehunt.xyz/api/profile/opt-in', headers=self.session.headers,
                                     json=json_data).json()
        if response['success']:
            logger.success(f'Успешно зарегистрировал аккаунт по рефке {random_code}')
            params = {
                'userAddress': self.address,
                'gameId': '2',
            }
            response = self.session.get('https://basehunt.xyz/api/profile/state', params=params,
                                        headers=self.session.headers).json()

            referralCode = response['referralData']['referralCode']
            numReferrals = response['referralData']['numReferrals']
            currentScore = response['scoreData']['currentScore']
            numChallengesCompleted = response['numChallengesCompleted']
            badges = ''
            badges_list = response['badges']
            if len(badges_list) > 0:
                for badge in badges_list:
                    badges += f'{badge["name"]}, '
            response = self.session.get('https://basehunt.xyz/api/leaderboard/rank', params=params,
                                        headers=self.session.headers).json()
            rank = response['rank']

            logger.info(
                f'rank: {rank} | referralCode: {referralCode} | numReferrals: {numReferrals} | currentScore: {currentScore} | numChallengesCompleted: {numChallengesCompleted} | badges: {badges}')

            if referralCode not in invites and not use_only_list_invite_code:
                with open('invites.txt', 'a') as file:
                    file.write(f"\n{referralCode}")
                    logger.info(f'Записал инвайт код в файл')

    @retry
    def claim_badge(self):
        self.send_list = ''
        badges = {
            1: 'Stand With Crypto',
            2: 'Coinbase One',
            3: 'Builder',
            4: 'Collector',
            5: 'Trader',
            6: 'Saver',
            7: '10 transactions',
            8: '50 transactions',
            9: '100 transactions',
            10: '1000 transactions',
        }
        for badge in badges:

            json_data = {
                'gameId': 2,
                'userAddress': self.address,
                'badgeId': badge,
            }

            response = self.session.post('https://basehunt.xyz/api/badges/claim', headers=self.session.headers,
                                         json=json_data).json()
            if response['success']:
                logger.success(f'Успешно склеймил "{badges[badge]}" badge')
                self.send_list += (f'\n{SUCCESS}Claim badge: Успешно склеймил "{badges[badge]}" badge')
                return self.send_list
    @retry
    def Mister_Miggles(self):
        self.send_list = ''
        if Onchain_Summer.check_quest(self, challengeId='ocsChallenge_d0778cee-ad0b-46b9-93d9-887b917b2a1f', name='Mister Miggles'):
            to, value, data = Onchain_Summer.get_tx_data(self, address_nft='0xDc03a75F96f38615B3eB55F0F289d36E7A706660')
            Onchain_Summer.send_tx(self,  name='Mister Miggles', to=to, data=data, value=value)
            time.sleep(3)
            Onchain_Summer.complete_quest(self, challengeId='ocsChallenge_d0778cee-ad0b-46b9-93d9-887b917b2a1f', name='Mister Miggles')
        return self.send_list

    @retry
    def Mister_Miggles_Song_A_Day(self):
        self.send_list = ''
        if Onchain_Summer.check_quest(self, challengeId='3Sx0O0fvmEre08aGa0ZsnR', name='Mister Miggles Song A Day'):
            to, value, data = Onchain_Summer.get_tx_data(self, address_nft='0x1f52841279fA4dE8B606a70373E9c84e84Ce9204')
            Onchain_Summer.send_tx(self,  name='Mister Miggles Song A Day', to=to, data=data, value=value)
            time.sleep(3)
            Onchain_Summer.complete_quest(self, challengeId='3Sx0O0fvmEre08aGa0ZsnR', name='Mister Miggles Song A Day')
        return self.send_list

    @retry
    def Introducing_Coinbase_Wallet_web_app(self):
        self.send_list = ''
        if Onchain_Summer.check_quest(self, challengeId='78zcHkWSABcPWMoacVI9Vs', name='Introducing Coinbase Wallet web app'):
            to, value, data = Onchain_Summer.get_tx_data(self, address_nft='0x6B033e8199ce2E924813568B716378aA440F4C67')
            Onchain_Summer.send_tx(self,  name='Introducing Coinbase Wallet web app', to=to, data=data, value=value)
            time.sleep(3)
            Onchain_Summer.complete_quest(self, challengeId='78zcHkWSABcPWMoacVI9Vs', name='Introducing Coinbase Wallet web app')
        return self.send_list

    @retry
    def Seasonal_Erosion_Relic_in_Winter(self):
        self.send_list = ''
        if Onchain_Summer.check_quest(self, challengeId='6fLQHp51Xb4t94cWVkD96R', name='Seasonal Erosion by Daniel Arsham'):
            Onchain_Summer.send_tx(self,  name='Seasonal Erosion by Daniel Arsham', to='0x2aa80a13395425EF3897c9684a0249a5226eA779', data='0xa0712d680000000000000000000000000000000000000000000000000000000000000002', value=0)
            time.sleep(3)
            Onchain_Summer.complete_quest(self, challengeId='6fLQHp51Xb4t94cWVkD96R', name='Seasonal Erosion by Daniel Arsham')
        return self.send_list

    @retry
    def Team_Liquid_OSPSeries(self):
        self.send_list = ''
        if Onchain_Summer.check_quest(self, challengeId='6VRBNN6qr2algysZeorek8', name='Team Liquid OSPSeries'):
            to, value, data = Onchain_Summer.get_tx_data(self, address_nft='0x1b9ac8580d2e81d7322f163362831448e7fcad1b')
            Onchain_Summer.send_tx(self,  name='Team Liquid OSPSeries', to=to, data=data, value=value)
            time.sleep(3)
            Onchain_Summer.complete_quest(self, challengeId='6VRBNN6qr2algysZeorek8', name='Team Liquid OSPSeries')
        return self.send_list

    @retry
    def Onchain_Summer_Buildathon(self):
        self.send_list = ''
        to, value, data = Onchain_Summer.get_tx_data(self, address_nft='0x0c45CA58cfA181b038E06dd65EAbBD1a68d3CcF3')
        Onchain_Summer.send_tx(self,  name='Onchain Summer Buildathon', to=to, data=data, value=value)
        return self.send_list

    # def donate(self):
    #     donate_usd = round(random.uniform(donate_amount[0], donate_amount[1]), 2)
    #     donate_session = Session()
    #     donate_session.headers['user-agent'] = random_ua()
    #     donate_session.headers.update({
    #         'authority': 'c.thirdweb.com',
    #         'accept': '*/*',
    #         'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    #         'content-type': 'application/json',
    #         'origin': 'https://www.standwithcrypto.org',
    #         'referer': 'https://www.standwithcrypto.org/',
    #         'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
    #         'sec-ch-ua-mobile': '?0',
    #         'sec-ch-ua-platform': '"Windows"',
    #         'sec-fetch-dest': 'empty',
    #         'sec-fetch-mode': 'cors',
    #         'sec-fetch-site': 'cross-site',
    #         'x-bundle-id': '',
    #         'x-client-id': 'd8044ba7cb9630c86f4891fa70c8318b',
    #         'x-sdk-name': '@thirdweb-dev/react',
    #         'x-sdk-os': 'Windows 10',
    #         'x-sdk-platform': 'browser',
    #         'x-sdk-version': '4.4.17',
    #     })
    #     json_data = {
    #         'source': 'connectWallet',
    #         'action': 'connect',
    #         'walletAddress': self.address,
    #         'walletType': 'metamask',
    #     }
    #
    #     response = donate_session.post('https://c.thirdweb.com/event', headers=donate_session.headers, json=json_data).json()
    #     if response['message'] == 'OK':
    #
    #         json_data = {
    #             'address': '0xa1d3aCd1dDEE12B7e834750fB8E28DF02b48029F',
    #             'chainId': '1',
    #         }
    #
    #         response = donate_session.post('https://www.standwithcrypto.org/api/auth/payload', json=json_data, headers=donate_session.headers, cookies=donate_session.cookies).json()
    #         msg = f"https://www.standwithcrypto.org wants you to sign in with your Ethereum account:\n{self.address}\n\nPlease ensure that the domain above matches the URL of the current website.\n\nVersion: 1\nChain ID: 1\nNonce: {response['payload']['nonce']}\nIssued At: {response['payload']['issued_at']}\nExpiration Time: {response['payload']['expiration_time']}\nNot Before: {response['payload']['invalid_before']}"
    #         message = encode_defunct(text=msg)
    #         text_signature = self.w3.eth.account.sign_message(message, private_key=self.private_key)
    #         signature_value = text_signature.signature.hex()
    #
    #         json_data = {
    #             'payload': {
    #                 'payload': {
    #                     'type': 'evm',
    #                     'domain': 'https://www.standwithcrypto.org',
    #                     'address': self.address,
    #                     'statement': 'Please ensure that the domain above matches the URL of the current website.',
    #                     'version': '1',
    #                     'chain_id': '1',
    #                     'nonce': response['payload']['nonce'],
    #                     'issued_at': response['payload']['issued_at'],
    #                     'expiration_time': response['payload']['expiration_time'],
    #                     'invalid_before': response['payload']['invalid_before'],
    #                 },
    #                 'signature': signature_value,
    #             },
    #         }
    #         response = donate_session.post('https://www.standwithcrypto.org/api/auth/login', json=json_data, headers=donate_session.headers, cookies=donate_session.cookies).json()
    #
    #         response = donate_session.get('https://www.standwithcrypto.org/api/auth/user').json()
    #         userId = response['session']['userId']
    #         json_data = {
    #             'amount': donate_usd,
    #         }
    #         data = '[]'
    #         donate_session.headers = {
    #             'authority': 'www.standwithcrypto.org',
    #             'accept': 'text/x-component',
    #             'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    #             'content-type': 'text/plain;charset=UTF-8',
    #             'origin': 'https://www.standwithcrypto.org',
    #             'referer': 'https://www.standwithcrypto.org/donate',
    #             'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
    #             'sec-ch-ua-mobile': '?0',
    #             'sec-ch-ua-platform': '"Windows"',
    #             'sec-fetch-dest': 'empty',
    #             'sec-fetch-mode': 'cors',
    #             'sec-fetch-site': 'same-origin',
    #         }
    #         response = donate_session.post('https://www.standwithcrypto.org/donate', data=data, headers=donate_session.headers, cookies=donate_session.cookies)
    #
    #         print(response)
    #         response = donate_session.put('https://api.commerce.coinbase.com/charges/eb454d0d-7e1a-4ed2-89d8-627a7d18fbd1/set_amount', json=json_data, headers=donate_session.headers, cookies=donate_session.cookies)
    #
    #         json_data = {
    #             'chain_id': 8453,
    #             'sender': self.address,
    #             'device_id': userId,
    #         }
    #
    #         response = donate_session.put('https://api.commerce.coinbase.com/charges/e0e7fa3a-7947-43cf-92cd-c2c667f190c1/hydrate', json=json_data, headers=donate_session.headers, cookies=donate_session.cookies).json()
    #         # print(json.dumps(response, indent=4))
    #
    #         signature = response['data']['web3_data']['transfer_intent']['call_data']['signature']
    #         recipient_amount = int(response['data']['web3_data']['transfer_intent']['call_data']['recipient_amount'])
    #         fee_amount = int(response['data']['web3_data']['transfer_intent']['call_data']['fee_amount'])
    #         id = response['data']['web3_data']['transfer_intent']['call_data']['id']
    #         deadline = int(time.time() + 100000)
    #
    #         data = (f'0x8bf122da'
    #                 f'0000000000000000000000000000000000000000000000000000000000000040'
    #                 f'00000000000000000000000000000000000000000000000000000000000001f4'
    #                 f'{hex(recipient_amount)[2:].lower().zfill(64)}' # recipient_amount
    #                 f'{hex(deadline)[2:].lower().zfill(64)}' # deadline
    #                 f'000000000000000000000000a4fa26f58fa636e669283cfeee4ae97a48011a5a'
    #                 f'000000000000000000000000833589fcd6edb6e08f4c7c32d4f71b54bda02913'
    #                 f'{self.address[2:].lower().zfill(64)}' # address
    #                 f'{hex(fee_amount)[2:].lower().zfill(64)}' # fee_amount
    #                 f'{id[2:].lower().ljust(64, "0")}' # id
    #                 f'0000000000000000000000008fccc78dae0a8f93b0fe6799de888d4c57e273db'
    #                 f'0000000000000000000000000000000000000000000000000000000000000140'
    #                 f'00000000000000000000000000000000000000000000000000000000000001c0'
    #                 f'0000000000000000000000000000000000000000000000000000000000000041'
    #                 f'{signature[2:].lower()}'
    #                 f'00000000000000000000000000000000000000000000000000000000000000'
    #                 f'000000000000000000000000000000000000000000000000000000000000001d'
    #                 f'4b3220496e666f726d6174696f6e616c204d6573736167653a20333220000000')
    #
    #         price = get_token_price('ETH', 'USDT')
    #         value_eth = donate_usd / price
    #         print(donate_usd, f'{"{:0.18f}".format(value_eth)}')
    #         Onchain_Summer.send_tx(self,  name='Stand With Crypto', to='0xef0d482daa16fa86776bc582aff3dfce8d9b8396', data=data, value=value_eth)

    # @retry
    # def Olympic_Games_Paris(self):
        # if Onchain_Summer.check_quest(self, challengeId='3nt43Lay6b18Fxqlz2nXS1', name='Olympic_Games_Paris'):
        #     headers = {
        #         'authority': 'erc721m-cosign-server.magiceden.io',
        #         'accept': 'application/json',
        #         'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        #         'content-type': 'application/json',
        #         'origin': 'https://magiceden.io',
        #         'referer': 'https://magiceden.io/',
        #         'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
        #         'sec-ch-ua-mobile': '?0',
        #         'sec-ch-ua-platform': '"Windows"',
        #         'sec-fetch-dest': 'empty',
        #         'sec-fetch-mode': 'cors',
        #         'sec-fetch-site': 'same-site',
        #         'user-agent': random_ua(),
        #         'x-bypass-bot-key': '',
        #     }
        #     json_data = {
        #         'metricsName': 'magiceden.sol.launchpad.openedition',
        #         'type': 'timing',
        #         'val': 3682,
        #     }
        #     response = requests.post('https://api-mainnet.magiceden.io/metrics/submit', headers=headers, json=json_data)
        #     print(response)
        #     json_data = {
        #         'collectionContract': '0xEEadefc9Df7ed4995cb93f5b5D9b923a7Dff8599',
        #         'minter': self.address,
        #         'qty': 1,
        #         'chainId': 8453,
        #         'nonce': 0,
        #     }
        #     response = requests.post('https://erc721m-cosign-server.magiceden.io/cosign', json=json_data, headers=headers)
        #     print(response)
            # deadline = int(time.time() + 10000)
            # data = (f'0xefb6b11f'
            #         f'0000000000000000000000000000000000000000000000000000000000000001'
            #         f'0000000000000000000000000000000000000000000000000000000000000080'
            #         f'{hex(deadline)[2:].zfill(64)}'
            #         f'00000000000000000000000000000000000000000000000000000000000000a0'
            #         f'0000000000000000000000000000000000000000000000000000000000000000'
            #         f'0000000000000000000000000000000000000000000000000000000000000041'
            #         f'{response["sig"][2:]}'
            #         f'1c00000000000000000000000000000000000000000000000000000000000000')
            #
            # Onchain_Summer.send_tx(self,  name='Olympic_Games_Paris', to='0xeeadefc9df7ed4995cb93f5b5d9b923a7dff8599', data=data, value=0)
            # time.sleep(3)
            # Onchain_Summer.complete_quest(self, challengeId='3nt43Lay6b18Fxqlz2nXS1', name='Olympic_Games_Paris')
            # return send_list
