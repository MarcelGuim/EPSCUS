from logging import root
import traci, math
import traci.constants as tc
import json
import xml.etree.ElementTree as ET
from pyproj import Proj, Transformer
import sumolib
from shapely.geometry import LineString, Point
from geopy.distance import geodesic
import xml.etree.ElementTree as ET
from routePreparator import mapa_generator_for_SUMO_data, resample_route, get_next_valid_edge, find_if_street_has_traffic_light, get_vehicles_in_front_of_ambulance, get_light_state, carregar_coordenades, generate_congestion, mapa_generator_for_OSM_data, get_data_for_congestion_IA, find_data_from_ambulance_route, valor_proper
from trafficGenerator import  generate_random_traffic_with_TRACI_for_begining_for_AI, generate_random_traffic_with_TRACI_for_during_in_next_edge, congestion_analyzer, get_congestion_for_edge, generate_random_route_starting_at_next_edge, generate_random_route_starting_at_specific_edge, generate_random_traffic_with_TRACI_for_during_in_random_edge_from_edges
from datetime import datetime, timedelta, timezone
from importRoutes import escriure_ruta, convertir_coordenades_a_edges
from dispositiu import find_if_there_is_emergency_lane, find_if_street_has_traffic_light, get_light_state, change_traffic_light_for_one_lane, change_traffic_lights_for_whole_edge, get_light_state_for_edge, create_emergency_lane, find_if_street_has_traffic_light_for_edge, activate_emergency_lane_in_edge
import random

class EdgeClass:
    def __init__(self,id, lanes, length, speed, vehicles, number_of_exits, density_at_the_exits, start_time, end_time):
        self.id = id
        self.lanes = lanes  # instance attribute
        self.length = length
        self.speed = speed
        self.vehicles = vehicles
        self.number_of_exits = number_of_exits
        self.density_at_the_exits = density_at_the_exits
        self.start_time = start_time
        self.end_time = end_time
    def get_data(self):
        return [self.lanes, self.length, self.speed, self.vehicles, self.number_of_exits, self.density_at_the_exits, float(self.end_time) - float(self.start_time)]


def run_simulation_with_vehicles_and_no_device(edges):
    sumoBinary = sumolib.checkBinary("sumo")
    traci.start([sumoBinary, "-c", "osm.sumocfg"])
    net = sumolib.net.readNet('osm.net.xml')

    # region Ambulance vehicle creation
    veh_id = "ambulance"
    route_id = "ambulance_route"
    depart_time = 200
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
    traci.vehicletype.setParameter("rescue", "junction.blocker", "true")
    traci.vehicletype.setParameter("rescue", "jmIgnoreFoeProb", "1")
    traci.vehicle.add(
        vehID=veh_id,
        routeID=route_id,
        typeID="rescue",
        depart=depart_time,
        departLane="best"
    )

    #endregion

    initial_amount = 1
    vehicles_added_beginning, type1, type2, type3, last_num = generate_random_traffic_with_TRACI_for_begining_for_AI(edges, initial_amount, net)
    result = []
    stop = False
    num = 0
    previous_edge = None
    edge_to_detect_stopping = None
    vehicles_added_during = []
    current_edge_from_list = None
    while not stop:
        traci.simulationStep()
        waiting = traci.simulation.getLoadedIDList()
        #This part allows entering vehicles to the sumilation whilst running, that way every X seconds Y vehicles are added to it.
        if traci.simulation.getTime()%10 == 0:
            next_edge = None
            next_next_edge = None
            if veh_id in traci.vehicle.getIDList():
                edge = traci.vehicle.getRoadID(veh_id)
                if edge in edges:
                    current_edge_from_list = edge
                if current_edge_from_list != None:
                    index = edges.index(current_edge_from_list)
                    if index < len(edges) - 1:
                        next_edge = edges[index + 1]
                    if index < len(edges) - 2:
                        next_next_edge = edges[index + 2]
            amount_next_edge = 1
            amount_next_next_edge = 1
            thing_to_append, type1_2, type2_2, type3_2, last_num = generate_random_traffic_with_TRACI_for_during_in_next_edge(next_edge, next_next_edge, edges, amount_next_edge, amount_next_next_edge, net, last_num + 1, veh_id)
            type1 += type1_2
            type2 += type2_2
            type3 += type3_2
            for t in thing_to_append:
                vehicles_added_during.append(t)
            num += 1

        if veh_id in traci.vehicle.getIDList():

            edge = traci.vehicle.getRoadID(veh_id)
            next_edge = None
            if edge in edges:
                current_edge_from_list = edge
                if edges.index(current_edge_from_list) != len(edges) - 1:
                    next_edge = edges[edges.index(current_edge_from_list) + 1]
            """            
            waiting = traci.simulation.getLoadedIDList()
            if len(waiting) != 0:
                for w in waiting:
                    if w == "simulation.findRoute":
                        continue
                    route = traci.vehicle.getRoute(w)
                    if route and next_edge != None and route[0] == next_edge:
                        traci.vehicle.remove(w)
            """

            x,y = traci.vehicle.getPosition(veh_id)
            edge = traci.vehicle.getRoadID(veh_id)
            lon, lat = net.convertXY2LonLat(x,y)
            currentTime = datetime.now(timezone.utc)
            time = traci.simulation.getTime()
            speed = traci.vehicle.getSpeed(veh_id)
            speed_lane = traci.lane.getMaxSpeed(edge+"_0")
            if speed < speed_lane:
                traci.vehicle.setSpeed(veh_id, speed_lane*1.25) 
            current_edge = traci.vehicle.getRoadID(veh_id)
            lanes = traci.edge.getLaneNumber(current_edge)
            length = traci.lane.getLength(current_edge+"_0")
            if previous_edge == None or current_edge != previous_edge:
                previous_edge = current_edge
            vehicles = traci.edge.getLastStepVehicleNumber(current_edge)

            result.append([lon,lat,time, speed, previous_edge, vehicles, lanes, length]) 
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
                        traci.vehicle.setSpeed(l, speed_lane)
            if edge_to_detect_stopping == None:
                edge_to_detect_stopping = edge                   
            if traci.simulation.getTime()%500 == 0:
                if edge_to_detect_stopping == edge:
                    stop = True
                else:
                    edge_to_detect_stopping == edge
        
        if veh_id in traci.simulation.getArrivedIDList():
            with open("result_with_traffic_and_no_device.json", "w") as f:
                json.dump(result, f)
            stop = True
    traci.close()

    total_time = result[-1][2] - result[0][2]
    print(f"Total time for simulation with vehicles but no device activation is: {total_time} seconds")

    return total_time, vehicles_added_beginning, vehicles_added_during, result, type1, type2, type3

