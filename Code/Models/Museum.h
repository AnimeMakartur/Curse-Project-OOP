#pragma once

#include "TouristDestination.h"

namespace travel {

// Музейний заклад — похідний клас від TouristDestination.
class Museum : public TouristDestination {
private:
    int exhibitsCount;
    bool hasAudioGuide;
    std::string expositionTheme;

public:
    Museum(int id, const std::string& name, double cost, double rating,
           double visitDuration, double openHour, double closeHour,
           const std::vector<std::string>& tags,
           int exhibitsCount, bool hasAudioGuide, const std::string& expositionTheme);

    double calculateRelevance(const Tourist& t, double w1, double w2, double w3) override;
    std::string getDetails() const override;
    std::string getType() const override;

    int getExhibitsCount() const;
    bool getHasAudioGuide() const;
    std::string getExpositionTheme() const;
};

} // namespace travel
