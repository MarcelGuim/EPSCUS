import traci
from routePreparator import get_next_valid_edge

def find_if_street_has_traffic_light(veh_id):
    lane_id = traci.vehicle.getLaneID(veh_id)
    tls_ids = traci.trafficlight.getIDList()
    for tls in tls_ids:
        if lane_id in traci.trafficlight.getControlledLanes(tls):
            return tls
    return None

def find_if_street_has_traffic_light_for_edge(edge_id):
    lane = edge_id + "_0"
    tls_ids = traci.trafficlight.getIDList()
    for tls in tls_ids:
        if lane in traci.trafficlight.getControlledLanes(tls):
            return tls
        
def get_light_state(current_lane_id, tls):
    controlled_links = traci.trafficlight.getControlledLinks(tls)
    state = traci.trafficlight.getRedYellowGreenState(tls)
    final_idx = 0
    for idx, link_group in enumerate(controlled_links):
        for link in link_group:
            incoming_lane = link[0]
            if incoming_lane == current_lane_id:
                current_light = state[idx]
                final_idx = idx
    return current_light, state, final_idx

def get_light_state_for_edge(edge_id, tls):
    lane_number = traci.edge.getLaneNumber(edge_id)
    lanes = []
    for i in range(lane_number):
        lanes.append(edge_id + "_" + str(i))
    controlled_links = traci.trafficlight.getControlledLinks(tls)
    state = traci.trafficlight.getRedYellowGreenState(tls)
    final_idx = []
    current_lights = []
    for idx, link_group in enumerate(controlled_links):
        for link in link_group:
            incoming_lane = link[0]
            if incoming_lane in lanes:
                current_lights.append(state[idx])
                final_idx.append(idx)
    return current_lights, state, final_idx

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
    return vehicles_a_davant

def find_if_there_is_emergency_lane(veh_id):
    edge_id = traci.vehicle.getRoadID(veh_id)
    total_lanes = traci.edge.getLaneNumber(edge_id)
    if total_lanes < 2:
        return False
    left_lane = edge_id + "_" + str(total_lanes - 1)
    second_lane = edge_id + "_" + str(total_lanes - 2)
    left_lane_vehicles = get_vehicles_in_front_of_ambulance(veh_id,left_lane)
    second_lane_vehicles = get_vehicles_in_front_of_ambulance(veh_id, second_lane)
    vehicles_in_left_lane_correct = []
    vehicles_in_left_lane_not_correct = []
    vehicles_in_second_lane_correct = []
    vehicles_in_second_lane_not_correct = []
    for llv in left_lane_vehicles:
        if traci.vehicle.getLateralLanePosition(llv) <= 0.7:
            vehicles_in_left_lane_not_correct.append(llv)
        else:
            vehicles_in_left_lane_correct.append(llv)
    for slv in second_lane_vehicles:
        if traci.vehicle.getLateralLanePosition(slv) <= -0.7:
            vehicles_in_second_lane_correct.append(slv)
        else:
            vehicles_in_second_lane_not_correct.append(slv)
    if len(vehicles_in_left_lane_not_correct) != 0 or len(vehicles_in_second_lane_not_correct) != 0:
        return False
    elif (len(vehicles_in_left_lane_correct) == 0 and len(vehicles_in_left_lane_not_correct) == 0) or (len(vehicles_in_second_lane_correct) == 0 and len(vehicles_in_second_lane_not_correct) == 0):
          return True
    else:
        return True

def change_traffic_light_for_one_lane(tls, new_state, state, idx):
    state_list = list(state)
    state_list[idx] = new_state
    new_lights = "".join(state_list)
    traci.trafficlight.setRedYellowGreenState(tls, new_lights)

def change_traffic_lights_for_whole_edge(tls, new_state, state, idx, previous_edge=None, current_edge=None):
    state_list = list(state)
    if previous_edge is not None and current_edge is not None:
        links = traci.trafficlight.getControlledLinks(tls)
        for i in links:
            if i[0][0][:-2] == previous_edge:
                idx.append(links.index(i))
    else:
        for i in range(len(state_list)):
            if i not in idx:
                state_list[i] = "r"
    for i in range (len(idx)):
        state_list[idx[i]] = new_state
    lanes = traci.trafficlight.getControlledLinks(tls)
    new_lights = "".join(state_list)
    traci.trafficlight.setRedYellowGreenState(tls, new_lights)

def change_traffic_lights_for_whole_edge_2(tls, new_state, state, idx, edges, previous_edge=None, current_edge=None):
    state_list = list(state)
    lanes = traci.trafficlight.getControlledLinks(tls)
    incoming_edges = []
    outgoing_edges = []
    for connection in lanes:
        for (incLane, outLane, _) in connection:
            incoming_edges.append(traci.lane.getEdgeID(incLane))
            outgoing_edges.append(traci.lane.getEdgeID(outLane))
    i = 0
    for inc in incoming_edges:
        if inc in edges:
            idx.append(i)
        i += 1
    i = 0
    for i in range(len(state_list)):
        if i not in idx:
            state_list[i] = "r"
    for i in range (len(idx)):
        state_list[idx[i]] = new_state
    new_lights = "".join(state_list)
    traci.trafficlight.setRedYellowGreenState(tls, new_lights)


