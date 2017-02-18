class Lot:
    """
    A lot is a collection of investments for the purposes of bookkeeping them
    together as a single investment.  This way, if we lose money on one of the
    sets of stocks chosen by the stock picker, we can count those loses
    together properly.  This is especially important if different lots happen
    to share some of the same securities.
    """

    def __init__(name, start_datetime, quant_api):
        self.name = name
        self.start_datetime = start_datetime
		self.quant_api = quant_api


	def set_target_positions(self, context, data):
        """
        Buy all stocks equally 
        """
        # Exit all positions before starting new ones
        context.target_positions = {}

        if len(context.stocks) == 0:
            log.info("No Stocks to buy")
            return

        division = min(1, 1.0/len(context.stocks))
        total_value = context.portfolio.portfolio_value
        value_per_division = total_value * division

        log.info("Current Value: %0.f Targeting position of $%0.f for each of %s (%d stocks)" % (total_value, value_per_division, ', '.join(stock.symbol for stock in context.stocks), len(context.stocks)))

        # buy all stocks equally
        for stock in context.stocks:
            if data.can_trade(stock):
                stock_price = data.current(stock, "price")
                number_shares = math.floor(value_per_division / stock_price)
                context.target_positions[stock] = TargetPosition(stock, number_shares)
            else:
                log.error("This shouldn't happen (%s)" % stock.symbol)

        # track how many positions we're holding
        self.quant_api.record(num_positions = len(context.target_positions))


	# Actually places orders, trying to get us where we want to be
    def reconcile_target_positions(self, context, data):
        self.quant_api.record(cash_balance = context.portfolio.cash)

        # First, sell off anything not being targeted
        selling = []
        for stock in context.portfolio.positions:
            if stock not in context.target_positions:
                if data.can_trade(stock):
                    self.quant_api.order_target(stock, 0)
                    selling.append(stock.symbol)

        if len(selling) > 0:
            log.info("Trying to sell: %s" % ", ".join(selling))

        # Then go through and try to meet the targets we've set.  We need to manually keep track of what cash is on hand so we don't over-reach
        cash_available = context.portfolio.cash
        can_invest_extra_cash = True
        for target in context.target_positions.itervalues():
            existing_share_count = context.portfolio.positions[target.stock].amount
            desired_share_count = target.number_shares
            share_count_difference = desired_share_count - existing_share_count

            # If we have more to buy, we can't backfill
            if share_count_difference > 0:
                can_invest_extra_cash = False
                order_id, cash_spent = self.cash_sensitive_order_target(target.stock, target.number_shares, context, data, cash_available)
                cash_available -= cash_spent
            elif share_count_difference < 0:
                log.info("Selling because %d - %d = %d" % (existing_share_count, desired_share_count, share_count_difference))
                self.quant_api.order_target(target.stock, target.number_shares)


	# Like order_target, but tries not to spend more than the given amount.
    # Returns the order id and an estimate of cash spent
    def cash_sensitive_order_target(self, stock, number_shares, context, data, cash_available):
        order_id = None
        cash_spent = 0
        share_price = data.current(stock, "price")
        shares_to_buy = min(number_shares, math.floor(float(cash_available) / share_price))
        if (data.can_trade(stock)):
            order_id = self.quant_api.order(stock, shares_to_buy)
            cash_spent = share_price * shares_to_buy

        return order_id, cash_spent
