from logging import root
import traci, math
import traci.constants as tc
import json
import os
import xml.etree.ElementTree as ET
from pyproj import Proj, Transformer
import sumolib
from shapely.geometry import LineString, Point
from geopy.distance import geodesic
import xml.etree.ElementTree as ET
from routePreparator import downsample_route, mapa_generator_for_SUMO_data, resample_route, get_next_valid_edge, find_if_street_has_traffic_light, get_vehicles_in_front_of_ambulance, get_light_state, carregar_coordenades, generate_congestion, mapa_generator_for_OSM_data, get_data_for_congestion_IA, find_data_from_ambulance_route, valor_proper
from trafficGenerator import congestion_analyzer, get_congestion_for_edge, generate_random_route_starting_at_next_edge, generate_random_route_starting_at_specific_edge
from datetime import datetime, timedelta, timezone
from importRoutes import escriure_ruta, convertir_coordenades_a_edges, generate_random_route, convertir_coordenades_a_edges
from dispositiu import find_if_there_is_emergency_lane, find_if_street_has_traffic_light, get_light_state, change_traffic_light_for_one_lane, change_traffic_lights_for_whole_edge, get_light_state_for_edge, create_emergency_lane, find_if_street_has_traffic_light_for_edge, activate_emergency_lane_in_edge
from Route_with_no_vehicles import run_simulation_with_no_vehicles
from Route_with_vehicles_but_no_device import run_simulation_with_vehicles_and_no_device
from Route_with_vehicles_and_device_activated_begining import run_simulation_with_vehicles_and_device_and_given_traffic, run_simulation_with_vehicles_and_device_random_traffic
from Route_with_vehicles_and_device_traffic_lights_activated import run_simulation_with_vehicles_and_traffic_lights_activated_for_given_traffic, run_simulation_with_vehicles_and_traffic_lights_activated_for_random_traffic
from Data_extraction import data_treatment, get_data_by_edge, compare_data, data_treatment_2, data_treatment_with_traffic_light
import subprocess
import shutil

