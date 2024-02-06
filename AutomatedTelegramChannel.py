import asyncio
from telethon.sync import TelegramClient
import MetaTrader5 as mt5
import pandas_ta as ta
import pandas as pd
from dma_cross_function import *
import time
import datetime


async def send_message(client, channel_username, message):
    await client.send_message(channel_username, message)


async def USDJPY(client, channel_username):
    symbol = "USDJPY"
    fib_levels = await asyncio.to_thread(check_gib, symbol)

    print(datetime.datetime.now().strftime("%H:%M:%S"))

    previous_price = None  # Initialize previous_price
    buyTp1 = 0
    buyTp2 = 0
    buyTp3 = 0
    buySl = 0
    buySignal = ""
    buyLimitSignal = ""
    sellTp1 = 0
    sellTp2 = 0
    sellTp3 = 0
    sellSl = 0
    sellSignal = ""
    sellLimitSignal = ""
    signal = "LOOKING"
    openTrades = 0
    buytp1check = True
    buytp2check = True
    buytp3check = True
    selltp1check = True
    selltp2check = True
    selltp3check = True
    trigger = True

    while True:
        if signal == "LOOKING":
            signal = await asyncio.to_thread(check_ema_wma_cross, symbol)
            print(signal)
        if signal == "BUY":
            rates_one = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_M30, datetime.datetime.utcnow(), 1000)
            df_one = pd.DataFrame(rates_one)
            df_one.set_index("time", inplace=True)
            df_one.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "real_volume": "Volume"}, inplace=True)
            df_one.index = pd.to_datetime(df_one.index, unit="s")
            df_one.ta.ema(length=72, append=True)
            current_candle = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M30, 0, 1)[0]
            ema = df_one["EMA_" + str(72)].iloc[-1]
            #print("BUY")
            current_candle = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M30, 0, 1)[0]
            current_price = current_candle['close']
            list_length = len(fib_levels)
            min_diff = float('inf')  # Initialize the minimum difference
            for i, price in enumerate(fib_levels):
                diff = abs(current_price - price)
                if diff < min_diff:
                    min_diff = diff
                    index = i
            if index < list_length - 1:
                priceAsk = mt5.symbol_info_tick(symbol).ask
                #buySl = priceAsk - ((priceAsk - fib_levels[index - 1]) / 2)
                buySl = ema - (check_pip(symbol) * 20)
                buyTp = priceAsk + (priceAsk - fib_levels[index - 1])
                buyLimitSl = fib_levels[index - 1] - (check_pip(symbol) * 50)
                buyLimitEntry = fib_levels[index - 1] + (check_pip(symbol) * 20)
                buyTp1 = fib_levels[index + 1]
                buyTp2 = fib_levels[index + 2]
                buyTp3 = fib_levels[min(index + 3, list_length - 1)]
                buySignal = "BUY {0} @ {1}\nTP1: {2}\nTP2: {3}\nTP3: {4}\nSL: {5}".format(symbol, current_price, buyTp1, buyTp2, buyTp3, buyLimitSl)
                buyLimitSignal = "BUY LIMIT {0} @ {1}\nTP1: {2}\nTP2: {3}\nTP3: {4}\nSL: {5}".format(symbol, buyLimitEntry, buyTp1, buyTp2, buyTp3, buyLimitSl)
                print(buySignal)
                print(buyLimitSignal)
                await send_message(client, channel_username, buySignal)
                await send_message(client, channel_username, buyLimitSignal)
                print("BUY SIGNAL SENT")
                openTrades += 1
            while openTrades == 1:
                priceAsk = mt5.symbol_info_tick(symbol).ask
                if priceAsk < buyTp1 and trigger:
                    print("Awaiting TP1 for {0}".format(symbol))
                    trigger = False
                if priceAsk >= buyTp1 and buytp1check:
                    buytp1msg = "TP1 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, buytp1msg)
                    buytp1check = False
                if priceAsk >= buyTp2 and buytp2check:
                    buytp2msg = "TP2 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, buytp2msg)
                    buytp2check = False
                if priceAsk >= buyTp3 and buytp3check:
                    buytp3msg = "TP3 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, buytp3msg)
                    buytp3check = False
                    openTrades = 0
                    signal = "LOOKING"
                    break
                #return buySignal, buyLimitSignal
        if signal == "SELL":
            rates_one = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_M30, datetime.datetime.utcnow(), 1000)
            df_one = pd.DataFrame(rates_one)
            df_one.set_index("time", inplace=True)
            df_one.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "real_volume": "Volume"}, inplace=True)
            df_one.index = pd.to_datetime(df_one.index, unit="s")
            df_one.ta.ema(length=72, append=True)
            current_candle = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M30, 0, 1)[0]
            ema = df_one["EMA_" + str(72)].iloc[-1]
            #print("SELL")
            current_candle = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M30, 0, 1)[0]
            current_price = current_candle['close']
            #print(current_price)
            list_length = len(fib_levels)
            min_diff = float('inf')  # Initialize the minimum difference
            for i, price in enumerate(fib_levels):
                diff = abs(current_price - price)
                if diff < min_diff:
                    min_diff = diff
                    index = i
            if index < list_length - 1:
                priceBid = mt5.symbol_info_tick(symbol).bid
                #sellSl = priceBid + ((fib_levels[index + 1] - priceBid) / 2)
                sellSl = ema + (check_pip(symbol) * 20)
                sellTp = priceBid - (fib_levels[index + 1] - priceBid)
                sellLimitSl = fib_levels[index + 1] + (check_pip(symbol) * 50)
                sellLimitEntry = fib_levels[index + 1] - (check_pip(symbol) * 20)
                slDiffSell = (sellLimitSl - current_price) * 100
                sellTp1 = fib_levels[index - 1]
                sellTp2 = fib_levels[index - 2]
                sellTp3 = fib_levels[index - 3]
                sellSignal = "SELL {0} @ {1}\nTP1: {2}\nTP2: {3}\nTP3: {4}\nSL: {5}".format(symbol, current_price, sellTp1, sellTp2, sellTp3, sellLimitSl)
                sellLimitSignal = "SELL LIMIT {0} @ {1}\nTP1: {2}\nTP2: {3}\nTP3: {4}\nSL: {5}".format(symbol, sellLimitEntry, sellTp1, sellTp2, sellTp3, sellLimitSl)
                print(sellSignal)
                print(sellLimitSignal)
                await send_message(client, channel_username, sellSignal)
                await send_message(client, channel_username, sellLimitSignal)
                print("SELL SIGNAL SENT")
                openTrades += 1
            while openTrades == 1:
                priceBid = mt5.symbol_info_tick(symbol).bid
                if priceBid > sellTp1 and trigger:
                    print("Awaiting TP1 for {0}".format(symbol))
                    trigger = False
                if priceBid <= sellTp1 and selltp1check:
                    selltp1msg = "TP1 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, selltp1msg)
                    selltp1check = False
                if priceBid <= sellTp2 and selltp2check:
                    selltp2msg = "TP2 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, selltp2msg)
                    selltp2check = False
                if priceBid <= sellTp3 and selltp3check:
                    selltp3msg = "TP3 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, selltp3msg)
                    selltp3check = False
                    openTrades = 0
                    signal = "LOOKING"
                    break
                #return sellSignal, sellLimitSignal


