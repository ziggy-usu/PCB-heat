import numpy as np

import current_tracing
import tracer

mm_to_mil = 1000 / 25.4


def get_board_dims(keep_out_lines):
    sig_dig = find_sig_digit(keep_out_lines)

    # find units
    units = find_units(keep_out_lines)

    # find overall dims
    return find_overall_dims(keep_out_lines, units, sig_dig)


def find_overall_dims(keep_out_lines, units, sig_dig):
    width = 0
    height = 0
    feature_id = 'x'
    feature_active = 'none'
    # first, find line that indicates new feature
    for line in keep_out_lines:
        if line.startswith('%AD'):
            feature_arr = line.split(',')
            feature_id_str = feature_arr[0]
            feature_id = feature_id_str[3:-1] + '*\n'

        if line == feature_id:
            feature_active = feature_id

        if feature_active == feature_id:
            # find x dim -> width
            line_x = line.find('X')
            line_y = line.find('Y')
            line_d = line.find('D')
            if line_x != -1:
                if line_y != -1:
                    width = float(line[line_x + 1: line_y]) * sig_dig
                else:
                    width = float(line[line_x + 1: line_d]) * sig_dig

            # find y dim -> height
            if line_y != -1:
                height = float(line[line_y + 1: line_d]) * sig_dig

        if width != 0 and height != 0:
            break

    return [width, height]


def find_units(keep_out_lines):
    units = 'in'
    for line in keep_out_lines:
        if line.startswith('%MO'):
            if line.endswith('IN*%\n'):
                units = 'in'
            elif line.endswith('MM*%\n'):
                units = 'mm'
            break
    return units


def find_sig_digit(keep_out_lines):
    sig_dig = 1
    for line in keep_out_lines:
        if line.startswith('%FSLA'):
            if line.endswith('X23Y23*%\n'):
                sig_dig = 1
            elif line.endswith('X24Y24*%\n'):
                sig_dig = 0.1
            elif line.endswith('X25Y25*%\n'):
                sig_dig = 0.01
            elif line.endswith('X42Y42*%\n'):
                sig_dig = 0.01 * mm_to_mil
            elif line.endswith('X43Y43*%\n'):
                sig_dig = 0.001 * mm_to_mil
            elif line.endswith('X44Y44*%\n'):
                sig_dig = 0.0001 * mm_to_mil
            break
    return sig_dig

