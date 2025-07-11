import requests
import json
from datetime import datetime, timezone, timedelta

# --- Configuration ---
OUTAGE_KEYWORDS = [
    "outage", "incident", "degraded", "disruption", "failure", "issue", "problem",
    "latency", "unavailable", "down", "investigating", "monitoring", "rerouted",
    "delayed", "intermittent"
]
RECENT_MINUTES = 15
CLOUDFLARE_STATUS_API_URL = "https://www.cloudflarestatus.com/api/v2/summary.json"
USER_AGENT = "PythonCloudflareStatusChecker/1.0"

# --- Helper Functions ---

def is_recent(date_string: str, minutes: int) -> bool:
    """
    Checks if a given ISO date string (UTC) is within the last N minutes.
    """
    if not date_string:
        return False
    try:
        # Parse the ISO 8601 date string.
        # Handle 'Z' for UTC and potential milliseconds.
        if date_string.endswith('Z'):
            date_string = date_string[:-1] + "+00:00"

        # Python's fromisoformat doesn't always handle milliseconds from all APIs perfectly,
        # so we might need to truncate them if they exist and cause issues.
        if '.' in date_string and '+' in date_string.split('.')[1]:
             parts = date_string.split('.')
             seconds_and_tz = parts[1].split('+')
             if len(seconds_and_tz[0]) > 6: # more than microsecond precision
                 seconds_and_tz[0] = seconds_and_tz[0][:6]
             date_string = parts[0] + '.' + seconds_and_tz[0] + '+' + seconds_and_tz[1]
        elif '.' in date_string and '-' in date_string.split('.')[1]: # For timezones like -07:00
             parts = date_string.split('.')
             seconds_and_tz = parts[1].split('-')
             if len(seconds_and_tz[0]) > 6:
                 seconds_and_tz[0] = seconds_and_tz[0][:6]
             date_string = parts[0] + '.' + seconds_and_tz[0] + '-' + seconds_and_tz[1]


        incident_time = datetime.fromisoformat(date_string)

        # Ensure it's offset-aware and convert to UTC if not already
        if incident_time.tzinfo is None:
            incident_time = incident_time.replace(tzinfo=timezone.utc)
        else:
            incident_time = incident_time.astimezone(timezone.utc)

        now_utc = datetime.now(timezone.utc)
        diff = now_utc - incident_time
        return timedelta(minutes=0) <= diff <= timedelta(minutes=minutes)
    except ValueError as e:
        print(f"Error parsing date string '{date_string}': {e}")
        return False

def fetch_status() -> dict | None:
    """
    Fetches the status from the Cloudflare API.
    """
    try:
        response = requests.get(CLOUDFLARE_STATUS_API_URL, headers={'User-Agent': USER_AGENT}, timeout=10)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Cloudflare status: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        return None

def contains_keyword(text: str | None, keywords: list[str]) -> bool:
    """
    Checks for outage keywords in a given text. Case-insensitive.
    """
    if not text:
        return False
    lower_text = text.lower()
    return any(keyword.lower() in lower_text for keyword in keywords)

# --- Main Logic ---

