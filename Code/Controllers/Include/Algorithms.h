#pragma once

#include <vector>

#include "PathStep.h"
#include "Route.h"
#include "Tourist.h"
#include "TouristDestination.h"

namespace travel {
namespace algorithms {

// Лінійний пошук (O(n)): фільтрація каталогу за параметрами туриста.
// Умова відбору (індикаторна функція 1.1, спрощена):
//   вартість <= залишку бюджету, тривалість огляду <= залишку часу,
//   об'єкт відкритий у currentHour, tags ∩ interests ≠ ∅.
std::vector<TouristDestination*> linearFilter(const std::vector<TouristDestination*>& catalog,
                                              const Tourist& tourist, double currentHour,
                                              double remainingBudget, double remainingTime);
// Сортування відібраних об'єктів (std::sort — Introsort у C++ з лямбда-компаратором)
// за спаданням інтегральної оцінки релевантності.
void sortByRelevance(std::vector<TouristDestination*>& list);
// Алгоритм Дейкстри (черга з пріоритетом) по ребрах одного міста.
// Вага ребра (u,v) — мінімальний час переміщення серед смуг/ліній, що вписуються
// у залишок бюджету туриста:
//   t(u,v) = min_{l ∈ lanes, cost(l) ≤ remainingBudget}
//            ( distanceKm / (v_base·k_speed(l)) + t_wait(l) )
// allowCar=false — смуги car_lane не розглядаються (у туриста немає власної машини).
// Повертає деталізовані кроки маршруту (PathStep із обраною смугою/лінією),
// або порожній вектор, якщо шляху немає.
std::vector<PathStep> dijkstra(const std::vector<Route>& routes, int startId, int endId,
                               double remainingBudget, bool allowCar = true);
// Перевантаження без бюджетного обмеження (budget = +inf): найшвидша лінія на кожному ребрі.
std::vector<PathStep> dijkstra(const std::vector<Route>& routes, int startId, int endId,
                               bool allowCar = true);
} // namespace algorithms
} // namespace travel
