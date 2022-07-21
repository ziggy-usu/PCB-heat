import numpy as np
from enum import Enum
from shapely.geometry import Polygon, Point
from math import ceil, floor, sqrt


class Component:
    def __init__(self, name, dims, location, heat_generated, side):
        self.name = name
        [self.width, self.length] = dims
        [self.x, self.y] = location
        self.heat = heat_generated
        self.side = side


class Circle:
    def __init__(self, f_id, radius):
        self.f_id = f_id
        self.radius = radius


class Rectangle:
    def __init__(self, f_id, width, height):
        self.f_id = f_id
        self.width = width
        self.height = height


class Oval:
    def __init__(self, f_id, width, height):
        self.f_id = f_id
        self.width = width
        self.height = height


class Line:
    def __init__(self, f_id, x_start, y_start, x_end, y_end, radius):
        self.f_id = f_id
        self.x_start = x_start
        self.y_start = y_start
        self.x_end = x_end
        self.y_end = y_end
        self.radius = radius


class Pour:
    def __init__(self, f_id, points):
        self.f_id = f_id
        self.points = points


class Simulation:
    def __init__(self, resolution, ambient_c, board_orientation, show_process, cond_in_plane_k, cond_thru_plane_k,
                 diel_in_plane_k, diel_thru_plane_k, conv_coef, rad_coef, rad_pow, comp_htc_coef):
        self.resolution = resolution
        self.ambient = ambient_c
        self.board_orientation = board_orientation
        self.show_process = show_process
        self.cond_k_coef = [cond_thru_plane_k, cond_in_plane_k, cond_in_plane_k]
        self.diel_k_coef = [diel_thru_plane_k, diel_in_plane_k, diel_in_plane_k]
        self.conv_coef = conv_coef
        self.rad_coef = rad_coef
        self.rad_pow = rad_pow
        self.comp_htc_coef = comp_htc_coef


class Cell(Enum):
    CONDUCTOR = -1
    AIR = -2
    INSULATOR = 0


def trace_circle(cond_mat, x_center, y_center, radius, res, cell_value):
    # https://www.redblobgames.com/grids/circle-drawing/
    top = floor((y_center - radius) / res)
    bottom = ceil((y_center + radius) / res)
    left = floor((x_center - radius) / res)
    right = ceil((x_center + radius) / res)

    for y in range(top, bottom):
        for x in range(left, right):
            dx = (x_center / res) - x
            dy = (y_center / res) - y
            dist_sq = dx*dx + dy*dy
            if dist_sq <= ((radius*radius) / res / res):
                cond_mat[x, y] = cell_value


def trace_line(cond_mat, x_start, y_start, x_end, y_end, radius, res, cell_value):
    # draw circles from start to end with some increment
    dx = x_end - x_start
    dy = y_end - y_start
    x_trace = x_start
    y_trace = y_start
    x_trace_prev = 0
    y_trace_prev = 0
    leng = sqrt(dx*dx + dy*dy)
    for p in range(0, floor(leng)):
        if floor(x_trace_prev) != floor(x_trace) or floor(y_trace_prev) != floor(y_trace):
            trace_circle(cond_mat, floor(x_trace), floor(y_trace), radius, res, cell_value)
        x_trace_prev = x_trace
        y_trace_prev = y_trace
        x_trace = x_trace + dx/leng
        y_trace = y_trace + dy/leng


def trace_rectangle(cond_mat, x_center, y_center, width, height, res, cell_value):
    top = floor((y_center - height/2) / res)
    bottom = ceil((y_center + height/2) / res)
    left = floor((x_center - width/2) / res)
    right = ceil((x_center + width/2) / res)

    for y in range(top, bottom):
        for x in range(left, right):
            cond_mat[x, y] = cell_value


def trace_oval(cond_mat, x_center, y_center, width, height, res, cell_value):
    if width > height:
        # left right circles
        width_sm = width - height
        trace_circle(cond_mat, floor(x_center - width_sm / 2), y_center, floor(height / 2), res, cell_value)
        trace_circle(cond_mat, ceil(x_center + width_sm / 2), y_center, floor(height / 2), res, cell_value)
        trace_rectangle(cond_mat, x_center, y_center, width_sm, height, res, cell_value)
    else:
        # top bottom circles
        height_sm = height - width
        trace_circle(cond_mat, x_center, floor(y_center - height_sm / 2), floor(width / 2), res, cell_value)
        trace_circle(cond_mat, x_center, ceil(y_center + height_sm / 2), floor(width / 2), res, cell_value)
        trace_rectangle(cond_mat, x_center, y_center, width, height_sm, res, cell_value)


def trace_pour(cond_mat, points, res, cell_value):
    pour_points = np.array(points) / res
    poly_pour = Polygon(pour_points)
    bounds = poly_pour.bounds

    for y in range(int(bounds[1]), int(bounds[3])):
        for x in range(int(bounds[0]), int(bounds[2])):
            P = Point(x, y)
            if poly_pour.contains(P):
                cond_mat[x, y] = cell_value
