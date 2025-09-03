from datetime import timedelta
import xml.etree.ElementTree as ET
import xml.dom.minidom as md
import traci
import random
import sumolib
from geopy.distance import geodesic
from routePreparator import mapa_generator_for_data_analysis, valor_proper

num_veh = 300
num_motos = 500

def reemplaçar_rutes(input_xml, output_xml, noves_rutes, tipus_vehicle=None):
    tree = ET.parse(input_xml)
    root = tree.getroot()

    parent = root if root.tag == 'routes' else root.find('routes')
    if parent is None:
        raise ValueError("No s'ha trobat `<routes>` com arrel o fill")

    for trip in list(parent.findall('trip')):
        parent.remove(trip)

    for trip in noves_rutes:
        trip_elem = ET.SubElement(parent, 'trip')
        for attr, val in trip.items():
            trip_elem.set(attr, str(val))

    if tipus_vehicle:
        ET.SubElement(parent, 'vType', tipus_vehicle)
    tree.write(output_xml, encoding='utf-8', xml_declaration=True)

def generate_random_route(edges, num_veh, net):
    routes = []
    time = 0
    for i in range(num_veh):
        coorect = False
        while not coorect:
            origin_edge = random.choice(edges)
            destination_edge = random.choice(edges)
            if net.getEdge(origin_edge).getType().startswith("highway") and net.getEdge(destination_edge).getType().startswith("highway") and origin_edge != destination_edge:
                coorect = True
        routes.append({
            'id': f'veh{i}',
            'depart': time,
            'from': origin_edge,
            'to': destination_edge,
            'departLane': 'best',
            'type': 'veh_passenger',
            'departSpeed': 'max'
        })
        if i % 50 == 0:
            time += 1
    return routes

def generate_random_route_starting_at_next_edge(veh_id, ambulance_edges, total_edges):
    result = []
    current_edge = traci.vehicle.getRoadID(veh_id)
    if current_edge not in ambulance_edges:
        return None
    index = ambulance_edges.index(traci.vehicle.getRoadID(veh_id))
    origin = ambulance_edges[index+1]
    while "#" not in origin:
        index += 1
        origin = ambulance_edges[index+1]
    while len(result) == 0:
        destination_edge = random.choice(total_edges)
        while not "#" in destination_edge:
            destination_edge = random.choice(total_edges)
        if "cluster" in destination_edge:
            continue
        route = traci.simulation.findRoute(origin, destination_edge)
        result = route.edges
    return result

def generate_random_route_starting_at_specific_edge(current_edge, ambulance_edges, total_edges, net):
    result = []
    possible_origin = net.getEdge(current_edge).getIncoming()
    options = []
    for p in possible_origin:
        options.append(p.getID())
    found = False
    while not found:
        origin = random.choice(options)
        if net.getEdge(origin).getType() == "highway.residential" or net.getEdge(origin).getType() == "highway.secondary_link" or net.getEdge(origin).getType() == "highway.primary" or net.getEdge(origin).getType() == "highway.secondary" or net.getEdge(origin).getType() == "highway.tertiary" or net.getEdge(origin).getType() == "highway.living_street" or  net.getEdge(origin).getType() ==  "highway.primary_link":
            found = True 
    while len(result) == 0:
        destination_edge = random.choice(total_edges)
        correct = False
        while not correct:
            destination_edge = random.choice(total_edges)
            if "cluster" in destination_edge or destination_edge.startswith(":"):
                continue
            if net.getEdge(destination_edge).getType() == "highway.primary" or net.getEdge(destination_edge).getType() == "highway.secondary" or net.getEdge(destination_edge).getType() == "highway.tertiary" or net.getEdge(destination_edge).getType() == "highway.living_street" or  net.getEdge(destination_edge).getType() ==  "highway.primary_link":
                correct = True
        route = traci.simulation.findRoute(origin, destination_edge)
        result = route.edges
    return result

def get_AmbulanceEdges(net):
    tree = ET.parse('ambulance.rou.xml')
    root = tree.getroot()

    parent = root if root.tag == 'route' else root.find('route')
    if parent is None:
        raise ValueError("No s'ha trobat `<route>` com arrel o fill")
    edges = parent.get('edges').split()
    if edges is None:
        raise ValueError("No s'ha trobat l'atribut `edges` a `<route>`")
    
    result = []
    for e in edges:
        incoming = net.getEdge(e).getIncoming()
        outgoing = net.getEdge(e).getOutgoing()
        result.append(e)
        for i in incoming:
            if i.getID() not in result:
                incoming_incoming = net.getEdge(i.getID()).getIncoming()
                for ii in incoming_incoming:
                    if '#' in ii.getID() and ii.getID() not in result:
                        result.append(ii.getID())
        for o in outgoing:
            if o.getID() not in result:
                outgoing_outgoing = net.getEdge(o.getID()).getIncoming()
                for oo in outgoing_outgoing:
                    if '#' in oo.getID() and oo.getID() not in result:
                        result.append(oo.getID())

    return result

