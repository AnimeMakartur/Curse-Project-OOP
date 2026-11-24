#pragma once

// Мінімальний JSON-парсер (без зовнішніх залежностей), достатній для
// читання локальної бази даних проєкту. Підтримує: null, true/false,
// числа, рядки (з екрануванням та \uXXXX), масиви, об'єкти.

#include <cctype>
#include <cmath>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

namespace travel {

class JsonValue {
  public:
    enum class Type { Null, Bool, Number, String, Array, Object };

    Type type = Type::Null;
    bool boolValue = false;
    double numberValue = 0.0;
    std::string stringValue;
    std::vector<JsonValue> arrayValue;
    std::map<std::string, JsonValue> objectValue;

    JsonValue() = default;

    bool isNull() const { return type == Type::Null; }
    bool isBool() const { return type == Type::Bool; }
    bool isNumber() const { return type == Type::Number; }
    bool isString() const { return type == Type::String; }
    bool isArray() const { return type == Type::Array; }
    bool isObject() const { return type == Type::Object; }

    bool asBool() const { return boolValue; }
    double asNumber() const { return numberValue; }
    const std::string& asString() const { return stringValue; }
    const std::vector<JsonValue>& asArray() const { return arrayValue; }
    const std::map<std::string, JsonValue>& asObject() const { return objectValue; }

    bool has(const std::string& key) const {
        return type == Type::Object && objectValue.find(key) != objectValue.end();
    }

    const JsonValue& at(const std::string& key) const {
        static const JsonValue nullValue;
        if (type != Type::Object)
            return nullValue;
        auto it = objectValue.find(key);
        return it != objectValue.end() ? it->second : nullValue;
    }

    const JsonValue& operator[](const std::string& key) const { return at(key); }

    // Зручні гетери з значенням за замовчуванням
    double getNumber(const std::string& key, double def = 0.0) const {
        const JsonValue& v = at(key);
        return v.isNumber() ? v.numberValue : def;
    }
    std::string getString(const std::string& key, const std::string& def = "") const {
        const JsonValue& v = at(key);
        return v.isString() ? v.stringValue : def;
    }
    bool getBool(const std::string& key, bool def = false) const {
        const JsonValue& v = at(key);
        return v.isBool() ? v.boolValue : def;
    }
    int getInt(const std::string& key, int def = 0) const {
        return static_cast<int>(getNumber(key, def));
    }
    std::vector<std::string> getStringArray(const std::string& key) const {
        std::vector<std::string> result;
        const JsonValue& v = at(key);
        if (v.isArray()) {
            for (const JsonValue& item : v.arrayValue) {
                if (item.isString())
                    result.push_back(item.stringValue);
            }
        }
        return result;
    }

    static JsonValue parse(const std::string& text) {
        Parser parser(text);
        JsonValue value = parser.parseValue();
        parser.skipWhitespace();
        if (!parser.atEnd())
            throw std::runtime_error("JSON: зайві дані після кореня");
        return value;
    }

  private:
    class Parser {
      public:
        explicit Parser(const std::string& text) : text(text), pos(0) {}

        bool atEnd() const { return pos >= text.size(); }

        void skipWhitespace() {
            while (pos < text.size() && std::isspace(static_cast<unsigned char>(text[pos])))
                ++pos;
        }

        JsonValue parseValue() {
            skipWhitespace();
            if (atEnd())
                throw std::runtime_error("JSON: неочікуваний кінець");
            char c = text[pos];
            if (c == '{')
                return parseObject();
            if (c == '[')
                return parseArray();
            if (c == '"') {
                JsonValue v;
                v.type = Type::String;
                v.stringValue = parseString();
                return v;
            }
            if (c == 't' || c == 'f')
                return parseBool();
            if (c == 'n')
                return parseNull();
            return parseNumber();
        }

      private:
        const std::string& text;
        size_t pos;

        char peek() const {
            if (atEnd())
                throw std::runtime_error("JSON: неочікуваний кінець");
            return text[pos];
        }

        void expect(char c) {
            if (atEnd() || text[pos] != c)
                throw std::runtime_error(std::string("JSON: очікувався символ '") + c + "'");
            ++pos;
        }

