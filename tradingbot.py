#!/usr/bin/env python
#Imports
from bittrex import bittrex
from time import sleep
import time
import sys
from poloniex import poloniex
def main(argv):
	period = float(raw_input("Period(Delay Between Each Check in seconds):	"))
	currency = raw_input("Coin(Example: ETH):	")
	minArb=float(raw_input("Minimum Arbitrage %. Recomended to set above 100.5 as fees from both sides add up to 0.5%.	"))
	trade = 'BTC'
	tradePlaced = False

	#Bittrex API Keys
	api = bittrex('BITTREXAPIKEYHERE','BITTREXAPISECRETHERE')

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

		if (poloAsk<bittrexBid):
			arbitrage=bittrexBid/poloAsk
			if ((arbitrage*100)>minArb):
				print "Buy from poloAsk, sell to bittrexBid. Profit: " + str(arbitrage*100)
				sellbook=conn.returnOrderBook(pair)["asks"][0][1]
				buybook=api.getorderbook(market, "sell")[0]["Quantity"]
				if (sellbook<buybook):
					api.selllimit(market, sellbook, bittrexBid)
					orderNumber=conn.sell(pair, poloAsk, sellbook)
					print "Selling {0} {1} @ BittrexBid @ {2} and buying {3} {4} @ PoloAsk @ {5}".format(sellbook, currency, bittrexBid, sellbook, currency, poloAsk)
				elif (buybook<sellbook):
					api.selllimit(market, buybook, bittrexBid)
					orderNumber=conn.sell(pair, poloAsk, buybook)
					print "Selling {0} {1} @ BittrexBid @ {2} and buying {3} {4} @ PoloAsk @ {5}".format(buybook, currency, bittrexBid, buybook, currency, poloAsk)
			#else:
			#print "Arbitrage found but less than min arb."
		elif(bittrexAsk<poloBid):
			arbitrage=poloBid/bittrexAsk
			if ((arbitrage*100)>minArb):
				print "Buy from Bittrex Ask, sell to poloBid. Profit: " + str(arbitrage*100)
				buybook=conn.returnOrderBook(pair)["bids"][0][1]
				sellbook=api.getorderbook(market, "sell")[0]["Quantity"]
				if (sellbook<buybook):
					api.buylimit(market, sellbook, bittrexAsk)
					orderNumber=conn.sell(pair, poloBid, sellbook)
					print "Selling {0} {1} @ PoloBid @ {2} and Buying {3} {4} @ BittrexAsk @ {5}".format(sellbook, currency, poloBid, sellbook, currency, bittrexAsk)
				elif (buybook<sellbook):
					api.buylimit(market, buybook, bittrexAsk)
					orderNumber=conn.sell(pair, poloBid, buybook)
                                        print "Selling {0} {1} @ PoloBid @ {2} and Buying {3} {4} @ BittrexAsk @ {5}".format(buybook, currency, poloBid, buybook, currency, bittrexAsk)
#			else:
#				print "Arbitrage found but less than min arb."
		time.sleep(period)


if __name__ == "__main__":
	main(sys.argv[1:])