def create_new_Routes(num_veh):
    try:
        traci.start(["sumo", "-c", "osm.sumocfg"])
        net = sumolib.net.readNet('osm.net.xml')
        edge_ids = get_AmbulanceEdges(net)
        traci.close()
        routes = generate_random_route(edge_ids, num_veh, net)
        reemplaçar_rutes('osm.passenger.trips copy.xml', 'osm.passenger.trips copy.xml', routes)
    except Exception as e:
        print("Error:", e)

def get_ordered_data(real_coords, simulated_coords):
    real_coords_treated = []
    simulated_coords_treated = []
    real_coords_treated.append(real_coords[0])
    simulated_coords_treated.append(simulated_coords[0])
    i = 1
    last_index_other_coords = 1
    last_index = 1
    total_v = 0
    if len(real_coords) < len(simulated_coords):
        while i < len(real_coords) - 1:
            real_coords_treated.append(real_coords[i])
            smallest_distance = geodesic((real_coords[i][1], real_coords[i][0]), (simulated_coords[last_index_other_coords][1], simulated_coords[last_index_other_coords][0])).meters
            stop = False
            while last_index_other_coords < len(simulated_coords) -1 and not stop:
                last_index_other_coords += 1
                total_v += simulated_coords[last_index_other_coords][2]
                if simulated_coords[last_index_other_coords][2] <= 0.5:
                    continue
                distance_to_point = geodesic((real_coords[i][1], real_coords[i][0]), (simulated_coords[last_index_other_coords][1], simulated_coords[last_index_other_coords][0])).meters
                if distance_to_point < smallest_distance:
                    smallest_distance = distance_to_point
                else:
                    stop = True
            i += 1
            divison = last_index_other_coords-last_index
            if divison != 0:
                simulated_coords_treated.append([simulated_coords[last_index_other_coords][0],simulated_coords[last_index_other_coords][1], total_v/(last_index_other_coords-last_index)])
            else:
                 simulated_coords_treated.append([simulated_coords[last_index_other_coords][0],simulated_coords[last_index_other_coords][1], 0])
            last_index = last_index_other_coords
            total_v = 0
    else:
         while i < len(simulated_coords) - 1:
            simulated_coords_treated.append(simulated_coords[i])
            smallest_distance = geodesic((simulated_coords[i][1], simulated_coords[i][0]), (real_coords[last_index_other_coords][1], real_coords[last_index_other_coords][0])).meters
            stop = False
            while last_index_other_coords < len(real_coords) -1 and not stop:
                last_index_other_coords += 1
                total_v += real_coords[last_index_other_coords][2]
                if real_coords[last_index_other_coords][2] <= 0.5:
                    continue
                distance_to_point = geodesic((simulated_coords[i][1], simulated_coords[i][0]), (real_coords[last_index_other_coords][1], real_coords[last_index_other_coords][0])).meters
                if distance_to_point < smallest_distance:
                    smallest_distance = distance_to_point
                else:
                    stop = True
            i += 1
            real_coords_treated.append([real_coords[last_index_other_coords][0],real_coords[last_index_other_coords][1], total_v/(last_index_other_coords-last_index)])
            last_index = last_index_other_coords
            total_v = 0
    return real_coords_treated, simulated_coords_treated    

