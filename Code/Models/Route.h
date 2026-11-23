#pragma once

#include <string>
#include <vector>

namespace travel {

// Тип смуги дороги.
// Доповнення до діаграми класів: ребро графа (Route) зберігає дорогу
// як масив полос, де для кожної полоси задано її тип.
enum class LaneType {
    Sidewalk,  // тротуар
    BikeLane,  // велосипедна доріжка
    CarLane,   // автомобільна смуга
    BusLane,   // автобусна смуга
    TramLine,  // відокремлена лінія трамвая
    Railway    // залізнична колія
};

std::string laneTypeToString(LaneType type);
std::string laneTypeToUkr(LaneType type);
bool laneTypeFromString(const std::string& text, LaneType& out);

// Ребро транспортно-пішохідного графа (маршрут між туристичними об'єктами).
class Route {
private:
    int fromId;
    int toId;
    double distanceKm;
    double travelTimeHours;
    double transportCost;
    double dailyTimeLimit;
    // Дорога у вигляді масиву: кожен елемент — тип відповідної полоси
    // (тротуар, велодоріжка, автобусна смуга, лінія трамвая, залізниця).
    std::vector<LaneType> lanes;

public:
    Route();
    Route(int fromId, int toId, double distanceKm, double travelTimeHours,
          double transportCost, double dailyTimeLimit,
          const std::vector<LaneType>& lanes = {});

    int getFromId() const;
    int getToId() const;
    double getDistance() const;
    double getTravelTime() const;
    double getTransportCost() const;
    double getDailyTimeLimit() const;

    const std::vector<LaneType>& getLanes() const;
    std::vector<std::string> getLaneNames() const;      // назви типів полос
    std::string getRoadDescription() const;             // людиночитний опис дороги
    void setLanes(const std::vector<LaneType>& newLanes);
};

} // namespace travel
