from investment_strategy import InvestmentStrategy
from investment_strategy_options import InvestmentStrategyOptions
from stock_picker_strategy import StockPickerStrategy
from quantopian_api import QuantopianAPI

def before_trading_start(context, data):
    """
    Every market morning, quantopian gives us some time to pull down and
    analyze the fundamentals.
    """
    context.strategy.before_trading_start(context, data)

def morning_action(context, data):
    """
    Every market morning, we poke the strategy and let it do things.
    """
    context.strategy.poke(context, data)
    

def initialize(context):
    """
    This is where quantopian starts running code.
    """

    quant_api = QuantopianAPI()
    
    options = InvestmentStrategyOptions()
    options.max_lot_size = 20
    options.min_lot_size = 10
    options.num_lots = 4
    options.stock_picker = StockPickerStrategy(quant_api)
    context.strategy = InvestmentStrategy(options, quant_api)

    # These few things should end up inside the investment strategy soon.
    context.days=0
    context.target_positions={}

    set_slippage(slippage.FixedSlippage(spread=0))
    set_commission(commission.PerTrade(cost=0))
    schedule_function(morning_action,
        date_rules.every_day(),
        time_rules.market_open(hours=0, minutes = 1))

