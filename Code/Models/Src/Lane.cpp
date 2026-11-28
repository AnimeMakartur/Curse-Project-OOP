#include "Lane.h"

namespace travel {

double Lane::travelTimeHours(double distanceKm) const {

    double speed = effectiveSpeedKmh();
    if (speed <= 0.0)
        speed = 1.0; // захист від ділення на нуль
    return distanceKm / speed + waitTimeHours;
}

} // namespace travel
