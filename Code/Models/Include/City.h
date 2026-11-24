#pragma once

#include <string>

namespace travel {

// Місто / міська агломерація — контейнер туристичних локацій та транспортного графа.
// Кожне місто має унікальний id; об'єкти (TouristDestination) та ребра графа (Route)
// прив'язані до міста через cityId.
class City {
private:
    int id;
    std::string name;
    std::string region;       // область / регіон
    std::string description;  // короткий опис агломерації

public:
    City();
    City(int id, const std::string& name,
         const std::string& region = "", const std::string& description = "");

    int getId() const;
    std::string getName() const;
    std::string getRegion() const;
    std::string getDescription() const;

    void setName(const std::string& newName);
    void setRegion(const std::string& newRegion);
    void setDescription(const std::string& newDescription);
};

} // namespace travel
