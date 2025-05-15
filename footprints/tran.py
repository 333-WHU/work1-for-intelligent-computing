#  将稀疏矩阵转换成三元组列表
import pathlib
import numpy as np
import json

def tran(matrix):
    triple_list = []
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            if matrix[i][j] != 0:
                triple_list.append((i, j, matrix[i][j]))
    return triple_list

# 对于所有csv文件
length = 0
for file in pathlib.Path('./').glob('*.csv'):
    # 读取csv文件
    data = np.loadtxt(file, delimiter=',')
    # 转换成三元组列表
    triple_list = tran(data)
    length += len(triple_list)
    # 将三元组列表写入json文件,按相同行合并
    triple_list.sort(key=lambda x: x[0])
    row_list = []
    t_list = []
    for triple in triple_list:
        if triple[0] not in row_list:
            row_list.append(triple[0])
            t_list.append({"row": triple[0],
                            "col_and_value": []})
        t_list[-1]["col_and_value"].append((triple[1],triple[2]))
    with open(file.stem + '.json', 'w') as f:
        json.dump(t_list, f)


print("压缩率: ",length*3/270/270/49)