import io
import logging
import zipfile
import json
from PIL import Image
from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import Color, HexColor
from models import PDFFile
from app import db

pdf_bp = Blueprint('pdf', __name__, url_prefix='/pdf')

# Configure logging for PDF operations
logger = logging.getLogger(__name__)

@pdf_bp.errorhandler(Exception)
def handle_error(error):
    logger.error(f"Operation error: {str(error)}")
    return jsonify({'error': str(error)}), 500

@pdf_bp.route('/compress', methods=['POST'])
@login_required
def compress_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    try:
        # Read input file size for comparison
        input_data = file.read()
        input_size = len(input_data)
        logger.info(f"Input PDF size: {input_size} bytes")

        pdf = PdfReader(io.BytesIO(input_data))
        writer = PdfWriter()

        for page_num, page in enumerate(pdf.pages, 1):
            logger.info(f"Processing page {page_num}")

            # Compress content streams
            page.compress_content_streams()

            # Remove unnecessary elements
            unnecessary_keys = ['/Metadata', '/StructParents', '/StructTreeRoot', '/AcroForm']
            for key in unnecessary_keys:
                if key in page:
                    del page[key]

            # Process images
            if '/Resources' in page:
                resources = page['/Resources']
                if '/XObject' in resources:
                    xObject = resources['/XObject'].get_object()

                    for obj in xObject:
                        if xObject[obj]['/Subtype'] == '/Image':
                            image = xObject[obj]
                            # Convert RGB to Grayscale
                            if '/ColorSpace' in image and image['/ColorSpace'] == '/DeviceRGB':
                                image['/ColorSpace'] = '/DeviceGray'

                            # Reduce bits per component
                            if '/BitsPerComponent' in image:
                                image['/BitsPerComponent'] = 4

                            # Apply maximum compression to images
                            if '/Filter' in image:
                                if isinstance(image['/Filter'], list):
                                    image['/Filter'] = ['/FlateDecode']
                                else:
                                    image['/Filter'] = '/FlateDecode'

            writer.add_page(page)

        # Set maximum compression
        output = io.BytesIO()
        writer._compress = True
        writer.write(output)
        output.seek(0)

        # Compare sizes
        output_size = output.getbuffer().nbytes
        compression_ratio = (1 - (output_size / input_size)) * 100
        logger.info(f"Output PDF size: {output_size} bytes")
        logger.info(f"Compression ratio: {compression_ratio:.2f}%")

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
        logger.error(f"Compression error: {str(e)}")
        return jsonify({'error': str(e)}), 500

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

