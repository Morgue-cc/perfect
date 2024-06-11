# Software Engineering

20211060034 沈铖

## 目录

- [一、项目描述](#一项目描述)
- [二、项目结构](#二项目结构)
- [三、项目文件说明](#三项目文件说明)
  - [3.1 embddings_process.py 文件](#embddings_processpy文件)
  - [3.2 getStru2Vec.py 文件](#getstru2vecpy文件)
  - [3.3 process_single_corpus.py 文件](#process_single_corpuspy文件)
  - [3.4 python_structured.py 文件](#python_structuredpy文件)
  - [3.5 sqlang_structured.py 文件](#sqlang_structuredpy文件)
  - [3.6 word_dict.py 文件](#word_dictpy文件)

## 一、项目描述

这个项目是一个专门设计用于处理编程语言（Python 和 SQL）和文本数据的工具集，主要功能包括自然语言处理和机器学习模型相关的词向量转换、词典构建、序列化语料库、解析和标记化查询，以及生成和优化用于模型训练的词汇表。它旨在为机器学习在代码理解和生成方面的应用提供预处理和数据准备，从这些数据中提取结构化信息、生成向量表示，并进行预处理和词典管理，对于编程语言的自动理解、代码生成、自然语言处理和机器学习研究非常有用。

## 二、项目结构

```
├── data_processing
│   └── embaddings_process.py
│   └── getStru2Vec.py
│   └── process_single_corpus.py
│   └── python_structured.py
│   └── sqlang_structured.py
│   └── word_dirt.py
|   └── config.json
```

## 三、项目文件说明

### embddings_process.py文件

1. **概述**  
   用于处理和转换词向量，构建词典，以及序列化文本数据。

2. **导入依赖库**

- pickle：用于序列化和反序列化 Python 对象。
- numpy：用于高效的数值计算和数组操作。
- gensim 的 KeyedVectors：用于加载和操作词向量模型。

3. **类和方法说明**

- trans_bin 函数：将文本格式的词向量文件转换成二进制格式，便于更快地加载。
- get_new_dict 函数：从已有的词向量模型中构建一个新的词典和词向量矩阵，并为特殊词（如'PAD', 'SOS', 'EOS', 'UNK'）分配向量。
- get_index 函数：将文本转换为词典中的索引序列。
- serialization 函数：序列化训练、测试、验证语料，将文本转换为适合机器学习模型处理的格式。

4. **优化说明**

- 代码模块化：将功能逻辑划分成独立的函数，使得代码更加清晰和可维护。
- 减少重复代码：合并了一些重复的逻辑，如特殊词向量的初始化和索引查找逻辑。
- 提高代码的可读性：通过更清晰的函数命名和使用常量来提高代码的可读性。
- 避免使用硬编码：将文件路径等配置信息作为脚本参数或配置文件读入，而不是硬编码在脚本中。

### getStru2Vec.py文件

1. **概述**  
   用于对 Python 和 SQL 语言的查询、上下文和代码进行解析。

2. **导入依赖库**

- pickle：用于序列化和反序列化 Python 对象结构。
- multiprocessing：提供了支持并发执行的功能，通过创建多个进程来加速数据处理。
- json: 用于处理 JSON 数据格式。
- argparse: 用于编写用户友好的命令行接口。
- typing 的 List, Tuple, Callable, Any: 这些是类型提示
- python_structured 的 python_query_parse, python_code_parse, python_context_parse：用于解析 Python 查询、代码和上下文数据的函数。
- sqlang_structured 的 sqlang_query_parse, sqlang_code_parse, sqlang_context_parse：用于解析 SQL 查询、代码和上下文数据的函数。

3. **类和方法说明**

- multipro_python_query 函数：解析 Python 查询数据。
- multipro_python_code 函数：解析 Python 代码。
- multipro_python_context 函数：解析 Python 上下文数据。
- multipro_sqlang_query 函数：解析 SQL 查询。
- multipro_sqlang_code 函数：解析 SQL 代码片段。
- multipro_sqlang_context 函数：解析 SQL 上下文数据。
- parse 函数：使用多进程来并行处理分割的数据列表，使用上述提到的解析函数对数据进行上下文、查询和代码的解析。结果被合并并打印出处理的数据条数。
- main 函数：读取源数据文件，应用 parse 函数进行数据解析，并将解析后的数据保存到指定的路径。

4. **优化说明**

- 避免使用 import：使用 from module import \*可能会导致命名空间污染和不明确的引用，应该只导入需要的函数或类。
- 类型注释：为函数参数和返回值添加类型注释，以提高代码的清晰度和可维护性。
- 文档字符串：为每个函数添加文档字符串，描述函数的作用、参数和返回值。
- 避免使用硬编码：将文件路径等配置信息作为脚本参数或配置文件读入，而不是硬编码在脚本中。
- 错误处理：处理可能的异常，例如文件读写操作。

### process_single_corpus.py文件

1. **概述**  
   用于处理和标记不同类型（STAQC 和大型数据集）的 Python 和 SQL 数据集，将它们分为单一问题和多重问题的子集，并将处理结果保存到指定的文件路径中。

2. **导入依赖库**

- pickle: 用于 Python 对象的序列化和反序列化，允许对象以文件形式保存在磁盘上。
- json: 用于处理 JSON 数据格式，支持将 Python 对象转换为 JSON 字符串，以及解析 JSON 字符串成 Python 对象。
- Counter (来自 collections 模块): 提供了一个计数器工具，用于统计可哈希对象中元素的出现次数。

3. **类和方法说明**

- load_pickle 函数: 加载并返回一个指定路径下的 pickle 文件中的数据。
- split_data 函数: 根据问题 ID，将数据分为只有单个问题的数据集和有多个问题的数据集。
- data_staqc_processing 函数: 读取 STAQC 数据集的文件，分离数据集，并将结果保存到指定的单一和多重问题文件中。
- data_large_processing 函数: 加载大型数据集的 pickle 文件，分离数据集，并将结果保存为 pickle 格式。
- single_unlabeled_to_labeled 函数: 将单一问题数据集中的每个数据项标记为已标记，并按问题 ID 排序，然后保存到输出路径。
- main 函数：从 config.json 文件中读取配置信息，处理 Python 和 SQL 相关的数据集，包括分离数据集和标记单一问题数据集。

4. **优化说明**

- 避免使用硬编码：将文件路径等配置信息作为脚本参数或配置文件读入，而不是硬编码在脚本中。
- 文档字符串：为每个函数添加文档字符串，描述函数的作用、参数和返回值。

### python_structured.py文件

1. **概述**

提供一个框架，用于解析和处理 Python 代码以及自然语言文本，实现包括去除无效字符、代码和文本的分词与标记化、词性还原和格式转换等功能。

2. **导入依赖库**

- re: 提供正则表达式的匹配和处理功能，用于文本搜索、替换等。
- ast: Python 的抽象语法树库，用于解析和处理 Python 代码结构。
- sys: 提供对一些与 Python 解释器和它的环境有关的函数和变量的访问。
- token: 提供对 Python 源代码的标记（Token）类型和相关功能的访问。
- tokenize: 用于将 Python 源代码字符串分解为标记（Token）序列。
- nltk 的 wordpunct_tokenize: 用于将文本分割成单词和标点符号。
- StringIO: 提供在内存中读写字符串的功能，类似于文件对象。
- inflection: 用于字符串的格式变换，如骆驼命名法转换为下划线命名法。
- nltk 的 pos_tag: 用于对文本进行词性标注。
- nltk 的 WordNetLemmatizer: 用于将单词还原到基本形式（词性还原）。
- nltk.corpus 的 wordnet: 用于词干提取和词义关系查询的语言数据库。

3. **类和方法说明**

- repair_program_io 函数: 处理 Python 代码中的 Jupyter Notebook 或 REPL 特有输入输出标记，以获得干净的代码文本。
- get_vars 函数: 从 Python 抽象语法树(AST)中提取所有变量名并按字典序返回。
- get_vars_heuristics 函数: 当 AST 解析失败时，使用启发式方法从代码中尽可能提取变量名。
- PythonParser 函数: 解析 Python 代码，提取变量名，并尝试进行代码标记化。
- revert_abbrev 函数: 将英文缩略词还原为完整形式的单词。
- get_wordpos 函数: 根据词性标记返回对应的 WordNet 词性。
- process_nl_line 函数: 预处理自然语言文本，包括格式化和去除无关字符。
- process_sent_word 函数: 对句子进行分词、词性标注、还原和提取词干。
- filter_all_invachar 函数: 去除所有可能导致解析错误的非常用字符。
- filter_part_invachar 函数: 去除部分可能导致解析错误的非常用字符。
- python_code_parse 函数: 对 Python 代码字符串进行解析，提取标记化的代码块。
- python_query_parse 函数: 解析 Python 相关的查询文本，提取标记化的单词列表。
- python_context_parse 函数: 解析 Python 上下文中的文本，提取标记化的单词列表。
- main() 函数: 用于演示上述函数如何处理给定的代码和文本查询。

4. **优化说明**

- 封装主逻辑：将主逻辑部分封装在一个函数中，比如 main()，以提高代码的可读性和可维护性。
- 循环处理输入：对于重复的函数调用，可以使用循环来简化代码。
- 错误处理：对于可能引发错误的部分，如函数调用，考虑添加适当的错误处理机制。

### sqlang_structured.py文件

1. **概述**  
   用于对 SQL 查询字符串进行分析和处理，包括字符串的清理、标记化、关键字识别、标识符重命名等，最终生成处理后的标记列表以供进一步使用。

2. **导入依赖库**

- re: 这是 Python 的正则表达式库，用于各种模式匹配和字符串操作，如搜索、替换和分割操作。
- sqlparse: 用于解析 SQL 语句，将其分解为组件以便于分析和重构。
- inflection: 用于字符串的格式转换，如在代码中用于将骆驼命名法转换为下划线命名法。
- nltk.corpus.wordnet: 是一个大型的语义词典，用于英语词汇的词义和同义词集。
- nltk: 用于词性标注、词形还原，即将单词从不同的时态、派生形式还原到基本形式。
- python_structured：自定义模块，包含了用于处理自然语言和结构化数据的函数。

3. **类和方法说明**

- tokenizeRegex 函数: 使用正则表达式分析和提取字符串中的特定模式，返回匹配的结果列表。
- SqlangParser.sanitizeSql 函数: 清理和标准化输入的 SQL 查询字符串 sql，如去除不必要的字符，添加分号结尾等。
- SqlangParser.parseStrings 函数: 分析和处理字符串标记 tok，将其转换为规定的格式或使用正则表达式进行分词。
- SqlangParser.renameIdentifiers 函数: 重命名 SQL 查询中的列和表标识符 tok，为它们生成新的名称并更新映射。
- SqlangParser.getTokens 函数: 从解析树 parse 中提取并返回所有标记的列表。
- sqlang_code_parse 函数: 用于处理输入的代码行 line，包括过滤无效字符、标记化、重命名标识符等，最终返回处理后的标记列表。
- query_parse 函数: 处理输入的查询 query，通过调用其他函数对查询进行分析和处理，返回处理后的结果。

4. **优化说明**

- 模块化导入：将重复的代码片段提取到单独的函数或方法中，然后通过调用该函数来替换原来的重复代码
- 错误处理：对于可能引发错误的部分，如函数调用，考虑添加适当的错误处理机制。

### word_dict.py文件

1. **概述**  
   用于处理两个文本文件中的词汇，生成一个去重且排除了一些词汇后的词汇表并保存。

2. **导入依赖库**

- pickle：用于序列化和反序列化 Python 对象。

3. **类和方法说明**

- get_vocab 函数：从两个语料库中提取词汇，返回包含了从两个语料库中提取出来的所有唯一词汇的词汇集合。
- load_pickle 函数：从指定的 pickle 文件中加载数据。
- vocab_processing 函数：处理两个文本文件中的词汇，生成一个去重且排除了一些词汇后的词汇表，并将其保存到指定路径的文件中。
- main 函数：读取配置文件 config.json，并根据配置文件中的路径信息，调用 vocab_processing 函数处理 Python 相关和 SQL 相关的文件。

4. **优化说明**

- 使用 f.read().splitlines() 来直接读取文件内容为字符串列表，代替原先使用 eval 的不安全做法。
- 修正 vocab_processing 函数中 get_vocab 函数的调用逻辑，确保正确地处理两个不同的数据集。
- 在写入最终的单词集时，使用了循环逐行写入，每个单词占一行，以提高文件的可读性。

### config.json文件

用于指定项目中使用的各种数据文件和资源的存储位置的配置文件。使得项目的数据管理更加集中和方便，允许在不同部分之间切换和更新路径，而不必在程序代码中手动更改它们。

- python 部分:
  - vec_bin_path: Python 结构化向量的二进制文件路径。
  - word_path: 包含 Python 单词词汇表的文本文件路径。
  - word_vec_path: Python 单词词汇的向量表示的 Pickle 文件路径。
  - word_dict_path: Python 单词字典的 Pickle 文件路径。
  - serialization_paths: 包含需要序列化处理的数据文件路径和对应序列化后文件的路径列表。
  - hnn: 教师数据文件路径，用于知识提取或迁移学习。
  - staqc: StaQC 数据集的 Python 相关数据文件路径。
  - word_dict: Python 单词词汇表字典的文本文件路径。
  - staqc_path: StaQC 数据集的无标签问题 ID 到索引块映射文件的路径。
  - staqc_single_save: StaQC 数据集中单个查询的保存路径。
  - staqc_multiple_save: StaQC 数据集中多个查询的保存路径。
  - large_path: 一个大型无标签数据集的 Pickle 文件路径。
  - large_single_save: 大型数据集中单个查询的 Pickle 文件保存路径。
  - large_multiple_save: 大型数据集中多个查询的 Pickle 文件保存路径。
  - large_single_label_save: 大型数据集中单个查询的文本文件保存路径。
- sql 部分:
  - vec_bin_path: SQL 结构化向量的二进制文件路径。
  - word_path: 包含 SQL 单词词汇表的文本文件路径。
  - word_vec_path: SQL 单词词汇的向量表示的 Pickle 文件路径。
  - word_dict_path: SQL 单词字典的 Pickle 文件路径。
  - serialization_paths: 包含需要序列化处理的数据文件路径和对应序列化后文件的路径列表。
  - hnn: 教师数据文件路径，用于知识提取或迁移学习。
  - staqc: StaQC 数据集的 SQL 相关数据文件路径。
  - word_dict: SQL 单词词汇表字典的文本文件路径。
  - new_staqc: 新的 StaQC 数据集的 SQL 无标签数据文件路径。
  - new_large: 大型数据集中 SQL 多个查询的无标签文本文件路径。
  - large_word_dict_sql: 大型数据集的 SQL 单词字典文本文件路径。
  - staqc_path: StaQC 数据集的无标签问题 ID 到索引块映射文件的路径。
  - staqc_single_save: StaQC 数据集中单个查询的保存路径。
  - staqc_multiple_save: StaQC 数据集中多个查询的保存路径。
  - large_path: 一个大型无标签 SQL 数据集的 Pickle 文件路径。
  - large_single_save: 大型数据集中单个 SQL 查询的 Pickle 文件保存路径。
  - large_multiple_save: 大型数据集中多个 SQL 查询的 Pickle 文件保存路径。
  - large_single_label_save: 大型数据集中单个 SQL 查询的文本文件保存路径。
