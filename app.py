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
st.set_page_config(page_title="Dynalite Maintenance Portal", layout="wide")
st.title("⚡ Control Tech Asia: Dynalite Maintenance Portal")
st.write("Predictive scheduling and automated task routing for your 6-member engineering team.")

# -------------------------------------------------------------------------
# 2. APPLICATION STATE & SESSION DATA
# -------------------------------------------------------------------------
# Define our fixed 7-member team
TEAM_MEMBERS = ["Alan", "Jaden", "Wei Seng", "Kenny", "Luthfi", "Adriel"]

# Initialize a mock dataset of Philips Dynalite machinery if not already loaded
if "machinery_df" not in st.session_state:
    data = {
        "Maintanence": ["GIC", "Google", "UBS", "Dulwich", "One George Street"],
        "Location / Zone": ["L49,47,43,42,40,34,32,31", "BLK X LY", "XXX", "XXX", "XXX"],
        "Site Temp (°C)": [20.0, 20.0, 20.0, 27.0, 25.0],  # Over 65°C requires urgent attention
        "Network Ping (ms)": [15, 142, 12, 185, 25],       # Fixed values: High ping (>100) indicates network strain
        "Assigned To": ["Adriel", "Jaden,Kenny", "Jaden", "Wei Seng", "Adriel"]
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

# Visual helper to highlight critical temperature or network risks in the table
def highlight_anomalies(row):
    styles = [''] * len(row)
    if row["Relay Temp (°C)"] > 65:
        styles = ['background-color: #ffcccc; color: #cc0000; font-weight: bold;'] * len(row)
    elif row["Network Ping (ms)"] > 100:
        styles = ['background-color: #fff3cd; color: #856404;'] * len(row)
    return styles

# Filter dataframe based on sidebar selection
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
col1, col2 = st.columns(2)  # <-- Fixed: Added the number 2 here

with col1:
    run_engine = st.button("🚀 Run Assignment Model", type="primary")


if run_engine:
    df_copy = st.session_state.machinery_df.copy()
    logs = []
    
    # Workload counter to distribute jobs fairly among unassigned members
    current_workloads = {member: (df_copy["Assigned To"] == member).sum() for member in TEAM_MEMBERS}
    
    for index, row in df_copy.iterrows():
        # Condition: If the machinery is unassigned AND exhibits critical conditions
        if row["Assigned To"] == "Unassigned":
            if row["Relay Temp (°C)"] > 65 or row["Network Ping (ms)"] > 100:
                # Find the team member who currently has the fewest tasks
                next_available_member = min(current_workloads, key=current_workloads.get)
                
                # Assign the task
                df_copy.at[index, "Assigned To"] = next_available_member
                current_workloads[next_available_member] += 1
                
                logs.append(f"✅ **{row['Maintanence']}** ({row['Location / Zone']}) assigned to **{next_available_member}** due to operational anomalies.")
                
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
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    # Typography configuration
    base_styles = getSampleStyleSheet()
    title_style = ParagraphStyle('DocTitle', parent=base_styles['Title'], fontName='Helvetica-Bold', fontSize=24, leading=28, textColor=colors.HexColor("#1a365d"), alignment=0)
    body_style = ParagraphStyle('DocBody', parent=base_styles['Normal'], fontName='Helvetica', fontSize=10, leading=14)
    header_style = ParagraphStyle('TableHeader', parent=base_styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=12, textColor=colors.whitesmoke)
    
    # Document Header Elements
    story.append(Paragraph("Philips Dynalite Maintenance Summary", title_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Control Tech Asia — Automated Weekly Allocation Report", body_style))
    story.append(Spacer(1, 15))
    
    # Format Table Data dynamically from our current UI DataFrame
    table_content = [[Paragraph(col, header_style) for col in dataframe.columns]]
    
    for _, row in dataframe.iterrows():
        row_cells = [
            Paragraph(str(row["Maintanence"]), body_style),
            Paragraph(str(row["Location / Zone"]), body_style),
            Paragraph(f"{row['Relay Temp (°C)']} °C", body_style),
            Paragraph(f"{row['Network Ping (ms)']} ms", body_style),
            Paragraph(str(row["Assigned To"]), body_style)
        ]
        table_content.append(row_cells)
    
    # PDF Table Styling layout
    pdf_table = Table(table_content, colWidths=[110, 110, 95, 105, 120])
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

# Generate binary stream data for download trigger
pdf_data = build_pdf(st.session_state.machinery_df)

st.download_button(
    label="📥 Download Weekly PDF Report",
    data=pdf_data,
    file_name="Weekly_Dynalite_Maintenance_Report.pdf",
    mime="application/pdf",
    type="secondary"
)
