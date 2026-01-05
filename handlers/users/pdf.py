import asyncio

from environs import Env
from playwright.async_api import async_playwright
import time

env = Env()
env.read_env()

FRONT_END_URL = env.str("FRONT_END_URL")

async def generate_pdf(guid, pdf_path):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = await browser.new_page()
        await page.goto(f"{FRONT_END_URL}/results/{guid}", wait_until="networkidle")
        time.sleep(4)
        file = await page.pdf(path=pdf_path, format='A4', print_background=False)
        await browser.close()
        print(f"PDF saved at {pdf_path}")
        return file




async def generate_pdf_service(id, pdf_path):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = await browser.new_page()
        await page.goto(f"{FRONT_END_URL}/results?id={id}", wait_until="networkidle")
        time.sleep(4)
        file = await page.pdf(path=pdf_path, format='A4', print_background=False)
        await browser.close()
        print(f"PDF saved at {pdf_path}")
        return file
