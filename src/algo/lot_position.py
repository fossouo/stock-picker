class LotPosition():
    """
    Fills the same role as a Quantopian position object, except that we might
    have multiple positions in the same security.

    Should be a fairly dumb object, controled by a position manager of some sort.
    """

    def __init__(self, symbol, num_shares):
        self.symbol = symbol
        self.initial_num_shares_target = num_shares
        self.num_shares = 0
        self.cost_basis = None

        self.order = None
