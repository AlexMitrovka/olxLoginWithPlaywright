import asyncio
import concurrent.futures
from bs4 import BeautifulSoup as bs
from playwright.async_api import async_playwright,TimeoutError as PlaywrightTimeoutError,expect
from pathlib import Path
import json
import aiofiles
import re

path_to_extension = Path(__file__).parent.joinpath("buster-solver")
user_data_dir = "/tmp/test-user-data-dir"


async def run(playwright, login, password):
    #print(path_to_extension)
    browser = await playwright.chromium.launch_persistent_context(
        f'{user_data_dir}{login}',
        headless=True,
        args=[
            f"--disable-extensions-except={path_to_extension}",
            f"--load-extension={path_to_extension}",
            ],
    )
    page = await browser.new_page()
    await page.goto("https://www.olx.ua/uk/myaccount/")
    await page.wait_for_load_state()
    async def url_compile(reg_exp, current_url=page.url):
        return reg_exp.match(current_url)
    pattern_logged = re.compile(r".*/d/uk/myaccount/")
    pattern_not_logged = re.compile(r".*/uk/")
    if not await url_compile(pattern_logged):
        if not await url_compile(pattern_not_logged):
            await page.goto("https://www.olx.ua/uk/myaccount/")
        logged = True
        while(logged):
            try:
                await page.locator("input[name=\"username\"]").fill(login)
                await page.locator("input[name=\"password\"]").fill(password)
                await page.get_by_test_id("login-submit-button").click()
                try:
                    iframe = await page.wait_for_selector('iframe[title="reCAPTCHA"]')
                    exist = True
                except:
                    exist = False
                    pass

                #print(iframe)
                if exist:
                    print('Please Solve the captcha')
                    await asyncio.sleep(1)
                    await page.locator('iframe[title="reCAPTCHA"]').click()
                    iframe_with_image = await page.wait_for_selector('iframe[title="recaptcha challenge expires in two minutes"]')
                    if iframe_with_image:
                        await page.frame_locator('iframe[title="recaptcha challenge expires in two minutes"]').locator(
                            "button[title='Get an audio challenge']").click()
                        await asyncio.sleep(0.5)
                        await page.frame_locator('iframe[title="recaptcha challenge expires in two minutes"]').locator(
                            "div[class='button-holder help-button-holder']").click()
                        print('Load succefully')
                        logged = False
                logged = False
            except Exception as e:
                print("Exception as ", e)
                page.reload()
                pass

    print(f"Logined {login} succefuly")

    await page.wait_for_load_state("domcontentloaded")
    try:
        await page.wait_for_selector('li[data-testid="tabs-messages"]')
        js_check_msg = """
           document.querySelector('li[data-testid="tabs-messages"] > a > span') ? document.querySelector('li[data-testid="tabs-messages"] > a > span').innerHTML : "0"
        """
        count = await page.evaluate_handle(js_check_msg)
        print(f'{login} u have {count} message')
        # if msg:
        #     print(f'{login} have msg')
    except Exception as e:
        print(f"Exception {login} : {e}")

    finally:
        await page.close()
        #print(f'{login} closed')

async def procces(login, password):
    async with async_playwright() as playwright:
        await run(playwright, login, password)

async def main():
    task = list()
    accounts = {
        'user_name': ['Login'], #May use array login and password
        'password': ['Password'],
    }
    count_accounts = len(accounts['user_name'])
    for i in range(count_accounts):
        login = accounts['user_name'][i]
        password = accounts['password'][i]
        task.append(asyncio.create_task(procces(login, password)))
    await asyncio.gather(*task)


if __name__ == "__main__":
    asyncio.run(main())