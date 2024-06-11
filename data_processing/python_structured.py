# -*- coding: utf-8 -*-
import re
import ast
import sys
import token
import tokenize

from nltk import wordpunct_tokenize
from io import StringIO
# 骆驼命名法
import inflection

# 词性还原
from nltk import pos_tag
from nltk.stem import WordNetLemmatizer

# 初始化词形还原器
wnler = WordNetLemmatizer()

# 词干提取
from nltk.corpus import wordnet


# 正则表达式模式
PATTERN_VAR_EQUAL = re.compile("(\s*[_a-zA-Z][_a-zA-Z0-9]*\s*)(,\s*[_a-zA-Z][_a-zA-Z0-9]*\s*)*=")
PATTERN_VAR_FOR = re.compile("for\s+[_a-zA-Z][_a-zA-Z0-9]*\s*(,\s*[_a-zA-Z][_a-zA-Z0-9]*)*\s+in")

# 对包含特定输入输出标记的Python程序代码进行处理
def repair_program_io(code):
    # 情况一：Jupyter Notebook代码块，可能包含 In [数字]: 和 Out[数字]: 以及续行标记 ...:
    pattern_case1_in = re.compile("In ?\[\d+]: ?")  # flag1
    pattern_case1_out = re.compile("Out ?\[\d+]: ?")  # flag2
    pattern_case1_cont = re.compile("( )+\.+: ?")  # flag3

    # 情况二：Python交互式解释器（REPL）代码块，可能包含 >>> 作为新命令的开始，以及 ... 作为多行命令的续行标记
    pattern_case2_in = re.compile(">>> ?")  # flag4
    pattern_case2_cont = re.compile("\.\.\. ?")  # flag5

    patterns = [pattern_case1_in, pattern_case1_out, pattern_case1_cont,
                pattern_case2_in, pattern_case2_cont]


    lines = code.split("\n") # 将输入的代码分割为行
    lines_flags = [0 for _ in range(len(lines))] # 为每行分配一个标志

    code_list = []

    # 如果一行匹配了某个模式，其对应的标志将被设置为该模式的索引值加1
    # 因为索引从0开始，而0保留用于表示“无匹配”情况
    for line_idx in range(len(lines)):
        line = lines[line_idx]
        for pattern_idx in range(len(patterns)):
            if re.match(patterns[pattern_idx], line):
                lines_flags[line_idx] = pattern_idx + 1
                break
    lines_flags_string = "".join(map(str, lines_flags))

    bool_repaired = False

    # 如果所有行都没有匹配任何模式，则认为代码不需要修复，直接返回原始代码
    if lines_flags.count(0) == len(lines_flags):  # no need to repair
        repaired_code = code
        code_list = [code]
        bool_repaired = True

    # 如果代码匹配了Jupyter Notebook或REPL的模式，则执行修复逻辑
    elif re.match(re.compile("(0*1+3*2*0*)+"), lines_flags_string) or \
            re.match(re.compile("(0*4+5*0*)+"), lines_flags_string):
        repaired_code = ""
        pre_idx = 0
        sub_block = ""
        # 如果代码的第一行没有特殊标记，则直接添加到repaired_code中，直到遇到第一个有标记的行
        if lines_flags[0] == 0:
            flag = 0
            while (flag == 0):
                repaired_code += lines[pre_idx] + "\n"
                pre_idx += 1
                flag = lines_flags[pre_idx]
            sub_block = repaired_code
            code_list.append(sub_block.strip())
            sub_block = ""

        for idx in range(pre_idx, len(lines_flags)):
            # 如果当前行有标记，则使用相应的正则表达式去除该行的特殊标记，并将处理后的行添加到repaired_code
            if lines_flags[idx] != 0:
                repaired_code += re.sub(patterns[lines_flags[idx] - 1], "", lines[idx]) + "\n"

                if len(sub_block.strip()) and (idx > 0 and lines_flags[idx - 1] == 0):
                    code_list.append(sub_block.strip())
                    sub_block = ""
                sub_block += re.sub(patterns[lines_flags[idx] - 1], "", lines[idx]) + "\n"

            # 如果在处理有标记的行之后遇到无标记的行，且这些无标记的行紧跟在有标记的行之后，将它们视为一个连续的代码块处理并添加到code_list中
            else:
                if len(sub_block.strip()) and (idx > 0 and lines_flags[idx - 1] != 0):
                    code_list.append(sub_block.strip())
                    sub_block = ""
                sub_block += lines[idx] + "\n"

        # 处理最后一个代码块
        if len(sub_block.strip()):
            code_list.append(sub_block.strip())

        # 设置修复标志
        if len(repaired_code.strip()) != 0:
            bool_repaired = True

    # 不符合以上条件的行，通过去除Out[数字]:后面的所有非匹配行来修复代码
    if not bool_repaired:
        repaired_code = "" # 用于存储修复后的代码
        sub_block = "" # 用于暂存被处理的代码块
        bool_after_Out = False # 用于标记当前处理的行是否在Out[数字]:后面
        for idx in range(len(lines_flags)):
            # 如果当前行有标记，说明这行是特定模式的一部分
            if lines_flags[idx] != 0:
                # 如果这行是Out[数字]:，设置bool_after_Out为True，表示后续行直到下一个有标记的行应该被忽略
                if lines_flags[idx] == 2:
                    bool_after_Out = True
                else:
                    bool_after_Out = False

                # 使用正则表达式移除当前行的特定标记，并将处理后的行添加到repaired_code和sub_block中
                repaired_code += re.sub(patterns[lines_flags[idx] - 1], "", lines[idx]) + "\n"
                if len(sub_block.strip()) and (idx > 0 and lines_flags[idx - 1] == 0):
                    code_list.append(sub_block.strip())
                    sub_block = ""
                sub_block += re.sub(patterns[lines_flags[idx] - 1], "", lines[idx]) + "\n"

            # 如果当前行没有标记，且不是紧跟在Out[数字]:标记后的行，则将这一行原样添加到repaired_code中
            else:
                if not bool_after_Out:
                    repaired_code += lines[idx] + "\n"
                # 如果sub_block非空并且行的标记状态发生变化，则将sub_block作为一个独立的代码块保存，并准备收集下一个代码块
                if len(sub_block.strip()) and (idx > 0 and lines_flags[idx - 1] != 0):
                    code_list.append(sub_block.strip())
                    sub_block = ""
                sub_block += lines[idx] + "\n"

    return repaired_code, code_list

