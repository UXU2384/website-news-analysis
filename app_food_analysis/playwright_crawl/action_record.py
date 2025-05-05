import asyncio
from playwright.async_api import async_playwright

async def crawler_start()->str:
  
    async with async_playwright() as p:
    
        executable_path="C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
        profile_path = 'C:/Users/r1138/AppData/Local/Microsoft/Edge/User Data'
        
        browser = await p.chromium.launch_persistent_context(
            executable_path=executable_path,
            user_data_dir=profile_path,
            headless=False,
        )

        page = await browser.new_page()
        await page.goto("https://www.foodpanda.com.tw")

        parent_locator = page.locator(".joker-swimlane-sds.bg-interaction-primary-feedback.bc-interaction-tertiary > div > div.lane-wrapper > ul").first
        locator = parent_locator.locator("li").first
        await locator.wait_for(state="visible", timeout=10*1000)
        text = await parent_locator.inner_html()

        await browser.close()
    
        return text

if __name__ == "__main__":
    html = asyncio.run(crawler_start())
    print(html)