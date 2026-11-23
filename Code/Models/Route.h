#pragma once

#include <string>
#include <vector>

#include "Lane.h"

namespace travel {

// Ребро мультимодального транспортного графа (ділянка дороги між вершинами u та v).
// Містить cityId (місто/агломерація), довжину distanceKm та набір доступних
// смуг/ліній lanes (тротуар, велодоріжка, авто-, автобусна смуга, метробус,
// швидкісний трамвай, приміська електричка, залізниця).
class Route {
private:
    int cityId;
    int fromId;
    int toId;
    double distanceKm;
    std::vector<Lane> lanes;

public:
    Route();
    Route(int cityId, int fromId, int toId, double distanceKm,
          const std::vector<Lane>& lanes = {});

    int getCityId() const;
    int getFromId() const;
    int getToId() const;
    double getDistance() const;

    const std::vector<Lane>& getLanes() const;
    void setLanes(const std::vector<Lane>& newLanes);
    std::vector<std::string> getLaneNames() const;   // назви типів смуг
    std::string getRoadDescription() const;          // людиночитний опис дороги

    // Чи є хоч одна смуга, що вписується в залишок бюджету.
    bool hasAffordableLane(double remainingBudget) const;
    // Оптимальна смуга/лінія: мінімальний сумарний час переміщення серед тих,
    // що вписуються в залишок бюджету туриста:
    //   t(u,v) = min_l ( distanceKm / (v_base * k_speed(l)) + t_wait(l) )
    // Якщо жодна платна лінія не доступна — береться найдешевша (зазвичай тротуар).
    Lane chooseBestLane(double remainingBudget) const;

    double optimalTravelTimeHours(double remainingBudget) const; // час найкращої смуги
    double optimalCost(double remainingBudget) const;             // вартість найкращої смуги

    // Сумісні гетери (без обмеження бюджету — найшвидша смуга).
    double getTravelTime() const;
    double getTransportCost() const;
};

} // namespace travel