def get_congestion_for_edge(coords_with_time, edges_with_Coords):
    result = []
    edge_index = 0
    smallest_distance = geodesic((coords_with_time[0][1], coords_with_time[0][0]), (edges_with_Coords[edge_index][1][1], edges_with_Coords[edge_index][1][0])).meters
    last_index = 0
    for s in coords_with_time:
        if edge_index == len(edges_with_Coords):
            break
        else:
            distance = geodesic((s[1], s[0]), (edges_with_Coords[edge_index][1][1], edges_with_Coords[edge_index][1][0])).meters
        if s == coords_with_time[-1]:
            if isinstance(s[2], timedelta):
                val1 = s[2].total_seconds()
            else:
                val1 = s[2]
            if isinstance(coords_with_time[last_index][2], timedelta):
                val2 = coords_with_time[last_index][2].total_seconds()
            else:
                val2 = coords_with_time[last_index][2]
            time = val1-val2
            if isinstance(time,timedelta):
                time = time.total_seconds()
            result.append([edges_with_Coords[edge_index][0], time])
            break
        elif distance <= smallest_distance:
            smallest_distance = distance
        else:
            if isinstance(s[2], timedelta):
                val1 = s[2].total_seconds()
            else:
                val1 = s[2]

            if isinstance(coords_with_time[last_index][2], timedelta):
                val2 = coords_with_time[last_index][2].total_seconds()
            else:
                val2 = coords_with_time[last_index][2]
            time = val1-val2
            if isinstance(time,timedelta):
                time = time.total_seconds()
            result.append([edges_with_Coords[edge_index][0], time])
            last_index = coords_with_time.index(s)
            edge_index += 1
            if edge_index < len(edges_with_Coords):
                smallest_distance = geodesic((s[1], s[0]), (edges_with_Coords[edge_index][1][1], edges_with_Coords[edge_index][1][0])).meters
            else:
                return result
    return result

def get_congestion_for_each_edge(simulated_coords_with_time, real_coords_with_time, edges_with_Coords):
    simulated_edges_congestion_for_simulated_coords = []
    edge_index = 0
    smallest_distance = geodesic((simulated_coords_with_time[0][1], simulated_coords_with_time[0][0]), (edges_with_Coords[edge_index][1][1], edges_with_Coords[edge_index][1][0])).meters
    last_index = 0
    for s in simulated_coords_with_time:
        if edge_index == len(edges_with_Coords):
            break
        else:
            distance = geodesic((s[1], s[0]), (edges_with_Coords[edge_index][1][1], edges_with_Coords[edge_index][1][0])).meters
        if s == simulated_coords_with_time[-1]:
            simulated_edges_congestion_for_simulated_coords.append([edges_with_Coords[edge_index][0],s[2]-simulated_coords_with_time[last_index][2]])
            break
        elif distance <= smallest_distance:
            smallest_distance = distance
        else:
            simulated_edges_congestion_for_simulated_coords.append([edges_with_Coords[edge_index][0],s[2]-simulated_coords_with_time[last_index][2]])
            last_index = simulated_coords_with_time.index(s)
            edge_index += 1
            smallest_distance = geodesic((s[1], s[0]), (edges_with_Coords[edge_index][1][1], edges_with_Coords[edge_index][1][0])).meters
    
    simulated_edges_congestion_for_real_coords = []
    edge_index = 0
    smallest_distance = geodesic((real_coords_with_time[0][1], real_coords_with_time[0][0]), (edges_with_Coords[edge_index][1][1], edges_with_Coords[edge_index][1][0])).meters
    last_index = 0
    for s in real_coords_with_time:
        distance = geodesic((s[1], s[0]), (edges_with_Coords[edge_index][1][1], edges_with_Coords[edge_index][1][0])).meters
        if edge_index == len(edges_with_Coords):
            break
        else:
            distance = geodesic((s[1], s[0]), (edges_with_Coords[edge_index][1][1], edges_with_Coords[edge_index][1][0])).meters
        if s == real_coords_with_time[-1]:
            simulated_edges_congestion_for_real_coords.append([edges_with_Coords[edge_index][0],(s[2]-real_coords_with_time[last_index][2]).total_seconds()])
            break
        elif distance <= smallest_distance:
            smallest_distance = distance
        else:
            simulated_edges_congestion_for_real_coords.append([edges_with_Coords[edge_index][0],(s[2]-real_coords_with_time[last_index][2]).total_seconds()])
            last_index = real_coords_with_time.index(s)
            edge_index += 1
            smallest_distance = geodesic((s[1], s[0]), (edges_with_Coords[edge_index][1][1], edges_with_Coords[edge_index][1][0])).meters
    return simulated_edges_congestion_for_simulated_coords, simulated_edges_congestion_for_real_coords

def get_difference_in_time_for_each_edge(simulates_edges_congestion, real_edges_congestion):
    if len(simulates_edges_congestion) != len(real_edges_congestion):
        print("ERROR, wrong entry in vector sizes")
        return
    i = 0
    result = []
    while i < len(simulates_edges_congestion):
        result.append(simulates_edges_congestion[i][1]- real_edges_congestion[i][1])
        i += 1
    return result

