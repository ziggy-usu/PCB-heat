import time
import numpy as np

from scipy.interpolate import interp1d
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import spsolve
from math import ceil

import tracer

# die_in_plane_k_corr = 700
# die_thru_plane_k_corr = 9000
# diel_k_corr = [die_thru_plane_k_corr, die_in_plane_k_corr, die_in_plane_k_corr]

# cond_in_plane_k_corr = 1
# cond_thru_plane_k_corr = 1
# cond_k_corr = [cond_thru_plane_k_corr, cond_in_plane_k_corr, cond_in_plane_k_corr]

# conv_corr = 1
# rad_corr_coef = 10
# rad_corr_pow = 0.5
# rad_correction = rad_corr_coef * (Tsk - Tak) ** rad_corr_pow
# comp_htc_corr = 15



def lookup_g_v2(temperature_c):
    temp_vec = np.asarray([0, 20, 40, 60, 80, 100, 200])
    g_v2_vec = np.asarray([8.28e5, 6.54e5, 5.2e5, 4.27e5, 3.47e5, 2.89e5, 1.28e5])

    g_v2_interp = interp1d(temp_vec, g_v2_vec)

    return g_v2_interp(temperature_c)


def lookup_k_air(temperature_c):
    temp_vec = np.asarray([0, 20, 40, 60, 80, 100, 200])
    k_vec = np.asarray([6.02e-4, 6.375e-4, 6.731e-4, 7.087e-4, 7.442e-4, 7.798e-4, 9.398e-4])

    k_interp = interp1d(temp_vec, k_vec)

    return k_interp(temperature_c)


