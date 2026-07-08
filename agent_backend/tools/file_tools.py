# 读文件
def read_flie(path:str):
    with open(path,"r",encoding="utf-8") as f:
        return f.read()

# 写文件
def write_flie(path:str , content:str):
    with open(path,"w",encoding="utf-8") as f:
        f.write(content)

# 清空文件内容
def clear_flie(path:str):
    with open(path,"w",encoding="utf-8") as f:
        f.write("")