#!/usr/bin/env python
#Imports
from bittrex import bittrex
from time import sleep
import time
import sys
from poloniex import poloniex
import argparse
def main(argv):
	# Setup Argument Parser
	parser = argparse.ArgumentParser(description='Poloniex/Bittrex Arbitrage Bot')
	parser.add_argument('-d', '--dryrun', action='store_true', required=False, help='simulates without trading (API keys not required)')
	args = parser.parse_args()

	if args.dryrun:
		print("Dryrun Mode Enabled (will not trade)")

	#Inputs and set variables
	period = float(raw_input("Period(Delay Between Each Check in seconds): "))
	currency = raw_input("Coin (Example: ETH): ")
	minArb = float(raw_input("Minimum Arbitrage % (Recomended to set above 100.5 as fees from both sides add up to 0.5%): "))
	trade = 'BTC'
	tradePlaced = False

	#Bittrex API Keys
	bittrexAPI = bittrex('APIKEY','APISECRET')

	#Polo API Keys
	poloniexAPI = poloniex('APIKEY','APISECRET')

	#Bittrex market
	market = '{0}-{1}'.format(trade,currency)

	#Polo market
	pair = '{0}_{1}'.format(trade,currency)

	while True:

		#Poloniex Prices
		currentValues = poloniexAPI.api_query("returnTicker")
		poloBid = float(currentValues[pair]["highestBid"])
		poloAsk = float(currentValues[pair]["lowestAsk"])
		print("Bid @ Poloniex:	" + str(poloBid))
		print("Ask @ Poloniex:	" + str(poloAsk))

		#Bittrex Prices
		summary=bittrexAPI.getmarketsummary(market)
		bittrexAsk = summary[0]['Ask']
		print("Ask @ Bittrex:	" + str(bittrexAsk))
		bittrexBid = summary[0]['Bid']
		print("Bid @ Bittrex:	" + str(bittrexBid))

		# Get Balance Information, fake numbers if dryrun.
		if not args.dryrun:
			# Query Bittrex API
			bittrexBalance=bittrexAPI.getbalance(currency)
			bittrexBTCBalance=bittrexAPI.getbalance("btc")
			# Query Poloniex API
			allpolobalance=poloniexAPI.api_query('returnBalances')
			# Copy Poloniex Balance Variables
			poloniexBalance=allpolobalance[currency]
			poloniexBTCBalance=allpolobalance["BTC"]
		else:
			# Faking Balance Numbers for Dryrun Simulation
			bittrexBalance=100.0
			bittrexBTCBalance=100.0
			poloniexBalance=100.0
			poloniexBTCBalance=100.0

		#Buy from Polo, Sell to Bittrex
		if (poloAsk<bittrexBid):
			arbitrage=bittrexBid/poloAsk
			#Check if min arb is met
			if ((arbitrage*100)>minArb):
				print("Buy from poloAsk, sell to bittrexBid. Profit: " + str(arbitrage*100))
				sellbook=poloniexAPI.returnOrderBook(pair)["asks"][0][1]
				buybook=bittrexAPI.getorderbook(market, "sell")[0]["Quantity"]

				#Find minimum order size
				tradesize=min(sellbook, buybook)

				#Setting order size incase balance not enough
				if (bittrexBalance<tradesize):
					tradesize=bittrexBalance

				if ((tradesize*poloAsk)>poloniexBTCBalance):
					tradesize=poloniexBTCBalance/poloAsk

				#Check if above min order size
				if ((tradesize*bittrexBid)>0.0005001):
					print("Selling {0} {1} @ BittrexBid @ {2} and buying {3} {4} @ PoloAsk @ {5}".format(tradesize, currency, bittrexBid, tradesize, currency, poloAsk))
					#Execute order
					if not args.dryrun:
						bittrexAPI.selllimit(market, tradesize, bittrexBid)
						orderNumber=poloniexAPI.buy(pair, poloAsk, tradesize)
					else:
						print("Dryrun: skipping order")

		#Sell to polo, Buy from Bittrex
		elif(bittrexAsk<poloBid):
			arbitrage=poloBid/bittrexAsk
			#Check if min arb is met
			if ((arbitrage*100)>minArb):
				print("Buy from Bittrex Ask, sell to poloBid. Profit: " + str(arbitrage*100))
				buybook=poloniexAPI.returnOrderBook(pair)["bids"][0][1]
				sellbook=bittrexAPI.getorderbook(market, "sell")[0]["Quantity"]

				#Find minimum order size
				tradesize=min(sellbook, buybook)

				#Setting order size incase balance not eough
				if (poloniexBalance<tradesize):
					tradesize=poloniexBalance

				if((tradesize*bittrexAsk)>bittrexBTCBalance):
					tradesize=bittrexBTCBalance/bittrexAsk

				#Check if above min order size
				if ((tradesize*bittrexAsk)>0.0005001):
					print("Selling {0} {1} @ PoloBid @ {2} and Buying {3} {4} @ BittrexAsk @ {5}".format(tradesize, currency, poloBid, tradesize, currency, bittrexAsk))
					#Execute order
					if not args.dryrun:
						bittrexAPI.buylimit(market, tradesize, bittrexAsk)
						orderNumber=poloniexAPI.sell(pair, poloBid, tradesize)
					else:
						print("Dryrun: skipping order")

		time.sleep(period)


if __name__ == "__main__":
	main(sys.argv[1:])
