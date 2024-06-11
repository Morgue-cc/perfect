# -*- coding: utf-8 -*-
import re
import sqlparse #0.4.2

#骆驼命名法
import inflection

#词干提取
from nltk.corpus import wordnet

#词性还原
from nltk import pos_tag
from nltk.stem import WordNetLemmatizer

from python_structured import process_nl_line, process_sent_word, filter_part_invachar, filter_all_invachar, query_parse

wnler = WordNetLemmatizer()


OTHER = 0
FUNCTION = 1
BLANK = 2
KEYWORD = 3
INTERNAL = 4

TABLE = 5
COLUMN = 6
INTEGER = 7
FLOAT = 8
HEX = 9
STRING = 10
WILDCARD = 11

SUBQUERY = 12

DUD = 13

# 字典，映射了标记类型的整数值到它们的字符串名称
ttypes = {0: "OTHER", 1: "FUNCTION", 2: "BLANK", 3: "KEYWORD", 4: "INTERNAL", 5: "TABLE", 6: "COLUMN", 7: "INTEGER",
          8: "FLOAT", 9: "HEX", 10: "STRING", 11: "WILDCARD", 12: "SUBQUERY", 13: "DUD", }

# 配置了一系列正则表达式和对应的回调函数,每个正则表达式都尝试匹配输入文本中的特定模式
scanner = re.Scanner([(r"\[[^\]]*\]", lambda scanner, token: token), (r"\+", lambda scanner, token: "REGPLU"),
                      (r"\*", lambda scanner, token: "REGAST"), (r"%", lambda scanner, token: "REGCOL"),
                      (r"\^", lambda scanner, token: "REGSTA"), (r"\$", lambda scanner, token: "REGEND"),
                      (r"\?", lambda scanner, token: "REGQUE"),
                      (r"[\.~``;_a-zA-Z0-9\s=:\{\}\-\\]+", lambda scanner, token: "REFRE"),
                      (r'.', lambda scanner, token: None), ])

# 辅助函数，词法分析返回匹配的结果列表
def tokenizeRegex(s):
    results = scanner.scan(s)[0]
    return results

