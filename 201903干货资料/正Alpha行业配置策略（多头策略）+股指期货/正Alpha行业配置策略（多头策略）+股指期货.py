# 混合策略模版
import pandas as pd
import numpy as np
import datetime
# 初始化函数,全局只运行一次
def init(context):
    g.index = '000300.SH'
    # 设置基准收益：沪深300指数
    set_benchmark(g.index)
    # 打印日志
    log.info('策略开始运行,初始化函数全局只运行一次')
    #设立期货子账户,其中stock为7000000，future为3000000
    set_subportfolios([{"cash": 10000000, "type": 'stock'},{"cash": 1500000, "type": "future"}])
    # 设置股票每笔交易的手续费为万分之二(手续费在买卖成交后扣除,不包括税费,税费在卖出成交后扣除)
    set_commission(PerShare(type='stock',cost=0.0002))
    # 设置期货每笔交易的手续费为十万分之四十五(按成交额计算并扣除,期货交易不需要缴纳税费)
    set_commission(PerShare(type='future',cost=0.000045))
    # 设置股票交易滑点0.05%,表示买入价为实际价格乘1.005,卖出价为实际价格乘0.995
    set_slippage(PriceSlippage(0.0005),'stock')
    # 设置期货交易滑点0.05%,表示买入价为实际价格乘1.005,卖出价为实际价格乘0.995
    set_slippage(PriceSlippage(0.0005),'future')
    # 设置期货保证金,IF为期货合约,第一个参数做多保证金8%，第二个参数做空保证金9%
    set_margin_rate('IF',0.15,0.15)
    # 设置日级最大成交比例25%,分钟级最大成交比例50%
    # 日频运行时，下单数量超过当天真实成交量25%,则全部不成交
    # 分钟频运行时，下单数量超过当前分钟真实成交量50%,则全部不成交
    set_volume_limit(1,1)
    #记录天数，隔20个交易日调仓
    g.day = 0
    #市值监控字典
    g.market_value_dict = {'95':0,'90':0}
    #行业alpha监控
    g.industrydict = {'A':0,'B':0,'labe':0}
    g.tradeday = list(get_trade_days('20170101','20200202',None).strftime('%Y-%m-%d'))