specific_route = False
json_defined_route = True
route = "route_1.json"
routes = ["route_7.json"]
filename = "result_comparison_specific_routes_10.json"
comparisson_of_three_simulations = True
comparisson_of_two_simulations = False
if comparisson_of_three_simulations:
    if specific_route:
        for r in routes:
            net = sumolib.net.readNet('osm.net.xml')
            sumoBinary = sumolib.checkBinary("sumo")
            traci.start([sumoBinary, "-c", "osm.sumocfg"])
            edges = []
            coordinates = carregar_coordenades(r)
            downsampled_coords = downsample_route(coordinates, 150)
            edges, edges_with_Coords =convertir_coordenades_a_edges(downsampled_coords, net)
            traci.close()
            final_data = []
            j = 7
            while j < 9:
                total_time_for_no_vehicles, result_for_no_vehicles, distance = run_simulation_with_no_vehicles(edges)
                #simulated_coords, simulated_time = mapa_generator_for_SUMO_data(result_for_no_vehicles,f"result_no_vehicles_map.html")
                data_for_no_vehicles, average_density_n_v, max_density_n_v = get_data_by_edge(result_for_no_vehicles, edges)
                results = []
                k = 0
                for k in range(2):
                    total_time_for_vehicles_and_no_device, vehicles_added_beginning, vehicles_added_during, result_for_vehicles_not_device, type1, type2, type3 = run_simulation_with_vehicles_and_no_device(j*30 + 1, 2*j, edges)
                    data_for_vehicles_no_device, average_density_v_n_d, max_density_v_n_d = get_data_by_edge(result_for_vehicles_not_device, edges)
                    #total_time_for_vehicles_and_lights_control, result_for_vehicles_and_light_control = run_simulation_with_vehicles_and_traffic_lights_activated_for_random_traffic(edges,j*50 + 1, 5*j, net)
                    #total_time_for_vehicles_and_device, result_for_vehicles_and_device, edges_with_no_tls_and_one_lane, edges_with_tls_and_one_lane, edges_with_tls_and_more_than_one_lane, edges_with_no_tls_and_more_than_one_lane = run_simulation_with_vehicles_and_device_random_traffic(edges,j*50 + 1, 5*j)
                    total_time_for_vehicles_and_lights_control, result_for_vehicles_and_light_control = run_simulation_with_vehicles_and_traffic_lights_activated_for_given_traffic(edges, vehicles_added_beginning, vehicles_added_during, net)
                    total_time_for_vehicles_and_device, result_for_vehicles_and_device, edges_with_no_tls_and_one_lane, edges_with_tls_and_one_lane, edges_with_tls_and_more_than_one_lane, edges_with_no_tls_and_more_than_one_lane = run_simulation_with_vehicles_and_device_and_given_traffic(edges, vehicles_added_beginning, vehicles_added_during)
                    print(f"total time for vehcile alone is: {total_time_for_no_vehicles}")
                    print(f"total time for vehicle and no device: {total_time_for_vehicles_and_no_device}")
                    print(f"total time for vehicle and lights control: {total_time_for_vehicles_and_lights_control}")
                    print(f"total time for vehicle and device: {total_time_for_vehicles_and_device}")
                    diference_from_ideal = total_time_for_vehicles_and_device - total_time_for_no_vehicles
                    total_diference_from_real = total_time_for_vehicles_and_no_device - total_time_for_vehicles_and_device
                    increase_in_ideal_percent = diference_from_ideal/total_time_for_no_vehicles*100
                    decrease_in_real_percent = total_diference_from_real/total_time_for_vehicles_and_no_device*100
                    print(f"the time has increased: {increase_in_ideal_percent} from the ideal conditions, but has decreased: {decrease_in_real_percent} from the 'real' conditions")
                    final_data.append([total_time_for_no_vehicles, total_time_for_vehicles_and_no_device, total_time_for_vehicles_and_device,diference_from_ideal, total_diference_from_real, increase_in_ideal_percent, decrease_in_real_percent])
                    data_for_vehicles_no_device, average_density_v_n_d, max_density_v_n_d = get_data_by_edge(result_for_vehicles_not_device, edges)
                    data_for_vehicles_and_device, average_density_v_d, max_density_v_d = get_data_by_edge(result_for_vehicles_and_device, edges)
                    #data_compared = compare_data(data_for_no_vehicles, data_for_vehicles_no_device, data_for_vehicles_and_device, edges_with_no_tls_and_one_lane, edges_with_tls_and_one_lane, edges_with_no_tls_and_more_than_one_lane, edges_with_tls_and_more_than_one_lane)
                    edges_tls_more_one = len(edges_with_tls_and_more_than_one_lane)/len(edges)*100
                    edges_no_tls_more_one = len(edges_with_no_tls_and_more_than_one_lane)/len(edges)*100
                    edges_tls_one = len(edges_with_tls_and_one_lane)/len(edges)*100
                    edges_no_tls_one = len(edges_with_no_tls_and_one_lane)/len(edges)*100
                    
                    results.append([type1/(type1+type2+type3), type2/(type1+type2+type3), type3/(type1+type2+type3), data_for_no_vehicles, data_for_vehicles_no_device, data_for_vehicles_and_device, total_time_for_no_vehicles, total_time_for_vehicles_and_no_device, total_time_for_vehicles_and_device, increase_in_ideal_percent, decrease_in_real_percent])

                    data_treatment_with_traffic_light(filename, distance,j, edges, k, type1/(type1+type2+type3), type2/(type1+type2+type3), type3/(type1+type2+type3), total_time_for_no_vehicles, total_time_for_vehicles_and_no_device, total_time_for_vehicles_and_device, total_time_for_vehicles_and_lights_control,  diference_from_ideal, total_diference_from_real, increase_in_ideal_percent, decrease_in_real_percent, edges_tls_more_one, edges_no_tls_more_one, edges_tls_one, edges_no_tls_one, average_density_v_n_d, average_density_v_d, max_density_v_n_d)

                    print(f"\n\n\n\n\n\n\n\n\n\n\n {j, k}")
                    #simulated_coords, simulated_time = mapa_generator_for_SUMO_data(result_for_vehicles_not_device,f"result_no_device_map_{j,k}.html")
                    #simulated_coords, simulated_time = mapa_generator_for_SUMO_data(result_for_vehicles_and_device,f"result_device_map{j,k}.html")
                    k += 1
                j += 1
                print(f"\n\n\n\n\n\n\n\n Data \n\n\n\n\n\n\n")
                total1 = 0
                total2 = 0
                total3 = 0
                total4 = 0
                total5 = 0
                total6 = 0
                total7 = 0

                for f in final_data:
                    total1 += f[0]
                    total2 += f[1]
                    total3 += f[2]
                    total4 += f[3]
                    total5 += f[4]
                    total6 += f[5]
                    total7 += f[6]

                print(f"The average ideal time is: {total1/len(final_data)}")
                print(f"The average real time is: {total2/len(final_data)}")
                print(f"The average device time is: {total3/len(final_data)}")
                print(f"The average difference between ideal time and device is: {total4/len(final_data)}")
                print(f"The average difference between ideal real time and device is: {total5/len(final_data)}")
                print(f"The average increase from ideal time is: {total6/len(final_data)}")
                print(f"The average decrease from real time is: {total7/len(final_data)}")
    else:
        j = 1
        while j < 20:
            net = sumolib.net.readNet('osm.net.xml')
            sumoBinary = sumolib.checkBinary("sumo")
            traci.start([sumoBinary, "-c", "osm.sumocfg"])
            edges = generate_random_route(traci.edge.getIDList(), net)
            traci.close()

            final_data = []

            total_time_for_no_vehicles, result_for_no_vehicles, distance = run_simulation_with_no_vehicles(edges)
            data_for_no_vehicles, average_density_n_v, max_density_n_v = get_data_by_edge(result_for_no_vehicles, edges)
            results = []
            k = 1
            while k < 9:
                for m in range(3):
                    total_time_for_vehicles_and_no_device, vehicles_added_beginning, vehicles_added_during, result_for_vehicles_not_device, type1, type2, type3 = run_simulation_with_vehicles_and_no_device(k*100 + 1 , k*2, edges)
                    total_time_for_vehicles_and_device, result_for_vehicles_and_device, edges_with_no_tls_and_one_lane, edges_with_tls_and_one_lane, edges_with_tls_and_more_than_one_lane, edges_with_no_tls_and_more_than_one_lane = run_simulation_with_vehicles_and_device_and_given_traffic(edges, vehicles_added_beginning, vehicles_added_during)
                    print(f"total time for vehcile alone is: {total_time_for_no_vehicles}")
                    print(f"total time for vehicle and no device: {total_time_for_vehicles_and_no_device}")
                    print(f"total time for vehicle and device: {total_time_for_vehicles_and_device}")
                    diference_from_ideal = total_time_for_vehicles_and_device - total_time_for_no_vehicles
                    total_diference_from_real = total_time_for_vehicles_and_no_device - total_time_for_vehicles_and_device
                    increase_in_ideal_percent = diference_from_ideal/total_time_for_no_vehicles*100
                    decrease_in_real_percent = total_diference_from_real/total_time_for_vehicles_and_no_device*100
                    print(f"the time has increased: {increase_in_ideal_percent} from the ideal conditions, but has decreased: {decrease_in_real_percent} from the 'real' conditions")
                    final_data.append([total_time_for_no_vehicles, total_time_for_vehicles_and_no_device, total_time_for_vehicles_and_device,diference_from_ideal, total_diference_from_real, increase_in_ideal_percent, decrease_in_real_percent])
                    data_for_vehicles_no_device, average_density_v_n_d, max_density_v_n_d = get_data_by_edge(result_for_vehicles_not_device, edges)
                    data_for_vehicles_and_device, average_density_v_d, max_density_v_d = get_data_by_edge(result_for_vehicles_and_device, edges)
                    #data_compared = compare_data(data_for_no_vehicles, data_for_vehicles_no_device, data_for_vehicles_and_device, edges_with_no_tls_and_one_lane, edges_with_tls_and_one_lane, edges_with_no_tls_and_more_than_one_lane, edges_with_tls_and_more_than_one_lane)
                    edges_tls_more_one = len(edges_with_tls_and_more_than_one_lane)/len(edges)*100
                    edges_no_tls_more_one = len(edges_with_no_tls_and_more_than_one_lane)/len(edges)*100
                    edges_tls_one = len(edges_with_tls_and_one_lane)/len(edges)*100
                    edges_no_tls_one = len(edges_with_no_tls_and_one_lane)/len(edges)*100
                    
                    results.append([type1/(type1+type2+type3), type2/(type1+type2+type3), type3/(type1+type2+type3), data_for_no_vehicles, data_for_vehicles_no_device, data_for_vehicles_and_device, total_time_for_no_vehicles, total_time_for_vehicles_and_no_device, total_time_for_vehicles_and_device, increase_in_ideal_percent, decrease_in_real_percent])                  
                    data_treatment(filename, distance,j, edges,  f"{k}_{m}", type1/(type1+type2+type3), type2/(type1+type2+type3), type3/(type1+type2+type3), total_time_for_no_vehicles, total_time_for_vehicles_and_no_device, total_time_for_vehicles_and_device, diference_from_ideal, total_diference_from_real, increase_in_ideal_percent, decrease_in_real_percent, edges_tls_more_one, edges_no_tls_more_one, edges_tls_one, edges_no_tls_one, average_density_v_n_d, average_density_v_d, max_density_v_n_d)
                    #data_treatment_2(data_for_no_vehicles, data_for_vehicles_no_device, data_for_vehicles_and_device, filename, distance, j, edges, f"{k}_{m}", type1/(type1+type2+type3), type2/(type1+type2+type3), type3/(type1+type2+type3), total_time_for_no_vehicles, total_time_for_vehicles_and_no_device, total_time_for_vehicles_and_device, diference_from_ideal, total_diference_from_real, increase_in_ideal_percent, decrease_in_real_percent, edges_with_tls_and_more_than_one_lane, edges_with_no_tls_and_more_than_one_lane, edges_with_tls_and_one_lane, edges_with_no_tls_and_one_lane, average_density_v_n_d, average_density_v_d, max_density_v_n_d)
                    
                    print(f"\n\n\n\n\n\n\n\n\n\n\n {j, k, m}")
                k += 1
            j += 1
            print(f"\n\n\n\n\n\n\n\n Data \n\n\n\n\n\n\n")
            total1 = 0
            total2 = 0
            total3 = 0
            total4 = 0
            total5 = 0
            total6 = 0
            total7 = 0

            for f in final_data:
                total1 += f[0]
                total2 += f[1]
                total3 += f[2]
                total4 += f[3]
                total5 += f[4]
                total6 += f[5]
                total7 += f[6]
            print(f"The average ideal time is: {total1/len(final_data)}")
            print(f"The average real time is: {total2/len(final_data)}")
            print(f"The average device time is: {total3/len(final_data)}")
            print(f"The average difference between ideal time and device is: {total4/len(final_data)}")
            print(f"The average difference between ideal real time and device is: {total5/len(final_data)}")
            print(f"The average increase from ideal time is: {total6/len(final_data)}")
            print(f"The average decrease from real time is: {total7/len(final_data)}")