async def USDCAD(client, channel_username):
    symbol = "USDCAD"
    fib_levels = await asyncio.to_thread(check_gib, symbol)

    print(datetime.datetime.now().strftime("%H:%M:%S"))

    previous_price = None  # Initialize previous_price
    buyTp1 = 0
    buyTp2 = 0
    buyTp3 = 0
    buySl = 0
    buySignal = ""
    buyLimitSignal = ""
    sellTp1 = 0
    sellTp2 = 0
    sellTp3 = 0
    sellSl = 0
    sellSignal = ""
    sellLimitSignal = ""
    signal = "LOOKING"
    openTrades = 0
    buytp1check = True
    buytp2check = True
    buytp3check = True
    selltp1check = True
    selltp2check = True
    selltp3check = True
    trigger = True

    while True:
        if signal == "LOOKING":
            signal = await asyncio.to_thread(check_ema_wma_cross, symbol)
            print(signal)
        if signal == "BUY":
            rates_one = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_M30, datetime.datetime.utcnow(), 1000)
            df_one = pd.DataFrame(rates_one)
            df_one.set_index("time", inplace=True)
            df_one.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "real_volume": "Volume"}, inplace=True)
            df_one.index = pd.to_datetime(df_one.index, unit="s")
            df_one.ta.ema(length=72, append=True)
            current_candle = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M30, 0, 1)[0]
            ema = df_one["EMA_" + str(72)].iloc[-1]
            #print("BUY")
            current_candle = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M30, 0, 1)[0]
            current_price = current_candle['close']
            list_length = len(fib_levels)
            min_diff = float('inf')  # Initialize the minimum difference
            for i, price in enumerate(fib_levels):
                diff = abs(current_price - price)
                if diff < min_diff:
                    min_diff = diff
                    index = i
            if index < list_length - 1:
                priceAsk = mt5.symbol_info_tick(symbol).ask
                #buySl = priceAsk - ((priceAsk - fib_levels[index - 1]) / 2)
                buySl = ema - (check_pip(symbol) * 20)
                buyTp = priceAsk + (priceAsk - fib_levels[index - 1])
                buyLimitSl = fib_levels[index - 1] - (check_pip(symbol) * 50)
                buyLimitEntry = fib_levels[index - 1] + (check_pip(symbol) * 20)
                buyTp1 = fib_levels[index + 1]
                buyTp2 = fib_levels[index + 2]
                buyTp3 = fib_levels[min(index + 3, list_length - 1)]
                buySignal = "BUY {0} @ {1}\nTP1: {2}\nTP2: {3}\nTP3: {4}\nSL: {5}".format(symbol, current_price, buyTp1, buyTp2, buyTp3, buyLimitSl)
                buyLimitSignal = "BUY LIMIT {0} @ {1}\nTP1: {2}\nTP2: {3}\nTP3: {4}\nSL: {5}".format(symbol, buyLimitEntry, buyTp1, buyTp2, buyTp3, buyLimitSl)
                print(buySignal)
                print(buyLimitSignal)
                await send_message(client, channel_username, buySignal)
                await send_message(client, channel_username, buyLimitSignal)
                print("BUY SIGNAL SENT")
                openTrades += 1
            while openTrades == 1:
                priceAsk = mt5.symbol_info_tick(symbol).ask
                if priceAsk < buyTp1 and trigger:
                    print("Awaiting TP1 for {0}".format(symbol))
                    trigger = False
                if priceAsk >= buyTp1 and buytp1check:
                    buytp1msg = "TP1 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, buytp1msg)
                    buytp1check = False
                if priceAsk >= buyTp2 and buytp2check:
                    buytp2msg = "TP2 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, buytp2msg)
                    buytp2check = False
                if priceAsk >= buyTp3 and buytp3check:
                    buytp3msg = "TP3 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, buytp3msg)
                    buytp3check = False
                    openTrades = 0
                    signal = "LOOKING"
                    break
                #return buySignal, buyLimitSignal
        if signal == "SELL":
            rates_one = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_M30, datetime.datetime.utcnow(), 1000)
            df_one = pd.DataFrame(rates_one)
            df_one.set_index("time", inplace=True)
            df_one.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "real_volume": "Volume"}, inplace=True)
            df_one.index = pd.to_datetime(df_one.index, unit="s")
            df_one.ta.ema(length=72, append=True)
            current_candle = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M30, 0, 1)[0]
            ema = df_one["EMA_" + str(72)].iloc[-1]
            #print("SELL")
            current_candle = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M30, 0, 1)[0]
            current_price = current_candle['close']
            #print(current_price)
            list_length = len(fib_levels)
            min_diff = float('inf')  # Initialize the minimum difference
            for i, price in enumerate(fib_levels):
                diff = abs(current_price - price)
                if diff < min_diff:
                    min_diff = diff
                    index = i
            if index < list_length - 1:
                priceBid = mt5.symbol_info_tick(symbol).bid
                #sellSl = priceBid + ((fib_levels[index + 1] - priceBid) / 2)
                sellSl = ema + (check_pip(symbol) * 20)
                sellTp = priceBid - (fib_levels[index + 1] - priceBid)
                sellLimitSl = fib_levels[index + 1] + (check_pip(symbol) * 50)
                sellLimitEntry = fib_levels[index + 1] - (check_pip(symbol) * 20)
                slDiffSell = (sellLimitSl - current_price) * 10000
                sellTp1 = fib_levels[index - 1]
                sellTp2 = fib_levels[index - 2]
                sellTp3 = fib_levels[index - 3]
                sellSignal = "SELL {0} @ {1}\nTP1: {2}\nTP2: {3}\nTP3: {4}\nSL: {5}".format(symbol, current_price, sellTp1, sellTp2, sellTp3, sellLimitSl)
                sellLimitSignal = "SELL LIMIT {0} @ {1}\nTP1: {2}\nTP2: {3}\nTP3: {4}\nSL: {5}".format(symbol, sellLimitEntry, sellTp1, sellTp2, sellTp3, sellLimitSl)
                print(sellSignal)
                print(sellLimitSignal)
                await send_message(client, channel_username, sellSignal)
                await send_message(client, channel_username, sellLimitSignal)
                print("SELL SIGNAL SENT")
                openTrades += 1
            while openTrades == 1:
                priceBid = mt5.symbol_info_tick(symbol).bid
                if priceBid > sellTp1 and trigger:
                    print("Awaiting TP1 for {0}".format(symbol))
                    trigger = False
                if priceBid <= sellTp1 and selltp1check:
                    selltp1msg = "TP1 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, selltp1msg)
                    selltp1check = False
                if priceBid <= sellTp2 and selltp2check:
                    selltp2msg = "TP2 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, selltp2msg)
                    selltp2check = False
                if priceBid <= sellTp3 and selltp3check:
                    selltp3msg = "TP3 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, selltp3msg)
                    selltp3check = False
                    openTrades = 0
                    signal = "LOOKING"
                    break
                #return sellSignal, sellLimitSignal



