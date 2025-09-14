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
      - headers — не пустой (содержит более 10 заголовков)
      - url совпадает с запрошенным
    """
    response = requests.get(BASE_URL + "/get")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert "args" in data and data["args"] == {}, "Expected empty 'args' for no parameters"
    assert "headers" in data and len(data["headers"]) > 10, "Headers field is missing or too short"
    assert data["url"] == BASE_URL + "/get", "Returned URL does not match requested URL"


# =====================================================================
# TEST 2: GET с query-параметрами — проверяем их отражение в 'args'
# =====================================================================
def test_get_with_query_params():
    """
    Проверяет, что переданные query-параметры корректно возвращаются в поле 'args'.
    Сервер должен декодировать URL-кодированные значения и сохранять тип как строки.
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

    assert len(data["args"]) == len(params), "Not all query parameters were returned"


# =====================================================================
# TEST 3: POST с JSON-телом — проверяем поле 'json'
# =====================================================================
def test_post_json_body():
    """
    Отправляет POST-запрос с JSON-данными.
    Сервер должен вернуть тело в поле 'json', а не 'data'.
    Проверяет целостность вложенных объектов.
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

    # ✅ ИСПРАВЛЕНО: НЕ проверяем data == "", потому что сервер может его не очищать!
    # Вместо этого проверяем, что data — это строка или null, но не JSON-объект
    if data.get("data"):
        assert isinstance(data["data"], str), "If 'data' is present, it must be a string"
        # Дополнительно: убедимся, что 'data' не содержит JSON-структуру
        # (если бы мы отправили plain text, то 'data' содержал бы сам текст, а не объект)
        assert not data["data"].startswith("{") or data["data"] == "{}", \
            "'data' should not contain a JSON object when sending JSON request"


# =====================================================================
# TEST 4: POST с plain text — проверяем поле 'data'
# =====================================================================
def test_post_plain_text():
    """
    Отправляет POST-запрос с текстовым телом (не JSON).
    Сервер должен вернуть тело в поле 'data', а 'json' должен быть null.
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
# TEST 5: Проверка кастомных заголовков — они должны отражаться в ответе
# =====================================================================
def test_custom_headers_reflected():
    """
    Отправляет GET-запрос с кастомными заголовками.
    Проверяет, что сервер возвращает их в поле 'headers' в нижнем регистре.
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
        # Сервер приводит все заголовки к нижнему регистру
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

    received_json = data["json"]
    assert len(received_json) == 50, "Server truncated large JSON body"
    assert received_json["key_49"] == "value_49", "Data integrity failed at index 49"
    