# 从Python代码的AST中提取所有在非读取上下文中使用的变量名，并按字典序返回这些变量名的列表
def get_vars(ast_root):
    return sorted(
        {node.id for node in ast.walk(ast_root) if isinstance(node, ast.Name) and not isinstance(node.ctx, ast.Load)})


# 在AST解析因代码中的错误或不完整而失败的情况下，仍尽可能提取变量名
def get_vars_heuristics(code):
    varnames = set() # 用于存储最终识别的所有唯一变量名
    code_lines = [_ for _ in code.split("\n") if len(_.strip())] # 将输入的代码字符串code按行分割，并过滤掉空行

    # 尝试AST解析
    start = 0
    end = len(code_lines) - 1
    bool_success = False
    while not bool_success:
        try:
            root = ast.parse("\n".join(code_lines[start:end])) # 解析代码行从start到end的部分
        except:
            end -= 1 # 如果解析失败，则逐渐缩小尝试解析的代码范围
        else:
            bool_success = True
    # print("Best effort parse at: start = %d and end = %d." % (start, end))
    # 一旦解析成功，用get_vars函数提取变量名，并添加到varnames集合中
    varnames = varnames.union(set(get_vars(root)))
    # print("Var names from base effort parsing: %s." % str(varnames))

    # processing the remaining...
    for line in code_lines[end:]:
        line = line.strip()
        try:
            root = ast.parse(line) # 尝试使用ast.parse解析每一行代码
        except:
            # 匹配赋值操作
            pattern_var_equal_matched = re.match(PATTERN_VAR_EQUAL, line)
            if pattern_var_equal_matched:
                match = pattern_var_equal_matched.group()[:-1]  # remove "="
                varnames = varnames.union(set([_.strip() for _ in match.split(",")]))

            # 匹配for循环
            pattern_var_for_matched = re.search(PATTERN_VAR_FOR, line)
            if pattern_var_for_matched:
                match = pattern_var_for_matched.group()[3:-2]  # remove "for" and "in"
                varnames = varnames.union(set([_.strip() for _ in match.split(",")]))

        else:
            varnames = varnames.union(get_vars(root)) # 如果解析成功，同样使用get_vars函数提取变量名

    return varnames