async def EURUSD(client, channel_username):
    symbol = "EURUSD"
    fib_levels = await asyncio.to_thread(check_gib, symbol)

    print(datetime.datetime.now().strftime("%H:%M:%S"))

    previous_price = None  # Initialize previous_price
    buyTp1 = 0
    buyTp2 = 0
    buyTp3 = 0
    buySl = 0
    buySignal = ""
    buyLimitSignal = ""
    sellTp1 = 0
    sellTp2 = 0
    sellTp3 = 0
    sellSl = 0
    sellSignal = ""
    sellLimitSignal = ""
    signal = "LOOKING"
    openTrades = 0
    buytp1check = True
    buytp2check = True
    buytp3check = True
    selltp1check = True
    selltp2check = True
    selltp3check = True
    trigger = True

    while True:
        if signal == "LOOKING":
            signal = await asyncio.to_thread(check_ema_wma_cross, symbol)
            print(signal)
        if signal == "BUY":
            rates_one = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_M30, datetime.datetime.utcnow(), 1000)
            df_one = pd.DataFrame(rates_one)
            df_one.set_index("time", inplace=True)
            df_one.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "real_volume": "Volume"}, inplace=True)
            df_one.index = pd.to_datetime(df_one.index, unit="s")
            df_one.ta.ema(length=72, append=True)
            current_candle = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M30, 0, 1)[0]
            ema = df_one["EMA_" + str(72)].iloc[-1]
            #print("BUY")
            current_candle = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M30, 0, 1)[0]
            current_price = current_candle['close']
            list_length = len(fib_levels)
            min_diff = float('inf')  # Initialize the minimum difference
            for i, price in enumerate(fib_levels):
                diff = abs(current_price - price)
                if diff < min_diff:
                    min_diff = diff
                    index = i
            if index < list_length - 1:
                priceAsk = mt5.symbol_info_tick(symbol).ask
                #buySl = priceAsk - ((priceAsk - fib_levels[index - 1]) / 2)
                buySl = ema - (check_pip(symbol) * 20)
                buyTp = priceAsk + (priceAsk - fib_levels[index - 1])
                buyLimitSl = fib_levels[index - 1] - (check_pip(symbol) * 50)
                buyLimitEntry = fib_levels[index - 1] + (check_pip(symbol) * 20)
                buyTp1 = fib_levels[index + 1]
                buyTp2 = fib_levels[index + 2]
                buyTp3 = fib_levels[min(index + 3, list_length - 1)]
                buySignal = "BUY {0} @ {1}\nTP1: {2}\nTP2: {3}\nTP3: {4}\nSL: {5}".format(symbol, current_price, buyTp1, buyTp2, buyTp3, buyLimitSl)
                buyLimitSignal = "BUY LIMIT {0} @ {1}\nTP1: {2}\nTP2: {3}\nTP3: {4}\nSL: {5}".format(symbol, buyLimitEntry, buyTp1, buyTp2, buyTp3, buyLimitSl)
                print(buySignal)
                print(buyLimitSignal)
                await send_message(client, channel_username, buySignal)
                await send_message(client, channel_username, buyLimitSignal)
                print("BUY SIGNAL SENT")
                openTrades += 1
            while openTrades == 1:
                priceAsk = mt5.symbol_info_tick(symbol).ask
                if priceAsk < buyTp1 and trigger:
                    print("Awaiting TP1 for {0}".format(symbol))
                    trigger = False
                if priceAsk >= buyTp1 and buytp1check:
                    buytp1msg = "TP1 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, buytp1msg)
                    buytp1check = False
                if priceAsk >= buyTp2 and buytp2check:
                    buytp2msg = "TP2 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, buytp2msg)
                    buytp2check = False
                if priceAsk >= buyTp3 and buytp3check:
                    buytp3msg = "TP3 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, buytp3msg)
                    buytp3check = False
                    openTrades = 0
                    signal = "LOOKING"
                    break
                #return buySignal, buyLimitSignal
        if signal == "SELL":
            rates_one = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_M30, datetime.datetime.utcnow(), 1000)
            df_one = pd.DataFrame(rates_one)
            df_one.set_index("time", inplace=True)
            df_one.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "real_volume": "Volume"}, inplace=True)
            df_one.index = pd.to_datetime(df_one.index, unit="s")
            df_one.ta.ema(length=72, append=True)
            current_candle = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M30, 0, 1)[0]
            ema = df_one["EMA_" + str(72)].iloc[-1]
            #print("SELL")
            current_candle = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M30, 0, 1)[0]
            current_price = current_candle['close']
            #print(current_price)
            list_length = len(fib_levels)
            min_diff = float('inf')  # Initialize the minimum difference
            for i, price in enumerate(fib_levels):
                diff = abs(current_price - price)
                if diff < min_diff:
                    min_diff = diff
                    index = i
            if index < list_length - 1:
                priceBid = mt5.symbol_info_tick(symbol).bid
                #sellSl = priceBid + ((fib_levels[index + 1] - priceBid) / 2)
                sellSl = ema + (check_pip(symbol) * 20)
                sellTp = priceBid - (fib_levels[index + 1] - priceBid)
                sellLimitSl = fib_levels[index + 1] + (check_pip(symbol) * 50)
                sellLimitEntry = fib_levels[index + 1] - (check_pip(symbol) * 20)
                slDiffSell = (sellLimitSl - current_price) * 10000
                sellTp1 = fib_levels[index - 1]
                sellTp2 = fib_levels[index - 2]
                sellTp3 = fib_levels[index - 3]
                sellSignal = "SELL {0} @ {1}\nTP1: {2}\nTP2: {3}\nTP3: {4}\nSL: {5}".format(symbol, current_price, sellTp1, sellTp2, sellTp3, sellLimitSl)
                sellLimitSignal = "SELL LIMIT {0} @ {1}\nTP1: {2}\nTP2: {3}\nTP3: {4}\nSL: {5}".format(symbol, sellLimitEntry, sellTp1, sellTp2, sellTp3, sellLimitSl)
                print(sellSignal)
                print(sellLimitSignal)
                await send_message(client, channel_username, sellSignal)
                await send_message(client, channel_username, sellLimitSignal)
                print("SELL SIGNAL SENT")
                openTrades += 1
            while openTrades == 1:
                priceBid = mt5.symbol_info_tick(symbol).bid
                if priceBid > sellTp1 and trigger:
                    print("Awaiting TP1 for {0}".format(symbol))
                    trigger = False
                if priceBid <= sellTp1 and selltp1check:
                    selltp1msg = "TP1 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, selltp1msg)
                    selltp1check = False
                if priceBid <= sellTp2 and selltp2check:
                    selltp2msg = "TP2 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, selltp2msg)
                    selltp2check = False
                if priceBid <= sellTp3 and selltp3check:
                    selltp3msg = "TP3 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, selltp3msg)
                    selltp3check = False
                    openTrades = 0
                    signal = "LOOKING"
                    break
                #return sellSignal, sellLimitSignal


