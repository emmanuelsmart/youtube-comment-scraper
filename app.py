import streamlit as st
import requests
import re
import pandas as pd
import time

EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
NOCAPTCHA_KEY = "nocap_mXo9eRBFl2p43IvDCz59YRIB"

def extract_video_id(url):
    video_id_match = re.search(r'(?:v=|\/)([a-zA-Z0-9_-]{11})', url)
    return video_id_match.group(1) if video_id_match else None

def solve_captcha_if_needed(site_url, site_key):
    st.info("🤖 CAPTCHA challenge detected by automation loop. Invoking noCaptchaAi...")
    payload = {
        "clientKey": NOCAPTCHA_KEY,
        "task": {
            "type": "ReCaptchaV2TaskProxyless",
            "websiteURL": site_url,
            "websiteKey": site_key
        }
    }
    try:
        # Create solving task via noCaptchaAi API
        res = requests.post("https://api.nocaptchaai.com/createTask", json=payload).json()
        if res.get("errorId") == 0:
            task_id = res.get("taskId")
            # Poll for the solution token
            for _ in range(30):
                time.sleep(2)
                status_res = requests.post("https://nocaptchaai.com", json={
                    "clientKey": NOCAPTCHA_KEY,
                    "taskId": task_id
                }).json()
                if status_res.get("status") == "ready":
                    st.success("✅ CAPTCHA successfully bypassed by AI solver!")
                    return status_res.get("solution", {}).get("gRecaptchaResponse")
        return None
    except Exception as e:
        st.error(f"Solver connection issue: {e}")
        return None

def deep_scrape_comments(video_url, targets_count):
    video_id = extract_video_id(video_url)
    if not video_id:
        st.error("Invalid YouTube URL path.")
        return []

    emails_found = []
    status_box = st.empty()
    
    # Target endpoint mapping data blocks directly to simulate scroll depth pagination
    base_endpoint = f"https://lemnoslife.com{video_id}"
    next_page_token = ""
    iterations = min(int(targets_count / 20), 15) # Max batches mapping deep iterations

    for batch in range(iterations + 1):
        status_box.text(f"⏳ Simulating deep scroll & structural clicking (Batch {batch + 1}/{iterations + 1})...")
        
        url = f"{base_endpoint}&maxResults=100"
        if next_page_token:
            url += f"&pageToken={next_page_token}"
            
        try:
            res = requests.get(url).json()
            
            # Simulated trigger if YouTube prompts a verification challenge route
            if "captcha" in str(res).lower():
                token = solve_captcha_if_needed(video_url, "6Lc3ny0UAAAAAFg48w1Z5w7975w7975w7975")
                if token:
                    continue # Try repeating item collection with bypassed session context

            if 'items' in res:
                for item in res['items']:
                    top_comment = item['snippet']['topLevelComment']['snippet']
                    comment_text = top_comment['textDisplay']
                    author = top_comment['authorDisplayName']
                    
                    # Pattern verification
                    matches = re.findall(EMAIL_REGEX, comment_text)
                    for email in matches:
                        if email not in [e['Email'] for e in emails_found]:
                            emails_found.append({
                                "Username": author,
                                "Email": email,
                                "Extract Segment": comment_text[:80] + "..."
                            })
            
            next_page_token = res.get('nextPageToken')
            if not next_page_token:
                break # Reached terminal end of the thread structure
                
            time.sleep(1.5) # Anti-detection pacing delay
            
        except Exception as e:
            st.error(f"Execution tracking interrupted: {str(e)}")
            break

    status_box.text(f"📊 Completed! Processed deep threads and extracted {len(emails_found)} target profiles.")
    return emails_found

# Render View UI 
st.set_page_config(page_title="Advanced Cloud Scraper", layout="centered")
st.title("🎯 Pro YouTube Email Harvester")
st.caption("Utilizing automated parsing arrays & noCaptchaAi integrations")

video_url = st.text_input("Paste Target YouTube Video Link:")
depth_selection = st.select_slider("Target Comment Depth Lookahead:", options=[50, 100, 200, 500, 1000], value=100)

if st.button("Execute Deep Harvester Routine", type="primary"):
    if video_url:
        with st.spinner("Processing deep loops..."):
            collected = deep_scrape_comments(video_url, depth_selection)
            
            if collected:
                df = pd.DataFrame(collected)
                st.dataframe(df)
                
                csv_data = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Export Captured Leads (.CSV)",
                    data=csv_data,
                    file_name="youtube_leads.csv",
                    mime="text/csv",
                )
            else:
                st.warning("Routine concluded. No explicit email matches identified within selected target range.")
    else:
        st.error("Please supply a valid YouTube web node identifier.")
