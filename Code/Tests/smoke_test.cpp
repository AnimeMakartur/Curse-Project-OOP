// Консольний smoke-тест ядра C++ (без GUI): перевіряє повний цикл
// завантаження БД -> профіль -> фільтр -> сортування -> Дейкстра -> план.
//
// Збірка (після Code/build.bat або вручну), наприклад:
//   g++ -std=c++17 -I ../Models -I ../DataBase -I ../Controllers smoke_test.cpp \
//       ../Models/*.cpp ../DataBase/DataLoader.cpp ../Controllers/Algorithms.cpp ../Controllers/TravelSystem.cpp \
//       -o smoke_test
// Запуск:
//   ./smoke_test ../DataBase/travel_db.json

#include <iostream>
#include <string>

#include "../Controllers/TravelSystem.h"

using namespace travel;

int main(int argc, char** argv) {
    std::string dbFile = (argc > 1) ? argv[1] : "../DataBase/travel_db.json";

    TravelSystem system;
    std::string error;
    if (!system.loadData(dbFile, error)) {
        std::cerr << "Помилка завантаження БД: " << error << "\n";
        return 1;
    }
    std::cout << "Завантажено об'єктів: " << system.getCatalogSize()
              << ", ребер графа: " << system.getRoutesCount() << "\n";

    Tourist tourist(1, "Єгор", 1000.0, true, 2, 8.0,
                    {"історія", "архітектура", "природа"});
    system.setTouristProfile(tourist);
    std::cout << "Денний бюджет: " << system.getTourist().getDailyBudget()
              << ", загальний: " << system.getTourist().getTotalBudget() << "\n";

    auto filtered = system.filterDestinations();
    std::cout << "\nВідфільтровано об'єктів: " << filtered.size() << "\n";
    system.sortDestinations(filtered);
    for (const TouristDestination* d : filtered) {
        std::cout << "  [" << d->getRelevance() << "] " << d->getDetails() << "\n";
    }

    if (!filtered.empty()) {
        auto path = system.findShortestPath(filtered.front()->getId(), filtered.back()->getId());
        std::cout << "\nНайкоротший шлях " << filtered.front()->getId()
                  << " -> " << filtered.back()->getId() << ": ";
        if (path.empty()) {
            std::cout << "немає шляху\n";
        } else {
            for (const Route& r : path) {
                std::cout << r.getFromId() << "->" << r.getToId()
                          << " (" << r.getRoadDescription() << ") ";
            }
            std::cout << "\n";
        }
    }

    TravelPlan plan = system.generatePersonalizedPlan();
    std::cout << "\n" << plan.exportPlanSummary() << "\n";
    return 0;
}
