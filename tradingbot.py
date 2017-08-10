
#!/usr/bin/env python
#Imports
from bittrex import bittrex
from time import sleep
import time
import sys
from poloniex import poloniex
def main(argv):
	period = 5
	pair = "BTC_DCR"
	currency = "DCR"
	tradePlaced = False

	#Bittrex API Keys
	api = bittrex('BITTREXAPIKEYHERE','BITTREXAPISECRETHERE')

	#Market to trade at
	trade = 'BTC'
	market= '{0}-{1}'.format(trade,currency)

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
			print "Buy from poloAsk, sell to bittrex Bid. Profit: 		" + str((arbitrage*100))
		elif(bittrexAsk<poloBid):
			arbitrage=polobid/bittrexAsk
			print "Buy from Bittrex Ask, sell to poloBid. Profit:		" + str((arbitrage*100))
		#orderNumber=conn.sell(pair,lastPairPrice,0.001)
		#orderNumber=conn.buy(pair, poloAsk, 0.1)
		time.sleep(period)


if __name__ == "__main__":
	main(sys.argv[1:])
