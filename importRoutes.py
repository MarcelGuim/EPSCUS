import csv
import traci, math
import traci.constants as tc
import json
import xml.etree.ElementTree as ET
from pyproj import Proj, Transformer
import sumolib
from shapely.geometry import LineString, Point
from routePreparator import resample_route, mostrar_ruta_en_mapa, downsample_route
from geopy.distance import geodesic
import random

EPS = 0.5

def carregar_coordenades(path_json):
    coordenades = []
    with open(path_json) as jsonfile:
        data = json.load(jsonfile)
        coords = data.get('geometry').get('coordinates', [])
    return coords

def calcular_angle(v1, v2):
    dot = v1[0]*v2[0] + v1[1]*v2[1]
    mag1 = math.hypot(*v1)
    mag2 = math.hypot(*v2)
    if mag1 == 0 or mag2 == 0:
        return math.pi
    cos_angle = dot / (mag1 * mag2)
    return math.acos(max(-1.0, min(1.0, cos_angle)))

def convertir_coordenades_a_edges(coordenades, net):
    edges = []
    edgesWithCoords = []
    i = 0
    origin_found = False
    while not origin_found and i < len(coordenades) - 1:
        lon1, lat1 = coordenades[i]
        x1, y1 = net.convertLonLat2XY(lon1, lat1)
        origin = traci.simulation.convertRoad(x1, y1)
        if isinstance(origin, tuple):
            origin = origin[0]
        if not origin.startswith(":") and "#" in origin:
            origin_found = True
            edges.append(origin)
            edgesWithCoords.append([origin, [lon1,lat1]])
        i += 1
    destination_found = False
    destination = None
    while not destination_found and i < len(coordenades) - 1:
        lon1, lat1 = coordenades[i]
        x1, y1 = net.convertLonLat2XY(lon1, lat1)
        destination = traci.simulation.convertRoad(x1, y1)
        if isinstance(destination, tuple):
            destination = destination[0]
        if not destination.startswith(":") and destination != origin:
            destination_found = True
        i += 1
        if destination_found and origin_found:
            route = traci.simulation.findRoute(origin, destination)
            if route is None or len(route.edges) == 0:
                destination_found = False
            else:
                first_edge = route.edges[0]
                reverse_first_edge = "-" + edges[-1] if not edges[-1].startswith("-") else edges[-1][1:]
                if first_edge == reverse_first_edge:
                    route = None
                    destination_found = False    
                else:
                    for edge in route.edges:
                        if edge not in edges and not edge.startswith(":"):
                            edges.append(edge)
                            edgesWithCoords.append([edge, [lon1, lat1]])
    while i < len(coordenades) - 1:
        destination_found = False
        destination = None
        while not destination_found and i < len(coordenades) - 1:
            lon1, lat1 = coordenades[i]
            x1, y1 = net.convertLonLat2XY(lon1, lat1)
            destination = traci.simulation.convertRoad(x1, y1)
            if isinstance(destination, tuple):
                destination = destination[0]
            if destination.startswith(":") or destination == origin:
                i += 1
                continue
            lon2, lat2 = coordenades[i + 1]
            x2, y2 = net.convertLonLat2XY(lon2, lat2)
            shape = net.getEdge(destination).getShape()
            if len(shape) >= 2:
                edge_vector = (shape[-1][0] - shape[0][0], shape[-1][1] - shape[0][1])
                move_vector = (x2 - x1, y2 - y1)
                angle = calcular_angle(edge_vector, move_vector)
                if angle < math.pi / 3:
                    destination_found = True
                if i == len(coordenades) - 2:
                    destination_found = True
            i += 1
            if destination_found:
                route = traci.simulation.findRoute(edges[-1], destination)
                if route is None or len(route.edges) == 0:
                        destination_found = False
                else:
                    first_edge = route.edges[0]
                    reverse_first_edge = "-" + edges[-1] if not edges[-1].startswith("-") else edges[-1][1:]
                    if edges[-1] == reverse_first_edge:
                        route = None
                        destination_found = False
                        continue
                    reverse_first_edge = None
                    for edge in route.edges:
                        if edge == reverse_first_edge:
                            route = None
                            destination_found = False
                            continue
                        reverse_first_edge = "-" + edge if not edge.startswith("-") else edge[1:] 
                    if route is not None:
                        for edge in route.edges:
                            if edge not in edges and not edge.startswith(":"):
                                edges.append(edge)
                                edgesWithCoords.append([edge, [lon1, lat1]])
    if len(edges) > 6:
        first_e = edges[0]
        reverse_first_edge = "-" + first_e if not first_e.startswith("-") else first_e[1:] 
        second_e = edges[1]
        reverse_second_edge = "-" + second_e if not second_e.startswith("-") else second_e[1:] 
        third_e = edges[2]
        reverse_third_edge = "-" + third_e if not third_e.startswith("-") else third_e[1:]
        fourth_e = edges[3]
        reverse_ffourth_edge = "-" + fourth_e if not fourth_e.startswith("-") else fourth_e[1:]
        fifth_e = edges[4]
        reverse_fifth_edge = "-" + fifth_e if not fifth_e.startswith("-") else fifth_e[1:]
        sixth_e = edges[5]
        reverse_sixth_edge = "-" + sixth_e if not sixth_e.startswith("-") else sixth_e[1:]
        reverses = []
        reverses.append(reverse_first_edge)
        reverses.append(reverse_second_edge)
        reverses.append(reverse_third_edge)
        reverses.append(reverse_ffourth_edge)
        reverses.append(reverse_fifth_edge)
        reverses.append(reverse_sixth_edge)
        if first_e in reverses:
            edges.remove(first_e)
        if second_e in reverses:
            edges.remove(second_e)
        if third_e in reverses:
            edges.remove(third_e)
    return edges, edgesWithCoords

