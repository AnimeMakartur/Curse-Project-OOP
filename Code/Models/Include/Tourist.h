#pragma once

#include <string>
#include <vector>

namespace travel {

// Турист (користувач): профіль з обраним містом/агломерацією, бюджетом, часом та інтересами.
class Tourist {
  private:
    int id;
    std::string name;
    double inputBudget; // введений бюджет (на день або на всю подорож)
    bool isTotalBudget; // true — inputBudget на всю подорож, false — на один день
    int tripDays;          // тривалість подорожі у днях
    double dailyTimeLimit; // доступний час на один день (год)
    std::vector<std::string> interestTags;
    int targetCityId; // обране місто/агломерація (City::id); -1 — не обрано

  public:
    Tourist();
    Tourist(int id, const std::string& name, double inputBudget, bool isTotalBudget, int tripDays,
            double dailyTimeLimit, const std::vector<std::string>& interestTags,
            int targetCityId = -1);

    // Розрахунковий денний бюджет, формула (1.7):
    // Bday = Binput, якщо бюджет на день; Bday = Binput / Dtrip, якщо на всю подорож.
    double getDailyBudget() const;
    // Загальний бюджет туру, формула (1.8): Btotal = Bday * Dtrip.
    double getTotalBudget() const;
    std::vector<std::string> getInterests() const;

    void updateProfile(double budget, int days, const std::vector<std::string>& tags);

    int getId() const;
    std::string getName() const;
    double getInputBudget() const;
    bool getIsTotalBudget() const;
    int getTripDays() const;
    double getDailyTimeLimit() const;
    int getTargetCityId() const;

    void setName(const std::string& newName);
    void setBudget(double budget, bool isTotal);
    void setTripDays(int days);
    void setDailyTimeLimit(double hours);
    void setInterests(const std::vector<std::string>& tags);
    void setTargetCityId(int cityId);
};

} // namespace travel
