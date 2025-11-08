"""
PDF Report Generator for GitHub Health Analysis
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
from typing import Dict, List
import io

def generate_health_report_pdf(health_data: Dict, output_path: str = None) -> bytes:
    """
    Generate PDF report for GitHub health analysis
    
    Args:
        health_data: Dict containing health report data
        output_path: Optional file path to save PDF. If None, returns bytes
    
    Returns:
        bytes: PDF file content
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer if output_path is None else output_path, pagesize=letter)
    story = []
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#6366f1'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#6366f1'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=colors.HexColor('#8b5cf6'),
        spaceAfter=8,
        spaceBefore=8
    )
    
    # Title
    story.append(Paragraph("GitHub Profile Health Report", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Date
    date_str = datetime.now().strftime("%B %d, %Y")
    story.append(Paragraph(f"Generated on: {date_str}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Summary Section
    username = health_data.get('username', 'Unknown')
    health_score = health_data.get('health_score', 0)
    good_pct = health_data.get('good_percentage', 0)
    bad_pct = health_data.get('bad_percentage', 0)
    
    story.append(Paragraph(f"Profile: <b>{username}</b>", heading_style))
    
    # Health Score
    score_color = colors.HexColor('#10b981') if health_score >= 70 else colors.HexColor('#f59e0b') if health_score >= 50 else colors.HexColor('#ef4444')
    score_style = ParagraphStyle(
        'ScoreStyle',
        parent=styles['Heading2'],
        fontSize=36,
        textColor=score_color,
        alignment=TA_CENTER
    )
    story.append(Paragraph(f"Health Score: {health_score}/100", score_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Percentages
    pct_data = [
        ['Metric', 'Percentage'],
        ['Good Patterns', f'{good_pct}%'],
        ['Bad Patterns', f'{bad_pct}%']
    ]
    pct_table = Table(pct_data, colWidths=[4*inch, 2*inch])
    pct_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(pct_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Language Percentages
    if 'language_percentages' in health_data:
        story.append(Paragraph("Languages Used", subheading_style))
        lang_data = [['Language', 'Percentage']]
        for lang, pct in sorted(health_data['language_percentages'].items(), key=lambda x: x[1], reverse=True):
            lang_data.append([lang, f'{pct}%'])
        
        lang_table = Table(lang_data, colWidths=[4*inch, 2*inch])
        lang_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8b5cf6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(lang_table)
        story.append(Spacer(1, 0.3*inch))
    
    # Good Patterns
    good_patterns = health_data.get('good_patterns', [])
    if good_patterns:
        story.append(Paragraph("✅ Good Patterns Found", heading_style))
        for pattern in good_patterns[:15]:  # Limit to top 15
            desc = pattern.get('description', '')
            category = pattern.get('category', '')
            story.append(Paragraph(f"• {desc} <i>({category})</i>", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
    
    # Bad Patterns
    bad_patterns = health_data.get('bad_patterns', [])
    if bad_patterns:
        story.append(Paragraph("❌ Bad Patterns Found", heading_style))
        for pattern in bad_patterns[:15]:  # Limit to top 15
            desc = pattern.get('description', '')
            category = pattern.get('category', '')
            story.append(Paragraph(f"• {desc} <i>({category})</i>", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
    
    # AI Suggestions
    ai_suggestions = health_data.get('ai_suggestions', {})
    if ai_suggestions:
        story.append(PageBreak())
        story.append(Paragraph("🤖 AI-Powered Recommendations", heading_style))
        
        if ai_suggestions.get('summary'):
            story.append(Paragraph(f"<b>Summary:</b> {ai_suggestions['summary']}", styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
        
        if ai_suggestions.get('suggestions'):
            story.append(Paragraph("Top Suggestions:", subheading_style))
            for i, suggestion in enumerate(ai_suggestions['suggestions'][:5], 1):
                story.append(Paragraph(f"{i}. {suggestion}", styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
        
        if ai_suggestions.get('roadmap'):
            story.append(Paragraph("Improvement Roadmap:", subheading_style))
            for i, step in enumerate(ai_suggestions['roadmap'][:5], 1):
                story.append(Paragraph(f"{i}. {step}", styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
        
        if ai_suggestions.get('enhancements'):
            story.append(Paragraph("Enhancement Opportunities:", subheading_style))
            for i, enhancement in enumerate(ai_suggestions['enhancements'][:5], 1):
                story.append(Paragraph(f"{i}. {enhancement}", styles['Normal']))
    
    # Build PDF
    doc.build(story)
    
    if output_path is None:
        buffer.seek(0)
        return buffer.getvalue()
    return b''

