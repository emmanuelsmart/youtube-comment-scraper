import streamlit as st
import requests
import re
import pandas as pd

EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

def get_youtube_comments_api(video_url):
    # Extracts the 11-character video ID from the URL
    video_id_match = re.search(r'(?:v=|\/)([a-zA-Z0-9_-]{11})', video_url)
    if not video_id_match:
        st.error("Invalid YouTube URL structure.")
        return []
    
    video_id = video_id_match.group(1)
    emails_found = []
    
    # We use a public, free, open-source YouTube operational mirror to fetch text
    # This avoids heavy headless browsers and blocks on a free server
    api_url = f"https://lemnoslife.com{video_id}&maxResults=100"
    
    try:
        response = requests.get(api_url).json()
        if 'items' in response:
            for item in response['items']:
                comment_text = item['snippet']['topLevelComment']['snippet']['textDisplay']
                author = item['snippet']['topLevelComment']['snippet']['authorDisplayName']
                
                # Regex matching
                found_emails = re.findall(EMAIL_REGEX, comment_text)
                for email in found_emails:
                    if email not in [e['Email'] for e in emails_found]:
                        emails_found.append({
                            "Username": author,
                            "Email": email,
                            "Comment": comment_text[:100] + "..."
                        })
        return emails_found
    except Exception as e:
        st.error(f"Error parsing comments: {str(e)}")
        return []

# Layout UI
st.set_page_config(page_title="Free YT Scraper", layout="centered")
st.title("📹 Free YouTube Comment Scraper")
st.caption("Running free on the cloud without a VPS")

url_input = st.text_input("Paste YouTube Video Link:")

if st.button("Extract Emails", type="primary"):
    if url_input:
        with st.spinner("Scanning data loops..."):
            scraped_data = get_youtube_comments_api(url_input)
            
            if scraped_data:
                df = pd.DataFrame(scraped_data)
                st.dataframe(df)
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download CSV to iPhone",
                    data=csv,
                    file_name="youtube_emails.csv",
                    mime="text/csv",
                )
            else:
                st.info("Scan finished. No plain-text emails were found in the recent comments.")
    else:
        st.warning("Please provide a valid link first.")
