import math
from typing import List, Dict, Any, Tuple, Optional
from app.schemas.routing import RouteOptimizeRequest, RouteOptimizeResponse, OptimizedStop, CandidateStop

# Hệ số phát thải CO2 trung bình đô thị Việt Nam (kg CO2 / km)
# 75% xe máy @ 0.082 kg/km + 25% ô tô @ 0.171 kg/km = 0.104 kg CO2/km
CO2_EMISSION_FACTOR_KG_PER_KM = 0.104

# Hệ số uốn khúc đường bộ thực tế so với đường chim bay (Ho Chi Minh City urban grid)
ROAD_DETOUR_FACTOR = 1.35

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c * ROAD_DETOUR_FACTOR, 2)

def get_transit_mins(dist_km: float, mode: str = 'motorbike') -> int:
    speeds = {
        'motorbike': 24.0,  # 24 km/h (vận tốc di chuyển trung bình nội đô HCM)
        'car': 18.0,        # 18 km/h (kẹt xe đô thị)
        'walking': 4.5,     # 4.5 km/h
    }
    speed = speeds.get(mode, 24.0)
    return max(3, int(round((dist_km / speed) * 60)))

def parse_time_to_minutes(time_str: str) -> int:
    try:
        parts = time_str.strip().split(':')
        return int(parts[0]) * 60 + int(parts[1])
    except Exception:
        return 8 * 60

