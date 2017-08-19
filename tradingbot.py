#!/usr/bin/env python
#Imports
from bittrex import bittrex
from time import sleep
import time
import sys
from poloniex import poloniex
def main(argv):

	#Inputs and set variables
	period = float(raw_input("Period(Delay Between Each Check in seconds):	"))
	currency = raw_input("Coin(Example: ETH):	")
	minArb=float(raw_input("Minimum Arbitrage %. Recomended to set above 100.5 as fees from both sides add up to 0.5%.	"))
	trade = 'BTC'
	tradePlaced = False

	#Bittrex API Keys
	api = bittrex('BITTREXAPIKEY','BITTREXAPISECRET')

	#Bittrex market
	market= '{0}-{1}'.format(trade,currency)

	#Polo market
	pair= '{0}_{1}'.format(trade,currency)

	#Polo API Keys
	conn= poloniex('POLONIEXAPIKEY','POLONIEXAPISECRET')

	while True:

		#Poloniex Prices
		currentValues = conn.api_query("returnTicker")
		poloBid = float(currentValues[pair]["highestBid"])
		poloAsk = float(currentValues[pair]["lowestAsk"])
		print "Bid @ Poloniex:	" + str(poloBid)
		print "Ask @ Poloniex	" + str(poloAsk)

		#Bittrex Prices
		summary=api.getmarketsummary(market)
		bittrexAsk = summary[0]['Ask']
		print "Ask @ Bittrex:	" + str(bittrexAsk)
		bittrexBid = summary[0]['Bid']
		print "Bid @ Bittrex:	" + str(bittrexBid)

		#Balances for currency
		bittrexBalance=api.getbalance(currency)
		allpolobalance=conn.api_query('returnBalances')
		poloniexBalance=allpolobalance[currency]


		#Balances for BTC
		bittrexBTCBalance=api.getbalance("btc")
		poloniexBTCBalance=allpolobalance["BTC"]

		#Buy from Polo, Sell to Bittrex
		if (poloAsk<bittrexBid):
			arbitrage=bittrexBid/poloAsk
			#Check if min arb is met
			if ((arbitrage*100)>minArb):
				print "Buy from poloAsk, sell to bittrexBid. Profit: " + str(arbitrage*100)
				sellbook=conn.returnOrderBook(pair)["asks"][0][1]
				buybook=api.getorderbook(market, "sell")[0]["Quantity"]

				#Find minimum order size
				tradesize=min(sellbook, buybook)

				#Setting order size incase balance not enough
				if (bittrexBalance<tradesize):
					tradesize=bittrexBalance

				if ((tradesize*poloAsk)>poloniexBTCBalance):
					tradesize=poloniexBTCBalance/poloAsk

				#Execute order
				api.selllimit(market, tradesize, bittrexBid)
				orderNumber=conn.sell(pair, poloAsk, tradesize)
				print "Selling {0} {1} @ BittrexBid @ {2} and buying {3} {4} @ PoloAsk @ {5}".format(tradesize, currency, bittrexBid, tradesize, currency, poloAsk)

		#Sell to polo, Buy from Bittrex
		elif(bittrexAsk<poloBid):
			arbitrage=poloBid/bittrexAsk
			#Check if min arb is met
			if ((arbitrage*100)>minArb):
				print "Buy from Bittrex Ask, sell to poloBid. Profit: " + str(arbitrage*100)
				buybook=conn.returnOrderBook(pair)["bids"][0][1]
				sellbook=api.getorderbook(market, "sell")[0]["Quantity"]

				#Find minimum order size
				tradesize=min(sellbook, buybook)

				#Setting order size incase balance not eough
				if (poloniexBalance<tradesize):
					tradesize=poloniexBalance

				if((tradesize*bittrexAsk)>bittrexBTCBalance):
					tradesize=bittrexBTCBalance/bittrexAsk

				#Execute order
				api.buylimit(market, tradesize, bittrexAsk)
				orderNumber=conn.sell(pair, poloBid, tradesize)
				print "Selling {0} {1} @ PoloBid @ {2} and Buying {3} {4} @ BittrexAsk @ {5}".format(tradesize, currency, poloBid, tradesize, currency, bittrexAsk)

		time.sleep(period)


if __name__ == "__main__":
	main(sys.argv[1:])
