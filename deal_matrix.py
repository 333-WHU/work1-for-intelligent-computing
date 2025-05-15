import pathlib
import json
import numpy as np
from osgeo import gdal

class Point:
    def __init__(self, x, y,gt):
        self.x = x
        self.y = y
        self.longitude = gt[0] + x * gt[1] + y * gt[2]
        self.latitude = gt[3] + x * gt[4] + y * gt[5]
class triple:
    """稀疏矩阵三元组表示的矩阵的一行"""
    def __init__(self, row):
        self.row = row
        self.col_and_value = []
        self.max_col = 0
        self.min_col = 0
        self.first_add = True
    
    def add(self, col, value):
        """添加元素"""
        self.col_and_value.append([col, value])
        if self.first_add:
            self.max_col = col
            self.min_col = col
            self.first_add = False
        if self.max_col < col:
            self.max_col = col
        if self.min_col > col:
            self.min_col = col
    def union(self,triple2):
        """和相同行的矩阵行合并，相同的列取最大值"""
        if self.row != triple2.row: # 行号不同,不合并
            return 0
        else:
            col_list = [col for col,value in self.col_and_value]
            for col,value in triple2.col_and_value:
                # 如果列号不同添加列号
                if col not in col_list:
                    self.add(col,value)
                    col_list.append(col)
                    continue
                # 如果列号相同取最大值
                for i in range(len(self.col_and_value)):
                    if self.col_and_value[i][0] == col:
                        self.col_and_value[i][1] = max(self.col_and_value[i][1],value)        
    def copy(self):
        """复制一份"""
        t = triple(self.row)
        for col,value in self.col_and_value:
            t.add(col,value)
        return t
    def mutiple(self, triple2)->float:
        """矩阵点积"""
        if self.row != triple2.row:
            return 0
        else:
            result = 0
            for col,value in self.col_and_value:
                for col2,value2 in triple2.col_and_value:
                    if col == col2:
                        result += value * value2
            return result
class triple_list:
    """稀疏矩阵三元组表示的分块矩阵"""
    def __init__(self,latitude,longitude):
        self.latitude = latitude
        self.longitude = longitude
        self.triple_list = []
        self.min_row = 0
        self.max_row = 0
        self.min_col = 0
        self.max_col = 0
        self.first_add = True

    def add(self,triple:triple):
        """添加一行"""
        self.triple_list.append(triple)
        if self.first_add:
            self.max_row = triple.row
            self.min_row = triple.row
            self.min_col = triple.min_col
            self.max_col = triple.max_col
            self.first_add = False
        if self.max_row < triple.row:
            self.max_row = triple.row
        if self.min_row > triple.row:
            self.min_row = triple.row
        if self.max_col < triple.max_col:
            self.max_col = triple.max_col
        if self.min_col > triple.min_col:
            self.min_col = triple.min_col
    def union(self,triple2:triple):
        """矩阵合并一行的数据"""
        row_list = [t.row for t in self.triple_list]
        if triple2.row not in row_list:
            self.add(triple2)
        else:
            for i in range(len(self.triple_list)):
                if self.triple_list[i].row == triple2.row:
                    self.triple_list[i].union(triple2)
                    break
    def add_offset(self,offset_x, offset_y):
        """添加偏移量"""
        for triple in self.triple_list:
            triple.row += offset_x
            for col,value in triple.col_and_value:
                col += offset_y

    def copy(self):
        """复制一份"""
        t = triple_list(self.latitude,self.longitude)
        for triple in self.triple_list:
            t.add(triple.copy())
        return t

    def mutiple(self,triple_list2)->float:
        """矩阵点积"""
        result = 0
        for triple in self.triple_list:
            for triple2 in triple_list2.triple_list:
                if triple.row == triple2.row:
                    result += triple.mutiple(triple2)
        return result
    
    def __getitem__(self, row_col):
        if len(row_col)==2:
            row,col = row_col
            for triple in self.triple_list:
                if triple.row == row:
                    for col2,value in triple.col_and_value:
                        if col2 == col:
                            return value
                    return 0
            return 0
        else:
            return 0

    def Get_H(self,pt_list:list[Point],side_length = 10):
        '''根据点集获取足迹矩阵'''
        H = triple_list(self.latitude,self.longitude)
        for pt in pt_list:
            # 根据经纬度在矩阵中找到以它为中心10x10区域
            # 计算图像坐标
            center_x = int((pt.longitude-self.longitude) * 10)+135
            center_y = int((pt.latitude-self.latitude) * 10)+135
            half = side_length // 2
            x_left = center_x - half
            y_top = center_y - half
            for i in (x_left,x_left+side_length):
                t = triple(i)
                for j in (y_top,y_top+side_length):
                    value = self[i,j]
                    if value:
                        t.add(j,value)
                if t.col_and_value:
                    H.union(t)
        return H
    def matrix2tif(self,file_path,gt):
        """将矩阵保存为tif文件,gt用于获取分辨率"""
        driver = gdal.GetDriverByName('GTiff')
        rows = self.max_row - self.min_row + 1
        cols = self.max_col - self.min_col + 1
        print(rows,cols)
        x_left = self.longitude + self.min_col * gt[1]
        y_top = self.latitude - self.max_row * gt[5]
        offset_x = -self.min_row
        offset_y = -self.min_col
        dataset = driver.Create(file_path, cols, rows, 1, gdal.GDT_Float32)
        dataset.SetGeoTransform((x_left, gt[1], 0, y_top, 0, gt[5]))
        band = dataset.GetRasterBand(1)
        band.SetNoDataValue(0)
        array = np.zeros((rows, cols))
        for triple in self.triple_list:
            row = triple.row + offset_x
            for col2,value in triple.col_and_value:
                col = col2 + offset_y
                array[row,col] = value
        band.WriteArray(array)
        dataset.FlushCache()
        dataset = None
        band = None
        driver = None
        

        
        

