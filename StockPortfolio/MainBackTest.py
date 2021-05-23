import sys
sys.path.append('../')
import time
from StockPortfolio import BackSimulation as bs
from StockPortfolio import BackTestFindOptimalMACD as btf

args = sys.argv

if args[1] == '--mode=client':
    start_time = time.time()

    arg_mode = 1
    arg_Re_Find_Optimal = "0"
    arg_months_ago = 6
    arg_for_months = 3
    arg_simulation_months_ago = arg_months_ago - arg_for_months
    arg_is_init = False
    arg_is_plot = False
    arg_plot_stock_name = None
    arg_random_range = 100
    arg_akirame = 2000
    arg_move_term = None

    if arg_simulation_months_ago == arg_for_months:
        arg_for_months = 0

    # myBackTestFindOptimalMACD = btf.BackTestFindOptimalMACD(months_ago=arg_months_ago, for_months=arg_for_months)
    myBackSimulation = bs.BackSimulation(months_ago=arg_simulation_months_ago, for_months=arg_for_months)

    slow_d_buy = 10
    slow_d_sell = 75
    myBackSimulation.simulation(mode=arg_mode,
                                is_plot=arg_is_plot,
                                plot_stock_name=arg_plot_stock_name,
                                move_term=arg_move_term,
                                slow_d_buy=slow_d_buy,
                                slow_d_sell=slow_d_sell)

    # if arg_simulation_months_ago == arg_for_months:
    #     arg_for_months = 0
    #
    # myBackSimulation = bs.BackSimulation(months_ago=arg_simulation_months_ago, for_months=arg_for_months)
    #
    # result = False
    # if arg_Re_Find_Optimal == "1":
    #     result = myBackTestFindOptimalMACD.update_MACD(is_init=arg_is_init,
    #                                                    is_plot=arg_is_plot,
    #                                                    plot_stock_name=arg_plot_stock_name,
    #                                                    random_range=arg_random_range,
    #                                                    akirame=arg_akirame,
    #                                                    move_term=arg_move_term)
    #
    # if result is True or arg_Re_Find_Optimal == "0":
    #     myBackSimulation.simulation(mode=arg_mode,
    #                                 is_plot=arg_is_plot,
    #                                 plot_stock_name=arg_plot_stock_name,
    #                                 move_term=arg_move_term)

    print(f"time = {time.time() - start_time}")


if __name__ == '__main__':
    start_time = time.time()

    arg_mode = int(args[1])
    arg_months_ago = int(args[2])
    arg_for_months = int(args[3])
    if args[4] == "1":
        arg_is_plot = True
    else:
        arg_is_plot = False
    if args[5] == "":
        arg_plot_stock_name = None
    else:
        arg_plot_stock_name = args[5]
    arg_move_term = 20

    arg_simulation_months_ago = arg_months_ago - arg_for_months
    if arg_simulation_months_ago == arg_for_months:
        arg_for_months = 0


    if arg_mode == 2: # 最適値 mode

        arg_Re_Find_Optimal = args[6]
        if args[7] == "1":
            arg_is_init = True
        else:
            arg_is_init = False

        arg_random_range = int(args[8])
        arg_akirame = int(args[9])


        myBackTestFindOptimalMACD = btf.BackTestFindOptimalMACD(months_ago=arg_months_ago,
                                                                for_months=arg_simulation_months_ago)
        result = False

        if arg_Re_Find_Optimal == "1":
            result = myBackTestFindOptimalMACD.update_MACD(is_init=arg_is_init,
                                                           is_plot=arg_is_plot,
                                                           plot_stock_name=arg_plot_stock_name,
                                                           random_range=arg_random_range,
                                                           akirame=arg_akirame,
                                                           move_term=arg_move_term)

        if result is True or arg_Re_Find_Optimal == "0":
            myBackSimulation = bs.BackSimulation(months_ago=arg_simulation_months_ago, for_months=arg_for_months)
            arg_mode = 3
            myBackSimulation.simulation(mode=arg_mode,
                                        is_plot=arg_is_plot,
                                        plot_stock_name=arg_plot_stock_name,
                                        move_term=arg_move_term)

    elif arg_mode == 1:  # nomal mode or rsi mode
        slow_d_buy = int(args[6])
        slow_d_sell = int(args[7])
        myBackSimulation = bs.BackSimulation(months_ago=arg_months_ago, for_months=arg_simulation_months_ago)
        myBackSimulation.simulation(mode=arg_mode,
                                    is_plot=arg_is_plot,
                                    plot_stock_name=arg_plot_stock_name,
                                    move_term=arg_move_term,
                                    slow_d_buy=slow_d_buy,
                                    slow_d_sell=slow_d_sell)

    elif arg_mode == 3:
        myBackSimulation = bs.BackSimulation(months_ago=arg_months_ago, for_months=arg_simulation_months_ago)
        myBackSimulation.simulation(mode=arg_mode,
                                    is_plot=arg_is_plot,
                                    plot_stock_name=arg_plot_stock_name,
                                    move_term=arg_move_term)

    print(f"time = {time.time() - start_time}")