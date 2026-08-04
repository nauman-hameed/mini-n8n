import requests


def execute_api_node(node_data: dict):
    api_url = node_data.get("apiUrl")
    method = node_data.get("method", "GET").upper()

    if not api_url:
        raise ValueError("API URL is missing.")

    if method == "GET":
        response = requests.get(
            api_url,
            timeout=15,
        )

    elif method == "POST":
        response = requests.post(
            api_url,
            json={},
            timeout=15,
        )

    else:
        raise ValueError(
            f"Unsupported API method: {method}"
        )

    response.raise_for_status()

    try:
        response_data = response.json()
    except ValueError:
        response_data = response.text

    return {
        "status_code": response.status_code,
        "data": response_data,
    }