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
	parser.add_argument('-s', '--symbol', default='XMR', type=str, required=False, help='symbol of your target coin [default: XMR]')
	parser.add_argument('-r', '--rate', default=1.0, type=float, required=False, help='minimum price difference [default: 1.0]')
	parser.add_argument('-i', '--interval', default=1, type=int, required=False, help='seconds to sleep between loops [default: 1]')
	parser.add_argument('-d', '--dryrun', action='store_true', required=False, help='simulates without trading (API keys not required)')
	parser.add_argument('-v', '--verbose', action='store_true', required=False, help='enables extra console messages (for debugging)')
	args = parser.parse_args()

	# Settings
	targetCurrency = args.symbol
	baseCurrency = 'BTC'

	# Print Settings
	print('Arb Pair: {}/{} | Rate: {} | Interval: {}'.format(baseCurrency, targetCurrency, args.rate, args.interval))
	if args.dryrun:
		print("Dryrun Mode Enabled (will not trade)")

	# Pair Strings for accessing API responses
	bittrexPair = '{0}-{1}'.format(baseCurrency, targetCurrency)
	poloniexPair = '{0}_{1}'.format(baseCurrency, targetCurrency)

	#Bittrex API Keys
	bittrexAPI = bittrex('APIKEY','APISECRET')
	#Polo API Keys
	poloniexAPI = poloniex('APIKEY','APISECRET')

	# Trade Function
	def trade(_buyExchange, _ask, _bid, _srcBalance, _buyBalance):
		# _buyExchange:
		# 0 = Poloniex
		# 1 = Bittrex
		arbitrage = _bid/_ask
		# Return minumum arbitrage percentage is not met
		if (arbitrage <= args.rate):
			return

		if (_buyExchange == 0):
			buyExchangeString = 'Poloniex'
			sellExchangeString = 'Bittrex'
			sellbook = poloniexAPI.returnOrderBook(poloniexPair)["asks"][0][1]
			buybook = bittrexAPI.getorderbook(bittrexPair, "sell")[0]["Quantity"]
		elif (_buyExchange == 1):
			buyExchangeString = 'Bittrex'
			sellExchangeString = 'Poloniex'
			buybook = poloniexAPI.returnOrderBook(poloniexPair)["bids"][0][1]
			sellbook = bittrexAPI.getorderbook(bittrexPair, "sell")[0]["Quantity"]

		print('\nBuy from ' + buyExchangeString + ', sell to ' + sellExchangeString + '. Arbitrage Rate: ' + str(arbitrage) + '%')

		#Find minimum order size
		tradesize = min(sellbook, buybook)

		#Setting order size incase balance not enough
		if (_srcBalance < tradesize):
			tradesize = _srcBalance

		if ((tradesize*_ask) > _buyBalance):
			tradesize = _buyBalance / _ask

		#Check if above min order size
		if ((tradesize*_bid)>0.0005001):
			print("==Order {}==\nSELL: {}	| {} @ {:.8f} (Balance: {})\nBUY: {}	| {} @ {:.8f} (Balance: {})".format(bittrexPair, sellExchangeString, tradesize, _bid, _srcBalance, buyExchangeString, tradesize, _ask, _buyBalance))
			#Execute order
			if not args.dryrun:
				if (_buyExchange == 0):
					bittrexAPI.selllimit(bittrexPair, tradesize, _bid)
					orderNumber = poloniexAPI.buy(poloniexPair, _ask, tradesize)
				elif (_buyExchange == 1):
					bittrexAPI.buylimit(bittrexPair, tradesize, _ask)
					orderNumber = poloniexAPI.sell(poloniexPair, _bid, tradesize)
			else:
				print("Dryrun: skipping order")
		else:
			print("Order size not above min order size, no trade was executed")

	# Main Loop
	while True:
		# Query Poloniex Prices
		currentValues = poloniexAPI.api_query("returnTicker")
		poloBid = float(currentValues[poloniexPair]["highestBid"])
		poloAsk = float(currentValues[poloniexPair]["lowestAsk"])
		# Query Bittrex Prices
		summary=bittrexAPI.getmarketsummary(bittrexPair)
		bittrexAsk = summary[0]['Ask']
		bittrexBid = summary[0]['Bid']
		# Print Prices
		print('\nASKS: Poloniex @ {:.8f} | {:.8f} @ Bitrex\nBIDS: Poloniex @ {:.8f} | {:.8f} @ Bitrex'.format(poloAsk, bittrexAsk, poloBid, bittrexBid))

		# Get Balance Information, fake numbers if dryrun.
		if not args.dryrun:
			# Query Bittrex API
			bittrexTargetBalance = bittrexAPI.getbalance(targetCurrency)
			bittrexBaseBalance = bittrexAPI.getbalance(baseCurrency)
			# Query Poloniex API
			poloniexBalanceData = poloniexAPI.api_query('returnBalances')
			# Copy Poloniex Balance Variables
			poloniexTargetBalance = poloniexBalanceData[targetCurrency]
			poloniexBaseBalance = poloniexBalanceData[baseCurrency]
		else:
			# Faking Balance Numbers for Dryrun Simulation
			bittrexTargetBalance=100.0
			bittrexBaseBalance=100.0
			poloniexTargetBalance=100.0
			poloniexBaseBalance=100.0

		# Buy from Polo, Sell to Bittrex
		if (poloAsk<bittrexBid):
			trade(0, poloAsk, bittrexBid, bittrexTargetBalance, poloniexBaseBalance)
		# Sell to polo, Buy from Bittrex
		elif(bittrexAsk<poloBid):
			trade(1, bittrexAsk, poloBid, poloniexTargetBalance, bittrexBaseBalance)

		time.sleep(args.interval)


if __name__ == "__main__":
	main(sys.argv[1:])
