# app.py — Tinder-style Date Planner WITH email submit
# Local run: pip install streamlit
# Cloud run: add EMAIL_USER/EMAIL_PASS in Streamlit Secrets (see notes below)
# Then: streamlit run app.py

import streamlit as st
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from email.message import EmailMessage
import smtplib, ssl

st.set_page_config(page_title="Date Planner (Swipe)", page_icon="💘", layout="wide")

# ---------- Paths ----------
IMG_DIR = Path("images")  # Put your images here

# ---------- Data ----------
FLOWERS: List[Tuple[str, str]] = [
    ("Roses", "flowers_roses.jpg"),
    ("Tulips", "flowers_tulips.jpg"),
    ("Sunflowers", "flowers_sunflowers.jpg"),
    ("Baby's Breath", "flowers_babysbreath.jpg"),
    ("Orchids", "flowers_orchids.jpg"),
    ("Daisies", "flowers_daisies.jpg"),
    ("Peonies", "flowers_peonies.jpg"),
]

ACTIVITIES: List[Tuple[str, str]] = [
    ("Park Picnic", "activity_picnic.jpg"),
    ("Museum", "activity_museum.jpg"),
    ("Arcade", "activity_arcade.jpg"),
    ("Cinema", "activity_cinema.jpg"),
    ("Bowling", "activity_bowling.jpg"),
    ("Kayaking", "activity_kayaking.jpg"),
    ("Mini Golf", "activity_minigolf.jpg"),
    ("Crafting Workshop", "activity_crafting.jpg"),
    ("Wine Tasting", "activity_winetasting.jpg"),
    ("Pub Crawl", "activity_pubcrawl.jpg"),
    ("Cat Cafe", "activity_catcafe.jpg"),
    ("Cafe", "activity_cafe.jpg"),
]

FOOD: List[Tuple[str, str]] = [
    ("Pizza", "food_pizza_veg.jpg"),
    ("Pasta", "food_pasta_veg.jpg"),
    ("Tapas (veg)", "food_tapas_veg.jpg"),
    ("Ramen (veg broth)", "food_ramen_veg.jpg"),
    ("Sushi (veg options)", "food_sushi_veg.jpg"),
    ("Burgers (veg)", "food_burgers_veg.jpg"),
    ("Vegan Curry", "food_curry_veg.jpg"),
    ("Ice Cream Parlour", "food_icecream.jpg"),
    ("Desserts", "food_desserts.jpg"),
]

CATEGORIES: Dict[str, List[Tuple[str, str]]] = {
    "Flowers": FLOWERS,
    "Activities": ACTIVITIES,
    "Food": FOOD,
}
ORDER = list(CATEGORIES.keys())

# ---------- Session ----------
def ensure_state():
    ss = st.session_state
    if "page" not in ss:
        ss.page = "Home"
    if "idx" not in ss:
        ss.idx = {cat: 0 for cat in ORDER}
    if "likes" not in ss:
        ss.likes = {cat: [] for cat in ORDER}   # [(label, filename), ...]
    if "passes" not in ss:
        ss.passes = {cat: [] for cat in ORDER}
    if "done" not in ss:
        ss.done = {cat: False for cat in ORDER}
    if "suggestions" not in ss:
        ss.suggestions = ""
    if "email_sent" not in ss:
        ss.email_sent = False

ensure_state()

# ---------- Helpers ----------
def img_path(filename: str) -> Optional[Path]:
    return (IMG_DIR / filename) if filename else None

def show_missing_warning(filename: str):
    st.warning(f"Image not found: `{filename}` in `images/`. Check the name & extension.")

def all_done() -> bool:
    return all(st.session_state.done.values())

def reset_category(cat: str):
    st.session_state.idx[cat] = 0
    st.session_state.likes[cat] = []
    st.session_state.passes[cat] = []
    st.session_state.done[cat] = False