def change_traffic_lights_for_whole_outgoing_edge(tls, new_state, state, idx, edges):
    state_list = list(state)
    lanes = traci.trafficlight.getControlledLinks(tls)
    incoming_edges = []
    outgoing_edges = []
    for connection in lanes:
        for (incLane, outLane, _) in connection:
            incoming_edges.append(traci.lane.getEdgeID(incLane))
            outgoing_edges.append(traci.lane.getEdgeID(outLane))
    i = 0
    for inc in incoming_edges:
        if inc in edges:
            idx.append(i)
        i += 1
    i = 0
    for i in range(len(state_list)):
        if i not in idx:
            state_list[i] = "r"
    for i in range (len(idx)):
        state_list[idx[i]] = new_state
    new_lights = "".join(state_list)
    traci.trafficlight.setRedYellowGreenState(tls, new_lights)

def change_lights_for_case_only_lights(tls, new_state, state, idx, net, edges, previous_edge=None, current_edge=None):
    change_traffic_lights_for_whole_edge_2(tls, new_state, state, idx, edges, previous_edge, current_edge)
    current_next_light, next_state, next_idx = get_light_state_for_edge(current_edge, tls)
    print(next_state)
    outgoing = net.getEdge(current_edge).getOutgoing()
    tls_s = []
    tls_s.append(tls)
    for e in outgoing:
        tls = find_if_street_has_traffic_light_for_edge(e.getID())
        if tls:
            tls_s.append(tls)
            current_next_light, next_state, next_idx = get_light_state_for_edge(e.getID(), tls)
            print(next_state)        
            change_traffic_lights_for_whole_outgoing_edge(tls, "G", next_state, next_idx, edges)
            current_next_light, next_state, next_idx = get_light_state_for_edge(e.getID(), tls)
            print(next_state)
            nwef = 2  
    try:
        next_next_edge = get_next_valid_edge(current_edge, edges)
        if next_next_edge is not None:
            return [next_next_edge, tls_s]
        else:
            return ["1", tls]
    except Exception as e:
        print("Error:", e)

#DEPRECATED
def create_emergency_lane(veh_id, edge_id):
    total_lanes = traci.edge.getLaneNumber(edge_id)
    if total_lanes < 2:
        return False
    left_lane = edge_id + "_" + str(total_lanes - 1)
    second_lane = edge_id + "_" + str(total_lanes - 2)
    left_lane_vehicles = get_vehicles_in_front_of_ambulance(veh_id,left_lane)
    second_lane_vehicles = get_vehicles_in_front_of_ambulance(veh_id, second_lane)
    for v in left_lane_vehicles:
        position = traci.vehicle.getLateralLanePosition(v)
        if position < 0.5:
            amount = 0.5-position
            traci.vehicle.setLaneChangeMode(v, 512)
            traci.vehicle.changeSublane(v, amount)
            print(f"Changed lane of vehicle {v} in left lane to make way for ambulance")
    for v in second_lane_vehicles:
        position = traci.vehicle.getLateralLanePosition(v)
        if position > -0.9:
            amount = -0.9-position
            traci.vehicle.setLaneChangeMode(v, 512)
            traci.vehicle.changeSublane(v, amount)
            print(f"Changed lane of vehicle {v} in second lane to make way for ambulance")

def get_outgoing_edges_of_edge(edge_id):
    lanes = traci.edge.getLanes(edge_id)
    outgoing_edges = set()
    for lane in lanes:
        for link in traci.lane.getLinks(lane.getID()):
            outgoing_lane = link[0]
            out_edge = traci.lane.getEdgeID(outgoing_lane)
            outgoing_edges.add(out_edge)
    return outgoing_edges

def activate_emergency_lane_in_edge(edge_id, edges, net):
    num_lanes = traci.edge.getLaneNumber(edge_id)
    #traci.lane.setAllowed(edge_id+"_"+str(num_lanes -1), ["emergency"])
    traci.lane.setAllowed(edge_id+"_0", ["emergency"])
    tls = find_if_street_has_traffic_light_for_edge(edge_id)
    next_next_edge = get_next_valid_edge(edge_id, edges)
    if tls:
        previous_edge = edges[edges.index(edge_id) - 1] if edges.index(edge_id) > 0 else None
        current_next_light, next_state, next_idx = get_light_state_for_edge(edge_id, tls)        
        change_traffic_lights_for_whole_edge(tls, "G", next_state, next_idx, previous_edge, edge_id)
        previous_edge = edge_id
        outgoing = net.getEdge(edge_id).getOutgoing()
        tls_s = []
        tls_s.append(tls)
        for e in outgoing:
            tls = find_if_street_has_traffic_light_for_edge(e.getID())
            if tls:
                tls_s.append(tls)
                current_next_light, next_state, next_idx = get_light_state_for_edge(e.getID(), tls)        
                change_traffic_lights_for_whole_edge(tls, "G", next_state, next_idx, previous_edge, e.getID())
        try:
            next_next_edge = get_next_valid_edge(edge_id, edges)
            if next_next_edge is not None:
                return [next_next_edge, tls_s]
            else:
                return ["1", tls]
        except Exception as e:
            print("Error:", e)