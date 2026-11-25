#include "Algorithms.h"

#include <algorithm>
#include <limits>
#include <map>
#include <queue>
#include <utility>

namespace travel {
namespace algorithms {

std::vector<TouristDestination*> linearFilter(const std::vector<TouristDestination*>& catalog,
                                              const Tourist& tourist, double currentHour,
                                              double remainingBudget, double remainingTime) {
    std::vector<TouristDestination*> result;
    std::vector<std::string> interests = tourist.getInterests();

    // Послідовний перегляд кожного елемента каталогу — лінійний пошук O(n)
    for (TouristDestination* dest : catalog) {
        if (!dest)
            continue;

        // I(c_i <= B_rem) — вартість вписується у залишок бюджету
        bool budgetOk = dest->getCost() <= remainingBudget;
        // I(t_i + t_travel <= T_rem) — спрощено: час огляду вписується у залишок часу
        bool timeOk = dest->getVisitDuration() <= remainingTime;
        // I(T_open <= t_curr <= T_close) — об'єкт відкритий
        bool openOk = dest->isOpen(currentHour);
        // I(Tags_i ∩ U_tags ≠ ∅) — є спільні теги з інтересами туриста
        bool tagsOk = false;
        for (const std::string& tag : dest->getTags()) {
            if (std::find(interests.begin(), interests.end(), tag) != interests.end()) {
                tagsOk = true;
                break;
            }
        }

        if (budgetOk && timeOk && openOk && tagsOk) {
            result.push_back(dest);
        }
    }
    return result;
}

void sortByRelevance(std::vector<TouristDestination*>& list) {
    std::sort(list.begin(), list.end(),
              [](const TouristDestination* a, const TouristDestination* b) {
                  return a->getRelevance() > b->getRelevance(); // за спаданням S_i
              });
}

std::vector<PathStep> dijkstra(const std::vector<Route>& routes, int startId, int endId,
                               double remainingBudget, bool allowCar) {
    std::vector<PathStep> emptyPath;
    if (startId == endId)
        return emptyPath;

    // Список суміжності: вершина -> (сусід, індекс ребра)
    std::map<int, std::vector<std::pair<int, size_t>>> adjacency;
    for (size_t i = 0; i < routes.size(); ++i) {
        adjacency[routes[i].getFromId()].push_back({routes[i].getToId(), i});
        adjacency[routes[i].getToId()].push_back({routes[i].getFromId(), i}); // неорієнтований граф
    }

    const double INF = std::numeric_limits<double>::infinity();
    std::map<int, double> dist;
    std::map<int, int> prevVertex;
    std::map<int, PathStep> prevStep;
    for (const auto& entry : adjacency)
        dist[entry.first] = INF;
    dist[startId] = 0.0;

    // Черга з пріоритетом (min-heap) за поточною оцінкою d[v]
    using QueueItem = std::pair<double, int>; // (d[u], вершина)
    std::priority_queue<QueueItem, std::vector<QueueItem>, std::greater<QueueItem>> queue;
    queue.push({0.0, startId});

    while (!queue.empty()) {
        auto [currentDist, u] = queue.top();
        queue.pop();
        if (currentDist > dist[u])
            continue; // застарілий запис у черзі
        if (u == endId)
            break;

        auto it = adjacency.find(u);
        if (it == adjacency.end())
            continue;
        for (const auto& [v, edgeIndex] : it->second) {
            const Route& route = routes[edgeIndex];
            // Пропускаємо ребро, якщо жодна його смуга/лінія не вписується в бюджет
            if (!route.hasAffordableLane(remainingBudget, allowCar))
                continue;
            // Автоматичний вибір оптимальної лінії/смуги з мінімальним часом переходу
            PathStep step(route, route.chooseBestLane(remainingBudget, allowCar));
            double w = step.timeHours; // вага ребра — мінімальний час переміщення
            // Релаксація: d[v] = min(d[v], d[u] + w(u, v))
            if (dist[u] + w < dist[v]) {
                dist[v] = dist[u] + w;
                prevVertex[v] = u;
                prevStep[v] = step;
                queue.push({dist[v], v});
            }
        }
    }

    if (dist.find(endId) == dist.end() || dist[endId] == INF) {
        return emptyPath; // шляху не існує
    }

    // Відновлення шляху від кінця до початку (деталізовані кроки з лініями транспорту)
    std::vector<PathStep> path;
    int current = endId;
    while (current != startId) {
        path.push_back(prevStep[current]);
        current = prevVertex[current];
    }
    std::reverse(path.begin(), path.end());
    return path;
}

std::vector<PathStep> dijkstra(const std::vector<Route>& routes, int startId, int endId,
                               bool allowCar) {
    return dijkstra(routes, startId, endId, std::numeric_limits<double>::infinity(), allowCar);
}

} // namespace algorithms
} // namespace travel
