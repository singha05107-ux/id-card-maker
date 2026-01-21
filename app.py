import streamlit as st
import fitz  # PyMuPDF
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import black, grey
import io

# --- Constants for ID Card (CR80 Standard) ---
# Card Dimensions in Inches
CARD_WIDTH_INCH = 3.375  # 85.6mm (Landscape width)
CARD_HEIGHT_INCH = 2.125 # 53.98mm (Landscape height)

# On the paper, since we need to fit 5 in a row, we must rotate them to Portrait slots
# So the SLOT on paper will be:
SLOT_WIDTH = CARD_HEIGHT_INCH * inch  # 2.125 inches on paper width
SLOT_HEIGHT = CARD_WIDTH_INCH * inch  # 3.375 inches on paper height

def generate_grid_pdf(uploaded_files, dpi_scale, gap_val, draw_cut_lines):
    # --- Configuration ---
    # LANDSCAPE LAYOUT: 5 Columns x 2 Rows
    COLS = 5
    ROWS = 2
    CARDS_PER_PAGE = COLS * ROWS # 10 cards
    
    # Gap settings (Converted to points)
    GAP = gap_val * mm 
    
    # --- Auto-Calculate Centering ---
    # Total grid dimensions
    total_grid_width = (COLS * SLOT_WIDTH) + ((COLS - 1) * GAP)
    total_grid_height = (ROWS * SLOT_HEIGHT) + ((ROWS - 1) * GAP)
    
    # A4 Landscape Dimensions
    page_width, page_height = landscape(A4)
    
    # Starting X and Y to perfectly center the grid
    start_x = (page_width - total_grid_width) / 0
    start_y = (page_height - total_grid_height) / 2
    
    # Output PDF setup
    output_buffer = io.BytesIO()
    c = canvas.Canvas(output_buffer, pagesize=landscape(A4))
    c.setTitle("ID Card Grid - 5x2")
    
    card_count = 0
    col = 0
    row = ROWS - 1 
    
    # --- Processing Files ---
    for uploaded_file in uploaded_files:
        file_bytes = uploaded_file.read()
        filename = uploaded_file.name.lower()
        
        try:
            # Handle PDF vs Images
            if filename.endswith(".pdf"):
                doc = fitz.open(stream=file_bytes, filetype="pdf")
            elif filename.endswith((".jpg", ".jpeg")):
                doc = fitz.open(stream=file_bytes, filetype="jpeg")
            elif filename.endswith(".png"):
                doc = fitz.open(stream=file_bytes, filetype="png")
            else:
                st.warning(f"Skipping unsupported file: {uploaded_file.name}")
                continue
        except Exception as e:
            st.error(f"Error reading {uploaded_file.name}: {e}")
            continue
        
        for page_num in range(len(doc)):
            # Safety Limit for memory
            if card_count >= 150:
                break
                
            page = doc.load_page(page_num)
            
            # --- INTELLIGENT ROTATION & DPI LOGIC ---
            # We want high quality, so we assume 300-600 DPI.
            # 72 points = 1 inch. To get 300 DPI, we need scale factor ~4.16
            
            # Check orientation of source image
            rect = page.rect
            is_source_landscape = rect.width > rect.height
            
            # Matrix logic:
            # We need the final image to fit into a Portrait Slot (2.125 W x 3.375 H)
            # If source is Landscape (Standard ID), we must rotate it 90 degrees.
            
            if is_source_landscape:
                # Rotate 90 degrees clockwise to make it stand up
                mat = fitz.Matrix(0, 1, -1, 0)
            else:
                # If already portrait, just scale
                mat = fitz.Matrix(1, 1) # Identity
            
            # Apply DPI Scaling on top of rotation
            scale_matrix = fitz.Matrix(dpi_scale, dpi_scale)
            final_matrix = mat * scale_matrix
            
            pix = page.get_pixmap(matrix=final_matrix, alpha=False)
            img_data = pix.tobytes("png")
            
            # Position Calculation
            x_pos = start_x + (col * (SLOT_WIDTH + GAP))
            y_pos = start_y + (row * (SLOT_HEIGHT + GAP))
            
            # --- Draw ID Card Image ---
            from reportlab.lib.utils import ImageReader
            img = ImageReader(io.BytesIO(img_data))
            
            # Draw the image into the calculated slot
            c.drawImage(img, x_pos, y_pos, width=SLOT_WIDTH, height=SLOT_HEIGHT)
            
            # --- Cutting Guides (Optional) ---
            if draw_cut_lines:
                c.setStrokeColor(grey)
                c.setLineWidth(0.5)
                c.setDash(3, 3) # Dashed line
                c.rect(x_pos, y_pos, SLOT_WIDTH, SLOT_HEIGHT)
                c.setDash(1, 0) # Reset
                
                # Crop Marks (Corner L shapes) - Better for professional cutting
                c.setStrokeColor(black)
                c.setLineWidth(1)
                len_mark = 5
                
                # Bottom Left
                c.line(x_pos - 2, y_pos, x_pos - 2 - len_mark, y_pos) # Horz
                c.line(x_pos, y_pos - 2, x_pos, y_pos - 2 - len_mark) # Vert
                
                # Top Right
                c.line(x_pos + SLOT_WIDTH + 2, y_pos + SLOT_HEIGHT, x_pos + SLOT_WIDTH + 2 + len_mark, y_pos + SLOT_HEIGHT)
                c.line(x_pos + SLOT_WIDTH, y_pos + SLOT_HEIGHT + 2, x_pos + SLOT_WIDTH, y_pos + SLOT_HEIGHT + 2 + len_mark)

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
        if card_count >= 150:
            st.warning("⚠️ 150 ID Cards limit reached for this batch.")
            break

    c.save()
    output_buffer.seek(0)
    return output_buffer

