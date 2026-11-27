// Консольний smoke-тест ядра C++ (без GUI і без JSON): перевіряє повний цикл
// наповнення бази через add-API -> профіль із targetCityId -> фільтр ->
// сортування -> Дейкстра з вибором лінії транспорту -> план із деталізацією
// переходів.
//
// JSON-файл бази даних тут НЕ читається: C++ ядро не парсить JSON (старий
// парсер JsonParser.h видалено), файл travel_db.json читає Python-сторона
// готовим парсером (стандартний модуль json) і передає сутності через C API —
// див. View/db_loader.py і View/travel_client.py. Демо-дані для Python-режиму
// — у Tests/sample_db.json.
//
// Збірка (після Code/build.bat або вручну), наприклад:
//   clang++ -std=c++17 -Wall -Wextra -I ../Models/Include -I ../Controllers/Include
//   smoke_test.cpp \
//       ../Models/Src/*.cpp ../Controllers/Src/Algorithms.cpp
//       ../Controllers/Src/TravelSystem.cpp \
//       -o smoke_test
// Запуск:
//   ./smoke_test
//   (або одразу зі скриптом збірки: Code\build.bat --tests  /  ./build.sh --tests)

#include <iostream>
#include <string>
#include <vector>

#include "Attraction.h"
#include "City.h"
#include "Lane.h"
#include "Museum.h"
#include "Route.h"
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

// Транспортні графи демо-бази (ребра зі смугами/лініями).
static void addDemoRoutes(TravelSystem& system) {
    size_t r;
    r = system.addRoute(Route(1, 1, 2, 0.4));
    system.addLane(r, Lane(LaneType::Sidewalk));
    system.addLane(r, Lane(LaneType::BikeLane));

    r = system.addRoute(Route(1, 2, 3, 1.2));
    system.addLane(r, Lane(LaneType::BusLane, "Bus 29", 1.0, 25.0, 0.3, 0.15));
    system.addLane(r, Lane(LaneType::TramLine, "Tram 8", 1.6, 35.0, 0.3, 0.12));
    system.addLane(r, Lane(LaneType::Sidewalk));

    r = system.addRoute(Route(1, 3, 4, 2.5));
    system.addLane(r, Lane(LaneType::Metrobus, "Metrobus M1", 1.5, 40.0, 0.4, 0.1));
    system.addLane(r, Lane(LaneType::TramLine, "Tram 1", 1.0, 22.0, 0.3, 0.12));
    system.addLane(r, Lane(LaneType::CarLane));

    r = system.addRoute(Route(1, 1, 4, 12.0));
    system.addLane(r, Lane(LaneType::Railway, "City railway S1", 1.6, 90.0, 0.9, 0.3));
    system.addLane(r, Lane(LaneType::SuburbanRail, "Suburban train 801", 1.4, 70.0, 0.6, 0.25));
    system.addLane(r, Lane(LaneType::CarLane));

    r = system.addRoute(Route(1, 5, 1, 0.6));
    system.addLane(r, Lane(LaneType::Sidewalk));
    system.addLane(r, Lane(LaneType::BikeLane));

    r = system.addRoute(Route(2, 11, 12, 1.0));
    system.addLane(r, Lane(LaneType::Sidewalk));
    system.addLane(r, Lane(LaneType::BikeLane));
    system.addLane(r, Lane(LaneType::BusLane, "Bus 55", 1.0, 25.0, 0.3, 0.15));

    r = system.addRoute(Route(2, 12, 13, 6.5));
    system.addLane(r, Lane(LaneType::Metrobus, "Metrobus M3", 1.5, 40.0, 0.4, 0.1));
    system.addLane(r, Lane(LaneType::BusLane, "Bus 118", 1.0, 25.0, 0.3, 0.2));
    system.addLane(r, Lane(LaneType::Sidewalk));

    r = system.addRoute(Route(2, 11, 13, 9.0));
    system.addLane(r, Lane(LaneType::SuburbanRail, "Suburban train N06", 1.4, 70.0, 0.6, 0.25));
    system.addLane(r, Lane(LaneType::CarLane));

    r = system.addRoute(Route(2, 14, 11, 0.8));
    system.addLane(r, Lane(LaneType::Sidewalk));
    system.addLane(r, Lane(LaneType::BusLane, "Bus 55", 1.0, 25.0, 0.3, 0.15));
}

// Демо-база у коді (еквівалентна Tests/sample_db.json): два міста, каталог
// і транспортні графи зі смугами/лініями.
static void fillDemoData(TravelSystem& system) {
    system.clearData();
    system.addCity(City(1, "Lviv", "Lviv Oblast",
                        "Compact old town with a tram network and dedicated bus lanes"));
    system.addCity(City(2, "Kyiv", "Kyiv Oblast",
                        "Megacity with a metrobus (BRT), suburban trains and a city railway"));
    system.addDestination(new Attraction(1, 1, "Rynok Square", 0, 4.8, 1.5, 0.0, 23.99,
                                         {"history", "architecture"}, true, "renaissance", false));
    system.addDestination(new Museum(2, 1, "Lviv History Museum", 1.6, 4.6, 2.0, 10.0, 18.0,
                                     {"history", "culture", "museums"}, 1200, true,
                                     "city history"));
    system.addDestination(new Attraction(3, 1, "High Castle", 1.0, 4.7, 1.0, 9.0, 20.0,
                                         {"nature", "history", "viewpoints"}, true, "medieval",
                                         false));
    system.addDestination(new Attraction(4, 1, "Opera House", 4.0, 4.9, 2.5, 10.0, 21.0,
                                         {"architecture", "culture", "theatre"}, false,
                                         "neo-renaissance", false));
    system.addDestination(new Attraction(5, 1, "Atlas Hotel", 0, 4.5, 0, 0.0, 23.99,
                                         {"hotel", "accommodation"}, false, "art nouveau", false));
    system.addDestination(new Attraction(11, 2, "Khreshchatyk", 0, 4.5, 1.5, 0.0, 23.99,
                                         {"history", "architecture"}, true, "classicism", false));
    system.addDestination(new Museum(12, 2, "National Museum of the History of Ukraine", 2.0, 4.7,
                                     2.0, 10.0, 17.0, {"history", "museums", "culture"}, 3000, true,
                                     "history of Ukraine"));
    system.addDestination(new Attraction(13, 2, "National Botanical Garden", 1.2, 4.6, 2.0, 8.0,
                                         19.0, {"nature"}, true, "landscape park", true));
    system.addDestination(new Attraction(14, 2, "Premier Kyiv Hotel", 0, 4.4, 0, 0.0, 23.99,
                                         {"hotel", "accommodation"}, false, "stalinist neoclassicism",
                                         false));
    addDemoRoutes(system);
}

int main() {
    TravelSystem system;
    fillDemoData(system);

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
