from shapely.geometry import LineString
from geopy.distance import geodesic
import json
import folium
import random
from datetime import datetime, timedelta, timezone
import pandas as pd
import matplotlib.cm as cm
import matplotlib.colors as colors
from branca.element import Template, MacroElement
import traci


def mostrar_ruta_en_mapa(coordenades, nom_fitxer="ruta_interpolada.html"):
    if not coordenades:
        raise ValueError("La llista de coordenades està buida.")

    # Centra el mapa en el primer punt
    lat_inici, lon_inici = coordenades[0][1], coordenades[0][0]
    mapa = folium.Map(location=[lat_inici, lon_inici], zoom_start=16)

    # Afegir línia al mapa
    folium.PolyLine(
        locations=[(lat, lon) for lon, lat in coordenades],
        color="blue",
        weight=4,
        opacity=0.8
    ).add_to(mapa)

    # Afegir un marcador al punt d'inici i final
    folium.Marker(location=[lat_inici, lon_inici], tooltip="Inici", icon=folium.Icon(color="green")).add_to(mapa)
    lat_final, lon_final = coordenades[-1][1], coordenades[-1][0]
    folium.Marker(location=[lat_final, lon_final], tooltip="Final", icon=folium.Icon(color="red")).add_to(mapa)

    # Guardar el mapa com a fitxer HTML
    mapa.save(nom_fitxer)
    print(f"Mapa guardat com: {nom_fitxer}")

def carregar_coordenades(path_json):
    coordenades = []
    with open(path_json) as jsonfile:
        data = json.load(jsonfile)
        coords = data.get('geometry').get('coordinates', [])
    return coords

