import os
import requests
from requests.auth import HTTPBasicAuth
import rasterio
from rasterio.transform import Affine
import pandas as pd  # 新增pandas库用于处理CSV文件

# 确保中文显示正常
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
plt.rcParams["axes.unicode_minus"] = False  # 正确显示负号


class GeoServerPublisher:
    def __init__(self, base_url, username, password, workspace):
        """初始化GeoServer连接"""
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.workspace = workspace
        self.auth = HTTPBasicAuth(username, password)
        self.headers = {'Content-Type': 'application/xml; charset=utf-8'}

    def create_workspace(self):
        """创建GeoServer工作区"""
        url = f"{self.base_url}/workspaces"
        data = f'<workspace><name>{self.workspace}</name></workspace>'

        response = requests.post(url, data=data.encode('utf-8'), headers=self.headers, auth=self.auth)
        if response.status_code == 201:
            print(f"工作区 '{self.workspace}' 创建成功")
        elif response.status_code == 409:
            print(f"工作区 '{self.workspace}' 已存在")
        else:
            print(f"创建工作区失败: {response.text}")

    def publish_raster(self, raster_path, layer_name, srs='EPSG:4326'):
        """发布栅格数据(WMS/WMTS/WCS)"""
        store_name = f"{layer_name}_store"

        # 创建覆盖存储
        coverage_url = f"{self.base_url}/workspaces/{self.workspace}/coveragestores"
        store_data = f"""
        <coverageStore>
            <name>{store_name}</name>
            <type>GeoTIFF</type>
            <url>file://{os.path.abspath(raster_path)}</url>
            <workspace>
                <name>{self.workspace}</name>
            </workspace>
        </coverageStore>
        """
        response = requests.post(coverage_url, data=store_data.encode('utf-8'), headers=self.headers, auth=self.auth)
        if response.status_code not in (201, 409):
            print(f"创建栅格存储失败: {response.text}")
            return False

        # 发布图层
        layer_url = f"{coverage_url}/{store_name}/coverages"
        layer_data = f"""
        <coverage>
            <name>{layer_name}</name>
            <title>{layer_name}</title>
            <srs>{srs}</srs>
            <enabled>true</enabled>
        </coverage>
        """
        response = requests.post(layer_url, data=layer_data.encode('utf-8'), headers=self.headers, auth=self.auth)
        if response.status_code not in (201, 409):
            print(f"发布栅格图层失败: {response.text}")
            return False

        print(f"栅格图层 '{layer_name}' 发布成功 (支持WMS/WMTS/WCS)")
        return True

    def publish_vector(self, shp_path, layer_name, srs='EPSG:4326'):
        """发布矢量数据(WFS)"""
        store_name = f"{layer_name}_store"

        # 创建数据存储（使用Shapefile）
        store_url = f"{self.base_url}/workspaces/{self.workspace}/datastores"
        store_data = f"""
        <dataStore>
            <name>{store_name}</name>
            <type>Shapefile</type>
            <connectionParameters>
                <parameter><name>url</name><value>file://{os.path.abspath(shp_path)}</value></parameter>
            </connectionParameters>
        </dataStore>
        """
        response = requests.post(store_url, data=store_data.encode('utf-8'), headers=self.headers, auth=self.auth)
        if response.status_code not in (201, 409):
            print(f"创建矢量存储失败: {response.text}")
            return False

        # 发布图层
        layer_url = f"{store_url}/{store_name}/featuretypes"
        layer_data = f"""
        <featureType>
            <name>{layer_name}</name>
            <title>{layer_name}</title>
            <srs>{srs}</srs>
            <enabled>true</enabled>
            <store class="dataStore"><name>{store_name}</name></store>
        </featureType>
        """
        response = requests.post(layer_url, data=layer_data.encode('utf-8'), headers=self.headers, auth=self.auth)
        if response.status_code not in (201, 409):
            print(f"发布矢量图层失败: {response.text}")
            return False

        print(f"矢量图层 '{layer_name}' 发布成功 (支持WFS)")
        return True

    def enable_wmts_for_layer(self, layer_name):
        """为图层启用WMTS服务"""
        url = f"{self.base_url}/workspaces/{self.workspace}/layers/{layer_name}"
        data = """
        <layer>
            <enabled>true</enabled>
            <advertised>true</advertised>
            <metadata>
                <entry key="WMTS_ENABLED">true</entry>
            </metadata>
        </layer>
        """
        response = requests.put(url, data=data.encode('utf-8'), headers=self.headers, auth=self.auth)
        if response.status_code == 200:
            print(f"WMTS服务已启用 for {layer_name}")
        else:
            print(f"启用WMTS失败: {response.text}")

    def delete_vector_store(self, store_name):
        """删除矢量存储"""
        url = f"{self.base_url}/workspaces/{self.workspace}/datastores/{store_name}"
        params = {'recurse': 'true'}
        response = requests.delete(url, auth=self.auth, params=params)
        if response.status_code == 200:
            print(f"矢量存储 '{store_name}' 删除成功")
        else:
            print(f"删除矢量存储失败: {response.text}")

    def delete_raster_store(self, store_name):
        """删除栅格存储"""
        url = f"{self.base_url}/workspaces/{self.workspace}/coveragestores/{store_name}"
        params = {'recurse': 'true'}
        response = requests.delete(url, auth=self.auth, params=params)
        if response.status_code == 200:
            print(f"栅格存储 '{store_name}' 删除成功")
        else:
            print(f"删除栅格存储失败: {response.text}")


