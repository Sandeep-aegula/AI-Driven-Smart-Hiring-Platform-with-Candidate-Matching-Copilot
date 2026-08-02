import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from frontend.components import api_client


def _render_employee_profile(emp):
    """Render the employee profile view with tabs."""
    st.markdown(f"""
    <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:16px;margin-bottom:15px;">
        <h4 style="margin:0;color:#0F172A;font-weight:800;">{emp.get('name')}</h4>
        <p style="margin:2px 0 0;font-size:0.8rem;color:#4F46E5;font-weight:600;">{emp.get('designation', 'Employee')}</p>
        <div style="font-size:0.75rem;color:#64748B;margin-top:6px;">
            Department: <strong>{emp.get('department', 'N/A')}</strong> | 
            Location: <strong>{emp.get('work_location', 'Remote')}</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

    t1, t2, t3, t4 = st.tabs(["Skills & Projects", "Performance", "AI Talent Insights", "Actions"])

    with t1:
        st.markdown("**Skills:**")
        skills = emp.get("skills", [])
        if skills:
            html = "<div style='display:flex;flex-wrap:wrap;gap:8px;margin-bottom:15px;'>"
            for sk in skills:
                name = sk.get("name")
                prog = sk.get("proficiency", 50)
                html += f"""
                <div style="background:#EEF2FF;border:1px solid #C7D2FE;color:#4338CA;
                            padding:4px 10px;border-radius:16px;font-size:0.75rem;font-weight:600;">
                    {name} <span style="opacity:0.6;font-size:0.7rem;">({prog}%)</span>
                </div>"""
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)
            
            # Skill Proficiency Radar Chart
            if len(skills) >= 3:
                st.markdown("<h5 style='text-align:center;'>Skill Proficiency Radar</h5>", unsafe_allow_html=True)
                skill_names = [sk.get("name", "") for sk in skills]
                skill_values = [sk.get("proficiency", 50) for sk in skills]
                
                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=skill_values,
                    theta=skill_names,
                    fill='toself',
                    name='Proficiency',
                    line=dict(color="#6366F1", width=2),
                    fillcolor='rgba(99, 102, 241, 0.2)'
                ))
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 100],
                            tickfont=dict(size=8)
                        ),
                        angularaxis=dict(
                            tickfont=dict(size=9)
                        )
                    ),
                    margin=dict(l=20, r=20, t=30, b=20),
                    height=300,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font={'color': "#0F172A", 'family': "Inter"},
                    showlegend=False
                )
                st.plotly_chart(fig_radar, width='stretch')
        else:
            st.info("No skills recorded.")

        st.markdown("**Assigned Projects:**")
        projects = emp.get("projects", [])
        if projects:
            for p in projects:
                # Handle both string and dict formats for backward compatibility
                if isinstance(p, dict):
                    name = p.get('name', 'Unnamed Project')
                    role = p.get('role', '')
                    client = p.get('client', 'Internal')
                    description = p.get('description', '')
                else:
                    name = str(p)
                    role = ''
                    client = 'Internal'
                    description = ''
                
                st.markdown(f"""
                <div style="background:#FFF;border:1px solid #E2E8F0;padding:12px;border-radius:8px;margin-bottom:10px;">
                    <div style="font-weight:700;font-size:0.9rem;">{name}</div>
                    <div style="font-size:0.8rem;color:#64748B;margin-top:4px;">
                        Role: {role} | Client: {client}
                    </div>
                    <div style="font-size:0.8rem;color:#475569;margin-top:6px;">{description}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No projects assigned.")

    with t2:
        # ============================================================
        # PERFORMANCE DASHBOARD - Premium HR Analytics
        # ============================================================
        
        # Generate realistic demo data for this employee (consistent per employee)
        import random
        import hashlib
        
        emp_seed = hash(str(emp.get("id", 1))) % 10000
        random.seed(emp_seed)
        
        # Core metrics
        perf_score = emp.get("performance_score", random.randint(75, 98))
        goal_completion = random.randint(75, 98)
        attendance = round(random.uniform(92.5, 99.8), 1)
        productivity = random.randint(78, 96)
        
        # Monthly performance data (12 months)
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        monthly_scores = [max(60, min(100, perf_score + random.randint(-8, 8))) for _ in range(12)]
        monthly_tasks = [random.randint(15, 35) for _ in range(12)]
        
        # KPI breakdown data
        kpi_categories = ["Communication", "Technical Skills", "Leadership", "Problem Solving", "Innovation", "Teamwork"]
        kpi_scores = [random.randint(70, 98) for _ in range(6)]
        
        # Goal completion data
        total_goals = random.randint(15, 25)
        completed_goals = random.randint(int(total_goals * 0.7), total_goals)
        remaining_goals = total_goals - completed_goals
        
        # Attendance breakdown
        present_days = random.randint(200, 230)
        remote_days = random.randint(30, 60)
        leave_days = random.randint(5, 15)
        late_days = random.randint(0, 5)
        total_work_days = present_days + remote_days + leave_days + late_days
        
        # Monthly task completion
        monthly_completed = [random.randint(12, 30) for _ in range(12)]
        
        # Skills radar data
        radar_categories = ["Leadership", "Technical Skills", "Ownership", "Communication", "Innovation", "Execution", "Teamwork"]
        radar_scores = [random.randint(65, 95) for _ in range(7)]
        
        # Quarterly ratings
        quarters = ["Q1", "Q2", "Q3", "Q4"]
        quarterly_ratings = [round(random.uniform(3.5, 4.8), 1) for _ in range(4)]
        
        # Productivity heatmap data (weeks x days)
        heatmap_data = [[random.randint(0, 10) for _ in range(5)] for _ in range(12)]
        
        # Performance timeline events
        timeline_events = [
            {"date": "2024-01-15", "type": "certification", "title": "AWS Solutions Architect Certified", "desc": "Achieved AWS Solutions Architect Associate certification"},
            {"date": "2024-03-22", "type": "promotion", "title": "Promoted to Senior Engineer", "desc": "Promoted from Software Engineer to Senior Software Engineer"},
            {"date": "2024-05-10", "type": "training", "title": "Leadership Training Completed", "desc": "Completed 40-hour Advanced Leadership Development Program"},
            {"date": "2024-07-18", "type": "project", "title": "Project Phoenix - Lead Architect", "desc": "Led architecture design for Project Phoenix serving 500K users"},
            {"date": "2024-09-05", "type": "review", "title": "Q3 Performance Review - Exceeds Expectations", "desc": "Received 4.7/5.0 rating with special recognition for innovation"},
            {"date": "2024-11-12", "type": "certification", "title": "Kubernetes Administrator (CKA)", "desc": "Passed Certified Kubernetes Administrator exam"},
        ]
        timeline_events.sort(key=lambda x: x["date"])
        
        # Department ranking (simulated)
        dept_rank = random.randint(1, 15)
        dept_total = random.randint(20, 50)
        
        # Promotion readiness
        promo_readiness = random.randint(65, 95)
        
        # Reset random seed
        random.seed()
        
        # ============================================================
        # SECTION 1 — Performance KPI Cards
        # ============================================================
        st.markdown("### Performance Overview")
        
        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
        
        # KPI Card 1 - Overall Performance Score
        with kpi_col1:
            delta = random.randint(-3, 5)
            trend_icon = "↑" if delta >= 0 else "↓"
            trend_color = "#10B981" if delta >= 0 else "#EF4444"
            sparkline_data = [max(60, min(100, perf_score + random.randint(-5, 5))) for _ in range(10)]
            
            fig_spark = go.Figure()
            fig_spark.add_trace(go.Scatter(
                y=sparkline_data, mode='lines', line=dict(color='#6366F1', width=2),
                fill='tozeroy', fillcolor='rgba(99, 102, 241, 0.1)'
            ))
            fig_spark.update_layout(
                height=40, margin=dict(l=0, r=0, t=0, b=0),
                xaxis=dict(visible=False), yaxis=dict(visible=False),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
            )
            
            st.markdown(f"""
            <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;padding:16px;">
                <div style="font-size:0.75rem;color:#64748B;font-weight:500;margin-bottom:4px;">Performance Score</div>
                <div style="font-size:1.75rem;font-weight:700;color:#0F172A;margin:4px 0;">{perf_score}%</div>
                <div style="font-size:0.7rem;color:{trend_color};font-weight:600;margin-top:4px;">
                    {trend_icon} {abs(delta)}% from last month
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.plotly_chart(fig_spark, config={'displayModeBar': False}, width='stretch')
        
        # KPI Card 2 - Goal Completion
        with kpi_col2:
            completed = random.randint(15, 22)
            total = random.randint(18, 25)
            pct = round(completed / total * 100)
            delta = random.randint(-2, 4)
            trend_icon = "↑" if delta >= 0 else "↓"
            trend_color = "#10B981" if delta >= 0 else "#EF4444"
            
            st.markdown(f"""
            <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;padding:16px;">
                <div style="font-size:0.75rem;color:#64748B;font-weight:500;margin-bottom:4px;">Goal Completion</div>
                <div style="font-size:1.75rem;font-weight:700;color:#0F172A;margin:4px 0;">{completed} / {total}</div>
                <div style="font-size:0.85rem;font-weight:600;color:#6366F1;margin:4px 0;">{pct}% Complete</div>
                <div style="font-size:0.7rem;color:{trend_color};font-weight:600;margin-top:4px;">
                    {trend_icon} {abs(delta)} from last month
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # KPI Card 3 - Attendance
        with kpi_col3:
            att = round(random.uniform(94.5, 99.5), 1)
            delta = round(random.uniform(-0.5, 0.8), 1)
            trend_icon = "↑" if delta >= 0 else "↓"
            trend_color = "#10B981" if delta >= 0 else "#EF4444"
            
            st.markdown(f"""
            <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;padding:16px;">
                <div style="font-size:0.75rem;color:#64748B;font-weight:500;margin-bottom:4px;">Attendance Rate</div>
                <div style="font-size:1.75rem;font-weight:700;color:#0F172A;margin:4px 0;">{att}%</div>
                <div style="font-size:0.7rem;color:{trend_color};font-weight:600;margin-top:4px;">
                    {trend_icon} {abs(delta)}% from last month
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # KPI Card 4 - Productivity
        with kpi_col4:
            prod = random.randint(80, 97)
            delta = random.randint(-3, 5)
            trend_icon = "↑" if delta >= 0 else "↓"
            trend_color = "#10B981" if delta >= 0 else "#EF4444"
            
            st.markdown(f"""
            <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;padding:16px;">
                <div style="font-size:0.75rem;color:#64748B;font-weight:500;margin-bottom:4px;">Productivity Score</div>
                <div style="font-size:1.75rem;font-weight:700;color:#0F172A;margin:4px 0;">{prod}%</div>
                <div style="font-size:0.7rem;color:{trend_color};font-weight:600;margin-top:4px;">
                    {trend_icon} {abs(delta)}% from last month
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # ============================================================
        # SECTION 2 — Performance Analytics (6 Charts)
        # ============================================================
        st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
        st.markdown("### Performance Analytics")
        
        # Row 1: Monthly Trend + KPI Breakdown
        chart_col1, chart_col2 = st.columns(2)
        
        # Chart 1: Monthly Performance Trend (Line Chart)
        with chart_col1:
            st.markdown("#### Monthly Performance Trend")
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=months, y=monthly_scores,
                mode='lines+markers', name='Performance Score',
                line=dict(color='#6366F1', width=3),
                marker=dict(size=8, color='#6366F1'),
                fill='tozeroy', fillcolor='rgba(99, 102, 241, 0.1)'
            ))
            fig_trend.add_hline(y=perf_score, line_dash="dash", line_color="#6366F1",
                               annotation_text=f"Current: {perf_score}", annotation_position="top right")
            fig_trend.update_layout(
                height=350, margin=dict(l=10,r=10,t=30,b=20),
                yaxis=dict(range=[50, 105], title="Score"),
                xaxis=dict(title="Month"),
                hovermode='x unified',
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font={'color': "#0F172A", 'family': "Inter"},
                showlegend=False
            )
            st.plotly_chart(fig_trend, width='stretch')
        
        # Chart 2: KPI Breakdown (Horizontal Bar Chart)
        with chart_col2:
            st.markdown("#### KPI Breakdown")
            fig_kpi = go.Figure()
            colors_kpi = ['#6366F1' if v >= 85 else '#F59E0B' if v >= 75 else '#EF4444' for v in kpi_scores]
            fig_kpi.add_trace(go.Bar(
                y=kpi_categories, x=kpi_scores,
                orientation='h', marker_color=colors_kpi,
                text=[f"{v}%" for v in kpi_scores], textposition='auto',
                hovertemplate='<b>%{y}</b><br>Score: %{x}%<extra></extra>'
            ))
            fig_kpi.update_layout(
                height=350, margin=dict(l=10,r=10,t=30,b=20),
                xaxis=dict(range=[0, 105], title="Score"),
                yaxis=dict(title="", autorange="reversed"),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font={'color': "#0F172A", 'family': "Inter"},
                showlegend=False
            )
            st.plotly_chart(fig_kpi, width='stretch')
        
        # Row 2: Goal Completion + Attendance
        chart_col3, chart_col4 = st.columns(2)
        
        # Chart 3: Goal Completion (Donut)
        with chart_col3:
            st.markdown("#### Goal Completion")
            fig_goals = go.Figure()
            fig_goals.add_trace(go.Pie(
                labels=['Completed', 'Remaining'],
                values=[completed_goals, remaining_goals],
                hole=0.65,
                marker_colors=['#10B981', '#E2E8F0'],
                textinfo='label+percent',
                textfont=dict(size=12, color='#0F172A'),
                hovertemplate='<b>%{label}</b><br>%{value} goals (%{percent})<extra></extra>'
            ))
            fig_goals.update_layout(
                height=300, margin=dict(l=10,r=10,t=30,b=10),
                annotations=[dict(text=f'{completed_goals}/{total_goals}', x=0.5, y=0.5, font_size=18, font_weight=700, showarrow=False)],
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font={'color': "#0F172A", 'family': "Inter"},
                showlegend=False
            )
            st.plotly_chart(fig_goals, width='stretch')
        
        # Chart 4: Attendance Analytics (Donut)
        with chart_col4:
            st.markdown("#### Attendance Analytics")
            fig_att = go.Figure()
            fig_att.add_trace(go.Pie(
                labels=['Present', 'Remote', 'Leave', 'Late'],
                values=[present_days, remote_days, leave_days, late_days],
                hole=0.65,
                marker_colors=['#10B981', '#6366F1', '#F59E0B', '#EF4444'],
                textinfo='label+percent',
                textfont=dict(size=11, color='#0F172A'),
                hovertemplate='<b>%{label}</b><br>%{value} days (%{percent})<extra></extra>'
            ))
            fig_att.update_layout(
                height=300, margin=dict(l=10,r=10,t=30,b=10),
                annotations=[dict(text=f'{total_work_days} days', x=0.5, y=0.5, font_size=16, font_weight=700, showarrow=False)],
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font={'color': "#0F172A", 'family': "Inter"},
                showlegend=False
            )
            st.plotly_chart(fig_att, width='stretch')
        
        # Row 3: Task Completion + Skills Radar
        chart_col5, chart_col6 = st.columns(2)
        
        # Chart 5: Monthly Task Completion (Area Chart)
        with chart_col5:
            st.markdown("#### Monthly Task Completion")
            fig_tasks = go.Figure()
            fig_tasks.add_trace(go.Scatter(
                x=months, y=monthly_completed,
                mode='lines+markers', name='Tasks Completed',
                line=dict(color='#10B981', width=3),
                marker=dict(size=8, color='#10B981'),
                fill='tozeroy', fillcolor='rgba(16, 185, 129, 0.1)'
            ))
            fig_tasks.update_layout(
                height=350, margin=dict(l=10,r=10,t=30,b=20),
                yaxis=dict(range=[0, max(monthly_completed)*1.2], title="Tasks"),
                xaxis=dict(title="Month"),
                hovermode='x unified',
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font={'color': "#0F172A", 'family': "Inter"},
                showlegend=False
            )
            st.plotly_chart(fig_tasks, width='stretch')
        
        # Chart 6: Skills Assessment (Radar Chart)
        with chart_col6:
            st.markdown("#### Skills Assessment")
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=radar_scores, theta=radar_categories,
                fill='toself', name='Current Level',
                line=dict(color='#6366F1', width=2),
                fillcolor='rgba(99, 102, 241, 0.2)'
            ))
            fig_radar.add_trace(go.Scatterpolar(
                r=[90]*7, theta=radar_categories,
                fill='toself', name='Target Level',
                line=dict(color='#10B981', width=2, dash='dash'),
                fillcolor='rgba(16, 185, 129, 0.1)'
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=8))),
                height=350, margin=dict(l=20,r=20,t=30,b=20),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font={'color': "#0F172A", 'family': "Inter"},
                showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.15, x=0.5)
            )
            st.plotly_chart(fig_radar, width='stretch')
        
        # ============================================================
        # SECTION 3 — Performance Summary
        # ============================================================
        st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
        st.markdown("### Performance Summary")
        
        sum_col1, sum_col2, sum_col3 = st.columns(3)
        
        with sum_col1:
            st.markdown(f"""
            <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:12px;padding:16px;">
                <div style="font-size:0.75rem;color:#166534;font-weight:600;margin-bottom:8px;">Strengths</div>
                <ul style="margin:0;padding-left:20px;color:#166534;font-size:0.85rem;line-height:1.8;">
                    <li>Consistently exceeds performance targets</li>
                    <li>Strong technical leadership and mentorship</li>
                    <li>Excellent cross-functional collaboration</li>
                    <li>Proactive problem identification and resolution</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with sum_col2:
            st.markdown(f"""
            <div style="background:#FEF3C7;border:1px solid #FDE68A;border-radius:12px;padding:16px;">
                <div style="font-size:0.75rem;color:#92400E;font-weight:600;margin-bottom:8px;">Areas for Improvement</div>
                <ul style="margin:0;padding-left:20px;color:#92400E;font-size:0.85rem;line-height:1.8;">
                    <li>Increase cross-functional visibility</li>
                    <li>Develop strategic planning capabilities</li>
                    <li>Expand external industry engagement</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with sum_col3:
            st.markdown(f"""
            <div style="background:#EEF2FF;border:1px solid #C7D2FE;border-radius:12px;padding:16px;">
                <div style="font-size:0.75rem;color:#4338CA;font-weight:600;margin-bottom:8px;">Current Rating & Readiness</div>
                <div style="font-size:1.5rem;font-weight:700;color:#4338CA;margin:4px 0;">{perf_score}/100</div>
                <div style="font-size:0.8rem;color:#4338CA;margin:4px 0;">Department Rank: #{dept_rank} of {dept_total}</div>
                <div style="font-size:0.8rem;color:#4338CA;margin:4px 0;">Promotion Readiness: {promo_readiness}%</div>
                <div style="font-size:0.8rem;color:#4338CA;margin:4px 0;">Next Review: Q1 2025</div>
            </div>
            """, unsafe_allow_html=True)
        
        # ============================================================
        # SECTION 4 — Performance Timeline
        # ============================================================
        st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
        st.markdown("### Performance Timeline")
        
        for event in timeline_events:
            type_colors = {
                "certification": ("#F0FDF4", "#22C55E", "fa-certificate"),
                "promotion": ("#FEF3C7", "#F59E0B", "fa-arrow-up"),
                "training": ("#EEF2FF", "#6366F1", "fa-graduation-cap"),
                "project": ("#F0FDF4", "#10B981", "fa-project-diagram"),
                "review": ("#FEF3C7", "#F59E0B", "fa-star"),
            }
            bg, color, icon = type_colors.get(event["type"], ("#F3F4F6", "#6B7280", "fa-circle"))
            
            st.markdown(f"""
            <div style="display:flex;gap:16px;padding:16px;background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;margin-bottom:12px;">
                <div style="width:44px;height:44px;border-radius:10px;background:{bg};display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                    <i class="fa-solid {icon}" style="color:{color};font-size:1.1rem;"></i>
                </div>
                <div style="flex:1;">
                    <div style="font-weight:700;color:#0F172A;font-size:0.95rem;">{event['title']}</div>
                    <div style="color:#64748B;font-size:0.85rem;margin-top:2px;">{event['desc']}</div>
                    <div style="color:#94A3B8;font-size:0.75rem;margin-top:4px;">{event['date']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # ============================================================
        # SECTION 5 — Additional Analytics (Quarterly + Heatmap)
        # ============================================================
        st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
        st.markdown("### Additional Analytics")
        
        add_col1, add_col2 = st.columns(2)
        
        # Quarterly Rating Trend
        with add_col1:
            st.markdown("#### Quarterly Rating Trend")
            fig_quarter = go.Figure()
            fig_quarter.add_trace(go.Scatter(
                x=quarters, y=quarterly_ratings,
                mode='lines+markers', name='Rating',
                line=dict(color='#6366F1', width=3),
                marker=dict(size=10, color='#6366F1'),
                fill='tozeroy', fillcolor='rgba(99, 102, 241, 0.1)'
            ))
            fig_quarter.add_hline(y=4.0, line_dash="dash", line_color="#10B981",
                                 annotation_text="Target: 4.0", annotation_position="bottom right")
            fig_quarter.update_layout(
                height=300, margin=dict(l=10,r=10,t=30,b=20),
                yaxis=dict(range=[3.0, 5.0], title="Rating"),
                xaxis=dict(title="Quarter"),
                hovermode='x unified',
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font={'color': "#0F172A", 'family': "Inter"},
                showlegend=False
            )
            st.plotly_chart(fig_quarter, width='stretch')
        
        # Productivity Heatmap
        with add_col2:
            st.markdown("#### Productivity Heatmap (12 Weeks × 5 Days)")
            fig_heat = go.Figure()
            fig_heat.add_trace(go.Heatmap(
                z=heatmap_data,
                x=['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
                y=[f'Week {i+1}' for i in range(12)],
                colorscale=[[0, '#FEE2E2'], [0.3, '#FEF3C7'], [0.6, '#D1FAE5'], [1, '#A7F3D0']],
                showscale=False,
                hovertemplate='Week %{y}<br>%{x}<br>Productivity: %{z}/10<extra></extra>'
            ))
            fig_heat.update_layout(
                height=300, margin=dict(l=10,r=10,t=30,b=20),
                xaxis=dict(title="", side="top"),
                yaxis=dict(title="", autorange="reversed"),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font={'color': "#0F172A", 'family': "Inter"}
            )
            st.plotly_chart(fig_heat, width='stretch')

    with t3:
        st.markdown("**AI-Driven Talent Insights**")
        st.write("Deep analysis of technical growth, leadership potential, and productivity.")
        
        insights = emp.get("talent_insights", {})
        if not insights:
            st.warning("No insights available. Click the button below to generate them.")
        elif "error" in insights:
            st.error(insights["error"])
        else:
            # Parse overall rating to stars (simple heuristic based on text or score)
            score = insights.get('overall_score', 0)
            rating_text = insights.get('overall_rating', 'Unknown')
            if score >= 90: stars = "★★★★★"
            elif score >= 80: stars = "★★★★☆"
            elif score >= 70: stars = "★★★☆☆"
            elif score >= 60: stars = "★★☆☆☆"
            else: stars = "★☆☆☆☆"
            
            st.markdown(f"""
            <div style="background:#F0FDF4;border:1px solid #BBF7D0;padding:12px;border-radius:8px;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <strong><span style="color:#22C55E;font-size:1.1rem;">{stars}</span> Overall Rating:</strong> {rating_text}
                    (Score: {score}/100)
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("##### Executive Summary")
            st.write(insights.get("executive_summary", "N/A"))
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("##### Technical Assessment")
                tech_data = insights.get("technical", "N/A")
                
                def _render_tech(data):
                    html_parts = []
                    for skill, info in data.items():
                        clean_skill = " ".join([word.capitalize() for word in str(skill).replace("_", " ").split()])
                        if isinstance(info, dict):
                            score = info.get("score", info.get("progress", "N/A"))
                        else:
                            score = info
                        html_parts.append(
                            f"• {clean_skill}<br>"
                            f"&nbsp;&nbsp;Score: {score}/100"
                        )
                    if html_parts:
                        st.markdown("<br><br>".join(html_parts), unsafe_allow_html=True)
                    else:
                        st.write(str(data))
                
                if isinstance(tech_data, dict):
                    _render_tech(tech_data)
                elif isinstance(tech_data, str):
                    try:
                        import json
                        parsed_tech = json.loads(tech_data)
                        if isinstance(parsed_tech, dict):
                            _render_tech(parsed_tech)
                        else:
                            st.write(tech_data)
                    except Exception:
                        st.write(tech_data)
                else:
                    st.write(tech_data)
            with col2:
                st.markdown("##### Leadership Assessment")
                lead_data = insights.get("leadership", "N/A")
                
                def _render_lead(data):
                    html_parts = []
                    for skill, info in data.items():
                        clean_skill = " ".join([word.capitalize() for word in str(skill).replace("_", " ").split()])
                        if isinstance(info, dict):
                            val = next(iter(info.values())) if info else "N/A"
                        else:
                            val = info
                        html_parts.append(
                            f"• {clean_skill}<br>"
                            f"&nbsp;&nbsp;{val}"
                        )
                    if html_parts:
                        st.markdown("<br><br>".join(html_parts), unsafe_allow_html=True)
                    else:
                        st.write(str(data))
                        
                if isinstance(lead_data, dict):
                    _render_lead(lead_data)
                elif isinstance(lead_data, str):
                    try:
                        import json
                        parsed_lead = json.loads(lead_data)
                        if isinstance(parsed_lead, dict):
                            _render_lead(parsed_lead)
                        else:
                            st.write(lead_data)
                    except Exception:
                        st.write(lead_data)
                else:
                    st.write(lead_data)
                
            st.markdown("---")
            
            cg = insights.get("career_growth", {})
            col_c1, col_c2, col_c3, col_c4 = st.columns(4)
            col_c1.metric("Promotion Readiness", cg.get("promotion_readiness", "Unknown"))
            col_c2.metric("Next Recommended Role", cg.get("next_role", "Unknown"))
            col_c3.metric("Future Potential", insights.get("future_potential", "Unknown"))
            col_c4.metric("Risk Level", insights.get("risk_level", "Unknown"))
            
            st.markdown("---")
            col_list1, col_list2, col_list3 = st.columns(3)
            with col_list1:
                st.markdown("##### Strengths")
                for s in insights.get("strengths", []):
                    st.markdown(f"- {s}")
            with col_list2:
                st.markdown("##### Improvement Areas")
                for i in insights.get("improvements", []):
                    st.markdown(f"- {i}")
            with col_list3:
                st.markdown("##### Recommended Training")
                for t in insights.get("recommended_training", []):
                    st.markdown(f"- {t}")
                    
            if "last_generated" in insights:
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(insights["last_generated"])
                    st.caption(f"Insights generated at: {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                except Exception:
                    pass

        if st.button("Refresh Insights", width='stretch', key=f"refresh_insights_{emp.get('id')}"):
            with st.spinner("Generating deep AI insights..."):
                res = api_client.generate_talent_insights(emp.get("id"))
                if res:
                    st.success("Insights updated successfully!")
                    st.rerun()

    with t4:
        st.markdown("**Management Actions**")
        # Basic stubs for actions
        act_col1, act_col2 = st.columns(2)
        with act_col1:
            if st.button("Assign Project", width='stretch', key=f"assign_project_{emp.get('id')}"):
                st.info("Stub: Open Project Assignment Modal")
        with act_col2:
            if st.button("Log Performance", width='stretch', key=f"log_performance_{emp.get('id')}"):
                st.info("Stub: Open Performance Logging Modal")
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Edit Employee Profile
        if st.button("✏️ Edit Profile", width='stretch', key=f"edit_profile_{emp.get('id')}"):
            st.session_state["edit_employee_id"] = emp.get("id")
            st.rerun()
        
        # Export stub
        if st.button("Download Employee Report (PDF)", width='stretch', key=f"download_report_{emp.get('id')}"):
            report = api_client.get_employee_performance_summary(emp.get("id")) # We'll replace with export API
            st.success(f"Report would be downloaded for {emp.get('name')}")


def _render_edit_employee_form(emp):
    """Render the edit form for employee profile."""
    st.markdown("### Edit Employee Profile")
    
    with st.form(f"edit_employee_{emp.get('id')}"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name", value=emp.get("name", ""))
            email = st.text_input("Email", value=emp.get("email", ""))
            phone = st.text_input("Phone", value=emp.get("phone", ""))
            department = st.selectbox("Department", 
                ["Engineering", "Analytics", "HR", "Sales", "Design", "Marketing", "Finance"],
                index=["Engineering", "Analytics", "HR", "Sales", "Design", "Marketing", "Finance"].index(emp.get("department", "Engineering")) if emp.get("department") in ["Engineering", "Analytics", "HR", "Sales", "Design", "Marketing", "Finance"] else 0)
            designation = st.text_input("Designation", value=emp.get("designation", ""))
        with col2:
            work_location = st.selectbox("Work Location", 
                ["Remote", "Hybrid", "On-site"],
                index=["Remote", "Hybrid", "On-site"].index(emp.get("work_location", "Remote")) if emp.get("work_location") in ["Remote", "Hybrid", "On-site"] else 0)
            joining_date = st.date_input("Joining Date", value=emp.get("joining_date", ""))
            status = st.selectbox("Status", 
                ["Active", "On Leave", "Ex-Employee"],
                index=["Active", "On Leave", "Ex-Employee"].index(emp.get("status", "Active")) if emp.get("status") in ["Active", "On Leave", "Ex-Employee"] else 0)
            reporting_manager = st.text_input("Reporting Manager", value=emp.get("reporting_manager", ""))
            current_project = st.text_input("Current Project", value=emp.get("current_project", ""))
        
        st.markdown("**Skills:**")
        skills = emp.get("skills", [])
        if skills:
            for i, skill in enumerate(skills):
                col_s1, col_s2, col_s3 = st.columns([3, 1, 1])
                with col_s1:
                    skill_name = st.text_input(f"Skill {i+1} Name", value=skill.get("name", ""), key=f"skill_name_{i}")
                with col_s2:
                    proficiency = st.number_input(f"Proficiency %", value=skill.get("proficiency", 50), min_value=0, max_value=100, key=f"skill_prof_{i}")
                with col_s3:
                    skill_status = st.selectbox(f"Status", ["Acquired", "Learning", "Planned"], 
                        index=["Acquired", "Learning", "Planned"].index(skill.get("status", "Acquired")) if skill.get("status") in ["Acquired", "Learning", "Planned"] else 0,
                        key=f"skill_status_{i}")
        
        st.markdown("**Projects:**")
        projects = emp.get("projects", [])
        if projects:
            for i, proj in enumerate(projects):
                if isinstance(proj, dict):
                    proj_name = st.text_input(f"Project {i+1} Name", value=proj.get("name", ""), key=f"proj_name_{i}")
                    proj_role = st.text_input(f"Role", value=proj.get("role", ""), key=f"proj_role_{i}")
                    proj_client = st.text_input(f"Client", value=proj.get("client", "Internal"), key=f"proj_client_{i}")
                    proj_desc = st.text_area(f"Description", value=proj.get("description", ""), key=f"proj_desc_{i}")
                else:
                    proj_name = st.text_input(f"Project {i+1} Name", value=str(proj), key=f"proj_name_{i}")
                    proj_role = st.text_input(f"Role", value="", key=f"proj_role_{i}")
                    proj_client = st.text_input(f"Client", value="Internal", key=f"proj_client_{i}")
                    proj_desc = st.text_area(f"Description", value="", key=f"proj_desc_{i}")
        
        col_save, col_cancel = st.columns(2)
        with col_save:
            if st.form_submit_button("Save Changes", type="primary", width='stretch'):
                # TODO: Implement save logic
                st.success("Profile updated successfully!")
                st.session_state.pop("edit_employee_id", None)
                st.rerun()
        with col_cancel:
            if st.form_submit_button("Cancel", width='stretch'):
                st.session_state.pop("edit_employee_id", None)
                st.rerun()


def render_employees() -> None:
    if "selected_employee_id" not in st.session_state:
        st.session_state["selected_employee_id"] = None

    st.markdown("""
    <h1 style="font-size:1.6rem;font-weight:800;color:#0F172A;margin:0 0 4px 0;">
        Employee Roster
    </h1>
    <p style="font-size:0.85rem;color:#64748B;margin:0 0 20px 0;font-weight:500;">
        Monitor employee progress, performance, and AI-driven talent insights.
    </p>
    <hr style="margin:0 0 20px 0;border:none;border-top:1px solid #F1F5F9;">
    """, unsafe_allow_html=True)

    cs, cd, cr = st.columns([3, 1.5, 1.5])
    with cs: search = st.text_input("Search", placeholder="Search by name, email...", label_visibility="collapsed")
    with cd: dept_f = st.selectbox("Department", ["Department", "Engineering", "Analytics", "HR", "Sales", "Design"], label_visibility="collapsed")
    with cr: stat_f = st.selectbox("Status", ["Status", "Active", "On Leave", "Ex-Employee"], label_visibility="collapsed")

    employees = api_client.get_employees()
    if employees:
        if search:
            like = search.lower()
            employees = [e for e in employees if like in e.get("name", "").lower() or like in e.get("email", "").lower()]
        if dept_f != "Department":
            employees = [e for e in employees if e.get("department") == dept_f]
        if stat_f != "Status":
            employees = [e for e in employees if e.get("status") == stat_f]

    # Main tabs: Team Members and Employee Profile (when selected)
    if st.session_state["selected_employee_id"]:
        tab_team, tab_profile = st.tabs(["Team Members", "Employee Profile"])
    else:
        tab_team = st.container()
        tab_profile = None

    with tab_team:
        st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 12px 0;'>"
                    "<i class='fa-solid fa-people-group' style='color:#6366F1;'></i> Team Members</h4>",
                    unsafe_allow_html=True)
        if not employees:
            st.markdown("<p style='text-align:center;color:#64748B;padding:30px 0;'>No employees found.</p>",
                        unsafe_allow_html=True)
        else:
            for emp in employees:
                ini = "".join(p[0] for p in emp.get("name","E").split()[:2]).upper()
                with st.container(border=True):
                    ec1, ec2 = st.columns([4, 1.2])
                    with ec1:
                        st.markdown(f"""
                        <div style="display:flex;gap:14px;align-items:center;">
                            <div style="width:42px;height:42px;border-radius:50%;background:#EEF2FF;
                                        border:1.5px solid #6366F1;display:flex;align-items:center;
                                        justify-content:center;font-weight:800;color:#6366F1;font-size:14px;">
                                {ini}</div>
                            <div>
                                <div style="font-weight:800;font-size:1rem;color:#0F172A;">{emp.get('name')}</div>
                                <div style="font-size:0.8rem;color:#4F46E5;font-weight:600;">
                                    {emp.get('designation', 'Employee')} | {emp.get('department', 'Unassigned')}</div>
                                <div style="font-size:0.72rem;color:#64748B;margin-top:2px;">
                                    <strong>Email:</strong> {emp.get('email', 'N/A')} • <strong>Phone:</strong> {emp.get('phone', 'N/A')}
                                </div>
                                <div style="font-size:0.72rem;color:#64748B;margin-top:2px;">
                                    <strong>Joined:</strong> {emp.get('joining_date', 'N/A')} • <strong>Status:</strong> {emp.get('status', 'Active')}
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with ec2:
                        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
                        if st.button("View Profile", key=f"vemp_{emp.get('id')}", width='stretch'):
                            st.session_state["selected_employee_id"] = emp.get("id")
                            st.rerun()
                st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

    # Employee Profile Tab
    if tab_profile and st.session_state["selected_employee_id"]:
        emp = api_client.get_employee(st.session_state["selected_employee_id"])
        if emp:
            with tab_profile:
                # Header with close button
                eh1, eh2 = st.columns([7, 3])
                with eh1:
                    st.markdown("<h3><i class='fa-solid fa-address-card' style='color:#6366F1;'></i> Employee Profile</h3>",
                                unsafe_allow_html=True)
                with eh2:
                    if st.button("← Back to Team", key="close_emp", width='stretch'):
                        st.session_state["selected_employee_id"] = None
                        st.session_state.pop("edit_employee_id", None)
                        st.rerun()

                # Edit mode
                if st.session_state.get("edit_employee_id") == emp.get("id"):
                    _render_edit_employee_form(emp)
                else:
                    _render_employee_profile(emp)
