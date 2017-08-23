# ArbitrageBot
![alt text](https://investorjunkie.com/wp-content/uploads/2011/02/arbitrage-cufflinks.gif)

Coded for python2.7+

```
usage: arbbot.py [-h] [-s SYMBOL] [-b BASESYMBOL] [-r RATE] [-i INTERVAL]
                 [-l LOGFILE] [-d] [-v]

Poloniex/Bittrex Arbitrage Bot

optional arguments:

  -h, --help            show this help message and exit
  -s SYMBOL, --symbol SYMBOL
                        symbol of your target coin [default: XMR]
  -b BASESYMBOL, --basesymbol BASESYMBOL
                        symbol of your base coin [default: BTC]
  -r RATE, --rate RATE  minimum price difference, 1.01 is 1 percent price
                        difference (exchanges charge .05 percent fee)
                        [default: 1.01]
  -i INTERVAL, --interval INTERVAL
                        seconds to sleep between loops [default: 1]
  -l LOGFILE, --logfile LOGFILE
                        file to output log data to [default: arbbot.log]
  -d, --dryrun          simulates without trading (API keys not required)
  -v, --verbose         enables extra console messages (for debugging)
```

When finished the bot will check both markets for their bids and asks. If the bittrex bid is higher than the poloniex ask, it will buy from the ask on poloniex, and sell to the bid on bittrex to make a % of profit. Same goes for the opposite. The bot will also have to check the order sizes.
