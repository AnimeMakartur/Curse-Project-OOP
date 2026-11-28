// C API поверх ядра TravelSystem — точка входу для Python GUI (ctypes).
// Рядки, що повертаються, виділяються у купі; Python має звільнити їх через ts_free_string.
// Усі результати повертаються у вигляді JSON-рядків (UTF-8), які Python розбирає
// готовим парсером (стандартний модуль json).
//
// Тип смуги передається як int (enum LaneType), рядкові ключі/укр. назви/дефолти —
// на боці Python (View/lane_types.py). JSON-файл бази C++ НЕ парсить: його читає Python.

#include <cstdio>
#include <cstring>
#include <sstream>
#include <string>
#include <vector>

#include "Attraction.h"
#include "City.h"
#include "Museum.h"
#include "PathStep.h"
#include "Tourist.h"
#include "TouristDestination.h"
#include "TravelPlan.h"
#include "TravelSystem.h"

#if defined(_WIN32)
#define TRAVEL_API extern "C" __declspec(dllexport)
#else
#define TRAVEL_API extern "C" __attribute__((visibility("default")))
#endif

using namespace travel;

namespace {

std::string escapeJson(const std::string& s) {

    std::string out;
    out.reserve(s.size() + 2);
    for (char c : s) {
        switch (c) {
        case '"':
            out += "\\\"";
            break;
        case '\\':
            out += "\\\\";
            break;
        case '\n':
            out += "\\n";
            break;
        case '\r':
            out += "\\r";
            break;
        case '\t':
            out += "\\t";
            break;
        default:
            if (static_cast<unsigned char>(c) < 0x20) {
                char buf[8];
                std::snprintf(buf, sizeof(buf), "\\u%04x", c);
                out += buf;
            } else {
                out += c; // UTF-8 іде як є
            }
        }
    }
    return out;
}

std::string q(const std::string& s) { return "\"" + escapeJson(s) + "\""; }

// Компактне представлення числа у JSON (%.10g, C-локаль → крапка).
std::string num(double v) {

    char buf[32];
    std::snprintf(buf, sizeof(buf), "%.10g", v);
    return buf;
}

std::string tagsToJson(const std::vector<std::string>& tags) {

    std::string out = "[";
    for (size_t i = 0; i < tags.size(); ++i) {
        if (i)
            out += ",";
        out += q(tags[i]);
    }
    out += "]";
    return out;
}

// Тип смуги у JSON — int (enum LaneType); рядкові/укр. представлення додає Python.
std::string laneToJson(const Lane& lane) {

    std::ostringstream out;
    out << "{"
        << "\"type\":" << static_cast<int>(lane.type)
        << ",\"routeName\":" << q(lane.routeName)
        << ",\"speedMultiplier\":" << num(lane.speedMultiplier)
        << ",\"baseSpeedKmh\":" << num(lane.baseSpeedKmh)
        << ",\"effectiveSpeedKmh\":" << num(lane.effectiveSpeedKmh())
        << ",\"cost\":" << num(lane.cost) << ",\"waitTimeHours\":" << num(lane.waitTimeHours)
        << "}";
    return out.str();
}

std::string lanesToJson(const Route& route) {

    std::string out = "[";
    const auto& lanes = route.getLanes();
    for (size_t i = 0; i < lanes.size(); ++i) {
        if (i)
            out += ",";
        out += laneToJson(lanes[i]);
    }
    out += "]";
    return out;
}

std::string routeToJson(const Route& r) {

    std::ostringstream out;
    out << "{"
        << "\"cityId\":" << r.getCityId() << ",\"fromId\":" << r.getFromId()
        << ",\"toId\":" << r.getToId() << ",\"distanceKm\":" << num(r.getDistance())
        << ",\"lanes\":" << lanesToJson(r) << "}";
    return out.str();
}

std::string pathStepToJson(const PathStep& s) {

    std::ostringstream out;
    out << "{"
        << "\"cityId\":" << s.route.getCityId() << ",\"fromId\":" << s.route.getFromId()
        << ",\"toId\":" << s.route.getToId() << ",\"distanceKm\":" << num(s.route.getDistance())
        << ",\"lane\":" << laneToJson(s.lane) << ",\"timeHours\":" << num(s.timeHours)
        << ",\"cost\":" << num(s.cost) << "}";
    return out.str();
}

std::string cityToJson(const City& c) {

    std::ostringstream out;
    out << "{"
        << "\"id\":" << c.getId() << ",\"name\":" << q(c.getName())
        << ",\"region\":" << q(c.getRegion()) << ",\"description\":" << q(c.getDescription())
        << "}";
    return out.str();
}

std::string destinationToJson(const TouristDestination* d) {

    std::ostringstream out;
    out << "{"
        << "\"id\":" << d->getId() << ",\"cityId\":" << d->getCityId()
        << ",\"type\":" << q(d->getType()) << ",\"name\":" << q(d->getName())
        << ",\"cost\":" << num(d->getCost()) << ",\"rating\":" << num(d->getRating())
        << ",\"visitDuration\":" << num(d->getVisitDuration())
        << ",\"openHour\":" << num(d->getOpenHour()) << ",\"closeHour\":" << num(d->getCloseHour())
        << ",\"tags\":" << tagsToJson(d->getTags()) << ",\"relevance\":" << num(d->getRelevance())
        << ",\"details\":" << q(d->getDetails()) << "}";
    return out.str();
}

std::string destinationsToJson(const std::vector<TouristDestination*>& list) {

    std::string out = "[";
    for (size_t i = 0; i < list.size(); ++i) {
        if (i)
            out += ",";
        out += destinationToJson(list[i]);
    }
    out += "]";
    return out;
}

std::string pathToJson(const std::vector<PathStep>& path) {

    std::string out = "[";
    for (size_t i = 0; i < path.size(); ++i) {
        if (i)
            out += ",";
        out += pathStepToJson(path[i]);
    }
    out += "]";
    return out;
}

std::vector<std::string> splitCsv(const std::string& text) {

    std::vector<std::string> result;
    std::string current;
    std::istringstream stream(text);
    while (std::getline(stream, current, ',')) {
        size_t first = current.find_first_not_of(" \t\r\n");
        size_t last = current.find_last_not_of(" \t\r\n");
        if (first != std::string::npos) {
            result.push_back(current.substr(first, last - first + 1));
        }
    }
    return result;
}

char* toCString(const std::string& s) {

    char* buffer = new char[s.size() + 1];
    std::memcpy(buffer, s.c_str(), s.size() + 1);
    return buffer;
}

TravelSystem* asSystem(void* handle) { return static_cast<TravelSystem*>(handle); }

} // namespace

