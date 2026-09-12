import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()


def _get_connection():
    return psycopg2.connect(
        host=os.getenv("PG_HOST"),
        port=os.getenv("PG_PORT"),
        dbname=os.getenv("PG_DB"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
    )


def get_avg_temp_from_db(city: str, month: str) -> dict:
    """
    Query the DB for the historical average temperature of a city for a given month.

    Returns a structured dict rather than raising on 'no data' — the agent
    needs to be able to REASON about a missing row (e.g. try a different
    month, or report 'no data'), not just crash.
    """
    query = sql.SQL(
        "SELECT avg_temp_celsius FROM weather_readings WHERE city = %s AND month = %s"
    )
    try:
        conn = _get_connection()
        with conn, conn.cursor() as cur:
            cur.execute(query, (city, month))
            row = cur.fetchone()
        conn.close()

        if row is None:
            return {"success": False, "error": f"No DB record for {city} in {month}"}

        return {"success": True, "city": city, "month": month, "avg_temp_celsius": float(row[0])}

    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # quick manual test — run this file directly before wiring into the agent
    print(get_avg_temp_from_db("Ahmedabad", "September"))
