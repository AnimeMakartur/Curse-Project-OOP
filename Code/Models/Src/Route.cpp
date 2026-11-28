#include "Route.h"

#include <algorithm>
#include <limits>

namespace travel {

// Дефолтна смуга "пішки" для fallback-випадків (значення відповідають sidewalk у Python).
static Lane sidewalkFallback() {

    return Lane(LaneType::Sidewalk, "", 1.0, 5.0, 0.0, 0.0);
}

Route::Route() : cityId(0), fromId(0), toId(0), distanceKm(0.0) {}

Route::Route(int cityId, int fromId, int toId, double distanceKm, const std::vector<Lane>& lanes)
    : cityId(cityId), fromId(fromId), toId(toId), distanceKm(distanceKm), lanes(lanes) {}

int Route::getCityId() const { return cityId; }
int Route::getFromId() const { return fromId; }
int Route::getToId() const { return toId; }
double Route::getDistance() const { return distanceKm; }

const std::vector<Lane>& Route::getLanes() const { return lanes; }

void Route::setLanes(const std::vector<Lane>& newLanes) { lanes = newLanes; }

bool Route::hasAffordableLane(double remainingBudget, bool allowCar) const {

    if (lanes.empty())
        return true; // порожній набір = тротуар (безкоштовно)
    for (const Lane& lane : lanes) {
        if (!allowCar && lane.type == LaneType::CarLane)
            continue;
        if (lane.isAffordable(remainingBudget))
            return true;
    }
    return false;
}

Lane Route::chooseBestLane(double remainingBudget, bool allowCar) const {

    if (lanes.empty())
        return sidewalkFallback();

    const Lane* best = nullptr;
    const Lane* cheapest = nullptr;
    for (const Lane& lane : lanes) {
        if (!allowCar && lane.type == LaneType::CarLane)
            continue;
        if (!cheapest || lane.cost < cheapest->cost)
            cheapest = &lane;
        if (!lane.isAffordable(remainingBudget))
            continue;
        if (!best || lane.travelTimeHours(distanceKm) < best->travelTimeHours(distanceKm)) {
            best = &lane;
        }
    }
    // Якщо жодна смуга не вписується в бюджет — найдешевша (зазвичай пішки, 0 EUR).
    return best ? *best : (cheapest ? *cheapest : sidewalkFallback());
}

double Route::optimalTravelTimeHours(double remainingBudget, bool allowCar) const {

    return chooseBestLane(remainingBudget, allowCar).travelTimeHours(distanceKm);
}

double Route::optimalCost(double remainingBudget, bool allowCar) const {

    return chooseBestLane(remainingBudget, allowCar).cost;
}

double Route::getTravelTime() const {

    return optimalTravelTimeHours(std::numeric_limits<double>::infinity());
}

double Route::getTransportCost() const {

    return optimalCost(std::numeric_limits<double>::infinity());
}

} // namespace travel
