import streamlit as st

def render_kpis():
    """Renders Section 2: Dashboard Overview KPI Cards."""
    # st.markdown("<!-- SECTION 2: DASHBOARD OVERVIEW -->", unsafe_allow_html=True)

    # Compute dynamic states based on current session lists
    cands = st.session_state.candidates_list
    total_cands = 1248 + (len(cands) - 5)
    shortlisted_cands = 412 + sum(1 for c in cands if c["status"] == "Shortlisted")
    interviews_cands = 85 + sum(1 for c in cands if c["status"] == "Interview Scheduled")
    offers_cands = 34 + sum(1 for c in cands if c["status"] == "Offer Released")
    rejected_cands = 195 + sum(1 for c in cands if c["status"] == "Rejected")

    kpi_cols = st.columns(5)

    # Total Candidates Card
    with kpi_cols[0]:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #2563EB;">
            <div class="kpi-icon-wrapper" style="color: #2563EB; background-color: #EFF6FF;"><i class="fa-solid fa-user-group"></i></div>
            <div class="kpi-title">Total Candidates</div>
            <div class="kpi-value">{total_cands:,}</div>
            <div class="kpi-growth growth-up">
                <span>↑ 12%</span> <span style="color: #94A3B8; font-weight: 500;">this month</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Shortlisted Card
    with kpi_cols[1]:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #10B981;">
            <div class="kpi-icon-wrapper" style="color: #10B981; background-color: #ECFDF5;"><i class="fa-solid fa-star"></i></div>
            <div class="kpi-title">Shortlisted</div>
            <div class="kpi-value">{shortlisted_cands}</div>
            <div class="kpi-growth growth-up">
                <span>↑ 8%</span> <span style="color: #94A3B8; font-weight: 500;">this month</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Interviews Scheduled Card
    with kpi_cols[2]:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #F59E0B;">
            <div class="kpi-icon-wrapper" style="color: #F59E0B; background-color: #FEF3C7;"><i class="fa-solid fa-calendar-days"></i></div>
            <div class="kpi-title">Interviews Scheduled</div>
            <div class="kpi-value">{interviews_cands}</div>
            <div class="kpi-growth growth-up">
                <span>↑ 15%</span> <span style="color: #94A3B8; font-weight: 500;">this week</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Offers Released Card
    with kpi_cols[3]:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #8B5CF6;">
            <div class="kpi-icon-wrapper" style="color: #8B5CF6; background-color: #F5F3FF;"><i class="fa-solid fa-briefcase"></i></div>
            <div class="kpi-title">Offers Released</div>
            <div class="kpi-value">{offers_cands}</div>
            <div class="kpi-growth growth-up">
                <span>↑ 5%</span> <span style="color: #94A3B8; font-weight: 500;">this month</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Rejected Candidates Card
    with kpi_cols[4]:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #EF4444;">
            <div class="kpi-icon-wrapper" style="color: #EF4444; background-color: #FEE2E2;"><i class="fa-solid fa-circle-xmark"></i></div>
            <div class="kpi-title">Rejected Candidates</div>
            <div class="kpi-value">{rejected_cands}</div>
            <div class="kpi-growth growth-down">
                <span>↓ 2%</span> <span style="color: #94A3B8; font-weight: 500;">this month</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
