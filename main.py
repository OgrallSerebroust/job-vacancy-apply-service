import json
import logging
import random
import re
from playwright.sync_api import Browser, Page, sync_playwright
from playwright_stealth import Stealth  # type: ignore


def apply_vacancy(page: Page) -> None:
    page.mouse.move(
        random.randint(100, 500),
        random.randint(100, 500)
    )
    response_letter_textarea = page.locator(
        selector='textarea[data-qa^="vacancy-response"]'
    )
    if response_letter_textarea.count():
        response_letter_textarea.click()
        response_letter_textarea.type(
            text=(
                "Здравствуйте! Я заинтересован в вашей вакансии и хотел бы"
                " откликнуться на неё.\nТест рыба"
            ),
            delay=random.randint(30, 100)
        )
    # page.click(
    #     selector='button[class^="magritte-button"]:has(span:has-text("Откликнуться"))'
    # )
    json_log_append({
        "test": page.url
    })
    # time.sleep(10000)
    page.close()
    # TODO: sleep and stealth. HH uses behavior analysis.


def auth_check(browser: Browser) -> bool:
    try:
        browser.new_context(
            storage_state="auth.json"
        )
        logging.info(
            msg="auth.json found. Attempting to login by it."
        )
        return True
    except FileNotFoundError:
        logging.warning(
            msg="auth.json not found. Attempting to initialize login by user."
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


def logging_by_user(browser: Browser) -> None:
    context = browser.new_context()
    page = context.new_page()
    page.goto(
        url="https://hh.ru"  # TODO: transport to config
    )
    input("Please, login by yourself and press Enter...")
    context.storage_state(
        path="auth.json"
    )
    logging.info(
        msg="Login by user completed. Storage state saved to auth.json."
    )


def skip_vacancy() -> None:
    logging.warning(
        msg="Skip"
    )
    pass


def vacancies_parse(browser: Browser) -> None:
    context = browser.new_context(
        storage_state="auth.json"
    )
    logging.info(
        msg="Authenticated successfully."
    )
    page = context.new_page()
    page.goto(
        url="https://hh.ru/search/vacancy?resume=YOUR_RESUME_ID&from=resumelist",
        timeout=60000
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
            applying_vacancy_page = context.new_page()
            applying_vacancy_page.goto(
                url="https://hh.ru" + link,
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
                skip_vacancy()
        page.locator(
            selector='a[data-qa="pager-page"]',
            has_text=re.compile(f"^{i + 2}$")
        ).click()


if __name__ == "__main__":
    logging.basicConfig(
        filename="app.log",
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    logging.info("RobJob started.")
    with Stealth().use_sync(sync_playwright()) as stealth_sync_playwright:
        browser: Browser = stealth_sync_playwright.chromium.launch(
            headless=False
        )
        if not auth_check(
            browser=browser
        ):
            logging_by_user(
                browser=browser
            )
        try:
            vacancies_parse(
                browser=browser
            )
        except Exception as exception:
            logging.error("RobJob failed with error: " + str(exception))
