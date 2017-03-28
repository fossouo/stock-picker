from lot_position import LotPosition

class SymbolLockError(Exception):
    """
    Raised when we try to lock a symbol that's being traded already.  We only
    want one thing to trade a symbol at a time.
    """
    pass

class PositionManager():
    """
    All orders are placed via an instance of this.  We could get away without
    this, except that we need to be able to track seperate positions for the
    same security, to support our lots.
    """

    def __init__():
        self.symbol_locks = set()
        self.buy_positions = []
        self.hold_positions = []
        self.sell_positions = []

    def lock_symbol(self, symbol):
        if symbol in self.symbol_locks:
            raise SymbolLockError("Symbol '%s' already locked." % symbol)
        self.symbol_locks.add(symbol)

    def unlock_symbol(self, symbol):
        if symbol not in self.symbol_locks:
            raise SymbolLockError("Symbol '%s' cannot be unlocked." % symbol)
        self.symbol_locks.remove(symbol)

    def order(self, symbol, num_shares):
        """
        Initializes a new positions and places an order to fill it.
        """
        self.lock_symbol(symbol)
        
        position = LotPosition(symbol, num_shares)
        self.positions.append(position)
        self.poke_position(position)
        return position

    def poke_buy_position(self, position):
        """
        Check on a position.  If we need to place a buy order, do so.
        """

        cash_available = context.portfolio.cash
            existing_share_count = context.portfolio.positions[target.stock].amount
            desired_share_count = target.number_shares
            share_count_difference = desired_share_count - existing_share_count

            # If we have more to buy, we can't backfill
            if share_count_difference > 0:
                can_invest_extra_cash = False
                order_id, cash_spent = self.cash_sensitive_order_target(target.stock, target.number_shares, context, data, cash_available)
                cash_available -= cash_spent


	# Actually places orders, trying to get us where we want to be
    def reconcile_target_positions(self, context, data):
        # First, sell off anything not being targeted
        selling = []
        for stock in context.portfolio.positions:
            if stock not in context.target_positions:
                if data.can_trade(stock):
                    self.quant_api.order_target(stock, 0)
                    selling.append(stock.symbol)

        if len(selling) > 0:
            log.info("Trying to sell: %s" % ", ".join(selling))



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
