import requests
from pyquery import PyQuery as pq
from typing import Dict, List

API_URL = "https://opera4u.operaunitn.cloud/ajax_tools/get_week"
# The server checks for these headers, so we need to include them or the request will not work
HEADERS = {"X-Requested-With": "XMLHttpRequest", "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}


def get_week_menu(unixtime: int) -> Dict[str, Dict[str, List[str]]]:
    """
    Get the menu for the week.
    The week returned is the week that contains the unixtime.

    Args:
    unixtime: int, the unix timestamp of the day for which we want the menu.

    Returns:
    Dict[int, Dict[int, List[str]]]: A dictionary where the first key is  keys are the days of the week and the values are dictionaries with the keys being 0 for lunch and 1 for dinner and the values being the food.
    """

    global API_URL, HEADERS

    data = {"timestamp_selezionato": str(unixtime), "tipo_menu_id": "1"}
    response = requests.post(API_URL, headers=HEADERS, data=data)
    html = response.json().get("visualizzazione_settimanale")
    doc = pq(html)
    menu: Dict[int, Dict[int, List[str]]] = {
        1: {0: {1: [], 2: [], 3: [], 4: []}, 1: []},
        2: {0: {1: [], 2: [], 3: [], 4: []}, 1: []},
        3: {0: {1: [], 2: [], 3: [], 4: []}, 1: []},
        4: {0: {1: [], 2: [], 3: [], 4: []}, 1: []},
        5: {0: {1: [], 2: [], 3: [], 4: []}, 1: []},
        6: {0: {1: [], 2: [], 3: [], 4: []}, 1: []},
        7: {0: {1: [], 2: [], 3: [], 4: []}, 1: []},
    }

    # Get the table for lunch
    for tr in doc("table").filter(lambda i, el: pq(el).find("th h5").text() == "Pranzo").find("tr"):
        tr = pq(tr)
        for food_td in tr.find("td[data-giorno][data-tipo-piatto]"):
            food_td = pq(food_td)

            # If the food table description element is empty, skip it
            if food_td.text().strip() == "":
                continue

            day_of_week = int(food_td.attr("data-giorno"))
            type_of_food = int(food_td.attr("data-tipo-piatto"))

            for food_name in food_td.find("p").map(lambda i, el: pq(el).text()):
                menu[day_of_week][0][type_of_food].append(food_name)

    # Get the table for dinner
    for tr in doc("table").filter(lambda i, el: pq(el).find("th h5").text() == "Dinner").find("tr"):
        tr = pq(tr)
        for food_td in tr.find("td[data-giorno][data-tipo-piatto]"):
            food_td = pq(food_td)

            # If the food table description element is empty, skip it
            if food_td.text().strip() == "":
                continue

            day_of_week = int(food_td.attr("data-giorno"))
            type_of_food = int(food_td.attr("data-tipo-piatto"))

            for food_name in food_td.find("p").map(lambda i, el: pq(el).text()):
                menu[day_of_week][0][type_of_food].append(food_name)

    # TODO: Add fixed menu to each day

    return menu


if __name__ == "__main__":
    menu = get_week_menu(1735231661)
    print(menu)
