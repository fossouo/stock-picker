import math
from target_position import TargetPosition

class InvestmentStrategy:
    """
    Responsible for using the stock picker to create lots of securities, and
    for managing the lifecycle of those lots.
    """
    def __init__(self, options, quant_api):
        self.options = options
        self.quant_api = quant_api
        self.ideal_lot_interval = timedelta(365 / options.num_lots)

        self.active_lots = []
        self.latest_lot = None
        self.trading_lot = None

    def poke(self, context, data):
        #TODO
        pass

    def before_trading_start(self, context, data): 
        """
        If needed, determines what the best investments of the day are, and
        stores that information in context.
        """

        if not self.is_time_for_new_lot():
            return

        context.todays_picks = self.options.stock_picker.pick_stocks(
            context,
            data,
            min_stocks=self.options.min_lot_size,
            max_stocks=self.options.max_lot_size)

    def is_time_for_new_lot():
        """
        Deciding when to start a new lot could includes some spacing thoughts
        as well asideas around whether or not all Robinhood cash is settled.
        """
        num_active_lots = len(self.active_lots)
        if num_active_lots == 0:
            return True

        elif num_active_lots < self.options.num_lots and (self.today() - self.latest_lot.start_datetime) >= self.ideal_lot_interval:
            return True

        return False
