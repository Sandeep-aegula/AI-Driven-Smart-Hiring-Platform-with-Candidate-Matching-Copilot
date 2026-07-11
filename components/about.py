"""
components/about.py — HirePilot About Page
"""
import streamlit as st


def render_about() -> None:
    st.markdown("""
    <h1 style="font-size:1.6rem;font-weight:800;color:#0F172A;margin:0 0 4px 0;">
        ℹ️ About HirePilot
    </h1>
    <p style="font-size:0.85rem;color:#64748B;margin:0 0 20px 0;font-weight:500;">
        AI-powered recruitment & talent management platform
    </p>
    <hr style="margin:0 0 20px 0;border:none;border-top:1px solid #F1F5F9;">
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        with st.container(border=True):
            st.markdown("""
            <div style="text-align:center;padding:20px 0;">
                <div style="background:linear-gradient(135deg,#6366F1,#4F46E5);width:64px;height:64px;
                            border-radius:18px;display:flex;align-items:center;justify-content:center;
                            font-size:30px;font-weight:800;color:white;margin:0 auto 16px;
                            box-shadow:0 8px 20px rgba(99,102,241,0.35);">
                    <i class="fa-solid fa-paper-plane" style="transform:rotate(-10deg);"></i>
                </div>
                <h2 style="font-size:1.8rem;font-weight:800;color:#0F172A;margin:0 0 4px 0;">HirePilot</h2>
                <div style="font-size:0.75rem;color:#64748B;font-weight:600;text-transform:uppercase;
                            letter-spacing:0.08em;margin-bottom:12px;">AI Recruitment & Talent Management</div>
                <span style="background:#EEF2FF;color:#4F46E5;padding:4px 14px;border-radius:9999px;
                             font-size:0.8rem;font-weight:700;border:1px solid #E0E7FF;">
                    Version 1.0.0 • Enterprise SaaS</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 12px 0;'>"
                        "<i class='fa-solid fa-rocket' style='color:#6366F1;'></i> Tech Stack</h4>",
                        unsafe_allow_html=True)
            stack = [
                ("🐍 Python",       "#3776AB", "Core language"),
                ("⚡ FastAPI",      "#009688", "REST API backend"),
                ("🎈 Streamlit",    "#FF4B4B", "Frontend SPA"),
                ("🤖 Ollama",       "#F59E0B", "Local AI model runtime"),
                ("🦙 qwen2.5-coder","#10B981", "AI model (7B)"),
                ("🗄️ JSON DB",      "#6366F1", "Local data storage"),
            ]
            for icon_name, color, desc in stack:
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;padding:8px 0;
                            border-bottom:1px solid #F1F5F9;">
                    <span style="background:{color}15;color:{color};width:32px;height:32px;
                                 border-radius:8px;display:flex;align-items:center;
                                 justify-content:center;font-size:15px;flex-shrink:0;">{icon_name.split()[0]}</span>
                    <div>
                        <div style="font-weight:700;color:#0F172A;font-size:0.85rem;">{" ".join(icon_name.split()[1:])}</div>
                        <div style="font-size:0.72rem;color:#64748B;">{desc}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with c2:
        with st.container(border=True):
            st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 12px 0;'>"
                        "<i class='fa-solid fa-star' style='color:#F59E0B;'></i> Key Features</h4>",
                        unsafe_allow_html=True)
            features = [
                ("🏠","Dashboard","Live KPIs, charts, pipeline funnel, quick actions."),
                ("💼","Job Management","CRUD operations, AI JD generator, pipeline tracking."),
                ("👥","Candidate Profiles","Resume parsing, AI match scoring, status workflow."),
                ("📄","Resume Parser","Bulk upload, Ollama AI extraction, profile linking."),
                ("🤖","AI Screening","Radar match, gap analysis, automated recommendation."),
                ("📅","Interview Mgmt","Scheduling, AI question generation, feedback logging."),
                ("👨‍💼","Employee Roster","Performance tracking, skill bars, promotion timeline."),
                ("📊","Analytics","Pipeline funnel, hiring trends, recruiter metrics."),
                ("📑","Reports","One-click PDF/CSV/Excel export, historical log."),
                ("🤖","AI Copilot","Local Ollama chat, quick prompts, streaming responses."),
            ]
            for icon, name, desc in features:
                st.markdown(f"""
                <div style="display:flex;gap:10px;padding:8px 0;border-bottom:1px solid #F1F5F9;">
                    <div style="background:#EEF2FF;color:#6366F1;width:32px;height:32px;border-radius:8px;
                                display:flex;align-items:center;justify-content:center;font-size:14px;
                                flex-shrink:0;">{icon}</div>
                    <div>
                        <div style="font-weight:700;color:#0F172A;font-size:0.85rem;">{name}</div>
                        <div style="font-size:0.72rem;color:#64748B;">{desc}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 12px 0;'>"
                        "<i class='fa-solid fa-terminal' style='color:#6366F1;'></i> Run Instructions</h4>",
                        unsafe_allow_html=True)
            st.code("""# From project root
# 1. Start backend
uvicorn backend.main:app --reload --port 8000

# 2. Start Ollama (optional)
ollama serve
ollama run qwen2.5-coder:7b

# 3. Launch HirePilot SPA
streamlit run app.py""", language="bash")
