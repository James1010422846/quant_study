import pandas as pd
# 初始化函数,全局只运行一次
def init(context):
    
	#调仓频率
	g.tradestep = 20
	#记录运行天数
	g.runday = 0 
	#股票组合持仓数量
	g.holdnum = 10
	
#每日开盘前9:00被调用一次
def before_trading(context):
    #判断是否调仓
    if g.runday%g.tradestep !=0:
	    return None
	#获取日期
    date = get_last_datetime().strftime('%Y-%m-%d')
    data = get_stylefactor(date, date, 'exposure',is_panel=1)[date]
    data['num'] = data['earnings_yield']-data['size']
    # 指标排序
    data = pd.DataFrame(data).sort_values(by ='num', ascending=False)
    #选取排序在前的股票，构建股票组合
    context.stock = list(data.index)[:g.holdnum]
    
## 开盘时运行函数
def handle_bar(context, bar_dict):
    #判断是否调仓
    if g.runday%g.tradestep !=0:
	    return None
	#获取账户持仓
    holdstock = list(context.portfolio.stock_account.positions.keys())
    #股票组合调出
    sellstock = list(set(holdstock) - set(context.stock))
    #清仓
    for s in sellstock:
        order_target(s,0)
    #股票组合调入
    buystock = list(set(context.stock) - set(holdstock))
    cash = 	context.portfolio.stock_account.available_cash/len(buystock)
    #买入
    for s in buystock:
        order_value(s,cash)
## 收盘后运行函数,用于储存自定义参数、全局变量,执行盘后选股等 
def after_trading(context):
	#运行天数+1 
	g.runday += 1
	# 获取时间
	time = get_datetime().strftime('%Y-%m-%d %H:%M:%S')
	# 打印时间
	log.info('{} 盘后运行'.format(time))
	log.info('一天结束')
	