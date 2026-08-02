def render_about_page(C):
    """Render the About Us page content."""
    A = C["about"]
    st.markdown(
        f"""
        <section class="hp-section" id="about">
          <div class="hp-container">
            <div class="hp-about-grid">
              <div class="hp-about-content">
                <div class="hp-section-tag">{A["tag"]}</div>
                <h2>{A["title"]}</h2>
                {''.join(f'<p>{p}</p>' for p in A["paragraphs"])}
                <ul class="hp-split-list">
                  {''.join(f'<li>{pt}</li>' for pt in A["points"])}
                </ul>
              </div>
              <div class="hp-about-image">
                <div style="font-size: 5rem;">{A["visual_emoji"]}</div>
              </div>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )