class TargetPosition:
    def __init__(self, stock, number_shares):
        self.stock = stock
        self.number_shares = number_shares

    def __str__(self):
        return "%s (%s): %d shares" % (self.stock.asset_name, self.stock.symbol, self.number_shares)