def run_simulation_with_vehicles_and_no_device_for_data_gathering(edges, initial_traffic, simulation_traffic):
    sumoBinary = sumolib.checkBinary("sumo")
    traci.start([sumoBinary, "-c", "osm.sumocfg"])
    net = sumolib.net.readNet('osm.net.xml')

    # region Ambulance vehicle creation
    veh_id = "ambulance"
    route_id = "ambulance_route"
    depart_time = 100
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
    traci.vehicletype.setParameter("rescue", "junction.blocker", "true")
    traci.vehicletype.setParameter("rescue", "jmIgnoreFoeProb", "1")
    traci.vehicle.add(
        vehID=veh_id,
        routeID=route_id,
        typeID="rescue",
        depart=depart_time,
        departLane="best"
    )

    #endregion

    vehicles_added_beginning, type1, type2, type3, last_num = generate_random_traffic_with_TRACI_for_begining_for_AI(edges, initial_traffic, net)
    result = []
    stop = False
    current_edge_from_list = None
    current_edge_from_list_2 = None
    edge_entry_time = 0
    data_for_training = []
    vehicles_in_entrance = 0
    while not stop:
        traci.simulationStep()
        #This part allows entering vehicles to the sumilation whilst running, that way every X seconds Y vehicles are added to it.
        if traci.simulation.getTime()%10 == 0:
            next_edge = None
            next_next_edge = None
            if veh_id in traci.vehicle.getIDList():
                edge = traci.vehicle.getRoadID(veh_id)
                if edge in edges:
                    current_edge_from_list = edge
                if current_edge_from_list != None:
                    index = edges.index(current_edge_from_list)
                    if index < len(edges) - 1:
                        next_edge = edges[index + 1]
                    if index < len(edges) - 2:
                        next_next_edge = edges[index + 2]
            amount_next_edge = round(simulation_traffic/2)
            amount_next_next_edge = amount_next_edge
            thing_to_append, type1_2, type2_2, type3_2, last_num = generate_random_traffic_with_TRACI_for_during_in_next_edge(next_edge, next_next_edge, edges, amount_next_edge, amount_next_next_edge, net, last_num + 1, veh_id)
        if veh_id in traci.vehicle.getIDList():
            edge = traci.vehicle.getRoadID(veh_id)
            if edge in edges and edge != current_edge_from_list_2:
                if current_edge_from_list_2 == None:
                    current_edge_from_list_2 = edge
                    edge_entry_time = traci.simulation.getTime()
                    vehicles_in_entrance = traci.edge.getLastStepVehicleNumber(current_edge_from_list_2)
                else:
                    speed_lane = traci.lane.getMaxSpeed(current_edge_from_list_2+"_0")
                    lanes = traci.edge.getLaneNumber(current_edge_from_list_2)
                    length = traci.lane.getLength(current_edge_from_list_2+"_0")
                    data_for_training.append([length, lanes, speed_lane, vehicles_in_entrance, traci.simulation.getTime() - edge_entry_time])
                    current_edge_from_list_2 = edge
                    edge_entry_time = traci.simulation.getTime()
                    vehicles_in_entrance = traci.edge.getLastStepVehicleNumber(current_edge_from_list_2)
            speed = traci.vehicle.getSpeed(veh_id)
            speed_lane = traci.lane.getMaxSpeed(edge+"_0")
            if speed < speed_lane:
                traci.vehicle.setSpeed(veh_id, speed_lane*1.25) 
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
                            traci.vehicle.setSpeed(l, speed_lane)
            """
            time = traci.simulation.getTime()
            speed_lane = traci.lane.getMaxSpeed(edge+"_0")
            if speed < speed_lane:
                traci.vehicle.setSpeed(veh_id, speed_lane*1.25) 
            current_edge = traci.vehicle.getRoadID(veh_id)
            lanes = traci.edge.getLaneNumber(current_edge)
            length = traci.lane.getLength(current_edge+"_0")
            if previous_edge == None or current_edge != previous_edge:
                previous_edge = current_edge
            vehicles = traci.edge.getLastStepVehicleNumber(current_edge)

            result.append([lon,lat,time, speed, previous_edge, vehicles, lanes, length]) 
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
                        traci.vehicle.setSpeed(l, speed_lane)
            if edge_to_detect_stopping == None:
                edge_to_detect_stopping = edge                   
            if traci.simulation.getTime()%500 == 0:
                if edge_to_detect_stopping == edge:
                    stop = True
                else:
                    edge_to_detect_stopping == edge
            """
        if veh_id in traci.simulation.getArrivedIDList():
            stop = True
    traci.close()

    return data_for_training

