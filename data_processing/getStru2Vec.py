import pickle
import multiprocessing
import json
import argparse
from typing import List, Tuple, Callable, Any
from python_structured import python_query_parse, python_code_parse, python_context_parse
from sqlang_structured import sqlang_query_parse, sqlang_code_parse, sqlang_context_parse


# 批量解析Python查询数据
def multipro_python_query(data_list: List[str]) -> List[Any]:
    return [python_query_parse(line) for line in data_list]


# 批量解析Python代码数据
def multipro_python_code(data_list: List[str]) -> List[Any]:
    return [python_code_parse(line) for line in data_list]


# 批量解析Python上下文数据
def multipro_python_context(data_list: List[str]) -> List[Any]:
    result = []
    for line in data_list:
        if line == '-10000':
            result.append(['-10000'])
            # 每个字符串元素，若等于特定标记'-10000'，就将这个标记作为列表添加到结果中
        else:
            result.append(python_context_parse(line))
            # 若不等于'-10000'，就用python_context_parse函数来解析它，并将解析结果添加到结果列表中
    return result


# 批量解析SQL查询数据
def multipro_sqlang_query(data_list: List[str]) -> List[Any]:
    return [sqlang_query_parse(line) for line in data_list]


# 批量解析SQL代码数据
def multipro_sqlang_code(data_list: List[str]) -> List[Any]:
    return [sqlang_code_parse(line) for line in data_list]


# 批量解析SQL上下文数据
def multipro_sqlang_context(data_list: List[str]) -> List[Any]:
    result = []
    for line in data_list:
        if line == '-10000':
            result.append(['-10000'])
        else:
            result.append(sqlang_context_parse(line))
    return result


# 多进程解析上下文、查询和代码数据。
def parse(data_list: List[str], split_num: int, context_func: Callable, query_func: Callable, code_func: Callable) -> Tuple[List[Any], List[Any], List[Any]]:
    pool = multiprocessing.Pool() # 多进程池

    # 将输入的字符串列表分割成一定长度的子列表
    split_list = [data_list[i:i + split_num] for i in range(0, len(data_list), split_num)]

    # 并行处理每个子列表，分别使用context_func、query_func、code_func函数，并将结果展开成一个列表
    context_data = [item for sublist in pool.map(context_func, split_list) for item in sublist]
    query_data = [item for sublist in pool.map(query_func, split_list) for item in sublist]
    code_data = [item for sublist in pool.map(code_func, split_list) for item in sublist]

    pool.close()
    pool.join()

    return context_data, query_data, code_data


# 处理和保存数据
def main(split_num: int, source_path: str, save_path: str, context_func: Callable, query_func: Callable, code_func: Callable) -> None:
    try:
        with open(source_path, 'rb') as f:
            corpus_lis = pickle.load(f)

        context_data, query_data, code_data = parse(corpus_lis, split_num, context_func, query_func, code_func)
        qids = [item[0] for item in corpus_lis] # 提取每个项目的ID，构建一个ID列表
        total_data = [[qids[i], context_data[i], code_data[i], query_data[i]] for i in range(len(qids))] # 将ID、上下文数据、代码数据和查询数据组合成新的列表

        with open(save_path, 'wb') as f:
            pickle.dump(total_data, f)
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == '__main__':
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='Process and save data.')
    parser.add_argument('lang_type', type=str, help='Language type, e.g. "python" or "sql"')
    parser.add_argument('split_num', type=int, help='Number to split the data')

    args = parser.parse_args()

    # 读取配置文件
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

    lang_config = config[args.lang_type]

    # 此处使用配置文件中的路径
    if args.lang_type == 'python':
        source_path = lang_config['serialization_paths'][2][0]
        save_path = lang_config['serialization_paths'][2][1]

        main(args.lang_type, args.split_num, source_path, save_path,
             multipro_python_context, multipro_python_query, multipro_python_code)

    elif args.lang_type == 'sql':
        source_path = lang_config['serialization_paths'][2][0]
        save_path = lang_config['serialization_paths'][2][1]

        main(args.lang_type, args.split_num, source_path, save_path,
             multipro_sqlang_context, multipro_sqlang_query, multipro_sqlang_code)

