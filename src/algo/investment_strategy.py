import math
from lot import Lot

class InvestmentStrategy:
    """
    Responsible for using the stock picker to create lots of securities, and
    for managing the lifecycle of those lots.
    """
    def __init__(self, options, quant_api):
        self.options = options
        self.quant_api = quant_api
        self.lot_interval = timedelta(365 / options.num_lots)
        self.lots = []

        self.reset_daily_data()


    def poke(self, context, data):
        """
        Let the strategy run for a tick.  If any lots need to do anything, poke
        them, and create a new lot if it's that time.

        We only want one lot to be active at a time.  "Active" should mean that
        it's in the process of buying or selling off.
        """
        active_lot = self.get_active_lot()
        if active_lot is not None:
            active_lot.poke()

        elif self.is_time_to_sell_lot():
            get_lot_to_sell().poke()
        
        elif self.is_time_for_new_lot():
            lot = Lot(self.today, self.quant_api)
            lot.set_target_positions(self.todays_picks, context, data)
            lot.poke()


    def before_trading_start(self, context, data): 
        """
        If needed, determines what the best investments of the day are, and
        stores that information in context.
        """

        self.reset_daily_data()

        if not self.is_time_for_new_lot():
            return

        self.todays_picks = self.options.stock_picker.pick_stocks(
            context, data, self.options.min_lot_size, self.options.max_lot_size)


    def is_time_to_sell_lot(self):
        """
        Let's us know if there's a lot that thinks it's time to sell.
        """
        return self.get_lot_to_sell() is not None


    def get_lot_to_sell(self):
        """
        Which lot thinks it's time to sell?
        """
        return next((lot for lot in self.lots if lot.is_time_to_sell(self.today)))


    def is_time_for_new_lot(self):
        """
        Deciding when to start a new lot could includes some spacing thoughts
        as well as ideas around whether or not all Robinhood cash is settled.
        """
        num_lots = len(self.lots)
        if num_lots == 0:
            return True

        elif num_lots < self.options.num_lots
                and (self.today - self.latest_lot.start_datetime) >= self.lot_interval:
            return True

        return False
        

    def reset_daily_data(self):
        """
        Updates things like the current day, among other things.
        """
        self.today = self.quant_api.get_datetime("US/Eastern")
        self.todays_picks = []
        self.last_started_lot = None

        last = None
        for lot in self.lots:
            if lot.status is Lot.HOLDING
                    and (last is None or lot.start_datetime > last.start_datetime):
                last = lot

        self.last_started_lot = last
