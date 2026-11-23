#pragma once

#include <vector>

#include "../Models/Route.h"
#include "../Models/Tourist.h"
#include "../Models/TouristDestination.h"

namespace travel {
namespace algorithms {

// Лінійний пошук (O(n)): фільтрація каталогу за параметрами туриста.
// Умова відбору (індикаторна функція 1.1, спрощена):
//   вартість <= залишку бюджету, тривалість огляду <= залишку часу,
//   об'єкт відкритий у currentHour, tags ∩ interests ≠ ∅.
std::vector<TouristDestination*> linearFilter(
    const std::vector<TouristDestination*>& catalog,
    const Tourist& tourist,
    double currentHour,
    double remainingBudget,
    double remainingTime);

// Сортування відібраних об'єктів (std::sort — Introsort у C++ з лямбда-компаратором)
// за спаданням інтегральної оцінки релевантності.
void sortByRelevance(std::vector<TouristDestination*>& list);

// Алгоритм Дейкстри (черга з пріоритетом): найкоротший шлях від startId до endId.
// Вага ребра — час переміщення (travelTimeHours).
// Повертає послідовність ребер Route або порожній вектор, якщо шляху немає.
std::vector<Route> dijkstra(const std::vector<Route>& routes, int startId, int endId);

} // namespace algorithms
} // namespace travel
