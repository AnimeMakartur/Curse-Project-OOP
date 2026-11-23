#include "Museum.h"

namespace travel {

Museum::Museum(int id, int cityId, const std::string& name, double cost, double rating,
               double visitDuration, double openHour, double closeHour,
               const std::vector<std::string>& tags,
               int exhibitsCount, bool hasAudioGuide, const std::string& expositionTheme)
    : TouristDestination(id, cityId, name, cost, rating, visitDuration, openHour, closeHour, tags),
      exhibitsCount(exhibitsCount), hasAudioGuide(hasAudioGuide),
      expositionTheme(expositionTheme) {}

double Museum::calculateRelevance(const Tourist& t, double w1, double w2, double w3) {
    // Базова формула (1.4) + невеликий бонус за наявність аудіогіда
    double score = baseRelevance(t, w1, w2, w3);
    if (hasAudioGuide) score += 0.05;
    setRelevance(score);
    return score;
}

std::string Museum::getDetails() const {
    return "Музей \"" + name + "\", тема експозиції: " + expositionTheme +
           ", експонатів: " + std::to_string(exhibitsCount) +
           (hasAudioGuide ? ", є аудіогід" : ", без аудіогіда");
}

std::string Museum::getType() const { return "museum"; }

int Museum::getExhibitsCount() const { return exhibitsCount; }
bool Museum::getHasAudioGuide() const { return hasAudioGuide; }
std::string Museum::getExpositionTheme() const { return expositionTheme; }

} // namespace travel
