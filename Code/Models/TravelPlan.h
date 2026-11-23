#pragma once

#include <string>
#include <vector>

#include "Route.h"
#include "Tourist.h"
#include "TouristDestination.h"

namespace travel {

// Сформований план подорожі: розклад по днях (об'єкти + маршрути між ними).
class TravelPlan {
private:
    Tourist tourist;
    std::vector<std::vector<TouristDestination*>> dailyDestinations; // [день][об'єкти]
    std::vector<std::vector<Route>> dailyRoutes;                     // [день][ребра графа]
    double totalCost;
    double totalDuration;

public:
    TravelPlan();
    explicit TravelPlan(const Tourist& tourist);

    // Додає крок у день (day — 1-based): об'єкт та маршрут, яким до нього дійшли
    void addDayStep(int day, const TouristDestination& dest, const Route& route);
    void calculateTotalMetrics();
    std::string exportPlanSummary() const;

    const Tourist& getTourist() const;
    double getTotalCost() const;
    double getTotalDuration() const;
    const std::vector<std::vector<TouristDestination*>>& getDailyDestinations() const;
    const std::vector<std::vector<Route>>& getDailyRoutes() const;
};

} // namespace travel