def run_simulation_with_no_device_and_vehicles_set_with_regression_ML(edges, data_for_ML, parameters):
    sumoBinary = sumolib.checkBinary("sumo")
    traci.start([sumoBinary, "-c", "osm.sumocfg"])
    net = sumolib.net.readNet('osm.net.xml')
    vehicles_added_beginning, type1, type2, type3, last_num = generate_random_traffic_with_TRACI_for_begining_for_AI(edges, 200, net)
    
    depart_time = 40
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
    traci.vehicletype.setParameter("rescue", "junction.blocker", "true")
    traci.vehicletype.setParameter("rescue", "jmIgnoreFoeProb", "1")
    #endregion

    result = []
    stop = False
    current_edge_from_list = None
    current_edge_from_list_2 = None
    vehicles_for_first_edge = 0
    num = last_num + 1
    edges_to_manage_traffic = []
    for e in edges:
        edges_to_manage_traffic.append(e)
    while not stop:
        traci.simulationStep()
        if traci.simulation.getTime() == 30:
            """
            vehicles_currently_in_edge = traci.edge.getLastStepVehicleIDs(edges[0])
            average_speed = 0
            for v in vehicles_currently_in_edge:
                average_speed += traci.vehicle.getSpeed(v)
            if len(vehicles_currently_in_edge) != 0:
                average_speed = average_speed/len(vehicles_currently_in_edge)
            vehicles_for_first_edge = round(parameters[0]["c"] + parameters[0]["m0"]*data_for_ML[0][1] + parameters[0]["m1"]*data_for_ML[0][2] + parameters[0]["m2"]*data_for_ML[0][2] + parameters[0]["m3"]*data_for_ML[0][3] + parameters[0]["m4"]*average_speed)
            if vehicles_for_first_edge < 0:
                vehicles_for_first_edge = 0
            vehicles_waiting = []
            waiting = traci.simulation.getLoadedIDList()
            if len(waiting) != 0:
                for w in waiting:
                    if w == "simulation.findRoute":
                        continue
                    route = traci.vehicle.getRoute(w)
                    if route and edges[0] != None and route[0] == edges[0]:
                        vehicles_waiting.append(w)
            if vehicles_for_first_edge < len(vehicles_currently_in_edge) + len(vehicles_waiting):
                substraction = vehicles_for_first_edge - len(vehicles_currently_in_edge) - len(vehicles_waiting)
                for s in range(substraction):
                    if len(vehicles_waiting) != 0:
                        veh_id_to_delete = random.choice(vehicles_waiting)
                        traci.vehicle.remove(veh_id_to_delete)
                        vehicles_waiting.remove(veh_id_to_delete)
                    else:
                        veh_id_to_delete = random.choice(vehicles_currently_in_edge)
                        traci.vehicle.remove(veh_id_to_delete)
                        vehicles_currently_in_edge.remove(veh_id_to_delete)
            elif vehicles_for_first_edge > len(vehicles_currently_in_edge) + len(vehicles_waiting):
                adition = vehicles_for_first_edge - len(vehicles_currently_in_edge) - len(vehicles_waiting)
                for a in range(adition):
                    generate_random_traffic_with_TRACI_for_during_in_next_edge(edges[0], None, edges, 1, 0, net, num, veh_id)
                    num += 1
            """
            num, vehicles_for_first_edge = adjust_the_number_of_vehicles_in_edge(edges[0], edges, net, veh_id, num, parameters, data_for_ML)
            correct = False
            while not correct:
                traci.simulationStep()
                vehicles_currently_in_edge = traci.edge.getLastStepVehicleIDs(edges[0])
                if len(vehicles_currently_in_edge) <= vehicles_for_first_edge + 3 and len(vehicles_currently_in_edge) >= vehicles_for_first_edge - 3:
                    correct = True
                    traci.vehicle.add(
                    vehID=veh_id,
                    routeID=route_id,
                    typeID="rescue",
                    depart=traci.simulation.getTime()+1,
                    departLane="best"
                    )
        if veh_id in traci.vehicle.getIDList():
            edge = traci.vehicle.getRoadID(veh_id)
            x,y = traci.vehicle.getPosition(veh_id)
            lon, lat = net.convertXY2LonLat(x,y)
            time = traci.simulation.getTime()
            result.append([lon,lat,time])
            if edge in edges and edge != current_edge_from_list:
                if current_edge_from_list != None:
                    edges_to_manage_traffic.remove(current_edge_from_list)
                current_edge_from_list = edge
            for e in edges_to_manage_traffic:
                num, vehicles_for_edge = adjust_the_number_of_vehicles_in_edge(e, edges, net, veh_id, num, parameters, data_for_ML)
            
        """
        if traci.simulation.getTime() >= depart_time - 30 and veh_id not in traci.vehicle.getIDList() and traci.simulation.getTime()%5 == 0:
            vehicles_currently_in_edge = traci.edge.getLastStepVehicleIDs(edges[0])
            average_speed = 0
            for v in vehicles_currently_in_edge:
                average_speed += traci.vehicle.getSpeed(v)
            if len(vehicles_currently_in_edge) != 0:
                average_speed = average_speed/len(vehicles_currently_in_edge)
            vehicles_for_first_edge = round(parameters[0]["c"] + parameters[0]["m0"]*data_for_ML[0][1] + parameters[0]["m1"]*data_for_ML[0][2] + parameters[0]["m2"]*data_for_ML[0][2] + parameters[0]["m3"]*data_for_ML[0][3] + parameters[0]["m4"]*average_speed)
            if vehicles_for_first_edge < 0:
                vehicles_for_first_edge = 0

            vehicles_waiting = []
            waiting = traci.simulation.getLoadedIDList()
            if len(waiting) != 0:
                for w in waiting:
                    if w == "simulation.findRoute":
                        continue
                    route = traci.vehicle.getRoute(w)
                    if route and edges[0] != None and route[0] == edges[0]:
                        vehicles_waiting.append(w)
            if vehicles_for_first_edge < len(vehicles_currently_in_edge) + len(vehicles_waiting):
                substraction = vehicles_for_first_edge - len(vehicles_currently_in_edge) - len(vehicles_waiting)
                for s in range(substraction):
                    if len(vehicles_waiting) != 0:
                        veh_id_to_delete = random.choice(vehicles_waiting)
                        traci.vehicle.remove(veh_id_to_delete)
                        vehicles_waiting.remove(veh_id_to_delete)
                    else:
                        veh_id_to_delete = random.choice(vehicles_currently_in_edge)
                        traci.vehicle.remove(veh_id_to_delete)
                        vehicles_currently_in_edge.remove(veh_id_to_delete)
            elif vehicles_for_first_edge > len(vehicles_currently_in_edge) + len(vehicles_waiting):
                adition = vehicles_for_first_edge - len(vehicles_currently_in_edge) - len(vehicles_waiting)
                for a in range(adition):
                    generate_random_traffic_with_TRACI_for_during_in_next_edge(edges[0], None, edges, 1, 0, net, num, veh_id)
                    num += 1
        """
        """
        if veh_id in traci.vehicle.getIDList():
            edge = traci.vehicle.getRoadID(veh_id)
            if edge in edges and edge != current_edge_from_list_2:
                if current_edge_from_list_2 == None:
                    current_edge_from_list_2 = edge
                    edge_entry_time = traci.simulation.getTime()
                    vehicles_in_entrance = traci.edge.getLastStepVehicleNumber(current_edge_from_list_2)
                else:
                    speed_lane = traci.lane.getMaxSpeed(current_edge_from_list_2+"_0")
                    lanes = traci.edge.getLaneNumber(current_edge_from_list_2)
                    length = traci.lane.getLength(current_edge_from_list_2+"_0")
                    current_edge_from_list_2 = edge
                    edge_entry_time = traci.simulation.getTime()
                    vehicles_in_entrance = traci.edge.getLastStepVehicleNumber(current_edge_from_list_2)
            speed = traci.vehicle.getSpeed(veh_id)
            speed_lane = traci.lane.getMaxSpeed(edge+"_0")
            if speed < speed_lane:
                traci.vehicle.setSpeed(veh_id, speed_lane*1.25) 
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
                            traci.vehicle.setSpeed(l, speed_lane)
        """
        if veh_id in traci.simulation.getArrivedIDList():
            stop = True
            traci.close()

    return result

