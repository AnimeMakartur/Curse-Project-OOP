#include "Tourist.h"

namespace travel {

Tourist::Tourist()
    : id(0), name(""), inputBudget(0.0), isTotalBudget(false),
      tripDays(1), dailyTimeLimit(8.0), targetCityId(-1) {}

Tourist::Tourist(int id, const std::string& name, double inputBudget, bool isTotalBudget,
                 int tripDays, double dailyTimeLimit, const std::vector<std::string>& interestTags,
                 int targetCityId)
    : id(id), name(name), inputBudget(inputBudget), isTotalBudget(isTotalBudget),
      tripDays(tripDays > 0 ? tripDays : 1), dailyTimeLimit(dailyTimeLimit),
      interestTags(interestTags), targetCityId(targetCityId) {}

double Tourist::getDailyBudget() const {
    if (isTotalBudget) {
        return tripDays > 0 ? inputBudget / tripDays : inputBudget;
    }
    return inputBudget;
}

double Tourist::getTotalBudget() const {
    return getDailyBudget() * tripDays;
}

std::vector<std::string> Tourist::getInterests() const {
    return interestTags;
}

void Tourist::updateProfile(double budget, int days, const std::vector<std::string>& tags) {
    inputBudget = budget;
    tripDays = days > 0 ? days : 1;
    interestTags = tags;
}

int Tourist::getId() const { return id; }
std::string Tourist::getName() const { return name; }
double Tourist::getInputBudget() const { return inputBudget; }
bool Tourist::getIsTotalBudget() const { return isTotalBudget; }
int Tourist::getTripDays() const { return tripDays; }
double Tourist::getDailyTimeLimit() const { return dailyTimeLimit; }
int Tourist::getTargetCityId() const { return targetCityId; }

void Tourist::setName(const std::string& newName) { name = newName; }

void Tourist::setBudget(double budget, bool isTotal) { inputBudget = budget; isTotalBudget = isTotal; }

void Tourist::setTripDays(int days) { tripDays = days > 0 ? days : 1; }

void Tourist::setDailyTimeLimit(double hours) { dailyTimeLimit = hours; }

void Tourist::setInterests(const std::vector<std::string>& tags) { interestTags = tags; }

void Tourist::setTargetCityId(int cityId) { targetCityId = cityId; }

} // namespace travel
