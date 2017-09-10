#!/usr/bin/env python
#Imports
import logging
import argparse
import time
import sys

from poloniex import poloniex
from bittrex import bittrex
try:
	# For Python 3+
	from configparser import ConfigParser, NoSectionError
except ImportError:
	# Fallback to Python 2.7
	from ConfigParser import ConfigParser, NoSectionError
def main(argv):
	# Setup Argument Parser
	parser = argparse.ArgumentParser(description='Poloniex/Bittrex Arbitrage Bot')
	parser.add_argument('-s', '--symbol', default='XMR', type=str, required=False, help='symbol of your target coin [default: XMR]')
	parser.add_argument('-b', '--basesymbol', default='BTC', type=str, required=False, help='symbol of your base coin [default: BTC]')
	parser.add_argument('-r', '--rate', default=1.01, type=float, required=False, help='minimum price difference, 1.01 is 1 percent price difference (exchanges charge .05 percent fee) [default: 1.01]')
	parser.add_argument('-m', '--max', default=0.0, type=float, required=False, help='maximum order size in target currency (0.0 is unlimited) [default: 0.0]')
	parser.add_argument('-i', '--interval', default=1, type=int, required=False, help='seconds to sleep between loops [default: 1]')
	parser.add_argument('-c', '--config', default='arbbot.conf', type=str, required=False, help='config file [default: arbbot.conf]')
	parser.add_argument('-l', '--logfile', default='arbbot.log', type=str, required=False, help='file to output log data to [default: arbbot.log]')
	parser.add_argument('-d', '--dryrun', action='store_true', required=False, help='simulates without trading (API keys not required)')
	parser.add_argument('-v', '--verbose', action='store_true', required=False, help='enables extra console messages (for debugging)')
	args = parser.parse_args()

	# Load Configuration
	targetCurrency = args.symbol
	baseCurrency = args.basesymbol
	# Pair Strings for accessing API responses
	bittrexPair = '{0}-{1}'.format(baseCurrency, targetCurrency)
	poloniexPair = '{0}_{1}'.format(baseCurrency, targetCurrency)

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

	# Load Config File
	config = ConfigParser()
	try:
		config.read(args.config)
		poloniexKey = config.get('ArbBot', 'poloniexKey')
		poloniexSecret = config.get('ArbBot', 'poloniexSecret')
		bittrexKey = config.get('ArbBot', 'bittrexKey')
		bittrexSecret = config.get('ArbBot', 'bittrexSecret')
	except NoSectionError:
		logger.warning('No Config File Found! Running in Drymode!')
		args.dryrun = True
		poloniexKey = 'POLONIEX_API_KEY'
		poloniexSecret = 'POLONIEX_API_SECRET'
		bittrexKey = 'BITTREX_API_KEY'
		bittrexSecret = 'BITTREX_API_SECRET'
		config.add_section('ArbBot')
		config.set('ArbBot', 'poloniexKey', poloniexKey)
		config.set('ArbBot', 'poloniexSecret', poloniexSecret)
		config.set('ArbBot', 'bittrexKey', bittrexKey)
		config.set('ArbBot', 'bittrexSecret', bittrexSecret)
		try:
			with open(args.config, 'w') as configfile:
				config.write(configfile)
		except IOError:
			logger.error('Failed to create and/or write to {}'.format(args.config))

	# Log Startup Settings
	logger.info('Arb Pair: {} | Rate: {} | Interval: {} | Max Order Size: {}'.format(bittrexPair, args.rate, args.interval, args.max))
	if args.dryrun:
		logger.info("Dryrun Mode Enabled (will not trade)")

	# Create Exchange API Objects
	bittrexAPI = bittrex(bittrexKey, bittrexSecret)
	poloniexAPI = poloniex(poloniexKey, poloniexSecret)
	def quit():
		logger.info('KeyboardInterrupt, quitting!')
		sys.exit()

	# Trade Function
	def trade(_buyExchange, _ask, _bid, _sellBalance, _buyBalance):
		# _buyExchange:
		# 0 = Poloniex
		# 1 = Bittrex
		arbitrage = _bid/_ask
		# Return if minumum arbitrage percentage is not met
		print('DEBUG: Current Rate: {} | Minimum Rate: {}'.format(arbitrage, args.rate))
		if arbitrage <= args.rate:
			return
		elif _buyExchange == 0:
			buyExchangeString = 'Poloniex'
			sellExchangeString = 'Bittrex'

			# Load Sellbook from Poloniex, Fail Gracefully
			try:
				sellbook = poloniexAPI.returnOrderBook(poloniexPair)["asks"][0][1]
			except KeyboardInterrupt:
				quit()
			except:
				logger.error('Failed to get Poloniex Asks for {}, skipping order attempt'.format(poloniexPair))
				return

			# Load Buybook from Bittrex, Fail Gracefully
			try:
				buybook = bittrexAPI.getorderbook(bittrexPair, "buy")[0]["Quantity"]
			except KeyboardInterrupt:
				quit()
			except:
				logger.error('Failed to get Bittrex Asks for {}, skipping order attempt'.format(poloniexPair))
				return
		elif _buyExchange == 1:
			buyExchangeString = 'Bittrex'
			sellExchangeString = 'Poloniex'

			# Load Buybook from Poloniex, Fail Gracefully
			try:
				buybook = poloniexAPI.returnOrderBook(poloniexPair)["bids"][0][1]
			except KeyboardInterrupt:
				quit()
			except:
				logger.error('Failed to get Bittrex Bids for {}, skipping order attempt'.format(poloniexPair))
				return

			# Load Sellbook from Bittrex, Fail Gracefully
			try:
				sellbook = bittrexAPI.getorderbook(bittrexPair, "sell")[0]["Quantity"]
			except KeyboardInterrupt:
				quit()
			except:
				logger.error('Failed to get Bittrex Asks for {}, skipping order attempt'.format(poloniexPair))
				return

		logger.info('OPPORTUNITY: BUY @ ' + buyExchangeString + ' | SELL @ ' + sellExchangeString + ' | RATE: ' + str(arbitrage) + '%')

		#Find minimum order size
		tradesize = min(sellbook, buybook)

		#Setting order size incase balance not enough
		if _sellBalance < tradesize:
			logger.info('Tradesize ({}) larger than sell balance ({} @ {}), lowering tradesize.'.format(tradesize, _sellBalance, sellExchangeString))
			tradesize = _sellBalance

		if (tradesize*_ask) > _buyBalance:
			newTradesize = _buyBalance / _ask
			logger.info('Tradesize ({}) larger than buy balance ({} @ {}), lowering tradesize to {}.'.format(tradesize, _buyBalance, buyExchangeString, newTradesize))
			tradesize = newTradesize

		if args.max >= 0.0 and tradesize > args.max:
			logger.debug('Tradesize ({}) larger than maximum ({}), lowering tradesize.'.format(tradesize, args.max))
			tradesize = args.max

		#Check if above min order size
		if (tradesize*_bid) > 0.0005001:
			logger.info("ORDER {}\nSELL: {}	| {} @ {:.8f} (Balance: {})\nBUY: {}	| {} @ {:.8f} (Balance: {})".format(bittrexPair, sellExchangeString, tradesize, _bid, _sellBalance, buyExchangeString, tradesize, _ask, _buyBalance))
			#Execute order
			if not args.dryrun:
				if _buyExchange == 0:
					bittrexAPI.selllimit(bittrexPair, tradesize, _bid)
					orderNumber = poloniexAPI.buy(poloniexPair, _ask, tradesize)
				elif _buyExchange == 1:
					bittrexAPI.buylimit(bittrexPair, tradesize, _ask)
					orderNumber = poloniexAPI.sell(poloniexPair, _bid, tradesize)
			else:
				logger.info("Dryrun: skipping order")
		else:
			logger.warning("Order size not above min order size, no trade was executed")

	# Main Loop
	while True:
		# Query Poloniex Prices
		try:
			currentValues = poloniexAPI.api_query("returnTicker")
		except KeyboardInterrupt:
			quit()
		except:
			logger.error('Failed to Query Poloniex API, Restarting Loop')
			continue
		poloBid = float(currentValues[poloniexPair]["highestBid"])
		poloAsk = float(currentValues[poloniexPair]["lowestAsk"])
		# Query Bittrex Prices
		try:
			summary=bittrexAPI.getmarketsummary(bittrexPair)
		except KeyboardInterrupt:
			quit()
		except:
			logger.error('Failed to Query Bittrex API, Restarting Loop')
			continue
		bittrexAsk = summary[0]['Ask']
		bittrexBid = summary[0]['Bid']
		# Print Prices
		print('\nASKS: Poloniex @ {:.8f} | {:.8f} @ Bitrex\nBIDS: Poloniex @ {:.8f} | {:.8f} @ Bitrex'.format(poloAsk, bittrexAsk, poloBid, bittrexBid))

		# Get Balance Information, fake numbers if dryrun.
		if not args.dryrun:
			# Query Bittrex API
			try:
				bittrexTargetBalance = bittrexAPI.getbalance(targetCurrency)
			except KeyboardInterrupt:
				quit()
			except:
				logger.error('Failed to Query Bittrex for {} Balance, Restarting Loop'.format(targetCurrency))
				continue
			try:
				bittrexBaseBalance = bittrexAPI.getbalance(baseCurrency)
			except KeyboardInterrupt:
				quit()
			except:
				logger.error('Failed to Query Bittrex for {} Balance, Restarting Loop'.format(baseCurrency))
				continue

			# Query Poloniex API
			try:
				poloniexBalanceData = poloniexAPI.api_query('returnBalances')
			except KeyboardInterrupt:
				quit()
			except:
				logger.error('Failed to Query Poloniex for Balance Data, Restarting Loop'.format(baseCurrency))
				continue
			
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
		if poloAsk < bittrexBid:
			trade(0, poloAsk, bittrexBid, bittrexTargetBalance, poloniexBaseBalance)
		# Sell to polo, Buy from Bittrex
		if bittrexAsk < poloBid:
			trade(1, bittrexAsk, poloBid, poloniexTargetBalance, bittrexBaseBalance)

		time.sleep(args.interval)


if __name__ == "__main__":
	main(sys.argv[1:])
