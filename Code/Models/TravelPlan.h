#pragma once

#include <string>
#include <vector>

#include "PathStep.h"
#include "Route.h"
#include "Tourist.h"
#include "TouristDestination.h"

namespace travel {

// Один пункт дня у плані: об'єкт призначення + деталізований шлях до нього
// (переходи із зазначенням обраної смуги/лінії транспорту).
struct DayItem {
    TouristDestination* destination = nullptr;
    std::vector<PathStep> transfers; // як дістатися від попередньої точки (порожньо — старт дня)
};

// Сформований план подорожі: розклад по днях (об'єкти + маршрути між ними) та метрики.
class TravelPlan {
private:
    Tourist tourist;
    std::vector<std::vector<DayItem>> days; // [день (0-based)][пункти]
    double totalCost = 0.0;         // квитки + проїзд, EUR
    double totalDuration = 0.0;     // весь час плану, год
    double totalTravelTime = 0.0;   // час у дорозі, год
    double totalVisitTime = 0.0;    // час на локаціях, год

public:
    TravelPlan();
    explicit TravelPlan(const Tourist& tourist);

    // Додає пункт у день (day — 1-based): об'єкт та шлях, яким до нього дійшли
    void addDayStep(int day, const TouristDestination& dest, const std::vector<PathStep>& transfers);
    void addDayStep(int day, const TouristDestination& dest); // без переходу (старт дня)

    void calculateTotalMetrics();
    std::string exportPlanSummary() const;

    const Tourist& getTourist() const;
    double getTotalCost() const;
    double getTotalDuration() const;
    double getTotalTravelTime() const;
    double getTotalVisitTime() const;
    double getRemainingBudget() const; // totalBudget туриста - totalCost
    const std::vector<std::vector<DayItem>>& getDays() const;
};

} // namespace travel
