import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set to False to watch it work!
        page = await browser.new_page()
        api_endpoints = set()

        # Monitor data APIs
        page.on("request", lambda r: api_endpoints.add(f"[{r.method}] {r.url}") if r.resource_type in ["xhr", "fetch"] else None)

        print("Navigating to target page...")
        await page.goto("https://smartoptions.trendlyne.com/dashboard/options/latest/", wait_until="networkidle")

        # --- STEP 1: OPEN DROPDOWNS / HAMBURGER MENUS ---
        # Look for typical menu toggle buttons (hamburger icons, dropdown triggers)
        menu_triggers = '[aria-haspopup="true"], button:has-text("Menu"), .hamburger, .menu-toggle, dropdown-toggle'
        triggers = await page.locator(menu_triggers).all()
        
        for trigger in triggers:
            try:
                if await trigger.is_visible():
                    print("Opening a menu dropdown...")
                    await trigger.click()
                    await asyncio.sleep(0.5) # Wait for dropdown animation to finish
            except Exception:
                continue

        # --- STEP 2: COLLECT ALL TABS AND MENU ITEMS ---
        # This expanded selector targets tabs, navigation buttons, and links inside navigation headers or dropdowns
        expanded_selector = (
            '[role="tab"], '                  # Standard tabs
            'nav button, nav a, '             # Items inside standard navigation bars
            '.menu-item, .dropdown-item, '    # Items likely inside dropdowns
            'ul.tabs li, [role="menuitem"]'   # Accessible menu items
        )
        
        clickable_items = await page.locator(expanded_selector).all()
        print(f"Found {len(clickable_items)} potential navigation/menu elements.")

        # --- STEP 3: CLICK EVERYTHING SEQUENTIALLY ---
        for index, item in enumerate(clickable_items):
            try:
                if await item.is_visible() and await item.is_enabled():
                    item_text = await item.inner_text()
                    print(f"Clicking item {index + 1}: '{item_text.strip()}'")
                    
                    await item.click()
                    await asyncio.sleep(1.5)  # Wait for the API to trigger
                    
                    # Scroll down a bit in case the action lazy-loads data
                    await page.evaluate("window.scrollBy(0, 300)")
                    await asyncio.sleep(0.5)
            except Exception:
                # If an item becomes hidden or detaches after a page shift, skip it safely
                continue

        print(f"\n--- Total Discovered APIs: {len(api_endpoints)} ---")
        print(api_endpoints)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
