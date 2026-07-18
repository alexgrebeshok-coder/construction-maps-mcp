"""Centralized error handling for MCP tools."""

from typing import Optional
import structlog

logger = structlog.get_logger()


# Custom exceptions
class ConstructionMapsError(Exception):
    """Base exception for all construction maps errors."""

    pass


class CadastreNotFoundError(ConstructionMapsError):
    """Cadastral number not found in Rosreestr."""

    pass


class GeocodeError(ConstructionMapsError):
    """Error during geocoding operation."""

    pass


class YandexAPIError(ConstructionMapsError):
    """Error from Yandex Maps API."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class RosreestrAPIError(ConstructionMapsError):
    """Error from Rosreestr/NSPD API."""

    pass


class CacheError(ConstructionMapsError):
    """Error during cache operations."""

    pass


async def handle_tool_error(tool_name: str, error: Exception) -> dict:
    """
    Centralized error handler for MCP tools.

    Args:
        tool_name: Name of the tool that encountered error
        error: The exception that was raised

    Returns:
        Structured error response dict
    """
    logger.error(
        "Tool execution failed",
        tool=tool_name,
        error_type=type(error).__name__,
        error_message=str(error),
    )

    # Cadastre not found - user error, no retry
    if isinstance(error, CadastreNotFoundError):
        return {
            "error": "cadastre_not_found",
            "message": str(error),
            "retry": False,
            "user_message": (
                "Кадастровый номер не найден. Проверьте правильность формата "
                "(XX:XX:XXXXXXX:XXXX) и существование участка в НСПД."
            ),
        }

    # Yandex API error - check if retryable
    elif isinstance(error, YandexAPIError):
        retry = error.status_code in [429, 500, 502, 503, 504] if error.status_code else True
        return {
            "error": "yandex_api_error",
            "message": str(error),
            "status_code": error.status_code,
            "retry": retry,
            "user_message": (
                "Ошибка Yandex Maps API. "
                + (
                    "Превышен лимит запросов, попробуйте позже."
                    if error.status_code == 429
                    else "Временная ошибка сервиса."
                )
            ),
        }

    # Rosreestr API error - usually retryable
    elif isinstance(error, RosreestrAPIError):
        return {
            "error": "rosreestr_api_error",
            "message": str(error),
            "retry": True,
            "user_message": (
                "Ошибка доступа к данным Росреестра. "
                "Возможно, сервис временно недоступен. Попробуйте позже."
            ),
        }

    # Geocoding error
    elif isinstance(error, GeocodeError):
        return {
            "error": "geocode_error",
            "message": str(error),
            "retry": False,
            "user_message": "Не удалось определить координаты для указанного адреса.",
        }

    # Cache error - usually not critical
    elif isinstance(error, CacheError):
        return {
            "error": "cache_error",
            "message": str(error),
            "retry": False,
            "user_message": "Ошибка кеширования (данные получены без кеша).",
        }

    # Unknown error
    else:
        return {
            "error": "unknown_error",
            "message": str(error),
            "retry": False,
            "user_message": f"Неизвестная ошибка: {str(error)}",
        }


def format_error_markdown(error_dict: dict) -> str:
    """
    Format error dict as Markdown for MCP response.

    Args:
        error_dict: Error dictionary from handle_tool_error

    Returns:
        Markdown-formatted error message
    """
    retry_text = "✅ Повторная попытка возможна" if error_dict.get("retry") else "❌ Повтор не поможет"

    return f"""## ❌ Ошибка: {error_dict.get('error', 'unknown')}

{error_dict.get('user_message', error_dict.get('message', 'Unknown error'))}

**Статус**: {retry_text}

_Техническая информация: {error_dict.get('message', 'N/A')}_
"""
