import requests
from bs4 import BeautifulSoup


## Constants.


URL_ROOT = "https://www.baseball-reference.com"
BOLD_START = "\033[1m"
BOLD_END = "\033[0m"


## Main.


def main():
    first_name = "Shohei"
    last_name = "Ohtani"
    year = 2022

    stats_1st_inning = get_1st_inning_stats_for_pitcher(first_name, last_name, year)

    if stats_1st_inning is None:
        return

    era_1st_inning = float(stats_1st_inning["earned_run_avg"])

    print(
        f"\n1st inning ERA for {BOLD_START}{first_name} {last_name}{BOLD_END} ({year}):"
        f" {BOLD_START}{era_1st_inning}{BOLD_END}\n"
    )


## Helpers.


def get_1st_inning_stats_for_pitcher(first_name, last_name, year):
    player_page_id = f"{last_name.lower()[:5]}{first_name.lower()[:2]}01"
    player_page_url = (
        f"{URL_ROOT}/players/split.fcgi?id={player_page_id}&year={year}&t=p"
    )
    fetch_res = requests.get(player_page_url)
    if fetch_res.status_code != 200:
        print(
            f"Unable to find stats page for {first_name} {last_name}."
            f" (Looked for it at this URL: {player_page_url}.)"
        )
        return

    raw_html = requests.get(player_page_url).content.decode().replace("<!--", "")

    parsed_html = BeautifulSoup(raw_html, "html.parser")

    by_inning_table = parsed_html.find("table", id="innng")

    for tr in by_inning_table.find_all("tr"):
        th = tr.find("th")
        if th is not None and th.get_text() == "1st inning":
            stats_1st_inning_dict = {
                td.get("data-stat"): td.get_text() for td in tr.find_all("td")
            }
            return stats_1st_inning_dict


if __name__ == "__main__":
    main()