def run_simulation_with_device_and_vehicles_for_data_gathering(edges, initial_traffic, simulation_traffic):
    sumoBinary = sumolib.checkBinary("sumo")
    traci.start([sumoBinary, "-c", "osm.sumocfg"])
    net = sumolib.net.readNet('osm.net.xml')

    # region Ambulance vehicle creation
    veh_id = "ambulance"
    route_id = "ambulance_route"
    depart_time = 100
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
    traci.vehicletype.setParameter("rescue", "junction.blocker", "true")
    traci.vehicletype.setParameter("rescue", "jmIgnoreFoeProb", "1")
    traci.vehicle.add(
        vehID=veh_id,
        routeID=route_id,
        typeID="rescue",
        depart=depart_time,
        departLane="best"
    )

    #endregion
    try:
        vehicles_added_beginning, type1, type2, type3, last_num = generate_random_traffic_with_TRACI_for_begining_for_AI(edges, initial_traffic, net)
    except Exception as e:
        print("Error:", e)
    result = []
    stop = False
    current_edge_from_list = None
    current_edge_from_list_2 = None
    edge_entry_time = 0
    data_for_training = []
    vehicles_in_entrance = 0

    edges_with_emergency_path, edges_without_emergency_path, sequence_of_edges_with_no_emergency_path = find_data_from_ambulance_route(edges)
    lights_to_change = []
    emergency_lanes_to_cancel = []
    allowed = None
    edges_with_no_tls_and_one_lane = []
    edges_with_tls_and_one_lane = []
    edges_with_tls_and_more_than_one_lane = []
    edges_with_no_tls_and_more_than_one_lane = []
    for e in edges:
        allowed = traci.lane.getAllowed(e+"_0")
        thing_to_append = activate_emergency_lane_in_edge(e, edges, net)
        if thing_to_append is not None:
            lights_to_change.append(thing_to_append)
            emergency_lanes_to_cancel.append([thing_to_append[0], e])
            edges_with_tls_and_more_than_one_lane.append(e)
        else:
            edges_with_no_tls_and_more_than_one_lane.append(e)
    for e in edges_without_emergency_path:
        tls = find_if_street_has_traffic_light_for_edge(e)
        if tls:
            edges_with_tls_and_one_lane.append(e)
            previous_edge = edges[edges.index(e) - 1] if edges.index(e) > 0 else None
            current_next_light, next_state, next_idx = get_light_state_for_edge(e, tls)        
            change_traffic_lights_for_whole_edge(tls, "G", next_state, next_idx, previous_edge, e)
            try:
                next_next_edge = get_next_valid_edge(e, edges)
                if next_next_edge is not None:
                    lights_to_change.append([next_next_edge, tls])
            except Exception as e:
                print("Error:", e)
        else:
            edges_with_no_tls_and_one_lane.append(e)

    while not stop:
        traci.simulationStep()
        #This part allows entering vehicles to the sumilation whilst running, that way every X seconds Y vehicles are added to it.
        if traci.simulation.getTime()%10 == 0:
            next_edge = None
            next_next_edge = None
            if veh_id in traci.vehicle.getIDList():
                edge = traci.vehicle.getRoadID(veh_id)
                if edge in edges:
                    current_edge_from_list = edge
                if current_edge_from_list != None:
                    index = edges.index(current_edge_from_list)
                    if index < len(edges) - 1:
                        next_edge = edges[index + 1]
                    if index < len(edges) - 2:
                        next_next_edge = edges[index + 2]
            amount_next_edge = round(simulation_traffic/2)
            amount_next_next_edge = amount_next_edge
            try:
                thing_to_append, type1_2, type2_2, type3_2, last_num = generate_random_traffic_with_TRACI_for_during_in_next_edge(next_edge, next_next_edge, edges, amount_next_edge, amount_next_next_edge, net, last_num + 1, veh_id)
            except Exception as e:
                print("Error:", e)
        if veh_id in traci.vehicle.getIDList():
            edge = traci.vehicle.getRoadID(veh_id)
            allowed_for_this_edge = traci.lane.getAllowed(edge+"_0")
            lane_number = traci.vehicle.getLaneIndex(veh_id)
            if len(allowed_for_this_edge) == 1 and "emergency" in allowed_for_this_edge and lane_number != 0:
                traci.vehicle.changeLane(veh_id, 0, 100)

            if edge in edges and edge != current_edge_from_list_2:
                if current_edge_from_list_2 == None:
                    current_edge_from_list_2 = edge
                    edge_entry_time = traci.simulation.getTime()
                    vehicles_in_entrance = traci.edge.getLastStepVehicleNumber(current_edge_from_list_2)
                else:
                    speed_lane = traci.lane.getMaxSpeed(current_edge_from_list_2+"_0")
                    lanes = traci.edge.getLaneNumber(current_edge_from_list_2)
                    length = traci.lane.getLength(current_edge_from_list_2+"_0")
                    tls = find_if_street_has_traffic_light_for_edge(current_edge_from_list_2)
                    if tls:
                        data_for_training.append([length, lanes, speed_lane, vehicles_in_entrance, traci.simulation.getTime() - edge_entry_time, 0])
                    else:
                        data_for_training.append([length, lanes, speed_lane, vehicles_in_entrance, traci.simulation.getTime() - edge_entry_time, 1])
                    current_edge_from_list_2 = edge
                    edge_entry_time = traci.simulation.getTime()
                    vehicles_in_entrance = traci.edge.getLastStepVehicleNumber(current_edge_from_list_2)
            speed = traci.vehicle.getSpeed(veh_id)
            speed_lane = traci.lane.getMaxSpeed(edge+"_0")
            if speed < speed_lane:
                traci.vehicle.setSpeed(veh_id, speed_lane*1.25) 
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
                            traci.vehicle.setSpeed(l, speed_lane)
        if veh_id in traci.simulation.getArrivedIDList():
            stop = True
    traci.close()

    return data_for_training

