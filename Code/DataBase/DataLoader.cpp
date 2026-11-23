#include "DataLoader.h"

#include <fstream>
#include <sstream>

#include "JsonParser.h"
#include "../Models/Attraction.h"
#include "../Models/Museum.h"

namespace travel {

bool DataLoader::load(const std::string& filename,
                      std::vector<TouristDestination*>& catalog,
                      std::vector<Route>& routes,
                      std::string& error) {
    clearCatalog(catalog);
    routes.clear();

    std::ifstream file(filename, std::ios::binary);
    if (!file.is_open()) {
        error = "Не вдалося відкрити файл бази даних: " + filename;
        return false;
    }
    std::ostringstream buffer;
    buffer << file.rdbuf();

    JsonValue root;
    try {
        root = JsonValue::parse(buffer.str());
    } catch (const std::exception& e) {
        error = std::string("Помилка розбору JSON: ") + e.what();
        return false;
    }

    if (!root.isObject()) {
        error = "Корінь JSON має бути об'єктом";
        return false;
    }

    // --- каталог туристичних об'єктів ---
    const JsonValue& destinations = root.at("destinations");
    if (destinations.isArray()) {
        for (const JsonValue& item : destinations.asArray()) {
            if (!item.isObject()) continue;
            std::string type = item.getString("type", "attraction");
            int id = item.getInt("id");
            std::string name = item.getString("name");
            double cost = item.getNumber("cost");
            double rating = item.getNumber("rating");
            double visitDuration = item.getNumber("visitDuration");
            double openHour = item.getNumber("openHour", 9.0);
            double closeHour = item.getNumber("closeHour", 18.0);
            std::vector<std::string> tags = item.getStringArray("tags");

            if (type == "museum") {
                catalog.push_back(new Museum(
                    id, name, cost, rating, visitDuration, openHour, closeHour, tags,
                    item.getInt("exhibitsCount"),
                    item.getBool("hasAudioGuide"),
                    item.getString("expositionTheme")));
            } else {
                catalog.push_back(new Attraction(
                    id, name, cost, rating, visitDuration, openHour, closeHour, tags,
                    item.getBool("isOutdoor"),
                    item.getString("architecturalStyle"),
                    item.getBool("isSeasonal")));
            }
        }
    }

    // --- ребра графа маршрутів ---
    const JsonValue& routeItems = root.at("routes");
    if (routeItems.isArray()) {
        for (const JsonValue& item : routeItems.asArray()) {
            if (!item.isObject()) continue;
            std::vector<LaneType> lanes;
            const JsonValue& lanesJson = item.at("lanes");
            if (lanesJson.isArray()) {
                for (const JsonValue& lane : lanesJson.asArray()) {
                    LaneType laneType;
                    if (lane.isString() && laneTypeFromString(lane.asString(), laneType)) {
                        lanes.push_back(laneType);
                    }
                }
            }
            routes.emplace_back(
                item.getInt("fromId"),
                item.getInt("toId"),
                item.getNumber("distanceKm"),
                item.getNumber("travelTimeHours"),
                item.getNumber("transportCost"),
                item.getNumber("dailyTimeLimit", 8.0),
                lanes);
        }
    }

    return true;
}

void DataLoader::clearCatalog(std::vector<TouristDestination*>& catalog) {
    for (TouristDestination* dest : catalog) delete dest;
    catalog.clear();
}

} // namespace travel