#每日开盘前9:00被调用一次,用于储存自定义参数、全局变量,执行盘前选股等
def handle_bar(context, bar_dict):
    #股票跟踪部分
    #持仓市值
    market_value = context.portfolio.stock_account.market_value
    #总资产
    total_value = context.portfolio.stock_account.total_value
    #股票仓位
    stocklevel = market_value/total_value
    
    if stocklevel>0.95:
        g.market_value_dict['95']+=1 
        g.market_value_dict['90'] = 0
    elif stocklevel <0.9:
        g.market_value_dict['90']+=1 
        g.market_value_dict['95'] = 0
    elif stocklevel>=0.9 and stocklevel<=0.95:
        g.market_value_dict['90'] = 0
        g.market_value_dict['95'] = 0
        
    if stocklevel ==0:
        #字典更新
        g.market_value_dict = {'95':0,'90':0}
        #仓位
        df = industry_stocklevel(context,bar_dict)
        df['weight_alpha_industry'] = (df['weight_alpha_industry']/100)*0.95
        stocklist = list(df['symbol'])
        stocklist = [s for s in stocklist if bar_dict[s].is_paused==0]
        for s in stocklist:
            weight = df.loc[s].weight_alpha_industry  
            order_target_percent(s,weight)
    elif stocklevel>0.95 and g.market_value_dict['95']>10:
        #字典更新
        g.market_value_dict = {'95':0,'90':0}
        #仓位
        df = industry_stocklevel(context,bar_dict)
        df['weight_alpha_industry'] = (df['weight_alpha_industry']/100)*0.95
        stocklist = list(df['symbol'])
        stocklist = [s for s in stocklist if bar_dict[s].is_paused==0]
        for s in stocklist:
            weight = df.loc[s].weight_alpha_industry  
            order_target_percent(s,weight)
            
    elif stocklevel<0.9 and g.market_value_dict['90']>10:
        #字典更新
        g.market_value_dict = {'95':0,'90':0}
        #仓位
        df = industry_stocklevel(context,bar_dict)
        df['weight_alpha_industry'] = (df['weight_alpha_industry']/100)*0.925
        stocklist = list(df['symbol'])
        stocklist = [s for s in stocklist if bar_dict[s].is_paused==0]
        for s in stocklist:
            weight = df.loc[s].weight_alpha_industry  
            order_target_percent(s,weight)
    
    
    labe = g.industrydict['labe']
  
    df = industry_stocklevel(context,bar_dict)
    
    labe2 = g.industrydict['labe']
    
    if labe != labe2:
        print('行业风格变化,由{}转变成{}'.format(labe,labe2))
        df['weight_alpha_industry'] = (df['weight_alpha_industry']/100)*stocklevel
        stocklist = list(df['symbol'])
        stocklist = [s for s in stocklist if bar_dict[s].is_paused==0]
        for s in stocklist:
            weight = df.loc[s].weight_alpha_industry  
            order_target_percent(s,weight)
            
            
    
    #期货对冲部分
    #获取当前IF交易合约
    code = get_futures_dominate('IF')
    #订阅IF品种
    subscribe(code)
    date = get_last_datetime().strftime('%Y-%m-%d')
    #当前点位
    indexnum = get_price_future(code,date,date,'1d',['close']).close.values
    #beta计算
    beta = 1
    #计算需开空数量
    num = int(market_value*beta/(indexnum*300))
    #查询当前空单数量
    future_key = list(context.portfolio.future_account.positions.keys())
    
    if len(future_key)==0:
        renum =0 
    else:
        for d in future_key:
            renum = context.portfolio.future_account.positions[d].short_amount
    future_account = renum - num
    if future_account > 0:
        print('昨日空单{},目前需要{}，执行'.format(renum,num))
        #平空
        order_future(code,abs(future_account),"close","short",limit_price=None)
        print('平空{}手'.format(future_account))
    elif future_account < 0:
        print('昨日空单{},目前需要{}，执行'.format(renum,num))
        #开空
        order_future(code,abs(future_account),"open","short",limit_price=None)
        print('开空{}手'.format(future_account))
        
    holdcode = list(context.portfolio.future_account.positions.keys())

    if len(holdcode) >0:
        code = holdcode[0]
        date = get_datetime().strftime('%Y-%m-%d')
        day = get_security_info(code).end_date
        day = day.strftime('%Y-%m-%d')
        downday = g.tradeday[g.tradeday.index(day)-1]
        if date ==downday:
            print('合约转移操作')
            #转合约
            order_future(code,abs(renum),"close","short",limit_price=None)
            code = get_future_code('IF',date)[1]
            subscribe(code)
            order_future(code,abs(num),"open","short",limit_price=None)
        
    
