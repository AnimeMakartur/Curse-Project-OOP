#include "TouristDestination.h"
#include "Tourist.h"

#include <algorithm>

namespace travel {

static const double RATING_MAX = 5.0; // максимальний бал рейтингу в системі

TouristDestination::TouristDestination(int id, const std::string& name, double cost,
                                       double rating, double visitDuration,
                                       double openHour, double closeHour,
                                       const std::vector<std::string>& tags)
    : id(id), name(name), cost(cost), rating(rating), visitDuration(visitDuration),
      openHour(openHour), closeHour(closeHour), tags(tags), relevanceScore(0.0) {}

double TouristDestination::baseRelevance(const Tourist& t, double w1, double w2, double w3) const {
    double ratingPart = (RATING_MAX > 0.0) ? w1 * rating / RATING_MAX : 0.0;

    std::vector<std::string> interests = t.getInterests();
    double tagsPart = 0.0;
    if (!interests.empty()) {
        size_t common = 0;
        for (const std::string& tag : tags) {
            if (std::find(interests.begin(), interests.end(), tag) != interests.end()) {
                ++common;
            }
        }
        tagsPart = w2 * static_cast<double>(common) / static_cast<double>(interests.size());
    }

    double budget = t.getDailyBudget();
    double costPart = (budget > 0.0) ? w3 * cost / budget : 0.0;

    return ratingPart + tagsPart - costPart;
}

int TouristDestination::getId() const { return id; }
std::string TouristDestination::getName() const { return name; }
double TouristDestination::getCost() const { return cost; }
double TouristDestination::getRating() const { return rating; }
double TouristDestination::getVisitDuration() const { return visitDuration; }
double TouristDestination::getOpenHour() const { return openHour; }
double TouristDestination::getCloseHour() const { return closeHour; }
const std::vector<std::string>& TouristDestination::getTags() const { return tags; }
double TouristDestination::getRelevance() const { return relevanceScore; }
void TouristDestination::setRelevance(double score) { relevanceScore = score; }

bool TouristDestination::isOpen(double currentHour) const {
    return currentHour >= openHour && currentHour <= closeHour;
}

} // namespace travel
