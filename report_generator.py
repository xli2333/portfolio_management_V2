from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import os
import io

# Try to register a Chinese font
CHINESE_FONT = 'Helvetica'
FONT_PATH = None

try:
    # On Windows, try to use SimHei or Microsoft YaHei
    if os.name == 'nt':
        # Check common paths
        paths = ['C:\\Windows\\Fonts\\simhei.ttf', 'C:\\Windows\\Fonts\\msyh.ttf'] # Note: msyh is usually ttc, but let's try ttf
        for p in paths:
            if os.path.exists(p):
                pdfmetrics.registerFont(TTFont('SimHei', p))
                CHINESE_FONT = 'SimHei'
                FONT_PATH = p
                print(f"Loaded Chinese font: {p}")
                break
except Exception as e:
    print(f"Font loading failed: {e}, falling back to default.")

def create_chat_pdf(symbol, messages) -> bytes:
    """
    Generate a PDF from chat messages.
    messages: list of strings (already formatted as "Role: Text")
    Returns: PDF bytes
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    margin = 2 * cm
    y = h - margin
    
    # Check font availability
    font_to_use = CHINESE_FONT if CHINESE_FONT in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
    
    # Title
    c.setFont(font_to_use, 16)
    c.drawString(margin, y, f"{symbol} - AI Chat History")
    y -= 1.5 * cm
    
    c.setFont(font_to_use, 10)
    
    line_height = 0.5 * cm
    
    for msg in messages:
        # Simple text wrapping logic
        text = msg.replace('\n', ' ') # Flatten for simplicity in this basic version
        
        # Split into lines (very basic wrapping)
        max_chars = 80
        lines = [text[i:i+max_chars] for i in range(0, len(text), max_chars)]
        
        for line in lines:
            if y < margin:
                c.showPage()
                y = h - margin
                c.setFont(font_to_use, 10)
            
            c.drawString(margin, y, line)
            y -= line_height
        
        y -= 0.5 * cm # Extra space between messages

    c.save()
    buffer.seek(0)
    return buffer.read()

from reportlab.lib.colors import HexColor

# ... (rest of imports)

def create_markdown_pdf(symbol, markdown_text) -> bytes:
    """
    Generate a formatted PDF from Markdown text using Platypus.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    
    # Check font availability
    font_to_use = CHINESE_FONT if CHINESE_FONT in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
    
    styles = getSampleStyleSheet()
    # Create Custom Styles with Chinese Font
    styles.add(ParagraphStyle(name='ChineseNormal', parent=styles['Normal'], fontName=font_to_use, fontSize=10, leading=14))
    styles.add(ParagraphStyle(name='ChineseHeading1', parent=styles['Heading1'], fontName=font_to_use, fontSize=18, leading=22, spaceAfter=12, textColor=HexColor('#0f172a')))
    styles.add(ParagraphStyle(name='ChineseHeading2', parent=styles['Heading2'], fontName=font_to_use, fontSize=14, leading=18, spaceBefore=12, spaceAfter=6, textColor=HexColor('#334155')))
    
    story = []
    
    # Title
    story.append(Paragraph(f"{symbol} - 深度研究报告", styles['ChineseHeading1']))
    story.append(Spacer(1, 0.5*cm))
    
    # Simple Markdown Parser
    lines = markdown_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            story.append(Spacer(1, 0.2*cm))
            continue
            
        try:
            # Clean Markdown formatting for cleaner PDF text
            clean_line = line.replace('**', '') # Remove bold markers for simplicity
            clean_line = clean_line.replace('__', '')
            clean_line = clean_line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            if line.startswith('# '):
                story.append(Paragraph(clean_line[2:], styles['ChineseHeading1']))
            elif line.startswith('## '):
                story.append(Paragraph(clean_line[3:], styles['ChineseHeading2']))
            elif line.startswith('### '):
                # Treat h3 as h2/bold for now
                story.append(Paragraph(f"<b>{clean_line[4:]}</b>", styles['ChineseNormal']))
            elif line.startswith('- ') or line.startswith('* '):
                # List item
                story.append(Paragraph(f"• {clean_line[2:]}", styles['ChineseNormal']))
            else:
                story.append(Paragraph(clean_line, styles['ChineseNormal']))
        except Exception as e:
            print(f"PDF Gen Error on line: {line} -> {e}")
            
    try:
        doc.build(story)
    except Exception as e:
        print(f"PDF Build Failed: {e}")
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer)
        c.drawString(100, 700, "PDF Generation Failed. Please check logs.")
        c.save()
        buffer.seek(0)
        return buffer.read()

    buffer.seek(0)
    return buffer.read()
