// Консольний smoke-тест ядра C++ (без GUI): перевіряє повний цикл
// завантаження БД (міста) -> профіль із targetCityId -> фільтр -> сортування
// -> Дейкстра з вибором лінії транспорту -> план із деталізацією переходів.
//
// Збірка (після Code/build.bat або вручну), наприклад:
//   clang++ -std=c++17 -Wall -Wextra -I ../Models/Include -I ../DataBase -I ../Controllers/Include
//   smoke_test.cpp \
//       ../Models/Src/*.cpp ../DataBase/DataLoader.cpp ../Controllers/Src/Algorithms.cpp
//       ../Controllers/Src/TravelSystem.cpp \ -o smoke_test
// Запуск:
//   ./smoke_test ../DataBase/travel_db.json
//   ./smoke_test sample_db.json        (демо-база з двома містами)

#include <iostream>
#include <string>
#include <vector>

#include "TravelSystem.h"

using namespace travel;

static void printPath(const std::vector<PathStep>& path) {
    if (path.empty()) {
        std::cout << "немає шляху\n";
        return;
    }
    for (const PathStep& step : path) {
        std::cout << "  " << step.route.getFromId() << " -> " << step.route.getToId() << " | "
                  << step.route.getDistance() << " км"
                  << " | " << step.timeHours << " год"
                  << " | " << step.cost << " EUR"
                  << " | " << step.lane.describe() << " (еф. швидкість "
                  << step.lane.effectiveSpeedKmh() << " км/год)\n";
    }
}

int main(int argc, char** argv) {
    std::string dbFile = (argc > 1) ? argv[1] : "../DataBase/travel_db.json";

    TravelSystem system;
    std::string error;
    if (!system.loadData(dbFile, error)) {
        std::cerr << "Помилка завантаження БД: " << error << "\n";
        return 1;
    }
    std::cout << "Завантажено міст: " << system.getCitiesCount()
              << ", об'єктів: " << system.getCatalogSize()
              << ", ребер графів: " << system.getRoutesCount() << "\n";
    for (const City& c : system.getCities()) {
        std::cout << "  місто #" << c.getId() << ": " << c.getName() << " (" << c.getRegion()
                  << ") — " << c.getDescription() << "\n";
    }
    if (system.getCities().empty()) {
        std::cout << "База порожня — завершення без профілю.\n";
        return 0;
    }

    int cityId = system.getCities().front().getId();
    Tourist tourist(1, "Єгор", 20.0, true, 2, 8.0, {"history", "architecture", "nature"}, cityId);
    system.setTouristProfile(tourist);
    std::cout << "\nПрофіль: " << system.getTourist().getName()
              << ", місто id=" << system.getTourist().getTargetCityId()
              << ", денний бюджет: " << system.getTourist().getDailyBudget()
              << ", загальний: " << system.getTourist().getTotalBudget() << "\n";

    auto filtered = system.filterDestinations();
    std::cout << "\nВідфільтровано об'єктів міста #" << cityId << ": " << filtered.size() << "\n";
    system.sortDestinations(filtered);
    for (const TouristDestination* d : filtered) {
        std::cout << "  [" << d->getRelevance() << "] id=" << d->getId()
                  << " cityId=" << d->getCityId() << " " << d->getDetails() << "\n";
    }

    if (filtered.size() >= 2) {
        int a = filtered.front()->getId();
        int b = filtered.back()->getId();
        std::cout << "\nНайкоротший шлях " << a << " -> " << b << " (Дейкстра, бюджет "
                  << tourist.getDailyBudget() << " EUR/day):\n";
        printPath(system.findShortestPath(a, b));

        // Перевірка ізоляції міст: вершини різних міст не з'єднуються
        int otherCityId = -1;
        for (const City& c : system.getCities()) {
            if (c.getId() != cityId) {
                otherCityId = c.getId();
                break;
            }
        }
        if (otherCityId != -1) {
            for (const TouristDestination* d : system.getCatalog(otherCityId)) {
                auto cross = system.findShortestPath(a, d->getId(), cityId, 1e9);
                std::cout << "  контроль: шлях " << a << " (місто " << cityId << ") -> "
                          << d->getId() << " (місто " << otherCityId << ") у межах міста " << cityId
                          << ": " << (cross.empty() ? "немає шляху (OK)" : "Є ШЛЯХ (ПОМИЛКА!)")
                          << "\n";
                break;
            }
        }
    }

    TravelPlan plan = system.generatePersonalizedPlan();
    std::cout << "\n" << plan.exportPlanSummary() << "\n";
    return 0;
}
