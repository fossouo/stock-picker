import math
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data import Fundamentals
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.filters import Q1500US
from quantopian.pipeline.filters import morningstar as mstar
from quantopian.pipeline.factors import BusinessDaysSincePreviousEvent
from quantopian.pipeline.factors import Returns
from quantopian.pipeline.factors.fundamentals import MarketCap

from target_position import TargetPosition

class InvestmentStrategy:
    """
    For now, this is a port of almost everything we had in algo.py.  Later, 
    this will be broken out into smaller pieces
    """
    def __init__(self, options):
        self.options = options
        self.quarters_passed = 0

    def poke(self, context, data):
        self.reconcile_target_positions(context, data)

    def before_trading_start(self, context, data): 
        """
        There are certain things that quantopian only allows to happen before the start of the day
        """
        context.days += 1


        self.do_screening2(context, data)

        if self.quarter_passed(context):
            self.rebalance(context, data) 
            self.quarters_passed += 1
            
    def make_pipeline(self): 
    
        # Filter
        non_zero_market_cap = MarketCap() > 0
        non_zero_shares_outstanding = Fundamentals.shares_outstanding.latest > 0
        non_zero_free_cash_flow = Fundamentals.free_cash_flow.latest > 0
        non_zero_invested_capital = Fundamentals.invested_capital.latest > 0
        non_zero_cash = Fundamentals.cash_and_cash_equivalents.latest > 0
        non_equal_cash_and_invested = Fundamentals.cash_and_cash_equivalents.latest != Fundamentals.invested_capital.latest
    
        universe = (non_zero_market_cap & non_zero_shares_outstanding & non_zero_free_cash_flow & non_zero_invested_capital & non_zero_cash & non_equal_cash_and_invested)
    
        #       .filter((fundamentals.cash_flow_statement.financing_cash_flow / fundamentals.valuation.market_cap) < 0)
    
        stakeholder_yield = (Fundamentals.financing_cash_flow.latest / Fundamentals.market_cap.latest) < 0
    
        #       .filter((fundamentals.income_statement.operating_income / (fundamentals.balance_sheet.invested_capital - fundamentals.balance_sheet.cash_and_cash_equivalents)) > 0.20)
    
        roi_on_invested_captial = (Fundamentals.operating_income.latest / (Fundamentals.invested_capital.latest - Fundamentals.cash_and_cash_equivalents)) > 0.20
          
        #       .filter(fundamentals.cash_flow_statement.operating_cash_flow > fundamentals.income_statement.net_income)
                               
        earnings_quality = (Fundamentals.operating_cash_flow.latest > Fundamentals.net_income_income_statement)
    
                       
        #       .filter((fundamentals.valuation.enterprise_value / fundamentals.cash_flow_statement.free_cash_flow) < 15)
                        
        enterprise_value_to_cash_flow = (Fundamentals.enterprise_value.latest / Fundamentals.free_cash_flow) < 15
    
        top_75_percent_returns = Returns(window_length=130).percentile_between(25, 100)
    
        the_five_factors = (
            stakeholder_yield & 
            roi_on_invested_captial & 
            earnings_quality & 
            enterprise_value_to_cash_flow #& 
            #top_75_percent_returns
        )
     
        pipe = Pipeline(
            columns={
                'stakeholder_yield': stakeholder_yield,
                "roi_on_invested_captial": roi_on_invested_captial,
                "earnings_quality": earnings_quality,
                "enterprise_value_to_cash_flow": enterprise_value_to_cash_flow,
                "top_75_percent_returns": top_75_percent_returns,
                "returns": Returns(window_length=130)
            },
            screen = (the_five_factors & universe)
        )

        return pipe
    
    def do_screening2(self, context, data):
        
        output = pipeline_output('fivefactors')
        context.security_list = list(output.index)
        self.compute_relative_strength(context,data)
        passed_screening = [stock for stock in output.index if data.can_trade(stock)
                           and context.relative_strength_6m[stock] > -0.6745]

        new_stocks = set()
        for stock in passed_screening:
            count = context.screened_counts.get(stock, 0)
            if count == 0:
                new_stocks.add(stock)
            context.screened_counts[stock] = count + 1

        symbols = (stock.symbol for stock in passed_screening)
        # log.info("Today's picks: %s (%d new)" % (", ".join(symbols), len(new_stocks)))
        

    def do_screening(self, context, data):
        fundamental_df = get_fundamentals(
            query(
                fundamentals.asset_classification.morningstar_sector_code,
                fundamentals.company_reference.country_id,
                fundamentals.company_reference.primary_exchange_id,
                fundamentals.share_class_reference.is_depositary_receipt,
                fundamentals.share_class_reference.is_primary_share,
                fundamentals.cash_flow_statement.financing_cash_flow,
                fundamentals.valuation.market_cap,
                
                fundamentals.income_statement.operating_income,
                fundamentals.balance_sheet.invested_capital,
                fundamentals.balance_sheet.cash_and_cash_equivalents,
                
                fundamentals.cash_flow_statement.operating_cash_flow,
                fundamentals.income_statement.net_income,
                fundamentals.valuation.enterprise_value,
                fundamentals.cash_flow_statement.free_cash_flow
            )

            # No Financials (103) and Real Estate (104) Stocks, no ADR or PINK, only USA
            #.filter(fundamentals.asset_classification.morningstar_sector_code != 103)
            #.filter(fundamentals.company_reference.country_id == "USA")
            #.filter(fundamentals.asset_classification.morningstar_sector_code != 104)
            #.filter(fundamentals.share_class_reference.is_depositary_receipt == False)
            #.filter(fundamentals.share_class_reference.is_primary_share == True)
            #.filter(fundamentals.company_reference.primary_exchange_id != "OTCPK")
            
            # Check for data sanity (i,e. avoid division by zero)
            .filter(fundamentals.valuation.market_cap > 0)
            .filter(fundamentals.valuation.shares_outstanding > 0)
            .filter(fundamentals.cash_flow_statement.free_cash_flow > 0)
            .filter(fundamentals.balance_sheet.invested_capital > 0)
            .filter(fundamentals.balance_sheet.cash_and_cash_equivalents > 0)
            .filter(fundamentals.balance_sheet.invested_capital != fundamentals.balance_sheet.cash_and_cash_equivalents)
            
            .filter((fundamentals.cash_flow_statement.financing_cash_flow / fundamentals.valuation.market_cap) < 0)
            .filter((fundamentals.income_statement.operating_income / (fundamentals.balance_sheet.invested_capital - fundamentals.balance_sheet.cash_and_cash_equivalents)) > 0.20)
           
            .filter(fundamentals.cash_flow_statement.operating_cash_flow > fundamentals.income_statement.net_income)
            .filter((fundamentals.valuation.enterprise_value / fundamentals.cash_flow_statement.free_cash_flow) < 15)
            
            .limit(self.options.max_lot_size)
        )

        context.fundamental_df = fundamental_df
        context.security_list = list(fundamental_df.columns.values)

        self.compute_relative_strength(context, data)
       
        # Filter out stocks without data and apply the momentum criteria
        # -0.6745 is an approximation for the top three-quarters of the market
        passed_screening = [stock for stock in fundamental_df
                          if data.can_trade(stock) and context.relative_strength_6m[stock] > -0.6745]

        new_stocks = set()
        for stock in passed_screening:
            count = context.screened_counts.get(stock, 0)
            if count == 0:
                new_stocks.add(stock)
            context.screened_counts[stock] = count + 1

        symbols = (stock.symbol for stock in passed_screening)
        # log.info("Today's picks: %s (%d new)" % (", ".join(symbols), len(new_stocks)))
        
        
    def rebalance(self, context, data):
        """
            Exit all positions before starting new ones.
            Apply the Momentum Criteria
            Buy all stocks equally 
        """
        # Exit all positions before starting new ones
        context.target_positions = {}

        if len(context.screened_counts) == 0:
            log.info("No Stocks to buy")
            return

        screened_stocks = context.screened_counts

        self.log_symbol_value(screened_stocks)

        # Trim down to just the top desired number
        trimmed_stocks = self.trim_by_value(screened_stocks, self.options.max_lot_size)
        
        self.log_symbol_value(trimmed_stocks)

        weight_denominator = 0
        for stock, count in trimmed_stocks.iteritems():
            weight_denominator += count
       
        total_value = context.portfolio.portfolio_value

        for stock, count in trimmed_stocks.iteritems():
            if data.can_trade(stock):
                stock_price = data.current(stock, "price")
                division = float(count) / weight_denominator
                target_value = total_value * division
                number_shares = math.floor(target_value / stock_price)
                context.target_positions[stock] = TargetPosition(stock, number_shares)
            else:
                log.error("This shouldn't happen (%s)" % stock.symbol)
                
        # track how many positions we're holding
        record(num_positions = len(context.target_positions))

        # clear the stock counters
        context.screened_counts = {}

        log.info(", ".join(map(str,context.target_positions.itervalues())))
        
    def trim_by_value(self, stock_map, n):
        """
        Returns a new map with the top n stocks, according to the map's value.
        Natural sorting is used.
        """
        output = {} 
        # ( http://stackoverflow.com/a/7197643 )
        top_n_stocks = sorted(stock_map, key=stock_map.get, reverse=True)[:n]
        for stock in top_n_stocks:
            output[stock] = stock_map[stock]

        return output
            
    def log_symbol_value(self, stock_value_map):
        output = []

        for stock, value in stock_value_map.iteritems():
            output.append("%s: %d" % (stock.symbol, value))

        log.info(", ".join(output))
        
        
    # Actually places orders, trying to get us where we want to be
    def reconcile_target_positions(self, context, data):
        record(cash_balance = context.portfolio.cash)
        
        # First, sell off anything not being targeted
        selling = []
        for stock in context.portfolio.positions:
            if stock not in context.target_positions:
                if data.can_trade(stock):
                    order_target(stock, 0)
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
                order_target(target.stock, target.number_shares)
                
    # Like order_target, but tries not to spend more than the given amount.
    # Returns the order id and an estimate of cash spent
    def cash_sensitive_order_target(self, stock, number_shares, context, data, cash_available):
        order_id = None
        cash_spent = 0
        share_price = data.current(stock, "price")
        shares_to_buy = min(number_shares, math.floor(float(cash_available) / share_price))
        if (data.can_trade(stock)):
            order_id = order(stock, shares_to_buy)    
            cash_spent = share_price * shares_to_buy
            
        return order_id, cash_spent
        
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

    def quarter_passed(self,context): 
        """
        Screener results quarterly updated
        """
        return context.days % 63 == 0