# 对给定的Python代码字符串进行解析和提取变量名，并尝试将代码进行标记化
def PythonParser(code):
    bool_failed_var = False
    bool_failed_token = False # 用于标记在解析变量名和标记化代码时是否遇到失败

    # 尝试使用ast.parse对代码进行解析，并通过get_vars函数提取变量名
    try:
        root = ast.parse(code)
        varnames = set(get_vars(root))
    # 如果解析失败，则尝试修复代码并重新解析
    except:
        repaired_code, _ = repair_program_io(code)
        # 再次尝试解析
        try:
            root = ast.parse(repaired_code)
            varnames = set(get_vars(root))
        # 仍然无法解析，标记解析变量名失败，并尝试提取变量名
        except:
            bool_failed_var = True
            varnames = get_vars_heuristics(code)

    tokenized_code = [] # 用于存储标记化的结果

    # 对代码进行第一次标记化
    def first_trial(_code):
        if len(_code) == 0:
            return True
        try:
            g = tokenize.generate_tokens(StringIO(_code).readline) # 使用生成器逐个产生代码的标记
            term = next(g)
        except:
            return False
        else:
            return True

    bool_first_success = first_trial(code)
    # 如果失败，则逐字符移除代码的起始部分，直到标记化成功
    while not bool_first_success:
        code = code[1:]
        bool_first_success = first_trial(code)
    g = tokenize.generate_tokens(StringIO(code).readline)
    term = next(g)

    bool_finished = False
    while not bool_finished:
        term_type = term[0]
        lineno = term[2][0] - 1
        posno = term[3][1] - 1
        # 如果标记类型是NUMBER、STRING或NEWLINE，则将标记类型名称直接添加到tokenized_code列表
        if token.tok_name[term_type] in {"NUMBER", "STRING", "NEWLINE"}:
            tokenized_code.append(token.tok_name[term_type])
        # 对于非COMMENT和ENDMARKER类型的标记
        elif not token.tok_name[term_type] in {"COMMENT", "ENDMARKER"} and len(term[1].strip()):
            candidate = term[1].strip()
            # 如果标记的内容不是之前提取的变量名，则将标记内容添加到列表中
            if candidate not in varnames:
                tokenized_code.append(candidate)
            # 否则，添加字符串"VAR"
            else:
                tokenized_code.append("VAR")

        # fetch the next term
        bool_success_next = False
        while not bool_success_next:
            try:
                term = next(g)
            # 遇到StopIteration异常，表示标记化已完成
            except StopIteration:
                bool_finished = True
                break
            # 遇到其他异常，设置标记化代码失败，并尝试对遇到错误的代码行进行处理
            except:
                bool_failed_token = True
                code_lines = code.split("\n")
                if lineno > len(code_lines) - 1:
                    print(sys.exc_info())
                else:
                    failed_code_line = code_lines[lineno]
                    if posno < len(failed_code_line) - 1:
                        failed_code_line = failed_code_line[posno:]
                        tokenized_failed_code_line = wordpunct_tokenize(failed_code_line) # 用wordpunct_tokenize对遇到错误的代码行进行标记化
                        tokenized_code += tokenized_failed_code_line # 将结果添加到tokenized_code列表中
                    # 如果错误发生在代码的中间行，从错误行之后的代码重新开始标记化过程
                    if lineno < len(code_lines) - 1:
                        code = "\n".join(code_lines[lineno + 1:])
                        g = tokenize.generate_tokens(StringIO(code).readline)
                    # 如果错误行是代码的最后一行，结束标记化循环
                    else:
                        bool_finished = True
                        break
            else:
                bool_success_next = True
    # 返回标记化的代码列表，和在变量名解析和代码标记化过程中是否遇到失败的两个布尔值
    return tokenized_code, bool_failed_var, bool_failed_token


