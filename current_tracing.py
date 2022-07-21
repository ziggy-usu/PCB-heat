from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
from pathfinding.core.diagonal_movement import DiagonalMovement
import numpy as np


class ElectricLoad:
    def __init__(self, name, current, path_start, path_end):
        self.name = name
        self.current = current
        self.path_start = path_start
        self.path_end = path_end


def find_current_path(path_start, path_end, mat_network):
    map_grid = Grid(matrix=np.transpose(mat_network))
    start = map_grid.node(path_start[0], path_start[1])
    end = map_grid.node(path_end[0], path_end[1])

    finder = AStarFinder(diagonal_movement=DiagonalMovement.always)

    [path, runs] = finder.find_path(start, end, map_grid)
    return path


def find_straight_path(path_start, path_end):
    path = []
    cursor_loc = np.asarray(path_start)
    path.append([cursor_loc[0], cursor_loc[1]])
    this_step = np.zeros([2], dtype=int)

    while not (path_end[0] == cursor_loc[0] and path_end[1] == cursor_loc[1]):
        this_step[0] = np.sign(path_end[0] - cursor_loc[0])
        this_step[1] = np.sign(path_end[1] - cursor_loc[1])
        cursor_loc = cursor_loc + this_step
        path.append([cursor_loc[0], cursor_loc[1]])

    return path


def find_middle_path(path_start, mat_network, short_path):
    steps = np.diff(np.transpose(np.asarray(short_path)))
    steps_trans = np.transpose(steps)
    p_orth = np.transpose([steps[1], -1 * steps[0]])
    way_points = []
    concat_path = []
    concat_steps = []
    way_points_back = 1

    cursor_loc = path_start
    for step in range(0, int(np.size(steps) / 2)):
        center_cell = cell_at_width_center(cursor_loc, mat_network, steps_trans[step], p_orth[step])
        way_points.append(center_cell)
        cursor_loc = cursor_loc + steps_trans[step]
    way_points.append(np.array(short_path[-1]))

    for way_point_no in range(1, len(way_points)):
        intermediate_path = find_straight_path(way_points[way_point_no-way_points_back], way_points[way_point_no])
        intermediate_steps = np.diff(np.asarray(intermediate_path), axis=0)
        l_path = len(intermediate_path)
        if l_path > 1:
            if len(concat_steps) > 0:
                step_direction_change = np.diff([concat_steps[-1], intermediate_steps[0]], axis=0)
                step_change_dist = np.linalg.norm(step_direction_change)
                if abs(step_change_dist) <= 1:
                    concat_path.extend(intermediate_path[:-1])
                    concat_steps.extend(intermediate_steps)
                    way_points_back = 1
                    if way_point_no == (len(way_points) - 1):
                        concat_path.extend([intermediate_path[-1]])
                else:
                    way_points_back = way_points_back + 1
            else:
                concat_path.extend(intermediate_path[:-1])
                concat_steps.extend(intermediate_steps)
                way_points_back = 1
        elif l_path == 1:
            way_points_back = way_points_back + 1

    return [tuple(x) for x in concat_path]  # concat_path


def cell_at_width_center(start_loc, mat_network, step, p_orth):
    # move from the current location in the path orthogonally until out of trace
    cursor_loc = start_loc

    trace_width = find_trace_width(cursor_loc, mat_network, step, p_orth)
    cursor_loc = cell_at_edge_of_width(start_loc, mat_network, p_orth)

    step_size = np.linalg.norm(step)
    step_progress = step_size

    while step_progress <= (trace_width / 2):
        cursor_loc = cursor_loc - p_orth
        step_progress = step_progress + step_size

    return cursor_loc


def set_res_values(start, end, mat_network, cell_thickness, material):
    short_path = find_current_path(start, end, mat_network)
    middle_path = find_middle_path(start, mat_network, short_path)
    acceptable_gap = np.linalg.norm(np.asarray(short_path[0]) - np.asarray(middle_path[0])) * 5
    if np.linalg.norm(np.asarray(short_path[-1]) - np.asarray(middle_path[-1])) <= acceptable_gap:
        path_taken = middle_path
    else:
        path_taken = short_path
    res_mat = calc_resistances(path_taken, start, end, material, cell_thickness, mat_network)
    # show_path(start, path_taken, res_mat)
    return res_mat


