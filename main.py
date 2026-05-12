import json
import logging
import random
import re
import time
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import BrowserContext, Page, sync_playwright
from playwright_stealth import Stealth  # type: ignore

from config import ConfigHh
from core.exceptions import VacanciesDeterminationError


def apply_vacancy(page: Page) -> None:
    response_letter_textarea = page.locator(
        selector='textarea[data-qa^="vacancy-response"]'
    )
    vacancy_id = parse_qs(qs=urlparse(page.url).query).get("vacancyId", [None])[0]
    if response_letter_textarea.count():
        logging.info(
            msg=(
                "Vacancy has been skipped due to response letter presence."
                " For more details check data log for vacancy url:"
            )
        )
        #TODO: URL or response
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
        logging.info(
            msg=(
                "Vacancy has been applied successfully."
                " For more details check data log for vacancy url:"
                f" {config_hh['vacancy_url']}/{vacancy_id}."
                    if vacancy_id else "Unknown url."
            )
        )  # FIXME: url to variable. Or You can change way in general.
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


def bezier_curve(
    t: float,
    p0: dict[str, int],
    p1: dict[str, int],
    p2: dict[str, int],
    p3: dict[str, int],
) -> tuple[float, float]:
    x = (
        (1 - t) ** 3 * p0["x"] +
        3 * (1 - t) ** 2 * t * p1["x"] +
        3 * (1 - t) * t ** 2 * p2["x"] +
        t ** 3 * p3["x"]
    )
    y = (
        (1 - t) ** 3 * p0["y"] +
        3 * (1 - t) ** 2 * t * p1["y"] +
        3 * (1 - t) * t ** 2 * p2["y"] +
        t ** 3 * p3["y"]
    )
    return (x, y)


def bezier_trace_mouse_move(
    page: Page,
    pointer_end: dict[str, int],
    pointer_start: dict[str, int],
) -> None:
    steps = random.randint(35, 80)
    control_point_1 = generate_control_points(
        page=page
    )
    control_point_2 = generate_control_points(
        page=page
    )
    for step in range(steps + 1):
        t = step / steps
        ease_t = t * t * (3 - 2 * t) # Ease in-out t
        x, y = bezier_curve(
            t=ease_t,
            p0=pointer_start,
            p1=control_point_1,
            p2=control_point_2,
            p3=pointer_end,
        )
        page.mouse.move(x, y)
        time.sleep(random.uniform(0.003, 0.015))


def generate_control_points(page: Page) -> dict[str, int]:
    viewport = page.viewport_size
    if viewport is None:
        viewport = page.evaluate("""
            () => ({
                height: window.innerHeight,
                width: window.innerWidth
            });
        """)
    return {
        "x": random.randint(0, viewport["width"]),
        "y": random.randint(0, viewport["height"]),
    }


def get_vacancies_total(page: Page):
    logging.info(
        msg="Collecting total vacancies count for current resume."
    )
    title_string_with_total = page.locator(
        selector='div[data-qa="vacancies-search-header"] span'
    ).inner_text()
    if not title_string_with_total:
        logging.error(
            msg=(
                "RobJob finished with error: "
                "Unable to determine count of all vacancies."
            )
        )
        raise VacanciesDeterminationError
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
    return total_vacancies


def json_log_append(data: dict[str, str]) -> None:
    with open(
        file="vacancies_replyed.jsonl",
        mode="a",
        encoding="utf-8"
    ) as vacancies_replyed_jsonl:
        vacancies_replyed_jsonl.write(
            json.dumps(data, ensure_ascii=False) + "\n"
        )


def human_behavior_simulation(page: Page, state: str) -> None:
    if state == "idle":
        time.sleep(random.uniform(1, 5))
        pointer_start = generate_control_points(
            page=page
        )
        pointer_end = generate_control_points(
            page=page
        )
        bezier_trace_mouse_move(
            page=page,
            pointer_end=pointer_end,
            pointer_start=pointer_start,
        )


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
    logging.info(
        msg="RobJob started."
    )
    logging.info(
        msg="Initializing browser context."
    )
    with Stealth().use_sync(sync_playwright()) as stealth_sync_playwright:
        browser = stealth_sync_playwright.chromium
        browser_context: BrowserContext = browser.launch_persistent_context(
            user_data_dir="./user_data",
            args=[
                "--disable-blink-features=AutomationControlled"
            ],
            headless=False,
        )
        logging.info(
            msg="Browser context has been initialized successfully."
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


def open_vacancy_page(browser_context: BrowserContext, vacancy_link: str):
    logging.info(
        msg="Opening vacancy applying page."
    )
    page = browser_context.new_page()
    config_hh = ConfigHh().model_dump()  # pyright: ignore[reportCallIssue]
    page.goto(
        url=config_hh["main_url"] + vacancy_link,
        wait_until="networkidle"
    )
    human_behavior_simulation(
        page=page,
        state="idle"
    )
    logging.info(
        msg="Checking vacancy applying possibility."
    )
    if page.locator(
        selector='button[class^="magritte-button"]:has(span)',
        has_text=re.compile(r"^Откликнуться$")
    ).count() > 0:
        apply_vacancy(
            page=page
        )
    else:
        skip_vacancy(
            vacancy_id=parse_qs(
                qs=urlparse(vacancy_link).query
            ).get("vacancyId", [None])[0]
        )


def skip_vacancy(vacancy_id: str | None) -> None:
    config_hh = ConfigHh().model_dump()  # pyright: ignore[reportCallIssue]
    json_log_append({
        "status": "skipped",
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "url": f"{config_hh['vacancy_url']}/{vacancy_id}"
            if vacancy_id else "Unknown url",
    })


def vacancies_parse(browser_context: BrowserContext) -> None:
    config_hh = ConfigHh().model_dump()  # pyright: ignore[reportCallIssue]
    page = browser_context.pages[0]
    human_behavior_simulation(
        page=page,
        state="idle"
    )
    logging.info(
        msg="Resume vacancies page redirecting."
    )
    page.goto(
        url=(
            config_hh["resume_vacancies_url"]
            + f'?resume={config_hh["resume_id"]}'
        ),
        wait_until="domcontentloaded"
    )
    human_behavior_simulation(
        page=page,
        state="idle"
    )
    total_vacancies = get_vacancies_total(
        page=page
    )
    logging.info(
        msg="Starting vacancies parsing and applying."
    )
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
                        "Unable to get vacancy link. Skipping vacancy."
                    )
                )
                continue
            open_vacancy_page(
                browser_context=browser_context,
                vacancy_link=link
            )
        page.locator(
            selector='a[data-qa="pager-page"]',
            has_text=re.compile(f"^{i + 2}$")
        ).click()


if __name__ == "__main__":
    main()
    # FIXME Configs don't transfer and don't dump. Change it to OOP
    # TODO Have to add other states to human behavior.