TRAVEL_API void* ts_create() { return new TravelSystem(); }

TRAVEL_API void ts_destroy(void* handle) { delete asSystem(handle); }

// --- наповнення бази даними: JSON читає Python (модуль json), сюди — готові сутності ---

TRAVEL_API void ts_clear_data(void* handle) {

    if (handle)
        asSystem(handle)->clearData();
}

TRAVEL_API void ts_add_city(void* handle, int id, const char* name, const char* region,
                            const char* description) {

    if (!handle)
        return;
    asSystem(handle)->addCity(
        City(id, name ? name : "", region ? region : "", description ? description : ""));
}

// Спільні поля об'єкта приходять окремими аргументами; tags — CSV-рядок (див. splitCsv).
TRAVEL_API void ts_add_attraction(void* handle, int id, int cityId, const char* name, double cost,
                                  double rating, double visitDuration, double openHour,
                                  double closeHour, const char* tagsCsv, int isOutdoor,
                                  const char* architecturalStyle, int isSeasonal) {

    if (!handle)
        return;
    asSystem(handle)->addDestination(new Attraction(
        id, cityId, name ? name : "", cost, rating, visitDuration, openHour, closeHour,
        splitCsv(tagsCsv), isOutdoor != 0, architecturalStyle ? architecturalStyle : "",
        isSeasonal != 0));
}