        JsonValue parseObject() {
            JsonValue v;
            v.type = Type::Object;
            expect('{');
            skipWhitespace();
            if (!atEnd() && text[pos] == '}') {
                ++pos;
                return v;
            }
            while (true) {
                skipWhitespace();
                std::string key = parseString();
                skipWhitespace();
                expect(':');
                v.objectValue[key] = parseValue();
                skipWhitespace();
                char c = peek();
                if (c == ',') {
                    ++pos;
                    continue;
                }
                if (c == '}') {
                    ++pos;
                    break;
                }
                throw std::runtime_error("JSON: очікувалося ',' або '}' в об'єкті");
            }
            return v;
        }

        JsonValue parseArray() {
            JsonValue v;
            v.type = Type::Array;
            expect('[');
            skipWhitespace();
            if (!atEnd() && text[pos] == ']') {
                ++pos;
                return v;
            }
            while (true) {
                v.arrayValue.push_back(parseValue());
                skipWhitespace();
                char c = peek();
                if (c == ',') {
                    ++pos;
                    continue;
                }
                if (c == ']') {
                    ++pos;
                    break;
                }
                throw std::runtime_error("JSON: очікувалося ',' або ']' у масиві");
            }
            return v;
        }

        std::string parseString() {
            expect('"');
            std::string result;
            while (true) {
                if (atEnd())
                    throw std::runtime_error("JSON: незакритий рядок");
                char c = text[pos++];
                if (c == '"')
                    break;
                if (c == '\\') {
                    if (atEnd())
                        throw std::runtime_error("JSON: незакритий екрануючий символ");
                    char esc = text[pos++];
                    switch (esc) {
                    case '"':
                        result += '"';
                        break;
                    case '\\':
                        result += '\\';
                        break;
                    case '/':
                        result += '/';
                        break;
                    case 'b':
                        result += '\b';
                        break;
                    case 'f':
                        result += '\f';
                        break;
                    case 'n':
                        result += '\n';
                        break;
                    case 'r':
                        result += '\r';
                        break;
                    case 't':
                        result += '\t';
                        break;
                    case 'u': {
                        if (pos + 4 > text.size())
                            throw std::runtime_error("JSON: замалий \\uXXXX");
                        unsigned code = 0;
                        for (int i = 0; i < 4; ++i) {
                            char h = text[pos++];
                            code <<= 4;
                            if (h >= '0' && h <= '9')
                                code += h - '0';
                            else if (h >= 'a' && h <= 'f')
                                code += h - 'a' + 10;
                            else if (h >= 'A' && h <= 'F')
                                code += h - 'A' + 10;
                            else
                                throw std::runtime_error("JSON: некоректний \\uXXXX");
                        }
                        // UTF-8 кодування code point (спрощено, без сурогатних пар)
                        if (code < 0x80) {
                            result += static_cast<char>(code);
                        } else if (code < 0x800) {
                            result += static_cast<char>(0xC0 | (code >> 6));
                            result += static_cast<char>(0x80 | (code & 0x3F));
                        } else {
                            result += static_cast<char>(0xE0 | (code >> 12));
                            result += static_cast<char>(0x80 | ((code >> 6) & 0x3F));
                            result += static_cast<char>(0x80 | (code & 0x3F));
                        }
                        break;
                    }
                    default:
                        throw std::runtime_error("JSON: невідомий екрануючий символ");
                    }
                } else {
                    result += c;
                }
            }
            return result;
        }

        JsonValue parseNumber() {
            size_t start = pos;
            if (!atEnd() && (text[pos] == '-' || text[pos] == '+'))
                ++pos;
            while (!atEnd() &&
                   (std::isdigit(static_cast<unsigned char>(text[pos])) || text[pos] == '.' ||
                    text[pos] == 'e' || text[pos] == 'E' || text[pos] == '+' || text[pos] == '-')) {
                ++pos;
            }
            if (start == pos)
                throw std::runtime_error("JSON: очікувалося число");
            JsonValue v;
            v.type = Type::Number;
            v.numberValue = std::stod(text.substr(start, pos - start));
            return v;
        }

        JsonValue parseBool() {
            JsonValue v;
            v.type = Type::Bool;
            if (text.compare(pos, 4, "true") == 0) {
                v.boolValue = true;
                pos += 4;
                return v;
            }
            if (text.compare(pos, 5, "false") == 0) {
                v.boolValue = false;
                pos += 5;
                return v;
            }
            throw std::runtime_error("JSON: очікувалося true/false");
        }

        JsonValue parseNull() {
            if (text.compare(pos, 4, "null") == 0) {
                pos += 4;
                JsonValue v;
                v.type = Type::Null;
                return v;
            }
            throw std::runtime_error("JSON: очікувалося null");
        }
    };
};

} // namespace travel
