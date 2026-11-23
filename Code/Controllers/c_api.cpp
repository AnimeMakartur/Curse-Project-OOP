// C API поверх ядра TravelSystem — точка входу для Python GUI (ctypes).
// Рядки, що повертаються, виділяються у купі; Python має звільнити їх через ts_free_string.
// Усі результати повертаються у вигляді JSON-рядків (UTF-8).

#include <cstdio>
#include <cstring>
#include <sstream>
#include <string>
#include <vector>

#include "TravelSystem.h"
#include "../Models/City.h"
#include "../Models/PathStep.h"
#include "../Models/Tourist.h"
#include "../Models/TouristDestination.h"
#include "../Models/TravelPlan.h"

#if defined(_WIN32)
  #define TRAVEL_API extern "C" __declspec(dllexport)
#else
  #define TRAVEL_API extern "C" __attribute__((visibility("default")))
#endif

using namespace travel;

namespace {

std::string g_lastError; // остання помилка завантаження БД (для ts_last_error)

std::string escapeJson(const std::string& s) {
    std::string out;
    out.reserve(s.size() + 2);
    for (char c : s) {
        switch (c) {
            case '"': out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            case '\n': out += "\\n"; break;
            case '\r': out += "\\r"; break;
            case '\t': out += "\\t"; break;
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
        if (i) out += ",";
        out += q(tags[i]);
    }
    out += "]";
    return out;
}

std::string laneToJson(const Lane& lane) {
    std::ostringstream out;
    out << "{"
        << "\"type\":" << q(laneTypeToString(lane.type))
        << ",\"typeUkr\":" << q(laneTypeToUkr(lane.type))
        << ",\"transportUkr\":" << q(laneTypeTransportUkr(lane.type))
        << ",\"routeName\":" << q(lane.routeName)
        << ",\"speedMultiplier\":" << num(lane.speedMultiplier)
        << ",\"baseSpeedKmh\":" << num(lane.baseSpeedKmh)
        << ",\"effectiveSpeedKmh\":" << num(lane.effectiveSpeedKmh())
        << ",\"cost\":" << num(lane.cost)
        << ",\"waitTimeHours\":" << num(lane.waitTimeHours)
        << ",\"description\":" << q(lane.describe())
        << "}";
    return out.str();
}

std::string lanesToJson(const Route& route) {
    std::string out = "[";
    const auto& lanes = route.getLanes();
    for (size_t i = 0; i < lanes.size(); ++i) {
        if (i) out += ",";
        out += laneToJson(lanes[i]);
    }
    out += "]";
    return out;
}

std::string routeToJson(const Route& r) {
    std::ostringstream out;
    out << "{"
        << "\"cityId\":" << r.getCityId()
        << ",\"fromId\":" << r.getFromId()
        << ",\"toId\":" << r.getToId()
        << ",\"distanceKm\":" << num(r.getDistance())
        << ",\"lanes\":" << lanesToJson(r)
        << "}";
    return out.str();
}

std::string pathStepToJson(const PathStep& s) {
    std::ostringstream out;
    out << "{"
        << "\"cityId\":" << s.route.getCityId()
        << ",\"fromId\":" << s.route.getFromId()
        << ",\"toId\":" << s.route.getToId()
        << ",\"distanceKm\":" << num(s.route.getDistance())
        << ",\"lane\":" << laneToJson(s.lane)
        << ",\"timeHours\":" << num(s.timeHours)
        << ",\"cost\":" << num(s.cost)
        << "}";
    return out.str();
}

std::string cityToJson(const City& c) {
    std::ostringstream out;
    out << "{"
        << "\"id\":" << c.getId()
        << ",\"name\":" << q(c.getName())
        << ",\"region\":" << q(c.getRegion())
        << ",\"description\":" << q(c.getDescription())
        << "}";
    return out.str();
}

std::string destinationToJson(const TouristDestination* d) {
    std::ostringstream out;
    out << "{"
        << "\"id\":" << d->getId()
        << ",\"cityId\":" << d->getCityId()
        << ",\"type\":" << q(d->getType())
        << ",\"name\":" << q(d->getName())
        << ",\"cost\":" << num(d->getCost())
        << ",\"rating\":" << num(d->getRating())
        << ",\"visitDuration\":" << num(d->getVisitDuration())
        << ",\"openHour\":" << num(d->getOpenHour())
        << ",\"closeHour\":" << num(d->getCloseHour())
        << ",\"tags\":" << tagsToJson(d->getTags())
        << ",\"relevance\":" << num(d->getRelevance())
        << ",\"details\":" << q(d->getDetails())
        << "}";
    return out.str();
}

std::string destinationsToJson(const std::vector<TouristDestination*>& list) {
    std::string out = "[";
    for (size_t i = 0; i < list.size(); ++i) {
        if (i) out += ",";
        out += destinationToJson(list[i]);
    }
    out += "]";
    return out;
}

std::string pathToJson(const std::vector<PathStep>& path) {
    std::string out = "[";
    for (size_t i = 0; i < path.size(); ++i) {
        if (i) out += ",";
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

TRAVEL_API void* ts_create() {
    return new TravelSystem();
}

TRAVEL_API void ts_destroy(void* handle) {
    delete asSystem(handle);
}

TRAVEL_API int ts_load_data(void* handle, const char* filename) {
    if (!handle || !filename) {
        g_lastError = "Некоректні аргументи ts_load_data";
        return 0;
    }
    std::string error;
    bool ok = asSystem(handle)->loadData(filename, error);
    g_lastError = ok ? "" : error;
    return ok ? 1 : 0;
}

TRAVEL_API const char* ts_last_error() {
    return g_lastError.c_str();
}

TRAVEL_API int ts_cities_count(void* handle) {
    return handle ? static_cast<int>(asSystem(handle)->getCitiesCount()) : 0;
}

TRAVEL_API char* ts_get_cities(void* handle) {
    if (!handle) return toCString("[]");
    const std::vector<City>& cities = asSystem(handle)->getCities();
    std::string out = "[";
    for (size_t i = 0; i < cities.size(); ++i) {
        if (i) out += ",";
        out += cityToJson(cities[i]);
    }
    out += "]";
    return toCString(out);
}

TRAVEL_API void ts_set_tourist(void* handle, int id, const char* name,
                               double budget, int isTotalBudget, int days,
                               double dailyTimeLimit, const char* interestsCsv,
                               int targetCityId) {
    if (!handle) return;
    std::vector<std::string> tags = interestsCsv ? splitCsv(interestsCsv) : std::vector<std::string>();
    Tourist tourist(id, name ? name : "", budget, isTotalBudget != 0, days,
                    dailyTimeLimit, tags, targetCityId);
    asSystem(handle)->setTouristProfile(tourist);
}

TRAVEL_API void ts_set_target_city(void* handle, int cityId) {
    if (!handle || !asSystem(handle)->hasProfile()) return;
    Tourist t = asSystem(handle)->getTourist();
    t.setTargetCityId(cityId);
    asSystem(handle)->setTouristProfile(t);
}

TRAVEL_API char* ts_get_profile(void* handle) {
    if (!handle) return toCString("{}");
    const Tourist& t = asSystem(handle)->getTourist();
    std::ostringstream out;
    out << "{"
        << "\"id\":" << t.getId()
        << ",\"name\":" << q(t.getName())
        << ",\"inputBudget\":" << num(t.getInputBudget())
        << ",\"isTotalBudget\":" << (t.getIsTotalBudget() ? "true" : "false")
        << ",\"tripDays\":" << t.getTripDays()
        << ",\"dailyTimeLimit\":" << num(t.getDailyTimeLimit())
        << ",\"dailyBudget\":" << num(t.getDailyBudget())
        << ",\"totalBudget\":" << num(t.getTotalBudget())
        << ",\"targetCityId\":" << t.getTargetCityId()
        << ",\"interests\":" << tagsToJson(t.getInterests())
        << "}";
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
    if (!handle) return toCString("[]");
    return toCString(destinationsToJson(asSystem(handle)->getCatalog(cityId)));
}

TRAVEL_API char* ts_filter_destinations(void* handle) {
    if (!handle) return toCString("[]");
    return toCString(destinationsToJson(asSystem(handle)->filterDestinations()));
}

TRAVEL_API char* ts_sorted_destinations(void* handle) {
    if (!handle) return toCString("[]");
    TravelSystem* sys = asSystem(handle);
    std::vector<TouristDestination*> list = sys->filterDestinations();
    sys->sortDestinations(list);
    return toCString(destinationsToJson(list));
}

// усі ребра графа міста (cityId < 0 — усі міста) зі списком смуг/ліній
TRAVEL_API char* ts_get_routes(void* handle, int cityId) {
    if (!handle) return toCString("[]");
    const std::vector<Route> routes = asSystem(handle)->getRoutes(cityId);
    std::string out = "[";
    for (size_t i = 0; i < routes.size(); ++i) {
        if (i) out += ",";
        out += routeToJson(routes[i]);
    }
    out += "]";
    return toCString(out);
}

TRAVEL_API char* ts_find_shortest_path(void* handle, int fromId, int toId) {
    if (!handle) return toCString("[]");
    return toCString(pathToJson(asSystem(handle)->findShortestPath(fromId, toId)));
}

// Дейкстра із явним залишком бюджету (визначає, які лінії транспорту доступні).
TRAVEL_API char* ts_find_shortest_path_budget(void* handle, int fromId, int toId, double budget) {
    if (!handle) return toCString("[]");
    TravelSystem* sys = asSystem(handle);
    return toCString(pathToJson(sys->findShortestPath(fromId, toId, sys->activeCityId(), budget)));
}

TRAVEL_API char* ts_generate_plan(void* handle) {
    if (!handle) return toCString("{}");
    TravelPlan plan = asSystem(handle)->generatePersonalizedPlan();

    std::ostringstream out;
    out << "{";
    out << "\"tourist\":" << q(plan.getTourist().getName());
    out << ",\"targetCityId\":" << plan.getTourist().getTargetCityId();
    out << ",\"days\":[";
    const auto& days = plan.getDays();
    for (size_t d = 0; d < days.size(); ++d) {
        if (d) out << ",";
        out << "{\"day\":" << (d + 1) << ",\"items\":[";
        for (size_t i = 0; i < days[d].size(); ++i) {
            if (i) out << ",";
            const DayItem& item = days[d][i];
            out << "{\"destination\":";
            out << (item.destination ? destinationToJson(item.destination) : std::string("null"));
            out << ",\"transfers\":[";
            for (size_t t = 0; t < item.transfers.size(); ++t) {
                if (t) out << ",";
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
    out << ",\"summary\":" << q(plan.exportPlanSummary());
    out << "}";
    return toCString(out.str());
}

TRAVEL_API void ts_free_string(char* str) {
    delete[] str;
}
