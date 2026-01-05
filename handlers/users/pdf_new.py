# import os
# PYPPETEER_CHROMIUM_REVISION = '1181217'
# os.environ['PYPPETEER_CHROMIUM_REVISION'] = PYPPETEER_CHROMIUM_REVISION

from environs import Env
from pyppeteer import launch
import ssl
import asyncio
import time


env = Env()
env.read_env()

FRONT_END_URL = env.str("FRONT_END_URL")


async def generate_pdf(guid, pdf_path):
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    browser = await launch(headless=True, args=['--no-sandbox'])
    page = await browser.newPage()
    response = await page.goto(f"{FRONT_END_URL}/results/{guid}",
                               {'waitUntil': 'networkidle2', 'timeout': 60000})
    time.sleep(4)
    print("FILE STATUS", response.status)
    if response.status in [200, '200']:
        await page.pdf({'path': pdf_path, 'format': 'A4'})
    
    await browser.close()
    print('CLOSED')