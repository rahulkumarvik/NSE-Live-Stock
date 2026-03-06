#include <iostream>
#include <fstream>
#include <string>
#include <iomanip>
#include <unistd.h>
#include <nlohmann/json.hpp>

using namespace std;        // no more std:: everywhere
using json = nlohmann::json;

// ── Load prices from JSON file ────────────────────────────
json loadPrices() {
    ifstream file("/home/coconut/stockengine/tmp/prices.json");

    if (!file.is_open()) {
        cout << "Error: prices.json not found!\n";
        cout << "Make sure price_feed.py is running.\n";
        return {};
    }

    json data;
    file >> data;
    return data;
}

// ── Display live table ────────────────────────────────────
void displayTable(const json& prices) {

    system("clear");

    cout << "================================\n";
    cout << "   NSE LIVE PRICES\n";
    cout << "================================\n\n";

    cout << left
         << setw(15) << "STOCK"
         << setw(15) << "PRICE (Rs)"
         << "\n";

    cout << string(30, '-') << "\n";

    for (auto& item : prices.items()) {
        string name  = item.key();
        float  price = item.value();

        cout << left
             << setw(15) << name
             << setw(15) << fixed
             << setprecision(2) << price
             << "\n";
    }

    cout << string(30, '-') << "\n";
    cout << "\nRefreshing every 5 seconds...\n";
}

// ── Main ──────────────────────────────────────────────────
int main() {

    cout << "Starting NSE viewer...\n";
    cout << "Make sure price_feed.py is running!\n";
    sleep(2);

    while (true) {

        json prices = loadPrices();

        if (!prices.empty()) {
            displayTable(prices);
        } else {
            cout << "Waiting for price feed...\n";
        }

        sleep(5);
    }

    return 0;
}