def publish_data_to_geoserver(shp_path, tif_path, geoserver_config):
    """
    将TIFF文件发布到GeoServer

    参数:
    - tif_path: TIFF文件路径
    - geoserver_config: GeoServer配置字典，包含base_url, username, password, workspace
    """
    # 创建GeoServer发布器实例
    publisher = GeoServerPublisher(
        base_url=geoserver_config['base_url'],
        username=geoserver_config['username'],
        password=geoserver_config['password'],
        workspace=geoserver_config['workspace']
    )
    # 创建工作区
    publisher.create_workspace()

    # 发布TIFF数据(WMS/WMTS/WCS服务)
    layer_name = "methane_footprint"
    print(f"\n正在发布TIFF数据...")

    try:
        success = publisher.publish_raster(
            raster_path=tif_path,
            layer_name=layer_name,
            srs='EPSG:4326'
        )

        if success:
            # 确保为图层启用WMTS服务
            publisher.enable_wmts_for_layer(layer_name)

            print(f"TIFF数据已成功发布为WMS/WMTS/WCS服务")
            print(f"WMS服务URL: {geoserver_config['base_url']}/wms?service=WMS&version=1.3.0&request=GetCapabilities")
            print(f"WMTS服务URL: {geoserver_config['base_url']}/wmts?REQUEST=GetCapabilities&SERVICE=WMTS")
            print(f"WCS服务URL: {geoserver_config['base_url']}/wcs?service=WCS&version=2.0.1&request=GetCapabilities")

            # 打印GeoServer图层预览URL
            preview_url = f"{geoserver_config['base_url'].replace('/rest', '')}/web/?wicket:bookmarkablePage=:org.geoserver.web.demo.MapPreviewPage"
            print(f"\n你可以在GeoServer管理界面预览这些图层: {preview_url}")
            print(f"图层名称: {geoserver_config['workspace']}:{layer_name}")

    except Exception as e:
        print(f"发布TIFF文件失败: {str(e)}")


if __name__ == "__main__":
    # 配置GeoServer连接信息
    geoserver_config = {
        'base_url': 'http://localhost:8080/geoserver/rest',  # GeoServer REST API地址
        'username': 'admin',  # GeoServer管理员用户名
        'password': 'geoserver',  # GeoServer管理员密码
        'workspace': 'ccccss'  # 工作区名称
    }

    # TIFF文件路径
    tif_path = './best_h_matrix.tif'  # 替换为实际的TIFF文件路径

    # 检查文件是否存在
    if not os.path.exists(tif_path):
        print(f"错误: TIFF文件 '{tif_path}' 不存在")
    else:
        # 发布数据到GeoServer
        publish_data_to_geoserver(None, tif_path, geoserver_config)
