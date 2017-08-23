# ArbitrageBot
![alt text](https://investorjunkie.com/wp-content/uploads/2011/02/arbitrage-cufflinks.gif)

Coded for python2.7+

Input coin name(Example: ETH), Delay Between each check(in seconds), and the minimum arbitrage(101=1% Min Arb).

When finished the bot will check both markets for their bids and asks. If the bittrex bid is higher than the poloniex ask, it will buy from the ask on poloniex, and sell to the bid on bittrex to make a % of profit. Same goes for the opposite. The bot will also have to check the order sizes.
