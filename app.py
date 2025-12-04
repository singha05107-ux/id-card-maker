import streamlit as st
import fitz  # PyMuPDF
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
# Added 'grey' for darker lines
from reportlab.lib.colors import black, lightgrey, grey
import io

def generate_grid_pdf(uploaded_files):
    # --- Configuration ---
    # A4 Size: 21.0 x 29.7 cm
    CARD_WIDTH = 5.5 * cm
    CARD_HEIGHT = 8.5 * cm
    
    # Gap (Cutting space)
    GAP = 0.5 * cm
    
    # Grid Layout (3x3 = 9 cards)
    COLS = 3
    ROWS = 3
    
    # Grid Total Height Calculation
    total_grid_height = (ROWS * CARD_HEIGHT) + ((ROWS - 1) * GAP)
    total_grid_width = (COLS * CARD_WIDTH) + ((COLS - 1) * GAP)
    
    # --- POSITION FIX ---
    # Bottom Margin 2.0 CM (Printer safe zone)
    bottom_margin = 2.0 * cm
    start_y = bottom_margin
    # Horizontal Center
    start_x = (21.0 * cm - total_grid_width) / 2
    
    # Output PDF setup
    output_buffer = io.BytesIO()
    c = canvas.Canvas(output_buffer, pagesize=A4)
    
    card_count = 0
    col = 0
    row = ROWS - 1 
    
    # --- Processing Files ---
    for uploaded_file in uploaded_files:
        file_stream = uploaded_file.read()
        doc = fitz.open(stream=file_stream, filetype="pdf")
        
        for page_num in range(len(doc)):
            if card_count >= 200:
                break
                
            page = doc.load_page(page_num)
            
            # 600 DPI Logic
            mat = fitz.Matrix(8.0, 8.0) 
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # Position Calculation
            x_pos = start_x + (col * (CARD_WIDTH + GAP))
            y_pos = start_y + (row * (CARD_HEIGHT + GAP))
            
            # --- 1. New Darker Cutting Guidelines with Scissors ---
            
            # A. Draw Dotted Rectangle (Darker and Thicker)
            c.setStrokeColor(grey) # Changed from lightgrey to grey
            c.setLineWidth(1.5)    # Thicker line for visibility
            c.setDash(4, 4)        # Bigger dashes
            # Draw rect slightly outside the card
            cut_rect_x = x_pos - 2
            cut_rect_y = y_pos - 2
            cut_rect_w = CARD_WIDTH + 4
            cut_rect_h = CARD_HEIGHT + 4
            c.rect(cut_rect_x, cut_rect_y, cut_rect_w, cut_rect_h)
            c.setDash(1, 0) # Reset to solid
            
            # B. Draw Scissor Icons (✂️) using ZapfDingbats font
            try:
                c.setFont("ZapfDingbats", 10)
                c.setFillColor(grey)
                scissor_char = chr(34) # Character code for scissor in ZapfDingbats
                
                # Scissor at Top-Left corner of cutting line
                c.drawString(cut_rect_x - 8, cut_rect_y + cut_rect_h - 5, scissor_char)
                
                # Scissor at Bottom-Right corner of cutting line
                c.drawString(cut_rect_x + cut_rect_w + 2, cut_rect_y + 2, scissor_char)
            except:
                # Fallback if font fails, just draw a small 'x'
                c.setFont("Helvetica", 8)
                c.drawString(cut_rect_x - 5, cut_rect_y + cut_rect_h, "x")

            # --- 2. Draw ID Card Image ---
            from reportlab.lib.utils import ImageReader
            img = ImageReader(io.BytesIO(img_data))
            c.drawImage(img, x_pos, y_pos, width=CARD_WIDTH, height=CARD_HEIGHT)
            
            # --- 3. Solid Black Border around the actual card ---
            c.setStrokeColor(black)
            c.setLineWidth(0.5)
            c.rect(x_pos, y_pos, CARD_WIDTH, CARD_HEIGHT)
            
            # Grid Update
            card_count += 1
            col += 1
            
            if col >= COLS:
                col = 0
                row -= 1
            
            if card_count % 9 == 0:
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

# --- Streamlit UI (Branding Area) ---

# Page Setup
st.set_page_config(page_title="राष्ट्रीय मध्यान्ह भोजन रसोइया फ्रन्ट", page_icon="🪪", layout="centered")

# --- SIDEBAR (Aapka Naam aur Contact) ---
with st.sidebar:
    # Koshish karein logo dikhane ki, agar file nahi mili to error nahi aayega
    try:
        st.image("logo.png", width=150)
    except:
        st.write("📂 Upload logo.png to see logo here")
        
    st.title("राष्ट्रीय मध्यान्ह भोजन रसोइया फ्रन्ट") # Yahan Apna Naam Likhein
    st.info("""
    **Address:** 14/17 sec-50 Faridabad
    **Mobile:** 9026479519
    **Email:** rasoiyafront3@gmail.com

    """)
    st.markdown("---")
    st.caption("Developed for professional use Ashish Singh.")

# --- MAIN HEADER (Logo + Title) ---
col1, col2 = st.columns([6, 4]) # Logo chhota, Naam bada

with col1:
    try:
        st.image("logo.png", width=80)
    except:
        st.write("🖼️") # Agar logo nahi hai to icon dikhega

with col2:
    st.title("ID Card Grid Maker") # Tool ka naam
    st.write("Professional Print Tool with Cutting Marks ✂️")

# --- FILE UPLOADER SECTION (Baaki same rahega) ---

uploaded_files = st.file_uploader("Upload ID Card PDFs", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    if st.button("Generate PDF with Scissors ✂️"):
        with st.spinner("Processing... Please wait"):
            try:
                pdf_output = generate_grid_pdf(uploaded_files)
                st.success("✅ PDF Generated! Ready to Print.")
                st.download_button(
                    label="📥 Download Final PDF",
                    data=pdf_output,
                    file_name="processed_id_cards.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Error: {e}")