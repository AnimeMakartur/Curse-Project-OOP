// Компактний юніт-тест C++ ядра TravelSystem (без Python/ctypes).
// Перевіряє ключові алгоритми напряму: фільтрацію, релевантність, Дейкстру, план.
// Збірка: build.bat --tests / build.sh --tests → Tests/.build/core_test.exe

#include <cassert>
#include <cmath>
#include <iostream>
#include <vector>

#include "Attraction.h"
#include "City.h"
#include "Lane.h"
#include "Museum.h"
#include "Route.h"
#include "TravelSystem.h"

using namespace travel;

static int failures = 0;
#define CHECK(cond)                                                                              \
    do {                                                                                         \
        if (!(cond)) {                                                                           \
            std::cerr << "FAIL: " << #cond << " (" << __FILE__ << ":" << __LINE__ << ")\n";      \
            ++failures;                                                                          \
        }                                                                                        \
    } while (0)

static bool approx(double a, double b, double eps = 1e-6) { return std::fabs(a - b) < eps; }

static void fillDemo(TravelSystem& sys) {
    sys.clearData();
    sys.addCity(City(1, "Lviv", "Lviv Oblast", "old town"));
    sys.addCity(City(2, "Kyiv", "Kyiv Oblast", "megacity"));
    sys.addDestination(new Attraction(1, 1, "Rynok Square", 0, 4.8, 1.5, 0.0, 23.99,
                                      {"history", "architecture"}, true, "renaissance", false));
    sys.addDestination(new Museum(2, 1, "History Museum", 1.6, 4.6, 2.0, 10.0, 18.0,
                                  {"history", "culture"}, 1200, true, "city history"));
    sys.addDestination(new Attraction(3, 1, "High Castle", 1.0, 4.7, 1.0, 9.0, 20.0,
                                      {"nature", "history"}, true, "medieval", false));
    sys.addDestination(new Attraction(4, 1, "Opera House", 4.0, 4.9, 2.5, 10.0, 21.0,
                                      {"architecture", "culture"}, false, "neo-renaissance", false));
    sys.addDestination(new Attraction(5, 1, "Atlas Hotel", 0, 4.5, 0, 0.0, 23.99,
                                      {"hotel"}, false, "art nouveau", false));

    size_t r = sys.addRoute(Route(1, 1, 2, 0.4));
    sys.addLane(r, Lane(LaneType::Sidewalk, "", 1.0, 5.0, 0.0, 0.0));
    sys.addLane(r, Lane(LaneType::BikeLane, "", 1.0, 15.0, 0.0, 0.0));

    r = sys.addRoute(Route(1, 2, 3, 1.2));
    sys.addLane(r, Lane(LaneType::BusLane, "Bus 29", 1.3, 30.0, 0.3, 0.15));
    sys.addLane(r, Lane(LaneType::TramLine, "Tram 8", 1.6, 35.0, 0.3, 0.12));
    sys.addLane(r, Lane(LaneType::Sidewalk, "", 1.0, 5.0, 0.0, 0.0));

    r = sys.addRoute(Route(1, 3, 4, 2.5));
    sys.addLane(r, Lane(LaneType::Metrobus, "Metrobus M1", 1.5, 40.0, 0.4, 0.1));
    sys.addLane(r, Lane(LaneType::CarLane, "", 1.0, 30.0, 0.0, 0.0));

    r = sys.addRoute(Route(1, 1, 4, 12.0));
    sys.addLane(r, Lane(LaneType::Railway, "City railway S1", 1.6, 90.0, 0.9, 0.3));
    sys.addLane(r, Lane(LaneType::CarLane, "", 1.0, 30.0, 0.0, 0.0));

    r = sys.addRoute(Route(1, 5, 1, 0.6));
    sys.addLane(r, Lane(LaneType::Sidewalk, "", 1.0, 5.0, 0.0, 0.0));
}

