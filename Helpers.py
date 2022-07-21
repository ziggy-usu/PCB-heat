import json

import layer
import drill
import pcb_board
import current_tracing
import tracer


def load_files(settings_file_name):
    # load settings
    settings_file = open(settings_file_name, 'r')
    setting_data = settings_file.read()
    settings = json.loads(setting_data)
    show_process = True

    # Simulation Files
    global grid_size
    global iter_lim
    Sim_settings = settings['Simulation']
    grid_size = Sim_settings.get('GridSize')
    sim_conditions = Sim_settings.get('Conditions')
    ambient_temp_c = sim_conditions.get('AmbientAirTempC')
    board_orientation = sim_conditions.get('BoardOrientation')

    simulation = tracer.Simulation(grid_size, ambient_temp_c, board_orientation, show_process)

    # Layers
    layer_list = []
    Layer_settings = settings['Layers']

    # Find keep out layer to get board dimensions
    keepOutLayerData = Layer_settings.get('KeepOut')
    keepOutGerber = keepOutLayerData.get('GerberFile')
    keepOutLines = load_Gerber(keepOutGerber)
    board_dims = layer.get_board_dims(keepOutLines)

    # General Board Settings
    boardData = settings['BoardSetup']
    drillFile = boardData.get('DrillFile')
    platingThickness = boardData.get('PlatingThickness')
    platingThicknessUnit = boardData.get('ThicknessUnit')
    if not isinstance(drillFile, type(None)):
        drillLines = load_Gerber(drillFile)
        drillLayer = drill.Drill(drillLines, board_dims, simulation.resolution, platingThickness,
                                 platingThicknessUnit)
        drillLayer.trace_drill()
    boardMaterials = boardData.get('Materials')
    conductorMaterial = boardMaterials.get('Conductor')
    dielectricMaterial = boardMaterials.get('Dielectric')
    platingMaterial = boardMaterials.get('Plating')
    solderMaskMaterial = boardMaterials.get('SolderMask')

    componentFileName = boardData.get('ComponentFile')
    board_components = list()
    if not isinstance(componentFileName, type(None)):
        component_file = open(componentFileName, 'r')
        component_data = component_file.read()
        components = json.loads(component_data)
        for component_name in components:
            this_component_data = components.get(component_name)
            comp_dims = this_component_data.get('Dimensions')
            comp_heat = this_component_data.get('Heat')
            comp_side = this_component_data.get('Side')
            comp_locations = this_component_data.get('Locations')
            if not isinstance(comp_locations, type(None)):
                for locationName in comp_locations:
                    this_loc = comp_locations.get(locationName)
                    this_component = tracer.Component(component_name, comp_dims, this_loc, comp_heat, comp_side)
                    board_components.append(this_component)

    for thisLayerName in Layer_settings:
        electric_loads_for_layer = list()
        thisLayerLines = list()

        if thisLayerName != 'KeepOut' and thisLayerName != 'Drill':
            thisLayerData = Layer_settings.get(thisLayerName)
            thisLayerType = thisLayerData.get('Type')
            thisLayerGerber = thisLayerData.get('GerberFile')
            if not isinstance(thisLayerGerber, type(None)):
                thisLayerLines = load_Gerber(thisLayerGerber)
            thisLayerThickness = thisLayerData.get('Thickness')
            thisLayerThicknessUnit = thisLayerData.get('ThicknessUnit')
            thisLayerLoads = thisLayerData.get('Loads')
            if not isinstance(thisLayerLoads, type(None)):
                for thisLoadThisLayerName in thisLayerLoads:
                    thisLoadThisLayerData = thisLayerLoads.get(thisLoadThisLayerName)
                    thisLoadThisLayerCurrent = thisLoadThisLayerData.get('Current')
                    thisLoadThisLayerStart = thisLoadThisLayerData.get('Start')
                    thisLoadThisLayerEnd = thisLoadThisLayerData.get('End')
                    thisLoadThisLayer = current_tracing.ElectricLoad(thisLoadThisLayerName, thisLoadThisLayerCurrent,
                                                                     thisLoadThisLayerStart, thisLoadThisLayerEnd)
                    electric_loads_for_layer.append(thisLoadThisLayer)

            if thisLayerType == "Conductor":
                thisLayerCondMaterial = conductorMaterial
                thisLayerInsulMaterial = dielectricMaterial
            elif thisLayerType == "Dielectric":
                thisLayerCondMaterial = conductorMaterial
                thisLayerInsulMaterial = dielectricMaterial
            elif thisLayerType == "SolderMask":
                thisLayerCondMaterial = platingMaterial
                thisLayerInsulMaterial = solderMaskMaterial

            if simulation.show_process:
                print("Creating layer: " + thisLayerName)

            thisLayer = layer.Layer(thisLayerName, thisLayerType, thisLayerLines, thisLayerCondMaterial,
                                    thisLayerThickness, thisLayerThicknessUnit, board_dims, simulation,
                                    electric_loads_for_layer)

            if not isinstance(thisLayerGerber, type(None)) and thisLayer.layer_type == "Conductor":
                if simulation.show_process:
                    print("Tracing layer: " + thisLayerName)
                thisLayer.trace_layer()

                if simulation.show_process:
                    print("Finding networks: " + thisLayerName)
                thisLayer.find_networks()

                if simulation.show_process:
                    print("Calculating conduction losses: " + thisLayerName)
                thisLayer.find_cond_loss()

            # this happens to both conductor and insulating layers
            if not isinstance(drillFile, type(None)):
                if simulation.show_process:
                    print("Drilling holes: " + thisLayerName)
                thisLayer.drill_holes(drillLayer)

            layer_list.append(thisLayer)

    board = pcb_board.Board(layer_list, board_components, simulation, conductorMaterial, dielectricMaterial)

    return board

    # need to add solder layers for top and bottom
    # need to add heat sink file with parameters


def load_Gerber(gerberFileLocation):
    with open(gerberFileLocation) as f:
        gerberData = f.readlines()
        return gerberData
