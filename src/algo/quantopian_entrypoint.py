from quantopian.algorithm import attach_pipeline, pipeline_output
from investment_strategy import InvestmentStrategy
from investment_strategy_options import InvestmentStrategyOptions

def morning_action(context, data):
    """
    Every market morning, we provide the strategy with market data and let it
    do things.
    """
    context.strategy.poke(context, data)
    

def initialize(context):
    """
    This is where quantopian starts running code.
    """

    options = InvestmentStrategyOptions()
    options.max_lot_size = 10
    options.min_lot_size = 10
    options.num_lots = 4
    context.strategy = InvestmentStrategy(options)
    
    pipeline = context.strategy.make_pipeline()
    attach_pipeline(pipeline, 'fivefactors')

    # These few things should end up inside the investment strategy soon.
    context.days=0
    context.target_positions={}
    context.screened_counts={}

    set_slippage(slippage.FixedSlippage(spread=0))
    set_commission(commission.PerTrade(cost=0))
    schedule_function(morning_action,
        date_rules.every_day(),
        time_rules.market_open(hours=0, minutes = 1))


def before_trading_start(context, data):
    context.strategy.before_trading_start(context,data)
