#include "DataLoader.h"

#include <filesystem>
#include <fstream>
#include <sstream>

#include "JsonParser.h"
#include "../Models/Attraction.h"
#include "../Models/Museum.h"

namespace travel {

namespace {

// Одна смуга/лінія у JSON: або рядок ("tram_line"), або об'єкт
// {"type": "tram_line", "routeName": "Трамвай №8", "speedMultiplier": 1.6,
//  "baseSpeedKmh": 35, "cost": 15, "waitTimeHours": 0.12}.
// Відсутні поля беруться з дефолтів типу лінії.
Lane parseLane(const JsonValue& item) {
    if (item.isString()) {
        LaneType type;
        if (laneTypeFromString(item.asString(), type)) return Lane(type);
        return Lane(LaneType::Sidewalk);
    }
    if (!item.isObject()) return Lane(LaneType::Sidewalk);

    LaneType type = LaneType::Sidewalk;
    laneTypeFromString(item.getString("type", "sidewalk"), type);
    Lane lane(type, item.getString("routeName", item.getString("name", "")));
    lane.speedMultiplier = item.getNumber("speedMultiplier", lane.speedMultiplier);
    lane.baseSpeedKmh = item.getNumber("baseSpeedKmh", lane.baseSpeedKmh);
    lane.cost = item.getNumber("cost", lane.cost);
    lane.waitTimeHours = item.getNumber("waitTimeHours", lane.waitTimeHours);
    return lane;
}

} // namespace

bool DataLoader::load(const std::string& filename,
                      std::vector<City>& cities,
                      std::vector<TouristDestination*>& catalog,
                      std::vector<Route>& routes,
                      std::string& error) {
    clearCatalog(catalog);
    routes.clear();
    cities.clear();

    // u8path: шлях у UTF-8 (з кирилицею) коректно відкривається і на Windows (wide-API),
    // і на Linux/macOS — на відміну від ifstream(const char*), що залежить від ANSI-кодування.
    std::ifstream file(std::filesystem::u8path(filename), std::ios::binary);
    if (!file.is_open()) {
        error = "Failed to open database file: " + filename;
        return false;
    }
    std::ostringstream buffer;
    buffer << file.rdbuf();

    JsonValue root;
    try {
        root = JsonValue::parse(buffer.str());
    } catch (const std::exception& e) {
        error = std::string("JSON parse error: ") + e.what();
        return false;
    }

    if (!root.isObject()) {
        error = "JSON root must be an object";
        return false;
    }

    // --- міста / агломерації ---
    const JsonValue& cityItems = root.at("cities");
    if (cityItems.isArray()) {
        for (const JsonValue& item : cityItems.asArray()) {
            if (!item.isObject()) continue;
            cities.emplace_back(
                item.getInt("id"),
                item.getString("name"),
                item.getString("region", ""),
                item.getString("description", ""));
        }
    }

    // --- каталог туристичних об'єктів (з прив'язкою до міста cityId) ---
    const JsonValue& destinations = root.at("destinations");
    if (destinations.isArray()) {
        for (const JsonValue& item : destinations.asArray()) {
            if (!item.isObject()) continue;
            std::string type = item.getString("type", "attraction");
            int id = item.getInt("id");
            int cityId = item.getInt("cityId", 0);
            std::string name = item.getString("name");
            double cost = item.getNumber("cost");
            double rating = item.getNumber("rating");
            double visitDuration = item.getNumber("visitDuration");
            double openHour = item.getNumber("openHour", 9.0);
            double closeHour = item.getNumber("closeHour", 18.0);
            std::vector<std::string> tags = item.getStringArray("tags");

            if (type == "museum") {
                catalog.push_back(new Museum(
                    id, cityId, name, cost, rating, visitDuration, openHour, closeHour, tags,
                    item.getInt("exhibitsCount"),
                    item.getBool("hasAudioGuide"),
                    item.getString("expositionTheme")));
            } else {
                catalog.push_back(new Attraction(
                    id, cityId, name, cost, rating, visitDuration, openHour, closeHour, tags,
                    item.getBool("isOutdoor"),
                    item.getString("architecturalStyle"),
                    item.getBool("isSeasonal")));
            }
        }
    }

    // --- ребра графів маршрутів міст (з cityId та набором смуг lanes) ---
    const JsonValue& routeItems = root.at("routes");
    if (routeItems.isArray()) {
        for (const JsonValue& item : routeItems.asArray()) {
            if (!item.isObject()) continue;
            std::vector<Lane> lanes;
            const JsonValue& lanesJson = item.at("lanes");
            if (lanesJson.isArray()) {
                for (const JsonValue& lane : lanesJson.asArray()) {
                    lanes.push_back(parseLane(lane));
                }
            }
            routes.emplace_back(
                item.getInt("cityId", 0),
                item.getInt("fromId"),
                item.getInt("toId"),
                item.getNumber("distanceKm"),
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
