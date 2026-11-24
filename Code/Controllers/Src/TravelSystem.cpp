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
    cities.clear();
    bool ok = DataLoader::load(filename, cities, catalog, routes, error);
    delete currentPlan;
    currentPlan = nullptr;
    return ok;
}
const std::vector<City>& TravelSystem::getCities() const { return cities; }
void TravelSystem::setTouristProfile(const Tourist& t) {
    currentTourist = t;
    hasTourist = true;
}
const Tourist& TravelSystem::getTourist() const { return currentTourist; }
bool TravelSystem::hasProfile() const { return hasTourist; }
int TravelSystem::activeCityId() const {
    return hasTourist ? currentTourist.getTargetCityId() : -1;
}
std::vector<TouristDestination*> TravelSystem::catalogForCity(int cityId) const {
    std::vector<TouristDestination*> result;
    for (TouristDestination* dest : catalog) {
        if (cityId < 0 || dest->getCityId() == cityId)
            result.push_back(dest);
    }
    return result;
}
std::vector<Route> TravelSystem::routesForCity(int cityId) const {
    std::vector<Route> result;
    for (const Route& route : routes) {
        if (cityId < 0 || route.getCityId() == cityId)
            result.push_back(route);
    }
    return result;
}
std::vector<TouristDestination*> TravelSystem::getCatalog(int cityId) const {
    return catalogForCity(cityId);
}
std::vector<Route> TravelSystem::getRoutes(int cityId) const { return routesForCity(cityId); }
std::vector<TouristDestination*> TravelSystem::filterDestinations() {
    if (!hasTourist)
        return {};
    // Каталог лише обраного міста — локації різних міст не змішуються.
    // Первинна фільтрація на повний денний бюджет/час і стартову годину дня.
    return algorithms::linearFilter(catalogForCity(activeCityId()), currentTourist, DAY_START_HOUR,
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
    if (!hasTourist)
        return plan;

    const int cityId = activeCityId();
    const std::vector<Route> cityRoutes = routesForCity(cityId);

    // 1. Фільтрація каталогу обраного міста (лінійний пошук)
    std::vector<TouristDestination*> candidates = filterDestinations();
    // 2. Розрахунок релевантності та 3. сортування за нею
    sortDestinations(candidates);

    // Жадібний розподіл об'єктів по днях з динамічним перерахунком залишків
    std::vector<bool> visited(catalog.size(), false);
    auto indexOf = [&](const TouristDestination* d) -> size_t {
        for (size_t i = 0; i < catalog.size(); ++i)
            if (catalog[i] == d)
                return i;
        return catalog.size();
    };

    for (int day = 1; day <= currentTourist.getTripDays(); ++day) {
        double budgetLeft = currentTourist.getDailyBudget();
        double timeLeft = currentTourist.getDailyTimeLimit();
        double currentHour = DAY_START_HOUR;
        int currentId = -1; // вершина, у якій перебуває турист на початку кроку

        for (TouristDestination* dest : candidates) {
            size_t idx = indexOf(dest);
            if (idx < visited.size() && visited[idx])
                continue;
            if (dest->getCost() > budgetLeft)
                continue;
            if (dest->getVisitDuration() > timeLeft)
                continue;
            if (!dest->isOpen(currentHour))
                continue;

            std::vector<PathStep> path;
            double travelTime = 0.0;
            double travelCost = 0.0;
            if (currentId != -1) {
                // Дейкстра лише по ребрах обраного міста, з поточним залишком бюджету:
                // на кожному ребрі автоматично обирається найшвидша доступна лінія.
                path = algorithms::dijkstra(cityRoutes, currentId, dest->getId(), budgetLeft);
                if (path.empty())
                    continue; // вершина недосяжна — пропускаємо
                for (const PathStep& step : path) {
                    travelTime += step.timeHours;
                    travelCost += step.cost;
                }
                if (travelTime + dest->getVisitDuration() > timeLeft)
                    continue;
                if (travelCost + dest->getCost() > budgetLeft)
                    continue;
            }

            // Пункт дня: об'єкт + деталізований шлях, яким до нього дійшли
            plan.addDayStep(day, *dest, path);

            budgetLeft -= dest->getCost() + travelCost;
            timeLeft -= dest->getVisitDuration() + travelTime;
            currentHour += dest->getVisitDuration() + travelTime;
            currentId = dest->getId();
            if (idx < visited.size())
                visited[idx] = true;
        }
    }

    plan.calculateTotalMetrics();
    delete currentPlan;
    currentPlan = new TravelPlan(plan);
    return plan;
}
std::vector<PathStep> TravelSystem::findShortestPath(int startId, int endId) {
    double budget = hasTourist ? currentTourist.getDailyBudget() : 0.0;
    return findShortestPath(startId, endId, activeCityId(), budget);
}
std::vector<PathStep> TravelSystem::findShortestPath(int startId, int endId, int cityId,
                                                     double remainingBudget) {
    return algorithms::dijkstra(routesForCity(cityId), startId, endId, remainingBudget);
}
const TravelPlan* TravelSystem::getCurrentPlan() const { return currentPlan; }
size_t TravelSystem::getCatalogSize() const { return catalog.size(); }
size_t TravelSystem::getRoutesCount() const { return routes.size(); }
size_t TravelSystem::getCitiesCount() const { return cities.size(); }

} // namespace travel