def run_simulation_with_device_activated_at_specific_time_and_vehicles_for_data_gathering(edges, initial_traffic, simulation_traffic, edges_with_coords):
    
    sumoBinary = sumolib.checkBinary("sumo-gui")
    traci.start([sumoBinary, "-c", "osm.sumocfg"])
    net = sumolib.net.readNet('osm.net.xml')
    depart_time = 200
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
    traci.vehicletype.setParameter("rescue", "junction.blocker", "true")
    traci.vehicletype.setParameter("rescue", "jmIgnoreFoeProb", "1")
    traci.vehicle.add(
        vehID=veh_id,
        routeID=route_id,
        typeID="rescue",
        depart=depart_time,
        departLane="best"
    )

    #endregion
    try:
        vehicles_added_beginning, type1, type2, type3, last_num = generate_random_traffic_with_TRACI_for_begining_for_AI(edges, initial_traffic, net)
    except Exception as e:
        print("Error:", e)
    stop = False
    current_edge_from_list = None
    current_edge_from_list_2 = None
    edge_entry_time = 0
    data_for_training = []
    vehicles_in_entrance = 0
    edges_to_see_if_are_empty = []
    """
    edges_with_emergency_path, edges_without_emergency_path, sequence_of_edges_with_no_emergency_path = find_data_from_ambulance_route(edges)
    lights_to_change = []
    emergency_lanes_to_cancel = []
    allowed = None
    edges_with_no_tls_and_one_lane = []
    edges_with_tls_and_one_lane = []
    edges_with_tls_and_more_than_one_lane = []
    edges_with_no_tls_and_more_than_one_lane = []
    for e in edges:
        allowed = traci.lane.getAllowed(e+"_0")
        thing_to_append = activate_emergency_lane_in_edge(e, edges, net)
        if thing_to_append is not None:
            lights_to_change.append(thing_to_append)
            emergency_lanes_to_cancel.append([thing_to_append[0], e])
            edges_with_tls_and_more_than_one_lane.append(e)
        else:
            edges_with_no_tls_and_more_than_one_lane.append(e)
    for e in edges_without_emergency_path:
        tls = find_if_street_has_traffic_light_for_edge(e)
        if tls:
            edges_with_tls_and_one_lane.append(e)
            previous_edge = edges[edges.index(e) - 1] if edges.index(e) > 0 else None
            current_next_light, next_state, next_idx = get_light_state_for_edge(e, tls)        
            change_traffic_lights_for_whole_edge(tls, "G", next_state, next_idx, previous_edge, e)
            try:
                next_next_edge = get_next_valid_edge(e, edges)
                if next_next_edge is not None:
                    lights_to_change.append([next_next_edge, tls])
            except Exception as e:
                print("Error:", e)
        else:
            edges_with_no_tls_and_one_lane.append(e)
    """
    edges_objects = {}
    edges_remaining = []
    k = 0
    for e in edges_with_coords:
        edges_remaining.append(e)
    while not stop:
        traci.simulationStep()
        #This part allows entering vehicles to the sumilation whilst running, that way every X seconds Y vehicles are added to it.
        if traci.simulation.getTime()%10 == 0:
            try:
                last_num = generate_random_traffic_with_TRACI_for_during_in_random_edge_from_edges(edges, simulation_traffic, net, last_num + 1, veh_id)
            except Exception as e:
                print("Error:", e)  
            """
            next_edge = None
            next_next_edge = None
            if veh_id in traci.vehicle.getIDList():
                edge = traci.vehicle.getRoadID(veh_id)
                if edge in edges:
                    current_edge_from_list = edge
                if current_edge_from_list != None:
                    index = edges.index(current_edge_from_list)
                    if index < len(edges) - 1:
                        next_edge = edges[index + 1]
                    if index < len(edges) - 2:
                        next_next_edge = edges[index + 2]
            amount_next_edge = round(simulation_traffic/2)
            amount_next_next_edge = amount_next_edge
            thing_to_append, type1_2, type2_2, type3_2, last_num = generate_random_traffic_with_TRACI_for_during_in_next_edge(next_edge, next_next_edge, edges, amount_next_edge, amount_next_next_edge, net, last_num + 1, veh_id)
            """
        if traci.simulation.getTime() == depart_time/2:
            k = 0
            while k < 4 if len(edges) >= 4 else len(edges):
                activate_emergency_lane_in_edge(edges[k], edges, net)
                for e in edges_remaining:
                    if e[0] == edges[k]:
                        edges_remaining.remove(e)
                entry_time = traci.simulation.getTime()
                lanes = traci.edge.getLaneNumber(edges[k])
                length = traci.lane.getLength(edges[k]+"_0")
                max_speed = traci.lane.getMaxSpeed(edges[k]+"_0")
                vehicles_in_entrance = traci.edge.getLastStepVehicleNumber(edges[k])
                exits = net.getEdge(edges[k]).getIncoming()
                id_s = []
                density_exit = 0
                for e in exits:
                    id_s.append(e.getID())
                for id in id_s:
                    lanes_exit = traci.edge.getLaneNumber(id)
                    length_exit = traci.lane.getLength(id+"_0")
                    vehicles_in_entrance_exit = traci.edge.getLastStepVehicleNumber(id)
                    density_exit += vehicles_in_entrance_exit/(length_exit * lanes_exit)
                density_exit = density_exit/len(id_s) if len(id_s) != 0 else 0
                edge_obj = EdgeClass(edges[k], lanes, length, max_speed, vehicles_in_entrance,
                                    len(id_s), density_exit, entry_time, 0)
                edges_objects[f"edge_{k}"] = edge_obj
                edges_to_see_if_are_empty.append([f"edge_{k}", edges[k]])
                k += 1
        
        if edges_to_see_if_are_empty != []:
            veh_to_remove = []
            for e in edges_to_see_if_are_empty:
                vehicles_in_lane = traci.lane.getLastStepVehicleNumber(e[1]+"_0")
                if vehicles_in_lane == 0:
                    edges_objects[e[0]].end_time = traci.simulation.getTime()
                    veh_to_remove.append(e)
            for v in veh_to_remove:
                edges_to_see_if_are_empty.remove(v)
        
        if veh_id in traci.vehicle.getIDList():

            x,y = traci.vehicle.getPosition(veh_id)
            lon, lat = net.convertXY2LonLat(x,y)
            edges_to_eliminate = []
            for e in edges_remaining:
                distance = geodesic((lat, lon), (e[1][1], e[1][0])).meters
                if distance <= 500:
                    edges_to_eliminate.append(e)
                    activate_emergency_lane_in_edge(e[0], edges, net)
                    entry_time = traci.simulation.getTime()
                    lanes = traci.edge.getLaneNumber(edges[k])
                    length = traci.lane.getLength(edges[k]+"_0")
                    max_speed = traci.lane.getMaxSpeed(edges[k]+"_0")
                    vehicles_in_entrance = traci.edge.getLastStepVehicleNumber(edges[k])
                    exits = net.getEdge(edges[k]).getIncoming()
                    id_s = []
                    density_exit = 0
                    for e in exits:
                        id_s.append(e.getID())
                    for id in id_s:
                        lanes_exit = traci.edge.getLaneNumber(id)
                        length_exit = traci.lane.getLength(id+"_0")
                        vehicles_in_entrance_exit = traci.edge.getLastStepVehicleNumber(id)
                        density_exit += vehicles_in_entrance_exit/(length_exit * lanes_exit)
                    density_exit = density_exit/len(id_s) if len(id_s) != 0 else 0
                    edge_obj = EdgeClass(edges[k], lanes, length, max_speed, vehicles_in_entrance,
                                        len(id_s), density_exit, entry_time, 0)
                    edges_objects[f"edge_{k}"] = edge_obj
                    edges_to_see_if_are_empty.append([f"edge_{k}", edges[k]])
                    k += 1
            for e in edges_to_eliminate:
                edges_remaining.remove(e)
            edge = traci.vehicle.getRoadID(veh_id)
            allowed_for_this_edge = traci.lane.getAllowed(edge+"_0")
            lane_number = traci.vehicle.getLaneIndex(veh_id)
            if len(allowed_for_this_edge) == 1 and "emergency" in allowed_for_this_edge and lane_number != 0:
                traci.vehicle.changeLane(veh_id, 0, 100)
            """
            if edge in edges and edge != current_edge_from_list_2:
                if current_edge_from_list_2 == None:
                    current_edge_from_list_2 = edge
                    edge_entry_time = traci.simulation.getTime()
                    vehicles_in_entrance = traci.edge.getLastStepVehicleNumber(current_edge_from_list_2)
                else:
                    speed_lane = traci.lane.getMaxSpeed(current_edge_from_list_2+"_0")
                    lanes = traci.edge.getLaneNumber(current_edge_from_list_2)
                    length = traci.lane.getLength(current_edge_from_list_2+"_0")
                    tls = find_if_street_has_traffic_light_for_edge(current_edge_from_list_2)
                    if tls:
                        data_for_training.append([length, lanes, speed_lane, vehicles_in_entrance, traci.simulation.getTime() - edge_entry_time, 0])
                    else:
                        data_for_training.append([length, lanes, speed_lane, vehicles_in_entrance, traci.simulation.getTime() - edge_entry_time, 1])
                    current_edge_from_list_2 = edge
                    edge_entry_time = traci.simulation.getTime()
                    vehicles_in_entrance = traci.edge.getLastStepVehicleNumber(current_edge_from_list_2)
            """
            speed = traci.vehicle.getSpeed(veh_id)
            speed_lane = traci.lane.getMaxSpeed(edge+"_0")
            if speed < speed_lane:
                traci.vehicle.setSpeed(veh_id, speed_lane*1.25) 
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
                            traci.vehicle.setSpeed(l, speed_lane)
        if veh_id in traci.simulation.getArrivedIDList():
            stop = True
    traci.close()
    result = []
    for e in edges_objects.values():
        result.append(e.get_data())
    return result

