import unittest
from app.schemas.routing import CandidateStop, RouteOptimizeRequest, RouteOptimizeResponse, OptimizedStop
from app.core.route_optimizer import optimize_food_tour_route

class TestRoutingContract(unittest.TestCase):
    def test_canonical_request_validation(self):
        canonical_data = {
            "start_location": [10.7769, 106.7009],
            "start_time_mins": 660,
            "budget": 200000,
            "routing_mode": "motorbike",
            "desired_stops": 2,
            "candidates": [
                {
                    "id": "rest_1",
                    "name": "Pho 24",
                    "lat": 10.7750,
                    "lon": 106.7020,
                    "meal_type": "main",
                    "open_time": "08:00",
                    "close_time": "22:00",
                    "dining_duration_mins": 45,
                    "avg_price": 60000,
                    "rating": 4.5
                },
                {
                    "id": "rest_2",
                    "name": "Che Ba Ba",
                    "lat": 10.7780,
                    "lon": 106.7050,
                    "meal_type": "dessert",
                    "open_time": "10:00",
                    "close_time": "21:00",
                    "dining_duration_mins": 30,
                    "avg_price": 30000,
                    "rating": 4.8
                }
            ]
        }
        req = RouteOptimizeRequest.model_validate(canonical_data)
        self.assertEqual(req.start_location, [10.7769, 106.7009])
        self.assertEqual(len(req.candidates), 2)
        self.assertEqual(req.candidates[0].lon, 106.7020)

    def test_legacy_request_compatibility(self):
        legacy_data = {
            "start_lat": 10.7769,
            "start_lng": 106.7009,
            "start_time": "11:30",
            "budget_vnd": 300000,
            "routing_mode": "motorbike",
            "restaurants": [
                {
                    "id": "rest_legacy_1",
                    "lat": 10.7750,
                    "lng": 106.7020,
                    "open": "08:00",
                    "close": "22:00",
                    "duration_mins": 40
                }
            ]
        }
        req = RouteOptimizeRequest.model_validate(legacy_data)
        self.assertEqual(req.start_location, [10.7769, 106.7009])
        self.assertEqual(req.start_time_mins, 690) # 11*60 + 30
        self.assertEqual(req.budget, 300000)
        self.assertEqual(len(req.candidates), 1)
        self.assertEqual(req.candidates[0].lon, 106.7020)
        self.assertEqual(req.candidates[0].dining_duration_mins, 40)
        self.assertEqual(req.candidates[0].open_time, "08:00")

    def test_response_contains_both_stops_and_ordered_stops(self):
        req_data = {
            "start_location": [10.7769, 106.7009],
            "start_time_mins": 660,
            "candidates": [
                {
                    "id": "r1",
                    "name": "Restaurant 1",
                    "lat": 10.7750,
                    "lon": 106.7020,
                }
            ]
        }
        req = RouteOptimizeRequest.model_validate(req_data)
        res = optimize_food_tour_route(req)
        self.assertIsInstance(res, RouteOptimizeResponse)
        self.assertTrue(len(res.stops) > 0)
        self.assertIsNotNone(res.ordered_stops)
        self.assertEqual(len(res.stops), len(res.ordered_stops))
        self.assertEqual(res.stops[0].id, res.ordered_stops[0].id)

if __name__ == '__main__':
    unittest.main()
