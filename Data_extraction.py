import json
import os
import matplotlib.pyplot as plt

def get_data_by_edge(data, edges):
    current_edge = None
    speed = 0
    index = 1
    initial_time = 0
    density = 0
    result = []
    for d in data:
        if current_edge == None:
            current_edge = d[4]
            initial_time = d[2]
        if d[4] == current_edge or d[4] not in edges:
            speed += d[3]
            index += 1
            density += d[5]/(d[6]*d[7]) 
        if d[4] != current_edge and d[4] in edges:
            result.append([current_edge, speed/index, density/index, d[2] - initial_time, d[6], d[7]])    
            current_edge = d[4]
            initial_time = d[2]
            speed = 0
            index = 1
            density = 0
    total_density = 0
    max_density = 0
    for r in result:
        total_density += r[2]
        if float(r[2]) > max_density:
            max_density = float(r[2])
    average_density = 0
    try:
        average_density = total_density/len(result)
    except:
        print("Error, average density not calculated")

    return result, average_density, max_density


def data_treatment(filename, distance,j, edges, k, type1, type2, type3, total_time_for_no_vehicles, total_time_for_vehicles_and_no_device, total_time_for_vehicles_and_device, diference_from_ideal, total_diference_from_real, increase_in_ideal_percent, decrease_in_real_percent,     edges_with_more_than_one_lane_and_tls, edges_with_more_than_one_lane_and_no_tls, edges_with_one_lane_and_tls, edges_with_one_lane_and_no_tls, average_density_v_n_d ,average_density_v_d, max_density_v_n_d):
    result = {
    f"result {j, k}": {
        "distance": distance,
        "cars": j,
        "vehicles": [type1, type2, type3],
        "edges": edges,
        "total_time_for_no_vehicles": total_time_for_no_vehicles,
        "total_time_for_vehicles_and_no_device": total_time_for_vehicles_and_no_device,
        "total_time_for_vehicles_and_device": total_time_for_vehicles_and_device,
        "diference_from_ideal": diference_from_ideal,
        "total_diference_from_real": total_diference_from_real, 
        "increase_in_ideal_percent": increase_in_ideal_percent, 
        "decrease_in_real_percent": decrease_in_real_percent,
        "edges_with_more_than_one_lane_and_tls": edges_with_more_than_one_lane_and_tls,
        "edges_with_more_than_one_lane_and_no_tls": edges_with_more_than_one_lane_and_no_tls,
        "edges_with_one_lane_and_tls": edges_with_one_lane_and_tls,
        "edges_with_one_lane_and_no_tls": edges_with_one_lane_and_no_tls,
        "average_density_v_n_d": average_density_v_n_d,
        "average_density_v_d": average_density_v_d,
        "max_density_v_n_d": max_density_v_n_d
        }
    }

    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        with open(filename, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = [data]
    else:
        data = []
    data.append(result)
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


def data_treatment_with_traffic_light(filename, distance,j, edges, k, type1, type2, type3, total_time_for_no_vehicles, total_time_for_vehicles_and_no_device, total_time_for_vehicles_and_device,total_time_for_vehicles_and_lights_control, diference_from_ideal, total_diference_from_real, increase_in_ideal_percent, decrease_in_real_percent,     edges_with_more_than_one_lane_and_tls, edges_with_more_than_one_lane_and_no_tls, edges_with_one_lane_and_tls, edges_with_one_lane_and_no_tls, average_density_v_n_d ,average_density_v_d, max_density_v_n_d):
    result = {
    f"result {j, k}": {
        "distance": distance,
        "cars": j,
        "vehicles": [type1, type2, type3],
        "edges": edges,
        "total_time_for_no_vehicles": total_time_for_no_vehicles,
        "total_time_for_vehicles_and_no_device": total_time_for_vehicles_and_no_device,
        "total_time_for_vehicles_and_device": total_time_for_vehicles_and_device,
        "total_time_for_vehicles_and_lights_control": total_time_for_vehicles_and_lights_control,
        "difference_from_ideal": diference_from_ideal,
        "total_difference_from_real": total_diference_from_real,
        "difference_from_just_traffic_control": total_time_for_vehicles_and_lights_control - total_time_for_vehicles_and_device,
        "increase_in_ideal_percent": increase_in_ideal_percent, 
        "decrease_in_real_percent": decrease_in_real_percent,
        "decrease_from_traffic_control": (total_time_for_vehicles_and_lights_control - total_time_for_vehicles_and_device)/total_time_for_vehicles_and_lights_control*100,
        "edges_with_more_than_one_lane_and_tls": edges_with_more_than_one_lane_and_tls,
        "edges_with_more_than_one_lane_and_no_tls": edges_with_more_than_one_lane_and_no_tls,
        "edges_with_one_lane_and_tls": edges_with_one_lane_and_tls,
        "edges_with_one_lane_and_no_tls": edges_with_one_lane_and_no_tls,
        "average_density_v_n_d": average_density_v_n_d,
        "average_density_v_d": average_density_v_d,
        "max_density_v_n_d": max_density_v_n_d
        }
    }

    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        with open(filename, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = [data]
    else:
        data = []
    data.append(result)
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def data_treatment_2(data_no_vehciles, data_for_vehicles_no_device, data_for_vehicles_and_device, filename, distance,j, edges, k, type1, type2, type3, total_time_for_no_vehicles, total_time_for_vehicles_and_no_device, total_time_for_vehicles_and_device, diference_from_ideal, total_diference_from_real, increase_in_ideal_percent, decrease_in_real_percent, edges_with_tls_and_more_than_one_lane, edges_with_no_tls_and_more_than_one_lane, edges_with_tls_and_one_lane, edges_with_no_tls_and_one_lane, average_density_v_n_d ,average_density_v_d, max_density_v_n_d):
    edges_tls_more_one = len(edges_with_tls_and_more_than_one_lane)/len(edges)*100
    edges_no_tls_more_one = len(edges_with_no_tls_and_more_than_one_lane)/len(edges)*100
    edges_tls_one = len(edges_with_tls_and_one_lane)/len(edges)*100
    edges_no_tls_one = len(edges_with_no_tls_and_one_lane)/len(edges)*100
    
    comparisson = []
    edges_no_v = []
    edges_v_no_d = []
    edges_v_d = []
    result = []
    for a in data_no_vehciles:
        edges_no_v.append(a[0])
    for a in data_for_vehicles_no_device:
        edges_v_no_d.append(a[0])
    for a in data_for_vehicles_and_device:
        edges_v_d.append(a[0])
    
    edges_common = []

    for e in edges_no_v:
        if e in edges_v_no_d and e in edges_v_d:
            edges_common.append(e)

    for e in edges_common:
        type_e = None
        if e in edges_with_tls_and_one_lane:
            type_e = 0
        if e in edges_with_no_tls_and_one_lane:
            type_e = 1
        if e in edges_with_tls_and_more_than_one_lane:
            type_e = 2
        if e in edges_with_no_tls_and_more_than_one_lane:
            type_e = 3
        index_no_v = edges_no_v.index(e)
        index_v_no_d = edges_v_no_d.index(e)
        index_v_d = edges_v_d.index(e)
        print(data_for_vehicles_and_device)
        print(data_no_vehciles)
        print(data_for_vehicles_no_device)
        #edge, time for no vehicles, time for vehicles no device, time for vehicle and device, number of lanes, tls?
        comparisson.append([data_for_vehicles_and_device[index_v_d][0], data_no_vehciles[index_no_v][3], data_for_vehicles_no_device[index_v_no_d][3], data_for_vehicles_and_device[index_v_d][3], data_for_vehicles_and_device[index_v_d][4], type_e])
        
    """
    if len(data_for_vehicles_and_device) == len(data_for_vehicles_no_device):
        for i in len(data_for_vehicles_and_device):
            if data_for_vehicles_and_device[i][0] in edges_with_tls_and_more_than_one_lane:
                type_ = 1
            if data_for_vehicles_and_device[i][0] in edges_with_no_tls_and_more_than_one_lane:
                type_ = 2
            if data_for_vehicles_and_device[i][0] in edges_with_tls_and_one_lane:
                type_ = 3
            if data_for_vehicles_and_device[i][0] in edges_with_no_tls_and_one_lane:
                type_ = 4
            comparisson.append([data_for_vehicles_and_device[i][0], data_for_vehicles_no_device[i][3],data_for_vehicles_and_device[i][3], data_for_vehicles_and_device[i][4], type_])
    """
    result = {
    f"result {j, k}": {
        "distance": distance,
        "cars": j,
        "vehicles": [type1, type2, type3],
        "edges": edges,
        "total_time_for_no_vehicles": total_time_for_no_vehicles,
        "total_time_for_vehicles_and_no_device": total_time_for_vehicles_and_no_device,
        "total_time_for_vehicles_and_device": total_time_for_vehicles_and_device,
        "diference_from_ideal": diference_from_ideal,
        "total_diference_from_real": total_diference_from_real, 
        "increase_in_ideal_percent": increase_in_ideal_percent, 
        "decrease_in_real_percent": decrease_in_real_percent,
        "edges_with_more_than_one_lane_and_tls": edges_tls_more_one,
        "edges_with_more_than_one_lane_and_no_tls": edges_no_tls_more_one,
        "edges_with_one_lane_and_tls": edges_tls_one,
        "edges_with_one_lane_and_no_tls": edges_no_tls_one,
        "average_density_v_n_d": average_density_v_n_d,
        "average_density_v_d": average_density_v_d,
        "max_density_v_n_d": max_density_v_n_d,
        "edges_comparisson": comparisson
        }
    }

    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        with open(filename, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = [data]
    else:
        data = []
    data.append(result)
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def compare_data(results_no_vehicles, results_vehicles_no_device, results_vehicles_device, edges_with_no_tls_and_one_lane, edges_with_tls_and_one_lane, edges_with_no_tls_and_more_than_one_lane, edges_with_tls_and_more_than_one_lane):
    edges_no_v = []
    edges_v_no_d = []
    edges_v_d = []
    result = []
    for a in results_no_vehicles:
        edges_no_v.append(a[0])
    for a in results_vehicles_no_device:
        edges_v_no_d.append(a[0])
    for a in results_vehicles_device:
        edges_v_d.append(a[0])
    
    edges_common = []

    for e in edges_no_v:
        if e in edges_no_v and e in edges_v_d:
            edges_common.append(e)

    for e in edges_common:
        type_e = None
        if e in edges_with_tls_and_one_lane:
            type_e = 0
        if e in edges_with_no_tls_and_one_lane:
            type_e = 1
        if e in edges_with_tls_and_more_than_one_lane:
            type_e = 2
        if e in edges_with_no_tls_and_more_than_one_lane:
            type_e = 3
        index_no_v = edges_no_v.index(e)
        index_v_no_d = edges_v_no_d.index(e)
        index_v_d = edges_v_d.index(e)

        #Result = lanes, density, speed increase (%), time decrease (%)
        speed_increase = (float(results_vehicles_device[index_v_d][1]) - float(results_vehicles_no_device[index_v_no_d][1]))/float(results_vehicles_device[index_v_d][1])*100
        time_decrease = (float(results_vehicles_no_device[index_v_no_d][3]) - float(results_vehicles_device[index_v_d][3]))/float(results_vehicles_no_device[index_v_no_d][3])*100
        result.append([results_no_vehicles[index_no_v][4], results_no_vehicles[index_no_v][5],results_vehicles_no_device[index_v_no_d][2],  int(speed_increase), int(time_decrease), type_e])
    return result

def results_vs_traffic(path, x_axis, y_axis):
    data = None
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = [data]
    i = 2
    results = []
    addition_y = 0
    index_addition_y = 0
    old_traffic = 0
    first = True
    for d in data:
        if not d:
            continue
        values = list(d.values())[0]
        key = list(d.keys())[0]
        traffic = int(key.split("(")[1].split(",")[0])
        if float(values['decrease_in_real_percent']) <= 0:
            continue
        if first or old_traffic == traffic:
            first = False
            addition_y += values[y_axis]
            index_addition_y += 1
            old_traffic = traffic
        else:
            results.append([old_traffic, addition_y/index_addition_y])
            addition_y = values[y_axis]
            index_addition_y = 1
            old_traffic = traffic
    
    results.append([old_traffic, addition_y/index_addition_y])
    x = [point[0] for point in results]
    y = [point[1] for point in results]
    plt.plot(x, y, marker="o", linestyle="-")
    plt.xlabel(x_axis)
    plt.ylabel(y_axis)
    plt.title(f"{x_axis} vs {y_axis}")
    plt.grid(True)
    plt.show()

def results_vs_distance(path, x_axis, y_axis):
    data = None
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = [data]
    if data == None:
        print("ERROR")
        return None
    results = []
    addition_y = 0
    index_addition_y = 0
    old_traffic = 0
    first = True
    distance = 0
    max_value = 0
    for d in data:
        if not d:
            continue
        values = list(d.values())[0]
        key = list(d.keys())[0]
        traffic = int(key.split("(")[1].split(",")[0])
        if float(values[y_axis]) <= 0:
            continue
        if first or old_traffic == traffic:
            first = False
            if float(values[y_axis]) > 70:
                continue
            addition_y += values[y_axis]
            if float(values[y_axis]) > max_value:
                max_value = float(values[y_axis])
            index_addition_y += 1
            old_traffic = traffic
            distance = values[x_axis]    
        else:
            results.append([distance, addition_y/index_addition_y])
            if float(values[y_axis]) > 70:
                addition_y = 0
                index_addition_y = 0
                distance = values[x_axis]
                old_traffic = traffic
                continue
            addition_y = values[y_axis]
            if float(values[y_axis]) > max_value:
                max_value = float(values[y_axis])
            index_addition_y = 1
            old_traffic = traffic
            distance = values[x_axis]
    print(max_value)
    results.append([distance, addition_y/index_addition_y])
    x = [point[0] for point in results]
    y = [point[1] for point in results]
    plt.plot(x, y, marker="o", linestyle="-")
    plt.xlabel(x_axis)
    plt.ylabel(y_axis)
    plt.title(f"{x_axis} vs {y_axis}")
    plt.grid(True)
    plt.show()

def results_vs_traffic_density(path, x_axis, y_axis):
    data = None
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = [data]
    results = []
    for d in data:
        if not d:
            continue
        values = list(d.values())[0]
        key = list(d.keys())[0]
        traffic = int(key.split("(")[1].split(",")[0])
        if float(values['decrease_in_real_percent']) <= 0:
            continue
        results.append([values[x_axis], values[y_axis]])
        
    x = [point[0] for point in results]
    y = [point[1] for point in results]
    plt.scatter(x, y, marker="o")
    plt.xlabel(x_axis)
    plt.ylabel(y_axis)
    plt.title(f"{x_axis} vs {y_axis}")
    plt.grid(True)
    plt.show(block = True)

def results_turns_vs_time_increase_ideal(path, x_axis, y_axis):
    data = None
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = [data]
    results = []
    for d in data:
        if not d:
            continue
        values = list(d.values())[0]
        key = list(d.keys())[0]
        traffic = int(key.split("(")[1].split(",")[0])
        results.append([float(traffic)+4, values[y_axis]])
        
    x = [point[0] for point in results]
    y = [point[1] for point in results]
    plt.scatter(x, y, marker="o")
    plt.xlabel(x_axis)
    plt.ylabel(y_axis)
    plt.title(f"{x_axis} vs {y_axis}")
    plt.grid(True)
    plt.show(block = True)

def results_x_value_vs_value_time_increase_ideal(path, x_axis, y_axis):
    data = None
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = [data]
    results = []
    for d in data:
        if not d:
            continue
        values = list(d.values())[0]
        key = list(d.keys())[0]
        results.append([values[x_axis], values[y_axis]])
        
    x = [point[0] for point in results]
    y = [point[1] for point in results]
    plt.scatter(x, y, marker="o")
    plt.xlabel(x_axis)
    plt.ylabel(y_axis)
    plt.title(f"{x_axis} vs {y_axis}")
    plt.grid(True)
    plt.show(block = True)

def results_times_vs_traffic_density(path, x_axis, y_axis_1, y_axis_2, y_axis_3, y_axis_4):
    data = None
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = [data]
    results = []
    for d in data:
        if not d:
            continue
        values = list(d.values())[0]
        key = list(d.keys())[0]
        traffic = int(key.split("(")[1].split(",")[0])
        if float(values['decrease_in_real_percent']) <= 0:
            continue
        results.append([values[x_axis], values[y_axis_1], values[y_axis_2], values[y_axis_3], values[y_axis_4]])
    
    x = [point[0] for point in results]
    y = [point[1] for point in results]
    w = [point[2] for point in results]
    z = [point[3] for point in results]
    k = [point[4] for point in results]

    plt.scatter(x, y, marker="o", color="blue", label=y_axis_1)
    #plt.scatter(x, w, marker="o", color="red", label=y_axis_2)
    plt.scatter(x, z, marker="o", color="green", label=y_axis_3)
    plt.scatter(x, k, marker="o", color="red", label=y_axis_4)
    plt.xlabel(x_axis)
    plt.ylabel("Time")
    plt.ylim(0, 300)
    plt.title(f"{x_axis} vs Times")
    plt.grid(True)
    plt.legend()
    plt.legend(loc="upper left")
    plt.show(block = True)

def results_relations_vs_traffic_density(path, x_axis, y_axis_1, y_axis_2, y_axis_3, y_axis_4):
    data = None
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = [data]
    results = []
    for d in data:
        if not d:
            continue
        values = list(d.values())[0]
        key = list(d.keys())[0]
        traffic = int(key.split("(")[1].split(",")[0])
        if float(values['decrease_in_real_percent']) <= 0:
            continue
        results.append([values[x_axis], values[y_axis_1], values[y_axis_2], values[y_axis_3], values[y_axis_4]])
    results_sorted = sorted(results, key=lambda x: x[0])
    final_data = []
    for p in results_sorted:
        result_1 = (p[3]-p[1])/p[1]*100
        result_2 = (p[4]-p[1])/p[1]*100
        final_data.append([p[0], result_1, result_2])
    i = 0
    presented_data = []
    while i < len(final_data) - 3:
        av_density = (final_data[i][0] + final_data[i+1][0] + final_data[i+2][0])/3
        av_y_value_1 = (final_data[i][1] + final_data[i+1][1] + final_data[i+2][1])/3
        av_y_value_2 = (final_data[i][2] + final_data[i+1][2] + final_data[i+2][2])/3
        diference = av_y_value_2 - av_y_value_1
        presented_data.append([av_density, av_y_value_1, av_y_value_2, diference])
        i += 3
    x = [point[0] for point in presented_data]
    y = [point[1] for point in presented_data]
    w = [point[2] for point in presented_data]
    z = [point[3] for point in presented_data]

    plt.scatter(x, y, marker="o", color="blue", label="increase with device")
    plt.scatter(x, w, marker="o", color="red", label="increase with traffic control")
    plt.scatter(x, z, marker="o", color="green", label="difference between increases") 
    plt.xlabel(x_axis)
    plt.ylabel("Time")
    plt.ylim(0, 1000)
    plt.title(f"{x_axis} vs Times")
    plt.grid(True)
    plt.legend()
    plt.legend(loc="upper right")
    plt.show(block = True)

def results_increases_vs_traffic_density(path, x_axis, y_axis_1, y_axis_2, y_axis_3, y_axis_4):
    data = None
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = [data]
    results = []
    for d in data:
        if not d:
            continue
        values = list(d.values())[0]
        key = list(d.keys())[0]
        traffic = int(key.split("(")[1].split(",")[0])
        if float(values['decrease_in_real_percent']) <= 0:
            continue
        results.append([values[x_axis], values[y_axis_1], values[y_axis_2], values[y_axis_3], values[y_axis_4]])
        relations = []
        for r in results:
            increase_device = (r[3]-r[1])/r[1]*100
            increase_lights = (r[4]-r[1])/r[1]*100
            increase_lights_with_device = (r[4] - r[3])/r[3]*100
            relations.append([r[0],increase_device, increase_lights, increase_lights_with_device])
    x = [point[0] for point in relations]
    y = [point[1] for point in relations]
    w = [point[2] for point in relations]
    z = [point[3] for point in relations]

    plt.scatter(x, y, marker="o", color="blue", label="increase_with_device")
    plt.scatter(x, w, marker="o", color="red", label="increase_with_traffic_lights")
    plt.scatter(x, z, marker="o", color="green", label="increase_traffic_lights_with_device")
    plt.xlabel(x_axis)
    plt.ylabel("Increase")
    plt.ylim(0, 100)
    plt.title(f"{x_axis} vs Increase")
    plt.grid(True)
    plt.legend()
    plt.legend(loc="upper left")
    plt.show(block = True)

def results_increases_vs_traffic_density_average(path, x_axis, y_axis_1, y_axis_2, y_axis_3, y_axis_4):
    data = None
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = [data]
    results = []
    for d in data:
        if not d:
            continue
        values = list(d.values())[0]
        key = list(d.keys())[0]
        traffic = int(key.split("(")[1].split(",")[0])
        if float(values['decrease_in_real_percent']) <= 0:
            continue
        results.append([values[x_axis], values[y_axis_1], values[y_axis_2], values[y_axis_3], values[y_axis_4]])
        relations = []
        for r in results:
            increase_device = (r[3]-r[1])/r[1]*100
            increase_lights = (r[4]-r[1])/r[1]*100
            increase_lights_with_device = (r[4] - r[3])/r[3]*100
            relations.append([r[0],increase_device, increase_lights, increase_lights_with_device])
    results_sorted = sorted(relations, key=lambda x: x[0])
    presented_data = []
    i = 0
    while i < len(results_sorted) - 3:
        av_density = (results_sorted[i][0] + results_sorted[i+1][0] + results_sorted[i+2][0])/3
        av_y_value_1 = (results_sorted[i][1] + results_sorted[i+1][1] + results_sorted[i+2][1])/3
        av_y_value_2 = (results_sorted[i][2] + results_sorted[i+1][2] + results_sorted[i+2][2])/3
        av_y_value_3 = (results_sorted[i][3] + results_sorted[i+1][3] + results_sorted[i+2][3])/3
        presented_data.append([av_density, av_y_value_1, av_y_value_2, av_y_value_3])
        i += 3
    x = [point[0] for point in presented_data]
    y = [point[1] for point in presented_data]
    w = [point[2] for point in presented_data]
    z = [point[3] for point in presented_data]
    """
    x = [point[0] for point in relations]
    y = [point[1] for point in relations]
    w = [point[2] for point in relations]
    z = [point[3] for point in relations]
    """
    plt.scatter(x, y, marker="o", color="blue", label="increase_with_device")
    plt.scatter(x, w, marker="o", color="red", label="increase_with_traffic_lights")
    plt.scatter(x, z, marker="o", color="green", label="increase_traffic_lights_with_device")
    plt.xlabel(x_axis)
    plt.ylabel("Increase")
    plt.ylim(0, 250)
    plt.title(f"{x_axis} vs Increase")
    plt.grid(True)
    plt.legend()
    plt.legend(loc="upper left")
    plt.show(block = True)

#results_relations_vs_traffic_density("result_comparison_specific_routes_9.json", "average_density_v_n_d", "total_time_for_no_vehicles","total_time_for_vehicles_and_no_device", "total_time_for_vehicles_and_device", "total_time_for_vehicles_and_lights_control")
#results_times_vs_traffic_density("result_comparison_specific_routes_9.json", "average_density_v_n_d", "total_time_for_no_vehicles","total_time_for_vehicles_and_no_device", "total_time_for_vehicles_and_device", "total_time_for_vehicles_and_lights_control")
#results_increases_vs_traffic_density("result_comparison_specific_routes_9.json", "average_density_v_n_d", "total_time_for_no_vehicles","total_time_for_vehicles_and_no_device", "total_time_for_vehicles_and_device", "total_time_for_vehicles_and_lights_control")
results_increases_vs_traffic_density_average("result_comparison_specific_routes_9.json", "average_density_v_n_d", "total_time_for_no_vehicles","total_time_for_vehicles_and_no_device", "total_time_for_vehicles_and_device", "total_time_for_vehicles_and_lights_control")
#results_vs_distance("result_comparison_turn_increase.json", "distance", "increase_in_ideal_percent")
#results_vs_traffic("result_comparison_1.json", "traffic", "decrease_in_real_percent")
#results_vs_traffic_density("result_comparison_specific_routes_5.json", "average_density_v_n_d", "decrease_in_real_percent")
#results_vs_traffic_density("result_comparison_specific_routes_5.json", "average_density_v_n_d", "increase_in_ideal_percent")
#results_turns_vs_time_increase_ideal("result_comparison_turn_increase.json", "distance", "increase_in_ideal_percent")