TRAVEL_API void ts_add_museum(void* handle, int id, int cityId, const char* name, double cost,
                              double rating, double visitDuration, double openHour,
                              double closeHour, const char* tagsCsv, int exhibitsCount,
                              int hasAudioGuide, const char* expositionTheme) {

    if (!handle)
        return;
    asSystem(handle)->addDestination(new Museum(
        id, cityId, name ? name : "", cost, rating, visitDuration, openHour, closeHour,
        splitCsv(tagsCsv), exhibitsCount, hasAudioGuide != 0,
        expositionTheme ? expositionTheme : ""));
}

// Додає ребро графа без смуг і повертає його індекс (для наступних ts_add_lane).
TRAVEL_API int ts_add_route(void* handle, int cityId, int fromId, int toId, double distanceKm) {

    if (!handle)
        return -1;
    return static_cast<int>(asSystem(handle)->addRoute(Route(cityId, fromId, toId, distanceKm)));
}

// Додає смугу/лінію до ребра графа за індексом; type — int (enum LaneType), усі числові поля
// — уже з дефолтами, добраними на боці Python (див. lane_types.py).
TRAVEL_API void ts_add_lane(void* handle, int routeIndex, int laneType, const char* routeName,
                            double speedMultiplier, double baseSpeedKmh, double cost,
                            double waitTimeHours) {
    if (laneType < 0 || laneType >= static_cast<int>(LaneType::COUNT))
        return;
    if (!handle)
        return;
    LaneType type = static_cast<LaneType>(laneType);
    Lane lane(type, routeName ? routeName : "", speedMultiplier, baseSpeedKmh, cost,
              waitTimeHours);
    asSystem(handle)->addLane(static_cast<size_t>(routeIndex), lane);
}

TRAVEL_API int ts_cities_count(void* handle) {

    return handle ? static_cast<int>(asSystem(handle)->getCitiesCount()) : 0;
}

TRAVEL_API char* ts_get_cities(void* handle) {

    if (!handle)
        return toCString("[]");
    const std::vector<City>& cities = asSystem(handle)->getCities();
    std::string out = "[";
    for (size_t i = 0; i < cities.size(); ++i) {
        if (i)
            out += ",";
        out += cityToJson(cities[i]);
    }
    out += "]";
    return toCString(out);
}

TRAVEL_API void ts_set_tourist(void* handle, int id, const char* name, double budget,
                               int isTotalBudget, int days, double dailyTimeLimit,
                               const char* interestsCsv, int targetCityId, int hasCar) {

    if (!handle)
        return;
    std::vector<std::string> tags =
        interestsCsv ? splitCsv(interestsCsv) : std::vector<std::string>();
    Tourist tourist(id, name ? name : "", budget, isTotalBudget != 0, days, dailyTimeLimit, tags,
                    targetCityId, hasCar != 0);
    asSystem(handle)->setTouristProfile(tourist);
}

TRAVEL_API void ts_set_target_city(void* handle, int cityId) {

    if (!handle || !asSystem(handle)->hasProfile())
        return;
    Tourist t = asSystem(handle)->getTourist();
    t.setTargetCityId(cityId);
    asSystem(handle)->setTouristProfile(t);
}

TRAVEL_API char* ts_get_profile(void* handle) {

    if (!handle)
        return toCString("{}");
    const Tourist& t = asSystem(handle)->getTourist();
    std::ostringstream out;
    out << "{"
        << "\"id\":" << t.getId() << ",\"name\":" << q(t.getName())
        << ",\"inputBudget\":" << num(t.getInputBudget())
        << ",\"isTotalBudget\":" << (t.getIsTotalBudget() ? "true" : "false")
        << ",\"tripDays\":" << t.getTripDays()
        << ",\"dailyTimeLimit\":" << num(t.getDailyTimeLimit())
        << ",\"dailyBudget\":" << num(t.getDailyBudget())
        << ",\"totalBudget\":" << num(t.getTotalBudget())
        << ",\"targetCityId\":" << t.getTargetCityId()
        << ",\"hasCar\":" << (t.getHasCar() ? "true" : "false")
        << ",\"interests\":" << tagsToJson(t.getInterests()) << "}";
    return toCString(out.str());
}

