

# ===================================== options ===================================== #

#----main-options----#
shuffle = True                                                      # True / False. если нужно перемешать кошельки
module = 1                                                          # 1 - первый логин с использованием рефки, 2 - клейм доступных бейджей
delay_wallets = [1, 2]                                              # минимальная и максимальная задержка между кошельками
RETRY_COUNT = 3                                                     # кол-во попыток при возникновении ошибок
use_only_list_invite_code = False                                   # при True, будет использовать рандомно только рефки из файла, при False будет добавлять рефки новых аккаунтов в файл
donate_amount = [0.1, 0.3]                                          # мин и макс USDT для доната

#------bot-options------#
bot_status = False                                                  # True / False
bot_token  = ''                                                     # telegram bot token
bot_id     = 0                                                      # telegram id

''' 
registration | первый логин с использованием рефки, запускать один раз
claim_badge | клейм доступных бейджей
get_statistics | получить статистику по аккаунту
speen_the_weel | ежедневные спины
donate | донат для получения бейджа | не работает

Quests:
Mister_Miggles | 0.70$ | 1000 XP
Mister_Miggles_Song_A_Day | 0.35$ | 250 XP
Introducing_Coinbase_Wallet_web_app | 0.35$ | 250 XP
Seasonal_Erosion_Relic_in_Winter | 0$ | 250 XP
Onchain_Summer_Buildathon | 0.70$ | бейдж
Team_Liquid_OSPSeries | 0.35$ | 500 XP
Celebrating_the_Ethereum_ETF | 0.35$ | 250 XP
ETFEREUM | 0.35$ | 150XP
Seasonal_Erosion_Relic_in_Spring | 0.00$ | 1000 XP

Olympic_Games_Paris | 0$ | 250 XP - не работает

Eсли указать модули (не меньше 2ух) в [], то они перемешаются. Пример ниже

'''
rotes_modules = [
    ['speen_the_weel'],
    [
        ['Onchain_Summer_Buildathon'],
        ['Team_Liquid_OSPSeries'],
    ],
    ['claim_badge']
]
# =================================== end-options =================================== #


