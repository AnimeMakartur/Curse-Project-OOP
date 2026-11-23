#include "Attraction.h"

namespace travel {

Attraction::Attraction(int id, int cityId, const std::string& name, double cost, double rating,
                       double visitDuration, double openHour, double closeHour,
                       const std::vector<std::string>& tags,
                       bool isOutdoor, const std::string& architecturalStyle, bool isSeasonal)
    : TouristDestination(id, cityId, name, cost, rating, visitDuration, openHour, closeHour, tags),
      isOutdoor(isOutdoor), architecturalStyle(architecturalStyle), isSeasonal(isSeasonal) {}

double Attraction::calculateRelevance(const Tourist& t, double w1, double w2, double w3) {
    // Базова формула (1.4) + невеликий бонус за цілорічну доступність пам'ятки
    double score = baseRelevance(t, w1, w2, w3);
    if (!isSeasonal) score += 0.05;
    setRelevance(score);
    return score;
}

std::string Attraction::getDetails() const {
    return "Пам'ятка \"" + name + "\"" +
           (isOutdoor ? ", відкрита" : ", закрита") +
           ", стиль: " + architecturalStyle +
           (isSeasonal ? ", сезонний об'єкт" : ", цілий рік");
}

std::string Attraction::getType() const { return "attraction"; }

bool Attraction::getIsOutdoor() const { return isOutdoor; }
std::string Attraction::getArchitecturalStyle() const { return architecturalStyle; }
bool Attraction::getIsSeasonal() const { return isSeasonal; }

} // namespace travel