def congestion_analyzer(real_coords, real_time, simulated_coords, simulated_time, simulated_coords_with_time, real_coords_with_time, edges_with_Coords):
    simulates_edges_congestion = get_congestion_for_edge(simulated_coords_with_time, edges_with_Coords)
    real_edges_congestion = get_congestion_for_edge(real_coords_with_time, edges_with_Coords)
    
    #simulates_edges_congestion, real_edges_congestion = get_congestion_for_each_edge(simulated_coords_with_time, real_coords_with_time, edges_with_Coords)
    #Aquesta funció de get_difference_in_time_for_each_edge el que retorna es la diferencia entre el retard simulat i el real.
    #Així és pot utilitzar per veure la diferencia entre la congestió que s'ha definit, vs la que realment hauria d'haver definit.
    #Es pot utilitzar per entrenar un model de IA que implementi manualment la congestió
    print(get_difference_in_time_for_each_edge(simulates_edges_congestion, real_edges_congestion))
    print(f"simulated time was: {simulated_time}")
    print(f"real time was: {real_time}")
    real_coords_treated, simulated_coords_treated = get_ordered_data(real_coords, simulated_coords)
    mapa_generator_for_data_analysis(real_coords_treated, "real_coords_treated_map.html")
    mapa_generator_for_data_analysis(simulated_coords_treated, "simulated_coords_treated_map.html")

def generate_random_traffic_with_TRACI_for_begining(edges, amount, net):
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

    vehicles_added = []
    i = 0
    type1 = 0
    type2 = 0
    type3 = 0
    while i < amount:
        correct = False
        origin = None
        while not correct:
            origin = random.choice(edges)
            if "cluster" in origin or origin.startswith(":"):
                continue
            if net.getEdge(origin).getType() == "highway.primary" or net.getEdge(origin).getType() == "highway.secondary" or net.getEdge(origin).getType() == "highway.tertiary" or net.getEdge(origin).getType() == "highway.living_street" or  net.getEdge(origin).getType() ==  "highway.primary_link":
                correct = True
        edge_list = generate_random_route_starting_at_specific_edge(origin, edges, traci.edge.getIDList(), net)
        while edge_list is None:
            edge_list = generate_random_route_starting_at_specific_edge(origin, edges, traci.edge.getIDList(), net)
        k = 1
        type = valor_proper(k,1, 3)
        typeId = None
        if round(type) == 1:
            typeId = "Compliance_1"
            type1 += 1
        elif round(type) == 2:
            typeId = "Compliance_2"
            type2 += 1
        elif round(type) == 3:
            typeId = "Compliance_3"
            type3 += 1
        traci.route.add("test"+str(i), edge_list)
        #Per fer proves de com afecta l'actitud dels conductors.
        traci.vehicle.add("test"+str(i), routeID="test"+str(i), departLane="allowed", typeID=typeId, depart=round(i/50))
        vehicles_added.append(["test"+str(i), edge_list, typeId, round(i/50)])

        #traci.vehicle.add("test"+str(i), routeID="test"+str(i), departLane="best", typeID="Compliance_0")
        #vehicles_added.append(["test"+str(i), edge_list, "Compliance_0"])
        i += 1
    
    return vehicles_added, type1, type2, type3

