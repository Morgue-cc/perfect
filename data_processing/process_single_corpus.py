import pickle
import json
from collections import Counter


# 从指定的pickle文件中加载数据
def load_pickle(filename):
    with open(filename, 'rb') as f:
        data = pickle.load(f, encoding='iso-8859-1')
    return data


# 根据问题ID将数据分为单一和多重问题集
def split_data(total_data, qids):
    result = Counter(qids)
    total_data_single = [data for data in total_data if result[data[0][0]] == 1]
    total_data_multiple = [data for data in total_data if result[data[0][0]] > 1]
    return total_data_single, total_data_multiple


# 处理STAQC数据集，将其分为单一和多重问题集并保存
def data_staqc_processing(filepath, save_single_path, save_multiple_path):
    with open(filepath, 'r', encoding='utf-8') as f:
        total_data = f.read()
    total_data = eval(total_data)
    qids = [data[0][0] for data in total_data]
    total_data_single, total_data_multiple = split_data(total_data, qids)

    with open(save_single_path, "w", encoding='utf-8') as f:
        f.write(str(total_data_single))
    with open(save_multiple_path, "w", encoding='utf-8') as f:
        f.write(str(total_data_multiple))


# 处理大型数据集，将其分为单一和多重问题集并保存
def data_large_processing(filepath, save_single_path, save_multiple_path):
    total_data = load_pickle(filepath)
    qids = [data[0][0] for data in total_data]
    total_data_single, total_data_multiple = split_data(total_data, qids)

    with open(save_single_path, 'wb') as f:
        pickle.dump(total_data_single, f)
    with open(save_multiple_path, 'wb') as f:
        pickle.dump(total_data_multiple, f)


# 将单一问题数据集标记为已标记，并按问题ID排序
def single_unlabeled_to_labeled(input_path, output_path):
    total_data = load_pickle(input_path)
    labeled_data = sorted([[data[0], 1] for data in total_data], key=lambda x: (x[0], x[1]))

    with open(output_path, "w", encoding='utf-8') as f:
        f.write(str(labeled_data))


if __name__ == "__main__":
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

        # STAQC Python 数据处理
        staqc_python_path = config['python']['staqc_path']
        staqc_python_single_save = config['python']['staqc_single_save']
        staqc_python_multiple_save = config['python']['staqc_multiple_save']
        data_staqc_processing(staqc_python_path, staqc_python_single_save, staqc_python_multiple_save)

        # STAQC SQL 数据处理
        staqc_sql_path = config['sql']['staqc_path']
        staqc_sql_single_save = config['sql']['staqc_single_save']
        staqc_sql_multiple_save = config['sql']['staqc_multiple_save']
        data_staqc_processing(staqc_sql_path, staqc_sql_single_save, staqc_sql_multiple_save)

        # 大型 Python 数据处理
        large_python_path = config['python']['large_path']
        large_python_single_save = config['python']['large_single_save']
        large_python_multiple_save = config['python']['large_multiple_save']
        data_large_processing(large_python_path, large_python_single_save, large_python_multiple_save)

        # 大型 SQL 数据处理
        large_sql_path = config['sql']['large_path']
        large_sql_single_save = config['sql']['large_single_save']
        large_sql_multiple_save = config['sql']['large_multiple_save']
        data_large_processing(large_sql_path, large_sql_single_save, large_sql_multiple_save)

        # 单一问题数据集标记
        large_sql_single_label_save = config['sql']['large_single_label_save']
        large_python_single_label_save = config['python']['large_single_label_save']
        single_unlabeled_to_labeled(large_sql_single_save, large_sql_single_label_save)
        single_unlabeled_to_labeled(large_python_single_save, large_python_single_label_save)