

# ===================================== options ===================================== #

#----main-options----#
shuffle = True                                                      # True / False. если нужно перемешать кошельки
delay_wallets = [1, 2]                                              # минимальная и максимальная задержка между кошельками
delay_transactions = [10, 15]                                       # минимальная и максимальная задержка между транзакциями
min_balance = 0.00001                                               # минимальный баланс для работы, для модулей без транз, указывайте больше нулей
RETRY_COUNT = 15                                                    # кол-во попыток при возникновении ошибок (советую +- 10)
use_only_list_invite_code = False                                   # при True, будет использовать рандомно только рефки из файла, при False будет добавлять рефки новых аккаунтов в файл

#------bot-options------#
bot_status = False                                                  # True / False
bot_token  = ''                                                     # telegram bot token
bot_id     = 0                                                      # telegram id

''' 
registration | первый логин с использованием рефки, запускать один раз
claim_badge | клейм доступных бейджей
get_statistics | получить статистику по аккаунту
speen_the_weel | ежедневные спины

Quests:
Mister_Miggles | 0.70$ | 1000 XP
Introducing_Coinbase_Wallet_web_app | 0.35$ | 250 XP
Onchain_Summer_Buildathon | 0.70$ | бейдж
Team_Liquid_OSPSeries | 0.35$ | 500 XP
Celebrating_the_Ethereum_ETF | 0.35$ | 250 XP
ETFEREUM | 0.35$ | 150XP
Ethereum_ETF | 0.35$ | 150XP
ETH_BREAKING_THROUGH | 0.35$ | 150XP
ETH_cant_be_stopped | 0.35$ | 150XP
Happy_Birthday_Toshi | 0.35$ | 250XP
EURC_Base_Launch | 0.35$ | 150XP
STIX_Launch_Tournament_Pass | 0$ | 1000XP
Live_and_let_live | 1.3$ | 5000XP

Forbes_Web3_INSPIRE | 0$ | 1000XP

Eсли указать модули (не меньше 2ух) в [], то они перемешаются. Пример ниже

'''
rotes_modules = [
    ['speen_the_weel'],
    [
        ['STIX_Launch_Tournament_Pass'],
        ['Ethereum_ETF'],
    ],
    ['get_statistics']
]
# =================================== end-options =================================== #