@pdf_bp.route('/to-images', methods=['POST'])
@login_required
def pdf_to_images():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    format = request.form.get('format', 'png')
    dpi = int(request.form.get('dpi', 300))

    try:
        pdf = PdfReader(io.BytesIO(file.read()))
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for page_num in range(len(pdf.pages)):
                # Convert PDF page to image
                page = pdf.pages[page_num]

                # Create a bytes buffer for the image
                image_buffer = io.BytesIO()

                # Convert PDF page to image using Pillow
                pil_image = page.to_image(resolution=dpi)
                pil_image.save(image_buffer, format=format.upper())
                image_buffer.seek(0)

                # Add image to zip file
                filename = f'page_{page_num + 1}.{format}'
                zip_file.writestr(filename, image_buffer.getvalue())

        zip_buffer.seek(0)

        # Save operation record
        pdf_file = PDFFile(
            filename='pdf_images.zip',
            user_id=current_user.id,
            operation_type='to_images',
            status='completed'
        )
        db.session.add(pdf_file)
        db.session.commit()

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='pdf_images.zip'
        )

    except Exception as e:
        logger.error(f"PDF to Images error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pdf_bp.route('/rotate', methods=['POST'])
@login_required
def rotate_pages():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    angle = int(request.form.get('angle', 90))
    pages = request.form.get('pages', '')

    try:
        pdf = PdfReader(io.BytesIO(file.read()))
        writer = PdfWriter()

        # Parse page ranges
        if pages:
            page_list = []
            for range_str in pages.split(','):
                if '-' in range_str:
                    start, end = map(int, range_str.split('-'))
                    page_list.extend(range(start - 1, min(end, len(pdf.pages))))
                else:
                    page_list.append(int(range_str) - 1)
        else:
            page_list = range(len(pdf.pages))

        # Rotate specified pages
        for i in range(len(pdf.pages)):
            page = pdf.pages[i]
            if i in page_list:
                page.rotate(angle)
            writer.add_page(page)

        output = io.BytesIO()
        writer.write(output)
        output.seek(0)

        # Save operation record
        pdf_file = PDFFile(
            filename='rotated.pdf',
            user_id=current_user.id,
            operation_type='rotate',
            status='completed'
        )
        db.session.add(pdf_file)
        db.session.commit()

        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='rotated.pdf'
        )

    except Exception as e:
        logger.error(f"Rotation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pdf_bp.route('/add-text', methods=['POST'])
@login_required
def add_text():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    text = request.form.get('text', '')
    x = float(request.form.get('x', 100))
    y = float(request.form.get('y', 100))
    color = request.form.get('color', '#000000')

    try:
        # Create PDF with text
        text_layer = io.BytesIO()
        c = canvas.Canvas(text_layer, pagesize=letter)

        # Convert hex color to RGB
        color = HexColor(color)
        c.setFillColor(color)

        c.drawString(x, y, text)
        c.save()
        text_layer.seek(0)

        # Merge text layer with original PDF
        pdf = PdfReader(io.BytesIO(file.read()))
        text_pdf = PdfReader(text_layer)
        writer = PdfWriter()

        for page in pdf.pages:
            page.merge_page(text_pdf.pages[0])
            writer.add_page(page)

        output = io.BytesIO()
        writer.write(output)
        output.seek(0)

        # Save operation record
        pdf_file = PDFFile(
            filename='text_added.pdf',
            user_id=current_user.id,
            operation_type='add_text',
            status='completed'
        )
        db.session.add(pdf_file)
        db.session.commit()

        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='text_added.pdf'
        )

    except Exception as e:
        logger.error(f"Add text error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pdf_bp.route('/extract-text', methods=['POST'])
@login_required
def extract_text():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        pages = request.form.get('pages', '')
        format = request.form.get('format', 'txt')

        pdf = PdfReader(io.BytesIO(file.read()))

        # Parse page ranges
        if pages:
            page_list = []
            for range_str in pages.split(','):
                if '-' in range_str:
                    start, end = map(int, range_str.split('-'))
                    page_list.extend(range(start - 1, min(end, len(pdf.pages))))
                else:
                    page_list.append(int(range_str) - 1)
        else:
            page_list = range(len(pdf.pages))

        # Extract text
        text_content = {}
        for i in page_list:
            if i < len(pdf.pages):
                text_content[f'page_{i+1}'] = pdf.pages[i].extract_text()

        output = io.BytesIO()

        if format == 'json':
            json_data = json.dumps(text_content, indent=2)
            output.write(json_data.encode('utf-8'))
            mimetype = 'application/json'
            filename = 'extracted_text.json'
        else:
            # Format as plain text
            text = '\n\n'.join([f'=== Page {k} ===\n{v}' for k, v in text_content.items()])
            output.write(text.encode('utf-8'))
            mimetype = 'text/plain'
            filename = 'extracted_text.txt'

        output.seek(0)

        # Save operation record
        pdf_file = PDFFile(
            filename=filename,
            user_id=current_user.id,
            operation_type='extract_text',
            status='completed'
        )
        db.session.add(pdf_file)
        db.session.commit()

        response = send_file(
            output,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
        response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
        return response

    except Exception as e:
        logger.error(f"Text extraction error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pdf_bp.route('/organize', methods=['POST'])
@login_required
def organize_pages():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    layout = request.form.get('layout', '1x1')

    try:
        pdf = PdfReader(io.BytesIO(file.read()))
        writer = PdfWriter()

        # Parse layout
        rows, cols = map(int, layout.split('x'))

        # Calculate pages per sheet
        pages_per_sheet = rows * cols
        total_pages = len(pdf.pages)

        # Process pages in groups
        for i in range(0, total_pages, pages_per_sheet):
            # Create a new page with the specified layout
            output_page = writer.add_blank_page(
                width=letter[0] * cols,
                height=letter[1] * rows
            )

            # Add pages to the layout
            for j in range(pages_per_sheet):
                if i + j < total_pages:
                    page = pdf.pages[i + j]
                    # Calculate position in the grid
                    row = j // cols
                    col = j % cols
                    # Translate and scale the page
                    page.scale_to(1.0/cols, 1.0/rows)
                    page.translate(col * letter[0], (rows - 1 - row) * letter[1])
                    # Merge into output page
                    output_page.merge_page(page)

        output = io.BytesIO()
        writer.write(output)
        output.seek(0)

        # Save operation record
        pdf_file = PDFFile(
            filename='organized.pdf',
            user_id=current_user.id,
            operation_type='organize',
            status='completed'
        )
        db.session.add(pdf_file)
        db.session.commit()

        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='organized.pdf'
        )

    except Exception as e:
        logger.error(f"Page organization error: {str(e)}")
        return jsonify({'error': str(e)}), 500