// C API поверх ядра TravelSystem — точка входу для Python GUI (ctypes).
// Рядки, що повертаються, виділяються у купі; Python має звільнити їх через ts_free_string.

#include <cstdio>
#include <cstring>
#include <sstream>
#include <string>
#include <vector>

#include "TravelSystem.h"
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

std::string tagsToJson(const std::vector<std::string>& tags) {
    std::string out = "[";
    for (size_t i = 0; i < tags.size(); ++i) {
        if (i) out += ",";
        out += q(tags[i]);
    }
    out += "]";
    return out;
}

std::string lanesToJson(const Route& route) {
    std::string out = "[";
    const auto& lanes = route.getLanes();
    for (size_t i = 0; i < lanes.size(); ++i) {
        if (i) out += ",";
        out += q(laneTypeToString(lanes[i]));
    }
    out += "]";
    return out;
}

std::string routeToJson(const Route& r) {
    std::ostringstream out;
    out << "{"
        << "\"fromId\":" << r.getFromId()
        << ",\"toId\":" << r.getToId()
        << ",\"distanceKm\":" << r.getDistance()
        << ",\"travelTimeHours\":" << r.getTravelTime()
        << ",\"transportCost\":" << r.getTransportCost()
        << ",\"lanes\":" << lanesToJson(r)
        << "}";
    return out.str();
}

std::string destinationToJson(const TouristDestination* d) {
    std::ostringstream out;
    out << "{"
        << "\"id\":" << d->getId()
        << ",\"type\":" << q(d->getType())
        << ",\"name\":" << q(d->getName())
        << ",\"cost\":" << d->getCost()
        << ",\"rating\":" << d->getRating()
        << ",\"visitDuration\":" << d->getVisitDuration()
        << ",\"openHour\":" << d->getOpenHour()
        << ",\"closeHour\":" << d->getCloseHour()
        << ",\"tags\":" << tagsToJson(d->getTags())
        << ",\"relevance\":" << d->getRelevance()
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

std::vector<std::string> splitCsv(const std::string& text) {
    std::vector<std::string> result;
    std::string current;
    std::istringstream stream(text);
    while (std::getline(stream, current, ',')) {
        // обрізка пробілів
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
    if (!handle || !filename) return 0;
    std::string error;
    return asSystem(handle)->loadData(filename, error) ? 1 : 0;
}

TRAVEL_API const char* ts_last_error() {
    return ""; // зарезервовано для розширення
}

TRAVEL_API void ts_set_tourist(void* handle, int id, const char* name,
                               double budget, int isTotalBudget, int days,
                               double dailyTimeLimit, const char* interestsCsv) {
    if (!handle) return;
    std::vector<std::string> tags = interestsCsv ? splitCsv(interestsCsv) : std::vector<std::string>();
    Tourist tourist(id, name ? name : "", budget, isTotalBudget != 0, days, dailyTimeLimit, tags);
    asSystem(handle)->setTouristProfile(tourist);
}

TRAVEL_API char* ts_get_profile(void* handle) {
    if (!handle) return toCString("{}");
    const Tourist& t = asSystem(handle)->getTourist();
    std::ostringstream out;
    out << "{"
        << "\"id\":" << t.getId()
        << ",\"name\":" << q(t.getName())
        << ",\"inputBudget\":" << t.getInputBudget()
        << ",\"isTotalBudget\":" << (t.getIsTotalBudget() ? "true" : "false")
        << ",\"tripDays\":" << t.getTripDays()
        << ",\"dailyTimeLimit\":" << t.getDailyTimeLimit()
        << ",\"dailyBudget\":" << t.getDailyBudget()
        << ",\"totalBudget\":" << t.getTotalBudget()
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

TRAVEL_API char* ts_find_shortest_path(void* handle, int fromId, int toId) {
    if (!handle) return toCString("[]");
    std::vector<Route> path = asSystem(handle)->findShortestPath(fromId, toId);
    std::string out = "[";
    for (size_t i = 0; i < path.size(); ++i) {
        if (i) out += ",";
        out += routeToJson(path[i]);
    }
    out += "]";
    return toCString(out);
}

TRAVEL_API char* ts_generate_plan(void* handle) {
    if (!handle) return toCString("{}");
    TravelPlan plan = asSystem(handle)->generatePersonalizedPlan();

    std::ostringstream out;
    out << "{";
    out << "\"tourist\":" << q(plan.getTourist().getName());
    out << ",\"days\":[";
    const auto& days = plan.getDailyDestinations();
    const auto& dayRoutes = plan.getDailyRoutes();
    for (size_t d = 0; d < days.size(); ++d) {
        if (d) out << ",";
        out << "{\"day\":" << (d + 1) << ",\"destinations\":[";
        for (size_t i = 0; i < days[d].size(); ++i) {
            if (i) out << ",";
            out << destinationToJson(days[d][i]);
        }
        out << "],\"routes\":[";
        for (size_t i = 0; i < dayRoutes[d].size(); ++i) {
            if (i) out << ",";
            out << routeToJson(dayRoutes[d][i]);
        }
        out << "]}";
    }
    out << "],\"totalCost\":" << plan.getTotalCost()
        << ",\"totalDuration\":" << plan.getTotalDuration()
        << ",\"summary\":" << q(plan.exportPlanSummary())
        << "}";
    return toCString(out.str());
}

TRAVEL_API void ts_free_string(char* str) {
    delete[] str;
}
