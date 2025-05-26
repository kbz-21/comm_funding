import cv2
import numpy as np
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
import os
import logging
import unicodedata
import pytesseract
import platform
from django.core.files.storage import default_storage
from fuzzywuzzy import fuzz
from .models import Hospital, DiseaseType, DoctorStamp

logger = logging.getLogger(__name__)



# Explicitly set the path to Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
 

def normalize(text):
    """Normalize text for comparison."""
    return unicodedata.normalize("NFKD", text.lower().strip())

def extract_text_from_pdf(pdf_path):
    """Extract text from all pages of the PDF using PyPDF2, with OCR fallback."""
    text = ''
    try:
        logger.debug(f"Attempting text extraction from {pdf_path} using PyPDF2")
        with open(pdf_path, 'rb') as file:
            reader = PdfReader(file)
            for page_num, page in enumerate(reader.pages, 1):
                extracted = page.extract_text() or ''
                logger.debug(f"Extracted text from page {page_num} (PyPDF2): {extracted}")
                text += extracted
        # Trigger OCR if no text or no hospital found
        approved_hospitals = [normalize(name) for name in Hospital.objects.values_list('name', flat=True)]
        if not text.strip() or not any(hospital in normalize(text) for hospital in approved_hospitals):
            logger.debug("Falling back to OCR for text extraction")
            images = convert_from_path(pdf_path)
            for page_num, image in enumerate(images, 1):
                ocr_text = pytesseract.image_to_string(image)
                logger.debug(f"Extracted text from page {page_num} (OCR): {ocr_text}")
                text += ocr_text
    except Exception as e:
        logger.error(f"Text extraction error: {str(e)}")
    logger.debug(f"Final extracted text: {text}")
    return text

def pdf_to_images(pdf_path):
    """Convert PDF pages to images using pdf2image."""
    try:
        images = convert_from_path(pdf_path)
        logger.debug(f"Converted {pdf_path} to {len(images)} images")
        return images
    except Exception as e:
        logger.error(f"PDF to images conversion error: {str(e)}")
        return []