def reset_all():
    for cat in ORDER:
        reset_category(cat)
    st.session_state.suggestions = ""
    st.session_state.email_sent = False
    st.session_state.page = "Home"

def category_progress(cat: str) -> str:
    total = len(CATEGORIES[cat])
    i = st.session_state.idx[cat]
    return f"{min(i+1, total)}/{total}" if not st.session_state.done[cat] else f"{total}/{total}"

def build_text_summary() -> str:
    lines = ["Date Planner Picks", ""]
    for cat in ORDER:
        liked_labels = [lbl for (lbl, _) in st.session_state.likes[cat]]
        lines.append(f"{cat}: " + (", ".join(liked_labels) if liked_labels else "-"))
    if st.session_state.suggestions.strip():
        lines += ["", "Notes:", st.session_state.suggestions.strip()]
    return "\n".join(lines) + "\n"

# ---------- Email ----------
def send_email_to_ewan(subject: str, body: str) -> bool:
    """
    Sends an email to ewanroberts200413@gmail.com using Gmail SMTP.
    Requires Streamlit Secrets:
      EMAIL_USER="your_gmail_address"
      EMAIL_PASS="your_gmail_app_password"
    """
    try:
        sender = st.secrets["EMAIL_USER"]
        password = st.secrets["EMAIL_PASS"]
        recipient = "ewanroberts200413@gmail.com"

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient
        msg.set_content(body)

        # Try SSL (465), then fallback to STARTTLS (587)
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                server.login(sender, password)
                server.send_message(msg)
            return True
        except Exception:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.ehlo()
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
                server.login(sender, password)
                server.send_message(msg)
            return True
    except Exception as e:
        st.error(f"Email error: {e}")
        return False

# ---------- Pages ----------
def home_page():
    st.title("💘 Date Planner — Swipe Style")
    st.write("Choose a category. Swipe by clicking **❤️ Like** or **❌ Pass**. Do them in any order. "
             "When all are done, you’ll be taken to **Summary** automatically.")
    st.divider()

    cols = st.columns(3)
    for i, cat in enumerate(ORDER):
        with cols[i % 3]:
            st.subheader(cat)
            items = CATEGORIES[cat]
            if items:
                _, thumb_file = items[0]
                fp = img_path(thumb_file)
                if fp and fp.exists():
                    st.image(str(fp), use_container_width=True)
                else:
                    show_missing_warning(thumb_file)
            st.caption(f"Progress: {category_progress(cat)}")
            if st.button(f"Open {cat}", key=f"open_{cat}"):
                st.session_state.page = cat
                st.rerun()

    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Summary"):
            st.session_state.page = "Summary"
            st.rerun()
    with c2:
        if st.button("Add notes / suggestions"):
            st.session_state.page = "Suggestions"
            st.rerun()
    with c3:
        if st.button("Reset everything"):
            reset_all()
            st.rerun()

def swipe_page(cat: str):
    st.header(f"{cat}  •  {category_progress(cat)}")
    items = CATEGORIES[cat]
    i = st.session_state.idx[cat]

    if i >= len(items):
        st.session_state.done[cat] = True
        st.success(f"{cat} completed!")
        st.session_state.page = "Summary" if all_done() else "Home"
        st.rerun()

    label, filename = items[i]
    fp = img_path(filename)

    colA, colB = st.columns([2, 1])
    with colA:
        if fp and fp.exists():
            st.image(str(fp), use_container_width=True)
        else:
            show_missing_warning(filename)
    with colB:
        st.subheader(label)
        st.write("Swipe:")
        like = st.button("❤️ Like", use_container_width=True, key=f"like_{cat}_{i}")
        skip = st.button("❌ Pass", use_container_width=True, key=f"pass_{cat}_{i}")

        if like or skip:
            if like:
                st.session_state.likes[cat].append((label, filename))
            else:
                st.session_state.passes[cat].append((label, filename))
            st.session_state.idx[cat] += 1
            st.rerun()

    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("⬅️ Back to Home", key=f"backhome_{cat}"):
            st.session_state.page = "Home"
            st.rerun()
    with c2:
        if st.button("↻ Restart this category", key=f"restart_{cat}"):
            reset_category(cat)
            st.rerun()
    with c3:
        if st.button("⏭️ Skip to Summary", key=f"skip_{cat}"):
            st.session_state.page = "Summary"
            st.rerun()