class Layer:
    def __init__(self, name, layer_type, lines, cond_material, thickness_val, thickness_type, dims, simulation, loads):
        self.name = name
        self.layer_type = layer_type
        self.lines = lines
        self.cond_material = cond_material
        self.thickness = self.convert_layer_thickness(thickness_val, thickness_type)
        self.width = int(dims[0])
        self.height = int(dims[1])
        self.simulation = simulation
        self.sim_res = self.simulation.resolution
        self.cond_mat = np.zeros([int(self.width / self.sim_res), int(self.height / self.sim_res)], dtype=int)
        self.res_mat = np.zeros(np.shape(self.cond_mat), dtype=float)
        self.Q_mat = np.zeros(np.shape(self.cond_mat), dtype=float)
        self.loads = loads

        if not isinstance(lines, type(None)):
            self.sig_dig = find_sig_digit(lines)
            self.units = find_units(lines)

    def trace_layer(self):
        # go line by line instructions
        feature_list = []
        this_feature_id = 'none'
        x_trace = -1.0
        y_trace = -1.0
        x_trace_prev = x_trace
        y_trace_prev = y_trace
        draw_trace = False
        pour_count = 0

        for line in self.lines:
            # if feature call out, add to feature array
            if line.startswith('%AD'):
                feature_arr = line.split(',')
                feature_id_str = feature_arr[0]
                feature_dim_str = feature_arr[1]

                feature_id = feature_id_str[3:-1] + '*\n'
                feature_class = feature_id_str[-1]
                if feature_class == 'C':
                    if self.units == 'in':
                        feature_rad = float(feature_dim_str[0:-3]) * 500
                    else:
                        feature_rad = float(feature_dim_str[0:-3]) * mm_to_mil / 2
                    new_feature = tracer.Circle(feature_id, feature_rad)

                elif feature_class == 'R' or feature_class == 'O':
                    feature_dims = feature_dim_str[0:-3].split('X')
                    if self.units == 'in':
                        feature_width = float(feature_dims[0]) * 1000
                        feature_height = float(feature_dims[1]) * 1000
                    else:
                        feature_width = float(feature_dims[0]) * mm_to_mil
                        feature_height = float(feature_dims[1]) * mm_to_mil

                    if feature_class == 'R':
                        new_feature = tracer.Rectangle(feature_id, feature_width, feature_height)
                    elif feature_class == 'O':
                        new_feature = tracer.Oval(feature_id, feature_width, feature_height)

                feature_list.append(new_feature)

            # if feature, start tracing
            elif line.startswith('D') and not line.startswith('D02') and not line.startswith('D03'):
                draw_trace = True
                which_feature = 0
                this_feature_id = line
                for feature in feature_list:

                    if feature.f_id == this_feature_id:
                        break
                    which_feature = which_feature + 1

            elif line.startswith('G36'):
                # start of pour feature
                draw_trace = False
                this_feature_id = 'pour'
                pour_points = []
                pour_count = pour_count + 1

            elif line.startswith('G37'):
                # end of pour feature
                draw_trace = True
                this_feature_id = 'pour_done'
                new_feature = tracer.Pour('pour' + str(pour_count), pour_points)
                feature_list.append(new_feature)
                tracer.trace_pour(self.cond_mat, pour_points, self.sim_res, tracer.Cell.CONDUCTOR.value)

            elif this_feature_id == 'pour':
                # Begin gathering points for pour
                [x_trace, y_trace, x_trace_prev, y_trace_prev, line_x, line_y, line_d] = Layer.x_y_d_pos(self, line,
                                                                                                         x_trace,
                                                                                                         y_trace,
                                                                                                         x_trace_prev,
                                                                                                         y_trace_prev)
                if x_trace != x_trace_prev or y_trace != y_trace_prev:
                    pour_points.append([x_trace, y_trace])

            elif draw_trace:
                [x_trace, y_trace, x_trace_prev, y_trace_prev, line_x, line_y, line_d] = Layer.x_y_d_pos(self, line,
                                                                                                         x_trace,
                                                                                                         y_trace,
                                                                                                         x_trace_prev,
                                                                                                         y_trace_prev)

                if line_d != -1:
                    feature_step = line[line_d:]
                    if feature_step == 'D01*\n':
                        # continue drawing from previous x & y
                        this_feature = feature_list[which_feature]
                        tracer.trace_line(self.cond_mat, x_trace_prev, y_trace_prev, x_trace, y_trace,
                                          this_feature.radius, self.sim_res, tracer.Cell.CONDUCTOR.value)

                    elif feature_step == 'D03*\n':
                        # end trace/shape
                        this_feature = feature_list[which_feature]
                        if this_feature.__class__ == tracer.Rectangle:
                            tracer.trace_rectangle(self.cond_mat, x_trace, y_trace, this_feature.width,
                                                   this_feature.height, self.sim_res, tracer.Cell.CONDUCTOR.value)
                        elif this_feature.__class__ == tracer.Oval:
                            tracer.trace_oval(self.cond_mat, x_trace, y_trace, this_feature.width, this_feature.height,
                                              self.sim_res, tracer.Cell.CONDUCTOR.value)
                        elif this_feature.__class__ == tracer.Circle:
                            tracer.trace_circle(self.cond_mat, x_trace, y_trace, this_feature.radius, self.sim_res,
                                                tracer.Cell.CONDUCTOR.value)

    def x_y_d_pos(self, this_line, x, y, x_prev, y_prev):
        line_x = this_line.find('X')
        line_y = this_line.find('Y')
        line_d = this_line.find('D')

        if line_x != -1:
            if line_y != -1:
                x_prev = x
                x = float(this_line[line_x + 1: line_y]) * self.sig_dig
            else:
                x_prev = x
                x = float(this_line[line_x + 1: line_d]) * self.sig_dig
        else:
            x_prev = x

        if line_y != -1:
            y_prev = y
            y = float(this_line[line_y + 1: line_d]) * self.sig_dig
        else:
            y_prev = y

        return [x, y, x_prev, y_prev, line_x, line_y, line_d]

    def convert_layer_thickness(self, thickness_val, thickness_type):
        if thickness_type == 'oz':
            thickness_rtn = thickness_val * 1.37
        elif thickness_type == 'in':
            thickness_rtn = thickness_val / 1000
        elif thickness_type == 'mil':
            thickness_rtn = thickness_val
        elif thickness_type == 'mm':
            thickness_rtn = thickness_val * .0254
        return thickness_rtn

    def find_networks(self):
        # starting network ID is 1
        new_network_id = 1
        [n_rows, n_cols] = self.cond_mat.shape

        net_add = 7

        for row in range(0, n_rows):
            for col in range(0, n_cols):
                if self.cond_mat[row, col] != tracer.Cell.INSULATOR.value and self.cond_mat[
                    row, col] != tracer.Cell.AIR.value:
                    for neighbor_row in range(row - 1, row + 2):
                        for neighbor_col in range(col - 1, col + 2):
                            if 0 <= neighbor_row <= n_rows - 1 and 0 <= neighbor_col <= n_cols - 1 \
                                    and not (neighbor_row == row and neighbor_col == col):
                                neighbor_cond_val = self.cond_mat[neighbor_row, neighbor_col]
                                # check if neighbor cell already has a network
                                if self.cond_mat[neighbor_row, neighbor_col] > 0:
                                    # check whether this cell doesn't yet have a network
                                    if self.cond_mat[row, col] == tracer.Cell.CONDUCTOR.value:
                                        self.cond_mat[row, col] = self.cond_mat[neighbor_row, neighbor_col]
                                    # check whether neighbor cell's network is lower number
                                    elif self.cond_mat[neighbor_row, neighbor_col] < self.cond_mat[row, col]:
                                        self.cond_mat[row, col] = self.cond_mat[neighbor_row, neighbor_col]
                                    # case where this cell already has a network
                                    # and it's network is lower number than it's neighbor
                                    elif self.cond_mat[neighbor_row, neighbor_col] > self.cond_mat[row, col]:
                                        # find all cells with neighboring network number
                                        # set all of those cells to this cell network number
                                        higher_network = np.argwhere(self.cond_mat == neighbor_cond_val)
                                        for higher_cell in higher_network:
                                            self.cond_mat[higher_cell[0], higher_cell[1]] = self.cond_mat[row, col]
                                # case where this cell has a network but the neighbor cell doesn't
                                elif self.cond_mat[neighbor_row, neighbor_col] < 0 \
                                        and self.cond_mat[row, col] != tracer.Cell.CONDUCTOR.value:
                                    self.cond_mat[neighbor_row, neighbor_col] = self.cond_mat[row, col]

                    if self.cond_mat[row, col] == tracer.Cell.CONDUCTOR.value:
                        self.cond_mat[row, col] = new_network_id
                        new_network_id = new_network_id + net_add
                        if net_add == 7:
                            net_add = 5
                        elif net_add == 5:
                            net_add = -3
                        else:
                            net_add = 7

    def find_cond_loss(self):
        cond_q_maps = []

        # for each load, find associated network
        for electric_load in self.loads:
            if self.simulation.show_process:
                print("Losses for load: " + electric_load.name)
            # convert start and end locations to matrix coord
            path_start = [int(electric_load.path_start[0] / self.sim_res),
                          int(electric_load.path_start[1] / self.sim_res)]
            path_end = [int(electric_load.path_end[0] / self.sim_res),
                        int(electric_load.path_end[1] / self.sim_res)]

            # find which network is at start
            this_network = self.cond_mat[path_start[0], path_start[1]]
            # check that end is same network
            end_network_check = self.cond_mat[path_end[0], path_end[1]]
            if this_network == end_network_check:
                # filter cond_mat to a matrix which only contains this network
                network_map = np.where(self.cond_mat == this_network, 1, 0)
                # pass in filtered matrix (map), start, end into current tracing for res_mat
                # for a network with a load, use current tracing to find resistance of each cell.
                # multiply the resistance by the current squared to get Q for cell
                this_network_q_mat = electric_load.current * electric_load.current \
                                     * current_tracing.set_res_values(path_start, path_end, network_map,
                                                                      self.thickness, self.cond_material)
                cond_q_maps.append(this_network_q_mat)

        for this_q_map in cond_q_maps:
            self.Q_mat = np.add(self.Q_mat, this_q_map)

    def drill_holes(self, drill_layer):
        hole_cells = np.argwhere(drill_layer.hole_mat == tracer.Cell.AIR.value)
        plated_cells = np.argwhere(drill_layer.hole_mat == tracer.Cell.CONDUCTOR.value)
        for hole_cell in hole_cells:
            self.cond_mat[hole_cell[0], hole_cell[1]] = tracer.Cell.AIR.value
        for plated_cell in plated_cells:
            if self.cond_mat[plated_cell[0], plated_cell[1]] <= tracer.Cell.INSULATOR.value:
                self.cond_mat[plated_cell[0], plated_cell[1]] = -1 * tracer.Cell.CONDUCTOR.value