# 缩略词处理，将缩写形式的英语单词还原为完整形式
def revert_abbrev(line):
    pat_is = re.compile("(it|he|she|that|this|there|here)(\"s)", re.I)
    # 's
    pat_s1 = re.compile("(?<=[a-zA-Z])\"s")
    # s
    pat_s2 = re.compile("(?<=s)\"s?")
    # not
    pat_not = re.compile("(?<=[a-zA-Z])n\"t")
    # would
    pat_would = re.compile("(?<=[a-zA-Z])\"d")
    # will
    pat_will = re.compile("(?<=[a-zA-Z])\"ll")
    # am
    pat_am = re.compile("(?<=[I|i])\"m")
    # are
    pat_are = re.compile("(?<=[a-zA-Z])\"re")
    # have
    pat_ve = re.compile("(?<=[a-zA-Z])\"ve")

    # 还原为原始形式
    line = pat_is.sub(r"\1 is", line)
    line = pat_s1.sub("", line)
    line = pat_s2.sub("", line)
    line = pat_not.sub(" not", line)
    line = pat_would.sub(" would", line)
    line = pat_will.sub(" will", line)
    line = pat_am.sub(" am", line)
    line = pat_are.sub(" are", line)
    line = pat_ve.sub(" have", line)

    return line

# 获取词性
def get_wordpos(tag):
    if tag.startswith('J'): # 形容词
        return wordnet.ADJ
    elif tag.startswith('V'): # 动词
        return wordnet.VERB
    elif tag.startswith('N'): # 名词
        return wordnet.NOUN
    elif tag.startswith('R'): # 副词
        return wordnet.ADV
    else:
        return None

# 子函数1：句子的去冗
def process_nl_line(line):
    # 句子预处理
    line = revert_abbrev(line)
    line = re.sub('\t+', '\t', line) # 将连续的制表符（\t+）替换为单个制表符（\t）
    line = re.sub('\n+', '\n', line) # 将连续的换行符（\n+）替换为单个换行符（\n）
    line = line.replace('\n', ' ') # 将所有换行符（\n）替换为空格
    line = re.sub(' +', ' ', line) # 替换连续的空格为单个空格
    line = line.strip() # 去除字符串首尾的空格

    # 骆驼命名转下划线
    line = inflection.underscore(line)

    # 去除括号里内容
    space = re.compile(r"\([^(|^)]+\)")  # 后缀匹配
    line = re.sub(space, '', line)
    # 去除开始和末尾空格
    line = line.strip()
    return line

# 子函数2：句子的分词
def process_sent_word(line):
    # 找单词
    line = re.findall(r"\w+|[^\s\w]", line)
    line = ' '.join(line)
    # 替换小数
    decimal = re.compile(r"\d+(\.\d+)+")
    line = re.sub(decimal, 'TAGINT', line)
    # 替换字符串
    string = re.compile(r'\"[^\"]+\"')
    line = re.sub(string, 'TAGSTR', line)
    # 替换十六进制
    decimal = re.compile(r"0[xX][A-Fa-f0-9]+")
    line = re.sub(decimal, 'TAGINT', line)
    # 替换数字 56
    number = re.compile(r"\s?\d+\s?")
    line = re.sub(number, ' TAGINT ', line)
    # 替换字符 6c60b8e1
    other = re.compile(r"(?<![A-Z|a-z_])\d+[A-Za-z]+")  # 后缀匹配
    line = re.sub(other, 'TAGOER', line)
    cut_words = line.split(' ')
    # 全部小写化
    cut_words = [x.lower() for x in cut_words]
    # 词性标注
    word_tags = pos_tag(cut_words)
    tags_dict = dict(word_tags)
    word_list = []
    for word in cut_words:
        word_pos = get_wordpos(tags_dict[word])
        if word_pos in ['a', 'v', 'n', 'r']:
            # 词性还原
            word = wnler.lemmatize(word, pos=word_pos)
        # 词干提取(效果最好）
        word = wordnet.morphy(word) if wordnet.morphy(word) else word
        word_list.append(word)
    return word_list

