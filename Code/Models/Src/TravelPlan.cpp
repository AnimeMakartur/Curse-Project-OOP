#include "TravelPlan.h"

namespace travel {

TravelPlan::TravelPlan()
    : tourist(), totalCost(0.0), totalDuration(0.0), totalTravelTime(0.0), totalVisitTime(0.0) {}

TravelPlan::TravelPlan(const Tourist& tourist)
    : tourist(tourist), totalCost(0.0), totalDuration(0.0), totalTravelTime(0.0),
      totalVisitTime(0.0) {}

void TravelPlan::addDayStep(int day, const TouristDestination& dest,
                            const std::vector<PathStep>& transfers) {

    if (day < 1)
        day = 1;
    size_t index = static_cast<size_t>(day - 1);
    if (days.size() < index + 1)
        days.resize(index + 1);

    DayItem item;
    item.destination = const_cast<TouristDestination*>(&dest);
    item.transfers = transfers;
    days[index].push_back(item);
}

void TravelPlan::addDayStep(int day, const TouristDestination& dest) {

    addDayStep(day, dest, std::vector<PathStep>());
}

void TravelPlan::calculateTotalMetrics() {

    totalCost = 0.0;
    totalDuration = 0.0;
    totalTravelTime = 0.0;
    totalVisitTime = 0.0;
    for (const auto& dayItems : days) {
        for (const DayItem& item : dayItems) {
            if (item.destination) {
                totalCost += item.destination->getCost();
                totalVisitTime += item.destination->getVisitDuration();
            }
            for (const PathStep& step : item.transfers) {
                totalCost += step.cost;
                totalTravelTime += step.timeHours;
            }
        }
    }
    totalDuration = totalVisitTime + totalTravelTime;
}

const Tourist& TravelPlan::getTourist() const { return tourist; }
double TravelPlan::getTotalCost() const { return totalCost; }
double TravelPlan::getTotalDuration() const { return totalDuration; }
double TravelPlan::getTotalTravelTime() const { return totalTravelTime; }
double TravelPlan::getTotalVisitTime() const { return totalVisitTime; }
double TravelPlan::getRemainingBudget() const { return tourist.getTotalBudget() - totalCost; }
const std::vector<std::vector<DayItem>>& TravelPlan::getDays() const { return days; }

} // namespace travel
