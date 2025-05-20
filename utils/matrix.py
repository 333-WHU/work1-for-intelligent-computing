import numpy as np

class Point:
    def __init__(self, col, row,gt):
        self.col = col
        self.row = row
        self.longitude = gt[0] + col * gt[1] + row * gt[2]
        self.latitude = gt[3] + col * gt[4] + row * gt[5]
        self.gt = gt

def get_point(longitude, latitude, gt):
    col = int((longitude - gt[0]) / gt[1])
    row = int((latitude - gt[3]) / gt[5])
    return Point(col, row, gt)

class Point_List:
    def __init__(self, solution,midpoint,gt):
        self.point_list = []
        for i in range(0,5):
            point = Point(solution[2*i]+midpoint.col,
                        solution[2*i+1]+midpoint.row,
                        gt)
            self.point_list.append(point)

    def __str__(self):
        stream = ""
        for point in self.point_list:
            stream += str(point.longitude) + " " + str(point.latitude) +"\t" + str(point.col) + " " + str(point.row) +"\n"
        return stream
        