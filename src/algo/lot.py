class Lot:
    """
    A lot is a collection of investments for the purposes of bookkeeping them
    together as a single investment.  This way, if we lose money on one of the
    sets of stocks chosen by the stock picker, we can count those loses
    together properly.  This is especially important if different lots happen
    to share some of the same securities.

    For the first pass, we're putting more logic in here than we probably
    should.  Responsibilities of this class include Lot Lifecycle, the actual
    buying, selling, and optimisation thereof.
    
    The only outside assumption we rely on is that no two Lots are in the
    BUYING or SELLING stages simultaniously.  We need this because we're
    relying on the global position data to derive changes in our local position
    state. (Meaning actual counting of shared owned, cost basis, etc.)
    """

    # Python 2 doesn't have enumerated types.  This will do.
    INIT = "init"
    BUYING = "buying"
    HOLDING = "holding"
    SELLING = "selling"
    FINISHED = "finished"


    def __init__(name, start_datetime, quant_api):
        self.name = name
        self.start_datetime = start_datetime
        self.target_end_datetime = start_datetime + datetime.timedelta(365)
		self.quant_api = quant_api
        self.state = self.INIT
        self.positions = []


    def is_active(self):
        """
        Active means buying or selling.  We don't want more than one lot to be
        active at a time.
        """
        return self.state in (self.BUYING, self.SELLING)


    def is_time_to_sell(self, today):
        return self.state is self.HOLDING and today > self.target_end_datetime


	def start_buying(self, positions, amount):
        """
        Sets up buy orders for each position, up to amount.
        """

        if len(positions) == 0:
            log.info("No Stocks to buy")
            return

        total_weight = reduce(
            lambda total, position: total + position.target_weight,
            positions, 0)

        for target_position in positions:
            stock = self.quant_api.symbol(target_position.symbol)
            stock_price = data.current(stock, "price")
            relative_weight = float(target_position.target_weight) / total_weight
            target_value = amount * relative_weight
            num_shares = math.floor(target_value / stock_price)

            position = self.position_manager.order(target_position.symbol, num_shares)
            self.positions.append(position)

        self.state = self.BUYING
