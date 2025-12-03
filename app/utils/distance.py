from geopy.distance import geodesic
import json


def calculate_distance(start_location: str, end_location: str) -> float:
    """
    시작 위치와 끝 위치 사이의 거리를 계산 (km)

    Args:
        start_location: JSON 문자열 형식의 시작 좌표 (예: '{"lat": 37.5665, "lng": 126.9780}')
        end_location: JSON 문자열 형식의 끝 좌표

    Returns:
        거리 (km)
    """
    try:
        start = json.loads(start_location)
        end = json.loads(end_location)

        start_coords = (start["lat"], start["lng"])
        end_coords = (end["lat"], end["lng"])

        distance = geodesic(start_coords, end_coords).kilometers
        return round(distance, 2)
    except Exception as e:
        return 0.0


def calculate_estimated_time(distance: float, walking_speed: float = 4.0) -> int:
    """
    거리를 기반으로 예상 소요 시간 계산 (분)

    Args:
        distance: 거리 (km)
        walking_speed: 걷는 속도 (km/h), 기본값 4.0

    Returns:
        예상 소요 시간 (분)
    """
    if distance <= 0:
        return 0
    time_hours = distance / walking_speed
    time_minutes = round(time_hours * 60)
    return max(1, time_minutes)  # 최소 1분


def calculate_carbon_saved(distance: float, carbon_per_km: float = 0.21) -> float:
    """
    걸은 거리를 기반으로 절감된 탄소량 계산 (kg)

    Args:
        distance: 거리 (km)
        carbon_per_km: km당 탄소 배출량 (kg), 기본값 0.21 (자동차 대비)

    Returns:
        절감된 탄소량 (kg)
    """
    if distance <= 0:
        return 0.0
    carbon_saved = distance * carbon_per_km
    return round(carbon_saved, 2)


def steps_to_distance(steps: int, step_length: float = 0.7) -> float:
    """
    걸음 수를 거리로 변환 (km)

    Args:
        steps: 걸음 수
        step_length: 보폭 (m), 기본값 0.7m

    Returns:
        거리 (km)
    """
    if steps <= 0:
        return 0.0
    distance_m = steps * step_length
    distance_km = distance_m / 1000
    return round(distance_km, 2)
