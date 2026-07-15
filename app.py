import streamlit as st
import asyncio
from playwright.async_api import async_playwright
import re
import pandas as pd
import requests
import time

EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

# Production Ready API Authentication Credentials
NOCAPTCHA_KEY = "nocap_mXo9eRBFl2p43IvDCz59YRIB"
BROWSERLESS_TOKEN = "2Ut3fEHQ16eosEu1933e524fc961f5ba1b80dfc4fcf1c782c" 

async def solve_captcha_via_api(url):
    st.info("🤖 CAPTCHA layer triggered. Invoking noCaptchaAi background array...")
    payload = {
        "clientKey": NOCAPTCHA_KEY,
        "task": {
            "type": "ReCaptchaV2TaskProxyless",
            "websiteURL": url,
            "websiteKey": "6Lc3ny0UAAAAAFg48w1Z5w7975w7975w7975" # YouTube global reCAPTCHA target key
        }
    }
    try:
        res = requests.post("https://nocaptchaai.com", json=payload).json()
        if res.get("errorId") == 0:
            task_id = res.get("taskId")
            for _ in range(30):
                await asyncio.sleep(2)
                status = requests.post("https://nocaptchaai.com", json={
                    "clientKey": NOCAPTCHA_KEY,
                    "taskId": task_id
                }).json()
                if status.get("status") == "ready":
                    st.success("✅ Challenge successfully resolved by solver.")
                    return status.get("solution", {}).get("gRecaptchaResponse")
        return None
    except Exception as e:
        st.error(f"Solver pipeline error: {e}")
        return None

async def run_deep_browser_scrape(target_url, max_scrolls):
    emails_found = []
    st_status = st.empty()
    
    # Clean standard endpoint format without complex flags to avoid firewall timeout drops
    ws_endpoint = f"wss://chrome.browserless.io/chromium?token={BROWSERLESS_TOKEN}"
    
    async with async_playwright() as p:
        st_status.text("🌐 Establishing connection to remote cloud browser...")
        try:
            # Increased timeout threshold to ensure the connection handshakes reliably
            browser = await p.chromium.connect(ws_endpoint, timeout=60000)
        except Exception as conn_err:
            st.error(f"Failed to connect to Browserless Cloud Instance: {str(conn_err)}")
            return []
            
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = await context.new_page()
        
        st_status.text("📹 Navigating to target video layout...")
        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(4000)
        except Exception as nav_err:
            st.error(f"Page loading timed out or failed: {str(nav_err)}")
            await browser.close()
            return []
        
        # Initial scroll down to bring components into viewport focus
        await page.evaluate("window.scrollTo(0, 700);")
        await page.wait_for_timeout(3000)
        
        # Iterative scrolling engine execution loop
        for scroll in range(int(max_scrolls)):
            st_status.text(f"⏳ Advancing view depth via scroll sequences ({scroll+1}/{max_scrolls})...")
            await page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight);")
            await page.wait_for_timeout(2500)
            
            if await page.locator("iframe[src*='recaptcha']").count() > 0:
                token = await solve_captcha_via_api(target_url)
                if token:
                    await page.evaluate(f'document.getElementById("g-recaptcha-response").innerHTML="{token}";')
        
        st_status.text("💥 Clicking 'Read more' toggles to expand hidden text...")
        expand_buttons = await page.locator("text=Read more").all()
        for btn in expand_buttons[:30]:
            try:
                await btn.click(timeout=1000)
            except:
                pass
                
        st_status.text("🔍 Parsing loaded webpage text arrays for pattern matching...")
        comment_nodes = await page.locator("#content-text").all_inner_texts()
        
        for text in comment_nodes:
            matches = re.findall(EMAIL_REGEX, text)
            for email in matches:
                if email not in [e.get('Captured Email') for e in emails_found]:
                    emails_found.append({
                        "Captured Email": email,
                        "Source Comment Context": text[:120] + "..."
                    })
                    
        await context.close()
        await browser.close()
        
    return emails_found

# Render View Layout Setup Configuration Engine
st.set_page_config(page_title="Playwright Web Harvester", layout="centered")
st.title("🎯 Playwright Cloud Harvester Engine")
st.caption("Running fully integrated browser pipelines via Browserless & noCaptchaAi")

target_link = st.text_input("Paste Target YouTube URL Node:")
scroll_depth = st.slider("Automated Scroll Depth Configuration:", 5, 40, 15)

if st.button("Deploy Automation Sequence", type="primary"):
    if target_link:
        with st.spinner("Executing remote script routines..."):
            leads = asyncio.run(run_deep_browser_scrape(target_link, scroll_depth))
            
            if leads:
                df = pd.DataFrame(leads)
                st.dataframe(df, use_container_width=True)
                
                csv_bytes = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Extracted Leads (.CSV)",
                    data=csv_bytes,
                    file_name="yt_playwright_leads.csv",
                    mime="text/csv"
                )
            else:
                st.warning("Routine completed. No matching email configurations discovered across selected depth.")
    else:
        st.error("Please insert an accessible YouTube web link target.")