# --- Streamlit UI ---

st.set_page_config(page_title="ID Card Print Master", page_icon="🖨️", layout="wide")

st.title("🖨️ Pro ID Card Organizer (5x2 Grid)")
st.markdown(
    """
    <style>
    .reportview-container { background: #f0f2f6; }
    </style>
    **Features:** Exact 3.375" x 2.125" Size | Auto-Centering | High DPI | Smart Rotation
    """, unsafe_allow_html=True
)

with st.sidebar:
    st.header("⚙️ Settings")
    
    st.info("The layout is **5 columns x 2 rows**. To fit 5 cards on A4 width, cards are automatically rotated 90°.")
    
    # Gap Adjustment
    gap_val = st.slider("Cutting Gap (mm)", 0.0, 5.0, 1.0, 0.5)
    
    # Cutting Lines
    draw_cut_lines = st.checkbox("Draw Cutting Borders/Marks", value=True)
    
    # DPI Settings
    quality = st.select_slider(
        "Print Quality", 
        options=["Draft", "High (300 DPI)", "Ultra (600 DPI)"], 
        value="High (300 DPI)"
    )
    
    if "Ultra" in quality:
        dpi_scale = 8.0 # Very High Res
    elif "High" in quality:
        dpi_scale = 4.16 # ~300 DPI
    else:
        dpi_scale = 2.0 

    st.markdown("---")
    st.caption("Designed for perfect edge-to-edge printing.")

# --- File Upload ---
uploaded_files = st.file_uploader(
    "Upload ID Cards (PDF, JPG, PNG) - Max 150", 
    type=["pdf", "jpg", "jpeg", "png"], 
    accept_multiple_files=True
)

if uploaded_files:
    num_files = len(uploaded_files)
    st.success(f"📂 {num_files} files loaded.")
    
    if st.button("🚀 Generate Print-Ready PDF"):
        with st.spinner("Processing High-Quality PDF..."):
            try:
                pdf_data = generate_grid_pdf(uploaded_files, dpi_scale, gap_val, draw_cut_lines)
                
                st.balloons()
                
                st.download_button(
                    label="📥 Download PDF (A4 Landscape)",
                    data=pdf_data,
                    file_name="id_cards_5x2_print_ready.pdf",
                    mime="application/pdf"
                )
                
                st.success("✅ Done! Cards have been rotated to fit 10 per page.")
                
            except Exception as e:
                st.error(f"An error occurred: {e}")