int main() {
    TravelSystem sys;
    fillDemo(sys);

    CHECK(sys.getCitiesCount() == 2);
    CHECK(sys.getCatalogSize() == 5);
    CHECK(sys.getRoutesCount() == 5);

    // Профіль: бюджет 20 на 2 дні → 10/день, інтереси history+nature
    Tourist t(1, "Test", 20.0, true, 2, 8.0, {"history", "nature"}, 1);
    sys.setTouristProfile(t);
    CHECK(approx(sys.getTourist().getDailyBudget(), 10.0));
    CHECK(approx(sys.getTourist().getTotalBudget(), 20.0));

    // Лінійний фільтр: Rynok (history), High Castle (history+nature) — музей закритий о 9:00
    auto filtered = sys.filterDestinations();
    CHECK(filtered.size() == 2);

    // Релевантність + сортування
    sys.sortDestinations(filtered);
    CHECK(filtered.size() == 2);
    CHECK(filtered[0]->getRelevance() > filtered[1]->getRelevance());

    // Дейкстра: 1 -> 3 (Rynok -> High Castle), найшвидший шлях через 2 (bike + tram)
    auto path = sys.findShortestPath(1, 3);
    CHECK(!path.empty());
    CHECK(path.size() == 2); // 1->2->3
    CHECK(path[0].route.getFromId() == 1);
    CHECK(path[0].route.getToId() == 2);
    CHECK(path[0].lane.type == LaneType::BikeLane); // bike швидший за sidewalk на 0.4 км
    CHECK(path[1].lane.type == LaneType::TramLine); // tram швидший за bus на 1.2 км

    // Дейкстра: 1 -> 4. Через місто (1->2->3->4: 0.027+0.141+0.142=0.310) швидше за пряму
    // залізницю (12/144+0.3=0.383), тому перший крок — 1->2 на велосипеді.
    auto path14 = sys.findShortestPath(1, 4);
    CHECK(!path14.empty());
    CHECK(path14.front().route.getFromId() == 1);
    CHECK(path14.front().route.getToId() == 2);
    double total14 = 0.0;
    for (const auto& s : path14)
        total14 += s.timeHours;
    CHECK(approx(total14, 0.4 / 15.0 + (1.2 / 56.0 + 0.12) + (2.5 / 60.0 + 0.1), 1e-4));

    // Недосяжна вершина (інше місто)
    auto cross = sys.findShortestPath(1, 999, 1, 1e9);
    CHECK(cross.empty());

    // План: 2 дні, бюджет 10/день
    TravelPlan plan = sys.generatePersonalizedPlan();
    CHECK(plan.getDays().size() >= 1);
    CHECK(plan.getTotalCost() > 0.0);
    CHECK(plan.getTotalCost() <= 20.0);

    // Lane: travelTimeHours
    Lane tram(LaneType::TramLine, "T8", 1.6, 35.0, 0.3, 0.12);
    CHECK(approx(tram.travelTimeHours(1.2), 1.2 / 56.0 + 0.12, 1e-9));
    CHECK(approx(tram.effectiveSpeedKmh(), 56.0));
    CHECK(tram.isAffordable(0.3));
    CHECK(!tram.isAffordable(0.29));

    // Route: chooseBestLane вибирає найшвидшу доступну смугу
    Route route(1, 1, 2, 1.2, {Lane(LaneType::Sidewalk, "", 1.0, 5.0, 0.0, 0.0),
                                Lane(LaneType::TramLine, "T8", 1.6, 35.0, 0.3, 0.12),
                                Lane(LaneType::BusLane, "B29", 1.3, 30.0, 0.3, 0.15)});
    Lane best = route.chooseBestLane(1.0, false);
    CHECK(best.type == LaneType::TramLine); // 1.2/56+0.12 < 1.2/39+0.15 < 1.2/5
    Lane bestNoBudget = route.chooseBestLane(0.0, false); // бюджет 0 → найдешевша (sidewalk)
    CHECK(bestNoBudget.type == LaneType::Sidewalk);
    CHECK(route.hasAffordableLane(0.0, false));  // sidewalk безкоштовний
    CHECK(!route.hasAffordableLane(-1.0, false)); // навіть sidewalk не "вписується" в -1

    // Route: car_lane недоступна без машини
    Route carRoute(1, 1, 2, 5.0, {Lane(LaneType::CarLane, "", 1.0, 30.0, 0.0, 0.0)});
    CHECK(!carRoute.hasAffordableLane(1.0, false));
    CHECK(carRoute.hasAffordableLane(1.0, true));

    // Tourist: бюджет на день vs на всю подорож
    Tourist daily(2, "D", 15.0, false, 3, 8.0, {}, 1);
    CHECK(approx(daily.getDailyBudget(), 15.0));
    CHECK(approx(daily.getTotalBudget(), 45.0));
    Tourist total(3, "T", 30.0, true, 3, 8.0, {}, 1);
    CHECK(approx(total.getDailyBudget(), 10.0));
    CHECK(approx(total.getTotalBudget(), 30.0));

    // TouristDestination: isOpen
    Attraction a(10, 1, "Test", 0, 4.0, 1.0, 9.0, 18.0, {"history"}, true, "baroque", false);
    CHECK(a.isOpen(9.0));
    CHECK(a.isOpen(18.0));
    CHECK(!a.isOpen(8.99));
    CHECK(!a.isOpen(18.01));
    CHECK(a.getType() == "attraction");

    // Релевантність: музей з аудіогідом отримує бонус 0.05
    Museum m(11, 1, "Museum", 1.0, 4.0, 2.0, 9.0, 18.0, {"history"}, 100, true, "art");
    double score = m.calculateRelevance(t, 0.4, 0.4, 0.2);
    CHECK(score > 0.0);
    CHECK(approx(m.getRelevance(), score));

    if (failures == 0) {
        std::cout << "All C++ core tests passed.\n";
        return 0;
    }
    std::cerr << failures << " test(s) failed.\n";
    return 1;
}
