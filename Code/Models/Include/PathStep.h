#pragma once

#include "Lane.h"
#include "Route.h"

namespace travel {

// Один деталізований крок маршруту: ребро графа + обрана на ньому смуга/лінія
// транспорту з розрахованим часом і вартістю переходу.
struct PathStep {
    Route route;
    Lane lane;              // обраний вид транспорту / смуга
    double timeHours = 0.0; // час переходу цією смугою, год
    double cost = 0.0;      // вартість проїзду, EUR

    PathStep();
    PathStep(const Route& r, const Lane& l);
};

} // namespace travel
