import streamlit as st
from frontend.services.cache import get_public_jobs



def _render_contact_page() -> None:
    CK = PUBLIC_CONTENT["contact"]
    st.markdown(
        f"""
        <section class="hp-hero" style="padding: 5rem 0 2rem;">
          <div class="hp-container">
            <div class="hp-contact-grid">
              <div class="hp-contact-info">
                <div class="hp-section-tag">{CK["tag"]}</div>
                <h2>{CK["title"]}</h2>
                <p>{CK["paragraph"]}</p>
                {''.join(
                  f'<div class="hp-contact-detail"><div class="icon"><i class="{d["icon"]}"></i></div><div><div style="font-size:0.75rem;color:#64748B;text-transform:uppercase;letter-spacing:0.08em;font-weight:700;">{d["title"]}</div><div style="color:#0F172A;font-weight:500;">{d["label"]}</div></div></div>'
                  for d in CK["details"]
                )}
              </div>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="hp-container" style="margin-top:-2rem;">', unsafe_allow_html=True)
    st.markdown('<div class="hp-contact-form">', unsafe_allow_html=True)
    with st.form("public_contact_full_form", clear_on_submit=True):
        cc1, cc2 = st.columns(2)
        with cc1:
            c_name = st.text_input("Full Name", key="contact_full_name")
        with cc2:
            c_email = st.text_input("Email Address", key="contact_full_email")
        st.text_input("Subject", key="contact_full_subject")
        c_msg = st.text_area("Message", height=150, key="contact_full_message")
        sent = st.form_submit_button("Send Message", type="primary", use_container_width=True)
        if sent:
            if c_name and c_email and c_msg:
                st.success("Thank you! Your message has been sent to the HirePilot team.")
            else:
                st.warning("Please fill in your name, email and message.")
    st.markdown('</div></div>', unsafe_allow_html=True)
    _render_public_footer()