def filter_all_invachar(line):
    # 去除非常用符号；防止解析有误
    assert isinstance(line, object)
    line = re.sub('[^(0-9|a-zA-Z\-_\'\")\n]+', ' ', line)
    # 包括\r\t也清除了
    # 中横线
    line = re.sub('-+', '-', line)
    # 下划线
    line = re.sub('_+', '_', line)
    # 去除横杠
    line = line.replace('|', ' ').replace('¦', ' ')
    return line

def filter_part_invachar(line):
    # 去除非常用符号；防止解析有误
    line = re.sub('[^(0-9|a-zA-Z\-_\'\")\n]+', ' ', line)
    # 包括\r\t也清除了
    # 中横线
    line = re.sub('-+', '-', line)
    # 下划线
    line = re.sub('_+', '_', line)
    # 去除横杠
    line = line.replace('|', ' ').replace('¦', ' ')
    return line

# 主函数：代码的tokens
def python_code_parse(line):
    line = filter_part_invachar(line) # 过滤或处理代码中的无效字符
    line = re.sub('\.+', '.', line) # 替换连续的点号（.）为单个字符
    line = re.sub('\t+', '\t', line) # 替换连续的制表符（\t）为单个字符
    line = re.sub('\n+', '\n', line) # 替换连续的换行符（\n）为单个字符
    line = re.sub('>>+', '', line)  # 去除重定向运算符或其他连续的大于号（>）
    line = re.sub(' +', ' ', line) # 将连续的空格替换为单个空格
    line = line.strip('\n').strip() # 去除字符串首尾的换行符和空格
    line = re.findall(r"[\w]+|[^\s\w]", line) # 标记化
    line = ' '.join(line)

    try:
        typedCode, failed_var, failed_token = PythonParser(line) # 对标记化后的代码进行进一步解析
        typedCode = inflection.underscore(' '.join(typedCode)).split(' ') # 骆驼命名转下划线
        cut_tokens = [re.sub("\s+", " ", x.strip()) for x in typedCode]
        token_list = [x.lower() for x in cut_tokens] # 全部小写化
        token_list = [x.strip() for x in token_list if x.strip() != ''] # 列表里包含 '' 和' '
        return token_list
    except:
        return '-1000' # 存在为空的情况，词向量要进行判断


# 主函数：句子的tokens
# 解析Python查询中的文本
def query_parse(line):
    line = filter_all_invachar(line) # 过滤掉所有无效字符
    line = process_nl_line(line) # 文本预处理
    word_list = process_sent_word(line) # 对预处理后的文本分词
    # 分词后去掉括号
    for i in range(0, len(word_list)):
        if re.findall('[()]', word_list[i]):
            word_list[i] = ''
    word_list = [x.strip() for x in word_list if x.strip() != ''] # 删除空字符串或仅包含空格的字符串
    return word_list
# 解析Python上下文中的文本
def context_parse(line):
    line = filter_part_invachar(line) # 过滤掉部分无效字符
    line = process_nl_line(line) # 文本预处理
    print(line)
    word_list = process_sent_word(line) # 对预处理后的文本分词
    word_list = [x.strip() for x in word_list if x.strip() != ''] # 删除空字符串或仅包含空格的字符串
    return word_list