async def GBPJPY(client, channel_username):
    symbol = "GBPJPY"
    fib_levels = await asyncio.to_thread(check_gib, symbol)

    print(datetime.datetime.now().strftime("%H:%M:%S"))

    previous_price = None  # Initialize previous_price
    buyTp1 = 0
    buyTp2 = 0
    buyTp3 = 0
    buySl = 0
    buySignal = ""
    buyLimitSignal = ""
    sellTp1 = 0
    sellTp2 = 0
    sellTp3 = 0
    sellSl = 0
    sellSignal = ""
    sellLimitSignal = ""
    signal = "LOOKING"
    openTrades = 0
    buytp1check = True
    buytp2check = True
    buytp3check = True
    selltp1check = True
    selltp2check = True
    selltp3check = True
    trigger = True

    while True:
        if signal == "LOOKING":
            signal = await asyncio.to_thread(check_ema_wma_cross, symbol)
            print(signal)
        if signal == "BUY":
            rates_one = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_M30, datetime.datetime.utcnow(), 1000)
            df_one = pd.DataFrame(rates_one)
            df_one.set_index("time", inplace=True)
            df_one.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "real_volume": "Volume"}, inplace=True)
            df_one.index = pd.to_datetime(df_one.index, unit="s")
            df_one.ta.ema(length=72, append=True)
            current_candle = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M30, 0, 1)[0]
            ema = df_one["EMA_" + str(72)].iloc[-1]
            #print("BUY")
            current_candle = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M30, 0, 1)[0]
            current_price = current_candle['close']
            list_length = len(fib_levels)
            min_diff = float('inf')  # Initialize the minimum difference
            for i, price in enumerate(fib_levels):
                diff = abs(current_price - price)
                if diff < min_diff:
                    min_diff = diff
                    index = i
            if index < list_length - 1:
                priceAsk = mt5.symbol_info_tick(symbol).ask
                #buySl = priceAsk - ((priceAsk - fib_levels[index - 1]) / 2)
                buySl = ema - (check_pip(symbol) * 20)
                buyTp = priceAsk + (priceAsk - fib_levels[index - 1])
                buyLimitSl = fib_levels[index - 1] - (check_pip(symbol) * 50)
                buyLimitEntry = fib_levels[index - 1] + (check_pip(symbol) * 20)
                buyTp1 = fib_levels[index + 1]
                buyTp2 = fib_levels[index + 2]
                buyTp3 = fib_levels[min(index + 3, list_length - 1)]
                buySignal = "BUY {0} @ {1}\nTP1: {2}\nTP2: {3}\nTP3: {4}\nSL: {5}".format(symbol, current_price, buyTp1, buyTp2, buyTp3, buyLimitSl)
                buyLimitSignal = "BUY LIMIT {0} @ {1}\nTP1: {2}\nTP2: {3}\nTP3: {4}\nSL: {5}".format(symbol, buyLimitEntry, buyTp1, buyTp2, buyTp3, buyLimitSl)
                print(buySignal)
                print(buyLimitSignal)
                await send_message(client, channel_username, buySignal)
                await send_message(client, channel_username, buyLimitSignal)
                print("BUY SIGNAL SENT")
                openTrades += 1
            while openTrades == 1:
                priceAsk = mt5.symbol_info_tick(symbol).ask
                if priceAsk < buyTp1 and trigger:
                    print("Awaiting TP1 for {0}".format(symbol))
                    trigger = False
                if priceAsk >= buyTp1 and buytp1check:
                    buytp1msg = "TP1 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, buytp1msg)
                    buytp1check = False
                if priceAsk >= buyTp2 and buytp2check:
                    buytp2msg = "TP2 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, buytp2msg)
                    buytp2check = False
                if priceAsk >= buyTp3 and buytp3check:
                    buytp3msg = "TP3 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, buytp3msg)
                    buytp3check = False
                    openTrades = 0
                    signal = "LOOKING"
                    break
                #return buySignal, buyLimitSignal
        if signal == "SELL":
            rates_one = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_M30, datetime.datetime.utcnow(), 1000)
            df_one = pd.DataFrame(rates_one)
            df_one.set_index("time", inplace=True)
            df_one.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "real_volume": "Volume"}, inplace=True)
            df_one.index = pd.to_datetime(df_one.index, unit="s")
            df_one.ta.ema(length=72, append=True)
            current_candle = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M30, 0, 1)[0]
            ema = df_one["EMA_" + str(72)].iloc[-1]
            #print("SELL")
            current_candle = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M30, 0, 1)[0]
            current_price = current_candle['close']
            #print(current_price)
            list_length = len(fib_levels)
            min_diff = float('inf')  # Initialize the minimum difference
            for i, price in enumerate(fib_levels):
                diff = abs(current_price - price)
                if diff < min_diff:
                    min_diff = diff
                    index = i
            if index < list_length - 1:
                priceBid = mt5.symbol_info_tick(symbol).bid
                #sellSl = priceBid + ((fib_levels[index + 1] - priceBid) / 2)
                sellSl = ema + (check_pip(symbol) * 20)
                sellTp = priceBid - (fib_levels[index + 1] - priceBid)
                sellLimitSl = fib_levels[index + 1] + (check_pip(symbol) * 50)
                sellLimitEntry = fib_levels[index + 1] - (check_pip(symbol) * 20)
                slDiffSell = (sellLimitSl - current_price) * 100
                sellTp1 = fib_levels[index - 1]
                sellTp2 = fib_levels[index - 2]
                sellTp3 = fib_levels[index - 3]
                sellSignal = "SELL {0} @ {1}\nTP1: {2}\nTP2: {3}\nTP3: {4}\nSL: {5}".format(symbol, current_price, sellTp1, sellTp2, sellTp3, sellLimitSl)
                sellLimitSignal = "SELL LIMIT {0} @ {1}\nTP1: {2}\nTP2: {3}\nTP3: {4}\nSL: {5}".format(symbol, sellLimitEntry, sellTp1, sellTp2, sellTp3, sellLimitSl)
                print(sellSignal)
                print(sellLimitSignal)
                await send_message(client, channel_username, sellSignal)
                await send_message(client, channel_username, sellLimitSignal)
                print("SELL SIGNAL SENT")
                openTrades += 1
            while openTrades == 1:
                priceBid = mt5.symbol_info_tick(symbol).bid
                if priceBid > sellTp1 and trigger:
                    print("Awaiting TP1 for {0}".format(symbol))
                    trigger = False
                if priceBid <= sellTp1 and selltp1check:
                    selltp1msg = "TP1 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, selltp1msg)
                    selltp1check = False
                if priceBid <= sellTp2 and selltp2check:
                    selltp2msg = "TP2 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, selltp2msg)
                    selltp2check = False
                if priceBid <= sellTp3 and selltp3check:
                    selltp3msg = "TP3 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, selltp3msg)
                    selltp3check = False
                    openTrades = 0
                    signal = "LOOKING"
                    break
                #return sellSignal, sellLimitSignal