def extract_stamp_from_image(image, approved_stamps):
    """Search for a stamp in the entire image and extract it."""
    try:
        image_np = np.array(image)
        image_cv = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        gray = cv2.equalizeHist(gray)

        debug_page_path = f'debug_page_{os.getpid()}.png'
        cv2.imwrite(debug_page_path, gray)
        logger.debug(f"Saved debug page image: {debug_page_path}")

        stamp_path = None
        max_val = 0
        best_match = None

        for stamp in approved_stamps:
            if not hasattr(stamp, 'image') or not stamp.image:
                logger.warning(f"Invalid stamp object in database: {stamp}")
                continue

            template_path = stamp.image.path
            if not os.path.exists(template_path):
                logger.error(f"Template image not found: {template_path}")
                continue

            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                logger.error(f"Failed to load template image: {template_path}")
                continue

            template = cv2.GaussianBlur(template, (5, 5), 0)
            template = cv2.equalizeHist(template)

            scales = [0.5, 0.75, 1.0, 1.25, 1.5]
            for scale in scales:
                scaled_template = cv2.resize(template, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
                if scaled_template.shape[0] > gray.shape[0] or scaled_template.shape[1] > gray.shape[1]:
                    continue

                result = cv2.matchTemplate(gray, scaled_template, cv2.TM_CCOEFF_NORMED)
                min_val, curr_max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                if curr_max_val > max_val and curr_max_val > 0.4:
                    max_val = curr_max_val
                    best_match = (max_loc, scaled_template.shape, template_path, scale)

        if best_match:
            (x, y), (h, w), template_path, scale = best_match
            stamp_region = image_cv[y:y+h, x:x+w]
            stamp_path = f'temp_stamp_{os.getpid()}.jpg'
            cv2.imwrite(stamp_path, stamp_region)
            logger.debug(f"Extracted stamp via template matching: {stamp_path}, confidence: {max_val}, scale: {scale}")
            return stamp_path

        logger.debug("No stamp found via template matching, trying contour detection")
        edges = cv2.Canny(gray, 30, 100)  # Fixed: Use gray, adjusted thresholds
        logger.debug(f"Detected edges with shape: {edges.shape}")
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in sorted(contours, key=cv2.contourArea, reverse=True):
            area = cv2.contourArea(contour)
            if 1000 < area < 100000:
                x, y, w, h = cv2.boundingRect(contour)
                stamp_region = image_cv[y:y+h, x:x+w]
                stamp_path = f'temp_stamp_{os.getpid()}.jpg'
                cv2.imwrite(stamp_path, stamp_region)
                logger.debug(f"Extracted stamp via contour detection: {stamp_path}, area: {area}")
                return stamp_path

        logger.debug("No stamp found in image")
        return None

    except Exception as e:
        logger.error(f"Stamp extraction error: {str(e)}")
        return None

def validate_pdf(pdf_file):
    """Validate a Medical campaign PDF for hospital, disease, and stamp."""
    try:
        temp_pdf_path = default_storage.save(f'temp/{pdf_file.name}', pdf_file)
        temp_pdf_full_path = os.path.join(default_storage.location, temp_pdf_path)
        logger.debug(f"Saved temporary PDF: {temp_pdf_full_path}")

        text = extract_text_from_pdf(temp_pdf_full_path)
        normalized_text = normalize(text)
        logger.debug(f"Normalized extracted text: {normalized_text}")

        approved_hospitals = [normalize(name) for name in Hospital.objects.values_list('name', flat=True)]
        approved_diseases = [normalize(name) for name in DiseaseType.objects.values_list('name', flat=True)]
        logger.debug(f"Approved hospitals: {approved_hospitals}")
        logger.debug(f"Approved diseases: {approved_diseases}")

        hospital_found = False
        for hospital in approved_hospitals:
            if fuzz.partial_ratio(hospital, normalized_text) > 90:  # Aligned with PDFValidationView
                hospital_found = True
                logger.debug(f"Matched hospital: {hospital}")
                break
        if not hospital_found:
            logger.debug("No hospital matched. Checking substrings:")
            for hospital in approved_hospitals:
                logger.debug(f"Checking hospital: {hospital}, In text: {hospital in normalized_text}")

        disease_found = False
        for disease in approved_diseases:
            if fuzz.partial_ratio(disease, normalized_text) > 90:  # Fuzzy matching for diseases
                disease_found = True
                logger.debug(f"Matched disease: {disease}")
                break
        logger.debug(f"Hospital found: {hospital_found}, Disease found: {disease_found}")

        images = pdf_to_images(temp_pdf_full_path)
        stamp_matched = False
        approved_stamps = DoctorStamp.objects.all()
        for image in images:
            stamp_path = extract_stamp_from_image(image, approved_stamps)
            if stamp_path:
                logger.debug(f"Attempting to match stamp: {stamp_path}")
                if match_stamp(stamp_path, approved_stamps):
                    stamp_matched = True
                    logger.debug(f"Stamp matched: {stamp_path}")
                    os.remove(stamp_path)
                    break
                os.remove(stamp_path)
            else:
                logger.debug("No stamp found in image")

        default_storage.delete(temp_pdf_path)

        if hospital_found and disease_found and stamp_matched:
            logger.info("PDF validation successful")
            return {'result': 'ACCEPTED', 'reason': 'Valid hospital, disease, and stamp found'}
        else:
            result = 'REJECTED'
            reasons = []
            if not hospital_found:
                reasons.append("This Hospital is not among the officially authorized hospitals")
            if not disease_found:
                reasons.append("The disease type is not recognized as an eligible condition")
            if not stamp_matched:
                reasons.append("This doctor is not an authorized approver")
            reason = ', '.join(reasons)
            logger.warning(f"PDF validation failed: {reason}")
            return {'result': result, 'reason': reason}

    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        if 'temp_pdf_path' in locals():
            default_storage.delete(temp_pdf_path)
        return {'result': 'REJECTED', 'reason': f'Validation error: {str(e)}'}

def match_stamp(extracted_stamp_path, approved_stamps):
    """Match the extracted stamp against approved stamps using ORB."""
    try:
        if not os.path.exists(extracted_stamp_path):
            logger.error(f"Extracted stamp file not found: {extracted_stamp_path}")
            return False

        extracted_img = cv2.imread(extracted_stamp_path, cv2.IMREAD_GRAYSCALE)
        if extracted_img is None:
            logger.error(f"Failed to load extracted stamp image: {extracted_stamp_path}")
            return False

        extracted_img = cv2.GaussianBlur(extracted_img, (5, 5), 0)
        extracted_img = cv2.equalizeHist(extracted_img)

        orb = cv2.ORB_create(nfeatures=2000)
        kp1, des1 = orb.detectAndCompute(extracted_img, None)
        if des1 is None:
            logger.debug("No keypoints detected in extracted stamp")
            return False

        for stamp in approved_stamps:
            if not hasattr(stamp, 'image') or not stamp.image:
                logger.warning(f"Invalid stamp object in database: {stamp}")
                continue

            approved_img_path = stamp.image.path
            if not os.path.exists(approved_img_path):
                logger.error(f"Approved stamp image not found: {approved_img_path}")
                continue

            approved_img = cv2.imread(approved_img_path, cv2.IMREAD_GRAYSCALE)
            if approved_img is None:
                logger.error(f"Failed to load approved stamp image: {approved_img_path}")
                continue

            approved_img = cv2.GaussianBlur(approved_img, (5, 5), 0)
            approved_img = cv2.equalizeHist(approved_img)

            kp2, des2 = orb.detectAndCompute(approved_img, None)
            if des2 is None:
                logger.debug(f"No keypoints detected in approved stamp: {approved_img_path}")
                continue

            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bf.match(des1, des2)
            logger.debug(f"Found {len(matches)} matches for stamp: {approved_img_path}")

            if len(matches) > 1:  # Further lowered threshold
                logger.debug(f"Stamp matched with {len(matches)} matches: {approved_img_path}")
                return True

        logger.debug("No matching stamp found")
        return False

    except Exception as e:
        logger.error(f"Stamp matching error: {str(e)}")
        return False