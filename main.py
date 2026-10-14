import json
import logging
import random
import re
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from jinja2 import Template
from ollama import chat  # type: ignore
from playwright.sync_api import BrowserContext, Locator, Page, sync_playwright
from playwright_stealth import Stealth  # type: ignore

from config import ConfigHh
from core.exceptions import VacanciesDeterminationError


def apply_vacancy(browser_context: BrowserContext) -> None:
    page = browser_context.pages[1]
    config_hh = ConfigHh().model_dump()  # pyright: ignore[reportCallIssue]
    response_letter_textarea = page.locator(
        selector='textarea[data-qa^="vacancy-response"]'
    )
    vacancy_id = parse_qs(
        qs=urlparse(page.url).query
    ).get("vacancyId", [None])[0]
    vacancy_page_url = (
        f" {config_hh['vacancy_url']}/{vacancy_id}"
        if vacancy_id else "unknown_id"
    )
    if response_letter_textarea.is_visible():
        if vacancy_id:
            logging.info(
                msg=(
                    "Replying message is necessary for applying this vacancy."
                    " Attempting to get vacancy description to starting generate reply"
                    " message."
                )
            )
            vacancy_description = open_vacancy_page_and_find_description(
                browser_context=browser_context,
                vacancy_id=vacancy_id
            )
            if vacancy_description:
                logging.info(
                    msg=(
                        "Vacancy description has been got successfully."
                        " Starting to generate reply message and type it in to"
                        " specified field."
                    )
                )
                response_letter = type_response_letter(
                    input_entity=response_letter_textarea,
                    vacancy_description=vacancy_description,
                )
                page.locator(
                    selector='button[class^="magritte-button"]:has(span)',
                    has_text=re.compile(r"^Откликнуться$"),
                ).click()
                if captcha_check(
                    page=page,
                ):
                    solve_captcha()
                logging.info(
                    msg=(
                        "Replying message has been typed successfully,"
                        " and vacancy has been applied successfully."
                        " For more details check data log for vacancy url:"
                        f" {vacancy_page_url}."
                    )
                )
                json_log_append({
                    "status": "uplied",
                    "response_letter": response_letter,
                    "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "url": f"{vacancy_page_url}",
                })
                human_behavior_simulation(
                    page=page,
                    state="idle"
                )
        else:
            logging.info(
                msg=(
                    "Vacancy is unavailable for applying. Skipping vacancy."
                    " For more details check data log for vacancy url:"
                    f" {vacancy_page_url}."
                )
            )
            skip_vacancy(
                vacancy_id=None,
                reason=(
                    "Vacancy has been skipped due to unavailability"
                    " of getting vacancy id."
                ),
            )
    elif page.locator(
        selector='textarea[name^="task_"]'
    ).count():
        logging.info(
            msg=(
                "Vacancy is unavailable for applying. Skipping vacancy."
                " For more details check data log for vacancy url:"
                    f" {vacancy_page_url}."
            )
        )
        skip_vacancy(
            vacancy_id=vacancy_id,
            reason=(
                "Vacancy has been skipped due to requirement"
                " of answering additional questions."
            )
        )
    else:
        page.locator(
            selector='button[class^="magritte-button"]:has(span)',
            has_text=re.compile(r"^Откликнуться$"),
        ).click()
        if captcha_check(
            page=page,
        ):
            solve_captcha()
        logging.info(
            msg=(
                "Vacancy has been applied successfully."
                " For more details check data log for vacancy url:"
                f" {vacancy_page_url}."
            )
        )
        json_log_append({
            "status": "uplied",
            "response_letter": "",
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "url": f"{vacancy_page_url}",
        })
        human_behavior_simulation(
            page=page,
            state="idle"
        )


