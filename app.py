import streamlit as st
import fitz  # PyMuPDF
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.colors import black, lightgrey, grey
import io

def generate_grid_pdf(uploaded_files, dpi_scale, left_margin_val, row_gap_val):
    # --- Configuration ---
    # Card Size
    CARD_WIDTH = 5.5 * cm
    CARD_HEIGHT = 8.5 * cm
    
    # Gap settings
    COL_GAP = 0.0 * cm  # Horizontal gap 0 hi rahega
    ROW_GAP = row_gap_val * cm # Vertical gap user decide karega
    
    # --- LANDSCAPE LAYOUT: 5x2 (Total 10 cards) ---
    COLS = 5
    ROWS = 2
    CARDS_PER_PAGE = COLS * ROWS # 10 cards
    
    # Grid Total Dimensions Calculation
    total_grid_width = (COLS * CARD_WIDTH) + ((COLS - 1) * COL_GAP)
    total_grid_height = (ROWS * CARD_HEIGHT) + ((ROWS - 1) * ROW_GAP)
    
    # --- POSITION LOGIC ---
    start_x = left_margin_val * cm
    start_y = (21.0 * cm - total_grid_height) / 2
    
    # Output PDF setup with LANDSCAPE orientation
    output_buffer = io.BytesIO()
    c = canvas.Canvas(output_buffer, pagesize=landscape(A4))
    
    card_count = 0
    col = 0
    row = ROWS - 1 
    
    # --- Processing Files ---
    for uploaded_file in uploaded_files:
        file_bytes = uploaded_file.read()
        filename = uploaded_file.name.lower()
        
        # --- NEW: File Type Detection (PDF or Image) ---
        try:
            if filename.endswith(".pdf"):
                doc = fitz.open(stream=file_bytes, filetype="pdf")
            elif filename.endswith((".jpg", ".jpeg")):
                doc = fitz.open(stream=file_bytes, filetype="jpeg")
            elif filename.endswith(".png"):
                doc = fitz.open(stream=file_bytes, filetype="png")
            else:
                # Agar koi aur file aa jaye to skip karein
                st.warning(f"Skipping unsupported file: {uploaded_file.name}")
                continue
        except Exception as e:
            st.error(f"Error reading {uploaded_file.name}: {e}")
            continue
        
        # Ab chahe PDF ho ya Image, PyMuPDF usse "doc" ki tarah hi treat karega
        for page_num in range(len(doc)):
            # Safety Limit
            if card_count >= 200:
                break
                
            page = doc.load_page(page_num)
            
            # --- DYNAMIC DPI LOGIC ---
            mat = fitz.Matrix(dpi_scale, dpi_scale) 
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # Position Calculation
            x_pos = start_x + (col * (CARD_WIDTH + COL_GAP))
            y_pos = start_y + (row * (CARD_HEIGHT + ROW_GAP))
            
            # --- Draw ID Card Image ---
            from reportlab.lib.utils import ImageReader
            img = ImageReader(io.BytesIO(img_data))
            # Image ko force-resize karke 5.5x8.5 cm box me fit karenge
            c.drawImage(img, x_pos, y_pos, width=CARD_WIDTH, height=CARD_HEIGHT)
            
            # --- Single Line Cutting Grid (Dashed) ---
            c.setStrokeColor(grey) 
            c.setLineWidth(1)
            c.setDash(4, 4)
            c.rect(x_pos, y_pos, CARD_WIDTH, CARD_HEIGHT)
            c.setDash(1, 0) # Reset to solid
            
            # --- Scissor Icons (✂️) ---
            try:
                c.setFont("ZapfDingbats", 8) 
                c.setFillColor(black)
                scissor_char = chr(34) 
                
                # Scissors
                c.drawString(x_pos - 4, y_pos + CARD_HEIGHT - 4, scissor_char)
                if col == COLS - 1:
                     c.drawString(x_pos + CARD_WIDTH + 1, y_pos - 2, scissor_char)
            except:
                pass 

            # Grid Update Logic
            card_count += 1
            col += 1
            
            if col >= COLS:
                col = 0
                row -= 1
            
            if card_count % CARDS_PER_PAGE == 0:
                c.showPage() 
                col = 0
                row = ROWS - 1 
        
        doc.close()
        if card_count >= 200:
            st.warning("⚠️ 200 ID Cards limit reached.")
            break

    c.save()
    output_buffer.seek(0)
    return output_buffer

