import pathlib
import numpy as np
from osgeo import gdal


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
class H_re:
    '''读取的分块矩阵'''
    def __init__(self,martrix,mid_latitude,mid_longitude,gt):
        self.martrix = martrix
        self.mid_latitude = mid_latitude
        self.mid_longitude = mid_longitude
        self.top_latitude = mid_latitude - 135 * gt[5]
        self.left_longitude = mid_longitude - 135 * gt[1]
        self.col_offset = int((self.left_longitude - gt[0])/gt[1])
        self.row_offset = int((self.top_latitude - gt[3])/gt[5])
        self.min_col = self.col_offset
        self.max_col = self.col_offset + 269
        self.min_row = self.row_offset
        self.max_row = self.row_offset + 269

def union_H_re(H_re_list:list[H_re]):
    # 合并多个H_re
    min_col = min([hre.min_col for hre in H_re_list])
    max_col = max([hre.max_col for hre in H_re_list])
    min_row = min([hre.min_row for hre in H_re_list])
    max_row = max([hre.max_row for hre in H_re_list])
    union_H = np.zeros((max_row - min_row + 1,max_col - min_col + 1))
    for row in range(min_row,max_row):
        for col in range(min_col,max_col):
            max_value = 0
            for hre in H_re_list:
                if hre.min_row <= row <= hre.max_row and hre.min_col <= col <= hre.max_col:
                    value = hre.martrix[row - hre.row_offset][col - hre.col_offset]
                    if max_value < value:
                        max_value = value
            union_H[row - min_row][col - min_col] = max_value
    return union_H,min_col,min_row


def read_np_matrix(file_folder,gt,range_size = 70, step = 10):
    # 读取np矩阵合成一个完整的矩阵
    logitude_left = gt[0]
    latitude_top = gt[3]
    H_list = []
    for file in pathlib.Path(file_folder).glob('*.csv'):
        data = np.loadtxt(file,delimiter=',')
        # 获取中心坐标
        file_name = file.stem
        information_list = file_name.split('_')
        mid_latitude = float(information_list[1])
        mid_longitude = float(information_list[2])
        H_re_i = H_re(data,mid_latitude,mid_longitude,gt)
        H_list.append(H_re_i)
    # 获取区域中心
    mid_latitude_list = [hre.mid_latitude for hre in H_list]
    mid_longitude_list = [hre.mid_longitude for hre in H_list]
    region_mid_latitude = sum(mid_latitude_list)/len(mid_latitude_list)
    region_mid_longitude = sum(mid_longitude_list)/len(mid_longitude_list)
    region_mid_col = int((region_mid_longitude - gt[0])/ gt[1])
    region_mid_row = int((region_mid_latitude - gt[3])/ gt[5])
    # 生成一个完整的矩阵
    read_H,min_col,min_row = union_H_re(H_list)
    #  截取范围内的矩阵
    half = int((range_size + step) / 2)
    read_H_min_col = region_mid_col - min_col - half
    read_H_min_row = region_mid_row - min_row - half
    read_H = read_H[read_H_min_row:read_H_min_row+2*half,read_H_min_col:read_H_min_col+2*half]
    return read_H

if __name__ == '__main__':
    read_tif = tif("./out1km.tif")
    read_H = read_np_matrix("./footprints/",read_tif.gt)
    print(read_H)
    with open('./0_0.csv',"w") as f:
        for row in read_H:
            for value in row:
                f.write(str(value) + ",")
            f.write("\n")
    