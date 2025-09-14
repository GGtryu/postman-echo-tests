
import requests
import pytest

BASE_URL = "https://postman-echo.com"

# =====================================================================
# TEST 1: GET без параметров — базовый чек
# =====================================================================
def test_get_empty():
    """
    Тестирует GET-запрос без query-параметров.
    Проверяет:
      - Статус-код 200
      - Ответ содержит 'args', 'headers', 'url'
      - args — пустой словарь
      - headers — не пустой
      - url совпадает с запрошенным
    """
    response = requests.get(BASE_URL + "/get")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert "args" in data and data["args"] == {}, "Expected empty args for no parameters"
    assert "headers" in data and len(data["headers"]) > 10, "Headers field is missing or empty"
    assert data["url"] == BASE_URL + "/get", "Returned URL does not match requested URL"


# =====================================================================
# TEST 2: GET с query-параметрами — проверяем 'args'
# =====================================================================
def test_get_with_query_params():
    """
    Отправляет GET с параметрами и проверяет, что они корректно возвращаются в 'args'.
    Проверяет кириллицу, числа, строки.
    """
    params = {
        "name": "Alex",
        "age": "25",
        "city": "Москва",  # Кирриллица — проверка кодировки
        "active": "true"
    }

    response = requests.get(BASE_URL + "/get", params=params)
    assert response.status_code == 200

    data = response.json()
    for key, value in params.items():
        assert data["args"].get(key) == str(value), \
            f"Query param '{key}' expected '{value}', got '{data['args'].get(key)}'"

    assert len(data["args"]) == len(params), "Not all parameters were returned"


# =====================================================================
# TEST 3: POST с JSON — проверяем поле 'json'
# =====================================================================
def test_post_json_body():
    """
    Отправляет POST с JSON-телом.
    Проверяет, что данные попадают в 'json', а не в 'data'.
    Проверяет вложенные объекты.
    """
    json_data = {
        "user_id": 123,
        "username": "test_user",
        "preferences": {
            "theme": "dark",
            "notifications": True
        }
    }

    response = requests.post(BASE_URL + "/post", json=json_data)
    assert response.status_code == 200

    data = response.json()
    assert "json" in data, "Response missing 'json' field for JSON body"
    assert data["json"] == json_data, "JSON body was modified by server"
    assert data["data"] == "", "Plain text 'data' field should be empty when sending JSON"


# =====================================================================
# TEST 4: POST с plain text — проверяем поле 'data'
# =====================================================================
def test_post_plain_text():
    """
    Отправляет POST с текстовым телом (не JSON).
    Проверяет, что данные попадают в 'data', а 'json' = null.
    """
    text_body = "Hello from Python!"

    response = requests.post(
        BASE_URL + "/post",
        data=text_body,
        headers={"Content-Type": "text/plain"}
    )
    assert response.status_code == 200

    data = response.json()
    assert "data" in data, "Response missing 'data' field for plain text"
    assert data["data"] == text_body, "Plain text body was altered"
    assert data["json"] is None, "JSON field should be null when sending plain text"


# =====================================================================
# TEST 5: Проверка кастомных заголовков — они должны отражаться
# =====================================================================
def test_custom_headers_reflected():
    """
    Отправляет GET с кастомными заголовками.
    Проверяет, что сервер возвращает их в 'headers' в нижнем регистре.
    """
    custom_headers = {
        "X-API-Key": "abc123xyz",
        "X-Client": "Python-Test-Script",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "MyCustomBot/1.0"
    }

    response = requests.get(BASE_URL + "/get", headers=custom_headers)
    assert response.status_code == 200

    data = response.json()
    for header_name, header_value in custom_headers.items():
        # Сервер приводит заголовки к нижнему регистру
        lower_header = header_name.lower()
        assert lower_header in data["headers"], f"Header '{header_name}' not found in response"
        assert data["headers"][lower_header] == header_value, \
            f"Header '{header_name}' value mismatch. Expected '{header_value}', got '{data['headers'][lower_header]}'"


# =====================================================================
# TEST 6: Большой JSON — проверяем целостность и ограничения
# =====================================================================
def test_large_json_body():
    """
    Отправляет POST с 50 ключами. Проверяет, что сервер не обрезает данные.
    """
    large_data = {f"key_{i}": f"value_{i}" for i in range(50)}

    response = requests.post(BASE_URL + "/post", json=large_data)
    assert response.status_code == 200

    data = response.json()
    received = data["json"]
    assert len(received) == 50, "Server truncated large JSON body"
    assert received["key_49"] == "value_49", "Data integrity failed at index 49"



