class InvestmentStrategyOptions:
    """
    (Tony, options objects always seem dumb at first, but I always wish I had
    them later)
    """

    def __init__(self):
        self.max_lot_size = None
        self.min_lot_size = None
        self.num_lots = None
        self.stock_picker = None
