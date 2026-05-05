import json
import logging

# import random
import re
import time
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import BrowserContext, Page, sync_playwright
from playwright_stealth import Stealth  # type: ignore

from config import ConfigHh


def apply_vacancy(page: Page) -> None:
    response_letter_textarea = page.locator(
        selector='textarea[data-qa^="vacancy-response"]'
    )
    vacancy_id = parse_qs(qs=urlparse(page.url).query).get("vacancyId", [None])[0]
    if response_letter_textarea.count():
        skip_vacancy(
            vacancy_id=vacancy_id
        )

        # response_letter_textarea.click()
        # response_letter_textarea.type(
        #     text=(
        #         "Здравствуйте! Я заинтересован в вашей вакансии и хотел бы"
        #         " откликнуться на неё.\n Тест рыба"
        #     ),
        #     delay=random.randint(30, 100)
        # )
    # page.click(
    #     selector='button[class^="magritte-button"]:has(span:has-text("Откликнуться"))'
    # )
    else:
        config_hh = ConfigHh().model_dump()  # pyright: ignore[reportCallIssue]
        json_log_append({
            "status": "uplied",
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "url": f"{config_hh['vacancy_url']}/{vacancy_id}"
                if vacancy_id else "Unknown url",
        })
    page.close()


def auth_check(browser_context: BrowserContext) -> bool:
    logging.info(
        msg="Checking login state."
    )
    config_hh = ConfigHh().model_dump()  # pyright: ignore[reportCallIssue]
    page = browser_context.pages[0]
    page.goto(
        url=config_hh["main_url"],
        wait_until="networkidle"
    )
    role = next(
        (
            cookie.get("value")
            for cookie in page.context.cookies()
            if cookie.get("name") == "hhrole"
        ),
        None
    )
    if role and role != "anonymous" and not page.locator(
        selector='a[role="button"]:has(span:has-text("Войти"))'
    ).is_visible():
        logging.info(
            msg="Login state is stable. Authenticated successfully."
        )
        return True
    else:
        logging.warning(
            msg=(
                "Login session has expired or invalid."
                " Attempting to initialize login by user."
            )
        )
        return False


def json_log_append(data: dict[str, str]) -> None:
    with open(
        file="vacancies_replyed.jsonl",
        mode="a",
        encoding="utf-8"
    ) as vacancies_replyed_jsonl:
        vacancies_replyed_jsonl.write(
            json.dumps(data, ensure_ascii=False) + "\n"
        )


# def human_behavior_simulation(page: Page):
#     page.mouse.move(
#         random.randint(100, 500),
#         random.randint(100, 500)
#     )
#     time.sleep(10000)


def logging_by_user(browser_context: BrowserContext) -> None:
    input("Please, login by yourself and press Enter...")
    logging.info(
        msg="Login by user completed."
    )


def main() -> None:
    logging.basicConfig(
        filename="app.log",
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    logging.info("RobJob started.")
    with Stealth().use_sync(sync_playwright()) as stealth_sync_playwright:
        browser = stealth_sync_playwright.chromium
        browser_context: BrowserContext = browser.launch_persistent_context(
            user_data_dir="./user_data",
            args=[
                "--disable-blink-features=AutomationControlled"
            ],
            headless=False,
        )
        if not auth_check(
            browser_context=browser_context
        ):
            logging_by_user(
                browser_context=browser_context
            )
        vacancies_parse(
            browser_context=browser_context
        )


def skip_vacancy(vacancy_id: str | None) -> None:
    config_hh = ConfigHh().model_dump()  # pyright: ignore[reportCallIssue]
    json_log_append({
        "status": "skipped",
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "url": f"{config_hh['vacancy_url']}{vacancy_id}"
            if vacancy_id else "Unknown url",
    })


def vacancies_parse(browser_context: BrowserContext) -> None:
    config_hh = ConfigHh().model_dump()  # pyright: ignore[reportCallIssue]
    page = browser_context.pages[0]
    page.goto(
        url=(
            config_hh["resume_vacancies_url"]
            + "?resume=YOUR_RESUME_ID"
        ),
        wait_until="domcontentloaded"
    )
    logging.info(
        msg="Collecting total vacancies count for search query."
    )
    title_string_with_total = page.locator(
        selector='div[data-qa="vacancies-search-header"] span'
    ).inner_text()
    if title_string_with_total:
        cleaned_title_string_with_total = re.sub(
            pattern=r"\s+",
            repl="",
            string=title_string_with_total
        )
        match_total_substring = re.search(
            pattern=r"(\d+)",
            string=cleaned_title_string_with_total
        )
        if match_total_substring:
            total_vacancies = match_total_substring.group(0)
        else:
            total_vacancies = 0
        logging.info(
            msg=(
                "Total vacancies count collected successfully: "
                f"{total_vacancies}."
            )
        )
        logging.info(
            msg="Starting vacancies parsing and applying."
        )
    else:
        logging.error(
            msg=(
                "RobJob finished with error: "
                "Unable to determine count of all vacancies."
            )
        )
        raise Exception("Unable to determine count of all vacancies.")
    # TODO: Add Select resume.
    for i in range((int(total_vacancies) + 49) // 50):
        vacancies_list = page.locator(
            selector=(
                'div[class^="magritte-card"]'
                '[data-qa="vacancy-serp__vacancy"]'
            )
        )
        for j in range(1):  # vacancies_list.count()
            link = vacancies_list.nth(j).locator(
                selector_or_locator='a[class^="magritte-button"]'
            ).first.get_attribute("href")
            if not link:
                logging.warning(
                    msg=(
                        "Unable to get vacancy link. Skippong vacancy."
                    )
                )
                continue
            applying_vacancy_page = browser_context.new_page()
            applying_vacancy_page.goto(
                url=config_hh["main_url"] + link,
                timeout=60000
            )
            if applying_vacancy_page.locator(
                selector='button[class^="magritte-button"]:has(span)',
                has_text=re.compile(r"^Откликнуться$")
            ).count() > 0:
                apply_vacancy(
                    page=applying_vacancy_page
                )
            else:
                skip_vacancy(
                    vacancy_id=parse_qs(
                        qs=urlparse(link).query
                    ).get("vacancyId", [None])[0]
                )
        page.locator(
            selector='a[data-qa="pager-page"]',
            has_text=re.compile(f"^{i + 2}$")
        ).click()


if __name__ == "__main__":
    main()
