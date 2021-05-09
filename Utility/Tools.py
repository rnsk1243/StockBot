from Logging import MyLogging as mylog
from itertools import combinations
import numpy as np
import json

logger = mylog.MyLogging(class_name="BackTest", thread_num=1)


def get_stock_combination(target_list, split_target_list, combi_r):
    """
    listをsplit_target_list数に分けて、分けたリストでcombi_r数分抽出の全場合の数をリターンする。
    :param target_list:ターゲットリスト
    :param split_target_list:リスト分割数
    :param combi_r:分割リストから何個抽出するか
    :return:全場合の数 List[tuple]
    """

    stock_list = list(np.array_split(target_list, split_target_list))
    combination_list = []
    for tmp_list in stock_list:
        combination_list.append(list(combinations(tmp_list, combi_r)))

    return combination_list

def write_json(path, path2, naiyou):
    try:
        if type(naiyou) is not dict:
            print(f"naiyouはdict typeを使ってください。 type:{type(naiyou)}")
            return

        with open(path, 'r', encoding='utf-8') as my_read_json:
            open_json = json.load(my_read_json)
            update_json = open_json[path2]
            update_json.update(**naiyou)
            open_json[path2] = update_json

        with open(path, 'w', encoding='utf-8') as my_write_json:
            json.dump(open_json, my_write_json, indent="\t", ensure_ascii=False)

    except FileNotFoundError as e:
        logger.write_log(f"{path}ファイルを見つかりません。 {str(e)}", log_lv=3)

    except Exception as e:
        logger.write_log(f"Exception occured : {str(e)}", log_lv=5)

