#include "PathStep.h"

namespace travel {

PathStep::PathStep() : route(), lane() {}

PathStep::PathStep(const Route& r, const Lane& l)
    : route(r), lane(l), timeHours(l.travelTimeHours(r.getDistance())), cost(l.cost) {}

} // namespace travel