def show_path(start, path, matrix):
    steps = np.diff(np.transpose(np.asarray(path)))
    steps_trans = np.transpose(steps)

    cursor_loc = start
    matrix[cursor_loc[0], cursor_loc[1]] = -matrix[cursor_loc[0], cursor_loc[1]]
    for step in range(0, int(np.size(steps) / 2)):
        cursor_loc = cursor_loc + steps_trans[step]
        matrix[cursor_loc[0], cursor_loc[1]] = -matrix[cursor_loc[0], cursor_loc[1]]


def calc_resistances(path, path_start, path_end, material, cell_ht, mat_network):
    steps = np.diff(np.transpose(np.asarray(path)))
    steps_trans = np.transpose(steps)
    p_orth = np.transpose([steps[1], -1 * steps[0]])
    mat_resistance = np.zeros(mat_network.shape)

    rho = material_rho_lookup(material)

    path_loc = path_start
    for step in range(0, int(np.size(steps)/2)):
        cursor_loc = path_loc
        trace_width = find_trace_width(cursor_loc, mat_network, steps_trans[step], p_orth[step])

        # with width calculated, assign all cells along path to this width or resistance
        this_resistance = rho / (trace_width * trace_width * cell_ht)
        set_res_for_trace_width(cursor_loc, this_resistance, mat_resistance, mat_network, p_orth[step])

        # move to next step
        path_loc = path_loc + steps_trans[step]

    # for each cell in network that doesn't have a resistance, find the closest cell that does and set equal to that
    no_res_cells1 = mat_resistance == 0
    no_res_cells2 = mat_network == 1
    no_res_cells = np.argwhere(no_res_cells1 * no_res_cells2)
    res_cells = np.argwhere(mat_resistance != 0)

    for no_res_cell in no_res_cells:
        # np.linalg.norm(steps_trans[step])
        idx = np.linalg.norm((res_cells-no_res_cell), axis=1).argmin()
        this_res_loc = res_cells[idx]
        # this_res = mat_resistance[this_res_loc[0], this_res_loc[1]]
        mat_resistance[no_res_cell[0], no_res_cell[1]] = mat_resistance[this_res_loc[0], this_res_loc[1]]

    clipped_res_mat = clip_res_matrix(mat_resistance, mat_network, path_start, path_end, steps)
    smoothed_res_mat = smooth_matrix_non_zero(clipped_res_mat, 10)

    return smoothed_res_mat


def find_trace_width(path_loc, mat_network, step, p_orth):
    trace_width = 1
    cursor_loc = cell_at_edge_of_width(path_loc, mat_network, p_orth)

    # move in opposite direction until out of trace counting to find width
    while mat_network[cursor_loc[0], cursor_loc[1]] == 1:
        cursor_loc = cursor_loc - p_orth
        # if step is diagonal, add diagonal distance to trace width
        if np.linalg.norm(step) > 1:
            trace_width = trace_width + np.sqrt(2)
        else:
            trace_width = trace_width + 1
    return trace_width


def set_res_for_trace_width(this_location, this_resistance, mat_resistance, mat_network, p_orth):
    edge_cell = cell_at_edge_of_width(this_location, mat_network, p_orth)
    cursor_loc = edge_cell

    # with width calculated, assign all cells along path to this width or resistance
    while mat_network[cursor_loc[0], cursor_loc[1]] == 1:
        mat_resistance[cursor_loc[0], cursor_loc[1]] = this_resistance
        cursor_loc = cursor_loc - p_orth


def cell_at_edge_of_width(start_loc, mat_network, p_orth):
    # move from the current location in the path orthogonally until out of trace
    cursor_loc = start_loc
    while mat_network[cursor_loc[0], cursor_loc[1]] == 1:
        cursor_loc = cursor_loc + p_orth

    # move back one location, start trace width count
    cursor_loc = cursor_loc - p_orth
    return cursor_loc


