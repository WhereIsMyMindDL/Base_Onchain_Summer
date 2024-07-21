import random
import time
import requests
from loguru import logger
from requests import Session
from pyuseragents import random as random_ua

from help import Account, retry, sign_and_send_transaction, SUCCESS, FAILED, check_gas, get_tx_data, sleeping_between_transactions
from settings import  use_only_list_invite_code


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

        logger.info(f'Quest {name}: mint nft...')
        # gas = random.randit(100000, 120000)

        txstatus, tx_hash = sign_and_send_transaction(self, tx_data)

        if txstatus == 1:
            logger.success(f'Quest {name}: mint nft: {self.scan + tx_hash}')
            self.send_list += (f'\n{SUCCESS}Quest {name}: mint nft - [tx hash]({self.scan + tx_hash})')

        else:
            logger.error(f'Quest {name}: mint nft: {self.scan + tx_hash}')
            self.send_list += (f'\n{FAILED}Quest {name}: mint nft - [tx hash]({self.scan + tx_hash})')

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
        Onchain_Summer.login(self)
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
                logger.info(f'Успешно склеймил "{badges[badge]}" badge')

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