def resample_route(coordinates, max_distance_m=0.5):
    if not coordinates or len(coordinates) < 2:
        return coordinates

    resampled = [coordinates[0]]

    for i in range(1, len(coordinates)):
        lon1, lat1 = coordinates[i - 1]
        lon2, lat2 = coordinates[i]
        d = geodesic((lat1, lon1), (lat2, lon2)).meters

        if d <= max_distance_m:
            resampled.append((lon2, lat2))
        else:
            # Nombre de punts addicionals a afegir
            num_segments = int(d // max_distance_m)
            for j in range(1, num_segments + 1):
                frac = j / (num_segments + 1)
                lon_interp = lon1 + frac * (lon2 - lon1)
                lat_interp = lat1 + frac * (lat2 - lat1)
                resampled.append((lon_interp, lat_interp))
            resampled.append((lon2, lat2))

    return resampled

def downsample_route(coordinates, min_distance_m=10):
    if not coordinates or len(coordinates) < 2:
        return coordinates

    downsampled = [coordinates[0]]
    last_point = coordinates[0]

    for i in range(1, len(coordinates)):
        lon, lat = coordinates[i]
        d = geodesic((last_point[1], last_point[0]), (lat, lon)).meters

        if d >= min_distance_m:
            downsampled.append((lon, lat))
            last_point = (lon, lat)

    return downsampled

def valor_proper(valor_actual, min_val, max_val, desviacio=1.5):
    while True:
        x_nou = random.gauss(mu=valor_actual, sigma=desviacio)
        if min_val <= x_nou <= max_val:
            return x_nou

def random100(len):
    num = 5
    result = []
    for i in range(len):
        result.append(num)
        num = valor_proper(num, 1, 10)

def interpolar_coords(lon1, lat1, lon2, lat2, fraccio):
    lon = lon1 + (lon2 - lon1) * fraccio
    lat = lat1 + (lat2 - lat1) * fraccio
    return (lon, lat)

def generate_congestion(coordinates, minSpeed, maxSpeed, measureTime):
    currentSpeed = random.uniform(minSpeed,maxSpeed)
    #currentSpeed = 30
    #Per simular molta congestió inicial, podem establir un valor aqui
    result = []
    currentTime = datetime.now(timezone.utc)
    coordinateIndex = 0
    result.append([coordinates[0][0], coordinates[0][1], currentTime])
    i = 0
    while True:
        if coordinateIndex == len(coordinates) -1:
            currentTime += timedelta(seconds=measureTime)
            result.append([coordinates[-1][0], coordinates[-1][1], currentTime])
            return result
        currentSpeed = valor_proper(currentSpeed, minSpeed, maxSpeed)
        distance = measureTime*currentSpeed/3.6
        coordinateDistance = geodesic((result[i][1], result[i][0]), (coordinates[coordinateIndex+1][1], coordinates[coordinateIndex+1][0])).meters
        if distance < coordinateDistance:
            fraccio = distance / coordinateDistance
            new_point = interpolar_coords(result[i][0], result[i][1], coordinates[coordinateIndex+1][0], coordinates[coordinateIndex+1][1], fraccio)
            currentTime += timedelta(seconds=measureTime)
            result.append([new_point[0], new_point[1], currentTime])
        elif distance > coordinateDistance:
            coordinateIndex += 1
            if coordinateIndex == len(coordinates) -1:
                currentTime += timedelta(seconds=measureTime)
                result.append([coordinates[-1][0], coordinates[-1][1], currentTime])
                return result
            coordinateDistance = geodesic((result[i][1], result[i][0]), (coordinates[coordinateIndex+1][1], coordinates[coordinateIndex+1][0])).meters
            while distance > coordinateDistance:
                coordinateIndex += 1
                if coordinateIndex == len(coordinates) -1:
                    currentTime += timedelta(seconds=measureTime)
                    result.append([coordinates[-1][0], coordinates[-1][1], currentTime])
                    return result
                coordinateDistance = geodesic((result[i][1], result[i][0]), (coordinates[coordinateIndex+1][1], coordinates[coordinateIndex+1][0])).meters
            fraccio = distance / coordinateDistance
            new_point = interpolar_coords(result[i][0], result[i][1], coordinates[coordinateIndex+1][0], coordinates[coordinateIndex+1][1], fraccio)
            currentTime += timedelta(seconds=measureTime)
            result.append([new_point[0], new_point[1], currentTime])
            coordinateIndex += 1
        i += 1

def mapa_generator_for_OSM_data(data, mapa_name):
    result = []
    v = []
    coords = []
    coords.append([data[0][0], data[0][1]])
    v.append(0)
    result.append([data[0][0], data[0][1], 0])
    for i in range(len(data)-1):
        coords.append([data[i+1][0], data[i+1][1]])
        speed = geodesic((data[i][1], data[i][0]), (data[i+1][1], data[i+1][0])).meters/((data[i+1][2]-data[i][2]).total_seconds())*3.6
        v.append(speed)
        result.append([data[i+1][0], data[i+1][1], speed])
    vmin, vmax = 0, 80
    norm = colors.Normalize(vmin=vmin, vmax=vmax)
    colormap = cm.get_cmap('gist_rainbow_r')
    center_lat = coords[len(coords)//2][1]
    center_long = coords[len(coords)//2][0]
    m = folium.Map(location=[center_lat, center_long], zoom_start=16, tiles='OpenStreetMap')
    for i in range(len(coords) - 1):
        val = v[i]
        if pd.isna(val):
            hex_color = "#999999"
        else:
            rgba = colormap(norm(val))
            hex_color = colors.rgb2hex(rgba)

        folium.PolyLine(
            locations=[
                [coords[i][1], coords[i][0]],
                [coords[i + 1][1], coords[i + 1][0]]
            ],
            color=hex_color,
            weight=5,
            opacity=0.8,
            popup=f"{val:.1f} km/h"
        ).add_to(m)
    totalTimeS = (data[-1][2]-data[0][2]).total_seconds()/60
    totalTime = f"{totalTimeS:.2f} min"
    print(totalTime)
    legend_html = f"""
    {{% macro html(this, kwargs) %}}
    <div style="
        position: fixed;
        bottom: 50px;
        left: 50px;
        width: 200px;
        height: auto;
        z-index: 9999;
        background-color: white;
        border: 2px solid grey;
        border-radius: 8px;
        padding: 10px;
        font-size: 13px;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
        word-wrap: break-word;
        overflow-wrap: break-word;
    ">
        <b>V (Km/h)</b><br>
        <div style="height: 16px; background: linear-gradient(to right, 
            #FF0000, #FF7F00, #FFFF00, #00FF00, #0000FF, #4B0082, #9400D3); 
            margin: 5px 0;">
        </div>
        <span style="float:left;">{vmax:.1f}</span>
        <span style="float:right;">{vmin:.1f}</span>
        <div style="clear: both;"></div>
        <p style="margin: 5px 0 0 0; font-size: 11px; max-width: 100%; word-wrap: break-word;">
            Red = fastest &nbsp;&nbsp; Purple = slowest<br>
            Total time is {totalTime}
        </p>
    </div>
    {{% endmacro %}}
    """

    legend = MacroElement()
    legend._template = Template(legend_html)
    m.get_root().add_child(legend)
    m.save(mapa_name)
    print(f"✅{mapa_name} generat correctament")
    return result, totalTime

def mapa_generator_for_SUMO_data(data, mapa_name):
    result = []
    v = []
    coords = []
    coords.append([data[0][0], data[0][1]])
    v.append(0)
    result.append([data[0][0], data[0][1], 0])
    for i in range(len(data)-1):
        coords.append([data[i+1][0], data[i+1][1]])
        speed = geodesic((data[i][1], data[i][0]), (data[i+1][1], data[i+1][0])).meters/((data[i+1][2]-data[i][2]))*3.6
        v.append(speed)
        result.append([data[i+1][0], data[i+1][1], speed])
    vmin, vmax = 0, 80    
    norm = colors.Normalize(vmin=vmin, vmax=vmax)
    colormap = cm.get_cmap('gist_rainbow_r')
    center_lat = coords[len(coords)//2][1]
    center_long = coords[len(coords)//2][0]
    m = folium.Map(location=[center_lat, center_long], zoom_start=16, tiles='OpenStreetMap')
    for i in range(len(coords) - 1):
        val = v[i]
        if pd.isna(val):
            hex_color = "#999999"
        else:
            rgba = colormap(norm(val))
            hex_color = colors.rgb2hex(rgba)

        folium.PolyLine(
            locations=[
                [coords[i][1], coords[i][0]],
                [coords[i + 1][1], coords[i + 1][0]]
            ],
            color=hex_color,
            weight=5,
            opacity=0.8,
            popup=f"{val:.1f} km/h"
        ).add_to(m)
    totalTime = (data[-1][2]-data[0][2])/60
    legend_html = f"""
    {{% macro html(this, kwargs) %}}
    <div style="
        position: fixed;
        bottom: 50px;
        left: 50px;
        width: 200px;
        height: auto;
        z-index: 9999;
        background-color: white;
        border: 2px solid grey;
        border-radius: 8px;
        padding: 10px;
        font-size: 13px;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
        word-wrap: break-word;
        overflow-wrap: break-word;
    ">
        <b>V (Km/h)</b><br>
        <div style="height: 16px; background: linear-gradient(to right, 
            #FF0000, #FF7F00, #FFFF00, #00FF00, #0000FF, #4B0082, #9400D3); 
            margin: 5px 0;">
        </div>
        <span style="float:left;">{vmax:.1f}</span>
        <span style="float:right;">{vmin:.1f}</span>
        <div style="clear: both;"></div>
        <p style="margin: 5px 0 0 0; font-size: 11px; max-width: 100%; word-wrap: break-word;">
            Red = fastest &nbsp;&nbsp; Purple = slowest<br>
            Total time is {totalTime}
        </p>
    </div>
    {{% endmacro %}}
    """

    legend = MacroElement()
    legend._template = Template(legend_html)
    m.get_root().add_child(legend)
    m.save(mapa_name)
    print(f"✅{mapa_name} generat correctament")
    return result, totalTime

def mapa_generator_for_data_analysis(data, mapa_name):
    vmin, vmax = 0, 80    
    norm = colors.Normalize(vmin=vmin, vmax=vmax)
    colormap = cm.get_cmap('gist_rainbow_r')
    center_lat = data[len(data)//2][1]
    center_long = data[len(data)//2][0]
    m = folium.Map(location=[center_lat, center_long], zoom_start=16, tiles='OpenStreetMap')
    for i in range(len(data) - 1):
        val = data[i][2]
        if pd.isna(val):
            hex_color = "#999999"
        else:
            rgba = colormap(norm(val))
            hex_color = colors.rgb2hex(rgba)

        folium.PolyLine(
            locations=[
                [data[i][1], data[i][0]],
                [data[i + 1][1], data[i + 1][0]]
            ],
            color=hex_color,
            weight=5,
            opacity=0.8,
            popup=f"{val:.1f} km/h"
        ).add_to(m)
    legend_html = f"""
    {{% macro html(this, kwargs) %}}
    <div style="
        position: fixed;
        bottom: 50px;
        left: 50px;
        width: 200px;
        height: auto;
        z-index: 9999;
        background-color: white;
        border: 2px solid grey;
        border-radius: 8px;
        padding: 10px;
        font-size: 13px;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
        word-wrap: break-word;
        overflow-wrap: break-word;
    ">
        <b>V (Km/h)</b><br>
        <div style="height: 16px; background: linear-gradient(to right, 
            #FF0000, #FF7F00, #FFFF00, #00FF00, #0000FF, #4B0082, #9400D3); 
            margin: 5px 0;">
        </div>
        <span style="float:left;">{vmax:.1f}</span>
        <span style="float:right;">{vmin:.1f}</span>
        <div style="clear: both;"></div>
        <p style="margin: 5px 0 0 0; font-size: 11px; max-width: 100%; word-wrap: break-word;">
            Red = fastest &nbsp;&nbsp; Purple = slowest<br>
        </p>
    </div>
    {{% endmacro %}}
    """

    legend = MacroElement()
    legend._template = Template(legend_html)
    m.get_root().add_child(legend)
    m.save(mapa_name)
    print(f"✅{mapa_name} generat correctament")

def get_next_valid_edge(currentEdge, edges):
    if "#" in currentEdge and not currentEdge.startswith(":") and "cluster" not in currentEdge:
        index = edges.index(currentEdge)
        if index == len(edges) - 1:
            return None
        next_edge = edges[index + 1]
        while "#" not in next_edge:
            index += 1
            if index == len(edges):
                return None
            next_edge = edges[index]
        return next_edge
    else:
        return None

def find_if_street_has_traffic_light(veh_id, net):
    lane_id = traci.vehicle.getLaneID(veh_id)
    tls_ids = traci.trafficlight.getIDList()
    for tls in tls_ids:
        if lane_id in traci.trafficlight.getControlledLanes(tls):
            return tls
    return None

def get_vehicles_in_front_of_ambulance(veh_id, lane_id):
    veh_pos = traci.vehicle.getLanePosition(veh_id)
    lane_length = traci.lane.getLength(lane_id)
    distance_to_end = lane_length - veh_pos
    vehicles_on_lane = traci.lane.getLastStepVehicleIDs(lane_id)
    vehicles_a_davant = [
        vid for vid in vehicles_on_lane
        if traci.vehicle.getLanePosition(vid) > veh_pos
    ]
    num_vehicles_a_davant = len(vehicles_a_davant)
    print(num_vehicles_a_davant)
    return vehicles_a_davant

def get_vehicles_in_emergency_lane(veh_id):
    veh_pos = traci.vehicle.getLanePosition(veh_id)
    current_edge = traci.vehicle.getRoadID(veh_id)
    lane_id = traci.vehicle.getLaneID(veh_id)
    lane_length = traci.lane.getLength(lane_id)
    distance_to_end = lane_length - veh_pos
    vehicles_on_lane = traci.lane.getLastStepVehicleIDs(lane_id)
    vehicles_a_davant = [
        vid for vid in vehicles_on_lane
        if traci.vehicle.getLanePosition(vid) > veh_pos
    ]
    num_vehicles_a_davant = len(vehicles_a_davant)
    print(num_vehicles_a_davant)
    return vehicles_a_davant    

def get_light_state(current_lane_id, tls):
    controlled_links = traci.trafficlight.getControlledLinks(tls)
    state = traci.trafficlight.getRedYellowGreenState(tls)
    for idx, link_group in enumerate(controlled_links):
        for link in link_group:
            incoming_lane = link[0]
            if incoming_lane == current_lane_id:
                current_light = state[idx]
    return current_light

def find_if_there_is_emergency_lane(veh_id):
    edge_id = traci.vehicle.getRoadID(veh_id)
    current_lane = traci.vehicle.getLaneID(veh_id)
    total_lanes = traci.vehicle.getLaneIndex(edge_id)
    if current_lane == len(total_lanes) or current_lane == len(total_lanes) -1:
        return

def get_data_for_congestion_IA(edges, veh_id, real_data, net):
    current_edge = traci.vehicle.getRoadID(veh_id)
    current_lane = traci.vehicle.getLaneID(veh_id)
    if current_lane == "":
        raise Exception("No current Lane Found")
    current_lane_ocupation = [current_lane, len(traci.lane.getLastStepVehicleIDs(current_lane))]
    current_lanes = [l.getID() for l in net.getEdge(current_edge).getLanes()]
    current_ocupation = []
    for l in current_lanes:
        vehicles = len(traci.lane.getLastStepVehicleIDs(l))
        current_ocupation.append([l, vehicles]) 
    veh_distance_to_end = traci.vehicle.getLanePosition(veh_id)
    next_edge = None
    time_for_next_edge = 0
    for e in edges:
        if e == current_edge:
            index = edges.index(e)
            if index == len(edges):
                raise Exception("No next Edge")
            next_edge = edges[index + 1]
    if next_edge == None:
        raise Exception("No next edge found")
    for r in real_data:
        if r[0] == next_edge:
            time_for_next_edge = r[1]
    next_lanes = [l.getID() for l in net.getEdge(next_edge).getLanes()]
    length_next_edge = traci.lane.getLength(next_lanes[0])
    speed_for_next_edge = length_next_edge/time_for_next_edge
    next_lanes_ocupation = []
    for l in next_lanes:
        vehicles = len(traci.lane.getLastStepVehicleIDs(l))
        next_lanes_ocupation.append([l, vehicles])
    current_edge_maximum_speed = traci.lane.getMaxSpeed(current_lane)
    next_edge_maximum_speed = traci.lane.getMaxSpeed(next_lanes[0])
    boolean_next_edge_counter_direction = False
    opposite_next_edge = "-" +next_edge if not next_edge.startswith("-") else next_edge[1:]
    if opposite_next_edge in traci.edge.getIDList():
        boolean_next_edge_counter_direction = True
    veh_id_waiting_to_enter = traci.simulation.getLoadedIDList()
    waiting_for_next_edge = 0
    if len(veh_id_waiting_to_enter) != 0:
        for w in veh_id_waiting_to_enter:
            if w == "simulation.findRoute":
                continue
            route = traci.vehicle.getRoute(w)
            if route and next_edge != None and route[0] == next_edge:
                waiting_for_next_edge += 1
    #result = [distance_to_next_edge, [current_lane, lane_ocupation], current_edge_ocupation(by_lanes), maximum_current_edge_speed,
    #time_for_next_edge, speed_for_next_edge, distance_of_next_edge, maximum_next_edge_speed, next_edge_occupancy, nº_of_lanes_in_next_edge,
    #opposite_direction, waiting_for_next_edge]
    result = [veh_distance_to_end, [current_lane, current_lane_ocupation], current_ocupation, current_edge_maximum_speed, time_for_next_edge, speed_for_next_edge, length_next_edge, next_edge_maximum_speed, next_lanes_ocupation, len(next_lanes_ocupation), boolean_next_edge_counter_direction, waiting_for_next_edge]
    return result

def find_data_from_ambulance_route(edges):
    edges_with_emergency_path = []
    edges_without_emergency_path = []
    sequence_of_edges_with_no_emergency_path = []
    current_sequence = []
    for e in edges:
        lanes = traci.edge.getLaneNumber(e)
        if lanes >= 2:
            print(f"edge {e} has {lanes} lanes, there could be an emergency path for the ambulance")
            edges_with_emergency_path.append(e)
        if lanes == 1:
            print(f"edge {e} has only 1 lane, there is no emergency path for the ambulance")
            edges_without_emergency_path.append(e)
        if lanes == 1 and (len(current_sequence) > 0 and current_sequence[-1] != edges[edges.index(e) - 1]):
            sequence_of_edges_with_no_emergency_path.append(current_sequence)
            current_sequence = []
        if lanes == 1 and (len(current_sequence) == 0 or current_sequence[-1] == edges[edges.index(e) - 1]):
            current_sequence.append(e)
    if len(current_sequence) > 0:
        sequence_of_edges_with_no_emergency_path.append(current_sequence)
    if len(edges) == edges_with_emergency_path:
        print("All edges have an emergency path for the ambulance")
    else:
        print(f"Only {len(edges_with_emergency_path)} edges have an emergency path for the ambulance, {len(edges_without_emergency_path)} edges do not have an emergency path for the ambulance")
    
    return edges_with_emergency_path, edges_without_emergency_path, sequence_of_edges_with_no_emergency_path
