#include "Route.h"

#include <algorithm>
#include <limits>

namespace travel {

Route::Route() : cityId(0), fromId(0), toId(0), distanceKm(0.0) {}

Route::Route(int cityId, int fromId, int toId, double distanceKm,
             const std::vector<Lane>& lanes)
    : cityId(cityId), fromId(fromId), toId(toId),
      distanceKm(distanceKm), lanes(lanes) {}

int Route::getCityId() const { return cityId; }
int Route::getFromId() const { return fromId; }
int Route::getToId() const { return toId; }
double Route::getDistance() const { return distanceKm; }

const std::vector<Lane>& Route::getLanes() const { return lanes; }

void Route::setLanes(const std::vector<Lane>& newLanes) { lanes = newLanes; }

std::vector<std::string> Route::getLaneNames() const {
    std::vector<std::string> names;
    names.reserve(lanes.size());
    for (const Lane& lane : lanes) names.push_back(laneTypeToUkr(lane.type));
    return names;
}

std::string Route::getRoadDescription() const {
    std::string result;
    for (size_t i = 0; i < lanes.size(); ++i) {
        if (i > 0) result += ", ";
        result += lanes[i].describe();
    }
    if (result.empty()) result = Lane(LaneType::Sidewalk).describe();
    return result;
}

bool Route::hasAffordableLane(double remainingBudget) const {
    if (lanes.empty()) return true; // порожній набір = тротуар (безкоштовно)
    for (const Lane& lane : lanes) {
        if (lane.isAffordable(remainingBudget)) return true;
    }
    return false;
}

Lane Route::chooseBestLane(double remainingBudget) const {
    if (lanes.empty()) return Lane(LaneType::Sidewalk);

    const Lane* best = nullptr;
    const Lane* cheapest = nullptr;
    for (const Lane& lane : lanes) {
        if (!cheapest || lane.cost < cheapest->cost) cheapest = &lane;
        if (!lane.isAffordable(remainingBudget)) continue;
        if (!best || lane.travelTimeHours(distanceKm) < best->travelTimeHours(distanceKm)) {
            best = &lane;
        }
    }
    // Якщо жодна смуга не вписується в бюджет — найдешевша (зазвичай пішки, 0 EUR).
    return best ? *best : (cheapest ? *cheapest : Lane(LaneType::Sidewalk));
}

double Route::optimalTravelTimeHours(double remainingBudget) const {
    return chooseBestLane(remainingBudget).travelTimeHours(distanceKm);
}

double Route::optimalCost(double remainingBudget) const {
    return chooseBestLane(remainingBudget).cost;
}

double Route::getTravelTime() const {
    return optimalTravelTimeHours(std::numeric_limits<double>::infinity());
}

double Route::getTransportCost() const {
    return optimalCost(std::numeric_limits<double>::infinity());
}

} // namespace travel
