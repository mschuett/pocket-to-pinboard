#!/usr/bin/python3
import requests
import os
import time
from datetime import datetime, timezone

POCKET_CONSUMER_KEY = os.environ["POCKET_CONSUMER_KEY"]
POCKET_ACCESS_TOKEN = os.environ["POCKET_ACCESS_TOKEN"]
PINBOARD_USERNAME = os.environ["PINBOARD_USERNAME"]
PINBOARD_API_TOKEN = os.environ["PINBOARD_API_TOKEN"]


def timestamp_to_isodate(timestamp):
    return (
        datetime.fromtimestamp(int(timestamp), timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


class PocketPinboard:
    def get_pocket_items(self, time=1):
        """Gets items from pocket, returns a list of """
        r = requests.get(
            "https://getpocket.com/v3/get",
            params={
                "consumer_key": POCKET_CONSUMER_KEY,
                "access_token": POCKET_ACCESS_TOKEN,
                "since": time,
                "sort": "oldest",
                "detailType": "complete",
                "state": "unread",
            },
        )
        url_tag_list = []
        pocket_items = r.json()
        if len(pocket_items["list"]) > 0:
            for key, value in pocket_items["list"].items():
                if all(
                    k in value.keys()
                    for k in ("resolved_url", "resolved_title", "excerpt")
                ):
                    item = {
                        "url": value["resolved_url"],
                        "title": value["resolved_title"],
                        "excerpt": value["excerpt"],
                        "timestamp": value["time_added"],
                        "tags": [],
                    }
                    if "tags" in value.keys():
                        item["tags"] = [tag for tag in value["tags"]]
                    url_tag_list.append(item)
        return url_tag_list

    def post_items_to_pinboard(self):
        starttime = self.get_last_update()
        items = self.get_pocket_items(time=starttime)
        for item in items:
            tags = [t.replace(" ", "_") for t in item["tags"]]
            url = "https://api.pinboard.in/v1/posts/add?auth_token="
            r = requests.get(
                "{}{}".format(url, PINBOARD_API_TOKEN),
                params={
                    "url": item["url"],
                    "description": item["title"],
                    "extended": item["excerpt"],
                    "tags": ", ".join(tags),
                    "dt": timestamp_to_isodate(item["timestamp"]),
                },
            )
            r.raise_for_status()
            print(
                "added to pinboard: %s - %s - %s"
                % (timestamp_to_isodate(item["timestamp"]), item["url"], item["title"])
            )
            # Pinboard API requests are limited to one call per user every three seconds
            time.sleep(3)
        self.update_timestamp()

    def update_timestamp(self):
        current_time = int(
            (datetime.now() - datetime.utcfromtimestamp(0)).total_seconds()
        )
        with open("timestamp.txt", "w") as stamp_file:
            stamp_file.write("{}".format(current_time))

    def get_last_update(self):
        with open("timestamp.txt") as stamp_file:
            content = stamp_file.readlines()
        return int(content[0])

    def run(self):
        self.post_items_to_pinboard()


if __name__ == "__main__":
    p = PocketPinboard()
    p.run()
