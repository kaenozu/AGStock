"""
Export Manager - データのエクスポート機能
CSV, Excel, PDF形式でのエクスポートをサポート
"""
import pandas as pd
from datetime import datetime
from typing import Dict
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch


class ExportManager:
    """データエクスポート管理クラス"""
    
    def __init__(self):
        self.export_formats = ['CSV', 'Excel', 'PDF', 'JSON']
    
    def export_to_csv(self, data: pd.DataFrame, filename: str) -> bytes:
        """CSVエクスポート"""
        buffer = io.StringIO()
        data.to_csv(buffer, index=False, encoding='utf-8-sig')
        return buffer.getvalue().encode('utf-8-sig')
    
    def export_to_excel(self, data: Dict[str, pd.DataFrame], filename: str) -> bytes:
        """Excelエクスポート（複数シート対応）"""
        buffer = io.BytesIO()
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            for sheet_name, df in data.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def export_to_pdf(self, data: pd.DataFrame, title: str, filename: str) -> bytes:
        """PDFエクスポート"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        
        # スタイル
        styles = getSampleStyleSheet()
        
        # タイトル
        title_para = Paragraph(f"<b>{title}</b>", styles['Title'])
        elements.append(title_para)
        elements.append(Spacer(1, 0.2*inch))
        
        # 日時
        date_para = Paragraph(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])
        elements.append(date_para)
        elements.append(Spacer(1, 0.3*inch))
        
        # テーブルデータ
        table_data = [data.columns.tolist()] + data.values.tolist()
        
        # テーブル作成
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def export_to_json(self, data: pd.DataFrame, filename: str) -> bytes:
        """JSONエクスポート"""
        json_str = data.to_json(orient='records', force_ascii=False, indent=2)
        return json_str.encode('utf-8')
    
    def export_portfolio_report(self, 
                                balance: Dict,
                                positions: pd.DataFrame,
                                history: pd.DataFrame,
                                format: str = 'PDF') -> bytes:
        """ポートフォリオレポートのエクスポート"""
        
        if format == 'PDF':
            # PDFレポート生成
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()
            
            # タイトル
            elements.append(Paragraph("<b>ポートフォリオレポート</b>", styles['Title']))
            elements.append(Spacer(1, 0.3*inch))
            
            # 残高情報
            elements.append(Paragraph("<b>残高情報</b>", styles['Heading2']))
            balance_data = [
                ['項目', '金額'],
                ['現金', f"¥{balance.get('cash', 0):,.0f}"],
                ['株式評価額', f"¥{balance.get('stock_value', 0):,.0f}"],
                ['総資産', f"¥{balance.get('total_equity', 0):,.0f}"]
            ]
            balance_table = Table(balance_data)
            balance_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(balance_table)
            elements.append(Spacer(1, 0.3*inch))
            
            # ポジション情報
            if not positions.empty:
                elements.append(Paragraph("<b>保有ポジション</b>", styles['Heading2']))
                pos_data = [positions.columns.tolist()] + positions.head(10).values.tolist()
                pos_table = Table(pos_data)
                pos_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(pos_table)
            
            doc.build(elements)
            buffer.seek(0)
            return buffer.getvalue()
        
        elif format == 'Excel':
            # Excelレポート生成
            data_dict = {
                '残高': pd.DataFrame([balance]),
                'ポジション': positions,
                '取引履歴': history.tail(100)
            }
            return self.export_to_excel(data_dict, 'portfolio_report.xlsx')
        
        else:
            raise ValueError(f"Unsupported format: {format}")


if __name__ == "__main__":
    # テスト
    manager = ExportManager()
    
    # サンプルデータ
    df = pd.DataFrame({
        'Date': ['2025-01-01', '2025-01-02'],
        'Ticker': ['7203.T', '9984.T'],
        'Price': [1000, 2000],
        'Quantity': [100, 50]
    })
    
    # CSV
    csv_data = manager.export_to_csv(df, 'test.csv')
    print(f"CSV exported: {len(csv_data)} bytes")
    
    # Excel
    excel_data = manager.export_to_excel({'Sheet1': df}, 'test.xlsx')
    print(f"Excel exported: {len(excel_data)} bytes")
    
    # PDF
    pdf_data = manager.export_to_pdf(df, 'Test Report', 'test.pdf')
    print(f"PDF exported: {len(pdf_data)} bytes")
