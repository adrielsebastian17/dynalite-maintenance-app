import streamlit as st
import pandas as pd
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# -------------------------------------------------------------------------
# 1. PAGE SETUP & CONFIGURATION
# -------------------------------------------------------------------------
st.set_page_config(page_title="Engineer's Maintenance Portal", layout="wide")
st.title("⚡ Control Tech Asia: Engineer's Maintenance Portal")
st.write("Predictive scheduling and automated task routing for your 6-member engineering team.")

# -------------------------------------------------------------------------
# 2. APPLICATION STATE & SESSION DATA
# -------------------------------------------------------------------------
TEAM_MEMBERS = ["Alan", "Jaden", "Wei Seng", "Kenny", "Luthfi", "Adriel"]

# Initialize updated dataset with Site Temp and Maintenance Date
if "machinery_df" not in st.session_state:
    data = {
        "Maintanence": ["Google", "GIC", "Micron", "One George Street", "Supreme Court"],
        "Location / Zone": ["BLK 80 Level 30", "L49-L31", "Micron 10A Fab", "L16-12", "Auditorium"],
        "Site Temp (°C)": [20.5, 20.5, 25.0, 25.0, 21.8],  # Over 30°C requires urgent attention
        "Network Ping (ms)":[42.0, 68.5, 38.0, 71.2, 50.0],  # Over 65°C requires urgent attention      
        "Maint. Date": ["14/07/2026", "20/07/2026", "15/07/2026", "21/07/2026", "18/07/2026"], # DD/MM/YYYY
        "Assigned To": ["Alan,Luthfi", "Adriel", "Jaden", "Kenny", "Wei Seng"]
    }
    st.session_state.machinery_df = pd.DataFrame(data)

# -------------------------------------------------------------------------
# 3. SIDEBAR CONTROLS
# -------------------------------------------------------------------------
st.sidebar.header("👥 Team Overview")
st.sidebar.write(f"**Total Active Engineers:** {len(TEAM_MEMBERS)}")
selected_member = st.sidebar.selectbox("Filter Dashboard by Engineer:", ["Show All"] + TEAM_MEMBERS)

# -------------------------------------------------------------------------
# 4. MAIN DASHBOARD DISPLAY
# -------------------------------------------------------------------------
st.header("🏢 Philips Dynalite Asset Status")

# Visual helper updated for Site Temp threshold (> 30°C)
def highlight_anomalies(row):
    styles = [''] * len(row)
    if row["Site Temp (°C)"] > 30:
        styles = ['background-color: #ffcccc; color: #cc0000; font-weight: bold;'] * len(row)
    elif row["Network Ping (ms)"] > 100:
        styles = ['background-color: #fff3cd; color: #856404;'] * len(row)
    return styles

if selected_member != "Show All":
    display_df = st.session_state.machinery_df[st.session_state.machinery_df["Assigned To"] == selected_member]
else:
    display_df = st.session_state.machinery_df

if display_df.empty:
    st.info(f"No tasks currently assigned to {selected_member}.")
else:
    st.dataframe(display_df.style.apply(highlight_anomalies, axis=1), use_container_width=True)

# -------------------------------------------------------------------------
# 5. PREDICTIVE MAINTENANCE ENGINE (LOGIC)
# -------------------------------------------------------------------------
st.header("🤖 Smart Assignment Engine")
col1, col2 = st.columns(2)

with col1:
    run_engine = st.button("🚀 Run Assignment Model", type="primary")

if run_engine:
    df_copy = st.session_state.machinery_df.copy()
    logs = []
    
    current_workloads = {member: (df_copy["Assigned To"] == member).sum() for member in TEAM_MEMBERS}
    
    for index, row in df_copy.iterrows():
        if row["Assigned To"] == "Unassigned":
            # Rule updated: Flag if site temperature is strictly greater than 30°C
            if row["Site Temp (°C)"] > 30 or row["Network Ping (ms)"] > 100:
                next_available_member = min(current_workloads, key=current_workloads.get)
                
                df_copy.at[index, "Assigned To"] = next_available_member
                current_workloads[next_available_member] += 1
                
                logs.append(f"✅ **{row['Maintanence']}** ({row['Location / Zone']}) assigned to **{next_available_member}** due to climate/network anomalies.")
                
    st.session_state.machinery_df = df_copy
    
    with col2:
        if logs:
            st.success("Analysis Complete! New assignments routed:")
            for log in logs:
                st.write(log)
            st.rerun()
        else:
            st.info("System optimized. No critical unassigned anomalies found.")

# -------------------------------------------------------------------------
# 6. WEEKLY PDF REPORT GENERATOR
# -------------------------------------------------------------------------
st.header("📅 Export Weekly Documentation")

def build_pdf(dataframe):
    buffer = io.BytesIO()
    # Margins kept tight to accommodate the 6 expanded columns perfectly
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=36, bottomMargin=36)
    story = []
    
    base_styles = getSampleStyleSheet()
    title_style = ParagraphStyle('DocTitle', parent=base_styles['Title'], fontName='Helvetica-Bold', fontSize=22, leading=26, textColor=colors.HexColor("#1a365d"), alignment=0)
    body_style = ParagraphStyle('DocBody', parent=base_styles['Normal'], fontName='Helvetica', fontSize=9, leading=13)
    header_style = ParagraphStyle('TableHeader', parent=base_styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=colors.whitesmoke)
    
    story.append(Paragraph("Philips Dynalite Maintenance Summary", title_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Control Tech Asia — Automated Weekly Allocation Report", body_style))
    story.append(Spacer(1, 15))
    
    # Generate headers dynamically from our updated 6-column structure
    table_content = [[Paragraph(col, header_style) for col in dataframe.columns]]
    
    for _, row in dataframe.iterrows():
        row_cells = [
            Paragraph(str(row["Maintanence"]), body_style),
            Paragraph(str(row["Location / Zone"]), body_style),
            Paragraph(f"{row['Site Temp (°C)']} °C", body_style),
            Paragraph(f"{row['Network Ping (ms)']} ms", body_style),
            Paragraph(str(row["Maint. Date"]), body_style),
            Paragraph(str(row["Assigned To"]), body_style)
        ]
        table_content.append(row_cells)
    
    # Layout column widths across the standard printable PDF space
    pdf_table = Table(table_content, colWidths=[90, 100, 75, 85, 80, 90])
    pdf_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1a365d")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('TOPPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ('BOTTOMPADDING', (0,1), (-1,-1), 6),
        ('TOPPADDING', (0,1), (-1,-1), 6),
    ]))
    
    story.append(pdf_table)
    doc.build(story)
    buffer.seek(0)
    return buffer

pdf_data = build_pdf(st.session_state.machinery_df)

st.download_button(
    label="📥 Download Weekly PDF Report",
    data=pdf_data,
    file_name="Weekly_Dynalite_Maintenance_Report.pdf",
    mime="application/pdf",
    type="secondary"
)