TRAVEL_API int ts_catalog_size(void* handle) {

    return handle ? static_cast<int>(asSystem(handle)->getCatalogSize()) : 0;
}

TRAVEL_API int ts_routes_count(void* handle) {

    return handle ? static_cast<int>(asSystem(handle)->getRoutesCount()) : 0;
}

// Повний каталог об'єктів міста (cityId < 0 — усі міста); для GUI-таблиці каталогу.
TRAVEL_API char* ts_catalog(void* handle, int cityId) {

    if (!handle)
        return toCString("[]");
    return toCString(destinationsToJson(asSystem(handle)->getCatalog(cityId)));
}

TRAVEL_API char* ts_filter_destinations(void* handle) {

    if (!handle)
        return toCString("[]");
    return toCString(destinationsToJson(asSystem(handle)->filterDestinations()));
}

TRAVEL_API char* ts_sorted_destinations(void* handle) {

    if (!handle)
        return toCString("[]");
    TravelSystem* sys = asSystem(handle);
    std::vector<TouristDestination*> list = sys->filterDestinations();
    sys->sortDestinations(list);
    return toCString(destinationsToJson(list));
}

// усі ребра графа міста (cityId < 0 — усі міста) зі списком смуг/ліній
TRAVEL_API char* ts_get_routes(void* handle, int cityId) {

    if (!handle)
        return toCString("[]");
    const std::vector<Route> routes = asSystem(handle)->getRoutes(cityId);
    std::string out = "[";
    for (size_t i = 0; i < routes.size(); ++i) {
        if (i)
            out += ",";
        out += routeToJson(routes[i]);
    }
    out += "]";
    return toCString(out);
}

TRAVEL_API char* ts_find_shortest_path(void* handle, int fromId, int toId) {

    if (!handle)
        return toCString("[]");
    return toCString(pathToJson(asSystem(handle)->findShortestPath(fromId, toId)));
}

// Дейкстра із явним залишком бюджету (визначає, які лінії транспорту доступні).
TRAVEL_API char* ts_find_shortest_path_budget(void* handle, int fromId, int toId, double budget) {

    if (!handle)
        return toCString("[]");
    TravelSystem* sys = asSystem(handle);
    return toCString(pathToJson(sys->findShortestPath(fromId, toId, sys->activeCityId(), budget)));
}

TRAVEL_API char* ts_generate_plan(void* handle) {

    if (!handle)
        return toCString("{}");
    TravelPlan plan = asSystem(handle)->generatePersonalizedPlan();

    std::ostringstream out;
    out << "{";
    out << "\"tourist\":" << q(plan.getTourist().getName());
    out << ",\"targetCityId\":" << plan.getTourist().getTargetCityId();
    out << ",\"days\":[";
    const auto& days = plan.getDays();
    for (size_t d = 0; d < days.size(); ++d) {
        if (d)
            out << ",";
        out << "{\"day\":" << (d + 1) << ",\"items\":[";
        for (size_t i = 0; i < days[d].size(); ++i) {
            if (i)
                out << ",";
            const DayItem& item = days[d][i];
            out << "{\"destination\":";
            out << (item.destination ? destinationToJson(item.destination) : std::string("null"));
            out << ",\"transfers\":[";
            for (size_t t = 0; t < item.transfers.size(); ++t) {
                if (t)
                    out << ",";
                out << pathStepToJson(item.transfers[t]);
            }
            out << "]}";
        }
        out << "]}";
    }
    out << "],\"totalCost\":" << num(plan.getTotalCost());
    out << ",\"totalDuration\":" << num(plan.getTotalDuration());
    out << ",\"totalTravelTime\":" << num(plan.getTotalTravelTime());
    out << ",\"totalVisitTime\":" << num(plan.getTotalVisitTime());
    out << ",\"remainingBudget\":" << num(plan.getRemainingBudget());
    out << "}";
    return toCString(out.str());
}

TRAVEL_API void ts_free_string(char* str) { delete[] str; }
