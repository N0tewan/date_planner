# app.py
# Run: pip install streamlit
# Then: streamlit run app.py

import streamlit as st
from pathlib import Path
from email.message import EmailMessage
import smtplib, ssl
from typing import Dict, Tuple, Optional

st.set_page_config(page_title="Date Planner", page_icon="💐", layout="wide")

# ---------- Files ----------
IMG_DIR = Path("images")

# Keep filenames as strings for safe session_state storage.
CATEGORIES = {
    "Flowers": [
        ("Roses", "flowers_roses.jpg"),
        ("Tulips", "flowers_tulips.jpg"),
        ("Sunflowers", "flowers_sunflowers.jpg"),
        ("Baby's Breath", "flowers_babysbreath.jpg"),
    ],
    "Activity": [
        ("Cinema", "activity_cinema.jpg"),
        ("Museum", "activity_museum.jpg"),
        ("Walk in Park", "activity_walk.jpg"),
        ("Arcade", "activity_arcade.jpg"),
        ("Cafe", "activity_cafe.jpg"),
        ("Cat Cafe", "activity_catcafe.jpg"),
    ],
    "Food (Vegetarian-friendly)": [
        ("Pizza", "food_pizza_veg.jpg"),
        ("Pasta", "food_pasta_veg.jpg"),
        ("Tapas (veg)", "food_tapas_veg.jpg"),
        ("Ramen (veg broth)", "food_ramen_veg.jpg"),
    ],
    "Vibe": [
        ("Cozy", "vibe_cozy.jpg"),
        ("Adventurous", "vibe_adventurous.jpg"),
        ("Romantic", "vibe_romantic.jpg"),
        ("Chill", "vibe_chill.jpg"),
    ],
}

LOCKED_DIET = "Vegetarian"
PAGES = ["Home"] + list(CATEGORIES.keys()) + ["Suggestions", "Summary"]

# ---------- Session defaults ----------
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "choices" not in st.session_state:
    st.session_state.choices: Dict[str, Tuple[str, str]] = {}  # {cat: (label, filename)}
if "temp_choice" not in st.session_state:
    st.session_state.temp_choice: Dict[str, Tuple[str, str]] = {}
if "extra_suggestions" not in st.session_state:
    st.session_state.extra_suggestions = ""
if "email_sent" not in st.session_state:
    st.session_state.email_sent = False

# ---------- Helpers ----------
def img_path(filename: str) -> Optional[Path]:
    return (IMG_DIR / filename) if filename else None

def show_missing_warning(filename: str):
    st.warning(f"Image not found: `{filename}` in `images/`. Check the name and extension.")

def card_button(label: str, filename: str, key: str) -> bool:
    """Small card with image and a button below."""
    fp = img_path(filename)
    if fp and fp.exists():
        st.image(str(fp), use_container_width=True)
    else:
        show_missing_warning(filename)
    return st.button(label, key=key)

def all_categories_submitted() -> bool:
    return all(cat in st.session_state.choices for cat in CATEGORIES.keys())

def category_page(cat: str):
    st.header(cat)
    options = CATEGORIES[cat]
    st.caption("Pick a card below, then press **Submit choice** to confirm. Or type your own under 'Custom'.")

    cols = st.columns(4)
    for i, (label, filename) in enumerate(options):
        with cols[i % 4]:
            if card_button(label, filename, key=f"btn_{cat}_{label}"):
                st.session_state.temp_choice[cat] = (label, filename)

    # Show current (not yet submitted)
    temp_val = st.session_state.temp_choice.get(cat)
    st.info(f"Selected (not submitted yet): **{temp_val[0]}**" if temp_val else "No selection yet.")

    # Custom option
    with st.expander("Custom (optional)"):
        custom_text = st.text_input(f"Custom {cat} label:", key=f"other_text_{cat}")
        custom_img = st.text_input("Optional image filename placed in images/ (e.g. myphoto.jpg):", key=f"other_img_{cat}")
        if custom_text.strip():
            st.session_state.temp_choice[cat] = (custom_text.strip(), custom_img.strip() or "")

    # Submit choice -> save + return Home (or Summary if everything is done)
    if st.button("Submit choice", type="primary", key=f"submit_{cat}"):
        chosen = st.session_state.temp_choice.get(cat)
        if chosen:
            st.session_state.choices[cat] = chosen
            st.success(f"{cat} saved as: **{chosen[0]}**")
            st.session_state.page = "Summary" if all_categories_submitted() else "Home"
            st.rerun()
        else:
            st.warning("Pick or type something before submitting.")

    # Show committed choice
    final_val = st.session_state.choices.get(cat)
    if final_val:
        st.write("Current saved choice:")
        colA, colB = st.columns([1,3])
        with colA:
            if final_val[1]:
                fp = img_path(final_val[1])
                if fp and fp.exists():
                    st.image(str(fp), use_container_width=True)
                else:
                    show_missing_warning(final_val[1])
        with colB:
            st.subheader(final_val[0])

def home_page():
    st.title("💐 Date Planner")
    st.write("Start anywhere. Make your picks, then view them on **Summary**.")
    st.divider()

    # If already complete, jump to Summary
    if all_categories_submitted():
        st.session_state.page = "Summary"
        st.rerun()

    cats = list(CATEGORIES.keys())
    rows = (len(cats) + 3) // 4
    idx = 0
    for _ in range(rows):
        cols = st.columns(4)
        for c in cols:
            if idx >= len(cats):
                continue
            cat = cats[idx]
            thumb_label, thumb_file = CATEGORIES[cat][0]  # first option as thumbnail
            with c:
                if card_button(cat, thumb_file, key=f"nav_{cat}"):
                    st.session_state.page = cat
                    st.rerun()
            idx += 1

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Suggestions"):
            st.session_state.page = "Suggestions"
            st.rerun()
    with c2:
        if st.button("Summary"):
            st.session_state.page = "Summary"
            st.rerun()

