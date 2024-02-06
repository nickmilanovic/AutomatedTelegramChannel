Python script used to automate a Telegram Trade Signal Channel on 6 different markets.
Asyncio library used for multithreading, 6 functions running concurrently, one for each market.

Example output:

SELL EURUSD @ 1.07496
TP1: 1.06991
TP2: 1.06697
TP3: 1.06403
SL: 1.08145

SELL LIMIT EURUSD @ 1.07940
TP1: 1.06991
TP2: 1.06697
TP3: 1.06403
SL: 1.08145

Each message will be a trade signal that is received from a strategy on a separate .py script. Due to privacy & legality reasons, the trading strategy is ommitted from GitHub, however AutomatedTelegramChannel.py
can be used as a skeleton for others wanting to automate their trading channels.
