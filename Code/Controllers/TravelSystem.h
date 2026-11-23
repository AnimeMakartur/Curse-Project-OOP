#pragma once

#include <string>
#include <vector>

#include "../Models/Route.h"
#include "../Models/Tourist.h"
#include "../Models/TouristDestination.h"
#include "../Models/TravelPlan.h"

namespace travel {

// Фасадне керуюче ядро інформаційно-аналітичної системи (bizнес-логіка, C++).
// Координує: завантаження даних, фільтрацію каталогу (лінійний пошук),
// ранжування (сортування), побудову маршруту (Дейкстра) та генерацію плану.
class TravelSystem {
private:
    std::vector<TouristDestination*> catalog; // каталог об'єктів (володіє пам'яттю)
    std::vector<Route> routes;                // ребра графа (зберігає граф)
    TravelPlan* currentPlan;                  // обраний план
    Tourist currentTourist;                   // обраний профіль туриста
    bool hasTourist;

    // Вагові коефіцієнти формули релевантності (1.4): w1 + w2 + w3 = 1
    double weightRating = 0.4;
    double weightTags = 0.4;
    double weightCost = 0.2;

    static constexpr double DAY_START_HOUR = 9.0; // початок туристичного дня

public:
    TravelSystem();
    ~TravelSystem();

    TravelSystem(const TravelSystem&) = delete;
    TravelSystem& operator=(const TravelSystem&) = delete;

    // Завантажує каталог та граф маршрутів з JSON-файлу бази даних
    bool loadData(const std::string& filename, std::string& error);

    void setTouristProfile(const Tourist& t);
    const Tourist& getTourist() const;
    bool hasProfile() const;

    // Лінійний пошук: фільтрація каталогу за профілем туриста
    std::vector<TouristDestination*> filterDestinations();

    // Сортування списку об'єктів (власна реалізація поверх std::sort)
    void sortDestinations(std::vector<TouristDestination*>& list);

    // Персоналізований підбір плану: фільтрація -> релевантність -> сортування -> жадібний розподіл по днях з Дейкстрою
    TravelPlan generatePersonalizedPlan();

    // Оптимальний маршрут (Дейкстра) між двома вершинами графа
    std::vector<Route> findShortestPath(int startId, int endId);

    const TravelPlan* getCurrentPlan() const;
    size_t getCatalogSize() const;
    size_t getRoutesCount() const;
};

} // namespace travel