def read_martix(file_folder):
    # 对于所有的json文件,合并为一个完整的矩阵
    mid_longitude = 112.7
    mid_latitude = 35.4
    H = triple_list(mid_latitude,mid_longitude)
    for file in pathlib.Path(file_folder).glob('*.json'):
        with open(file, 'r') as f:
            # 分割filename
            filename = file.stem
            information_list = filename.split('_')
            # 获取中心坐标
            center_latitude = float(information_list[1])            
            center_longitude = float(information_list[2])
            data = json.load(f)
            # 偏移量
            offset_x = int((center_latitude - H.latitude) * 10)
            offset_y = int((center_longitude - H.longitude) * 10)
            for row_data in data: # 对每一行进行
                # 获取行号
                row = row_data['row'] + offset_x
                # 生成一个triple
                triple_row = triple(row)
                # 获取列号和通量值
                for col,value in row_data['col_and_value']:
                    col = col + offset_y
                    triple_row.add(col,value)
                H.union(triple_row)
    return H
            



class tif:
    def __init__(self,file_path):
        self.file_path = file_path
        self.dataset = gdal.Open(file_path)
        self.gt = self.dataset.GetGeoTransform()
        self.band = self.dataset.GetRasterBand(1)
        self.array = self.band.ReadAsArray()
        self.width = self.dataset.RasterXSize  # 列数
        self.height = self.dataset.RasterYSize  # 行数
        self.box = {'left': self.gt[0],
                'top': self.gt[3], 
                'right': self.gt[0] + self.gt[1] * self.width,
                'bottom': self.gt[3] + self.gt[5] * self.height,
                'width': self.width,
                'height': self.height
                }
        self.NODATA = self.band.GetNoDataValue()
    def Get_x(self,pt_list:list[Point],center_point:Point,side_length = 10)->triple_list:
        '''根据图像中坐标获取通量值,x,y为中心行列号，返回长度为10的方阵'''
        x_h = triple_list(center_point.latitude,center_point.longitude)
        # 计算矩形范围
        half = side_length // 2
        for pt in pt_list:
            # 根据经纬度在矩阵中找到以它为中心10x10区域
            x_left = max(0,pt.x - half)
            y_top = max(0,pt.y - half)
            x_right = min(self.width,pt.x + half)
            y_bottom = min(self.height,pt.y + half)
            for i in range(x_left,x_right):
                row = i - center_point.x +135
                t = triple(row)
                for j in range(y_top,y_bottom):
                    col = j - center_point.y +135
                    value = self.array[j,i]
                    if value != self.NODATA:
                        t.add(col,value)
                if t.col_and_value:
                    x_h.union(t)
        return x_h


if __name__ == '__main__':
    from time import time
    start = time()
    total_triple = read_martix('./footprints/')
    print(total_triple.max_row,np.max([t.max_col for t in total_triple.triple_list]))
    print(total_triple.min_row,np.min([t.min_col for t in total_triple.triple_list]))
    end = time()
    print(end-start)