def generate_random_traffic_with_TRACI_for_during(next_edge, next_next_edge, edges, amount, net, num):
    vehicles_added = []
    i = 0
    type1 = 0
    type2 = 0
    type3 = 0
    amount_1 = amount // 2
    amount_2 = amount - amount_1
    #In this part I'm generating vehicles with routes that are on the next edge or not, depending on whether there is a next edge or not
    if next_edge == None and next_next_edge == None:
        while i < amount:
            correct = False
            origin = None
            while not correct:
                origin = random.choice(edges)
                if "cluster" in origin or origin.startswith(":"):
                    continue
                if net.getEdge(origin).getType() == "highway.primary" or net.getEdge(origin).getType() == "highway.secondary" or net.getEdge(origin).getType() == "highway.tertiary" or net.getEdge(origin).getType() == "highway.living_street" or  net.getEdge(origin).getType() ==  "highway.primary_link":
                    correct = True
            edge_list = generate_random_route_starting_at_specific_edge(origin, edges, traci.edge.getIDList(), net)
            while edge_list is None:
                edge_list = generate_random_route_starting_at_specific_edge(origin, edges, traci.edge.getIDList(), net)
            k = 1
            type = valor_proper(k,1, 3)
            typeId = None
            if round(type) == 1:
                typeId = "Compliance_1"
                type1 += 1
            elif round(type) == 2:
                typeId = "Compliance_2"
                type2 += 1
            elif round(type) == 3:
                typeId = "Compliance_3"
                type3 += 1
            traci.route.add("test"+str(num + i), edge_list)
            #Per fer proves de com afecta l'actitud dels conductors.
            traci.vehicle.add("test"+str(num + i), routeID="test"+str(num + i), departLane="allowed", typeID=typeId)
            vehicles_added.append(["test"+str(num + i), edge_list, typeId, traci.simulation.getTime()])

            #traci.vehicle.add("test"+str(i), routeID="test"+str(i), departLane="best", typeID="Compliance_0")
            #vehicles_added.append(["test"+str(i), edge_list, "Compliance_0"])
            i += 1
    elif next_edge != None and next_next_edge == None:
        while i < amount:
            correct = False
            origin = next_edge
            edge_list = generate_random_route_starting_at_specific_edge(origin, edges, traci.edge.getIDList(), net)
            while edge_list is None:
                edge_list = generate_random_route_starting_at_specific_edge(origin, edges, traci.edge.getIDList(), net)
            k = 1
            type = valor_proper(k,1, 3)
            typeId = None
            if round(type) == 1:
                typeId = "Compliance_1"
                type1 += 1
            elif round(type) == 2:
                typeId = "Compliance_2"
                type2 += 1
            elif round(type) == 3:
                typeId = "Compliance_3"
                type3 += 1
            traci.route.add("test"+str(num + i), edge_list)
            #Per fer proves de com afecta l'actitud dels conductors.
            traci.vehicle.add("test"+str(num + i), routeID="test"+str(num + i), departLane="allowed", typeID=typeId)
            vehicles_added.append(["test"+str(num + i), edge_list, typeId, traci.simulation.getTime()])

            #traci.vehicle.add("test"+str(i), routeID="test"+str(i), departLane="best", typeID="Compliance_0")
            #vehicles_added.append(["test"+str(i), edge_list, "Compliance_0"])
            i += 1
    elif next_edge != None and next_next_edge != None:
        while i < amount_1:
            correct = False
            origin = next_edge
            edge_list = generate_random_route_starting_at_specific_edge(origin, edges, traci.edge.getIDList(), net)
            while edge_list is None:
                edge_list = generate_random_route_starting_at_specific_edge(origin, edges, traci.edge.getIDList(), net)
            k = 1
            type = valor_proper(k,1, 3)
            typeId = None
            if round(type) == 1:
                typeId = "Compliance_1"
                type1 += 1
            elif round(type) == 2:
                typeId = "Compliance_2"
                type2 += 1
            elif round(type) == 3:
                typeId = "Compliance_3"
                type3 += 1
            traci.route.add("test"+str(num + i), edge_list)
            #Per fer proves de com afecta l'actitud dels conductors.
            traci.vehicle.add("test"+str(num + i), routeID="test"+str(num + i), departLane="allowed", typeID=typeId)
            vehicles_added.append(["test"+str(num + i), edge_list, typeId, traci.simulation.getTime()])

            #traci.vehicle.add("test"+str(i), routeID="test"+str(i), departLane="best", typeID="Compliance_0")
            #vehicles_added.append(["test"+str(i), edge_list, "Compliance_0"])
            i += 1
        l = 0
        while l < amount_2:
            correct = False
            origin = next_next_edge
            edge_list = generate_random_route_starting_at_specific_edge(origin, edges, traci.edge.getIDList(), net)
            while edge_list is None:
                edge_list = generate_random_route_starting_at_specific_edge(origin, edges, traci.edge.getIDList(), net)
            k = 1
            type = valor_proper(k,1, 3)
            typeId = None
            if round(type) == 1:
                typeId = "Compliance_1"
                type1 += 1
            elif round(type) == 2:
                typeId = "Compliance_2"
                type2 += 1
            elif round(type) == 3:
                typeId = "Compliance_3"
                type3 += 1
            traci.route.add("test"+str(num + i), edge_list)
            #Per fer proves de com afecta l'actitud dels conductors.
            traci.vehicle.add("test"+str(num + i), routeID="test"+str(num + i), departLane="allowed", typeID=typeId)
            vehicles_added.append(["test"+str(num + i), edge_list, typeId, traci.simulation.getTime()])

            #traci.vehicle.add("test"+str(i), routeID="test"+str(i), departLane="best", typeID="Compliance_0")
            #vehicles_added.append(["test"+str(i), edge_list, "Compliance_0"])
            i += 1
            l += 1
        
    return vehicles_added, type1, type2, type3


