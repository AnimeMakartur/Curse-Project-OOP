#pragma once

#include "TouristDestination.h"

namespace travel {

// Туристична пам'ятка — похідний клас від TouristDestination.
class Attraction : public TouristDestination {
  private:
    bool isOutdoor;
    std::string architecturalStyle;
    bool isSeasonal;

  public:
    Attraction(int id, int cityId, const std::string& name, double cost, double rating,
               double visitDuration, double openHour, double closeHour,
               const std::vector<std::string>& tags, bool isOutdoor,
               const std::string& architecturalStyle, bool isSeasonal);

    double calculateRelevance(const Tourist& t, double w1, double w2, double w3) override;
    std::string getDetails() const override;
    std::string getType() const override;

    bool getIsOutdoor() const;
    std::string getArchitecturalStyle() const;
    bool getIsSeasonal() const;
};

} // namespace travel
