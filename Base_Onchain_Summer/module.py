import time
import random
import requests
import pandas as pd
from uuid import uuid4
from loguru import logger
from requests import Session
from pyuseragents import random as random_ua

from settings import use_only_list_invite_code
from help import Account, retry, sign_and_send_transaction, SUCCESS, FAILED, get_tx_data, sleeping_between_transactions

class Onchain_Summer(Account):
    def __init__(self, id, private_key, proxy, rpc):
        super().__init__(id=id, private_key=private_key, proxy=proxy, rpc=rpc)
        self.session = Session()
        self.user_agent = random_ua()
        self.proxy = proxy
        self.send_list = ''
        if self.proxy != None:
            self.session.proxies.update({'http': f"http://{self.proxy}"})

    @retry
    def login(self):

        self.session.headers = {
            'authority': 'basehunt.xyz',
            'accept': '*/*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'origin': 'https://wallet.coinbase.com',
            'referer': 'https://wallet.coinbase.com/',
            'user-agent': self.user_agent,
            'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
        }

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
            for idx, badge in enumerate(badges_list, start=1):
                badges += f'{badge["name"]}, '
            badges = badges[0:-2]
        response = self.session.get('https://basehunt.xyz/api/leaderboard/rank', params=params, headers=self.session.headers).json()
        rank = response['rank']

        logger.info(f'\nСтатистика по аккаунту:\nrank: {rank} \nreferralCode: {referralCode} \nnumReferrals: {numReferrals} \ncurrentScore: {currentScore} \nnumChallengesCompleted: {numChallengesCompleted} \nbadges: {badges}')
        with open('accounts_data.xlsx', 'rb') as file:
            exel = pd.read_excel(file)
        exel = exel.astype({'Badges': 'str'})
        exel = exel.astype({'Referral-code': 'str'})
        exel.loc[(self.id - 1), 'Points'] = int(currentScore)
        exel.loc[(self.id - 1), 'Rank'] = int(rank)
        exel.loc[(self.id - 1), 'Completed'] = int(numChallengesCompleted)
        exel.loc[(self.id - 1), 'Badges'] = badges
        exel.loc[(self.id - 1), 'Referrals'] = int(numReferrals)
        exel.loc[(self.id - 1), 'Referral-code'] = referralCode
        exel.to_excel('accounts_data.xlsx', header=True, index=False)
        
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
            logger.success(f'Выпало {response["spinData"]["lastSpinResult"]["points"]} {response["spinData"]["lastSpinResult"]["type"]}...')
            self.send_list += (f'\n{SUCCESS}Speen the weel: Выпало {response["spinData"]["lastSpinResult"]["points"]} {response["spinData"]["lastSpinResult"]["type"]}...')
        else:
            logger.info(f'Нет доступных спинов, ждем до завтра...')
            self.send_list += (f'\n{SUCCESS}Нет доступных спинов, ждем до завтра...')
        return self.send_list
    
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
    def do_quest(self, challengeId, name, address_nft):
        self.send_list = ''
        if Onchain_Summer.check_quest(self, challengeId=challengeId, name=name):
            to, value, data = Onchain_Summer.get_tx_data(self, address_nft=address_nft)
            Onchain_Summer.send_tx(self, name=name, to=to, data=data, value=value)
            time.sleep(3)
            Onchain_Summer.complete_quest(self, challengeId=challengeId, name=name)

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
        else:
            Exception

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

    def send_tx(self, name, to, data, value):
        value = int(self.w3.to_wei(value, 'ether')) if type(value) == float else value
        tx_data = get_tx_data(self, data=data, to=to, value=value)

        logger.info(f'Quest {name}: send txs...')
        # gas = random.randit(100000, 120000)

        txstatus, tx_hash = sign_and_send_transaction(self, tx_data)

        if txstatus == 1:
            logger.success(f'Quest {name}: send txs: {self.scan + tx_hash}')
            self.send_list += (f'\n{SUCCESS}Quest {name}: send txs - [tx hash]({self.scan + tx_hash})')
            sleeping_between_transactions()

        else:
            logger.error(f'Quest {name}: send txs: {self.scan + tx_hash}')
            self.send_list += (f'\n{FAILED}Quest {name}: send txs - [tx hash]({self.scan + tx_hash})')

    def get_tx_data(self, address_nft, tokenId=None):
        headers = {
            'accept': 'application/json',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json',
            'origin': 'https://wallet.coinbase.com',
            'priority': 'u=1, i',
            'referer': 'https://wallet.coinbase.com/',
            'sec-ch-ua': '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'user-agent': random_ua(),
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'x-cb-device-id': str(uuid4()),
            'x-cb-is-logged-in': 'false',
            'x-cb-pagekey': 'unknown',
            'x-cb-platform': 'web',
            'x-cb-project-name': 'wallet_dapp',
            'x-cb-session-uuid': str(uuid4()),
            'x-cb-ujs': '',
            'x-cb-version-name': 'unknown',
        }
        json_data = {
            'bypassSimulation': True,
            'mintAddress': address_nft,
            'network': 'networks/base-mainnet',
            'quantity': '1',
            'takerAddress': self.address,
        }
        if tokenId is not None:
            json_data['tokenId'] = tokenId

        response = requests.post('https://api.wallet.coinbase.com/rpc/v3/creators/mintToken', headers=headers, json=json_data)
        if response.status_code != 200:
            raise TypeError('Wrong response for get tx data')

        response_json: dict = response.json()
        to = response_json['callData']['to']
        value = int(response_json['callData']['value'], 16)
        data = response_json['callData']['data']
        return to, value, data

    def STIX_Launch_Tournament_Pass(self):
        Onchain_Summer.do_quest(self, challengeId='ocsChallenge_bd5208b5-ff1e-4f5b-8522-c4d4ebb795b7', name='STIX Launch Tournament Pass', address_nft='0xa7891c87933BB99Db006b60D8Cb7cf68141B492f')
        return self.send_list

    def Happy_Birthday_Toshi(self):
        Onchain_Summer.do_quest(self, challengeId='1pjoNf5onjgsi7r9fWp3ob', name='Happy Birthday Toshi', address_nft='0xE65dFa5C8B531544b5Ae4960AE0345456D87A47D')
        return self.send_list

    def ETH_cant_be_stopped(self):
        Onchain_Summer.do_quest(self, challengeId='ocsChallenge_c1de2373-35ad-4f3c-ab18-4dfadf15754d', name='ETH cant be stopped', address_nft='0xb0FF351AD7b538452306d74fB7767EC019Fa10CF')
        return self.send_list

    def ETH_BREAKING_THROUGH(self):
        Onchain_Summer.do_quest(self, challengeId='78AUXYw8UCyFUPE2zy9yMZ', name='ETH BREAKING THROUGH', address_nft='0x96E82d88c07eCa6a29B2AD86623397B689380652')
        return self.send_list

    def EURC_Base_Launch(self):
        Onchain_Summer.do_quest(self, challengeId='1iZiHPbqaIGW5F08bCit6J', name='EURC Base Launch', address_nft='0x615194d9695d0c02Fc30a897F8dA92E17403D61B')
        return self.send_list

    def Ethereum_ETF(self):
        Onchain_Summer.do_quest(self, challengeId='ocsChallenge_ee0cf23e-74a1-4bb3-badf-037a6bbf35e8', name='Ethereum ETF', address_nft='0xC00F7096357f09d9f5FE335CFD15065326229F66')
        return self.send_list

    def ETFEREUM(self):
        Onchain_Summer.do_quest(self, challengeId='ocsChallenge_eba9e6f0-b7b6-4d18-8b99-a64aea045117', name='ETFEREUM', address_nft='0xE8aD8b2c5Ec79d4735026f95Ba7C10DCB0D3732B')
        return self.send_list

    def Celebrating_the_Ethereum_ETF(self):
        Onchain_Summer.do_quest(self, challengeId='5e383RWcRtGAwGUorkGiYC', name='Celebrating the Ethereum ETF', address_nft='0xb5408b7126142C61f509046868B1273F96191b6d')
        return self.send_list

    def Mister_Miggles(self):
        Onchain_Summer.do_quest(self, challengeId='ocsChallenge_d0778cee-ad0b-46b9-93d9-887b917b2a1f', name='Mister Miggles', address_nft='0xDc03a75F96f38615B3eB55F0F289d36E7A706660')
        return self.send_list

    def Introducing_Coinbase_Wallet_web_app(self):
        Onchain_Summer.do_quest(self, challengeId='78zcHkWSABcPWMoacVI9Vs', name='Introducing Coinbase Wallet web app', address_nft='0x6B033e8199ce2E924813568B716378aA440F4C67')
        return self.send_list

    def Team_Liquid_OSPSeries(self):
        Onchain_Summer.do_quest(self, challengeId='6VRBNN6qr2algysZeorek8', name='Team Liquid OSPSeries', address_nft='0x1b9ac8580d2e81d7322f163362831448e7fcad1b')
        return self.send_list

    @retry
    def Onchain_Summer_Buildathon(self):
        self.send_list = ''
        to, value, data = Onchain_Summer.get_tx_data(self, address_nft='0x0c45CA58cfA181b038E06dd65EAbBD1a68d3CcF3')
        Onchain_Summer.send_tx(self,  name='Onchain Summer Buildathon', to=to, data=data, value=value)
        return self.send_list