def get_route(lat1, lon1, lat2, lon2, net):
    try:
        x1, y1 = net.convertLonLat2XY(lon1, lat1)
        x2, y2 = net.convertLonLat2XY(lon2, lat2)
        origin = safe_convertRoad(x1, y1, net)
        destination = safe_convertRoad(x2, y2, net)
        if isinstance(origin, tuple):
            origin = origin[0]
        if isinstance(destination, tuple):
            destination = destination[0]
        route = traci.simulation.findRoute(origin, destination)
        return route
    except traci.TraCIException:
        return None

def safe_convertRoad(x, y, net):
    result = traci.simulation.convertRoad(x, y)
    if isinstance(result, tuple):
        edge_id = result[0]
    else:
        edge_id = result
    if not edge_id.startswith(":"):
        return edge_id
    incoming = net.getEdge(edge_id).getIncoming()
    outgoing = net.getEdge(edge_id).getOutgoing()
    for edge in incoming + outgoing:
        if not edge.getID().startswith(":"):
            return edge.getID()
    return edge_id

def escriure_ruta(edges, sortida):
    with open(sortida, "w") as f:
        f.write('<routes>\n')
        f.write('    <vType id="rescue" latAlignment="arbitrary" sigma="0" vClass="emergency" speedFactor="1.5" guiShape="emergency" maxSpeed="50" jmIgnoreFoeProb="1" jmIgnoreKeepClearTime="1" jmDriveRedSpeed="2.77" impatience="1.0" lcPushy="1" lcImpatience="1" lcTimeToImpatience="0" lcOpposite="1" lcOvertakeRight="1" lcStrategic="1" lcSpeedGain="1" minGapLat="0.25" minGap="0.5">\n')
        f.write('         <param key="has.bluelight.device" value="true"/>\n')
        f.write('    </vType>\n')
        f.write(f'    <route id="ambulance_route" edges="{" ".join(edges)}"/>\n')
        f.write(f'    <vehicle id="ambulance" type="rescue" route="ambulance_route" depart="100" departLane="best"/>\n')
        f.write('</routes>\n')

