"""
    Patrick O'Shaughnessy - Millennial Money
    
    1. Stakeholder yield < 5%. Stakeholder yield = Cash from financing 12m / Market Cap Q1
    2. ROIC > 20%
       ROIC = operating_income /  (invested_capital - cash)
    3. CFO > Net Income (Earnings Quality)
    4. EV/FCF < 15 (Value)
    5. 6M Relative Strength top three-quarters of the market. 
       6M Relative Strength = 6M Stock Total Return / 6M Total Return S&P500 (Momentum)
       
    The positions are updated quarterly.
"""

import math
import pandas as pd
import numpy as np

# Called by framework
def initialize(context):
    set_slippage(slippage.FixedSlippage(spread=0))
    set_commission(commission.PerTrade(cost=0))
    context.max_num_stocks = 50
    context.days = 0
    context.quarter_days = 65
    context.relative_strength_6m = {}
    context.target_positions = {}
    schedule_function(func=reconcile_target_positions, date_rule=date_rules.every_day())
          
def quarter_passed(context): 
    """
    Screener results quarterly updated
    """
    return context.days % context.quarter_days == 0

# Called by framework
def before_trading_start(context, data): 
    context.days += 1
    
    if not quarter_passed(context):
        return
    
    do_screening(context)
    context.security_list = list(context.fundamental_df.columns.values)
    compute_relative_strength(context, data)
    rebalance(context, data)
    
def do_screening(context):
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
        
        .filter((fundamentals.cash_flow_statement.financing_cash_flow / fundamentals.valuation.market_cap) < 0.05)
        .filter((fundamentals.income_statement.operating_income / (fundamentals.balance_sheet.invested_capital - fundamentals.balance_sheet.cash_and_cash_equivalents)) > 0.20)
       
        .filter(fundamentals.cash_flow_statement.operating_cash_flow > fundamentals.income_statement.net_income)
        .filter((fundamentals.valuation.enterprise_value / fundamentals.cash_flow_statement.free_cash_flow) < 15)
        
        .limit(context.max_num_stocks)
    )
   
     # Update context
    context.stocks = [stock for stock in fundamental_df]
    context.fundamental_df = fundamental_df
    
    
def rebalance(context, data):
    """
        Exit all positions before starting new ones.
        Apply the Momentum Criteria
        Buy all stocks equally 
    """
    # Exit all positions before starting new ones
    context.target_positions = {}

    # Filter out stocks without data and apply the momentum criteria
    # -0.6745 is an approximation for the top three-quarters of the market
    context.stocks = [stock for stock in context.stocks
                      if data.can_trade(stock) and context.relative_strength_6m[stock] > -0.6745]
   
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
    record(num_positions = len(context.target_positions))
    
# Actually places orders, trying to get us where we want to be
def reconcile_target_positions(context, data):
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
            order_id, cash_spent = cash_sensitive_order_target(target.stock, target.number_shares, context, data, cash_available)
            cash_available -= cash_spent
        elif share_count_difference < 0:
            log.info("Selling because %d - %d = %d" % (existing_share_count, desired_share_count, share_count_difference))
            order_target(target.stock, target.number_shares)
            
# Like order_target, but tries not to spend more than the given amount.
# Returns the order id and an estimate of cash spent
def cash_sensitive_order_target(stock, number_shares, context, data, cash_available):
    order_id = None
    cash_spent = 0
    share_price = data.current(stock, "price")
    shares_to_buy = min(number_shares, math.floor(float(cash_available) / share_price))
    if (data.can_trade(stock)):
        order_id = order(stock, shares_to_buy)    
        cash_spent = share_price * shares_to_buy
        
    return order_id, cash_spent
    
def compute_relative_strength(context, data):   
    prices = data.history(context.security_list + [symbol('SPY')], 'price', 150, '1d')
    # Price % change in the last 6 months
    pct_change = (prices.ix[-130] - prices.ix[0]) / prices.ix[0]
    
    pct_change_spy = pct_change[symbol('SPY')]
    pct_change = pct_change - pct_change_spy
    if pct_change_spy != 0:
        pct_change = pct_change / abs(pct_change_spy)
    pct_change = pct_change.drop(symbol('SPY'))
    context.relative_strength_6m = pct_change
    
class TargetPosition:
    def __init__(self, stock, number_shares):
        self.stock = stock
        self.number_shares = number_shares