'''
根据各行业 Alpha 与其它行业 Alpha 相关系数，
国信证券将24个行业分为两类
一类行业包括：采掘行业S21、金融行业S48,S49、房地产行业S43、有色金属S24、黑色金属和交运仓储S42。
其余所有行业为二类行业。
'''
def industry_stocklevel(context,bar_dict):
    import numpy as np
    import pandas as pd
    import statsmodels.api as sm
    #获取时间
    date = get_last_datetime().strftime('%Y-%m-%d')
    #获取指数成分股
    stocklist = get_index_stocks(g.index,date)
    #获取权重
    df = get_index_weight(g.index,date)
    #获取行业
    dt2,dt = get_sfactor_industry(date,date,stocklist,industry='s_industryid1')
    #行业标签
    df['industry'] = df['symbol'].apply(lambda x:dt[date][x] if x in list(dt[date].index) else 'S11')
    #行业alpha计算
    data = history(stocklist+[g.index],['quote_rate'],250,'1d',skip_paused=False,fq='pre',is_panel=1)['quote_rate']
    
    alphadict = {}
    g.betadict = []
    
    x = list(data[g.index])
    X = sm.add_constant(x)
    
    for s in stocklist:
        y = list(data[s])
        model = sm.OLS(y,X)
        results = model.fit()
        alpha = results.params[0]
        beta = results.params[1]
        from math import isnan
        if isnan(beta) == False:
            g.betadict.append(beta)
        alphadict[s] = alpha
        
    df['alpha'] = df['symbol'].apply(lambda x:alphadict[x] if x in list(alphadict.keys()) else 0)
    df['alpha'] = df['alpha']*df['weight']
    
    Aalpha = g.industrydict['A']
    Balpha = g.industrydict['B']
    
    #行业分类1类alpha
    Astock = df[(df['industry']=='S21')|(df['industry']=='S48')|(df['industry']=='S49')|(df['industry']=='S43')|(df['industry']=='S24')|(df['industry']=='S42')]
    Aalpha2 = Astock.mean().alpha
    #行业分类2类alpha
    Bstock = df[(df['industry']!='S21')&(df['industry']!='S48')&(df['industry']!='S49')&(df['industry']!='S43')&(df['industry']!='S24')&(df['industry']!='S42')]
    Balpha2 = Bstock.mean().alpha
    
    g.industrydict['A'] = Aalpha2
    g.industrydict['B'] = Balpha2
    
    if Aalpha ==0 and Balpha==0:
        if Aalpha2 >Balpha2:
            g.industrydict['labe'] = 'A'
            print('A行业alpha较大，进行超配')
        else:
            g.industrydict['labe'] = 'B'
            print('B行业alpha较大，进行超配')
            
    elif Aalpha<0 and Aalpha2>0 and Balpha*Balpha2>0:
        g.industrydict['labe'] = 'A'
        print('A行业alpha进入正值区间，进行超配')
    elif Balpha<0 and Balpha2>0 and Aalpha*Aalpha2>0:
        g.industrydict['labe'] = 'B'
        print('B行业alpha进入正值区间，进行超配')
        
    elif Aalpha*Aalpha2<0 and Balpha*Balpha2<0:
        if Aalpha2>Balpha2:
            g.industrydict['labe'] = 'A'
            print('AB行业alpha同时进入正值区间，A较大，进行超配')
        elif Aalpha2<Balpha2:
            g.industrydict['labe'] = 'B'
            print('AB行业alpha同时进入正值区间，B较大进行超配')
            
            
    if g.industrydict['labe']=='A':

        df['alpha_industry'] = df['industry'].apply(lambda x:1 if x in ['S21','S48','S49','S43','S24','S42'] else 0 )
        n = len(list(Astock['symbol']))
        df.index = df['symbol']
        #输出超配行业下的个股权重
        df['weight_alpha_industry'] = df['symbol'].apply(lambda x:0.7*df.loc[x].weight+30/n if df.loc[x].alpha_industry==1 else 0.7*df.loc[x].weight)
        return df
    elif g.industrydict['labe']=='B':

        df['alpha_industry'] = df['industry'].apply(lambda x:1 if x not in ['S21','S48','S49','S43','S24','S42'] else 0 )
        n = len(list(Bstock['symbol']))
        df.index = df['symbol']
        #输出超配行业下的个股权重
        df['weight_alpha_industry'] = df['symbol'].apply(lambda x:0.7*df.loc[x].weight+30/n if df.loc[x].alpha_industry==1 else 0.7*df.loc[x].weight)
        return df
#每日盘后15:00被调用一次,用于储存自定义参数、全局变量,执行盘前选股等
def after_trading(context):
    #天数记录+1
    g.day = g.day +1
    