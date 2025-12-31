import asyncio
import os
from playwright.async_api import async_playwright
import time

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()

        # Base URL
        base_url = "http://localhost:8501"
        
        # Ensure docs directory exists
        docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")
        os.makedirs(docs_dir, exist_ok=True)

        print(f"Go to {base_url}")
        try:
            await page.goto(base_url, timeout=60000)
            await page.wait_for_load_state("networkidle")
            # Wait for some content to ensure it's loaded
            await page.wait_for_selector(".main", timeout=30000)
            
            # Screenshot Home
            print("Capturing Home...")
            await page.screenshot(path=os.path.join(docs_dir, "screenshot_home.png"))
            
            # Function to navigate and capture
            # Streamlit sidebar navigation
            # We can find links in the sidebar
            
            # 1. Search Page
            # print("Navigating to Search...")
            # await page.click('text=🔍 搜尋') 
            # await page.wait_for_load_state("networkidle")
            # await page.wait_for_timeout(2000)
            # await page.screenshot(path=os.path.join(docs_dir, "screenshot_search.png"))

            # 2. Filter Page
            # print("Navigating to Filter...")
            # await page.click('text=🎛️ 篩選') 
            # await page.wait_for_load_state("networkidle")
            # await page.wait_for_timeout(2000)
            # await page.screenshot(path=os.path.join(docs_dir, "screenshot_filter.png"))

            # 3. Ranking Page
            print("Navigating to Ranking...")
            await page.click('text=🏆 排名') 
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(2000)
            # Scroll down a bit to show the table clearly
            await page.evaluate("window.scrollBy(0, 300)")
            await page.wait_for_timeout(1000)
            await page.screenshot(path=os.path.join(docs_dir, "screenshot_ranking.png"))
            
            # 4. AI Page
            # print("Navigating to AI...")
            # await page.click('text=🤖 AI智慧選股')
            # await page.wait_for_load_state("networkidle")
            # await page.wait_for_timeout(2000) 
            # await page.screenshot(path=os.path.join(docs_dir, "screenshot_ai.png"))

            print("All screenshots captured.")

        except Exception as e:
            print(f"Error: {e}")
            # Capture debug screenshot
            await page.screenshot(path="debug_error.png")
            print(await page.content())
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
