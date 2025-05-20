import numpy as np
import pygad
from utils.matrix import Point,Point_List,get_point
from utils.input import tif,read_np_matrix
from utils.output import out_point2shp,np_matrix2tif


def Get_x_np(read_tif:tif,pt_list:Point_List,side_length = 10):
    '''根据图像中坐标获取通量矩阵
    read_tif：读取的通量tif文件
    pt_list：解集点列表
    side_length：正方形边长
    '''
    x_h = np.zeros((80,80))
    # 计算矩形范围
    half = int(side_length / 2)
    for pt in pt_list.point_list:
        col_offset = pt.col - half
        row_offset = pt.row - half
        for row in range(row_offset,row_offset+side_length):
            for col in range(col_offset,col_offset+side_length):
                value = read_tif.array[row][col]
                if x_h[row - row_offset][col-  col_offset] < value:
                    x_h[row - row_offset][col - col_offset] = value
    return x_h

def Get_H_np(read_H,mid_point,pt_list:Point_List,side_length = 10):
    '''根据图像中坐标获取足迹矩阵
    read_H：读取的足迹矩阵
    mid_point：读取的足迹矩阵中心点
    pt_list：解集点列表
    side_length：正方形边长
    '''
    H = np.zeros((80,80))
    half_length = int(H.shape[0] / 2)
    # 计算矩形范围
    half = side_length // 2
    for pt in pt_list.point_list:
        col_offset = pt.col - half - mid_point.col - half_length
        row_offset = pt.row - half - mid_point.row - half_length
        for row in range(row_offset,row_offset+side_length):
            for col in range(col_offset,col_offset+side_length):
                value = read_H[row][col]
                if H[row][col] < value:
                    H[row][col] = value
    return H

# 插值后通量数据读取
read_tif = tif("./out1km.tif")
# 中心点
mid_longitude = 112.7
mid_latitude = 35.4
center_point = get_point(mid_longitude,mid_latitude,read_tif.gt)
# 总体足迹矩阵
read_H = read_np_matrix("./footprints/",
                        gt=read_tif.gt)
np_matrix2tif(file_path="./footprints.tif",
              array=read_H,
              mid_point=center_point,
              half=40,
              gt=read_tif.gt)
def fitness_f(ga_instance,solution, solution_idx):
    '''适应度函数'''
    point_list = solution.tolist()
    pt_list = Point_List(solution=solution,
                         midpoint= center_point,
                         gt=read_tif.gt)
    # 计算通量
    x_h = Get_x_np(read_tif,pt_list)
    # 计算点积
    y_h = np.vdot(x_h,read_H)
    # 计算适应度
    return y_h

# 创建遗传算法实例
box = read_tif.box
ga_instance = pygad.GA(
    num_generations=200,
    num_parents_mating=10,
    fitness_func=fitness_f,
    sol_per_pop=50,
    num_genes=10,
    gene_type=int,
    gene_space=[# 五个点的坐标，每个坐标由两个基因表示，取值范围为-35到35的整数
        {'low': -35, 'high': 35,'step':1},
        {'low': -35, 'high': 35,'step':1},
        {'low': -35, 'high': 35,'step':1},
        {'low': -35, 'high': 35,'step':1},
        {'low': -35, 'high': 35,'step':1},
        {'low': -35, 'high': 35,'step':1},
        {'low': -35, 'high': 35,'step':1},
        {'low': -35, 'high': 35,'step':1},
        {'low': -35, 'high': 35,'step':1},
        {'low': -35, 'high': 35,'step':1},
        ],
    parent_selection_type= "tournament", # 锦标赛选择
    keep_parents=4,
    crossover_type="single_point",
    mutation_type="random",
    mutation_percent_genes=10
)
# 运行算法
ga_instance.run()
# 输出结果
solution, solution_fitness, _ = ga_instance.best_solution()
# 将图像坐标转换成经纬度坐标
solution = solution.tolist()
best_point_list = Point_List(solution=solution,
                         midpoint= center_point,
                         gt=read_tif.gt)
print("最优解为：")
print(best_point_list)
print(f"适应度: {solution_fitness}")
# 可视化
ga_instance.plot_fitness()
best_H = Get_H_np(read_H=read_H,
                 mid_point=center_point,
                 pt_list=best_point_list,
                 side_length=10)

# 保存点结果为shp文件
out_point2shp("./best_point", best_point_list)
# 保存H
np_matrix2tif(file_path="./best_H.tif",
              array=best_H,
              mid_point=center_point,
              half=40,
              gt=read_tif.gt)
              