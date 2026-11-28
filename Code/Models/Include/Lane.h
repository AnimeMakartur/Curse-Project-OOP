#pragma once

#include <string>

namespace travel {

// Тип смуги руху / лінії транспорту. Порядок значень — int-індекси, що йдуть у C API;
// рядкові ключі, українські назви та дефолти — на боці Python (View/lane_types.py).
enum class LaneType {
    Sidewalk = 0,    // sidewalk
    BikeLane = 1,    // bike_lane
    CarLane = 2,     // car_lane
    BusLane = 3,     // bus_lane
    Metrobus = 4,    // metrobus
    TramLine = 5,    // tram_line
    SuburbanRail = 6, // suburban_rail
    Railway = 7      // railway
};

// Одна смуга/лінія дороги: тип, назва маршруту, швидкісні параметри, вартість, очікування.
struct Lane {

    LaneType type = LaneType::Sidewalk;
    std::string routeName;
    double speedMultiplier = 1.0;
    double baseSpeedKmh = 5.0;
    double cost = 0.0;
    double waitTimeHours = 0.0;

    Lane() = default;
    Lane(LaneType laneType, const std::string& name, double mult, double baseSpeed,
         double laneCost, double waitHours)
        : type(laneType), routeName(name), speedMultiplier(mult), baseSpeedKmh(baseSpeed),
          cost(laneCost), waitTimeHours(waitHours) {}

    // Час переміщення цією смугою на відстань distanceKm:
    //   t = distanceKm / (baseSpeedKmh * speedMultiplier) + waitTimeHours
    double travelTimeHours(double distanceKm) const;
    double effectiveSpeedKmh() const { return baseSpeedKmh * speedMultiplier; }
    bool isAffordable(double remainingBudget) const { return cost <= remainingBudget; }
};

} // namespace travel
