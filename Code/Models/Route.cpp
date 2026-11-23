#include "Route.h"

namespace travel {

std::string laneTypeToString(LaneType type) {
    switch (type) {
        case LaneType::Sidewalk: return "sidewalk";
        case LaneType::BikeLane: return "bike_lane";
        case LaneType::CarLane:  return "car_lane";
        case LaneType::BusLane:  return "bus_lane";
        case LaneType::TramLine: return "tram_line";
        case LaneType::Railway:  return "railway";
    }
    return "sidewalk";
}

std::string laneTypeToUkr(LaneType type) {
    switch (type) {
        case LaneType::Sidewalk: return "тротуар";
        case LaneType::BikeLane: return "велосипедна доріжка";
        case LaneType::CarLane:  return "автомобільна смуга";
        case LaneType::BusLane:  return "автобусна смуга";
        case LaneType::TramLine: return "відокремлена лінія трамвая";
        case LaneType::Railway:  return "залізнична колія";
    }
    return "тротуар";
}

bool laneTypeFromString(const std::string& text, LaneType& out) {
    if (text == "sidewalk" || text == "тротуар") { out = LaneType::Sidewalk; return true; }
    if (text == "bike_lane" || text == "велосипедна доріжка" || text == "велодоріжка") { out = LaneType::BikeLane; return true; }
    if (text == "car_lane" || text == "автомобільна смуга" || text == "автомобільна дорога") { out = LaneType::CarLane; return true; }
    if (text == "bus_lane" || text == "автобусна смуга") { out = LaneType::BusLane; return true; }
    if (text == "tram_line" || text == "відокремлена лінія трамвая" || text == "трамвайна лінія") { out = LaneType::TramLine; return true; }
    if (text == "railway" || text == "залізнична колія" || text == "залізниця") { out = LaneType::Railway; return true; }
    return false;
}

Route::Route()
    : fromId(0), toId(0), distanceKm(0.0), travelTimeHours(0.0),
      transportCost(0.0), dailyTimeLimit(0.0) {}

Route::Route(int fromId, int toId, double distanceKm, double travelTimeHours,
             double transportCost, double dailyTimeLimit,
             const std::vector<LaneType>& lanes)
    : fromId(fromId), toId(toId), distanceKm(distanceKm),
      travelTimeHours(travelTimeHours), transportCost(transportCost),
      dailyTimeLimit(dailyTimeLimit), lanes(lanes) {}

int Route::getFromId() const { return fromId; }
int Route::getToId() const { return toId; }
double Route::getDistance() const { return distanceKm; }
double Route::getTravelTime() const { return travelTimeHours; }
double Route::getTransportCost() const { return transportCost; }
double Route::getDailyTimeLimit() const { return dailyTimeLimit; }

const std::vector<LaneType>& Route::getLanes() const { return lanes; }

std::vector<std::string> Route::getLaneNames() const {
    std::vector<std::string> names;
    names.reserve(lanes.size());
    for (LaneType lane : lanes) names.push_back(laneTypeToUkr(lane));
    return names;
}

std::string Route::getRoadDescription() const {
    std::string result;
    for (size_t i = 0; i < lanes.size(); ++i) {
        if (i > 0) result += ", ";
        result += laneTypeToUkr(lanes[i]);
    }
    if (result.empty()) result = "пішохідний перехід";
    return result;
}

void Route::setLanes(const std::vector<LaneType>& newLanes) { lanes = newLanes; }

} // namespace travel
