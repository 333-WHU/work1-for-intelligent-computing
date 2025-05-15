from osgeo import gdal
import os

input_path = "./Global_Fuel_Exploitation_Inventory_v2_2019_Total_Fuel_Exploitation.tif"
output_path = "./out1km.tif"
# 设置GDAL异常处理
gdal.UseExceptions()

try:
    # 关键参数设置
    warp_options = gdal.WarpOptions(
        format='GTiff',
        xRes=0.01,  # 1km分辨率（单位：度）
        yRes=0.01,
        resampleAlg='bilinear',
        outputType=gdal.GDT_Float32,
        dstNodata=-9999  # 明确设置NODATA值
    )
    
    # 执行重采样
    gdal.Warp(
        destNameOrDestDS=output_path,
        srcDSOrSrcDSTab=input_path,
        options=warp_options
    )
    print(f"成功生成: {output_path}")

except Exception as e:
    print(f"处理失败: {str(e)}")
    # 清理可能生成的不完整文件
    if os.path.exists(output_path):
        os.remove(output_path)
