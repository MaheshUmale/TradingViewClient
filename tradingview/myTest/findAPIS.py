import asyncio
from urllib.parse import urlparse, parse_qs
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Listen for background network calls
        async def handle_request(request):
            # Only listen to data APIs (XHR and Fetch), skip JS/CSS/Images
            if request.resource_type in ["xhr", "fetch"]:
                url = request.url
                method = request.method
                
                print(f"\n{"="*40}")
                print(f"📡 API FOUND: [{method}] {url.split('?')[0]}")
                print(f"{"="*40}")

                # Case 1: Handle GET Parameters (Query Params in URL)
                parsed_url = urlparse(url)
                query_params = parse_qs(parsed_url.query)
                if query_params:
                    print("➡️ URL Query Parameters:")
                    for key, val in query_params.items():
                        print(f"   • {key}: {val[0] if len(val) == 1 else val}")

                # Case 2: Handle POST/PUT Payload (Body Data)
                if method in ["POST", "PUT", "PATCH"]:
                    post_data = request.post_data
                    if post_data:
                        print("➡️ Post Body Payload:")
                        # Try to format it cleanly if it's JSON text
                        if request.headers.get("content-type", "").startswith("application/json"):
                            print(f"   Format: JSON")
                            print(f"   Body: {post_data}")
                        else:
                            print(f"   Format: Raw Text/Form Data")
                            print(f"   Body: {post_data[:200]}...") # truncate if too long

        # Attach the network listener
        page.on("request", handle_request)

        print("Navigating to target page...")
        # Replace with your target URL
        await page.goto("https://smartoptions.trendlyne.com/dashboard/options/latest/", wait_until="networkidle")

        # Simulate scrolling to trigger APIs
        print("Scrolling down to capture APIs...")
        for _ in range(3):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(1.5)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
