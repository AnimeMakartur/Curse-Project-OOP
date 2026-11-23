#pragma once

#include <string>
#include <vector>

#include "../Models/Route.h"
#include "../Models/TouristDestination.h"

namespace travel {

// Завантаження локальної бази знань (JSON-файл) у пам'ять:
// каталог туристичних об'єктів та ребра графа маршрутів.
class DataLoader {
public:
    // Читає файл формату travel_db.json (див. schema.md).
    // У разі помилки повертає false і заповнює error описом проблеми.
    static bool load(const std::string& filename,
                     std::vector<TouristDestination*>& catalog,
                     std::vector<Route>& routes,
                     std::string& error);

    // Звільняє пам'ять, виділену під каталог об'єктів.
    static void clearCatalog(std::vector<TouristDestination*>& catalog);
};

} // namespace travel
