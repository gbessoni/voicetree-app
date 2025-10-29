from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # Create a user
    page.request.post("http://localhost:8000/api/users", data={
        "username": "testuser",
        "display_name": "Test User",
        "bio": "This is a test bio."
    })

    # Go to the profile page
    page.goto("http://localhost:8000/testuser")
    page.wait_for_load_state()
    page.screenshot(path="jules-scratch/verification/before_fill.png")

    # Submit a voice bio
    page.fill("#voice-bio-text", "Hello, this is a test voice bio.")
    page.click("button[type=submit]")
    page.wait_for_timeout(5000) # wait for 5 seconds

    # Go to the admin page
    page.goto("http://localhost:8000/admin")
    page.wait_for_load_state()
    page.screenshot(path="jules-scratch/verification/admin_page.png")

    # Approve the voice bio
    page.click(".approve-btn")

    # Go back to the profile page
    page.goto("http://localhost:8000/testuser")
    page.wait_for_load_state()
    page.screenshot(path="jules-scratch/verification/profile_page.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