def adjust_the_number_of_vehicles_in_edge(edge_id, edges, net, veh_id, num, parameters, data_for_ML):
    total_vehicles = traci.edge.getLastStepVehicleIDs(edge_id)
    amount_of_vehicles = []
    for v in total_vehicles:
        amount_of_vehicles.append(v)
    vehicles_waiting = []
    waiting = traci.simulation.getLoadedIDList()
    if len(waiting) != 0:
        for w in waiting:
            if w == "simulation.findRoute":
                continue
            try:
                route = traci.vehicle.getRoute(w)
                if route and edges[0] != None and route[0] == edges[0]:
                    vehicles_waiting.append(w)
            except:
                continue
    average_speed = 0
    for v in amount_of_vehicles:
        average_speed += traci.vehicle.getSpeed(v)
    if len(amount_of_vehicles) != 0:
        average_speed = average_speed/len(amount_of_vehicles)
    data = []
    for d in data_for_ML:
        if d[0] == edge_id:
            data = d
            break
    vehicles_for_edge = 0
    if data != []:
        vehicles_for_edge = round(parameters[0]["c"] + parameters[0]["m0"]*data[1] + parameters[0]["m1"]*data[2] + parameters[0]["m2"]*data[2] + parameters[0]["m3"]*data[3] + parameters[0]["m4"]*average_speed)
        if vehicles_for_edge < 0:
            vehicles_for_edge = 0
        if vehicles_for_edge < len(amount_of_vehicles) + len(vehicles_waiting):
            substraction = len(amount_of_vehicles) + len(vehicles_waiting) - vehicles_for_edge
            for s in range(substraction):
                if len(vehicles_waiting) != 0 and not (len(vehicles_waiting) == 1 and veh_id in vehicles_waiting):
                    veh_id_to_delete = random.choice(vehicles_waiting)
                    while veh_id_to_delete == veh_id:
                        veh_id_to_delete = random.choice(vehicles_waiting)
                    traci.vehicle.remove(veh_id_to_delete)
                    vehicles_waiting.remove(veh_id_to_delete)
                elif len(amount_of_vehicles) != 0 and not (len(amount_of_vehicles) == 1 and veh_id in amount_of_vehicles):
                    veh_id_to_delete = random.choice(amount_of_vehicles)
                    while veh_id_to_delete == veh_id:
                        veh_id_to_delete = random.choice(amount_of_vehicles)
                    traci.vehicle.remove(veh_id_to_delete)
                    amount_of_vehicles.remove(veh_id_to_delete)
        elif vehicles_for_edge > len(amount_of_vehicles) + len(vehicles_waiting):
            adition = vehicles_for_edge - len(amount_of_vehicles) - len(vehicles_waiting)
            for a in range(adition):
                generate_random_traffic_with_TRACI_for_during_in_next_edge(edge_id, None, edges, 1, 0, net, num, veh_id)
                num += 1
    return num, vehicles_for_edge