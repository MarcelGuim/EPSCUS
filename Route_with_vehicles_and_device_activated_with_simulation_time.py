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
from trafficGenerator import congestion_analyzer, get_congestion_for_edge, generate_random_route_starting_at_next_edge, generate_random_route_starting_at_specific_edge
from datetime import datetime, timedelta, timezone
from importRoutes import escriure_ruta, convertir_coordenades_a_edges
from dispositiu import find_if_there_is_emergency_lane, find_if_street_has_traffic_light, get_light_state, change_traffic_light_for_one_lane, change_traffic_lights_for_whole_edge, get_light_state_for_edge, create_emergency_lane, find_if_street_has_traffic_light_for_edge, activate_emergency_lane_in_edge
from trafficGenerator import generate_random_traffic_with_TRACI_for_begining, generate_random_traffic_with_TRACI_for_during, congestion_analyzer, get_congestion_for_edge, generate_random_route_starting_at_next_edge, generate_random_route_starting_at_specific_edge


def run_simulation_with_vehicles_and_device_and_given_traffic(edges, vehicles_added_beginning, vehicles_added_during):
    total_time = None
    result = None
    edges_with_no_tls_and_one_lane = None
    edges_with_tls_and_one_lane = None
    edges_with_tls_and_more_than_one_lane = None
    edges_with_no_tls_and_more_than_one_lane = None
    set_speed = []
    sumoBinary = sumolib.checkBinary("sumo")
    traci.start([sumoBinary, "-c", "osm.sumocfg"])
    net = sumolib.net.readNet('osm.net.xml')
    edges_with_emergency_path, edges_without_emergency_path, sequence_of_edges_with_no_emergency_path = find_data_from_ambulance_route(edges)
    lights_to_change = []
    emergency_lanes_to_cancel = []
    allowed = None
    edges_with_no_tls_and_one_lane = []
    edges_with_tls_and_one_lane = []
    edges_with_tls_and_more_than_one_lane = []
    edges_with_no_tls_and_more_than_one_lane = []
    for e in edges_with_emergency_path:
        allowed = traci.lane.getAllowed(e+"_0")
        thing_to_append = activate_emergency_lane_in_edge(e, edges, net)
        if thing_to_append is not None:
            lights_to_change.append(thing_to_append)
            emergency_lanes_to_cancel.append([thing_to_append[0], e])
            edges_with_tls_and_more_than_one_lane.append(e)
        else:
            edges_with_no_tls_and_more_than_one_lane.append(e)
    for e in edges_without_emergency_path:
        allowed = traci.lane.getAllowed(e+"_0")
        thing_to_append = activate_emergency_lane_in_edge(e, edges, net)
        if thing_to_append is not None:
            lights_to_change.append(thing_to_append)
            emergency_lanes_to_cancel.append([thing_to_append[0], e])
            edges_with_tls_and_one_lane.append(e)
        else:
            edges_with_no_tls_and_one_lane.append(e)
    
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
    traci.vehicletype.setParameter("rescue", "lcKeepRight", "1")
    traci.vehicletype.setParameter("rescue", "lcAssertive", "1")
    traci.vehicletype.setParameter("rescue", "lcCooperative", "0")
    traci.vehicletype.setParameter("rescue", "minGapLat", "0")
    traci.vehicletype.setParameter("rescue", "minGap", "0.1")
    traci.vehicletype.setParameter("rescue", "junction.blocker", "true")
    traci.vehicletype.setParameter("rescue", "jmIgnoreFoeProb", "1")
    traci.vehicletype.setParameter("rescue", "carFollowModel", "Krauss")
    traci.vehicletype.setParameter("rescue", "tau", "0.1")
    traci.vehicle.add(
        vehID=veh_id,
        routeID=route_id,
        typeID="rescue",
        depart=200,
        departLane="best"
    )

    #endregion
    
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

    i = 0
    for v in vehicles_added_beginning:
        try:
            traci.route.add(v[0], v[1])
            traci.vehicle.add(v[0], routeID=v[0], departLane="allowed", typeID=v[2], depart=v[3])
        except:
            print(f"Error adding vehicle: {v[0]}")
        i += 1
    vehciles_to_add_during_ambulance = []
    for v in vehicles_added_during:
        if v[-1] == 0 and v[-2] == 0:
            try:
                traci.route.add(v[0], v[1])
                traci.vehicle.add(v[0], routeID=v[0], departLane="allowed", typeID=v[2], depart=v[3])
            except:
                print(f"Error adding vehicle: {v[0]}")
        else:
            vehciles_to_add_during_ambulance.append(v) 
    result = []
    stop = False
    previous_edge = None
    current_edge = None
    try:
        while not stop:
            traci.simulationStep()
            if veh_id in traci.vehicle.getIDList(): 

                edge = traci.vehicle.getRoadID(veh_id)
                next_edge = None
                if edge in edges:
                    current_edge = edge
                    if edges.index(current_edge) != len(edges) - 1:
                        next_edge = edges[edges.index(current_edge) + 1]            
                waiting = traci.simulation.getLoadedIDList()
                if len(waiting) != 0:
                    for w in waiting:
                        if w == "simulation.findRoute":
                            continue
                        route = traci.vehicle.getRoute(w)
                        if route and next_edge != None and route[0] == next_edge:
                            traci.vehicle.remove(w)

                if len(set_speed) != 0 and set_speed[0] == edge:
                    traci.vehicle.setSpeedMode("ambulance", 23) 
                    set_speed = []
                edge = traci.vehicle.getRoadID(veh_id)
                if edge in edges:
                    current_edge = edge
                allowed_for_this_edge = traci.lane.getAllowed(edge+"_0")
                lane_number = traci.vehicle.getLaneIndex(veh_id)
                if len(allowed_for_this_edge) == 1 and "emergency" in allowed_for_this_edge and lane_number != 0:
                    traci.vehicle.changeLane(veh_id, 0, 100)
                x,y = traci.vehicle.getPosition(veh_id)
                lon, lat = net.convertXY2LonLat(x,y)

                vehicles_to_delete = []
                for v in vehciles_to_add_during_ambulance:
                    if geodesic((v[-2], v[-1]), (lat, lon)).meters < 5:
                        vehicles_to_delete.append(v)
                        try:
                            traci.route.add(v[0], v[1])
                            traci.vehicle.add(v[0], routeID=v[0], departLane="allowed", typeID=v[2], depart=traci.simulation.getTime())
                        except:
                            print(f"Error, veh: {v[0]} can't be added to the simulation")
                    else:
                        break

                for v in vehicles_to_delete:
                    vehciles_to_add_during_ambulance.remove(v)

                time = traci.simulation.getTime() 
                speed = traci.vehicle.getSpeed(veh_id)
                speed_lane = traci.lane.getMaxSpeed(edge+"_0")
                if speed < 0.5:
                    traci.vehicle.setSpeedMode(veh_id, 0)
                    next_next_edge = get_next_valid_edge(edge, edges)
                    if next_next_edge is not None:
                        set_speed.append(next_next_edge)
                    leader = traci.vehicle.getLeader(veh_id, dist=100.0)
                    if leader is None:
                        traci.vehicle.setSpeed(veh_id, speed_lane*1.25)
                    can_right = traci.vehicle.couldChangeLane(veh_id, -1)
                    if can_right:
                        traci.vehicle.changeLaneRelative(veh_id, -1,50)
                    can_left = traci.vehicle.couldChangeLane(veh_id, 1, 100)
                    if can_left and not can_right:
                        traci.vehicle.changeLaneRelative(veh_id, 1,50)
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
                            traci.vehicle.setSpeed(l, speed_lane)                   
            
                for l in lights_to_change:
                    e = l[0]
                    tls_s = l[1]
                    if edge == e:
                        for tls in tls_s:
                            traci.trafficlight.setProgram(tls, "0")
                    
                for l in emergency_lanes_to_cancel:
                    e = l[0]
                    deactivated_edge = l[1]
                    if edge == e:
                        traci.lane.setAllowed(str(deactivated_edge) + "_0", allowed)
            
            if veh_id in traci.simulation.getArrivedIDList():
                with open("result_with_traffic_and_device.json", "w") as f:
                    json.dump(result, f)
                stop = True
    except traci.exceptions.FatalTraCIError:
        print("error, closing and restarting sim")
    traci.close()
    try:
        total_time = result[-1][2] - result[0][2]
        print(f"Total time for simulation with vehicles but no device activation is: {total_time} seconds")
    except:
        total_time = 0

    return total_time, result, edges_with_no_tls_and_one_lane, edges_with_tls_and_one_lane, edges_with_tls_and_more_than_one_lane, edges_with_no_tls_and_more_than_one_lane

