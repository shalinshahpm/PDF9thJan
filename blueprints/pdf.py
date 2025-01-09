import io
from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from models import PDFFile
from app import db

pdf_bp = Blueprint('pdf', __name__, url_prefix='/pdf')

@pdf_bp.route('/operations')
@login_required
def operations():
    return render_template('pdf/operations.html')

@pdf_bp.route('/merge', methods=['POST'])
@login_required
def merge_pdfs():
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files provided'}), 400

    files = request.files.getlist('files[]')
    merger = PdfMerger()

    try:
        for file in files:
            pdf_content = io.BytesIO(file.read())
            merger.append(pdf_content)

        output = io.BytesIO()
        merger.write(output)
        output.seek(0)

        # Save operation record
        pdf_file = PDFFile(
            filename='merged.pdf',
            user_id=current_user.id,
            operation_type='merge',
            status='completed'
        )
        db.session.add(pdf_file)
        db.session.commit()

        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='merged.pdf'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@pdf_bp.route('/split', methods=['POST'])
@login_required
def split_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    try:
        pdf = PdfReader(io.BytesIO(file.read()))
        writer = PdfWriter()

        page_ranges = request.form.get('ranges', '').split(',')
        for range_str in page_ranges:
            start, end = map(int, range_str.split('-'))
            for page_num in range(start - 1, min(end, len(pdf.pages))):
                writer.add_page(pdf.pages[page_num])

        output = io.BytesIO()
        writer.write(output)
        output.seek(0)

        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='split.pdf'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@pdf_bp.route('/watermark', methods=['POST'])
@login_required
def watermark_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    watermark_text = request.form.get('text', 'Watermark')

    try:
        # Create watermark
        watermark_buffer = io.BytesIO()
        c = canvas.Canvas(watermark_buffer, pagesize=letter)
        c.setFont("Helvetica", 60)
        c.setFillAlpha(0.3)  # Set transparency
        c.translate(300, 400)
        c.rotate(45)
        c.drawString(0, 0, watermark_text)
        c.save()
        watermark_buffer.seek(0)

        # Apply watermark to PDF
        pdf = PdfReader(io.BytesIO(file.read()))
        watermark_pdf = PdfReader(watermark_buffer)
        writer = PdfWriter()

        for page in pdf.pages:
            page.merge_page(watermark_pdf.pages[0])
            writer.add_page(page)

        output = io.BytesIO()
        writer.write(output)
        output.seek(0)

        # Save operation record
        pdf_file = PDFFile(
            filename='watermarked.pdf',
            user_id=current_user.id,
            operation_type='watermark',
            status='completed'
        )
        db.session.add(pdf_file)
        db.session.commit()

        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='watermarked.pdf'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@pdf_bp.route('/encrypt', methods=['POST'])
@login_required
def encrypt_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    password = request.form.get('password')

    if not password:
        return jsonify({'error': 'Password is required'}), 400

    try:
        pdf = PdfReader(io.BytesIO(file.read()))
        writer = PdfWriter()

        for page in pdf.pages:
            writer.add_page(page)

        writer.encrypt(password)
        output = io.BytesIO()
        writer.write(output)
        output.seek(0)

        # Save operation record
        pdf_file = PDFFile(
            filename='encrypted.pdf',
            user_id=current_user.id,
            operation_type='encrypt',
            status='completed'
        )
        db.session.add(pdf_file)
        db.session.commit()

        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='encrypted.pdf'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@pdf_bp.route('/compress', methods=['POST'])
@login_required
def compress_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    try:
        pdf = PdfReader(io.BytesIO(file.read()))
        writer = PdfWriter()

        for page in pdf.pages:
            # Apply multiple compression techniques
            page.compress_content_streams()  # Compress page contents

            # Remove unnecessary metadata
            if '/Metadata' in page:
                del page['/Metadata']

            # Reduce image quality if present
            for key in page:
                if '/XObject' in page[key]:
                    xObject = page[key]['/XObject'].get_object()
                    for obj in xObject:
                        if xObject[obj]['/Subtype'] == '/Image':
                            if '/Filter' in xObject[obj]:
                                if '/ColorSpace' in xObject[obj]:
                                    if xObject[obj]['/ColorSpace'] == '/DeviceRGB':
                                        xObject[obj]['/ColorSpace'] = '/DeviceGray'
                                if '/BitsPerComponent' in xObject[obj]:
                                    if xObject[obj]['/BitsPerComponent'] > 4:
                                        xObject[obj]['/BitsPerComponent'] = 4

            writer.add_page(page)

        # Set compression parameters
        output = io.BytesIO()
        writer._compress = True
        writer.write(output)
        output.seek(0)

        # Save operation record
        pdf_file = PDFFile(
            filename='compressed.pdf',
            user_id=current_user.id,
            operation_type='compress',
            status='completed'
        )
        db.session.add(pdf_file)
        db.session.commit()

        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='compressed.pdf'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500