# 分析处理SQL查询
class SqlangParser():
    @staticmethod
    # 清理和标准化输入的SQL查询字符串
    def sanitizeSql(sql):
        s = sql.strip().lower()
        if not s[-1] == ";":
            s += ';' # 添加分号结尾
        s = re.sub(r'\(', r' ( ', s)
        s = re.sub(r'\)', r' ) ', s)
        words = ['index', 'table', 'day', 'year', 'user', 'text'] # 替换特定单词
        for word in words:
            s = re.sub(r'([^\w])' + word + '$', r'\1' + word + '1', s)
            s = re.sub(r'([^\w])' + word + r'([^\w])', r'\1' + word + '1' + r'\2', s)
        s = s.replace('#', '') # 移除不需要的字符
        return s

    # 分析和处理字符串标记
    def parseStrings(self, tok):
        if isinstance(tok, sqlparse.sql.TokenList):
            for c in tok.tokens:
                self.parseStrings(c) # 使用正则表达式进行分词
        elif tok.ttype == STRING:
            if self.regex:
                tok.value = ' '.join(tokenizeRegex(tok.value))
            else:
                tok.value = "CODSTR" # 直接替换为 "CODSTR"

    # 重命名SQL查询中的列和表标识符
    def renameIdentifiers(self, tok):
        # 遍历标记列表，递归处理每个子标记
        if isinstance(tok, sqlparse.sql.TokenList):
            for c in tok.tokens:
                self.renameIdentifiers(c)

        # 为尚未映射的列标识符生成新名称，更新映射，并增加列标识符计数
        elif tok.ttype == COLUMN:
            if str(tok) not in self.idMap["COLUMN"]:
                colname = "col" + str(self.idCount["COLUMN"])
                self.idMap["COLUMN"][str(tok)] = colname
                self.idMapInv[colname] = str(tok)
                self.idCount["COLUMN"] += 1
            tok.value = self.idMap["COLUMN"][str(tok)]

        # 为尚未映射的表标识符生成新名称，更新映射，并增加表标识符计数
        elif tok.ttype == TABLE:
            if str(tok) not in self.idMap["TABLE"]:
                tabname = "tab" + str(self.idCount["TABLE"])
                self.idMap["TABLE"][str(tok)] = tabname
                self.idMapInv[tabname] = str(tok)
                self.idCount["TABLE"] += 1
            tok.value = self.idMap["TABLE"][str(tok)]

        # 替换浮点数、整数和十六进制数的标记
        elif tok.ttype == FLOAT:
            tok.value = "CODFLO"
        elif tok.ttype == INTEGER:
            tok.value = "CODINT"
        elif tok.ttype == HEX:
            tok.value = "CODHEX"

    # 基于标记列表提供一个哈希值
    def __hash__(self):
        return hash(tuple([str(x) for x in self.tokensWithBlanks]))

    # 构造函数，初始化解析器
    def __init__(self, sql, regex=False, rename=True):
        # 清理和标准化输入的SQL字符串
        self.sql = SqlangParser.sanitizeSql(sql)

        # 初始化几个字典和计数器来追踪列和表的重命名
        self.idMap = {"COLUMN": {}, "TABLE": {}}
        self.idMapInv = {}
        self.idCount = {"COLUMN": 0, "TABLE": 0}

        # 设置标志来确定是否在解析字符串时使用正则表达式
        self.regex = regex

        # 初始化一个解析树哨兵变量和一个表的堆栈
        self.parseTreeSentinel = False
        self.tableStack = []

        # 解析清理过的SQL字符串，并获取解析树的第一个元素作为主要处理对象
        self.parse = sqlparse.parse(self.sql)
        self.parse = [self.parse[0]]

        # 调用几个方法来处理解析树
        self.removeWhitespaces(self.parse[0]) # 去除空白符
        self.identifyLiterals(self.parse[0]) # 识别字面量和关键字
        self.parse[0].ptype = SUBQUERY # 将解析树的第一个元素标记为子查询
        self.identifySubQueries(self.parse[0]) # 识别子查询
        self.identifyFunctions(self.parse[0]) # 识别函数
        self.identifyTables(self.parse[0]) # 识别表名

        self.parseStrings(self.parse[0]) # 处理字符串标记

        if rename:
            self.renameIdentifiers(self.parse[0]) # 重命名标识符

        self.tokens = SqlangParser.getTokens(self.parse) # 获取处理后的标记列表

    @staticmethod
    # 从解析树中提取并返回所有标记的列表
    def getTokens(parse):
        flatParse = []
        for expr in parse:
            for token in expr.flatten():
                if token.ttype == STRING:
                    flatParse.extend(str(token).split(' '))
                else:
                    flatParse.append(str(token))
        return flatParse

    # 移除SQL语句中的空白标记
    def removeWhitespaces(self, tok):
        if isinstance(tok, sqlparse.sql.TokenList):
            tmpChildren = []
            for c in tok.tokens:
                if not c.is_whitespace:
                    tmpChildren.append(c)

            tok.tokens = tmpChildren
            for c in tok.tokens:
                self.removeWhitespaces(c)

    # 标识并处理子查询
    def identifySubQueries(self, tokenList):
        isSubQuery = False

        for tok in tokenList.tokens:
            if isinstance(tok, sqlparse.sql.TokenList):
                subQuery = self.identifySubQueries(tok)
                if (subQuery and isinstance(tok, sqlparse.sql.Parenthesis)):
                    tok.ttype = SUBQUERY
            elif str(tok) == "select":
                isSubQuery = True
        return isSubQuery

    # 标识字面量和关键词等，为它们分配适当的标记类型
    def identifyLiterals(self, tokenList):
        blankTokens = [sqlparse.tokens.Name, sqlparse.tokens.Name.Placeholder]
        blankTokenTypes = [sqlparse.sql.Identifier]

        for tok in tokenList.tokens:
            if isinstance(tok, sqlparse.sql.TokenList): # 嵌套的标记集合
                tok.ptype = INTERNAL
                self.identifyLiterals(tok)
            elif (tok.ttype == sqlparse.tokens.Keyword or str(tok) == "select"): # 关键字或 "select" 字符串
                tok.ttype = KEYWORD
            elif (tok.ttype == sqlparse.tokens.Number.Integer or tok.ttype == sqlparse.tokens.Literal.Number.Integer): # 整数
                tok.ttype = INTEGER
            elif (tok.ttype == sqlparse.tokens.Number.Hexadecimal or tok.ttype == sqlparse.tokens.Literal.Number.Hexadecimal): # 十六进制数
                tok.ttype = HEX
            elif (tok.ttype == sqlparse.tokens.Number.Float or tok.ttype == sqlparse.tokens.Literal.Number.Float): # 浮点数
                tok.ttype = FLOAT
            elif (tok.ttype == sqlparse.tokens.String.Symbol or tok.ttype == sqlparse.tokens.String.Single or
                  tok.ttype == sqlparse.tokens.Literal.String.Single or tok.ttype == sqlparse.tokens.Literal.String.Symbol): # 字符串
                tok.ttype = STRING
            elif (tok.ttype == sqlparse.tokens.Wildcard): # 通配符
                tok.ttype = WILDCARD
            elif (tok.ttype in blankTokens or isinstance(tok, blankTokenTypes[0])): # 列名
                tok.ttype = COLUMN

    #  标识SQL查询中的函数调用
    def identifyFunctions(self, tokenList):
        for tok in tokenList.tokens:
            if (isinstance(tok, sqlparse.sql.Function)): # 标记是一个函数
                self.parseTreeSentinel = True
            elif (isinstance(tok, sqlparse.sql.Parenthesis)): # 标记是一个括号表达式
                self.parseTreeSentinel = False
            if self.parseTreeSentinel: # 标志为 True ，即当前标记位于函数内，类型设置为 FUNCTION
                tok.ttype = FUNCTION
            if isinstance(tok, sqlparse.sql.TokenList): # 标记是一个标记列表
                self.identifyFunctions(tok)

    # 标识并处理表名标识符
    def identifyTables(self, tokenList):
        if tokenList.ptype == SUBQUERY:
            self.tableStack.append(False)

        for i in range(len(tokenList.tokens)):
            # 对于每个标记 tok，检查它和前一个标记 prevtok
            prevtok = tokenList.tokens[i - 1]
            tok = tokenList.tokens[i]

            # 如果 tok 是一个点（.）且前一个标记被标记为列名，则前一个标记是一个表名
            if (str(tok) == "." and tok.ttype == sqlparse.tokens.Punctuation and prevtok.ttype == COLUMN):
                prevtok.ttype = TABLE

            # 如果 tok 是关键字 "from"，则后续的标记是表名
            elif (str(tok) == "from" and tok.ttype == sqlparse.tokens.Keyword):
                self.tableStack[-1] = True

            # 如果 tok 是某些关键字，则表示表名上下文的结束
            elif ((str(tok) == "where" or str(tok) == "on" or str(tok) == "group" or str(tok) == "order" or str(tok) == "union")
                  and tok.ttype == sqlparse.tokens.Keyword):
                self.tableStack[-1] = False

            # 如果 tok 是一个标记列表，则递归标识嵌套结构中的表名
            if isinstance(tok, sqlparse.sql.TokenList):
                self.identifyTables(tok)

            # 如果 tok 是列名，且当前处于表名上下文，则是表名
            elif (tok.ttype == COLUMN):
                if self.tableStack[-1]:
                    tok.ttype = TABLE

        # 完成子查询的处理，移除相应的元素
        if tokenList.ptype == SUBQUERY:
            self.tableStack.pop()

    def __str__(self):
        return ' '.join([str(tok) for tok in self.tokens])

    # 从解析树中提取标记并返回它们的字符串表示
    def parseSql(self):
        return [str(tok) for tok in self.tokens]


