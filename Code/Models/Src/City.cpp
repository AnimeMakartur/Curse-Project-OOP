#include "City.h"

namespace travel {

City::City() : id(0), name(""), region(""), description("") {}

City::City(int id, const std::string& name,
           const std::string& region, const std::string& description)
    : id(id), name(name), region(region), description(description) {}

int City::getId() const { return id; }
std::string City::getName() const { return name; }
std::string City::getRegion() const { return region; }
std::string City::getDescription() const { return description; }

void City::setName(const std::string& newName) { name = newName; }
void City::setRegion(const std::string& newRegion) { region = newRegion; }
void City::setDescription(const std::string& newDescription) { description = newDescription; }

} // namespace travel
