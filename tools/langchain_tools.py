from langchain_core.tools import tool
from tools.db_tool import get_avg_temp_from_db
from tools.api_tool import get_current_temp_from_api


@tool
def db_avg_temp_tool(city: str, month: str) -> dict:
    """Look up the historical AVERAGE temperature (Celsius) for a city and
    month from the database. Use this when the question needs a historical
    or 'usual' temperature, not today's actual temperature."""
    return get_avg_temp_from_db(city, month)


@tool
def api_current_temp_tool(city: str) -> dict:
    """Fetch TODAY'S ACTUAL current temperature (Celsius) for a city from a
    live external weather API. Use this when the question needs the real,
    current temperature right now, not a historical average."""
    return get_current_temp_from_api(city)


ALL_TOOLS = [db_avg_temp_tool, api_current_temp_tool]
