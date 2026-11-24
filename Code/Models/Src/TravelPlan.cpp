#include "TravelPlan.h"

#include <sstream>

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

std::string TravelPlan::exportPlanSummary() const {
    std::ostringstream out;
    out << "=== Personalized travel plan for " << tourist.getName()
        << " (city id=" << tourist.getTargetCityId() << ") ===\n";
    out << "Daily budget: " << tourist.getDailyBudget()
        << " EUR, total budget: " << tourist.getTotalBudget()
        << " EUR, days: " << tourist.getTripDays() << "\n\n";

    for (size_t day = 0; day < days.size(); ++day) {
        out << "Day " << (day + 1) << ":\n";
        const auto& items = days[day];
        if (items.empty()) {
            out << "  (free day)\n\n";
            continue;
        }
        for (size_t i = 0; i < items.size(); ++i) {
            const DayItem& item = items[i];
            for (const PathStep& step : item.transfers) {
                out << "  -> transfer " << step.route.getFromId() << " -> " << step.route.getToId()
                    << ": " << step.route.getDistance() << " km, " << step.timeHours << " h, "
                    << step.cost << " EUR — " << step.lane.describe() << "\n";
            }
            if (item.destination) {
                out << "  " << (i + 1) << ". " << item.destination->getName() << " ("
                    << item.destination->getType() << ", " << item.destination->getCost()
                    << " EUR, " << item.destination->getVisitDuration() << " h, rating "
                    << item.destination->getRating() << ")\n";
            }
        }
        out << "\n";
    }
    out << "Total: cost " << totalCost << " EUR (remaining budget " << getRemainingBudget()
        << " EUR), time on site " << totalVisitTime << " h, travel time " << totalTravelTime
        << " h, total " << totalDuration << " h.\n";
    return out.str();
}

const Tourist& TravelPlan::getTourist() const { return tourist; }
double TravelPlan::getTotalCost() const { return totalCost; }
double TravelPlan::getTotalDuration() const { return totalDuration; }
double TravelPlan::getTotalTravelTime() const { return totalTravelTime; }
double TravelPlan::getTotalVisitTime() const { return totalVisitTime; }
double TravelPlan::getRemainingBudget() const { return tourist.getTotalBudget() - totalCost; }
const std::vector<std::vector<DayItem>>& TravelPlan::getDays() const { return days; }

} // namespace travel