elif comparisson_of_two_simulations:
    if specific_route:
        if json_defined_route:
            net = sumolib.net.readNet('osm.net.xml')
            sumoBinary = sumolib.checkBinary("sumo")
            traci.start([sumoBinary, "-c", "osm.sumocfg"])
            edges = []
            coordinates = carregar_coordenades(route)
            edges, edges_with_Coords =convertir_coordenades_a_edges(coordinates, net)
            traci.close()
        else:
            edges = ["526213091#0","449991627#0","1409649738#0","295124095#0"]
        final_data = []
        j = 3
        real_edges = edges
        while j < 26:
            total_time_for_no_vehicles, result_for_no_vehicles, distance = run_simulation_with_no_vehicles(real_edges)
            data_for_no_vehicles, average_density_n_v = get_data_by_edge(result_for_no_vehicles, real_edges)
            results = []
            k = 0
            for k in range(5):
                #total_time_for_vehicles_and_no_device, vehicles_added, result_for_vehicles_not_device, type1, type2, type3 = run_simulation_with_vehicles_and_no_device(150 + j*5, 15, real_edges)
                total_time_for_vehicles_and_device, result_for_vehicles_and_device, edges_with_no_tls_and_one_lane, edges_with_tls_and_one_lane, edges_with_tls_and_more_than_one_lane, edges_with_no_tls_and_more_than_one_lane, type1, type2, type3 = run_simulation_with_vehicles_and_device_random_traffic(real_edges, 550 + j*5, 15)
                print(f"total time for vehcile alone is: {total_time_for_no_vehicles}")
                #print(f"total time for vehicle and no device: {total_time_for_vehicles_and_no_device}")
                print(f"total time for vehicle and device: {total_time_for_vehicles_and_device}")
                diference_from_ideal = total_time_for_vehicles_and_device - total_time_for_no_vehicles
                #total_diference_from_real = total_time_for_vehicles_and_no_device - total_time_for_vehicles_and_device
                increase_in_ideal_percent = diference_from_ideal/total_time_for_no_vehicles*100
                #decrease_in_real_percent = total_diference_from_real/total_time_for_vehicles_and_no_device*100
                #print(f"the time has increased: {increase_in_ideal_percent} from the ideal conditions, but has decreased: {decrease_in_real_percent} from the 'real' conditions")
                final_data.append([total_time_for_no_vehicles, total_time_for_vehicles_and_device,diference_from_ideal, increase_in_ideal_percent])
                #data_for_vehicles_no_device, average_density_v_n_d = get_data_by_edge(result_for_vehicles_not_device, edges)
                data_for_vehicles_and_device, average_density_v_d = get_data_by_edge(result_for_vehicles_and_device, edges)
                #data_compared = compare_data(data_for_no_vehicles, data_for_vehicles_no_device, data_for_vehicles_and_device, edges_with_no_tls_and_one_lane, edges_with_tls_and_one_lane, edges_with_no_tls_and_more_than_one_lane, edges_with_tls_and_more_than_one_lane)
                edges_tls_more_one = len(edges_with_tls_and_more_than_one_lane)/len(real_edges)*100
                edges_no_tls_more_one = len(edges_with_no_tls_and_more_than_one_lane)/len(real_edges)*100
                edges_tls_one = len(edges_with_tls_and_one_lane)/len(real_edges)*100
                edges_no_tls_one = len(edges_with_no_tls_and_one_lane)/len(real_edges)*100
                total_time_for_vehicles_and_no_device = 0
                data_for_vehicles_no_device = 0
                decrease_in_real_percent = 0
                total_diference_from_real = 0
                average_density_v_n_d = 0
                results.append([type1/(type1+type2+type3), type2/(type1+type2+type3), type3/(type1+type2+type3), data_for_no_vehicles, data_for_vehicles_no_device, data_for_vehicles_and_device, total_time_for_no_vehicles, total_time_for_vehicles_and_no_device, total_time_for_vehicles_and_device, increase_in_ideal_percent, decrease_in_real_percent])
                data_treatment(filename, distance,j, real_edges, k, type1/(type1+type2+type3), type2/(type1+type2+type3), type3/(type1+type2+type3), total_time_for_no_vehicles, total_time_for_vehicles_and_no_device, total_time_for_vehicles_and_device, diference_from_ideal, total_diference_from_real, increase_in_ideal_percent, decrease_in_real_percent, edges_tls_more_one, edges_no_tls_more_one, edges_tls_one, edges_no_tls_one, average_density_v_n_d, average_density_v_d)
                print(f"\n\n\n\n\n\n\n\n\n\n\n {j, k}")
                k += 1
            j += 1
            print(f"\n\n\n\n\n\n\n\n Data \n\n\n\n\n\n\n")
            total1 = 0
            total2 = 0
            total3 = 0
            total4 = 0
            total5 = 0
            total6 = 0
            total7 = 0

            for f in final_data:
                total1 += f[0]
                total2 += f[1]
                total3 += f[2]
                total4 += f[3]

            print(f"The average ideal time is: {total1/len(final_data)}")
            print(f"The average device time is: {total2/len(final_data)}")
            print(f"The average difference between ideal time and device is: {total3/len(final_data)}")
            print(f"The average increase from ideal time is: {total4/len(final_data)}")
    else:
        j = 1
        with open(filename, "w") as f:
            json.dump({}, f)
        while j < 20:
            net = sumolib.net.readNet('osm.net.xml')
            sumoBinary = sumolib.checkBinary("sumo")
            traci.start([sumoBinary, "-c", "osm.sumocfg"])
            edges = generate_random_route(traci.edge.getIDList(), net)
            traci.close()

            final_data = []

            total_time_for_no_vehicles, result_for_no_vehicles, distance = run_simulation_with_no_vehicles(edges)
            data_for_no_vehicles, average_density_n_v = get_data_by_edge(result_for_no_vehicles, edges)
            results = []
            for k in range(10):
                for m in range(7):
                    total_time_for_vehicles_and_no_device, vehicles_added_beginning, vehicles_added_during, result_for_vehicles_not_device, type1, type2, type3 = run_simulation_with_vehicles_and_no_device(m*100, m*2, edges)
                    total_time_for_vehicles_and_device, result_for_vehicles_and_device, edges_with_no_tls_and_one_lane, edges_with_tls_and_one_lane, edges_with_tls_and_more_than_one_lane, edges_with_no_tls_and_more_than_one_lane = run_simulation_with_vehicles_and_device_and_given_traffic(edges, vehicles_added_beginning, vehicles_added_during)
                    print(f"total time for vehcile alone is: {total_time_for_no_vehicles}")
                    print(f"total time for vehicle and no device: {total_time_for_vehicles_and_no_device}")
                    print(f"total time for vehicle and device: {total_time_for_vehicles_and_device}")
                    diference_from_ideal = total_time_for_vehicles_and_device - total_time_for_no_vehicles
                    total_diference_from_real = total_time_for_vehicles_and_no_device - total_time_for_vehicles_and_device
                    increase_in_ideal_percent = diference_from_ideal/total_time_for_no_vehicles*100
                    decrease_in_real_percent = total_diference_from_real/total_time_for_vehicles_and_no_device*100
                    print(f"the time has increased: {increase_in_ideal_percent} from the ideal conditions, but has decreased: {decrease_in_real_percent} from the 'real' conditions")
                    final_data.append([total_time_for_no_vehicles, total_time_for_vehicles_and_no_device, total_time_for_vehicles_and_device,diference_from_ideal, total_diference_from_real, increase_in_ideal_percent, decrease_in_real_percent])
                    data_for_vehicles_no_device, average_density_v_n_d = get_data_by_edge(result_for_vehicles_not_device, edges)
                    data_for_vehicles_and_device, average_density_v_d = get_data_by_edge(result_for_vehicles_and_device, edges)
                    #data_compared = compare_data(data_for_no_vehicles, data_for_vehicles_no_device, data_for_vehicles_and_device, edges_with_no_tls_and_one_lane, edges_with_tls_and_one_lane, edges_with_no_tls_and_more_than_one_lane, edges_with_tls_and_more_than_one_lane)
                    edges_tls_more_one = len(edges_with_tls_and_more_than_one_lane)/len(edges)*100
                    edges_no_tls_more_one = len(edges_with_no_tls_and_more_than_one_lane)/len(edges)*100
                    edges_tls_one = len(edges_with_tls_and_one_lane)/len(edges)*100
                    edges_no_tls_one = len(edges_with_no_tls_and_one_lane)/len(edges)*100
                    
                    results.append([type1/(type1+type2+type3), type2/(type1+type2+type3), type3/(type1+type2+type3), data_for_no_vehicles, data_for_vehicles_no_device, data_for_vehicles_and_device, total_time_for_no_vehicles, total_time_for_vehicles_and_no_device, total_time_for_vehicles_and_device, increase_in_ideal_percent, decrease_in_real_percent])
                    data_treatment(filename, distance, j, edges, f"{k}_{m}", type1/(type1+type2+type3), type2/(type1+type2+type3), type3/(type1+type2+type3), total_time_for_no_vehicles, total_time_for_vehicles_and_no_device, total_time_for_vehicles_and_device, diference_from_ideal, total_diference_from_real, increase_in_ideal_percent, decrease_in_real_percent, edges_tls_more_one, edges_no_tls_more_one, edges_tls_one, edges_no_tls_one, average_density_v_n_d, average_density_v_d)
                    print(f"\n\n\n\n\n\n\n\n\n\n\n {j, k, m}")

            j += 1
            print(f"\n\n\n\n\n\n\n\n Data \n\n\n\n\n\n\n")
            total1 = 0
            total2 = 0
            total3 = 0
            total4 = 0
            total5 = 0
            total6 = 0
            total7 = 0

            for f in final_data:
                total1 += f[0]
                total2 += f[1]
                total3 += f[2]
                total4 += f[3]
                total5 += f[4]
                total6 += f[5]
                total7 += f[6]
            print(f"The average ideal time is: {total1/len(final_data)}")
            print(f"The average real time is: {total2/len(final_data)}")
            print(f"The average device time is: {total3/len(final_data)}")
            print(f"The average difference between ideal time and device is: {total4/len(final_data)}")
            print(f"The average difference between ideal real time and device is: {total5/len(final_data)}")
            print(f"The average increase from ideal time is: {total6/len(final_data)}")
            print(f"The average decrease from real time is: {total7/len(final_data)}")