def main():
    queries = [
        "change row_height and column_width in libreoffice calc use python tagint",
        "What is the standard way to add N seconds to datetime.time in Python?",
        "Convert INT to VARCHAR SQL 11?",
        "python construct a dictionary {0: [0, 0, 0], 1: [0, 0, 1], 2: [0, 0, 2], 3: [0, 0, 3], ...,999: [9, 9, 9]}"
    ]
    contexts = [
        "How to calculateAnd the value of the sum of squares defined as \n 1^2 + 2^2 + 3^2 + ... +n2 until a user specified sum has been reached sql()",
        "how do i display records (containing specific) information in sql() 11?",
        "Convert INT to VARCHAR SQL 11?"
    ]
    codes = [
        'if(dr.HasRows)\n{\n // ....\n}\nelse\n{\n MessageBox.Show("ReservationAnd Number Does Not Exist","Error", MessageBoxButtons.OK, MessageBoxIcon.Asterisk);\n}',
        'root -> 0.0 \n while root_ * root < n: \n root = root + 1 \n print(root * root)',
        'root = 0.0 \n while root * root < n: \n print(root * root) \n root = root + 1',
        'n = 1 \n while n <= 100: \n n = n + 1 \n if n > 10: \n  break print(n)',

        "diayong(2) def sina_download(url, output_dir='.', merge=True, info_only=False, **kwargs):\n    "
        "if 'news.sina.com.cn/zxt' in url:\n        sina_zxt(url, output_dir=output_dir, merge=merge, info_only=info_only, **kwargs)\n  "
        "return\n\n    vid = match1(url, r'vid=(\\d+)')\n    if vid is None:\n        video_page = get_content(url)\n        "
        "vid = hd_vid = match1(video_page, r'hd_vid\\s*:\\s*\\'([^\\']+)\\'')\n  if hd_vid == '0':\n            "
        "vids = match1(video_page, r'[^\\w]vid\\s*:\\s*\\'([^\\']+)\\'').split('|')\n            vid = vids[-1]\n\n    "
        "if vid is None:\n        vid = match1(video_page, r'vid:\"?(\\d+)\"?')\n    if vid:\n   "
        "sina_download_by_vid(vid, output_dir=output_dir, merge=merge, info_only=info_only)\n    "
        "else:\n        vkey = match1(video_page, r'vkey\\s*:\\s*\"([^\"]+)\"')\n        if vkey is None:\n            "
        "vid = match1(url, r'#(\\d+)')\n            sina_download_by_vid(vid, output_dir=output_dir, merge=merge, info_only=info_only)\n            "
        "return\n        title = match1(video_page, r'title\\s*:\\s*\"([^\"]+)\"')\n        "
        "sina_download_by_vkey(vkey, title=title, output_dir=output_dir, merge=merge, info_only=info_only)",

        "d = {'x': 1, 'y': 2, 'z': 3} \n for key in d: \n  print (key, 'corresponds to', d[key])",

        '  #       page  hour  count\n # 0     3727441     1   2003\n # 1     3727441     2    654\n # 2     3727441     3   5434\n # 3     3727458     1    326\n '
        '# 4     3727458     2   2348\n # 5     3727458     3   4040\n # 6   3727458_1     4    374\n # 7   3727458_1     5   2917\n # 8   3727458_1     6   3937\n '
        '# 9     3735634     1   1957\n # 10    3735634     2   2398\n # 11    3735634     3   2812\n # 12    3768433     1    499\n # 13    3768433     2   4924\n '
        '# 14    3768433     3   5460\n # 15  3768433_1     4   1710\n # 16  3768433_1     5   3877\n # 17  3768433_1     6   1912\n # 18  3768433_2     7   1367\n '
        '# 19  3768433_2     8   1626\n # 20  3768433_2     9   4750\n'
    ]
    for query in queries:
        print(query_parse(query))
    for context in contexts:
        print(context_parse(context))
    for code in codes:
        print(python_code_parse(code))

if __name__ == '__main__':
    main()

