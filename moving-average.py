#Initalize function is necessary to retrieve any data that will be used, such as our security information. Only called once.
def initialize(context):
    set_symbol_lookup_date('2016-01-01') #To distinguish between older company.
    context.security = symbol('SPY')
    
    schedule_function(rebalance, 
                      date_rules.week_start(days_offset=0), 
                      time_rules.market_open(hours = 1, minutes = 0))
    
#Function that runs the algorithm every minute.  
#def handle_data(context, data):
def rebalance(context, data):   
    #Calculates the stock's moving average for the last 5 number of days, and its current price.
    mavg = data.history(context.security, 'price', bar_count=5, frequency='1d').mean()
    
    #Gives the current price 
    current_price = data.current(context.security, 'price')
    
    #Gives the current amount of cash in my portfolio.
    cash = context.portfolio.cash
    
    percent = mavg*0.01
    
    #How many shares I can buy.
    #number_of_shares = (cash/current_price)
    
    #If stock price is 1% greater than average price, buy shares according to how much cash I have.
    if context.portfolio.returns == 0.05:
        order_target_percent(context.security, -1)
    else:
        if current_price > percent*mavg and cash > current_price:
            #Buy as much shares as possible
            order_target_percent(context.security, 1)
            #Log when we buy the shares
            log.info("Buying %s" % (context.security.symbol))
        
        elif current_price < mavg:
            #Sell all shares
            order_target_percent(context.security, -1)
            #Log current price.
            log.info("Selling %s" % (context.security.symbol))
        
    #Record the current price to be seen on the custom graph    
    record(price=current_price)