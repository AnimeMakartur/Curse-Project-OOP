#pragma once

#include <string>
#include <vector>

#include "City.h"
#include "PathStep.h"
#include "Route.h"
#include "Tourist.h"
#include "TouristDestination.h"
#include "TravelPlan.h"

namespace travel {
// Фасадне керуюче ядро інформаційно-аналітичної системи (бізнес-логіка, C++).
// Координує: завантаження даних (міста + каталог + граф), фільтрацію каталогу
// обраного міста (лінійний пошук), ранжування (сортування), побудову маршруту
// (Дейкстра з вибором лінії транспорту) та генерацію персоналізованого плану.
class TravelSystem {
  private:
    std::vector<City> cities; // міста / агломерації з БД
    std::vector<TouristDestination*> catalog; // каталог об'єктів усіх міст (володіє пам'яттю)
    std::vector<Route> routes; // ребра графів усіх міст
    TravelPlan* currentPlan;   // обраний план
    Tourist currentTourist;    // обраний профіль туриста
    bool hasTourist;           // чи встановлено профіль туриста

    // Вагові коефіцієнти формули релевантності (1.4): w1 + w2 + w3 = 1
    double weightRating = 0.4;
    double weightTags = 0.4;
    double weightCost = 0.2;
    // початок туристичного дня
    static constexpr double DAY_START_HOUR = 9.0;
    // Допоміжні вибірки в межах міста (cityId < 0 — усі міста)
    std::vector<TouristDestination*> catalogForCity(int cityId) const;
    std::vector<Route> routesForCity(int cityId) const;
    // Якщо весь шлях — car_lane (турист із машиною), згортає його в один прямий
    // перегін startId -> endId без проміжних вершин-будівель; інакше повертає як є.
    static std::vector<PathStep> collapseCarPath(const std::vector<PathStep>& path, int startId,
                                                 int endId, int cityId);

  public:
    TravelSystem();
    ~TravelSystem();

    TravelSystem(const TravelSystem&) = delete;
    TravelSystem& operator=(const TravelSystem&) = delete;

    // Завантажує міста, каталог та графи маршрутів з JSON-файлу бази даних
    bool loadData(const std::string& filename, std::string& error);
    //
    const std::vector<City>& getCities() const;

    void setTouristProfile(const Tourist& t);
    const Tourist& getTourist() const;
    bool hasProfile() const;
    int activeCityId() const; // targetCityId туриста (або -1)
    // Лінійний пошук: фільтрація каталогу ОБРАНОГО МІСТА за профілем туриста
    std::vector<TouristDestination*> filterDestinations();
    // Повний каталог об'єктів міста (cityId < 0 — усі міста) — для GUI-таблиці
    std::vector<TouristDestination*> getCatalog(int cityId) const;
    // Усі ребра транспортного графа міста (cityId < 0 — усі міста)
    std::vector<Route> getRoutes(int cityId) const;
    // Сортування списку об'єктів за релевантністю (std::sort поверх оцінок)
    void sortDestinations(std::vector<TouristDestination*>& list);
    // Персоналізований підбір плану в межах обраного міста:
    // фільтрація -> релевантність -> сортування -> жадібний розподіл по днях з Дейкстрою
    TravelPlan generatePersonalizedPlan();
    // Оптимальний маршрут (Дейкстра) між двома вершинами графа ОБРАНОГО міста
    // з урахуванням денного бюджету туриста
    std::vector<PathStep> findShortestPath(int startId, int endId);
    // Явна версія: задане місто, залишок бюджету та дозвіл на car_lane (чи є машина)
    std::vector<PathStep> findShortestPath(int startId, int endId, int cityId,
                                           double remainingBudget, bool allowCar = true);
    const TravelPlan* getCurrentPlan() const;
    size_t getCatalogSize() const;
    size_t getRoutesCount() const;
    size_t getCitiesCount() const;
};

} // namespace travel
