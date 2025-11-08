"""
PDF Generator - Generate PDFs for receipts, reports, and ID cards
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics import renderPDF
import qrcode
from io import BytesIO
import os
from datetime import datetime


class PDFGenerator:
    """PDF generation utilities"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#FF6F00')
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.HexColor('#FF6F00')
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        ))
    
    def generate_payment_receipt(self, receipt_data, output_path=None):
        """Generate enhanced payment receipt PDF with QR code and school branding"""
        try:
            if output_path is None:
                output_path = f"uploads/receipts/receipt_{receipt_data['payment'].receipt_no}.pdf"
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            doc = SimpleDocTemplate(output_path, pagesize=letter, 
                                  topMargin=0.5*inch, bottomMargin=0.5*inch,
                                  leftMargin=0.5*inch, rightMargin=0.5*inch)
            story = []
            
            payment = receipt_data['payment']
            student = receipt_data['student']
            school = receipt_data['school']
            
            # Enhanced Header with tactical ops styling
            story.append(Paragraph(f'<font color="#FF6F00" size="20"><b>{school.name}</b></font>', 
                                 ParagraphStyle('SchoolHeader', alignment=TA_CENTER, spaceAfter=10)))
            story.append(Paragraph('<font color="#666666" size="12">Excellence in Education</font>', 
                                 ParagraphStyle('Tagline', alignment=TA_CENTER, spaceAfter=5)))
            story.append(Paragraph(f'<font size="10">{school.address if hasattr(school, "address") else ""} | Phone: {school.phone if hasattr(school, "phone") else ""}</font>', 
                                 ParagraphStyle('Contact', alignment=TA_CENTER, spaceAfter=20)))
            
            # Receipt title with styling
            story.append(Paragraph('<font color="#FF6F00" size="16"><b>PAYMENT RECEIPT</b></font>', 
                                 ParagraphStyle('ReceiptTitle', alignment=TA_CENTER, spaceAfter=20)))
            
            # Receipt number and date in header box
            header_data = [
                [f'<b>Receipt No: {payment.receipt_no}</b>', f'<b>Date: {payment.payment_date.strftime("%d/%m/%Y")}</b>']
            ]
            header_table = Table(header_data, colWidths=[3*inch, 3*inch])
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FF6F00')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.white)
            ]))
            story.append(header_table)
            story.append(Spacer(1, 20))
            
            # Student details section
            story.append(Paragraph('<font color="#FF6F00" size="12"><b>Student Information</b></font>', 
                                 ParagraphStyle('SectionHeader', spaceAfter=10)))
            
            student_data = [
                ['Student Name:', student.name, 'Class:', student.class_info.get_display_name() if student.class_info else 'N/A'],
                ['Admission No:', student.admission_no, 'Roll No:', getattr(student, 'roll_number', 'N/A')],
                ['Father\'s Name:', getattr(student, 'father_name', 'N/A'), 'Phone:', getattr(student, 'phone', 'N/A')],
                ['Address:', getattr(student, 'address', 'N/A'), '', '']
            ]
            
            student_table = Table(student_data, colWidths=[1.5*inch, 2.5*inch, 1*inch, 1.5*inch])
            student_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8F9FA')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (-1, -1), 'Helvetica'),
                ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0'))
            ]))
            
            story.append(student_table)
            story.append(Spacer(1, 20))
            
            # Payment details section
            story.append(Paragraph('<font color="#FF6F00" size="12"><b>Payment Details</b></font>', 
                                 ParagraphStyle('SectionHeader', spaceAfter=10)))
            
            # Get fee breakdown if available
            fee_structure = getattr(payment, 'fee_structure', None)
            payment_data = [
                ['<b>Description</b>', '<b>Amount</b>']
            ]
            
            if fee_structure:
                # Add fee breakdown
                if fee_structure.tuition_fee > 0:
                    payment_data.append(['Tuition Fee', f"₹{fee_structure.tuition_fee:,.2f}"])
                if fee_structure.admission_fee > 0:
                    payment_data.append(['Admission Fee', f"₹{fee_structure.admission_fee:,.2f}"])
                if fee_structure.development_fee > 0:
                    payment_data.append(['Development Fee', f"₹{fee_structure.development_fee:,.2f}"])
                if fee_structure.transport_fee > 0:
                    payment_data.append(['Transport Fee', f"₹{fee_structure.transport_fee:,.2f}"])
                if fee_structure.library_fee > 0:
                    payment_data.append(['Library Fee', f"₹{fee_structure.library_fee:,.2f}"])
                if fee_structure.lab_fee > 0:
                    payment_data.append(['Lab Fee', f"₹{fee_structure.lab_fee:,.2f}"])
                if fee_structure.sports_fee > 0:
                    payment_data.append(['Sports Fee', f"₹{fee_structure.sports_fee:,.2f}"])
                if fee_structure.other_fee > 0:
                    payment_data.append(['Other Fee', f"₹{fee_structure.other_fee:,.2f}"])
            else:
                payment_data.append(['Fee Payment', f"₹{payment.amount:,.2f}"])
            
            # Add separator line
            payment_data.append(['', ''])
            payment_data.append([f'<b>Total Amount Paid</b>', f'<b>₹{payment.amount:,.2f}</b>'])
            payment_data.append(['', ''])
            payment_data.append(['Payment Mode', payment.payment_mode.value.title()])
            if payment.transaction_id:
                payment_data.append(['Transaction ID', payment.transaction_id])
            if payment.cheque_no:
                payment_data.append(['Cheque Number', payment.cheque_no])
            if hasattr(payment, 'collected_by') and payment.collected_by:
                payment_data.append(['Collected By', getattr(payment.collector, 'name', 'N/A')])
            
            payment_table = Table(payment_data, colWidths=[4*inch, 2*inch])
            payment_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6F00')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0')),
                # Highlight total row
                ('BACKGROUND', (-2, -4), (-1, -4), colors.HexColor('#FF6F00')),
                ('TEXTCOLOR', (-2, -4), (-1, -4), colors.white),
                ('FONTNAME', (-2, -4), (-1, -4), 'Helvetica-Bold'),
            ]))
            
            story.append(payment_table)
            story.append(Spacer(1, 30))
            
            # QR Code and verification section
            qr_data = f"SCHOOL:{school.id}|RECEIPT:{payment.receipt_no}|STUDENT:{student.admission_no}|AMOUNT:{payment.amount}|DATE:{payment.payment_date.strftime('%Y-%m-%d')}|VERIFY:https://school.edu/verify/{payment.receipt_no}"
            
            # Create a table with QR code and verification info
            qr_section_data = []
            qr_img = self.generate_qr_code(qr_data, size=1.2*inch)
            
            if qr_img:
                verification_text = f'''
                <font size="10"><b>Receipt Verification</b></font><br/>
                <font size="8">Scan QR code to verify this receipt online</font><br/>
                <font size="8">Receipt ID: {payment.receipt_no}</font><br/>
                <font size="8">Verification Code: {payment.receipt_no[-6:].upper()}</font>
                '''
                qr_section_data = [[qr_img, Paragraph(verification_text, self.styles['CustomNormal'])]]
                
                qr_table = Table(qr_section_data, colWidths=[1.5*inch, 4*inch])
                qr_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ]))
                story.append(qr_table)
                story.append(Spacer(1, 20))
            
            # Important notes section
            notes_text = '''
            <font size="9"><b>Important Notes:</b></font><br/>
            <font size="8">• This is a computer-generated receipt and does not require signature</font><br/>
            <font size="8">• Please keep this receipt for your records</font><br/>
            <font size="8">• For any queries, contact the school office</font><br/>
            <font size="8">• Receipt is valid only if payment is realized</font>
            '''
            story.append(Paragraph(notes_text, self.styles['CustomNormal']))
            story.append(Spacer(1, 20))
            
            # Footer with tactical ops styling
            footer_data = [
                ['<font color="#FF6F00" size="12"><b>Thank you for your payment!</b></font>'],
                [f'<font size="8">Generated on: {datetime.now().strftime("%d/%m/%Y at %H:%M:%S")} | System: School Management System v2.0</font>']
            ]
            
            footer_table = Table(footer_data, colWidths=[6*inch])
            footer_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(footer_table)
            
            doc.build(story)
            return True, output_path
            
        except Exception as e:
            return False, f"Error generating receipt: {str(e)}"
    
    def generate_student_id_card(self, student, output_path=None):
        """Generate student ID card PDF"""
        try:
            if output_path is None:
                output_path = f"id_card_{student.admission_no}.pdf"
            
            doc = SimpleDocTemplate(output_path, pagesize=(3.5*inch, 2.2*inch))
            story = []
            
            # School name
            story.append(Paragraph(student.school.name, 
                                 ParagraphStyle('SchoolName', parent=self.styles['Normal'], 
                                              fontSize=12, alignment=TA_CENTER, textColor=colors.HexColor('#FF6F00'))))
            story.append(Spacer(1, 10))
            
            # Student details table
            id_data = [
                [student.name, ''],
                [f"Class: {student.class_info.get_display_name() if student.class_info else 'N/A'}", ''],
                [f"Roll No: {student.roll_number}", ''],
                [f"Admission: {student.admission_no}", ''],
                [f"DOB: {student.date_of_birth.strftime('%d/%m/%Y') if student.date_of_birth else 'N/A'}", '']
            ]
            
            # Add photo placeholder if no photo
            if student.photo_url:
                # In a real implementation, you'd add the actual photo here
                id_data[0][1] = "PHOTO"
            else:
                id_data[0][1] = "NO PHOTO"
            
            id_table = Table(id_data, colWidths=[2*inch, 1*inch])
            id_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            
            story.append(id_table)
            
            doc.build(story)
            return True, output_path
            
        except Exception as e:
            return False, f"Error generating ID card: {str(e)}"
    
    def generate_fee_report(self, report_data, output_path=None):
        """Generate fee collection report PDF"""
        try:
            if output_path is None:
                output_path = f"fee_report_{datetime.now().strftime('%Y%m%d')}.pdf"
            
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            story = []
            
            # Header
            story.append(Paragraph("Fee Collection Report", self.styles['CustomTitle']))
            story.append(Paragraph(f"Generated on: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 
                                 self.styles['CustomNormal']))
            story.append(Spacer(1, 20))
            
            # Summary
            summary_data = [
                ['Total Collections', f"₹{report_data.get('total_collected', 0):,.2f}"],
                ['Total Transactions', str(report_data.get('total_transactions', 0))],
                ['Average Payment', f"₹{report_data.get('average_payment', 0):,.2f}"]
            ]
            
            summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 30))
            
            # Payment mode breakdown
            if 'mode_breakdown' in report_data:
                story.append(Paragraph("Payment Mode Breakdown", self.styles['CustomHeading']))
                
                mode_data = [['Payment Mode', 'Amount']]
                for mode, amount in report_data['mode_breakdown'].items():
                    mode_data.append([mode.title(), f"₹{amount:,.2f}"])
                
                mode_table = Table(mode_data, colWidths=[3*inch, 2*inch])
                mode_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6F00')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(mode_table)
            
            doc.build(story)
            return True, output_path
            
        except Exception as e:
            return False, f"Error generating report: {str(e)}"
    
    def generate_qr_code(self, data, size=1*inch):
        """Generate QR code image for PDF"""
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(data)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Save to BytesIO
            img_buffer = BytesIO()
            qr_img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            # Create reportlab Image
            img = Image(img_buffer, width=size, height=size)
            return img
            
        except Exception as e:
            print(f"Error generating QR code: {e}")
            return None