def escriure_ruta_automatica(route, sortida):
    with open(sortida, "w") as f:
        f.write('<routes>\n')
        f.write('    <vType id="rescue" latAlignment="arbitrary" sigma="0" vClass="emergency" speedFactor="1.5" guiShape="emergency" maxSpeed="50" jmIgnoreFoeProb="1" jmIgnoreKeepClearTime="1" jmDriveRedSpeed="2.77" impatience="1.0" lcPushy="1" lcImpatience="1" lcTimeToImpatience="0" lcOpposite="1" lcOvertakeRight="1" lcStrategic="1" lcSpeedGain="1" minGapLat="0.25" minGap="0.5">\n')
        f.write('         <param key="has.bluelight.device" value="true"/>\n')
        f.write('    </vType>\n')
        f.write(f'    <route id="ambulance_route" edges="{" ".join(route.edges)}"/>\n')
        f.write(f'    <vehicle id="ambulance" type="rescue" route="ambulance_route" depart="100"/>\n')
        f.write('</routes>\n')

def processar_route_automatica(path_json, rou_output):
    try:
        traci.start(["sumo", "-c", "osm.sumocfg"])
        net = sumolib.net.readNet('osm.net.xml')
        coordenades = carregar_coordenades(path_json)
        route = get_route(coordenades[0][1], coordenades[0][0], coordenades[-1][1], coordenades[-1][0], net)
        print("Ruta generada:", route.edges)
        traci.close()
        escriure_ruta_automatica(route, rou_output)
        print("Ruta generada:", route.edges)
    except Exception as e:
        print("Error:", e)

def processar_route_amb_coords(path_json, rou_output):
    try:
        traci.start(["sumo-gui", "-c", "osm.sumocfg"])
        net = sumolib.net.readNet('osm.net.xml')
        coordenades = carregar_coordenades(path_json)
        #resampled_coords = resample_route(coordenades, max_distance_m=1)
        downsampled_coords = downsample_route(coordenades, min_distance_m=250)
        mostrar_ruta_en_mapa(downsampled_coords, "downsampled.html")
        mostrar_ruta_en_mapa(coordenades, "original.html")
        edges, edgesWithCoords = convertir_coordenades_a_edges(coordenades, net)
        traci.close()
        if edges is None:
            print("No s'ha pogut generar la ruta.")
            return
        escriure_ruta(edges, rou_output)
    except Exception as e:
        print("Error:", e)

def generate_random_route(total_edges, net):
    result = []
    valid = False
    valid_route = False
    while not valid_route:
        while len(result) == 0:
            while not valid:
                destination_edge = random.choice(total_edges)
                origin = random.choice(total_edges)
                if "#" in destination_edge and "#" in origin:
                    if "cluster" not in destination_edge and "cluster" not in origin:
                        if net.getEdge(destination_edge).getType() == "highway.primary" or net.getEdge(destination_edge).getType() == "highway.secondary" or net.getEdge(destination_edge).getType() == "highway.tertiary" or net.getEdge(destination_edge).getType() == "highway.living_street" or  net.getEdge(destination_edge).getType() ==  "highway.primary_link":
                            if net.getEdge(origin).getType() == "highway.primary" or net.getEdge(origin).getType() == "highway.secondary" or net.getEdge(origin).getType() == "highway.tertiary" or net.getEdge(origin).getType() == "highway.living_street" or  net.getEdge(origin).getType() ==  "highway.primary_link":
                                if not origin.startswith(":") and not destination_edge.startswith(":"):
                                    valid = True
            try:
                route = traci.simulation.findRoute(origin, destination_edge)
                result = route.edges
            except:
                print("Error in creating random route, trying again")
            if len(result) == 0:
                valid = False
        for r in result:
            if len(result) == 0:
                break
            if result.index(r) == 0:
                continue
            shape = net.getEdge(r).getShape()
            previous_shape = net.getEdge(result[result.index(r)-1]).getShape()
            edge_vector = (shape[-1][0] - shape[0][0], shape[-1][1] - shape[0][1])
            previous_vector = (previous_shape[-1][0] - previous_shape[0][0], previous_shape[-1][1] - previous_shape[0][1])
            angle = calcular_angle(edge_vector, previous_vector)
            if angle > 3*math.pi/4 and angle < 5*math.pi/4:
                result = []
                valid = False
                break
        if len(result) != 0:
            valid_route = True
    return result


#processar_route_automatica("route.json", "vehicle_real.rou.xml")
#processar_route_amb_coords("route_1.json", "ambulance.rou.xml")



