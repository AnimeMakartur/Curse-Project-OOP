#pragma once

#include <string>
#include <vector>

namespace travel {

class Tourist;

// Базовий абстрактний клас точки інтересу (туристичного об'єкта).
class TouristDestination {
protected:
    int id;
    std::string name;
    double cost;            // вартість вхідного квитка
    double rating;          // рейтинг (0..5)
    double visitDuration;   // середній час огляду (год)
    double openHour;        // година відкриття
    double closeHour;       // година закриття
    std::vector<std::string> tags; // теги категорій
    double relevanceScore;  // інтегральна оцінка релевантності (розраховується)

    // Спільна частина формули релевантності (1.4):
    // S = w1*R/Rmax + w2*|Tags ∩ Utags|/|Utags| - w3*c/Bday
    double baseRelevance(const Tourist& t, double w1, double w2, double w3) const;

public:
    TouristDestination(int id, const std::string& name, double cost, double rating,
                       double visitDuration, double openHour, double closeHour,
                       const std::vector<std::string>& tags);
    virtual ~TouristDestination() = default;

    int getId() const;
    std::string getName() const;
    double getCost() const;
    double getRating() const;
    double getVisitDuration() const;
    double getOpenHour() const;
    double getCloseHour() const;
    const std::vector<std::string>& getTags() const;
    double getRelevance() const;
    void setRelevance(double score);

    bool isOpen(double currentHour) const;

    // Поліморфні методи — реалізуються у похідних класах
    virtual double calculateRelevance(const Tourist& t, double w1, double w2, double w3) = 0;
    virtual std::string getDetails() const = 0;
    virtual std::string getType() const = 0;
};

} // namespace travel