def run_simulation_with_vehicles_and_device_random_traffic(edges, initial_amount, simulation_amount, edges_with_coords):
    total_time = None
    result = None
    edges_with_no_tls_and_one_lane = None
    edges_with_tls_and_one_lane = None
    edges_with_tls_and_more_than_one_lane = None
    edges_with_no_tls_and_more_than_one_lane = None
    
    sumoBinary = sumolib.checkBinary("sumo-gui")
    traci.start([sumoBinary, "-c", "osm.sumocfg"])
    net = sumolib.net.readNet('osm.net.xml')
    edges_with_emergency_path, edges_without_emergency_path, sequence_of_edges_with_no_emergency_path = find_data_from_ambulance_route(edges)
    lights_to_change = []
    emergency_lanes_to_cancel = []
    allowed = None
    
    k = 0
    while k < 4:
        allowed = traci.lane.getAllowed(edges[k]+"_0")
        thing_to_append = activate_emergency_lane_in_edge(edges[k], edges, net)
        if thing_to_append is not None:
            lights_to_change.append(thing_to_append)
            emergency_lanes_to_cancel.append([thing_to_append[0], edges[k]])
        for ed in edges_with_coords:
            if ed[0] == edges[k]:
                edges_with_coords.remove(ed)
                break
        k += 1
        
    """
    for e in edges_with_emergency_path:
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
    traci.vehicletype.setParameter("rescue", "lcKeepRight", "1")
    traci.vehicletype.setParameter("rescue", "lcAssertive", "1")
    traci.vehicletype.setParameter("rescue", "lcCooperative", "0")
    traci.vehicletype.setParameter("rescue", "minGapLat", "0")
    traci.vehicletype.setParameter("rescue", "minGap", "0.1")
    traci.vehicletype.setParameter("rescue", "junction.blocker", "true")
    traci.vehicletype.setParameter("rescue", "jmIgnoreFoeProb", "1")
    traci.vehicletype.setParameter("rescue", "carFollowModel", "Krauss")
    traci.vehicletype.setParameter("rescue", "tau", "0.1")
    traci.vehicle.add(
        vehID=veh_id,
        routeID=route_id,
        typeID="rescue",
        depart=100,
        departLane="best"
    )

    #endregion
    
    vehicles_added, type1, type2, type3 = generate_random_traffic_with_TRACI_for_begining(edges, initial_amount, net)

    result = []
    stop = False
    previous_edge = None
    num = 0
    while not stop:
        traci.simulationStep()

        if traci.simulation.getTime()%50 == 0:
          next_edge = None
          next_next_edge = None
          if veh_id in traci.vehicle.getIDList():
              edge = traci.vehicle.getRoadID(veh_id)
              if edge in edges:
                  index = edges.index(edge)
                  if index < len(edges) - 1:
                      next_edge = edges[index + 1]
                  if index < len(edges) - 2:
                      next_next_edge = edges[index + 2]
          thing_to_append, type1_2, type2_2, type3_2 = generate_random_traffic_with_TRACI_for_during(next_edge, next_next_edge, edges, simulation_amount, net, initial_amount + num*simulation_amount, veh_id)
          type1 += type1_2
          type2 += type2_2
          type3 += type3_2
          for t in thing_to_append:
            vehicles_added.append(t)
          num += 1

        if veh_id in traci.vehicle.getIDList():
            edge = traci.vehicle.getRoadID(veh_id)
            allowed_for_this_edge = traci.lane.getAllowed(edge+"_0")
            lane_number = traci.vehicle.getLaneIndex(veh_id)
            if len(allowed_for_this_edge) == 1 and "emergency" in allowed_for_this_edge and lane_number != 0:
                traci.vehicle.changeLane(veh_id, 0, 100)
            x,y = traci.vehicle.getPosition(veh_id)
            lon, lat = net.convertXY2LonLat(x,y)
            edges_to_create_emergency_lane = []
            for s in edges_with_coords:
                distance = geodesic((lat, lon), (s[1][1], s[1][0])).meters
                if distance < 150:
                    edges_to_create_emergency_lane.append(s[0])
            if len(edges_to_create_emergency_lane) != 0:
                for street in edges_to_create_emergency_lane:
                    allowed = traci.lane.getAllowed(street+"_0")
                    thing_to_append = activate_emergency_lane_in_edge(street, edges, net)
                    if thing_to_append is not None:
                        lights_to_change.append(thing_to_append)
                        emergency_lanes_to_cancel.append([thing_to_append[0], street])
                    for ed in edges_with_coords:
                        if ed[0] == street:
                            edges_with_coords.remove(ed)
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
                        traci.vehicle.setSpeed(l, speed + (1 / 1))                   
        
            for l in lights_to_change:
                e = l[0]
                tls_s = l[1]
                if edge == e:
                    for tls in tls_s: 
                        traci.trafficlight.setProgram(tls, "0")
                
            for l in emergency_lanes_to_cancel:
                e = l[0]
                deactivated_edge = l[1]
                if edge == e:
                    traci.lane.setAllowed(str(deactivated_edge) + "_0", allowed)
        
        if veh_id in traci.simulation.getArrivedIDList():
            with open("result_with_traffic_and_device.json", "w") as f:
                json.dump(result, f)
            stop = True
    traci.close()

    total_time = result[-1][2] - result[0][2]
    print(f"Total time for simulation with vehicles but and device activation is: {total_time} seconds")

    return total_time, result, edges_with_no_tls_and_one_lane, edges_with_tls_and_one_lane, edges_with_tls_and_more_than_one_lane, edges_with_no_tls_and_more_than_one_lane, type1, type2, type3