def suggestions_page():
    st.header("Notes / Suggestions")
    st.text_area("Anything else you want to add? (favourite places, allergies, music, etc.)",
                 key="suggestions", height=160)
    st.info("These notes will appear on the Summary page.")
    if st.button("Back to Home"):
        st.session_state.page = "Home"
        st.rerun()

def summary_page():
    st.title("💘 Your Picks — Summary")
    if all_done():
        st.success("All categories completed. Nice picks!")

    for cat in ORDER:
        st.subheader(cat)
        likes = st.session_state.likes[cat]
        if not likes:
            st.caption("_No likes in this category yet._")
        else:
            cols = st.columns(3)
            for i, (label, filename) in enumerate(likes):
                with cols[i % 3]:
                    fp = img_path(filename)
                    if fp and fp.exists():
                        st.image(str(fp), use_container_width=True)
                    else:
                        show_missing_warning(filename)
                    st.write(f"**{label}**")
        st.divider()

    # Notes
    if st.session_state.suggestions.strip():
        st.subheader("Notes / Suggestions")
        st.write(st.session_state.suggestions.strip())

    # Download text summary
    text_blob = build_text_summary()
    st.download_button("Download your picks", data=text_blob, file_name="date_plan.txt")

    # --- Submit & Email to Ewan ---
    st.markdown("### Submit your picks")
    name = st.text_input("Your name (optional)")
    feedback = st.text_area("What did you think of this planner?", height=100)
    if st.button("Submit and email to Ewan"):
        body = []
        if name.strip():
            body.append(f"Name: {name.strip()}")
        if feedback.strip():
            body += ["Feedback:", feedback.strip(), ""]
        body.append("Selections:")
        for cat in ORDER:
            liked_labels = [lbl for (lbl, _) in st.session_state.likes[cat]]
            body.append(f"- {cat}: " + (", ".join(liked_labels) if liked_labels else "-"))
        if st.session_state.suggestions.strip():
            body += ["", "Notes:", st.session_state.suggestions.strip()]
        ok = send_email_to_ewan("Date Planner submission", "\n".join(body))
        if ok:
            st.success("Submitted! Your picks were emailed to Ewan.")
            st.session_state.email_sent = True
        else:
            st.error("Couldn’t send email. Check secrets on Streamlit Cloud.")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Back to Home"):
            st.session_state.page = "Home"
            st.rerun()
    with c2:
        if st.button("Reset everything"):
            reset_all()
            st.rerun()

# ---------- Sidebar (status + quick nav) ----------
with st.sidebar:
    st.header("Status")
    for cat in ORDER:
        done_mark = "✅" if st.session_state.done[cat] else "⏳"
        st.write(f"{done_mark} {cat}: {category_progress(cat)}")
    st.divider()
    pages = ["Home", *ORDER, "Suggestions", "Summary"]
    current_idx = pages.index(st.session_state.page) if st.session_state.page in pages else 0
    nav_choice = st.radio("Go to:", pages, index=current_idx, key="nav_radio")
    if nav_choice != st.session_state.page:
        st.session_state.page = nav_choice
        st.rerun()

# ---------- Router ----------
if st.session_state.page == "Home":
    home_page()
elif st.session_state.page == "Suggestions":
    suggestions_page()
elif st.session_state.page == "Summary":
    summary_page()
elif st.session_state.page in ORDER:
    swipe_page(st.session_state.page)
else:
    st.session_state.page = "Home"
    st.rerun()