# 主函数：代码的tokens
def sqlang_code_parse(line):
    line = filter_part_invachar(line)  # 过滤或处理代码中的无效字符
    line = re.sub('\.+', '.', line)  # 替换连续的点号（.）为单个字符
    line = re.sub('\t+', '\t', line)  # 替换连续的制表符（\t）为单个字符
    line = re.sub('\n+', '\n', line)  # 替换连续的换行符（\n）为单个字符
    line = re.sub('>>+', '', line)  # 去除重定向运算符或其他连续的大于号（>）
    line = re.sub(' +', ' ', line)  # 将连续的空格替换为单个空格
    line = line.strip('\n').strip()  # 去除字符串首尾的换行符和空格
    line = re.findall(r"[\w]+|[^\s\w]", line)  # 标记化
    line = ' '.join(line)

    try:
        query = SqlangParser(line, regex=True)
        typedCode = query.parseSql()
        typedCode = typedCode[:-1]
        typedCode = inflection.underscore(' '.join(typedCode)).split(' ') # 骆驼命名转下划线
        cut_tokens = [re.sub("\s+", " ", x.strip()) for x in typedCode]
        token_list = [x.lower()  for x in cut_tokens] # 全部小写化
        token_list = [x.strip() for x in token_list if x.strip() != ''] # 列表里包含 '' 和' '
        return token_list
    except:
        return '-1000' # 存在为空的情况，词向量要进行判断


