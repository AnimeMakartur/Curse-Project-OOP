#include "TravelPlan.h"

#include <sstream>

namespace travel {

TravelPlan::TravelPlan() : totalCost(0.0), totalDuration(0.0) {}

TravelPlan::TravelPlan(const Tourist& tourist)
    : tourist(tourist), totalCost(0.0), totalDuration(0.0) {}

void TravelPlan::addDayStep(int day, const TouristDestination& dest, const Route& route) {
    if (day < 1) day = 1;
    size_t index = static_cast<size_t>(day - 1);
    if (dailyDestinations.size() < index + 1) {
        dailyDestinations.resize(index + 1);
        dailyRoutes.resize(index + 1);
    }
    dailyDestinations[index].push_back(const_cast<TouristDestination*>(&dest));
    dailyRoutes[index].push_back(route);
}

void TravelPlan::calculateTotalMetrics() {
    totalCost = 0.0;
    totalDuration = 0.0;
    for (const auto& dayDests : dailyDestinations) {
        for (const TouristDestination* dest : dayDests) {
            totalCost += dest->getCost();
            totalDuration += dest->getVisitDuration();
        }
    }
    for (const auto& dayRoutes : dailyRoutes) {
        for (const Route& route : dayRoutes) {
            totalCost += route.getTransportCost();
            totalDuration += route.getTravelTime();
        }
    }
}

std::string TravelPlan::exportPlanSummary() const {
    std::ostringstream out;
    out << "=== Персоналізований туристичний план для " << tourist.getName() << " ===\n";
    out << "Бюджет на день: " << tourist.getDailyBudget()
        << " грн, загальний бюджет: " << tourist.getTotalBudget()
        << " грн, днів: " << tourist.getTripDays() << "\n\n";

    for (size_t day = 0; day < dailyDestinations.size(); ++day) {
        out << "День " << (day + 1) << ":\n";
        const auto& dests = dailyDestinations[day];
        const auto& routes = dailyRoutes[day];
        for (size_t i = 0; i < dests.size(); ++i) {
            out << "  " << (i + 1) << ". " << dests[i]->getName()
                << " (" << dests[i]->getType() << ", " << dests[i]->getCost() << " грн, "
                << dests[i]->getVisitDuration() << " год, рейтинг "
                << dests[i]->getRating() << ")\n";
            if (i < routes.size() && routes[i].getFromId() != routes[i].getToId()) {
                out << "     маршрут: " << routes[i].getFromId() << " -> "
                    << routes[i].getToId() << ", " << routes[i].getDistance() << " км, "
                    << routes[i].getTravelTime() << " год, "
                    << routes[i].getTransportCost() << " грн; дорога: "
                    << routes[i].getRoadDescription() << "\n";
            }
        }
        if (dests.empty()) out << "  (вільний день)\n";
        out << "\n";
    }
    out << "Разом: вартість " << totalCost << " грн, тривалість "
        << totalDuration << " год.\n";
    return out.str();
}

const Tourist& TravelPlan::getTourist() const { return tourist; }
double TravelPlan::getTotalCost() const { return totalCost; }
double TravelPlan::getTotalDuration() const { return totalDuration; }
const std::vector<std::vector<TouristDestination*>>& TravelPlan::getDailyDestinations() const {
    return dailyDestinations;
}
const std::vector<std::vector<Route>>& TravelPlan::getDailyRoutes() const {
    return dailyRoutes;
}

} // namespace travel
