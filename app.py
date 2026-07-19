import streamlit as st
import io
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import grey, black
from reportlab.lib.utils import ImageReader

# --- New Card Dimensions ---
# Outer Slot (Cutting Size): 56mm x 88mm
SLOT_WIDTH = 56 * mm  
SLOT_HEIGHT = 88 * mm 

# Inner Content (Printed Matter): 50mm x 82mm
CONTENT_WIDTH = 50 * mm
CONTENT_HEIGHT = 82 * mm

# Auto-calculate margin for centering (3mm on each side)
MARGIN_X = (SLOT_WIDTH - CONTENT_WIDTH) / 2
MARGIN_Y = (SLOT_HEIGHT - CONTENT_HEIGHT) / 2

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

    # Starting X and Y to perfectly center the grid on A4 paper
    start_x = (page_width - total_grid_width) / 2
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
            # Check orientation of source image
            rect = page.rect
            is_source_landscape = rect.width > rect.height

            # Rotate 90 degrees if source is landscape to fit in portrait slot
            if is_source_landscape:
                mat = fitz.Matrix(90) 
            else:
                mat = fitz.Matrix(1, 1) # Identity

            # Apply DPI Scaling on top of rotation
            scale_matrix = fitz.Matrix(dpi_scale, dpi_scale)
            final_matrix = mat * scale_matrix

            pix = page.get_pixmap(matrix=final_matrix, alpha=False)
            img_data = pix.tobytes("png")

            # --- Position Calculation ---
            # Outer Slot Position (For cutting and layout calculation)
            x_pos = start_x + (col * (SLOT_WIDTH + GAP))
            y_pos = start_y + (row * (SLOT_HEIGHT + GAP))

            # Inner Content Position (Shifted by 3mm margin)
            img_x = x_pos + MARGIN_X
            img_y = y_pos + MARGIN_Y

            # --- Draw ID Card Image ---
            img = ImageReader(io.BytesIO(img_data))
            
            # Image ko andar wale 50x82 area me draw karein
            c.drawImage(img, img_x, img_y, width=CONTENT_WIDTH, height=CONTENT_HEIGHT)

            # --- Cutting Guides (Optional) ---
            if draw_cut_lines:
                c.setStrokeColor(grey)
                c.setLineWidth(0.5)
                c.setDash(3, 3) # Dashed line
                
                # Cutting box outer 56x88 dimensions par banega
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
        
        # Break out of outer loop if limit reached
        if card_count >= 150:
            break
            
    if card_count >= 150:
        st.warning("⚠️ 150 ID Cards limit reached for this batch.")

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
    **Features:** Exact 56x88 mm Size | 50x82 mm Safe Print Area | Auto-Centering | High DPI | Smart Rotation
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
    st.caption("Designed for perfect edge-to-edge printing with a 3mm safe margin.")

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

                st.success("✅ Done! Cards are set to 50x82mm print size inside a 56x88mm cutting box.")

            except Exception as e:
                st.error(f"An error occurred: {e}")