class Simultaneous:
    def __init__(self, board):

        self.board = board
        self.simulation = self.board.simulation
        # build 'G' tensor matrix, and 'S' boundary conditions vector
        self.g_row = list()
        self.g_col = list()
        self.g_data = list()
        self.neighbor_c_list = list()
        self.s_list = list()

        # build G matrix and S vector
        self.grid_dims = np.append(np.size(self.board.layers), np.shape(self.board.layers[0].Q_mat))
        self.g_dim = np.prod(self.grid_dims)
        self.s_vec = list()  # np.zeros([self.g_dim, 1])
        self.skipped_cells = list()

        # calculate reusable values
        self.cell_wid = self.simulation.resolution
        self.cell_ht = self.cell_wid
        self.cell_dep = self.board.layers[0].thickness

        # self.temp_mat = np.ones(self.grid_dims) * self.find_ave_board_temp()
        if self.simulation.show_process:
            print("Creating simultaneous simulation")
        self.htc = list()
        self.temp_mat = self.calc_initial_board_temps()

        # self.res_htc = -0.003 * self.simulation.resolution * self.simulation.resolution + 0.035 * self.simulation.resolution + 1
        # self.res_cond = -0.004 * self.simulation.resolution * self.simulation.resolution - 0.02 * self.simulation.resolution + 2.4

        self.q_components = np.zeros(np.append(2, np.shape(self.board.layers[0].Q_mat)))

    def calc_initial_board_temps(self):
        t_ave = self.calc_ave_board_temp()

        if self.simulation.show_process:
            print("Initial mean temp:" + str(t_ave))

        temp_cell_mat = list()
        for layer in range(0, self.board.mat_dep):
            layer_temp_mat = t_ave * np.ones_like(self.board.layers[layer].cond_mat)
            temp_cell_mat.append(layer_temp_mat)

        return np.asarray(temp_cell_mat)

    def calc_ave_board_temp(self):
        # find total heat generated in board from cond loss and component (70%)
        q_tot = self.find_total_board_q()
        iter_limit = 10000
        iter = 0

        [L, W, H] = self.get_general_board_dims()
        c_2_k = 273.16
        Ta = self.simulation.ambient
        beta_a = 1/(Ta+c_2_k)

        # guess dt = 20 deg C
        dt = 20
        temp_thresh = 0.1
        temp_delta = temp_thresh * 2

        while abs(temp_delta) > temp_thresh:
            iter += 1

            Ts = Ta + dt
            Tf = (Ts + Ta) / 2

            g_v2 = lookup_g_v2(Tf)
            k_air = lookup_k_air(Tf)
            Pr = 0.71

            Ra_less_P = g_v2*beta_a*dt*Pr

            P_top_btm = W * L / (2 * (W + L))
            P_side = H

            Ra_top_btm = Ra_less_P * P_top_btm ** 3
            Ra_side = Ra_less_P * P_side ** 3

            if Ra_top_btm < 8e6:
                C_top = 0.54
                n_top = 1/4
            else:
                C_top = 0.15
                n_top = 1 / 3

            if Ra_side < 1e9:
                C_side = 0.59
                n_side = 1 / 4
            else:
                C_side = 0.13
                n_side = 1 / 3

            C_btm = 0.27
            n_btm = 1/4

            epsilon = 0.8
            sigma = 5.67 * 1e-8 / 1550

            # convection
            h_top = (C_top * k_air * Ra_top_btm ** n_top / P_top_btm) / self.simulation.conv_coef
            h_side = (C_side * k_air * Ra_side ** n_side / P_side) / self.simulation.conv_coef
            h_btm = (C_btm * k_air * Ra_top_btm ** n_btm / P_top_btm) / self.simulation.conv_coef
            q_conv = h_top * (L * W) * dt + \
                     h_side * (2 * W * H) * dt + \
                     h_side * (2 * L * H) * dt + \
                     h_btm * (L * W) * dt

            # radiation
            Tsk = Ts + c_2_k
            Tak = Ta + c_2_k
            rad_correction = self.simulation.rad_coef * (Tsk - Tak) ** self.simulation.rad_pow
            Cr = 2 * epsilon * sigma * (W * L + H * L + H * W) / rad_correction
            q_rad = Cr * (Tsk ** 4 - Tak ** 4)

            q_out = q_conv + q_rad
            q_error = q_tot - q_out

            if q_error > 0:
                temp_delta = q_error / q_tot
            else:
                temp_delta = -0.8 * dt
            dt += temp_delta

            if iter > iter_limit:
                if self.simulation.show_process:
                    print("Iteration limit on finding board temp")
                break

        self.htc = [h_top, h_side, h_btm]
        Ts = Ta + dt
        # self.htc = [0.0004, 0.0003, 0.0002]
        return Ts

    def get_general_board_dims(self):
        board_L = self.board.mat_ht * self.simulation.resolution
        board_W = self.board.mat_wid * self.simulation.resolution
        board_H = 0
        for layer in range(0, self.board.mat_dep):
            board_H += self.board.layers[layer].thickness

        if self.simulation.board_orientation == [0, 0]:
            L = board_L / 1000
            W = board_W / 1000
            H = board_H / 1000

        elif self.simulation.board_orientation == [1, 0] or self.simulation.board_orientation == [-1, 0]:
            L = board_H / 1000
            W = board_W / 1000
            H = board_L / 1000

        elif self.simulation.board_orientation == [0, 1] or self.simulation.board_orientation == [0, -1]:
            L = board_L / 1000
            W = board_H / 1000
            H = board_W / 1000

        return [L, W, H]

    def find_total_board_q(self):
        q_cond = 0
        for layer in range(0, self.board.mat_dep):  # k direction
            q_cond += np.sum(self.board.layers[layer].Q_mat)
        q_comp = 0
        for component in self.board.components:
            q_comp += component.heat

        return q_cond + q_comp

    def series_conductance(self, c1, c2):
        return 1 / (1 / c1 + 1 / c2)

    def prepare_sparse_matrices(self):
        start_time = time.perf_counter()
        self.s_vec = list()
        for layer in range(0, self.grid_dims[0]):  # k direction
            self.cell_dep = self.board.layers[layer].thickness
            for col in range(0, self.grid_dims[2]):  # j direction
                for row in range(0, self.grid_dims[1]):  # i direction
                    # if self.board.layers[layer].cond_mat[row, col] != tracer.Cell.AIR.value:
                    this_board_coord = [layer, row, col]
                    # empty list for neighboring cells - used to build matrix cell for self (sum of neighbor 'C's)
                    self.neighbor_c_list = list()
                    self.s_list = list()
                    this_q = self._find_this_q(this_board_coord)

                    self._handle_neighbors(this_board_coord)

                    # handle self location in G matrix
                    this_c = sum(self.neighbor_c_list)
                    g_row_ind = row + col * self.board.mat_wid + layer * (self.board.mat_wid * self.board.mat_ht)
                    self.g_row.append(g_row_ind)
                    self.g_col.append(g_row_ind)
                    self.g_data.append(this_c)
                    this_s = sum(self.s_list) * self.simulation.ambient + this_q
                    self.s_vec.append(this_s)

        if self.simulation.show_process:
            print("Matrix prep time: " + str(time.perf_counter() - start_time))

    def calc_component_heat(self):
        # total_components_heat = np.zeros_like(self.layers[0].Q_mat)
        self.q_components = np.zeros(np.append(2, np.shape(self.board.layers[0].Q_mat)))
        for component in self.board.components:
            component_heat = np.zeros_like(self.board.layers[0].Q_mat)
            # determine if top or bottom layer component
            if component.side == 'Top':
                related_layer = 0
                conv_dir = self.get_conv_dir([-1, 0, 0])
            else:
                related_layer = len(self.board.layers) - 1
                conv_dir = self.get_conv_dir([1, 0, 0])
            # Find related layer cells which are conductor material (set)
            related_cells = list()
            cells_temps = list()
            for row in range(ceil((component.x - component.width / 2) / self.simulation.resolution),
                             ceil((component.x + component.width / 2) / self.simulation.resolution)):
                for col in range(ceil((component.y - component.length / 2) / self.simulation.resolution),
                                 ceil((component.y + component.length / 2) / self.simulation.resolution)):

                    # assumes nearly all conduction is transferred through exposed conductor
                    if self.board.layers[related_layer].cond_mat[row, col] > tracer.Cell.INSULATOR.value:
                        related_cells.append([row, col])
                        cells_temps.append(self.temp_mat[related_layer, row, col])

            # Find mean temperature of cells -> dT = T_mean - T_ambient
            temp_mean = np.average(np.asarray(cells_temps))
            delta_temp = temp_mean - self.simulation.ambient

            # calculate heat lose through top of component through convection and radiation
            htc = self.get_htc(conv_dir, self.simulation.ambient, temp_mean) * self.simulation.comp_htc_coef
            heat_conv_rad = htc * component.width * component.length * delta_temp
            # the remaining heat is conductive heat into board, its heat is distributed to the set of layer cells
            heat_cond = (component.heat - heat_conv_rad)
            heat_per_cell = heat_cond / len(related_cells)

            for related_cell in related_cells:
                component_heat[related_cell[0], related_cell[1]] = heat_per_cell
            self.q_components[np.sign(related_layer)] += component_heat

    def get_htc(self, orientation, temp_amb, temp_surf):
        htc_conv = 0
        C2K = 273.16

        # free convection
        if orientation == 'vertical':
            htc_conv = self.htc[1]
        elif orientation == 'horizontal top':
            htc_conv = self.htc[0]
        elif orientation == 'horizontal bottom':
            htc_conv = self.htc[2]

        # radiation
        Tsk = temp_surf + C2K
        Tak = temp_amb + C2K
        rad_correction = self.simulation.rad_coef * (Tsk - Tak) ** self.simulation.rad_pow

        epsilon = 0.8  # assumed for solder mask (close to epoxy paint)
        # Stefan Boltzmann Constant converted to W / (in^2 K^4)
        sigma = 5.67 * 1e-8 / 1550
        htc_rad = epsilon * sigma * ((Tsk) * (Tsk) + (Tak) * (Tak)) * (
                (Tsk) + (Tak)) / rad_correction
        # unit of W / (mil^2 C), from W / (in^2 K)
        htc = (htc_conv + htc_rad) * 1e-6

        return htc

    def solve(self):
        if self.simulation.show_process:
            print("Solving simultaneous solution")

        self.calc_component_heat()

        self.prepare_sparse_matrices()
        g_mat = csr_matrix((np.asarray(self.g_data), (np.asarray(self.g_row), np.asarray(self.g_col))),
                           shape=(len(self.s_vec), len(self.s_vec)))

        solve_start = time.perf_counter()
        t_vec = np.transpose(spsolve(g_mat, np.asarray(self.s_vec)))
        if self.simulation.show_process:
            print("Matrix solve time: " + str(time.perf_counter() - solve_start))

        self.temp_mat = np.rot90(t_vec.reshape(self.grid_dims[0], self.grid_dims[2], self.grid_dims[1]),
                                 k=3,  axes=(1, 2))
        if self.simulation.show_process:
            print("Final mean temp:" + str(np.mean(self.temp_mat)))

    def _handle_neighbors(self, board_coord):
        # look in i-1 dir
        neighbor_dir = [0, -1, 0]
        self._neighbor_ij(board_coord, neighbor_dir)

        # look in i+1 dir
        neighbor_dir = [0, 1, 0]
        self._neighbor_ij(board_coord, neighbor_dir)

        # look in j-1 dir
        neighbor_dir = [0, 0, -1]
        self._neighbor_ij(board_coord, neighbor_dir)

        # look in j+1 dir
        neighbor_dir = [0, 0, 1]
        self._neighbor_ij(board_coord, neighbor_dir)

        # look in k-1 dir
        neighbor_dir = [-1, 0, 0]
        self._neighbor_k(board_coord, neighbor_dir)

        # look in k+1 dir
        neighbor_dir = [1, 0, 0]
        self._neighbor_k(board_coord, neighbor_dir)

    def _find_this_q(self, coord):

        # find q from conduction losses
        q_cond = self.board.layers[coord[0]].Q_mat[coord[1], coord[2]]

        # find q from component source (q_cond = q_tot - q_conv - q_rad)
        if coord[0] == 0:
            q_component = self.q_components[0, coord[1], coord[2]]
        elif coord[0] == self.board.mat_dep - 1:
            q_component = self.q_components[1, coord[1], coord[2]]
        else:
            q_component = 0

        return q_cond + q_component

    def get_area(self, neighbor_dir):
        if neighbor_dir[0] != 0:
            area = self.cell_wid * self.cell_ht
        else:
            area = self.cell_wid * self.cell_dep
        return area

    def get_depth(self, neighbor_dir):
        if neighbor_dir[0] == 0:
            depth = self.cell_dep
        else:
            depth = self.cell_wid
        return depth

    def get_conv_dir(self, neighbor_dir):
        conv_dir = 'vertical'
        if self.simulation.board_orientation == [0, 0]:
            if neighbor_dir == [-1, 0, 0]:
                conv_dir = 'horizontal top'
            elif neighbor_dir == [1, 0, 0]:
                conv_dir = 'horizontal bottom'

        elif self.simulation.board_orientation == [1, 0]:
            if neighbor_dir == [0, 0, 1]:
                conv_dir = 'horizontal top'
            elif neighbor_dir == [0, 0, -1]:
                conv_dir = 'horizontal bottom'

        elif self.simulation.board_orientation == [0, 1]:
            if neighbor_dir == [0, -1, 0]:
                conv_dir = 'horizontal top'
            elif neighbor_dir == [0, 1, 0]:
                conv_dir = 'horizontal bottom'

        elif self.simulation.board_orientation == [-1, 0]:
            if neighbor_dir == [0, 0, -1]:
                conv_dir = 'horizontal top'
            elif neighbor_dir == [0, 0, 1]:
                conv_dir = 'horizontal bottom'

        elif self.simulation.board_orientation == [0, -1]:
            if neighbor_dir == [0, 1, 0]:
                conv_dir = 'horizontal top'
            elif neighbor_dir == [0, -1, 0]:
                conv_dir = 'horizontal bottom'

        return conv_dir

    def neighbor_c_air(self, coord, neighbor_dir):
        area = self.get_area(neighbor_dir)
        conv_dir = self.get_conv_dir(neighbor_dir)
        htc = self.get_htc(conv_dir, self.simulation.ambient, self.temp_mat[coord[0], coord[1], coord[2]])  # * self.res_htc
        return htc * area

    def neighbor_c_cond(self, coord, neighbor_dir):
        k_coord = [coord[0] + neighbor_dir[0], coord[1] + neighbor_dir[1], coord[2] + neighbor_dir[2]]

        neighbor_c = self.find_c_cond(k_coord, neighbor_dir)

        return neighbor_c

    def self_c_cond(self, coord, neighbor_dir):
        k_coord = coord

        self_c = self.find_c_cond(k_coord, neighbor_dir)

        return self_c

    def find_c_cond(self, coord, neighbor_dir):
        this_k_cell_material = self.board.layers[coord[0]].cond_mat[coord[1], coord[2]]
        if this_k_cell_material > tracer.Cell.INSULATOR.value:
            this_k = np.sum(
                np.fabs(np.asarray(neighbor_dir)) * np.asarray(self.board.cond_k) / self.simulation.cond_k_coef)
        elif this_k_cell_material == tracer.Cell.AIR.value:
            this_k = np.sum(np.fabs(np.asarray(neighbor_dir)) * np.asarray(self.board.sold_k))
        else:
            this_k = np.sum(
                np.fabs(np.asarray(neighbor_dir)) * np.asarray(self.board.diel_k) / self.simulation.diel_k_coef)
        area = self.get_area(neighbor_dir)
        # depth is half due to grid format
        depth = self.get_depth(neighbor_dir) / 2

        return this_k * area / depth  # * self.res_cond

    def _neighbor_ij(self, coord, neighbor_dir):
        if neighbor_dir[1] != 0:
            which_coord = 1
            self_dir = [0, 1, 0]

        else:
            which_coord = 2
            self_dir = [0, 0, 1]

        # find self C
        self_c = self.self_c_cond(coord, self_dir)

        # if neighbor is air on border, add to S vector and G matrix
        # edge of board -> conv and rad thru air
        if (coord[which_coord] == 0 and neighbor_dir[which_coord] == -1) or (
                coord[1] == (self.board.mat_wid - 1) and neighbor_dir[1] == 1) or (
                coord[2] == (self.board.mat_ht - 1) and neighbor_dir[2] == 1):
            neighbor_c = self.neighbor_c_air(coord, neighbor_dir)
            dir_c = self.series_conductance(self_c, neighbor_c)
            self.s_list.append(dir_c)
            self.neighbor_c_list.append(dir_c)
        else:
            neighbor_c = self.neighbor_c_cond(coord, neighbor_dir)
            dir_c = self.series_conductance(self_c, neighbor_c)
            self.neighbor_c_list.append(dir_c)

            g_row_ind = coord[1] + coord[2] * self.board.mat_wid + coord[0] * (self.board.mat_wid * self.board.mat_ht)
            g_col_ind = g_row_ind + neighbor_dir[1] + neighbor_dir[2] * self.board.mat_wid
            self.g_row.append(g_row_ind)
            self.g_col.append(g_col_ind)
            self.g_data.append(-dir_c)

    def _neighbor_k(self, coord, neighbor_dir):
        which_coord = 0
        self_c = self.self_c_cond(coord, [1, 0, 0])

        # if neighbor is air, add to S vector and G matrix
        # edge of board -> conv and rad thru air
        if (coord[which_coord] == 0 and neighbor_dir[which_coord] == -1) or (
                coord[which_coord] == (self.board.mat_dep - 1) and neighbor_dir[which_coord] == 1):
            neighbor_c = self.neighbor_c_air(coord, neighbor_dir)
            dir_c = self.series_conductance(self_c, neighbor_c)
            self.s_list.append(dir_c)
            self.neighbor_c_list.append(dir_c)
        # conduction thru board
        # find neighbor C, then add to G matrix and nei_Cs
        # assumes that holes are made is k direction so if this isn't an air cell, it's neighbor in k won't be either
        else:
            neighbor_c = self.neighbor_c_cond(coord, neighbor_dir)
            dir_c = self.series_conductance(self_c, neighbor_c)
            self.neighbor_c_list.append(dir_c)

            g_row_ind = coord[1] + coord[2] * self.board.mat_wid + coord[0] * (self.board.mat_wid * self.board.mat_ht)
            g_col_ind = g_row_ind + neighbor_dir[0] * (self.board.mat_wid * self.board.mat_ht)
            self.g_row.append(g_row_ind)
            self.g_col.append(g_col_ind)
            self.g_data.append(-dir_c)
