from json import JSONEncoder

import Helpers
import current_tracing
import drill
import heat_transfer
import layer
import pcb_board
import tracer


class BoardEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


class BoardSetup:
    def __init__(self, conductor_material, dielectric_material, plating_thickness, drill_file, keepout_file, layers,
                 components):
        self.conductor_material = conductor_material
        self.dielectric_material = dielectric_material
        self.plating_thickness = plating_thickness
        self.drill_file = drill_file
        self.keepout_file = keepout_file
        self.layers = layers
        self.components = components


class LayerSetup:
    def __init__(self, name, layer_type, thickness, gerber_file):
        self.name = name
        self.layer_type = layer_type
        self.thickness = thickness
        self.gerber_file = gerber_file


class ComponentSetup:
    def __init__(self, name, side, width, length, x_position, y_position):
        self.name = name
        self.side = side
        self.width = width
        self.length = length
        self.x_position = x_position
        self.y_position = y_position


class SimulationSetup:
    def __init__(self, resolution, ambient, orientation, tuning, loads, component_heats):
        self.resolution = resolution
        self.ambient = ambient
        self.orientation = orientation
        self.tuning = tuning
        self.loads = loads
        self.component_heats = component_heats


class TuningSetup:
    def __init__(self, cond_k_inplane, cond_k_thruplane, diel_k_inplane, diel_k_thruplane, conv_coef, rad_coef, rad_pow,
                 component_htc):
        self.cond_k_inplane = cond_k_inplane
        self.cond_k_thruplane = cond_k_thruplane
        self.diel_k_inplane = diel_k_inplane
        self.diel_k_thruplane = diel_k_thruplane
        self.conv_coef = conv_coef
        self.rad_coef = rad_coef
        self.rad_pow = rad_pow
        self.component_htc = component_htc

class LoadSetup:
    def __init__(self, name, layer, current, x_start, y_start, x_end, y_end):
        self.name = name
        self.layer = layer
        self.current = current
        self.x_start = x_start
        self.y_start = y_start
        self.x_end = x_end
        self.y_end = y_end


class ComponentHeatSetup:
    def __init__(self, component_name, heat):
        self.component_name = component_name
        self.heat = heat


def run_simulation(board_settings, sim_settings):
    this_sim_orientation = [0, 0]
    if sim_settings.orientation == "X-axis -90":
        this_sim_orientation = [-1, 0]
    elif sim_settings.orientation == "X-axis +90":
        this_sim_orientation = [1, 0]
    elif sim_settings.orientation == "Y-axis -90":
        this_sim_orientation = [0, -1]
    elif sim_settings.orientation == "Y-axis +90":
        this_sim_orientation = [0, 1]

    simulation = tracer.Simulation(int(sim_settings.resolution), float(sim_settings.ambient), this_sim_orientation,
                                   True,
                                   float(sim_settings.tuning.cond_k_inplane),
                                   float(sim_settings.tuning.cond_k_thruplane),
                                   float(sim_settings.tuning.diel_k_inplane),
                                   float(sim_settings.tuning.diel_k_thruplane),
                                   float(sim_settings.tuning.conv_coef),
                                   float(sim_settings.tuning.rad_coef),
                                   float(sim_settings.tuning.rad_pow),
                                   float(sim_settings.tuning.component_htc))
    keepOutGerber = board_settings.keepout_file
    keepOutLines = Helpers.load_Gerber(keepOutGerber)
    board_dims = layer.get_board_dims(keepOutLines)

    drillFile = board_settings.drill_file
    platingThickness = float(board_settings.plating_thickness)
    platingThicknessUnit = 'oz'
    if drillFile != '':
        drillLines = Helpers.load_Gerber(drillFile)
        drillLayer = drill.Drill(drillLines, board_dims, simulation.resolution, platingThickness,
                                 platingThicknessUnit)
        drillLayer.trace_drill()

    conductorMaterial = board_settings.conductor_material
    dielectricMaterial = board_settings.dielectric_material
    platingMaterial = conductorMaterial

    board_components = list()
    for component_heat in sim_settings.component_heats:
        for board_component in board_settings.components:
            if board_component.name == component_heat.component_name:
                this_board_component = tracer.Component(board_component.name,
                                                [float(board_component.width), float(board_component.length)],
                                                [float(board_component.x_position), float(board_component.y_position)],
                                                float(component_heat.heat), board_component.side)
                board_components.append(this_board_component)
                break

    layer_list = []
    for layer_setting in board_settings.layers:
        thisLayerName = layer_setting.name
        thisLayerType = layer_setting.layer_type
        thisLayerGerber = layer_setting.gerber_file
        if thisLayerGerber != '':
            thisLayerLines = Helpers.load_Gerber(thisLayerGerber)
        thisLayerThickness = float(layer_setting.thickness)
        thisLayerThicknessUnit = 'mil'

        electric_loads_for_layer = list()
        for load_setting in sim_settings.loads:
            if load_setting.layer == layer_setting.name:
                thisLoadThisLayerCurrent = float(load_setting.current)
                thisLoadThisLayerStart = [float(load_setting.x_start), float(load_setting.y_start)]
                thisLoadThisLayerEnd = [float(load_setting.x_end), float(load_setting.y_end)]
                thisLoadThisLayer = current_tracing.ElectricLoad(load_setting.name, thisLoadThisLayerCurrent,
                                                                 thisLoadThisLayerStart, thisLoadThisLayerEnd)
                electric_loads_for_layer.append(thisLoadThisLayer)

        thisLayer = layer.Layer(thisLayerName, thisLayerType, thisLayerLines, conductorMaterial,
                                thisLayerThickness, thisLayerThicknessUnit, board_dims, simulation,
                                electric_loads_for_layer)

        if not isinstance(thisLayerGerber, type(None)) and thisLayer.layer_type == "Conductor":
            if simulation.show_process:
                print("Tracing layer: " + layer_setting.name)
            thisLayer.trace_layer()

            if simulation.show_process:
                print("Finding networks: " + layer_setting.name)
            thisLayer.find_networks()

            if simulation.show_process:
                print("Calculating conduction losses: " + layer_setting.name)
            thisLayer.find_cond_loss()

        # this happens to both conductor and insulating layers
        if not isinstance(drillFile, type(None)):
            if simulation.show_process:
                print("Drilling holes: " + layer_setting.name)
            thisLayer.drill_holes(drillLayer)

        layer_list.append(thisLayer)

    board = pcb_board.Board(layer_list, board_components, simulation, conductorMaterial, dielectricMaterial)

    heat_transfer_analysis = heat_transfer.Simultaneous(board)
    heat_transfer_analysis.solve()

    return heat_transfer_analysis
