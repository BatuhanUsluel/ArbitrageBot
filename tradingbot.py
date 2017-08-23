#!/usr/bin/env python
#Imports
import logging
import argparse
import time
import sys
from poloniex import poloniex
from bittrex import bittrex
def main(argv):
	# User Settings
	poloniexKey = 'POLONIEX_API_KEY'
	poloniexSecret = 'POLONIEX_API_SECRET'
	bittrexKey = 'BITTREX_API_KEY'
	bittrexSecret = 'BITTREX_API_SECRET'

	# Setup Argument Parser
	parser = argparse.ArgumentParser(description='Poloniex/Bittrex Arbitrage Bot')
	parser.add_argument('-s', '--symbol', default='XMR', type=str, required=False, help='symbol of your target coin [default: XMR]')
	parser.add_argument('-b', '--basesymbol', default='BTC', type=str, required=False, help='symbol of your base coin [default: BTC]')
	parser.add_argument('-r', '--rate', default=1.0, type=float, required=False, help='minimum price difference [default: 1.0]')
	parser.add_argument('-i', '--interval', default=1, type=int, required=False, help='seconds to sleep between loops [default: 1]')
	parser.add_argument('-l', '--logfile', default='arbbot.log', type=str, required=False, help='file to output log data to [default: arbbot.log]')
	parser.add_argument('-d', '--dryrun', action='store_true', required=False, help='simulates without trading (API keys not required)')
	parser.add_argument('-v', '--verbose', action='store_true', required=False, help='enables extra console messages (for debugging)')
	args = parser.parse_args()

	# Create Logger
	logger = logging.getLogger()
	logger.setLevel(logging.DEBUG)
	# Create console handler and set level to debug
	ch = logging.StreamHandler()
	ch.setLevel(logging.DEBUG)
	# Create file handler and set level to debug
	fh = logging.FileHandler(args.logfile, mode='a', encoding=None, delay=False)
	fh.setLevel(logging.DEBUG)
	# Create formatter
	formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
	# Add formatter to handlers
	ch.setFormatter(formatter)
	fh.setFormatter(formatter)
	# Add handlers to logger
	logger.addHandler(ch)
	logger.addHandler(fh)

	# Load Configuration
	targetCurrency = args.symbol
	baseCurrency = args.basesymbol

	# Log Startup Settings
	logger.info('Arb Pair: {}/{} | Rate: {} | Interval: {}'.format(baseCurrency, targetCurrency, args.rate, args.interval))
	if args.dryrun:
		logger.info("Dryrun Mode Enabled (will not trade)")

	# Pair Strings for accessing API responses
	bittrexPair = '{0}-{1}'.format(baseCurrency, targetCurrency)
	poloniexPair = '{0}_{1}'.format(baseCurrency, targetCurrency)

	# Create Exchange API Objects
	bittrexAPI = bittrex(poloniexKey, poloniexSecret)
	poloniexAPI = poloniex(bittrexKey, bittrexSecret)

	# Trade Function
	def trade(_buyExchange, _ask, _bid, _srcBalance, _buyBalance):
		# _buyExchange:
		# 0 = Poloniex
		# 1 = Bittrex
		arbitrage = _bid/_ask
		# Return if minumum arbitrage percentage is not met
		if (arbitrage <= args.rate):
			return
		elif (_buyExchange == 0):
			buyExchangeString = 'Poloniex'
			sellExchangeString = 'Bittrex'
			sellbook = poloniexAPI.returnOrderBook(poloniexPair)["asks"][0][1]
			buybook = bittrexAPI.getorderbook(bittrexPair, "sell")[0]["Quantity"]
		elif (_buyExchange == 1):
			buyExchangeString = 'Bittrex'
			sellExchangeString = 'Poloniex'
			buybook = poloniexAPI.returnOrderBook(poloniexPair)["bids"][0][1]
			sellbook = bittrexAPI.getorderbook(bittrexPair, "sell")[0]["Quantity"]

		logger.info('OPPORTUNITY: BUY @ ' + buyExchangeString + ' | SELL @ ' + sellExchangeString + ' | RATE: ' + str(arbitrage) + '%')

		#Find minimum order size
		tradesize = min(sellbook, buybook)

		#Setting order size incase balance not enough
		if (_srcBalance < tradesize):
			tradesize = _srcBalance

		if ((tradesize*_ask) > _buyBalance):
			tradesize = _buyBalance / _ask

		#Check if above min order size
		if ((tradesize*_bid)>0.0005001):
			logger.info("ORDER {}\nSELL: {}	| {} @ {:.8f} (Balance: {})\nBUY: {}	| {} @ {:.8f} (Balance: {})".format(bittrexPair, sellExchangeString, tradesize, _bid, _srcBalance, buyExchangeString, tradesize, _ask, _buyBalance))
			#Execute order
			if not args.dryrun:
				if (_buyExchange == 0):
					bittrexAPI.selllimit(bittrexPair, tradesize, _bid)
					orderNumber = poloniexAPI.buy(poloniexPair, _ask, tradesize)
				elif (_buyExchange == 1):
					bittrexAPI.buylimit(bittrexPair, tradesize, _ask)
					orderNumber = poloniexAPI.sell(poloniexPair, _bid, tradesize)
			else:
				logger.info("Dryrun: skipping order")
		else:
			logger.warning("Order size not above min order size, no trade was executed")

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
