def get_k_values(material):
    # values in W/inC
    # [thru-plane(k), in-plane (i, j)]
    switch = {
        'Copper': [9.9, 9.9, 9.9],
        'Aluminum': [5.5, 5.5, 5.5],
        'Gold': [7.5, 7.5, 7.5],
        'Silver': [10.6, 10.6, 10.6],
        'Nickel': [2.3, 2.3, 2.3],
        'Solder': [1.46, 1.46, 1.46],
        'Epoxy': [0.09, 0.09, 0.09],
        'Fr-4': [0.00737, 0.020574, 0.020574],
        'Polyamide': [0.005, 0.005, 0.005],
        'ThermalCompound': [0.02, 0.02, 0.02]
    }

    return switch.get(material)


class Board:
    def __init__(self, layers, components, simulation, cond_material, diel_material):
        self.layers = layers
        self.components = components
        self.simulation = simulation
        self.cond_material = cond_material
        self.diel_material = diel_material
        [self.mat_wid, self.mat_ht] = self.layers[0].cond_mat.shape
        self.mat_dep = len(self.layers)
        self.cond_k = get_k_values(self.cond_material)
        self.diel_k = get_k_values(self.diel_material)
        self.sold_k = get_k_values('Solder')