"""
final_data = []
filename = "result_comparison_2.json"
with open(filename, "w") as f:
    json.dump({}, f)  # empty dictionary

total_time_for_no_vehicles, result_for_no_vehicles, distance = run_simulation_with_no_vehicles(edges)
data_for_no_vehicles, average_density_n_v = get_data_by_edge(result_for_no_vehicles, edges)
results = []
j = 3
while j < 11:
    for k in range(10):
        total_time_for_vehicles_and_no_device, vehicles_added, result_for_vehicles_not_device, type1, type2, type3 = run_simulation_with_vehicles_and_no_device(j*100, j, edges)
        total_time_for_vehicles_and_device, result_for_vehicles_and_device, edges_with_no_tls_and_one_lane, edges_with_tls_and_one_lane, edges_with_tls_and_more_than_one_lane, edges_with_no_tls_and_more_than_one_lane = run_simulation_with_vehicles_and_device(edges, vehicles_added)
        print(f"total time for vehcile alone is: {total_time_for_no_vehicles}")
        print(f"total time for vehicle and no device: {total_time_for_vehicles_and_no_device}")
        print(f"total time for vehicle and device: {total_time_for_vehicles_and_device}")
        diference_from_ideal = total_time_for_vehicles_and_device - total_time_for_no_vehicles
        total_diference_from_real = total_time_for_vehicles_and_no_device - total_time_for_vehicles_and_device
        increase_in_ideal_percent = diference_from_ideal/total_time_for_no_vehicles*100
        decrease_in_real_percent = total_diference_from_real/total_time_for_vehicles_and_no_device*100
        print(f"the time has increased: {increase_in_ideal_percent} from the ideal conditions, but has decreased: {decrease_in_real_percent} from the 'real' conditions")
        final_data.append([total_time_for_no_vehicles, total_time_for_vehicles_and_no_device, total_time_for_vehicles_and_device,diference_from_ideal, total_diference_from_real, increase_in_ideal_percent, decrease_in_real_percent])
        data_for_vehicles_no_device, average_density_v_n_d = get_data_by_edge(result_for_vehicles_not_device, edges)
        data_for_vehicles_and_device, average_density_v_d = get_data_by_edge(result_for_vehicles_and_device, edges)
        #data_compared = compare_data(data_for_no_vehicles, data_for_vehicles_no_device, data_for_vehicles_and_device, edges_with_no_tls_and_one_lane, edges_with_tls_and_one_lane, edges_with_no_tls_and_more_than_one_lane, edges_with_tls_and_more_than_one_lane)
        edges_tls_more_one = len(edges_with_tls_and_more_than_one_lane)/len(edges)*100
        edges_no_tls_more_one = len(edges_with_no_tls_and_more_than_one_lane)/len(edges)*100
        edges_tls_one = len(edges_with_tls_and_one_lane)/len(edges)*100
        edges_no_tls_one = len(edges_with_no_tls_and_one_lane)/len(edges)*100
        
        results.append([type1/(type1+type2+type3), type2/(type1+type2+type3), type3/(type1+type2+type3), data_for_no_vehicles, data_for_vehicles_no_device, data_for_vehicles_and_device, total_time_for_no_vehicles, total_time_for_vehicles_and_no_device, total_time_for_vehicles_and_device, increase_in_ideal_percent, decrease_in_real_percent])
        data_treatment(filename, distance,j, edges, k, type1/(type1+type2+type3), type2/(type1+type2+type3), type3/(type1+type2+type3), total_time_for_no_vehicles, total_time_for_vehicles_and_no_device, total_time_for_vehicles_and_device, diference_from_ideal, total_diference_from_real, increase_in_ideal_percent, decrease_in_real_percent, edges_tls_more_one, edges_no_tls_more_one, edges_tls_one, edges_no_tls_one, average_density_v_n_d, average_density_v_d)
        print(f"\n\n\n\n\n\n\n\n\n\n\n {j, k}")
    j += 1
    print(f"\n\n\n\n\n\n\n\n Data \n\n\n\n\n\n\n")
    total1 = 0
    total2 = 0
    total3 = 0
    total4 = 0
    total5 = 0
    total6 = 0
    total7 = 0

    for f in final_data:
        total1 += f[0]
        total2 += f[1]
        total3 += f[2]
        total4 += f[3]
        total5 += f[4]
        total6 += f[5]
        total7 += f[6]

    print(f"The average ideal time is: {total1/len(final_data)}")
    print(f"The average real time is: {total2/len(final_data)}")
    print(f"The average device time is: {total3/len(final_data)}")
    print(f"The average difference between ideal time and device is: {total4/len(final_data)}")
    print(f"The average difference between ideal real time and device is: {total5/len(final_data)}")
    print(f"The average increase from ideal time is: {total6/len(final_data)}")
    print(f"The average decrease from real time is: {total7/len(final_data)}")


"""
"""
sumoBinary = sumolib.checkBinary("sumo-gui")
traci.start([sumoBinary, "-c", "osm.sumocfg"])
#net = sumolib.net.readNet('osm.net.xml')
#coordinates = carregar_coordenades(route)

#congestedCoords = generate_congestion(coordinates, 0, 50, 2)
#resampled_coords = resample_route(coordinates, max_distance_m=1)
#edges, edges_with_Coords = convertir_coordenades_a_edges(resampled_coords, net)
#real_coords, real_time = mapa_generator_for_OSM_data(congestedCoords, 'Mapa_V_gradient.html')
#real_edges_congestion = get_congestion_for_edge(congestedCoords, edges_with_Coords)

# region Random vehicle types generation
traci.vehicletype.copy("DEFAULT_VEHTYPE", "Compliance_0")
traci.vehicletype.setParameter("Compliance_0", "device.bluelight.device", "true")
traci.vehicletype.setParameter("Compliance_0", "device.bluelight.compliance", "1")
traci.vehicletype.setParameter("Compliance_0", "device.bluelight.visibility", "150")
traci.vehicletype.setParameter("Compliance_0", "device.bluelight.responseTime", "0.5")
traci.vehicletype.setParameter("Compliance_0", "device.bluelight.reaction-prob-near", "1")
traci.vehicletype.setParameter("Compliance_0", "device.bluelight.reaction-prob-far", "1")
traci.vehicletype.setParameter("Compliance_0", "device.bluelight.minGap", "3")
traci.vehicletype.setParameter("Compliance_0", "device.bluelight.mingapfactor", "0")
traci.vehicletype.setParameter("Compliance_0", "lcStrategic", "0")
traci.vehicletype.setParameter("Compliance_0", "lcSublane", "0")
traci.vehicletype.setParameter("Compliance_0", "laneChangeModel.lcCooperative", "1")
traci.vehicletype.setParameter("Compliance_0", "laneChangeModel.lcAssertive", "1")
traci.vehicletype.setParameter("Compliance_0", "laneChangeModel.lcImpatience", "1")

traci.vehicletype.copy("DEFAULT_VEHTYPE", "Compliance_1")
traci.vehicletype.setParameter("Compliance_1", "device.bluelight.device", "true")
traci.vehicletype.setParameter("Compliance_1", "device.bluelight.compliance", "1")
traci.vehicletype.setParameter("Compliance_1", "device.bluelight.visibility", "150")
traci.vehicletype.setParameter("Compliance_1", "device.bluelight.responseTime", "0.5")
traci.vehicletype.setParameter("Compliance_1", "device.bluelight.reaction-prob-near", "0.9")
traci.vehicletype.setParameter("Compliance_1", "device.bluelight.reaction-prob-far", "0.35")
traci.vehicletype.setParameter("Compliance_1", "device.bluelight.minGap", "1.5")
traci.vehicletype.setParameter("Compliance_1", "device.bluelight.mingapfactor", "2")
traci.vehicletype.setParameter("Compliance_1", "lcStrategic", "0")
traci.vehicletype.setParameter("Compliance_1", "lcSublane", "0")
traci.vehicletype.setParameter("Compliance_1", "laneChangeModel.lcCooperative", "0.95")
traci.vehicletype.setParameter("Compliance_1", "laneChangeModel.lcAssertive", "0.95")
traci.vehicletype.setParameter("Compliance_1", "laneChangeModel.lcImpatience", "0.95")

traci.vehicletype.copy("DEFAULT_VEHTYPE", "Compliance_2")
traci.vehicletype.setParameter("Compliance_2", "device.bluelight.device", "true")
traci.vehicletype.setParameter("Compliance_2", "device.bluelight.compliance", "0.8")
traci.vehicletype.setParameter("Compliance_2", "device.bluelight.visibility", "125")
traci.vehicletype.setParameter("Compliance_2", "device.bluelight.responseTime", "1.5")
traci.vehicletype.setParameter("Compliance_2", "device.bluelight.reaction-prob-near", "0.8")
traci.vehicletype.setParameter("Compliance_2", "device.bluelight.reaction-prob-far", "0.3")
traci.vehicletype.setParameter("Compliance_2", "device.bluelight.minGap", "2")
traci.vehicletype.setParameter("Compliance_2", "device.bluelight.mingapfactor", "2")
traci.vehicletype.setParameter("Compliance_2", "lcStrategic", "0")
traci.vehicletype.setParameter("Compliance_2", "lcSublane", "0")
traci.vehicletype.setParameter("Compliance_2", "laneChangeModel.lcCooperative", "0.85")
traci.vehicletype.setParameter("Compliance_2", "laneChangeModel.lcAssertive", "0.85")
traci.vehicletype.setParameter("Compliance_2", "laneChangeModel.lcImpatience", "0.85")

traci.vehicletype.copy("DEFAULT_VEHTYPE", "Compliance_3")
traci.vehicletype.setParameter("Compliance_3", "device.bluelight.device", "true")
traci.vehicletype.setParameter("Compliance_3", "device.bluelight.compliance", "0.6")
traci.vehicletype.setParameter("Compliance_3", "device.bluelight.visibility", "75")
traci.vehicletype.setParameter("Compliance_3", "device.bluelight.responseTime", "3.5")
traci.vehicletype.setParameter("Compliance_3", "device.bluelight.reaction-prob-near", "0.65")
traci.vehicletype.setParameter("Compliance_3", "device.bluelight.reaction-prob-far", "0.15")
traci.vehicletype.setParameter("Compliance_3", "device.bluelight.minGap", "2")
traci.vehicletype.setParameter("Compliance_3", "device.bluelight.mingapfactor", "1")
traci.vehicletype.setParameter("Compliance_3", "lcStrategic", "0")
traci.vehicletype.setParameter("Compliance_3", "lcSublane", "0")
traci.vehicletype.setParameter("Compliance_3", "laneChangeModel.lcCooperative", "0.75")
traci.vehicletype.setParameter("Compliance_3", "laneChangeModel.lcAssertive", "0.75")
traci.vehicletype.setParameter("Compliance_3", "laneChangeModel.lcImpatience", "0.75")
# endregion

# region Ambulance vehicle creation
veh_id = "ambulance"
route_id = "ambulance_route"

traci.route.add(route_id, edges)
traci.vehicletype.copy("DEFAULT_VEHTYPE", "rescue")
traci.vehicletype.setVehicleClass("rescue", "emergency")
traci.vehicletype.setShapeClass("rescue", "emergency")
traci.vehicletype.setMaxSpeed("rescue", 50)
traci.vehicletype.setSpeedFactor("rescue", 1.5)
traci.vehicletype.setParameter("rescue", "has.bluelight.device", "true")
traci.vehicletype.setParameter("rescue", "latAlignment", "arbitrary")
traci.vehicletype.setParameter("rescue", "sigma", "0")
traci.vehicletype.setParameter("rescue", "jmIgnoreFoeProb", "1")
traci.vehicletype.setParameter("rescue", "jmIgnoreKeepClearTime", "1")
traci.vehicletype.setParameter("rescue", "jmDriveRedSpeed", "2.77")
traci.vehicletype.setParameter("rescue", "impatience", "1.0")
traci.vehicletype.setParameter("rescue", "lcPushy", "1")
traci.vehicletype.setParameter("rescue", "lcImpatience", "1")
traci.vehicletype.setParameter("rescue", "lcTimeToImpatience", "0")
traci.vehicletype.setParameter("rescue", "lcOpposite", "1")
traci.vehicletype.setParameter("rescue", "lcOvertakeRight", "1")
traci.vehicletype.setParameter("rescue", "lcStrategic", "0")
traci.vehicletype.setParameter("rescue", "lcSpeedGain", "1")
traci.vehicletype.setParameter("rescue", "lcAssertive", "1")
traci.vehicletype.setParameter("rescue", "lcCooperative", "0")
traci.vehicletype.setParameter("rescue", "minGapLat", "0.25")
traci.vehicletype.setParameter("rescue", "minGap", "0.5")
traci.vehicletype.setParameter("rescue", "junction.blocker", "false")
traci.vehicletype.setParameter("rescue", "jmIgnoreFoeProb", "1")
traci.vehicle.add(
    vehID=veh_id,
    routeID=route_id,
    typeID="rescue",
    depart=100,
    departLane="best"
)

#endregion

#ATENCIÓ !!!!!!!!
#Aquesta funció retorna els edges on si que es podria fer un camí d'emergència i aquells on no,
#Això s'ha de tenir en compte per despres mirar si s'ha de generar el camí d'emergència, o si s'ha de jugar
#amb els semàfors per fer que l'ambulància pugui passar sense problemes.
edges_with_emergency_path, edges_without_emergency_path, sequence_of_edges_with_no_emergency_path = find_data_from_ambulance_route(edges)

print("\n\n\nEdges with emergency path:")
print(sequence_of_edges_with_no_emergency_path)


#Adding the emergency lanes at the begining of the simulation.

for e in edges_with_emergency_path:
    traci.lane.setAllowed(e+"_0", ["emergency"])

vehicles_added = []

#The next function generates a specified amount of vehicles with random routes and choosing one of the 
#three compliance types. Each one of them represents a different attitude towards the ambulance.
#They are then saved into the vehicles_added list, which will then be used to add them back to the second 
#Simulation, this would then allow to extract results for the same simulations using or not the device.
i = 0
while i < 150:
    edge_list = generate_random_route_starting_at_specific_edge("228671312#2", edges, traci.edge.getIDList())
    while edge_list is None:
        edge_list = generate_random_route_starting_at_specific_edge("228671312#2", edges, traci.edge.getIDList())
    k = 1
    type = valor_proper(k,1, 3)
    typeId = None
    if round(type) == 1:
        typeId = "Compliance_1"
    elif round(type) == 2:
        typeId = "Compliance_2"
    elif round(type) == 3:
        typeId = "Compliance_3"
    traci.route.add("test"+str(i), edge_list)
    #Per fer proves de com afecta l'actitud dels conductors.
    #traci.vehicle.add("test"+str(i), routeID="test"+str(i), departLane="best", typeID=typeId)
    traci.vehicle.add("test"+str(i), routeID="test"+str(i), departLane="best", typeID="Compliance_0")
    vehicles_added.append(["test"+str(i), edge_list, typeId])
    i += 1

traci.simulationStep()
stop = False  #ATENCIÓ!!!!!!!!!!!!!!!!!!!!!!

result = []
lights_to_change = []
emergency_lanes_to_cancel = []
configured = False

device_active = False
allowed = None

while not stop:
    traci.simulationStep()
    
    if traci.simulation.getTime() == 100000:
        for e in edges_with_emergency_path:
            allowed = traci.lane.getAllowed(e+"_0")
            thing_to_append = activate__emergency_lane_in_edge(e, edges)
            if thing_to_append is not None:
                lights_to_change.append(thing_to_append)
                emergency_lanes_to_cancel.append([thing_to_append[0], e])

    if veh_id in traci.vehicle.getIDList():
        lane = traci.vehicle.getLaneIndex(veh_id)
        edge = traci.vehicle.getRoadID(veh_id)
        lanes = traci.edge.getLaneNumber(edge)
        lane_id = traci.vehicle.getLaneID(veh_id)

        next_edge = get_next_valid_edge(edge, edges)
        next_tls = None
        if next_edge in edges_without_emergency_path:
            next_tls = find_if_street_has_traffic_light_for_edge(next_edge)
        if next_tls:
            current_next_light, next_state, next_idx = get_light_state_for_edge(next_edge, next_tls)
            if "r" in current_next_light:
                change_traffic_lights_for_whole_edge(next_tls, "G", next_state, next_idx)
                try:
                    next_next_edge = get_next_valid_edge(next_edge, edges)
                    if next_next_edge is not None:
                        lights_to_change.append([next_next_edge, next_tls])
                except Exception as e:
                    print("Error:", e)
        #These two lines are used to either bring back the lights cycle to normal, or to elminate the emergency lanes created
        for l in lights_to_change:
            e = l[0]
            tls = l[1]
            if edge == e: 
                traci.trafficlight.setProgram(tls, "0")
            
        for l in emergency_lanes_to_cancel:
            e = l[0]
            deactivated_edge = l[1]
            if edge == e:
                traci.lane.setAllowed(str(deactivated_edge) + "_0", allowed)
            
        if device_active:
            tls = find_if_street_has_traffic_light(veh_id)
            if tls:
                current_light, state, idx = get_light_state_for_edge(edge, tls)
                if "r" in current_light:
                    change_traffic_lights_for_whole_edge(tls, "G", state, idx)
                    try:
                        next_edge = get_next_valid_edge(edge, edges)
                        if next_edge is not None:
                            lights_to_change.append([next_edge, tls])
                    except Exception as e:
                        print("Error:", e)
            next_tls = None
            next_edge = get_next_valid_edge(edge, edges)
            if next_edge is not None:
                next_tls = find_if_street_has_traffic_light_for_edge(next_edge)
            if next_tls:
                current_next_light, next_state, next_idx = get_light_state_for_edge(next_edge, next_tls)
                if "r" in current_next_light:
                    change_traffic_lights_for_whole_edge(next_tls, "G", next_state, next_idx)
                    try:
                        next_next_edge = get_next_valid_edge(next_edge, edges)
                        if next_next_edge is not None:
                            lights_to_change.append([next_next_edge, next_tls])
                    except Exception as e:
                        print("Error:", e)
            
            emergency_lane = find_if_there_is_emergency_lane(veh_id)
            if not emergency_lane:
                create_emergency_lane(veh_id, edge)

    #Aquesta part del codi el que està fent és mirar si l'ambulància està a la simulació, si ho està, agafa les seves dades
    #coords, velocitat, temps... i ho guarda per després comparar-ho amb les dades reals
    #També fa un comportament de l'ambulància que a la simulació normal no fa, si hi ha un vehicle aturat al davant i és degut a un semàfor
    #en vermell, en un cas real aquests vehicles atravesarien el semàfor en vermell per deixar passar l'ambulànci, però a la simulació normal 
    #això no es fa. Aquesta part del codi mira si està o no en aquest cas, i si ho està fa aquesta funció.

    if veh_id in traci.vehicle.getIDList(): 
        x,y = traci.vehicle.getPosition(veh_id)
        lon, lat = net.convertXY2LonLat(x,y)
        currentTime = datetime.now(timezone.utc)
        time = traci.simulation.getTime()
        result.append([lon,lat,time])
        speed = traci.vehicle.getSpeed(veh_id)
        if speed <= 0.5:
            leaders = []
            leader = traci.vehicle.getLeader(veh_id, 5)
            while leader != None:
                leaders.append(leader[0])
                leader = traci.vehicle.getLeader(leader[0], 5)
                if leader == None:
                    continue
                if leader[1] > 5:
                    leader = None
            if len(leaders) <= 5 and len(leaders) != 0:
                for l in leaders:
                    traci.vehicle.setSpeedMode(l, 7)
                    speed = traci.vehicle.getSpeed(l)
                    traci.vehicle.setSpeed(l, speed + (1 / 1))
        try:
            #print(get_data_for_congestion_IA(edges, veh_id, real_edges_congestion, net))
            jk = 2
        except Exception as e:
            print("Error:", e)
    
    for v in traci.vehicle.getIDList():
        if v == veh_id:
            continue
        v_edge = traci.vehicle.getRoadID(v)
        allowed = traci.lane.getAllowed(v_edge + "_0")
        if len(allowed) == 1 and allowed[0] == "emergency":
            traci.vehicle.changeLaneRelative(v, 1, 60)
            #traci.vehicle.setLaneChangeMode(v, 512)  # Set lane change mode to allow emergency lane changes
            continue

    if veh_id in traci.simulation.getArrivedIDList():
        with open("result_with_device.json", "w") as f:
            json.dump(result, f)
        simulated_coords, simulated_time = mapa_generator_for_SUMO_data(result,'result_map.html')
        stop = True

traci.close()

result = []
with open("result_with_device.json", "r") as f:
    result = json.load(f)

simulated_coords, simulated_time = mapa_generator_for_SUMO_data(result,'result_map.html')
#congestion_analyzer(real_coords, real_time, simulated_coords,simulated_time, result, congestedCoords, edges_with_Coords)
"""
