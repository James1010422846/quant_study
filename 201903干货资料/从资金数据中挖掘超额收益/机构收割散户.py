#初始化函数,全局只运行一次
def init(context):	
    #基准指数代码
    g.indexcode = '000016.SH'
    #设置基准收益
    set_benchmark(g.indexcode)
    #获取交易日列表
    tradelist = list(get_trade_days("20130101", "20200102", count=None).strftime('%Y%m%d'))
    #月历
    g.mtradelist = time(tradelist)
#日运行
def handle_bar(context, bar_dict):
    #获取日期
    date = get_datetime().strftime('%Y%m%d')
    #月历判断
    if date in g.mtradelist:
        #清仓
        for s in list(context.portfolio.stock_account.positions.keys()):
            order_target(s,0)
        #调仓月末
        enddate = get_last_datetime().strftime('%Y%m%d')
        #获取当日沪深300指数成份股
        stocklist = get_index_stocks(g.indexcode, date)
        #全市场中非ST非停牌个股列表
        goldstock = [stock for stock in stocklist if not bar_dict[stock].is_st and not bar_dict[stock].is_paused]
        #获取资金数据
        factorname = 'factor'
        factordf = get_money_flow_step(goldstock,
                                   None,
                                   enddate,
                                   '1d',
                                   ['buy_l','sell_l','act_buy_xl','act_sell_xl','dde_l','net_flow_rate','l_net_value'],
                                   20,
                                   is_panel=1).fillna(0)
        factordf[factorname] = (factordf['sell_l'].fillna(0)-factordf['buy_l'].fillna(0)).rank(axis=1,ascending = False)+(factordf['act_buy_xl'].fillna(0)-factordf['act_sell_xl'].fillna(0)).rank(axis=1,ascending = False)

        buystock = list(factordf[factorname].sum().sort_values(ascending= True).index)[:int((len(goldstock)*0.2))]
        cash = context.portfolio.stock_account.available_cash /len(buystock)
        for s in buystock:
            order_value(s,cash)
#月历函数
def time(tradelist):
    mtradelist = []
    for s in range(0,len(tradelist)):
        if s == len(tradelist)-1:
            break
        if (tradelist[s+1][4:6]>tradelist[s][4:6]) or (tradelist[s+1][4:6]=='01' and tradelist[s][4:6]=='12'):
            mtradelist.append(tradelist[s])
    return mtradelist

        
    

    
    
