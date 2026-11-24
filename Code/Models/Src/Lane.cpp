#include "Lane.h"

namespace travel {

std::string laneTypeToString(LaneType type) {
    switch (type) {
    case LaneType::Sidewalk:
        return "sidewalk";
    case LaneType::BikeLane:
        return "bike_lane";
    case LaneType::CarLane:
        return "car_lane";
    case LaneType::BusLane:
        return "bus_lane";
    case LaneType::Metrobus:
        return "metrobus";
    case LaneType::TramLine:
        return "tram_line";
    case LaneType::SuburbanRail:
        return "suburban_rail";
    case LaneType::Railway:
        return "railway";
    }
    return "sidewalk";
}

std::string laneTypeToUkr(LaneType type) {
    switch (type) {
    case LaneType::Sidewalk:
        return "sidewalk";
    case LaneType::BikeLane:
        return "bike lane";
    case LaneType::CarLane:
        return "car lane";
    case LaneType::BusLane:
        return "dedicated bus lane";
    case LaneType::Metrobus:
        return "metrobus line";
    case LaneType::TramLine:
        return "express tram";
    case LaneType::SuburbanRail:
        return "suburban train";
    case LaneType::Railway:
        return "city railway";
    }
    return "sidewalk";
}

std::string laneTypeTransportUkr(LaneType type) {
    switch (type) {
    case LaneType::Sidewalk:
        return "On foot (sidewalk)";
    case LaneType::BikeLane:
        return "Bicycle (bike lane)";
    case LaneType::CarLane:
        return "Car (general lane)";
    case LaneType::BusLane:
        return "Bus (dedicated bus lane)";
    case LaneType::Metrobus:
        return "Metrobus (BRT)";
    case LaneType::TramLine:
        return "Express tram";
    case LaneType::SuburbanRail:
        return "Suburban train";
    case LaneType::Railway:
        return "City railway";
    }
    return "On foot (sidewalk)";
}

bool laneTypeFromString(const std::string& text, LaneType& out) {
    if (text == "sidewalk" || text == "тротуар") {
        out = LaneType::Sidewalk;
        return true;
    }
    if (text == "bike_lane" || text == "велодоріжка" || text == "велосипедна доріжка") {
        out = LaneType::BikeLane;
        return true;
    }
    if (text == "car_lane" || text == "автомобільна смуга" || text == "автомобільна дорога") {
        out = LaneType::CarLane;
        return true;
    }
    if (text == "bus_lane" || text == "автобусна смуга" || text == "виділена автобусна смуга") {
        out = LaneType::BusLane;
        return true;
    }
    if (text == "metrobus" || text == "метробус" || text == "brt" || text == "лінія метробуса") {
        out = LaneType::Metrobus;
        return true;
    }
    if (text == "tram_line" || text == "трамвайна лінія" || text == "швидкісний трамвай" ||
        text == "відокремлена лінія трамвая") {
        out = LaneType::TramLine;
        return true;
    }
    if (text == "suburban_rail" || text == "приміська електричка" || text == "електричка") {
        out = LaneType::SuburbanRail;
        return true;
    }
    if (text == "railway" || text == "залізниця" || text == "залізнична колія" ||
        text == "міська залізниця") {
        out = LaneType::Railway;
        return true;
    }
    return false;
}

double laneTypeDefaultBaseSpeed(LaneType type) {
    switch (type) {
    case LaneType::Sidewalk:
        return 5.0;
    case LaneType::BikeLane:
        return 15.0;
    case LaneType::CarLane:
        return 30.0; // рух у загальному потоці (затори)
    case LaneType::BusLane:
        return 30.0;
    case LaneType::Metrobus:
        return 40.0;
    case LaneType::TramLine:
        return 35.0;
    case LaneType::SuburbanRail:
        return 70.0;
    case LaneType::Railway:
        return 90.0;
    }
    return 5.0;
}

double laneTypeDefaultSpeedMultiplier(LaneType type) {
    switch (type) {
    case LaneType::Sidewalk:
        return 1.0;
    case LaneType::BikeLane:
        return 1.0;
    case LaneType::CarLane:
        return 1.0;
    case LaneType::BusLane:
        return 1.3; // бонус виділеної смуги
    case LaneType::Metrobus:
        return 1.5; // високий пріоритет BRT
    case LaneType::TramLine:
        return 1.6; // без заторів
    case LaneType::SuburbanRail:
        return 1.4;
    case LaneType::Railway:
        return 1.6; // максимальна швидкість
    }
    return 1.0;
}

double laneTypeDefaultCost(LaneType type) {
    switch (type) {
    case LaneType::Sidewalk:
        return 0.0;
    case LaneType::BikeLane:
        return 0.0;
    case LaneType::CarLane:
        return 0.0; // власне авто / безкоштовно
    case LaneType::BusLane:
        return 0.30;
    case LaneType::Metrobus:
        return 0.40;
    case LaneType::TramLine:
        return 0.30;
    case LaneType::SuburbanRail:
        return 0.60;
    case LaneType::Railway:
        return 0.90;
    }
    return 0.0;
}

double laneTypeDefaultWaitHours(LaneType type) {
    switch (type) {
    case LaneType::Sidewalk:
        return 0.0;
    case LaneType::BikeLane:
        return 0.0;
    case LaneType::CarLane:
        return 0.0;
    case LaneType::BusLane:
        return 0.15; // ~9 хв
    case LaneType::Metrobus:
        return 0.10; // ~6 хв
    case LaneType::TramLine:
        return 0.12; // ~7 хв
    case LaneType::SuburbanRail:
        return 0.25; // ~15 хв
    case LaneType::Railway:
        return 0.30; // ~18 хв
    }
    return 0.0;
}

Lane::Lane() : Lane(LaneType::Sidewalk) {}

Lane::Lane(LaneType laneType, const std::string& name)
    : type(laneType), routeName(name), speedMultiplier(laneTypeDefaultSpeedMultiplier(laneType)),
      baseSpeedKmh(laneTypeDefaultBaseSpeed(laneType)), cost(laneTypeDefaultCost(laneType)),
      waitTimeHours(laneTypeDefaultWaitHours(laneType)) {}

Lane::Lane(LaneType laneType, const std::string& name, double mult, double baseSpeed,
           double laneCost, double waitHours)
    : type(laneType), routeName(name), speedMultiplier(mult), baseSpeedKmh(baseSpeed),
      cost(laneCost), waitTimeHours(waitHours) {}

double Lane::travelTimeHours(double distanceKm) const {
    double speed = effectiveSpeedKmh();
    if (speed <= 0.0)
        speed = 1.0; // захист від ділення на нуль
    return distanceKm / speed + waitTimeHours;
}

std::string Lane::describe() const {
    std::string result = laneTypeTransportUkr(type);
    if (!routeName.empty())
        result += " «" + routeName + "»";
    return result;
}

} // namespace travel
