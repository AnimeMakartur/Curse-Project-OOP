#include "TravelSystem.h"

#include "../DataBase/DataLoader.h"
#include "Algorithms.h"

namespace travel {

TravelSystem::TravelSystem() : currentPlan(nullptr), hasTourist(false) {}

TravelSystem::~TravelSystem() {
    DataLoader::clearCatalog(catalog);
    delete currentPlan;
}

bool TravelSystem::loadData(const std::string& filename, std::string& error) {
    bool ok = DataLoader::load(filename, catalog, routes, error);
    delete currentPlan;
    currentPlan = nullptr;
    return ok;
}

void TravelSystem::setTouristProfile(const Tourist& t) {
    currentTourist = t;
    hasTourist = true;
}

const Tourist& TravelSystem::getTourist() const { return currentTourist; }
bool TravelSystem::hasProfile() const { return hasTourist; }

std::vector<TouristDestination*> TravelSystem::filterDestinations() {
    if (!hasTourist) return {};
    // Первинна фільтрація на повний денний бюджет/час і стартову годину дня
    return algorithms::linearFilter(catalog, currentTourist, DAY_START_HOUR,
                                    currentTourist.getDailyBudget(),
                                    currentTourist.getDailyTimeLimit());
}

void TravelSystem::sortDestinations(std::vector<TouristDestination*>& list) {
    if (hasTourist) {
        for (TouristDestination* dest : list) {
            dest->calculateRelevance(currentTourist, weightRating, weightTags, weightCost);
        }
    }
    algorithms::sortByRelevance(list);
}

TravelPlan TravelSystem::generatePersonalizedPlan() {
    TravelPlan plan(hasTourist ? currentTourist : Tourist());
    if (!hasTourist) return plan;

    // 1. Фільтрація каталогу (лінійний пошук)
    std::vector<TouristDestination*> candidates = filterDestinations();
    // 2. Розрахунок релевантності та 3. сортування за нею
    sortDestinations(candidates);

    // Жадібний розподіл об'єктів по днях з динамічним перерахунком залишків
    std::vector<bool> visited(catalog.size(), false);
    auto indexOf = [&](const TouristDestination* d) -> size_t {
        for (size_t i = 0; i < catalog.size(); ++i)
            if (catalog[i] == d) return i;
        return catalog.size();
    };

    for (int day = 1; day <= currentTourist.getTripDays(); ++day) {
        double budgetLeft = currentTourist.getDailyBudget();
        double timeLeft = currentTourist.getDailyTimeLimit();
        double currentHour = DAY_START_HOUR;
        int currentId = -1; // вершина, у якій перебуває турист на початку кроку

        for (TouristDestination* dest : candidates) {
            size_t idx = indexOf(dest);
            if (idx < visited.size() && visited[idx]) continue;
            if (!dest->isOpen(currentHour)) continue;
            if (dest->getCost() > budgetLeft) continue;
            if (dest->getVisitDuration() > timeLeft) continue;

            std::vector<Route> path;
            double travelTime = 0.0;
            double travelCost = 0.0;
            if (currentId != -1) {
                path = findShortestPath(currentId, dest->getId());
                if (path.empty()) continue; // вершина недосяжна — пропускаємо
                for (const Route& r : path) {
                    travelTime += r.getTravelTime();
                    travelCost += r.getTransportCost();
                }
                if (travelTime + dest->getVisitDuration() > timeLeft) continue;
                if (travelCost + dest->getCost() > budgetLeft) continue;
            }

            // Крок дня: об'єкт + маршрут, яким до нього дійшли
            Route arrivalRoute = path.empty() ? Route() : path.back();
            plan.addDayStep(day, *dest, arrivalRoute);

            budgetLeft -= dest->getCost() + travelCost;
            timeLeft -= dest->getVisitDuration() + travelTime;
            currentHour += dest->getVisitDuration() + travelTime;
            currentId = dest->getId();
            if (idx < visited.size()) visited[idx] = true;
        }
    }

    plan.calculateTotalMetrics();
    delete currentPlan;
    currentPlan = new TravelPlan(plan);
    return plan;
}

std::vector<Route> TravelSystem::findShortestPath(int startId, int endId) {
    return algorithms::dijkstra(routes, startId, endId);
}

const TravelPlan* TravelSystem::getCurrentPlan() const { return currentPlan; }
size_t TravelSystem::getCatalogSize() const { return catalog.size(); }
size_t TravelSystem::getRoutesCount() const { return routes.size(); }

} // namespace travel
