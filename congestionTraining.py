from logging import root
import traci, math
import traci.constants as tc
import json
import os
from pyproj import Proj, Transformer
import sumolib
from shapely.geometry import LineString, Point
from geopy.distance import geodesic
from routePreparator import downsample_route, mapa_generator_for_SUMO_data, resample_route, get_next_valid_edge, find_if_street_has_traffic_light, get_vehicles_in_front_of_ambulance, get_light_state, carregar_coordenades, generate_congestion, mapa_generator_for_OSM_data, get_data_for_congestion_IA, find_data_from_ambulance_route, valor_proper
from trafficGenerator import congestion_analyzer, get_congestion_for_edge, generate_random_route_starting_at_next_edge, generate_random_route_starting_at_specific_edge
import time
from importRoutes import escriure_ruta, convertir_coordenades_a_edges, generate_random_route, convertir_coordenades_a_edges
from dispositiu import find_if_there_is_emergency_lane, find_if_street_has_traffic_light, get_light_state, change_traffic_light_for_one_lane, change_traffic_lights_for_whole_edge, get_light_state_for_edge, create_emergency_lane, find_if_street_has_traffic_light_for_edge, activate_emergency_lane_in_edge
from Route_with_no_vehicles import run_simulation_with_no_vehicles, run_simulation_with_no_vehicles_to_get_coords
from Route_with_vehicles_but_no_device import run_simulation_with_vehicles_and_no_device
from Route_with_vehicles_and_congestion_genearted_with_AI import run_simulation_with_vehicles_and_no_device, run_simulation_with_vehicles_and_no_device_for_data_gathering

"""
route = "route_1.json"
net = sumolib.net.readNet('osm.net.xml')
sumoBinary = sumolib.checkBinary("sumo")
traci.start([sumoBinary, "-c", "osm.sumocfg"])
edges = []
coordinates = carregar_coordenades(route)
downsampled_coords = downsample_route(coordinates, 150)
edges, edges_with_Coords =convertir_coordenades_a_edges(downsampled_coords, net)
traci.close()
"""
filename = "results_for_training_23.json"
i = 0
while True:
    net = sumolib.net.readNet('osm.net.xml')
    sumoBinary = sumolib.checkBinary("sumo")
    traci.start([sumoBinary, "-c", "osm.sumocfg"])
    edges = generate_random_route(traci.edge.getIDList(), net)
    traci.close()
    coordinates, edges_with_coords, data_for_each_edge = run_simulation_with_no_vehicles_to_get_coords(edges)
    congestedCoords = generate_congestion(coordinates, 0, 50, 2)
    j = 1
    results = []
    while j < 9:
        results.append(run_simulation_with_vehicles_and_no_device_for_data_gathering(edges, j*50, j*3))
        j += 1
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        with open(filename, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = [data]
    else:
        data = []
    data.append(results)
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    i += 1
"""
simulated_coords, simulated_time = mapa_generator_for_SUMO_data(result,'result_map.html')
congestion_analyzer(real_coords, real_time, simulated_coords,simulated_time, result, congestedCoords, edges_with_coords)
"""