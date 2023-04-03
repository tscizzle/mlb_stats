import time

import requests
from bs4 import BeautifulSoup


## Constants.


LAST_YEAR = 2022
URL_ROOT = "https://www.baseball-reference.com"
BOLD_START = "\033[1m"
BOLD_END = "\033[0m"


## Main.


def main():
    matchups = get_todays_matchups()
    print(f"\n\t{len(matchups)} matchups\n")

    team_batting_1st_inning_era = get_1st_inning_era_for_batting_teams(LAST_YEAR)

    for matchup_idx, matchup in enumerate(matchups):
        team_abbrev = matchup["team_abbrev"]
        pitcher_player_id = matchup["pitcher_player_id"]
        pitcher_name = matchup["pitcher_name"]

        team_batting_era = team_batting_1st_inning_era[team_abbrev]
        pitcher_era = get_1st_inning_era_for_pitcher(pitcher_player_id, LAST_YEAR)

        print(
            f"\t{matchup_idx + 1}."
            f" {team_abbrev} batting"
            f" ({BOLD_START}{round(team_batting_era, 2)}{BOLD_END} ERA)"
            f" vs."
            f" {pitcher_name} pitching"
            f" ({BOLD_START}{pitcher_era}{BOLD_END} ERA)"
        )
    print()


## Helpers.


last_get = -1


def rate_limited_get(*args, **kwargs):
    """
    This function is for abiding by the website's rules and avoiding getting blocked
        (https://www.sports-reference.com/bot-traffic.html).
    """
    global last_get
    while time.time() - last_get < 3.1:
        time.sleep(0.1)

    results = requests.get(*args, **kwargs)

    last_get = time.time()

    return results


def get_todays_matchups():
    game_previews_url = f"{URL_ROOT}/previews"
    fetch_res = rate_limited_get(game_previews_url)
    if fetch_res.status_code != 200:
        print(f"Unable to get today's matchups at {game_previews_url}")
        return

    raw_html = fetch_res.content.decode().replace("<!--", "")
    parsed_html = BeautifulSoup(raw_html, "html.parser")

    todays_matchups = []
    all_game_summaries_div = parsed_html.find("div", class_="game_summaries")
    for game_summary_div in all_game_summaries_div.find_all(
        "div", class_="game_summary"
    ):
        pitcher_matchup_table = game_summary_div.find_all("table")[1]
        trs = pitcher_matchup_table.find_all("tr")
        away_team_tds = trs[0].find_all("td")
        away_team_abbrev = away_team_tds[0].find("strong").get_text()
        away_team_pitcher_name = away_team_tds[1].find("a").get_text()
        away_team_pitcher_player_id = (
            away_team_tds[1].find("a").get("href").split("/")[-1].split(".")[0]
        )
        home_team_tds = trs[1].find_all("td")
        home_team_abbrev = home_team_tds[0].find("strong").get_text()
        home_team_pitcher_name = home_team_tds[1].find("a").get_text()
        home_team_pitcher_player_id = (
            home_team_tds[1].find("a").get("href").split("/")[-1].split(".")[0]
        )
        todays_matchups.append(
            {
                "team_abbrev": away_team_abbrev,
                "pitcher_player_id": home_team_pitcher_player_id,
                "pitcher_name": home_team_pitcher_name,
            }
        )
        todays_matchups.append(
            {
                "team_abbrev": home_team_abbrev,
                "pitcher_player_id": away_team_pitcher_player_id,
                "pitcher_name": away_team_pitcher_name,
            }
        )
    return todays_matchups


def get_1st_inning_era_for_batting_teams(year):
    all_teams_url = (
        f"{URL_ROOT}/tools/split_stats_lg.cgi"
        f"?full=1&params=innng|1st inning|ML|{year}|bat|AB|"
    )
    fetch_res = rate_limited_get(all_teams_url)
    if fetch_res.status_code != 200:
        print(f"Unable to find 1st inning batting stats page at {all_teams_url}")
        return

    raw_html = fetch_res.content.decode().replace("<!--", "")
    parsed_html = BeautifulSoup(raw_html, "html.parser")

    team_1st_inning_runs = {}
    table = parsed_html.find("table", id="split1")
    tbody = table.find("tbody")
    for tr in tbody.find_all("tr"):
        team_abbrev = tr.find_all("td", {"data-stat": "team"})[0].get_text()
        runs = int(tr.find_all("td", {"data-stat": "R"})[0].get_text())
        games = int(tr.find_all("td", {"data-stat": "G"})[0].get_text())
        team_1st_inning_runs[team_abbrev] = runs / games
    return team_1st_inning_runs


def get_1st_inning_era_for_pitcher(player_id, year):
    player_page_url = f"{URL_ROOT}/players/split.fcgi?id={player_id}&year={year}&t=p"
    fetch_res = rate_limited_get(player_page_url)
    if fetch_res.status_code != 200:
        print(f"Unable to find stats page for {player_id} at {player_page_url}")
        return

    raw_html = fetch_res.content.decode().replace("<!--", "")
    parsed_html = BeautifulSoup(raw_html, "html.parser")

    by_inning_table = parsed_html.find("table", id="innng")
    for tr in by_inning_table.find_all("tr"):
        th = tr.find("th")
        if th is not None and th.get_text() == "1st inning":
            for td in tr.find_all(
                "td",
            ):
                if td.get("data-stat") == "earned_run_avg":
                    era = float(td.get_text())
                    return era


if __name__ == "__main__":
    main()
