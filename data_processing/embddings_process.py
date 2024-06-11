import json
import pickle
import numpy as np
from gensim.models import KeyedVectors

SPECIAL_TOKENS = ['PAD', 'SOS', 'EOS', 'UNK']
VEC_SIZE = 300
MAX_CODE_LEN = 350 # 代码
MAX_TEXT_LEN = 100 # 上下文
MAX_QUERY_LEN = 25 # 查询


# 将词向量文件保存为二进制文件
def trans_bin(input_path, output_path):
    wv = KeyedVectors.load_word2vec_format(input_path, binary=False) # 加载指定路径下的文本格式词向量文件到变量 wv
    wv.init_sims(replace=True) # 优化词向量的内存使用，必要时替换原始向量
    wv.save(output_path) # 将优化后的词向量保存到指定的输出路径的二进制文件中


# 构建新的词典和词向量矩阵
def build_new_dict_and_matrix(type_vec_path, type_word_path, final_vec_path, final_word_path):
    model = KeyedVectors.load(type_vec_path, mmap='r')
    with open(type_word_path, 'r') as f:
        total_word = eval(f.read()) # 读取二进制词向量、词典文件

    rng = np.random.RandomState(None) # 随机数生成器
    special_embeddings = [rng.uniform(-0.25, 0.25, size=(VEC_SIZE,)).squeeze() for _ in SPECIAL_TOKENS] # 为特殊标记生成随机的词向量
    word_vectors, word_dict = special_embeddings, SPECIAL_TOKENS[:] # 将特殊标记的向量和标记本身作为初始内容

    for word in total_word:
        try:
            word_vectors.append(model.wv[word])
            word_dict.append(word) # 从模型中获取每个词汇的向量，添加到词向量列表和词典
        except KeyError:
            pass # 词汇不在模型中则忽略

    word_vectors = np.array(word_vectors)
    word_dict = {word: i for i, word in enumerate(word_dict)} # 每个词汇映射到其索引

    with open(final_vec_path, 'wb') as f:
        pickle.dump(word_vectors, f)
    with open(final_word_path, 'wb') as f:
        pickle.dump(word_dict, f) # 将词向量矩阵、词典以二进制形式序列化保存


# 得到词在词典中的位置
def get_index(text, word_dict, max_len, is_code=False):
    indices = [word_dict.get(word, word_dict['UNK']) for word in text[:max_len - 1]]

    if is_code:
        indices = [word_dict['SOS']] + indices + [word_dict['EOS']] # 是代码，开头添加 'SOS'，末尾添加 'EOS'
    else:
        indices = (indices + [word_dict['PAD']] * max_len)[:max_len] # 不是代码，添加 'PAD' 扩充或截断到 max_len

    return indices


# 将训练、测试、验证语料序列化
def serialize_corpus(word_dict_path, corpus_path, output_path):
    with open(word_dict_path, 'rb') as f:
        word_dict = pickle.load(f) # 加载并反序列化词典文件
    with open(corpus_path, 'r') as f:
        corpus = eval(f.read()) # 加载并评估语料库文件

    serialized_data = []
    for entry in corpus:
        qid, contexts, code, query = entry[0], entry[1], entry[2][0], entry[3] # 每条记录中提取问题ID、上下文、代码和查询

        contexts = [get_index(context, word_dict, MAX_TEXT_LEN) for context in contexts]
        code_indices = get_index(code, word_dict, MAX_CODE_LEN, is_code=True)
        query_indices = get_index(query, word_dict, MAX_QUERY_LEN) # 将上下文中的文本、代码、查询序列化为索引列表

        serialized_data.append([qid, contexts, [code_indices], query_indices, 4, 0]) # 将序列化后的数据添加到列表

    with open(output_path, 'wb') as f:
        pickle.dump(serialized_data, f)


def process_data(vec_bin_path, word_path, word_vec_path, word_dict_path, serialization_paths=None):
    trans_bin(vec_bin_path, word_vec_path) # 转换词向量文件
    build_new_dict_and_matrix(vec_bin_path, word_path, word_vec_path, word_dict_path) # 构建新的词典和词向量矩阵
    if serialization_paths:
        for corpus_path, output_path in serialization_paths:
            serialize_corpus(word_dict_path, corpus_path, output_path) # 序列化语料


def main(config_type):
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    process_data(**config[config_type])
    print('序列化完毕')


if __name__ == '__main__':
    # 可以通过命令行参数或其他方式选择配置类型
    config_type = 'python'  # 或 'sql'
    main(config_type)
