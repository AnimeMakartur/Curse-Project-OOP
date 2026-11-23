#pragma once

#include <string>

namespace travel {

// Тип смуги руху / лінії громадського транспорту на ділянці дороги.
enum class LaneType {
    Sidewalk,      // sidewalk       — пішохідний тротуар
    BikeLane,      // bike_lane      — велодоріжка
    CarLane,       // car_lane       — загальна автомобільна смуга
    BusLane,       // bus_lane       — виділена автобусна смуга (бонус до швидкості)
    Metrobus,      // metrobus       — лінія метробуса / BRT (високий пріоритет)
    TramLine,      // tram_line      — швидкісний / відокремлений трамвай
    SuburbanRail,  // suburban_rail  — приміська електричка
    Railway        // railway        — міська залізниця (макс. швидкість на великі дистанції)
};

std::string laneTypeToString(LaneType type);          // canonical JSON-ім'я: "tram_line" тощо
std::string laneTypeToUkr(LaneType type);             // коротка назва: "швидкісний трамвай"
std::string laneTypeTransportUkr(LaneType type);      // опис виду транспорту: "Швидкісний трамвай"
bool laneTypeFromString(const std::string& text, LaneType& out);

// Базові параметри смуги за замовчуванням (можуть перевизначатися у JSON).
double laneTypeDefaultBaseSpeed(LaneType type);       // базова швидкість, км/год
double laneTypeDefaultSpeedMultiplier(LaneType type); // коефіцієнт приросту швидкості k_speed
double laneTypeDefaultCost(LaneType type);            // вартість проїзду, грн
double laneTypeDefaultWaitHours(LaneType type);       // середній час очікування транспорту, год

// Одна смуга/лінія дороги: тип, назва маршруту, швидкісні параметри, вартість, очікування.
struct Lane {
    LaneType type = LaneType::Sidewalk;
    std::string routeName;        // опціонально: "Трамвай №8", "Метробус М1"
    double speedMultiplier = 1.0; // k_speed(l)
    double baseSpeedKmh = 5.0;    // v_base, км/год
    double cost = 0.0;            // вартість проїзду, грн
    double waitTimeHours = 0.0;   // t_wait, год

    Lane();
    explicit Lane(LaneType laneType, const std::string& name = "");
    Lane(LaneType laneType, const std::string& name,
         double speedMultiplier, double baseSpeedKmh,
         double cost, double waitTimeHours);

    // Час переміщення цією смугою/лінією на відстань distanceKm:
    //   t = distanceKm / (baseSpeedKmh * speedMultiplier) + waitTimeHours
    double travelTimeHours(double distanceKm) const;
    double effectiveSpeedKmh() const { return baseSpeedKmh * speedMultiplier; }
    bool isAffordable(double remainingBudget) const { return cost <= remainingBudget; }

    // Людиночитний опис: напр. "Швидкісний трамвай «Трамвай №8»"
    std::string describe() const;
};

} // namespace travel
