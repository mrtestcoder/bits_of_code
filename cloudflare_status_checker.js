const OUTAGE_KEYWORDS = [
  "outage", "incident", "degraded", "disruption", "failure", "issue", "problem",
  "latency", "unavailable", "down", "investigating", "monitoring", "rerouted",
  "delayed", "intermittent"
];
const RECENT_MINUTES = 15; // Check for updates within the last 15 minutes

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

/**
 * Checks if a given ISO date string is within the last N minutes.
 * @param {string} dateString - The ISO date string to check.
 * @param {number} minutes - The number of minutes to consider as "recent".
 * @returns {boolean} - True if the date is recent, false otherwise.
 */
function isRecent(dateString, minutes) {
  if (!dateString) return false;
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = diffMs / (1000 * 60);
    return diffMins <= minutes && diffMins >= 0; // ensure it's not in the future
  } catch (e) {
    console.error("Error parsing date:", dateString, e);
    return false;
  }
}

/**
 * Fetches the status from the Cloudflare API.
 * @returns {Promise<Object|null>} - The parsed JSON data or null if an error occurs.
 */
async function fetchStatus() {
  try {
    const response = await fetch('https://www.cloudflarestatus.com/api/v2/summary.json', {
      headers: { 'User-Agent': 'CloudflareStatusCheckerWorker/1.0' } // Good practice to set a User-Agent
    });
    if (!response.ok) {
      console.error(`API request failed with status: ${response.status}`);
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching Cloudflare status:', error);
    return null;
  }
}

/**
 * Checks for outage keywords in a given text.
 * @param {string} text - The text to search within.
 * @param {string[]} keywords - An array of keywords to look for.
 * @returns {boolean} - True if any keyword is found (case-insensitive), false otherwise.
 */
function containsKeyword(text, keywords) {
  if (!text) return false;
  const lowerText = text.toLowerCase();
  return keywords.some(keyword => lowerText.includes(keyword.toLowerCase()));
}

/**
 * Analyzes the Cloudflare status data for potential outages.
 * @param {Object} data - The parsed JSON data from the Cloudflare status API.
 * @param {string[]} keywords - Keywords to search for.
 * @param {number} recentMinutes - Time window for recent events.
 * @returns {Array<Object>} - An array of potential outage objects.
 */
function checkForOutages(data, keywords, recentMinutes) {
  const potentialOutages = [];
  const now = new Date();

  // Process Incidents
  if (data.incidents && Array.isArray(data.incidents)) {
    data.incidents.forEach(incident => {
      let isRelevantIncident = false;
      let foundKeywordInIncident = false;

      // Check if incident itself is recent or ongoing
      if (isRecent(incident.created_at, recentMinutes) ||
          isRecent(incident.updated_at, recentMinutes) ||
          (incident.resolved_at === null || isRecent(incident.resolved_at, recentMinutes))) {
        isRelevantIncident = true;
      }

      if (containsKeyword(incident.name, keywords)) {
        foundKeywordInIncident = true;
      }

      const recentUpdates = [];
      if (incident.incident_updates && Array.isArray(incident.incident_updates)) {
        incident.incident_updates.forEach(update => {
          if (isRecent(update.created_at, recentMinutes) || isRecent(update.updated_at, recentMinutes)) {
            if (containsKeyword(update.body, keywords)) {
              foundKeywordInIncident = true;
            }
            recentUpdates.push({
              body: update.body, // Consider stripping HTML for cleaner output if needed
              updated_at: update.updated_at,
              status: update.status,
            });
          }
        });
      }

      // If the incident is relevant (recent/ongoing) AND keywords were found in name or recent updates
      if (isRelevantIncident && foundKeywordInIncident) {
        potentialOutages.push({
          type: "incident",
          id: incident.id,
          name: incident.name,
          status: incident.status,
          impact: incident.impact,
          created_at: incident.created_at,
          updated_at: incident.updated_at,
          resolved_at: incident.resolved_at,
          shortlink: incident.shortlink,
          components_affected: incident.components.map(c => ({ id: c.id, name: c.name })),
          recent_matching_updates: recentUpdates.filter(u => containsKeyword(u.body, keywords)) // Only updates that matched
        });
      }
    });
  }

  // Process Components
  if (data.components && Array.isArray(data.components)) {
    data.components.forEach(component => {
      if (component.status.toLowerCase() !== 'operational' && isRecent(component.updated_at, recentMinutes)) {
        // Check name or status itself for keywords (e.g. "partial_outage" in status)
        if (containsKeyword(component.name, keywords) || containsKeyword(component.status, keywords)) {
          potentialOutages.push({
            type: "component_status",
            id: component.id,
            name: component.name,
            status: component.status,
            updated_at: component.updated_at,
            description: component.description || "N/A"
          });
        }
      }
    });
  }

  // Process Scheduled Maintenances
  if (data.scheduled_maintenances && Array.isArray(data.scheduled_maintenances)) {
    data.scheduled_maintenances.forEach(maint => {
      let isRelevantMaintenance = false;
      let foundKeywordInMaintenance = false;

      const scheduledFor = new Date(maint.scheduled_for);
      const scheduledUntil = new Date(maint.scheduled_until);

      if ( (scheduledFor <= now && now < scheduledUntil) || // Currently active
           isRecent(maint.updated_at, recentMinutes) ) {
        isRelevantMaintenance = true;
      }

      if (containsKeyword(maint.name, keywords)) {
        foundKeywordInMaintenance = true;
      }

      const recentMaintenanceUpdates = [];
      if (maint.incident_updates && Array.isArray(maint.incident_updates)) {
        maint.incident_updates.forEach(update => {
          if (isRecent(update.created_at, recentMinutes) || isRecent(update.updated_at, recentMinutes)) {
            if (containsKeyword(update.body, keywords)) {
              foundKeywordInMaintenance = true;
            }
            recentMaintenanceUpdates.push({
              body: update.body, // Consider stripping HTML
              updated_at: update.updated_at,
              status: update.status
            });
          }
        });
      }

      if (isRelevantMaintenance && foundKeywordInMaintenance) {
        potentialOutages.push({
          type: "scheduled_maintenance_alert",
          id: maint.id,
          name: maint.name,
          status: maint.status,
          impact: maint.impact,
          scheduled_for: maint.scheduled_for,
          scheduled_until: maint.scheduled_until,
          shortlink: maint.shortlink,
          components_affected: maint.components.map(c => ({ id: c.id, name: c.name })),
          recent_matching_updates: recentMaintenanceUpdates.filter(u => containsKeyword(u.body, keywords))
        });
      }
    });
  }

  return potentialOutages;
}

/**
 * Handles the incoming request.
 * @param {Request} request - The incoming request object.
 * @returns {Promise<Response>} - The response to send back.
 */
async function handleRequest(request) {
  const statusData = await fetchStatus();

  if (!statusData) {
    return new Response(JSON.stringify({ error: 'Failed to fetch Cloudflare status API.' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const potentialOutages = checkForOutages(statusData, OUTAGE_KEYWORDS, RECENT_MINUTES);

  if (potentialOutages.length > 0) {
    return new Response(JSON.stringify({
      message: `Potential outages or service disruptions detected within the last ${RECENT_MINUTES} minutes.`,
      details: potentialOutages,
      checked_at: new Date().toISOString()
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } else {
    return new Response(JSON.stringify({
      message: `No recent outages or relevant service disruptions detected within the last ${RECENT_MINUTES} minutes.`,
      checked_at: new Date().toISOString()
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}