async def XAUUSD(client, channel_username):
    symbol = "XAUUSD"
    fib_levels = await asyncio.to_thread(check_gib, symbol)

    print(datetime.datetime.now().strftime("%H:%M:%S"))

    previous_price = None  # Initialize previous_price
    buyTp1 = 0
    buyTp2 = 0
    buyTp3 = 0
    buySl = 0
    buySignal = ""
    buyLimitSignal = ""
    sellTp1 = 0
    sellTp2 = 0
    sellTp3 = 0
    sellSl = 0
    sellSignal = ""
    sellLimitSignal = ""
    signal = "LOOKING"
    openTrades = 0
    buytp1check = True
    buytp2check = True
    buytp3check = True
    selltp1check = True
    selltp2check = True
    selltp3check = True
    trigger = True

    while True:
        if signal == "LOOKING":
            signal = await asyncio.to_thread(check_ema_wma_cross, symbol)
            print(signal)
        if signal == "BUY":
            rates_one = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_M30, datetime.datetime.utcnow(), 1000)
            df_one = pd.DataFrame(rates_one)
            df_one.set_index("time", inplace=True)
            df_one.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "real_volume": "Volume"}, inplace=True)
            df_one.index = pd.to_datetime(df_one.index, unit="s")
            df_one.ta.ema(length=72, append=True)
            current_candle = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M30, 0, 1)[0]
            ema = df_one["EMA_" + str(72)].iloc[-1]
            #print("BUY")
            current_candle = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M30, 0, 1)[0]
            current_price = current_candle['close']
            list_length = len(fib_levels)
            min_diff = float('inf')  # Initialize the minimum difference
            for i, price in enumerate(fib_levels):
                diff = abs(current_price - price)
                if diff < min_diff:
                    min_diff = diff
                    index = i
            if index < list_length - 1:
                priceAsk = mt5.symbol_info_tick(symbol).ask
                #buySl = priceAsk - ((priceAsk - fib_levels[index - 1]) / 2)
                buySl = ema - (check_pip(symbol) * 20)
                buyTp = priceAsk + (priceAsk - fib_levels[index - 1])
                buyLimitSl = fib_levels[index - 1] - (check_pip(symbol) * 50)
                buyLimitEntry = fib_levels[index - 1] + (check_pip(symbol) * 20)
                buyTp1 = fib_levels[index + 1]
                buyTp2 = fib_levels[index + 2]
                buyTp3 = fib_levels[min(index + 3, list_length - 1)]
                buySignal = "BUY {0} @ {1}\nTP1: {2}\nTP2: {3}\nTP3: {4}\nSL: {5}".format(symbol, current_price, buyTp1, buyTp2, buyTp3, buyLimitSl)
                buyLimitSignal = "BUY LIMIT {0} @ {1}\nTP1: {2}\nTP2: {3}\nTP3: {4}\nSL: {5}".format(symbol, buyLimitEntry, buyTp1, buyTp2, buyTp3, buyLimitSl)
                print(buySignal)
                print(buyLimitSignal)
                await send_message(client, channel_username, buySignal)
                await send_message(client, channel_username, buyLimitSignal)
                print("BUY SIGNAL SENT")
                openTrades += 1
            while openTrades == 1:
                priceAsk = mt5.symbol_info_tick(symbol).ask
                if priceAsk < buyTp1 and trigger:
                    print("Awaiting TP1 for {0}".format(symbol))
                    trigger = False
                if priceAsk >= buyTp1 and buytp1check:
                    buytp1msg = "TP1 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, buytp1msg)
                    buytp1check = False
                if priceAsk >= buyTp2 and buytp2check:
                    buytp2msg = "TP2 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, buytp2msg)
                    buytp2check = False
                if priceAsk >= buyTp3 and buytp3check:
                    buytp3msg = "TP3 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, buytp3msg)
                    buytp3check = False
                    openTrades = 0
                    signal = "LOOKING"
                    break
                #return buySignal, buyLimitSignal
        if signal == "SELL":
            rates_one = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_M30, datetime.datetime.utcnow(), 1000)
            df_one = pd.DataFrame(rates_one)
            df_one.set_index("time", inplace=True)
            df_one.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "real_volume": "Volume"}, inplace=True)
            df_one.index = pd.to_datetime(df_one.index, unit="s")
            df_one.ta.ema(length=72, append=True)
            current_candle = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M30, 0, 1)[0]
            ema = df_one["EMA_" + str(72)].iloc[-1]
            #print("SELL")
            current_candle = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M30, 0, 1)[0]
            current_price = current_candle['close']
            #print(current_price)
            list_length = len(fib_levels)
            min_diff = float('inf')  # Initialize the minimum difference
            for i, price in enumerate(fib_levels):
                diff = abs(current_price - price)
                if diff < min_diff:
                    min_diff = diff
                    index = i
            if index < list_length - 1:
                priceBid = mt5.symbol_info_tick(symbol).bid
                #sellSl = priceBid + ((fib_levels[index + 1] - priceBid) / 2)
                sellSl = ema + (check_pip(symbol) * 20)
                sellTp = priceBid - (fib_levels[index + 1] - priceBid)
                sellLimitSl = fib_levels[index + 1] + (check_pip(symbol) * 50)
                sellLimitEntry = fib_levels[index + 1] - (check_pip(symbol) * 20)
                slDiffSell = (sellLimitSl - current_price) * 10000
                sellTp1 = fib_levels[index - 1]
                sellTp2 = fib_levels[index - 2]
                sellTp3 = fib_levels[index - 3]
                sellSignal = "SELL {0} @ {1}\nTP1: {2}\nTP2: {3}\nTP3: {4}\nSL: {5}".format(symbol, current_price, sellTp1, sellTp2, sellTp3, sellLimitSl)
                sellLimitSignal = "SELL LIMIT {0} @ {1}\nTP1: {2}\nTP2: {3}\nTP3: {4}\nSL: {5}".format(symbol, sellLimitEntry, sellTp1, sellTp2, sellTp3, sellLimitSl)
                print(sellSignal)
                print(sellLimitSignal)
                await send_message(client, channel_username, sellSignal)
                await send_message(client, channel_username, sellLimitSignal)
                print("SELL SIGNAL SENT")
                openTrades += 1
            while openTrades == 1:
                priceBid = mt5.symbol_info_tick(symbol).bid
                if priceBid > sellTp1 and trigger:
                    print("Awaiting TP1 for {0}".format(symbol))
                    trigger = False
                if priceBid <= sellTp1 and selltp1check:
                    selltp1msg = "TP1 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, selltp1msg)
                    selltp1check = False
                if priceBid <= sellTp2 and selltp2check:
                    selltp2msg = "TP2 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, selltp2msg)
                    selltp2check = False
                if priceBid <= sellTp3 and selltp3check:
                    selltp3msg = "TP3 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, selltp3msg)
                    selltp3check = False
                    openTrades = 0
                    signal = "LOOKING"
                    break
                #return sellSignal, sellLimitSignal


