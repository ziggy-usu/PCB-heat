import numpy as np
import tracer

mm_to_mil = 1000 / 25.4


class Drill:

    def __init__(self, lines, dims, sim_resolution, thickness_val, thickness_type):
        self.lines = lines
        self.width = int(dims[0])
        self.height = int(dims[1])
        self.sim_res = sim_resolution
        self.thickness = self.convert_layer_thickness(thickness_val, thickness_type)

        self.hole_mat = np.zeros([int(self.width / sim_resolution), int(self.height / sim_resolution)], dtype=int)

        if not isinstance(lines, type(None)):
            [self.sig_dig, self.units] = self.find_units_sig_dig()

    def trace_drill(self):
        # go line by line instructions
        hole_list = []
        this_hole_id = 'none'
        hole_ref = -1
        x_hole = -1.0
        y_hole = -1.0
        which_hole = -1

        hole_list_add = True

        for line in self.lines:
            # if hole call out, add to hole array
            if line.startswith('T'):
                # still adding the tools to the hole array
                if hole_list_add:
                    hole_arr = line.split('F')
                    hole_id_str = hole_arr[0]
                    hole_id = int(hole_id_str[1:])
                    hole_dim_str = hole_arr[1].split('C')
                    if self.units == "in":
                        hole_rad = float(hole_dim_str[1]) * 500
                    else:
                        hole_rad = float(hole_dim_str[1]) * mm_to_mil / 2
                    new_hole = tracer.Circle(hole_id, hole_rad)
                    hole_list.append(new_hole)

                # call out for switching tool
                else:
                    which_hole = 0
                    this_hole_id = int(line[1:])
                    for hole in hole_list:
                        if hole.f_id == this_hole_id:
                            break
                        which_hole = which_hole + 1

            elif line.startswith('%'):
                # change from adding tools to using tools
                hole_list_add = False

            elif line.startswith('X') or line.startswith('Y'):
                this_hole = hole_list[which_hole]
                [x_hole, y_hole] = self.x_y_pos(line, x_hole, y_hole)
                tracer.trace_circle(self.hole_mat, x_hole, y_hole, this_hole.radius, self.sim_res,
                                    tracer.Cell.CONDUCTOR.value)
                lesser_rad = this_hole.radius - self.thickness  # max(self.thickness, self.sim_res)
                tracer.trace_circle(self.hole_mat, x_hole, y_hole, lesser_rad, self.sim_res,
                                    tracer.Cell.AIR.value)

    def x_y_pos(self, this_line, prev_x, prev_y):
        line_x = this_line.find('X')
        line_y = this_line.find('Y')
        x_str = ''
        y_str = ''
        x = prev_x
        y = prev_y

        if line_x != -1:
            if line_y != -1:
                x_str = this_line[line_x + 1: line_y]
            else:
                x_str = this_line[line_x + 1: -1]

            x = self.number_sig_dig(x_str, self.sig_dig)
            if self.units == "mm":
                x = x * mm_to_mil

        if line_y != -1:
            y_str = this_line[line_y + 1: -1]
            y = self.number_sig_dig(y_str, self.sig_dig)
            if self.units == "mm":
                y = y * mm_to_mil

        return [x, y]

    def number_sig_dig(self, this_string, sig_dig):
        while len(this_string) < sig_dig:
            this_string = this_string + '0'
        ret_val = float(this_string[0:sig_dig])
        if len(this_string) > len(this_string[0:sig_dig]):
            ret_val = ret_val + float(this_string[sig_dig:]) / (10 ^ (len(this_string[sig_dig:])))
        return ret_val

    def convert_layer_thickness(self, thickness_val, thickness_type):
        if thickness_type == 'oz':
            thickness_rtn = thickness_val * 1.37
        elif thickness_type == 'in':
            thickness_rtn = thickness_val / 1000
        elif thickness_type == 'mil':
            thickness_rtn = thickness_val
        elif thickness_type == 'mm':
            thickness_rtn = thickness_val / mm_to_mil
        return thickness_rtn

    def find_units_sig_dig(self):
        units = 'in'
        for line in self.lines:
            if line.startswith('INCH'):
                units = 'in'
                sig_dig = 5
                break
            elif line.startswith('METRIC'):
                units = 'mm'
                sig_dig = 4
                break
        return [sig_dig, units]