def clip_res_matrix(in_matrix, mat_network, path_start, path_end, steps):
    steps_trans = np.transpose(steps)

    out_matrix = in_matrix

    # start location
    cursor_loc = path_start
    step = 0
    cursor_loc = cursor_loc - steps_trans[step]
    start_step = np.rint(np.mean(steps_trans[1:5], axis=0))
    start_step = start_step.astype(int)
    p_orth = [start_step[1], -1 * start_step[0]]
    cursor_loc = cursor_loc - start_step
    # check if the step is diagonal, if so, split up step movement to two half steps keeping orthogonal direction
    if np.prod(start_step) != 0:
        half_step_1 = [start_step[0], 0]
        half_step_2 = [0, start_step[1]]
        while mat_network[cursor_loc[0], cursor_loc[1]] == 1:
            set_res_for_trace_width(cursor_loc, 0, out_matrix, mat_network, p_orth)
            cursor_loc = cursor_loc - half_step_1
            set_res_for_trace_width(cursor_loc, 0, out_matrix, mat_network, p_orth)
            cursor_loc = cursor_loc - half_step_2
    else:
        while mat_network[cursor_loc[0], cursor_loc[1]] == 1:
            set_res_for_trace_width(cursor_loc, 0, out_matrix, mat_network, p_orth)
            cursor_loc = cursor_loc - start_step

    # end location
    cursor_loc = path_end
    step = len(steps_trans) - 1

    end_step = np.rint(np.mean(steps_trans[-5:-1], axis=0))
    end_step = end_step.astype(int)
    p_orth = [end_step[1], -1 * end_step[0]]
    cursor_loc = cursor_loc + end_step
    # check if the step is diagonal, if so, split up step movement to two half steps keeping orthogonal direction
    if np.prod(end_step) != 0:
        half_step_1 = [end_step[0], 0]
        half_step_2 = [0, end_step[1]]
        while mat_network[cursor_loc[0], cursor_loc[1]] == 1:
            set_res_for_trace_width(cursor_loc, 0, out_matrix, mat_network, p_orth)
            cursor_loc = cursor_loc + half_step_1
            set_res_for_trace_width(cursor_loc, 0, out_matrix, mat_network, p_orth)
            cursor_loc = cursor_loc + half_step_2
    else:
        while mat_network[cursor_loc[0], cursor_loc[1]] == 1:
            set_res_for_trace_width(cursor_loc, 0, out_matrix, mat_network, p_orth)
            cursor_loc = cursor_loc + end_step

    return out_matrix


def smooth_matrix_non_zero(in_matrix, radius):
    [nrow, ncol] = in_matrix.shape
    out_matrix = np.zeros_like(in_matrix)

    for row in range(0, nrow):
        for col in range(0, ncol):
            mat_val = in_matrix[row, col]
            if in_matrix[row, col] > 0:
                nei_row_start = max(row - radius, 0)
                nei_col_start = max(col - radius, 0)
                nei_vals = [in_matrix[row, col]]
                for nei_row in range(nei_row_start, min(row + radius, nrow)):
                    for nei_col in range(nei_col_start, min(col + radius, ncol)):
                        if not (nei_row == row and nei_col == col):
                            if in_matrix[nei_row, nei_col] > 0:
                                nei_vals.append(in_matrix[nei_row, nei_col])
                ave_val = np.average(np.asarray(nei_vals))
                out_matrix[row, col] = ave_val

    return out_matrix


def material_rho_lookup(material):
    # https://www.thoughtco.com/table-of-electrical-resistivity-conductivity-608499
    switch = {
        'Copper': 6.61e-4,
        'Aluminum': 8.98e-4,
        'Gold': 9.61E-04,
        'Silver': 6.26E-04,
        'Nickel': 2.75E-03
    }
    # units: ohm mil
    return switch.get(material)