async def US30(client, channel_username):
    symbol = "US30"
    fib_levels = await asyncio.to_thread(check_gib, symbol)

    print(datetime.datetime.now().strftime("%H:%M:%S"))

    previous_price = None  # Initialize previous_price
    buyTp1 = 0
    buyTp2 = 0
    buyTp3 = 0
    buySl = 0
    buySignal = ""
    buyLimitSignal = ""
    sellTp1 = 0
    sellTp2 = 0
    sellTp3 = 0
    sellSl = 0
    sellSignal = ""
    sellLimitSignal = ""
    signal = "LOOKING"
    openTrades = 0
    buytp1check = True
    buytp2check = True
    buytp3check = True
    selltp1check = True
    selltp2check = True
    selltp3check = True
    trigger = True

    while True:
        if signal == "LOOKING":
            signal = await asyncio.to_thread(check_ema_wma_cross, symbol)
            print(signal)
        if signal == "BUY":
            rates_one = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_M30, datetime.datetime.utcnow(), 1000)
            df_one = pd.DataFrame(rates_one)
            df_one.set_index("time", inplace=True)
            df_one.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "real_volume": "Volume"}, inplace=True)
            df_one.index = pd.to_datetime(df_one.index, unit="s")
            df_one.ta.ema(length=72, append=True)
            current_candle = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M30, 0, 1)[0]
            ema = df_one["EMA_" + str(72)].iloc[-1]
            #print("BUY")
            current_candle = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M30, 0, 1)[0]
            current_price = current_candle['close']
            list_length = len(fib_levels)
            min_diff = float('inf')  # Initialize the minimum difference
            for i, price in enumerate(fib_levels):
                diff = abs(current_price - price)
                if diff < min_diff:
                    min_diff = diff
                    index = i
            if index < list_length - 1:
                priceAsk = mt5.symbol_info_tick(symbol).ask
                #buySl = priceAsk - ((priceAsk - fib_levels[index - 1]) / 2)
                buySl = ema - (check_pip(symbol) * 20)
                buyTp = priceAsk + (priceAsk - fib_levels[index - 1])
                buyLimitSl = fib_levels[index - 1] - (check_pip(symbol) * 50)
                buyLimitEntry = fib_levels[index - 1] + (check_pip(symbol) * 20)
                buyTp1 = fib_levels[index + 1]
                buyTp2 = fib_levels[index + 2]
                buyTp3 = fib_levels[min(index + 3, list_length - 1)]
                buySignal = "BUY {0} @ {1}\nTP1: {2}\nTP2: {3}\nTP3: {4}\nSL: {5}".format(symbol, current_price, buyTp1, buyTp2, buyTp3, buyLimitSl)
                buyLimitSignal = "BUY LIMIT {0} @ {1}\nTP1: {2}\nTP2: {3}\nTP3: {4}\nSL: {5}".format(symbol, buyLimitEntry, buyTp1, buyTp2, buyTp3, buyLimitSl)
                print(buySignal)
                print(buyLimitSignal)
                await send_message(client, channel_username, buySignal)
                await send_message(client, channel_username, buyLimitSignal)
                print("BUY SIGNAL SENT")
                openTrades += 1
            while openTrades == 1:
                priceAsk = mt5.symbol_info_tick(symbol).ask
                if priceAsk < buyTp1 and trigger:
                    print("Awaiting TP1 for {0}".format(symbol))
                    trigger = False
                if priceAsk >= buyTp1 and buytp1check:
                    buytp1msg = "TP1 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, buytp1msg)
                    buytp1check = False
                if priceAsk >= buyTp2 and buytp2check:
                    buytp2msg = "TP2 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, buytp2msg)
                    buytp2check = False
                if priceAsk >= buyTp3 and buytp3check:
                    buytp3msg = "TP3 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, buytp3msg)
                    buytp3check = False
                    openTrades = 0
                    signal = "LOOKING"
                    break
                #return buySignal, buyLimitSignal
        if signal == "SELL":
            rates_one = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_M30, datetime.datetime.utcnow(), 1000)
            df_one = pd.DataFrame(rates_one)
            df_one.set_index("time", inplace=True)
            df_one.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "real_volume": "Volume"}, inplace=True)
            df_one.index = pd.to_datetime(df_one.index, unit="s")
            df_one.ta.ema(length=72, append=True)
            current_candle = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M30, 0, 1)[0]
            ema = df_one["EMA_" + str(72)].iloc[-1]
            #print("SELL")
            current_candle = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M30, 0, 1)[0]
            current_price = current_candle['close']
            #print(current_price)
            list_length = len(fib_levels)
            min_diff = float('inf')  # Initialize the minimum difference
            for i, price in enumerate(fib_levels):
                diff = abs(current_price - price)
                if diff < min_diff:
                    min_diff = diff
                    index = i
            if index < list_length - 1:
                priceBid = mt5.symbol_info_tick(symbol).bid
                #sellSl = priceBid + ((fib_levels[index + 1] - priceBid) / 2)
                sellSl = ema + (check_pip(symbol) * 20)
                sellTp = priceBid - (fib_levels[index + 1] - priceBid)
                sellLimitSl = fib_levels[index + 1] + (check_pip(symbol) * 50)
                sellLimitEntry = fib_levels[index + 1] - (check_pip(symbol) * 20)
                slDiffSell = (sellLimitSl - current_price) * 10000
                sellTp1 = fib_levels[index - 1]
                sellTp2 = fib_levels[index - 2]
                sellTp3 = fib_levels[index - 3]
                sellSignal = "SELL {0} @ {1}\nTP1: {2}\nTP2: {3}\nTP3: {4}\nSL: {5}".format(symbol, current_price, sellTp1, sellTp2, sellTp3, sellLimitSl)
                sellLimitSignal = "SELL LIMIT {0} @ {1}\nTP1: {2}\nTP2: {3}\nTP3: {4}\nSL: {5}".format(symbol, sellLimitEntry, sellTp1, sellTp2, sellTp3, sellLimitSl)
                print(sellSignal)
                print(sellLimitSignal)
                await send_message(client, channel_username, sellSignal)
                await send_message(client, channel_username, sellLimitSignal)
                print("SELL SIGNAL SENT")
                openTrades += 1
            while openTrades == 1:
                priceBid = mt5.symbol_info_tick(symbol).bid
                if priceBid > sellTp1 and trigger:
                    print("Awaiting TP1 for {0}".format(symbol))
                    trigger = False
                if priceBid <= sellTp1 and selltp1check:
                    selltp1msg = "TP1 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, selltp1msg)
                    selltp1check = False
                if priceBid <= sellTp2 and selltp2check:
                    selltp2msg = "TP2 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, selltp2msg)
                    selltp2check = False
                if priceBid <= sellTp3 and selltp3check:
                    selltp3msg = "TP3 Hit for {0}".format(symbol)
                    await send_message(client, channel_username, selltp3msg)
                    selltp3check = False
                    openTrades = 0
                    signal = "LOOKING"
                    break
                #return sellSignal, sellLimitSignal


async def main():
    api_id = "ENTER API ID HERE"
    api_hash = "ENTER API HAS HERE"
    phone_number = "ENTER PHONE NUMBER HERE"
    session_name = 'my_session'
    client = TelegramClient(session_name, api_id, api_hash)
    channel_username = "ENTER CHANNEL USERNAME HERE"
    # connect to MetaTrader 5
    if not mt5.initialize(login="ENTER METATRADER 5 LOGIN HERE", password="ENTER METATRADER 5 PASSWORD HERE", server="ENTER METATRADER 5 SERVER HERE", portable=True):
        print("initialize() failed")
        mt5.shutdown()
    async with client:
        # Run the functions concurrently
        results = await asyncio.gather(
            send_message(client, channel_username, "Greetings! We will begin looking for trades at 0100 EST."),
            US30(client, channel_username),
            USDCAD(client, channel_username),
            GBPJPY(client, channel_username),
            XAUUSD(client, channel_username),
            USDJPY(client, channel_username),
            EURUSD(client, channel_username)
        )


if __name__ == "__main__":
    asyncio.run(main())