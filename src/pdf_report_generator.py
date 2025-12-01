"""
PDF Report Generator Module
Generates automated weekly/monthly performance reports with AI analysis.
"""
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from src.paper_trader import PaperTrader
from src.ai_analyst import AIAnalyst
from src.data_loader import fetch_stock_data

# For PDF generation
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logging.warning("reportlab not installed. PDF generation disabled.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFReportGenerator:
    def __init__(self):
        self.pt = PaperTrader()
        self.analyst = AIAnalyst()
        self.styles = getSampleStyleSheet() if PDF_AVAILABLE else None
    
    def generate_performance_chart(self, output_path: str = "temp_performance.png"):
        """Generate performance chart and save to file."""
        try:
            # Get equity history
            # TODO: Implement proper equity tracking
            # For now, create a dummy chart
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Dummy data for demonstration
            dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
            equity = [1000000 * (1 + 0.001 * i + 0.02 * (i % 7 == 0)) for i in range(30)]
            
            ax.plot(dates, equity, linewidth=2, color='#2E86AB')
            ax.fill_between(dates, equity, alpha=0.3, color='#2E86AB')
            ax.set_title('Portfolio Equity Curve', fontsize=14, fontweight='bold')
            ax.set_xlabel('Date')
            ax.set_ylabel('Equity (¥)')
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return output_path
        except Exception as e:
            logger.error(f"Error generating chart: {e}")
            return None
    
    def generate_ai_analysis(self) -> str:
        """Generate AI analysis of performance."""
        if not self.analyst.enabled:
            return "AI analysis unavailable (API key not configured)"
        
        try:
            balance = self.pt.get_current_balance()
            positions = self.pt.get_positions()
            
            context = f"""
## Portfolio Status
- Total Equity: ¥{balance['total_equity']:,.0f}
- Cash: ¥{balance['cash']:,.0f}
- Positions: {len(positions)}

Please provide:
1. Performance assessment
2. Risk analysis
3. Improvement suggestions

Keep it concise (max 200 words).
"""
            
            analysis = self.analyst.generate_response(
                system_prompt="You are a professional portfolio analyst. Provide concise, actionable insights in Japanese.",
                user_prompt=context,
                temperature=0.7
            )
            
            return analysis
        except Exception as e:
            logger.error(f"Error generating AI analysis: {e}")
            return f"AI analysis error: {str(e)}"
    
    def generate_weekly_report(self, output_path: str = "weekly_report.pdf") -> bool:
        """
        Generate weekly PDF report.
        
        Args:
            output_path: Path to save PDF
            
        Returns:
            True if successful
        """
        if not PDF_AVAILABLE:
            logger.error("reportlab not installed. Cannot generate PDF.")
            return False
        
        try:
            # Create PDF
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#2E86AB'),
                spaceAfter=30
            )
            
            title = Paragraph(f"AGStock Weekly Report<br/>{datetime.now().strftime('%Y-%m-%d')}", title_style)
            story.append(title)
            story.append(Spacer(1, 0.2*inch))
            
            # Portfolio Summary
            balance = self.pt.get_current_balance()
            positions = self.pt.get_positions()
            
            summary_data = [
                ['Metric', 'Value'],
                ['Total Equity', f"¥{balance['total_equity']:,.0f}"],
                ['Cash', f"¥{balance['cash']:,.0f}"],
                ['Positions', str(len(positions))],
                ['Initial Capital', f"¥{self.pt.initial_capital:,.0f}"],
                ['Total Return', f"{((balance['total_equity'] - self.pt.initial_capital) / self.pt.initial_capital):.1%}"]
            ]
            
            summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Performance Chart
            chart_path = self.generate_performance_chart()
            if chart_path:
                img = Image(chart_path, width=5*inch, height=3*inch)
                story.append(img)
                story.append(Spacer(1, 0.3*inch))
            
            # AI Analysis
            story.append(Paragraph("AI Performance Analysis", self.styles['Heading2']))
            story.append(Spacer(1, 0.1*inch))
            
            ai_analysis = self.generate_ai_analysis()
            analysis_para = Paragraph(ai_analysis.replace('\n', '<br/>'), self.styles['BodyText'])
            story.append(analysis_para)
            
            # Build PDF
            doc.build(story)
            logger.info(f"Weekly report generated: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            return False

if __name__ == "__main__":
    # Test
    generator = PDFReportGenerator()
    success = generator.generate_weekly_report("test_report.pdf")
    print(f"Report generated: {success}")
