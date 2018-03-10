# Cloned from another user, this is NOT original work
from sklearn.ensemble import RandomForestClassifier
import numpy as np
import pandas as pd
from pytz import timezone
from scipy import stats

trading_freq = 20 # trading frequency, days

def initialize(context):
    context.stocks = [ sid(19662),  # XLY Consumer Discrectionary SPDR Fund
                       sid(19656),  # XLF Financial SPDR Fund
                       sid(19658),  # XLK Technology SPDR Fund
                       sid(19655),  # XLE Energy SPDR Fund
                       sid(19661),  # XLV Health Care SPRD Fund
                       sid(19657),  # XLI Industrial SPDR Fund
                       sid(19659),  # XLP Consumer Staples SPDR Fund
                       sid(19654),  # XLB Materials SPDR Fund
                       sid(19660),  # XLU Utilities SPRD Fund
                       sid(8554) ]  # SPY SPDR S&P 500 ETF Trust
    
    context.classifier = RandomForestClassifier() # Use a random forest classifier
    
    context.prediction = np.ones_like(context.stocks[0:-1])
    
    set_commission(commission.PerShare(cost=0.013, min_trade_cost=1.3))
    
    context.day_count = -1
    
    context.allocation = -1.0*np.ones_like(context.stocks[0:-1])
    
    context.prices = pd.DataFame()
    
def handle_data(context, data):
    
    # Trade only once per day
    loc_dt = get_datetime().astimezone(timezone('US/Eastern'))
    if loc_dt.hour == 16 and loc_dt.minute == 0:
        context.day_count += 1
        pass
    else:
        return
    
    # Limit trading frequency
    if context.day_count % trading_freq != 0.0:
        return
    
    prices = history(20,'1d','price').as_matrix(context.stocks)
    
    changes_all = stats.zscore(prices, axis=0, ddof=1)
    changes = changes_all[:,0:-1] - np.tile(changes_all[:,-1],(len(context.stocks)-1,1)).T
    record(changes_med = np.median(changes))
    changes = changes > np.median(changes)    
        
    for k in range(len(context.stocks)-1):
        
        X = np.split(changes[:,k],20)
        Y = X[-1]
        
        context.classifier.fit(X, Y) # Generate the model
        
        context.prediction[k] = context.classifier.predict(Y)
    
    allocation = context.prediction.astype(float)
    denom = np.sum(allocation)
    if denom != 0.0:
        allocation = allocation/np.sum(allocation)
    
    # return if allocation unchanged
    if np.array_equal(context.allocation,allocation):
        return     
    
    context.allocation = allocation
    
    for stock,percent in zip(context.stocks[0:-1],allocation):
        order_target_percent(stock,percent)