def check_for_outages(data: dict, keywords: list[str], recent_minutes: int) -> list[dict]:
    """
    Analyzes the Cloudflare status data for potential outages.
    """
    potential_outages = []
    now_utc = datetime.now(timezone.utc)

    # Process Incidents
    for incident in data.get("incidents", []):
        is_relevant_incident = False
        found_keyword_in_incident = False

        created_at_recent = is_recent(incident.get("created_at"), recent_minutes)
        updated_at_recent = is_recent(incident.get("updated_at"), recent_minutes)
        resolved_at = incident.get("resolved_at")
        is_ongoing_or_recently_resolved = resolved_at is None or is_recent(resolved_at, recent_minutes)

        if created_at_recent or updated_at_recent or is_ongoing_or_recently_resolved:
            is_relevant_incident = True

        if contains_keyword(incident.get("name"), keywords):
            found_keyword_in_incident = True

        recent_matching_updates_details = []
        for update in incident.get("incident_updates", []):
            if is_recent(update.get("created_at"), recent_minutes) or \
               is_recent(update.get("updated_at"), recent_minutes):
                if contains_keyword(update.get("body"), keywords):
                    found_keyword_in_incident = True # Keyword found in an update also flags the incident
                    recent_matching_updates_details.append({
                        "body": update.get("body"),
                        "updated_at": update.get("updated_at"),
                        "status": update.get("status")
                    })

        if is_relevant_incident and found_keyword_in_incident:
            potential_outages.append({
                "type": "incident",
                "id": incident.get("id"),
                "name": incident.get("name"),
                "status": incident.get("status"),
                "impact": incident.get("impact"),
                "created_at": incident.get("created_at"),
                "updated_at": incident.get("updated_at"),
                "resolved_at": resolved_at,
                "shortlink": incident.get("shortlink"),
                "components_affected": [comp.get("name") for comp in incident.get("components", [])],
                "recent_matching_updates": recent_matching_updates_details
            })

    # Process Components
    for component in data.get("components", []):
        comp_status = component.get("status", "operational").lower()
        comp_updated_at = component.get("updated_at")

        if comp_status != 'operational' and is_recent(comp_updated_at, recent_minutes):
            if contains_keyword(component.get("name"), keywords) or \
               contains_keyword(comp_status, keywords): # Check status string itself
                potential_outages.append({
                    "type": "component_status",
                    "id": component.get("id"),
                    "name": component.get("name"),
                    "status": component.get("status"),
                    "updated_at": comp_updated_at,
                    "description": component.get("description")
                })

    # Process Scheduled Maintenances
    for maint in data.get("scheduled_maintenances", []):
        is_relevant_maintenance = False
        found_keyword_in_maintenance = False

        scheduled_for_str = maint.get("scheduled_for")
        scheduled_until_str = maint.get("scheduled_until")

        try:
            # Ensure dates are offset-aware for comparison
            scheduled_for = datetime.fromisoformat(scheduled_for_str.replace('Z', '+00:00')) if scheduled_for_str else None
            scheduled_until = datetime.fromisoformat(scheduled_until_str.replace('Z', '+00:00')) if scheduled_until_str else None

            if scheduled_for and scheduled_until:
                if scheduled_for <= now_utc < scheduled_until: # Currently active
                    is_relevant_maintenance = True
        except ValueError:
            pass # Date parsing error already handled by is_recent or here

        if is_recent(maint.get("updated_at"), recent_minutes):
             is_relevant_maintenance = True # Also relevant if recently updated

        if contains_keyword(maint.get("name"), keywords):
            found_keyword_in_maintenance = True

        recent_maintenance_updates_details = []
        for update in maint.get("incident_updates", []):
            if is_recent(update.get("created_at"), recent_minutes) or \
               is_recent(update.get("updated_at"), recent_minutes):
                if contains_keyword(update.get("body"), keywords):
                    found_keyword_in_maintenance = True
                    recent_maintenance_updates_details.append({
                        "body": update.get("body"),
                        "updated_at": update.get("updated_at"),
                        "status": update.get("status")
                    })

        if is_relevant_maintenance and found_keyword_in_maintenance:
            potential_outages.append({
                "type": "scheduled_maintenance_alert",
                "id": maint.get("id"),
                "name": maint.get("name"),
                "status": maint.get("status"),
                "impact": maint.get("impact"),
                "scheduled_for": scheduled_for_str,
                "scheduled_until": scheduled_until_str,
                "shortlink": maint.get("shortlink"),
                "components_affected": [comp.get("name") for comp in maint.get("components", [])],
                "recent_matching_updates": recent_maintenance_updates_details
            })

    return potential_outages

# --- Main Execution ---

if __name__ == "__main__":
    print(f"[{datetime.now(timezone.utc).isoformat()}] Fetching Cloudflare status...")
    status_data = fetch_status()

    if status_data:
        print(f"[{datetime.now(timezone.utc).isoformat()}] Analyzing data for recent issues (last {RECENT_MINUTES} minutes)...")
        outages_found = check_for_outages(status_data, OUTAGE_KEYWORDS, RECENT_MINUTES)

        result = {
            "checked_at_utc": datetime.now(timezone.utc).isoformat(),
            "recent_minutes_checked": RECENT_MINUTES,
        }

        if outages_found:
            print(f"[{datetime.now(timezone.utc).isoformat()}] Potential issues FOUND.")
            result["message"] = f"Potential outages or service disruptions detected within the last {RECENT_MINUTES} minutes."
            result["details"] = outages_found
        else:
            print(f"[{datetime.now(timezone.utc).isoformat()}] No recent issues detected.")
            result["message"] = f"No recent outages or relevant service disruptions detected within the last {RECENT_MINUTES} minutes."
            result["details"] = []

        # Print the full result as JSON
        print("\n--- JSON Output ---")
        print(json.dumps(result, indent=2))
        print("--- End JSON Output ---")

    else:
        print(f"[{datetime.now(timezone.utc).isoformat()}] Could not retrieve Cloudflare status data.")
        # Output JSON even on failure for consistent parsing by other tools
        print("\n--- JSON Output ---")
        print(json.dumps({
            "checked_at_utc": datetime.now(timezone.utc).isoformat(),
            "error": "Failed to fetch or parse Cloudflare status API data."
        }, indent=2))
        print("--- End JSON Output ---")