if __name__ == '__main__':
    print(sqlang_code_parse('""geometry": {"type": "Polygon" , 111.676,"coordinates": [[[6.69245274714546, 51.1326962505233], [6.69242714158622, 51.1326908883821], [6.69242919794447, 51.1326955158344], [6.69244041615532, 51.1326998744549], [6.69244125953742, 51.1327001609189], [6.69245274714546, 51.1326962505233]]]} How to 123 create a (SQL  Server function) to "join" multiple rows from a subquery into a single delimited field?'))
    print(query_parse("change row_height and column_width in libreoffice calc use python tagint"))
    print(query_parse('MySQL Administrator Backups: "Compatibility Mode", What Exactly is this doing?'))
    print(sqlang_code_parse('>UPDATE Table1 \n SET Table1.col1 = Table2.col1 \n Table1.col2 = Table2.col2 FROM \n Table2 WHERE \n Table1.id =  Table2.id'))
    print(sqlang_code_parse("SELECT\n@supplyFee:= 0\n@demandFee := 0\n@charedFee := 0\n"))
    print(sqlang_code_parse('@prev_sn := SerialNumber,\n@prev_toner := Remain_Toner_Black\n'))
    print(sqlang_code_parse(' ;WITH QtyCTE AS (\n  SELECT  [Category] = c.category_name\n          , [RootID] = c.category_id\n          , [ChildID] = c.category_id\n  FROM    Categories c\n  UNION ALL \n  SELECT  cte.Category\n          , cte.RootID\n          , c.category_id\n  FROM    QtyCTE cte\n          INNER JOIN Categories c ON c.father_id = cte.ChildID\n)\nSELECT  cte.RootID\n        , cte.Category\n        , COUNT(s.sales_id)\nFROM    QtyCTE cte\n        INNER JOIN Sales s ON s.category_id = cte.ChildID\nGROUP BY cte.RootID, cte.Category\nORDER BY cte.RootID\n'))
    print(sqlang_code_parse("DECLARE @Table TABLE (ID INT, Code NVARCHAR(50), RequiredID INT);\n\nINSERT INTO @Table (ID, Code, RequiredID)   VALUES\n    (1, 'Physics', NULL),\n    (2, 'Advanced Physics', 1),\n    (3, 'Nuke', 2),\n    (4, 'Health', NULL);    \n\nDECLARE @DefaultSeed TABLE (ID INT, Code NVARCHAR(50), RequiredID INT);\n\nWITH hierarchy \nAS (\n    --anchor\n    SELECT  t.ID , t.Code , t.RequiredID\n    FROM @Table AS t\n    WHERE t.RequiredID IS NULL\n\n    UNION ALL   \n\n    --recursive\n    SELECT  t.ID \n          , t.Code \n          , h.ID        \n    FROM hierarchy AS h\n        JOIN @Table AS t \n            ON t.RequiredID = h.ID\n    )\n\nINSERT INTO @DefaultSeed (ID, Code, RequiredID)\nSELECT  ID \n        , Code \n        , RequiredID\nFROM hierarchy\nOPTION (MAXRECURSION 10)\n\n\nDECLARE @NewSeed TABLE (ID INT IDENTITY(10, 1), Code NVARCHAR(50), RequiredID INT)\n\nDeclare @MapIds Table (aOldID int,aNewID int)\n\n;MERGE INTO @NewSeed AS TargetTable\nUsing @DefaultSeed as Source on 1=0\nWHEN NOT MATCHED then\n Insert (Code,RequiredID)\n Values\n (Source.Code,Source.RequiredID)\nOUTPUT Source.ID ,inserted.ID into @MapIds;\n\n\nUpdate @NewSeed Set RequiredID=aNewID\nfrom @MapIds\nWhere RequiredID=aOldID\n\n\n/*\n--@NewSeed should read like the following...\n[ID]  [Code]           [RequiredID]\n10....Physics..........NULL\n11....Health...........NULL\n12....AdvancedPhysics..10\n13....Nuke.............12\n*/\n\nSELECT *\nFROM @NewSeed\n"))



