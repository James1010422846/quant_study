import pandas as pd 
import numpy as np
# 初始化函数,全局只运行一次
def init(context):
    # K线形态定义
    g.data = szzj()
    g.day = 0
    g.tc = 20
    g.num = 5

def handle_bar(context, bar_dict):
    if g.day %g.tc == 0:
        
        s1 = list(context.portfolio.stock_account.positions.keys())
        for s  in s1:
            order_target(s,0)
            
        date = get_last_datetime().strftime('%Y%m%d')
    
        stocklist = get_index_stocks('000905.SH',date)
        stocklist = [stock for stock in stocklist if not bar_dict[stock].is_st and not bar_dict[stock].is_paused]
        data = history(stocklist,['open','high','low','close'],60,'1d',skip_paused=False,fq='pre',is_panel=1)
 
        
        closedf = data['close'].fillna(0)
        opendf = data['open'].fillna(0)
        highdf = data['high'].fillna(0)
        lowdf = data['low'].fillna(0)
        
        dt = pd.DataFrame(columns=['stock','startdate','enddate','T'])
        stocklist = list(closedf.columns)
        y=0
        for s in stocklist:
            corropen = round(np.corrcoef(g.data[1],opendf[s])[0][1],3)
            corrhigh = round(np.corrcoef(g.data[2],highdf[s])[0][1],3)
            corrlow = round(np.corrcoef(g.data[3],lowdf[s])[0][1],3)
            corrclose = round(np.corrcoef(g.data[0],closedf[s])[0][1],3)
            # 综合值
            T = (corropen+corrhigh+corrlow+corrclose)/4
            startdate = '20181109'
            enddate = '20190211'
            dt.loc[y] = [s,startdate,enddate,T]
            y+=1
        dt = dt.fillna(0)
        dt = dt.sort_values(by='T',ascending=False)
        for s in range(0,g.num):
            q = dt.iloc[s].stock
            order_target_percent(q,1/g.num)

    g.day +=1

def szzj():
    # 上涨中继形态
    data = get_price('002359.SZ',None,'20190118','1d',['open','high','low','close'],bar_count=60,is_panel =1)
    close1 = data['close']
    open1 = data['open']
    high1 = data['high']
    low1 = data['low']    
    return (close1,open1,high1,low1)