def suggestions_page():
    st.header("Suggestions")
    st.text_area("Anything else? (favourite places, flowers, music, allergies, notes)",
                 key="extra_suggestions", height=160)
    st.info("These notes will be included in the final summary.")

def build_text_summary() -> str:
    text_lines = ["Date Planner Picks", ""]
    for cat in CATEGORIES.keys():
        if cat in st.session_state.choices:
            label, _ = st.session_state.choices[cat]
            text_lines.append(f"{cat}: {label}")
        else:
            text_lines.append(f"{cat}: -")
    text_lines.append(f"Dietary needs: {LOCKED_DIET}")
    if st.session_state.extra_suggestions.strip():
        text_lines += ["", "Suggestions:", st.session_state.extra_suggestions.strip()]
    return "\n".join(text_lines) + "\n"

def summary_page():
    st.header("Your Picks")

    # Auto-warn if not done
    if not all_categories_submitted():
        st.warning("You have not finished all categories yet. You can still submit, but consider completing them first.")
    else:
        st.success("All categories completed! 🎉")

    # Show each saved choice as text + thumbnail
    for cat in CATEGORIES.keys():
        label, filename = st.session_state.choices.get(cat, ("-", ""))
        st.subheader(cat)
        colA, colB = st.columns([1,3])
        with colA:
            if filename:
                fp = img_path(filename)
                if fp and fp.exists():
                    st.image(str(fp), use_container_width=True)
                else:
                    show_missing_warning(filename)
        with colB:
            st.write(f"**{label}**")
        st.divider()

    st.write(f"Dietary needs: **{LOCKED_DIET}**")
    if st.session_state.extra_suggestions.strip():
        st.write("**Suggestions:**")
        st.write(st.session_state.extra_suggestions.strip())

    # Download text file
    text_blob = build_text_summary()
    st.download_button("Download your plan", data=text_blob, file_name="date_plan.txt")

    # ---- Final submit and feedback form ----
    st.markdown("### Submit & Feedback")
    with st.form("final_submit"):
        respondent_name = st.text_input("Your name (optional)")
        respondent_email = st.text_input("Your email (optional, if you want a copy)")
        feedback = st.text_area("What did you think of this planner?", height=120)
        send_copy = st.checkbox("Email a copy to me as well", value=True)
        submitted = st.form_submit_button("Submit and send")

    if submitted:
        # Compose email
        recipient = st.secrets.get("RECIPIENT_EMAIL", None)  # your email from secrets
        if not recipient:
            st.error("Email not sent: RECIPIENT_EMAIL is not set in secrets.")
            return

        subject = "New Date Planner submission"
        body = []
        if respondent_name:
            body.append(f"Name: {respondent_name}")
        if respondent_email:
            body.append(f"Email: {respondent_email}")
        body.append("")
        body.append("Selections:")
        for cat in CATEGORIES.keys():
            label, _ = st.session_state.choices.get(cat, ("-", ""))
            body.append(f"- {cat}: {label}")
        body.append(f"- Dietary needs: {LOCKED_DIET}")
        if st.session_state.extra_suggestions.strip():
            body += ["", "Additional Suggestions:", st.session_state.extra_suggestions.strip()]
        if feedback.strip():
            body += ["", "Feedback:", feedback.strip()]
        body_text = "\n".join(body)

        ok = send_email(subject, body_text, recipient)

        # Optionally send copy to respondent
        if respondent_email and send_copy:
            send_email("Your Date Planner submission (copy)", body_text, respondent_email)

        if ok:
            st.success("Thanks! Your response has been submitted and emailed.")
            st.session_state.email_sent = True
        else:
            st.error("Could not send email. Check your SMTP settings in secrets.")

    # Reset all
    if st.button("Reset everything"):
        st.session_state.choices = {}
        st.session_state.temp_choice = {}
        st.session_state.extra_suggestions = ""
        st.session_state.email_sent = False
        st.success("Cleared. Go back to Home to start again.")

def send_email(subject: str, body: str, to_email: str) -> bool:
    """
    Send email using SMTP settings from Streamlit secrets.
    Required secrets:
      SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_SENDER, RECIPIENT_EMAIL
    """
    try:
        smtp_host = st.secrets["SMTP_HOST"]
        smtp_port = int(st.secrets.get("SMTP_PORT", 465))
        smtp_user = st.secrets["SMTP_USERNAME"]
        smtp_pass = st.secrets["SMTP_PASSWORD"]
        sender    = st.secrets.get("SMTP_SENDER", smtp_user)

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = to_email
        msg.set_content(body)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"SMTP error: {e}")
        return False

# ---------- Sidebar Nav ----------
with st.sidebar:
    st.header("Menu")
    st.session_state.page = st.radio("Go to:", PAGES, index=PAGES.index(st.session_state.page))

# ---------- Router ----------
if st.session_state.page == "Home":
    home_page()
elif st.session_state.page == "Suggestions":
    suggestions_page()
elif st.session_state.page == "Summary":
    summary_page()
else:
    category_page(st.session_state.page)