def format_minutes_to_time(mins: int) -> str:
    h = (mins // 60) % 24
    m = mins % 60
    return f"{h:02d}:{m:02d}"

def select_best_candidates(
    candidates: List[CandidateStop],
    desired_stops: int,
    budget: Optional[int],
    start_lat: float,
    start_lon: float
) -> List[CandidateStop]:
    """
    [TASK-BIZ-02-01 & BIZ-02-04] Lọc và chọn K ứng viên tốt nhất:
    - Loại trừ các ứng viên đơn lẻ vượt quá toàn bộ ngân sách
    - Đảm bảo tính đa dạng tiến trình ẩm thực: starter -> main -> dessert/cafe
    - Ưu tiên điểm đánh giá và khoảng cách từ điểm xuất phát
    """
    if len(candidates) <= desired_stops:
        return candidates

    # Lọc bỏ quán có giá cao hơn ngân sách tổng (nếu ngân sách hợp lệ)
    valid_pool = candidates
    if budget and budget > 0:
        affordable = [c for c in candidates if (c.avg_price or 50000) <= budget]
        if affordable:
            valid_pool = affordable

    # Phân nhóm theo meal_type
    groups: Dict[str, List[CandidateStop]] = {
        'starter': [],
        'main': [],
        'dessert': [],
        'cafe': [],
    }

    for c in valid_pool:
        m_type = c.meal_type if c.meal_type in groups else 'main'
        groups[m_type].append(c)

    # Sắp xếp từng nhóm theo điểm đánh giá và khoảng cách gần xuất phát
    for k in groups:
        groups[k].sort(
            key=lambda c: (
                -(c.rating or 4.0),
                haversine_distance_km(start_lat, start_lon, c.lat, c.lon)
            )
        )

    selected: List[CandidateStop] = []

    if desired_stops == 2:
        # 1 món chính + 1 tráng miệng / cafe
        if groups['main']:
            selected.append(groups['main'].pop(0))
        if groups['cafe']:
            selected.append(groups['cafe'].pop(0))
        elif groups['dessert']:
            selected.append(groups['dessert'].pop(0))
    elif desired_stops == 3:
        # 1 khai vị/ăn nhẹ + 1 món chính + 1 cafe/tráng miệng
        if groups['starter']:
            selected.append(groups['starter'].pop(0))
        if groups['main']:
            selected.append(groups['main'].pop(0))
        if groups['cafe']:
            selected.append(groups['cafe'].pop(0))
        elif groups['dessert']:
            selected.append(groups['dessert'].pop(0))
    elif desired_stops >= 4:
        if groups['starter']:
            selected.append(groups['starter'].pop(0))
        if groups['main']:
            selected.append(groups['main'].pop(0))
        if groups['dessert']:
            selected.append(groups['dessert'].pop(0))
        if groups['cafe']:
            selected.append(groups['cafe'].pop(0))

    # Nếu vẫn chưa đủ số chặng mong muốn, lấy thêm từ pool còn lại theo rating cao nhất
    remaining = [c for c in valid_pool if c not in selected]
    remaining.sort(
        key=lambda c: (
            -(c.rating or 4.0),
            haversine_distance_km(start_lat, start_lon, c.lat, c.lon)
        )
    )

    while len(selected) < desired_stops and remaining:
        selected.append(remaining.pop(0))

    return selected[:desired_stops]

def solve_with_ortools(
    nodes: List[Dict[str, Any]],
    dist_matrix: List[List[float]],
    time_matrix: List[List[int]],
    start_time_mins: int
) -> Optional[List[int]]:
    """
    [TASK-BIZ-02-05] Giải bài toán TSPTW (Traveling Salesperson Problem with Time Windows)
    bằng Google OR-Tools constraint solver.
    """
    try:
        from ortools.constraint_solver import routing_enums_pb2
        from ortools.constraint_solver import pywrapcp
    except ImportError:
        return None

    num_locations = len(nodes)
    if num_locations <= 1:
        return []

    manager = pywrapcp.RoutingIndexManager(num_locations, 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    # Đăng ký hàm chi phí khoảng cách
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(dist_matrix[from_node][to_node] * 1000)

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Đăng ký chiều Thời Gian (Time Dimension)
    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        dwell = nodes[from_node]['duration']
        transit = time_matrix[from_node][to_node]
        return dwell + transit

    time_callback_index = routing.RegisterTransitCallback(time_callback)
    routing.AddDimension(
        time_callback_index,
        180,       # Cho phép slack tối đa 180 phút
        24 * 60,   # Horizon cả ngày (1440 phút)
        False,     # Không bắt buộc start cumul bằng 0
        'Time'
    )
    time_dimension = routing.GetDimensionOrDie('Time')

    # Ràng buộc Time Window [open, close] cho từng địa điểm
    for i, node in enumerate(nodes):
        index = manager.NodeToIndex(i)
        open_m = node['open']
        close_m = max(open_m + node['duration'], node['close'])
        time_dimension.CumulVar(index).SetRange(open_m, close_m)

    # Ràng buộc thời gian xuất phát tại Node 0
    start_index = manager.NodeToIndex(0)
    time_dimension.CumulVar(start_index).SetRange(start_time_mins, start_time_mins + 15)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.milliseconds = 500

    solution = routing.SolveWithParameters(search_parameters)

    if solution:
        route = []
        index = routing.Start(0)
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node != 0:
                route.append(node)
            index = solution.Value(routing.NextVar(index))
        return route

    return None

def solve_greedy_gastronomic(
    candidates: List[CandidateStop],
    start_lat: float,
    start_lon: float,
    start_time_mins: int,
    mode: str
) -> List[Dict[str, Any]]:
    """
    [TASK-BIZ-02-05 Fallback] Thuật toán Heuristic ưu tiên Tiến trình Ẩm thực (Gastronomic Progression):
    1. Khai vị / Ăn vặt (Starter) ->
    2. Món chính (Main) ->
    3. Tráng miệng / Cafe (Dessert / Cafe)
    Kết hợp tối thiểu hóa quãng đường chuyển tiếp giữa các chặng kế tiếp.
    """
    meal_order_weight = {
        'starter': 1,
        'main': 2,
        'dessert': 3,
        'cafe': 3,
    }

    # Phân nhóm ứng viên theo loại bữa ăn
    unvisited = list(candidates)
    scheduled: List[Dict[str, Any]] = []
    curr_lat = start_lat
    curr_lon = start_lon
    curr_time = start_time_mins

    # Bước 1: Sắp xếp sơ bộ theo progression
    unvisited.sort(
        key=lambda c: (
            meal_order_weight.get(c.meal_type or 'main', 2),
            haversine_distance_km(curr_lat, curr_lon, c.lat, c.lon),
            -(c.rating or 4.0)
        )
    )

    idx = 1
    while unvisited:
        # Tìm ứng viên tiếp theo phù hợp nhất với tiến trình và gần điểm hiện tại nhất
        current_stage = scheduled[-1]['candidate'].meal_type if scheduled else None
        current_weight = meal_order_weight.get(current_stage or 'starter', 0)

        # Ưu tiên các quán có trọng số tiến trình >= trọng số chặng hiện tại
        eligible = [c for c in unvisited if meal_order_weight.get(c.meal_type or 'main', 2) >= current_weight]
        pool = eligible if eligible else unvisited

        # Chọn quán có khoảng cách di chuyển ngắn nhất từ điểm hiện tại
        next_cand = min(pool, key=lambda c: haversine_distance_km(curr_lat, curr_lon, c.lat, c.lon))
        unvisited.remove(next_cand)

        dist = haversine_distance_km(curr_lat, curr_lon, next_cand.lat, next_cand.lon)
        transit_m = get_transit_mins(dist, mode)
        arrival_m = curr_time + transit_m

        open_m = parse_time_to_minutes(next_cand.open_time or '08:00')
        close_m = parse_time_to_minutes(next_cand.close_time or '22:00')

        # Nếu đến sớm hơn giờ mở cửa, chờ đến khi quán mở
        actual_arrival_m = max(arrival_m, open_m)
        duration_m = next_cand.dining_duration_mins or 45
        departure_m = actual_arrival_m + duration_m

        scheduled.append({
            'candidate': next_cand,
            'order_index': idx,
            'arrival_time': format_minutes_to_time(actual_arrival_m),
            'departure_time': format_minutes_to_time(departure_m),
            'dining_duration_mins': duration_m,
            'transit_time_mins': transit_m,
            'dist_from_prev_km': round(dist, 2),
        })

        curr_lat = next_cand.lat
        curr_lon = next_cand.lon
        curr_time = departure_m
        idx += 1

    return scheduled

def optimize_food_tour_route(request: RouteOptimizeRequest) -> RouteOptimizeResponse:
    candidates = request.candidates
    if not candidates:
        return RouteOptimizeResponse(
            stops=[],
            total_distance_km=0.0,
            total_duration_mins=0,
            total_cost=0,
            remaining_budget=request.budget or 0,
            co2_saved_kg=0.0,
            status='EMPTY',
            message='Không có ứng viên nhà hàng nào được cung cấp.',
            algorithm_used='None',
            routing_mode=request.routing_mode or 'motorbike',
        )

    start_lat, start_lon = request.start_location[0], request.start_location[1]
    start_time_mins = request.start_time_mins or 660  # 11:00 AM
    mode = request.routing_mode or 'motorbike'
    budget = request.budget or 250000
    desired_stops = max(1, min(request.desired_stops or 3, 10))

    # [TASK-BIZ-02-01] Chọn lọc K ứng viên tối ưu theo khẩu vị, ngân sách và tiến trình
    selected_candidates = select_best_candidates(
        candidates=candidates,
        desired_stops=desired_stops,
        budget=budget,
        start_lat=start_lat,
        start_lon=start_lon
    )

    # [TASK-BIZ-02-05] Thử giải với Google OR-Tools TSPTW
    nodes = [{'lat': start_lat, 'lon': start_lon, 'open': start_time_mins, 'close': start_time_mins + 30, 'duration': 0}]
    for c in selected_candidates:
        nodes.append({
            'lat': c.lat,
            'lon': c.lon,
            'open': parse_time_to_minutes(c.open_time or '08:00'),
            'close': parse_time_to_minutes(c.close_time or '22:00'),
            'duration': c.dining_duration_mins or 45,
        })

    n = len(nodes)
    dist_matrix = [[0.0] * n for _ in range(n)]
    time_matrix = [[0] * n for _ in range(n)]

    for i in range(n):
        for j in range(n):
            if i != j:
                d = haversine_distance_km(nodes[i]['lat'], nodes[i]['lon'], nodes[j]['lat'], nodes[j]['lon'])
                dist_matrix[i][j] = d
                time_matrix[i][j] = get_transit_mins(d, mode)

    or_tools_order = solve_with_ortools(nodes, dist_matrix, time_matrix, start_time_mins)

    stops_result: List[OptimizedStop] = []
    total_dist = 0.0
    total_cost = 0
    algorithm_used = 'OR-Tools TSPTW'

    if or_tools_order and len(or_tools_order) == len(selected_candidates):
        # OR-Tools tìm được nghiệm tối ưu thỏa mãn tất cả Time Windows
        curr_time = start_time_mins
        prev_node = 0

        for order_idx, node_idx in enumerate(or_tools_order):
            cand = selected_candidates[node_idx - 1]
            dist_km = dist_matrix[prev_node][node_idx]
            transit_m = time_matrix[prev_node][node_idx]
            arrival_m = curr_time + transit_m
            open_m = nodes[node_idx]['open']
            actual_arrival = max(arrival_m, open_m)
            duration_m = cand.dining_duration_mins or 45
            departure_m = actual_arrival + duration_m

            stops_result.append(OptimizedStop(
                id=cand.id,
                name=cand.name,
                lat=cand.lat,
                lon=cand.lon,
                order_index=order_idx + 1,
                meal_type=cand.meal_type or 'main',
                arrival_time=format_minutes_to_time(actual_arrival),
                departure_time=format_minutes_to_time(departure_m),
                dining_duration_mins=duration_m,
                transit_time_mins=transit_m,
                distance_to_next_km=round(dist_km, 2),
                estimated_cost=cand.avg_price or 50000,
                tags=cand.tags,
            ))

            total_dist += dist_km
            total_cost += cand.avg_price or 50000
            curr_time = departure_m
            prev_node = node_idx

        status_msg = 'OR-Tools TSPTW Optimal Solution'
        algorithm_used = 'OR-Tools TSPTW'
    else:
        # Fallback sang Gastronomic Progression Heuristic
        heuristic_stops = solve_greedy_gastronomic(selected_candidates, start_lat, start_lon, start_time_mins, mode)
        for s in heuristic_stops:
            cand = s['candidate']
            stops_result.append(OptimizedStop(
                id=cand.id,
                name=cand.name,
                lat=cand.lat,
                lon=cand.lon,
                order_index=s['order_index'],
                meal_type=cand.meal_type or 'main',
                arrival_time=s['arrival_time'],
                departure_time=s['departure_time'],
                dining_duration_mins=s['dining_duration_mins'],
                transit_time_mins=s['transit_time_mins'],
                distance_to_next_km=s['dist_from_prev_km'],
                estimated_cost=cand.avg_price or 50000,
                tags=cand.tags,
            ))
            total_dist += s['dist_from_prev_km']
            total_cost += cand.avg_price or 50000

        status_msg = 'Gastronomic Progression Heuristic'
        algorithm_used = 'Gastronomic Progression Heuristic'

    # Tính toán phát thải CO2 tiết kiệm được (so với đường vòng lộn xộn không tối ưu 1.35x)
    detour_dist = total_dist * 1.35
    dist_saved = max(0.5, detour_dist - total_dist)
    co2_saved = round(dist_saved * CO2_EMISSION_FACTOR_KG_PER_KM, 2)

    total_duration = sum(s.dining_duration_mins + s.transit_time_mins for s in stops_result)
    remaining_budget = max(0, budget - total_cost)

    return RouteOptimizeResponse(
        stops=stops_result,
        total_distance_km=round(total_dist, 2),
        total_duration_mins=total_duration,
        total_cost=total_cost,
        remaining_budget=remaining_budget,
        co2_saved_kg=co2_saved,
        status='SUCCESS',
        message=f"Tối ưu thành công lộ trình ẩm thực ({status_msg})",
        algorithm_used=algorithm_used,
        routing_mode=mode,
    )


