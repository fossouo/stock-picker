class StockPickerStrategy:
	"""
	At any given moment, this strategy should be able to give us a more-or-less
    ranked listing of what we should consider buying.
	"""
    def __init__(self, quant_api):
        self.quant_api = quant_api

    def pick_stocks(context, data, min_stocks, max_stocks):
		"""
		Pick stocks from scratch.  (Currently stores everything in context,
        which ought not to be. Also ignores min/max)
		"""
        self.do_screening(context)
        context.security_list = list(context.fundamental_df.columns.values)
        self.compute_relative_strength(context, data)

    def do_screening(self, context):
        f = self.quant_api.fundamentals

        fundamentals_query = self.quant_api.query(
            f.asset_classification.morningstar_sector_code,
            f.company_reference.country_id,
            f.company_reference.primary_exchange_id,
            f.share_class_reference.is_depositary_receipt,
            f.share_class_reference.is_primary_share,
            f.cash_flow_statement.financing_cash_flow,
            f.valuation.market_cap,

            f.income_statement.operating_income,
            f.balance_sheet.invested_capital,
            f.balance_sheet.cash_and_cash_equivalents,

            f.cash_flow_statement.operating_cash_flow,
            f.income_statement.net_income,
            f.valuation.enterprise_value,
            f.cash_flow_statement.free_cash_flow
        )

        # No Financials (103) and Real Estate (104) Stocks, no ADR or PINK, only USA
        #.filter(f.asset_classification.morningstar_sector_code != 103)
        #.filter(f.company_reference.country_id == "USA")
        #.filter(f.asset_classification.morningstar_sector_code != 104)
        #.filter(f.share_class_reference.is_depositary_receipt == False)
        #.filter(f.share_class_reference.is_primary_share == True)
        #.filter(f.company_reference.primary_exchange_id != "OTCPK")

        # Check for data sanity (i,e. avoid division by zero)
        .filter(f.valuation.market_cap > 0)
        .filter(f.valuation.shares_outstanding > 0)
        .filter(f.cash_flow_statement.free_cash_flow > 0)
        .filter(f.balance_sheet.invested_capital > 0)
        .filter(f.balance_sheet.cash_and_cash_equivalents > 0)
        .filter(f.balance_sheet.invested_capital != f.balance_sheet.cash_and_cash_equivalents)

        .filter((f.cash_flow_statement.financing_cash_flow / f.valuation.market_cap) < 0)
        .filter((f.income_statement.operating_income / (f.balance_sheet.invested_capital - f.balance_sheet.cash_and_cash_equivalents)) > 0.20)

        .filter(f.cash_flow_statement.operating_cash_flow > f.income_statement.net_income)
        .filter((f.valuation.enterprise_value / f.cash_flow_statement.free_cash_flow) < 15)

        .limit(self.options.max_lot_size)

        fundamental_df = self.quant_api.get_fundamentals(fundamentals_query)

         # Update context
        context.stocks = [stock for stock in fundamental_df]
        context.fundamental_df = fundamental_df


	def compute_relative_strength(self, context, data):
        prices = data.history(context.security_list + [symbol('SPY')], 'price', 150, '1d')
        # Price % change in the last 6 months
        pct_change = (prices.ix[-130] - prices.ix[0]) / prices.ix[0]

        pct_change_spy = pct_change[symbol('SPY')]
        pct_change = pct_change - pct_change_spy
        if pct_change_spy != 0:
            pct_change = pct_change / abs(pct_change_spy)
        pct_change = pct_change.drop(symbol('SPY'))
        context.relative_strength_6m = pct_change

        # Filter out stocks without data and apply the momentum criteria
        # -0.6745 is an approximation for the top three-quarters of the market
        context.stocks = [stock for stock in context.stocks
        	if data.can_trade(stock) and context.relative_strength_6m[stock] > -0.6745]


