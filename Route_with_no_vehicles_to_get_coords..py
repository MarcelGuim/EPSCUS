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


def run_simulation_with_no_vehicles_to_get_coords(edges):
    sumoBinary = sumolib.checkBinary("sumo-gui")
    traci.start([sumoBinary, "-c", "osm.sumocfg"])
    net = sumolib.net.readNet('osm.net.xml')

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
        depart=0,
        departLane="best"
    )
    #endregion
    result = []
    stop = False
    while not stop:
        traci.simulationStep()            
        if veh_id in traci.vehicle.getIDList(): 
            x,y = traci.vehicle.getPosition(veh_id)
            lon, lat = net.convertXY2LonLat(x,y)
            result.append([lon,lat])
        if veh_id in traci.simulation.getArrivedIDList():
            stop = True
    traci.close()
    return result