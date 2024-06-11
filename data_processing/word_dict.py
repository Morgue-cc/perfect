import pickle
import json

# 从两个语料库中提取词汇集合
def get_vocab(corpus1, corpus2):
    word_vocab = set()
    for corpus in [corpus1, corpus2]:
        for item in corpus:
            word_vocab.update(item[1][0])
            word_vocab.update(item[1][1])
            word_vocab.update(item[2][0])
            word_vocab.update(item[3])
    print(len(word_vocab))
    return word_vocab

# 从指定的 pickle 文件中加载数据
def load_pickle(filename):
    with open(filename, 'rb') as f:
        data = pickle.load(f)
    return data


# 处理两个文本文件中的词汇，生成一个去重且排除了一些词汇后的词汇表并保存
def vocab_processing(filepath1, filepath2, save_path):
    # 将每个文件的内容转换为一个集合，以去除重复的行。
    with open(filepath1, 'r') as f:
        total_data1 = set(f.read().splitlines())

    with open(filepath2, 'r') as f:
        total_data2 = set(f.read().splitlines())

    # 获取最终的词汇集合
    word_set = get_vocab(total_data1, total_data2)

    # 找到交集并移除
    excluded_words = total_data1.intersection(word_set)
    word_set -= excluded_words

    print(len(total_data1))
    print(len(word_set))

    with open(save_path, 'w') as f:
        for word in word_set:
            f.write(f"{word}\n") # 写入指定文件，每个词汇占一行


def main(config_path):
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)

    # 处理Python相关的文件
    vocab_processing(
        config['python']['hnn'],
        config['python']['staqc'],
        config['python']['word_dict']
    )

    # 处理SQL相关的文件
    vocab_processing(
        config['sql']['word_dict'],
        config['sql']['new_large'],
        config['sql']['large_word_dict_sql']
    )


if __name__ == "__main__":
    config_path = 'config.json'
    main(config_path)
