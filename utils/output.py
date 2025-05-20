import os
from osgeo import ogr,osr,gdal
from utils.matrix import Point,Point_List

def out_point2shp(file_path,point_list:Point_List):
    """将点输出为shp文件"""
    # 创建数据源（Shapefile）
    driver = ogr.GetDriverByName("ESRI Shapefile")
    if os.path.exists(file_path):
        driver.DeleteDataSource(file_path)  # 如果文件已存在，删除
    ds = driver.CreateDataSource(file_path)
    # 定义空间参考（WGS84坐标系）
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)  # EPSG:4326 是 WGS84 经纬度坐标系
    # 创建图层（点类型）
    layer = ds.CreateLayer("best_points", srs, ogr.wkbPoint)
    # 6. 遍历点数据，写入几何和属性
    for point in point_list.point_list:
        # 创建点几何
        geom = ogr.Geometry(ogr.wkbPoint)
        geom.AddPoint(point.longitude, point.latitude)
        # 创建要素（Feature）
        feature = ogr.Feature(layer.GetLayerDefn())
        feature.SetGeometry(geom)
        # 将要素写入图层
        layer.CreateFeature(feature)
        feature = None  # 释放资源
    # 7. 关闭数据源
    ds = None
    print(f"Shapefile 已生成: {file_path}")


def np_matrix2tif(file_path,array,mid_point:Point,half,gt):
    """将矩阵保存为tif文件,gt用于获取分辨率"""
    driver = gdal.GetDriverByName('GTiff')
    logitude_left = mid_point.longitude - half * gt[1]
    latitude_top = mid_point.latitude - half * gt[5]
    dataset = driver.Create(file_path, array.shape[1], array.shape[0], 1, gdal.GDT_Float32)
    dataset.SetGeoTransform((logitude_left, gt[1], 0, latitude_top, 0, gt[5]))
    band = dataset.GetRasterBand(1)
    band.SetNoDataValue(0.0)
    band.WriteArray(array)
    dataset.FlushCache()
    dataset = None
    band = None
    driver = None