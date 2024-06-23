import grequests
import requests
import json
import time
from time import sleep
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36",
}
RETRY = 5
RETRY_WAIT = 10


def fetch_url(url):
    for _ in range(RETRY):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response
        except Exception as e:
            print(f"Failed to fetch URL: {url} :: {e}")
            print("Retrying...")
            time.sleep(RETRY_WAIT)
    raise Exception(f"Failed to fetch URL :: {url}")


def get_submission_info(username):
    cur = 0

    while True:
        curr_url = f"https://kenkoooo.com/atcoder/atcoder-api/v3/user/submissions?user={username}&from_second={cur}"
        response = fetch_url(curr_url)
        submissions = json.loads(response.text)
        if not submissions:
            break

        for submission in submissions:
            if submission.get("result", "") == "AC":
                try:
                    yield {
                        "language": submission["language"],
                        "problem_code": submission["problem_id"],
                        "solution_id": submission["id"],
                        "problem_link": f'https://atcoder.jp/contests/{submission["contest_id"]}/tasks/{submission["problem_id"]}',
                        "link": f'https://atcoder.jp/contests/{submission["contest_id"]}/submissions/{submission["id"]}',
                    }
                except KeyError:
                    print("Could not find submission. Trying again...")
            cur = submission.get("epoch_second", "") + 1
        sleep(1)


def fetch_code(html):
    soup = BeautifulSoup(html, "lxml")
    return soup.select_one("#submission-code").text


def get_solutions(username, all_info=None):
    if not all_info:
        all_info = list(get_submission_info(username))[::-1]

    responses = grequests.imap(
        grequests.get(info["link"], HEADERS=HEADERS) for info in all_info
    )
    for response, info in zip(responses, all_info):
        code = fetch_code(response.text)
        yield {
            "language": info["language"],
            "problem_code": info["problem_code"],
            "solution_id": info["solution_id"],
            "problem_link": info["problem_link"],
            "link": info["link"],
            "solution": code,
        }
