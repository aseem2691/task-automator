import json
import ssl
import urllib.request

import certifi
from langchain_core.tools import tool

_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

# ESPN publishes a public, undocumented scoreboard JSON API that requires no
# signup and returns live/recent/upcoming events. Endpoint pattern:
#   https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard
# For each supported sport we probe up to two of the most-watched leagues so a
# single call still returns something useful across seasons.
_API_BASE = "https://site.api.espn.com/apis/site/v2/sports"

_SPORT_LEAGUES: dict[str, list[tuple[str, str]]] = {
    "cricket": [("IPL", "cricket/8048"), ("Internationals", "cricket/8039")],
    "soccer": [("EPL", "soccer/eng.1"), ("Champions League", "soccer/uefa.champions")],
    "football": [("EPL", "soccer/eng.1"), ("Champions League", "soccer/uefa.champions")],
    "american_football": [("NFL", "football/nfl")],
    "nfl": [("NFL", "football/nfl")],
    "basketball": [("NBA", "basketball/nba")],
    "nba": [("NBA", "basketball/nba")],
    "baseball": [("MLB", "baseball/mlb")],
    "mlb": [("MLB", "baseball/mlb")],
    "hockey": [("NHL", "hockey/nhl")],
    "ice_hockey": [("NHL", "hockey/nhl")],
    "nhl": [("NHL", "hockey/nhl")],
}


def _http_get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "task-automator/1.0"})
    with urllib.request.urlopen(req, timeout=10, context=_SSL_CONTEXT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _format_event(ev: dict, league_label: str) -> str:
    name = ev.get("name") or ev.get("shortName") or "(unknown match)"
    status_type = (ev.get("status") or {}).get("type") or {}
    desc = status_type.get("description") or ""
    detail = status_type.get("detail") or ""
    status_str = " / ".join(x for x in (desc, detail) if x)

    competition = (ev.get("competitions") or [{}])[0]
    competitors = competition.get("competitors") or []
    score_lines = []
    for c in competitors:
        team = (c.get("team") or {}).get("displayName") or "?"
        score = c.get("score") or ""
        if score:
            score_lines.append(f"      {team}: {score}")
        else:
            score_lines.append(f"      {team}")

    header = f"  - [{league_label}] {name}"
    if status_str:
        header += f" ({status_str})"
    return "\n".join([header, *score_lines])


@tool
def get_live_scores(sport: str = "cricket") -> str:
    """Get live sports scores via ESPN's public scoreboard API (no API key required).

    Returns currently-live matches plus today's finished and upcoming fixtures
    across the most-watched leagues for the requested sport. Each sport probes
    one or two leagues: cricket → IPL + internationals, soccer/football → EPL +
    UEFA Champions League, basketball → NBA, baseball → MLB, NFL → NFL, NHL →
    NHL.

    Events include status labels like "In Progress", "Full Time", or
    "Scheduled" so the LLM can tell live from finished from upcoming.

    Args:
        sport: Sport name. Accepts: cricket, soccer/football, basketball/nba,
            american_football/nfl, baseball/mlb, ice_hockey/nhl.
    """
    key = sport.strip().lower().replace(" ", "_")
    leagues = _SPORT_LEAGUES.get(key)
    if leagues is None:
        options = ", ".join(sorted(set(_SPORT_LEAGUES.keys())))
        return f"Error: unknown sport '{sport}'. Try: {options}."

    all_blocks: list[str] = []
    errors: list[str] = []

    for label, path in leagues:
        url = f"{_API_BASE}/{path}/scoreboard"
        try:
            data = _http_get_json(url)
        except Exception as e:
            errors.append(f"{label}: {e}")
            continue

        events = data.get("events") or []
        for ev in events[:10]:
            all_blocks.append(_format_event(ev, label))

    if all_blocks:
        header = f"{sport.capitalize()} scoreboard:"
        return "\n".join([header, *all_blocks])

    if errors:
        return f"Error fetching {sport} scores: " + "; ".join(errors)

    league_names = ", ".join(lbl for lbl, _ in leagues)
    return f"No {sport} events found across {league_names} right now."
