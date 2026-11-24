#pragma once

#include <string>
#include <vector>

#include "City.h"
#include "Route.h"
#include "TouristDestination.h"

namespace travel {

// Завантаження локальної бази знань (JSON-файл) у пам'ять:
// міста/агломерації (cities), каталог туристичних об'єктів (destinations)
// та ребра транспортних графів міст (routes).
class DataLoader {
public:
    // Читає файл формату travel_db.json (див. schema.md).
    // У разі помилки повертає false і заповнює error описом проблеми.
    static bool load(const std::string& filename,
                     std::vector<City>& cities,
                     std::vector<TouristDestination*>& catalog,
                     std::vector<Route>& routes,
                     std::string& error);

    // Звільняє пам'ять, виділену під каталог об'єктів.
    static void clearCatalog(std::vector<TouristDestination*>& catalog);
};

} // namespace travel
