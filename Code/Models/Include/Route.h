#pragma once

#include <string>
#include <vector>

#include "Lane.h"

namespace travel {

// Ребро мультимодального транспортного графа (ділянка дороги між вершинами u та v).
class Route {

  private:
    int cityId;
    int fromId;
    int toId;
    double distanceKm;
    std::vector<Lane> lanes;

  public:
    Route();
    Route(int cityId, int fromId, int toId, double distanceKm, const std::vector<Lane>& lanes = {});

    int getCityId() const;
    int getFromId() const;
    int getToId() const;
    double getDistance() const;

    const std::vector<Lane>& getLanes() const;
    void setLanes(const std::vector<Lane>& newLanes);

    // Чи є хоч одна смуга, що вписується в залишок бюджету.
    bool hasAffordableLane(double remainingBudget, bool allowCar = true) const;
    // Оптимальна смуга: мінімальний час серед тих, що вписуються в бюджет.
    // allowCar=false — car_lane не розглядається.
    Lane chooseBestLane(double remainingBudget, bool allowCar = true) const;

    double optimalTravelTimeHours(double remainingBudget, bool allowCar = true) const;
    double optimalCost(double remainingBudget, bool allowCar = true) const;

    double getTravelTime() const;
    double getTransportCost() const;
};

} // namespace travel
