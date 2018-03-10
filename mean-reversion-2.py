#Import necessary functions like Pipeline that will build the stocks we want to trade, or Returns that calculates our returns.
import numpy as np
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline.factors import SimpleMovingAverage, AverageDollarVolume, Returns
from quantopian.pipeline.data.builtin import USEquityPricing

def initialize(context):
    #Define the long (expecting price to go up) and short (expecting the price to go down) leverage (leverage is borrowing money to increase potential returns on invesment at a greater risk).
    #Decreasing long_leverage, for example, would  decrease the amount of longs bought.
    #Positive means buy, negative means sell
    context.long_leverage = 0.5
    context.short_leverage = -0.5
    
    #Set the number of days back in which we calculate the returns
    context.returns_lookback = 5
    
    #Create a pipeline to be used for our longs and shorts
    pipe = Pipeline()
    attach_pipeline(pipe, 'my_pipeline')
  
    #Create the dollar_volume factor that is used to determine which stocks to buy
    dollar_volume = AverageDollarVolume(window_length=30)
    pipe.add(dollar_volume, 'dollar_volume')
    
    #Create recent_returns factor that calculates the returns for the past 5 days
    recent_returns = Returns(window_length=context.returns_lookback)
    pipe.add(recent_returns, 'recent_returns')
    
    #Define what stocks we're looking at: the top 1% of stocks defined by avergae daily trading volume (the most traded stocks on the market)
    high_dollar_volume = dollar_volume.percentile_between(99,100)
    
    #Of that 1% of most traded stocks, the bottom 10% will be our shorts, and the top 10% will be the longs.
    low_returns = recent_returns.percentile_between(0,10,mask=high_dollar_volume) 
    high_returns = recent_returns.percentile_between(90,100,mask=high_dollar_volume) 
    
    #Add our stocks to our pipeline
    pipe.add(low_returns, 'low_returns')
    pipe.add(high_returns, 'high_returns')

    #Rebalance every Monday at 11 PM Central each week
    schedule_function(rebalance, 
                      date_rules.week_start(days_offset=0), 
                      time_rules.market_open(hours = 1, minutes = 0))
#Called every time we trade. 
def handle_data(context, data):
    
    #Create the variable of what we want to record
    longs = shorts = 0
    
    #The for loop that calculates how many longs and shorts we have
    for position in context.portfolio.positions.itervalues():
        if position.amount > 0:
            longs += 1
        if position.amount < 0:
            shorts += 1
    
    #Record the number of shorts and longs in the portfolio over time, as well as the leverage
    record(leverage=context.account.leverage, long_count=longs, short_counts=shorts)
    
#Run before each day starts
def before_trading_start(context, data):
    
    #Get pipeline output (that has all of our paramters to what stocks we will be trading)
    context.output = pipeline_output('my_pipeline')   
    
    #Set the securities that we want to long
    context.long_secs = context.output[context.output['low_returns']]
    #Set the securities that we want to short
    context.short_secs = context.output[context.output['high_returns']]
    
    #Create a list of the securities that we are using for this trading day
    context.security_list = context.long_secs.index.union(context.short_secs.index).tolist()
    context.security_set = set(context.security_list)
#Called once every trading day, defined in our initialize() function
def rebalance(context, data):
    
    #Set even weights among the stocks. For each stock in a short or long position, this weight will determine what percentage of the portfolio the stock is allowed
    context.long_weight = context.long_leverage / len(context.long_secs)
    context.short_weight = context.short_leverage / len(context.short_secs)

    #Loop through each stock that we are trading today.
    for stock in context.security_list:
        if data.can_trade(stock):
            
            #If the stock is a long, buy that stock according to its designated weight (which will be a percent and positive)
            if stock in context.long_secs.index:
                order_target_percent(stock, context.long_weight)
                
            #If the stock is a short, sell that stock according to its weight (which will be a percent and negative)
            elif stock in context.short_secs.index:
                order_target_percent(stock, context.short_weight)
                
    #Else, close any securities that were not longs or shorts, say if they fell out of our top 1% of trade volume
    for stock in context.portfolio.positions:
        if stock not in context.security_set and data.can_trade(stock):
            order_target_percent(stock , 0)
      
    #Log the shorts and longs for the week to be displayed everyday we trade 
    log.info("This week's longs: "+", ".join([long_.symbol for long_ in context.long_secs.index]))
    log.info("This week's shorts: "+", ".join([short_.symbol for short_ in context.short_secs.index]))