# --- Streamlit UI ---

# Page Setup
st.set_page_config(page_title="राष्ट्रीय मध्यान्ह भोजन रसोइया फ्रन्ट", page_icon="🪪", layout="wide")

# --- SIDEBAR ---
with st.sidebar:
    try:
        st.image("logo.png", width=150)
    except:
        st.info("📂 Upload logo.png to see logo here")
        
    st.title("Admin Panel") 
    st.markdown("### Contact Details")
    st.info("""
    **Address:** 14/17 sec-50 Faridabad  
    
    **Mobile:** 9026479519  
    
    **Email:** rasoiyafront3@gmail.com
    """)
    st.markdown("---")
    
    # --- Margin & Gap Adjustment ---
    st.markdown("### 📏 Adjustments")
    
    st.write("**1. Left Margin (Horizontal):**")
    left_margin_val = st.slider(
        "Move Grid Left/Right (cm)", 
        min_value=0.0, 
        max_value=2.2, 
        value=0.6, 
        step=0.1
    )
    
    st.write("**2. Row Gap (Vertical):**")
    row_gap_val = st.slider(
        "Gap between Rows (cm)", 
        min_value=0.0, 
        max_value=2.0, 
        value=0.5, 
        step=0.1
    )
    
    st.markdown("---")
    st.caption("Developed by Ashish Singh.")

# --- MAIN HEADER ---
col1, col2 = st.columns([1, 6]) 

with col1:
    try:
        st.image("logo.png", width=100)
    except:
        st.write("🖼️") 

with col2:
    st.title("राष्ट्रीय मध्यान्ह भोजन रसोइया फ्रन्ट") 
    st.subheader("ID Card Grid Maker (PDF + Images)")
    st.write("Support: PDF, JPG, PNG | Adjustable Settings | 10 Cards per Page")

# --- SETTINGS SECTION (DPI CONTROL) ---
st.markdown("---")
st.write("### ⚙️ Printing Settings")

col_dpi, col_info = st.columns([3, 2])

with col_dpi:
    dpi_choice = st.radio(
        "Select Print Quality (Resolution):",
        ["Fast (150 DPI)", "Standard (300 DPI)", "Ultra HD (600 DPI)"],
        index=1,
        horizontal=True
    )

if "150" in dpi_choice:
    dpi_scale = 2.0
elif "300" in dpi_choice:
    dpi_scale = 4.0
else:
    dpi_scale = 8.0 

# --- FILE UPLOADER SECTION ---
# Added 'jpg', 'jpeg', 'png' to the allowed types
uploaded_files = st.file_uploader(
    "Upload ID Cards (PDF, JPG, PNG)", 
    type=["pdf", "jpg", "jpeg", "png"], 
    accept_multiple_files=True
)

if uploaded_files:
    num_files = len(uploaded_files)
    st.success(f"📂 {num_files} files selected.")
    
    if st.button(f"Generate PDF ({dpi_choice}) ✂️"):
        with st.spinner(f"Processing..."):
            try:
                pdf_output = generate_grid_pdf(uploaded_files, dpi_scale, left_margin_val, row_gap_val)
                
                st.balloons() 
                st.success(f"✅ PDF Generated! (Row Gap: {row_gap_val} cm)")
                
                st.download_button(
                    label="📥 Download Final PDF",
                    data=pdf_output,
                    file_name=f"id_cards_images_supported.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Error: {e}")