def auth_check(browser_context: BrowserContext) -> bool:
    logging.info(
        msg="Checking login state."
    )
    config_hh = ConfigHh().model_dump()  # pyright: ignore[reportCallIssue]
    page = browser_context.pages[0]
    page.goto(
        url=config_hh["main_url"],
        wait_until="domcontentloaded"
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


def captcha_check(page: Page) -> bool:
    return page.get_by_role(
        "dialog",
        name=re.compile(
            pattern="капч",
            flags=re.IGNORECASE,
        ),
    ).is_visible()


def change_chosen_vacancy(page: Page) -> None:
    config_hh = ConfigHh().model_dump()  # pyright: ignore[reportCallIssue]
    vacancies_selector = page.locator(
        selector='div[class^="magritte-cell"][data-qa="cell"]'
    ).filter(
        has=page.locator(
            selector='div[class^="magritte-wrapper"][data-qa="resume-title"]',
        )
    )
    vacancies_selector.click()
    page.locator(
        selector=f'label[data-magritte-select-option="{config_hh["resume_id"]}"]'
    ).click()


def check_chosen_vacancy(page: Page) -> bool:
    chosen_vacancy_element = page.locator(
        selector='div[class^="magritte-wrapper"][data-qa="resume-title"]'
    )
    if chosen_vacancy_element.is_visible():
        if chosen_vacancy_element.inner_text() != (
            "Python Backend Developer / Backend-разработчик Python"
        ):
            return False
    return True


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


def generate_response_letter(vacancy_description: str) -> str:
    system_prompt_template = Template(
        source=Path("neural_network/prompts/system.md").read_text(encoding="UTF-8")
    )
    response = chat(
        model="gemma3:4b",
        messages=[{
            "role": "system",
            "content": system_prompt_template.render(
                user_data=Path("neural_network/prompts/user_data.md").read_text(
                    encoding="UTF-8"
                )
            )
        },{
            "role": "user",
            "content": vacancy_description
        }],
        think=False,
        options={
            "temperature": 0.7,
        },
    )
    return response.message.content or ""


def get_vacancies_total(page: Page):
    logging.info(
        msg="Collecting total vacancies count for current resume."
    )
    title_string_with_total = page.locator(
        selector=(
            'div[data-qa="vacancies-search-header"]'
            ' div[data-qa="title-container"] span'
        )
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


def open_vacancy_page_and_find_description(
    browser_context: BrowserContext,
    vacancy_id: str
) -> str | None:
    config_hh = ConfigHh().model_dump()  # pyright: ignore[reportCallIssue]
    vacancy_page = browser_context.new_page()
    vacancy_page.goto(
        url=config_hh['vacancy_url'] + "/" + vacancy_id,
        wait_until="domcontentloaded"
    )
    human_behavior_simulation(
        page=vacancy_page,
        state="idle"
    )
    if vacancy_page.locator(
        selector='.vacancy-description'
    ).is_visible():
        logging.info(
            msg="Vacancy description collecting started."
        )
        vacancy_description = vacancy_page.locator(
            selector='[data-qa="vacancy-title"]'
        ).inner_text() + "\n"
        vacancy_salary_block = vacancy_page.locator(
            selector='[data-qa="vacancy-salary"]'
        )
        if vacancy_salary_block.is_visible():
            vacancy_description += "Зарплата: " + vacancy_page.locator(
                selector='[data-qa="vacancy-salary"]'
            ).inner_text() + "\n"
        else:
            vacancy_description += "Зарплата: не указана\n"
        vacancy_skills_block = vacancy_page.locator(
            selector='ul[class^="vacancy-skill-list"]'
        )
        if vacancy_skills_block.is_visible():
            vacancy_description += "Ключевые навыки: " + ", " .join([
                line for line in vacancy_page.locator(
                    selector='ul[class^="vacancy-skill-list"]'
                ).inner_text().splitlines()
            ]) + "\n"
        else:
            vacancy_description += "Ключевые навыки: не указаны\n"
        # TODO: Add more fields, for example: employment, schedule and etc.
        vacancy_description += "\n".join([
            line for line in vacancy_page.locator(
                selector='.vacancy-description [data-qa="vacancy-description"]'
            ).inner_text().splitlines() if line.strip()
        ])
        vacancy_page.close()
        return vacancy_description
    else:
        vacancy_page.close()
        logging.info(
            msg=(
                "Vacancy is unavailable for applying. Skipping vacancy."
                " For more details check data log for vacancy url:"
                f" {config_hh['vacancy_url']}/{vacancy_id}."
                    if vacancy_id else "unknown_id"
            )
        )
        skip_vacancy(
            vacancy_id=vacancy_id,
            reason=(
                "Vacancy has been skipped due to unavailability"
                " of getting vacancy description."
            ),
        )
        return None


def open_vacancy_response_page(
    browser_context: BrowserContext,
    vacancy_link: str
) -> None:
    logging.info(
        msg="Opening vacancy applying page."
    )
    page = browser_context.new_page()
    config_hh = ConfigHh().model_dump()  # pyright: ignore[reportCallIssue]
    page.goto(
        url=config_hh["main_url"] + vacancy_link,
        wait_until="domcontentloaded",
    )
    human_behavior_simulation(
        page=page,
        state="idle"
    )
    if captcha_check(
        page=page,
    ):
        solve_captcha()
    # TODO: Horrible checking. Please, change it.
    logging.info(
        msg="Checking chosen vacancy on the page."
    )
    if not check_chosen_vacancy(
        page=page
    ):
        logging.info(
            msg="Chosen vacancy on the page is not suitable. Changing it."
        )
        change_chosen_vacancy(
            page=page
        )
    logging.info(
        msg="Suitable vacancy is now chosen."
    )
    logging.info(
        msg="Checking vacancy applying possibility."
    )
    if page.locator(
        selector='button[class^="magritte-button"]:has(span)',
        has_text=re.compile(r"^Откликнуться$")
    ).count() > 0:
        apply_vacancy(
            browser_context=browser_context,
        )
    else:
        vacancy_id=parse_qs(
            qs=urlparse(vacancy_link).query
        ).get("vacancyId", [None])[0]
        logging.info(
            msg=(
                "Vacancy is unavailable for applying. Skipping vacancy."
                " For more details check data log for vacancy url:"
                f" {config_hh['vacancy_url']}/{vacancy_id}."
                    if vacancy_id else "unknown_id"
            )
        )
        skip_vacancy(
            vacancy_id=vacancy_id,
            reason=(
                "Vacancy has been skipped due to applying before"
                " or applying unavailability."
            ),
        )
    page.close()


def skip_vacancy(vacancy_id: str | None, reason: str = "Reason not specified") -> None:
    config_hh = ConfigHh().model_dump()  # pyright: ignore[reportCallIssue]
    json_log_append({
        "status": "skipped",
        "reason": reason,
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "url": f"{config_hh['vacancy_url']}/{vacancy_id}"
            if vacancy_id else "unknown_id",
    })


def solve_captcha() -> None:
    input("Please, solve the CAPTCHA in your browser, then press Enter to continue...")
    logging.info(
        msg="CAPTCHA solving has been required. User confirmed CAPTCHA completion."
    )


# WARNING: This function works with input_entity like textarea.
# But other inputs can have problems.
def type_response_letter(input_entity: Locator, vacancy_description: str) -> str:
    input_entity.click()
    if input_entity.input_value():
        input_entity.press("Control+A")
        input_entity.press("Backspace")
    # TODO: Add humanisation pause
    response_letter = generate_response_letter(
        vacancy_description=vacancy_description
    ).strip()
    response_letter_by_words = response_letter.split(" ")
    chunked_response_letter = [
        " ".join(response_letter_by_words[i:i + 10])
        for i in range(0, len(response_letter_by_words), 10)
    ]
    for chunk in chunked_response_letter:
        input_entity.press_sequentially(
            text=chunk + " ",
            delay=random.randint(30, 100),
        )
    input_entity.press("Backspace")
    return response_letter


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
    if captcha_check(
        page=page,
    ):
        solve_captcha()
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
                'ol[class^="vacancies-list"] > li'
            )
        )
        for j in range(vacancies_list.count()):
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
            open_vacancy_response_page(
                browser_context=browser_context,
                vacancy_link=link
            )
        page.locator(
            selector='a[data-qa="pager-page"]',
            has_text=re.compile(f"^{i + 2}$")
        ).click(
            force=True
        )


if __name__ == "__main__":
    main()
    # FIXME Configs don't transfer and don't dump. Change it to OOP
    # FIXME: reply without test - block. Skip vacancy.
    # FIXME: test check before cover letter generation.

    # TODO Have to add other states to human behavior.
    # TODO: Add retrying functionality and change domcontentloaded to networkidle.
    # TODO: is_visible check change to
        # vacancy_description_locator.wait_for(state="visible")
        # vacancy_description = vacancy_description_locator.inner_text()
