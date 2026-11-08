from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    data = response.data
    message = "请求失败，请稍后重试"
    if isinstance(data, dict):
        detail = data.get("detail")
        if detail:
            message = str(detail)
        else:
            for value in data.values():
                if isinstance(value, list) and value:
                    message = str(value[0])
                    break
                if isinstance(value, str):
                    message = value
                    break
    elif isinstance(data, list) and data:
        message = str(data[0])
    response.data = {"detail": message, "code": getattr(exc, "default_code", "API_ERROR")}
    return response
