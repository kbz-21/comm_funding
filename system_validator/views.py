from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Hospital, DiseaseType, DoctorStamp
from .utils import extract_text_from_pdf, pdf_to_images, extract_stamp_from_image, match_stamp
import os
import unicodedata
import logging
from fuzzywuzzy import fuzz

logger = logging.getLogger(__name__)

def normalize(text):
    """Normalize text for comparison."""
    return unicodedata.normalize("NFKD", text.lower().strip())

class PDFValidationView(APIView):
    def post(self, request):
        if 'pdf_file' not in request.FILES:
            return Response({'error': 'No PDF file provided'}, status=status.HTTP_400_BAD_REQUEST)

        pdf_file = request.FILES['pdf_file']
        pdf_path = 'temp.pdf'
        with open(pdf_path, 'wb') as f:
            for chunk in pdf_file.chunks():
                f.write(chunk)

        try:
            text = extract_text_from_pdf(pdf_path)
            normalized_text = normalize(text)
            logger.debug(f"Normalized extracted text: {normalized_text}")

            approved_hospitals = [normalize(name) for name in Hospital.objects.values_list('name', flat=True)]
            approved_diseases = [normalize(name) for name in DiseaseType.objects.values_list('name', flat=True)]
            logger.debug(f"Approved hospitals: {approved_hospitals}")
            logger.debug(f"Approved diseases: {approved_diseases}")

            hospital_found = False
            for hospital in approved_hospitals:
                if fuzz.partial_ratio(hospital, normalized_text) > 90:
                    hospital_found = True
                    logger.debug(f"Matched hospital: {hospital}")
                    break
            if not hospital_found:
                logger.debug("No hospital matched. Checking substrings:")
                for hospital in approved_hospitals:
                    logger.debug(f"Checking hospital: {hospital}, In text: {hospital in normalized_text}")

            disease_found = False
            for disease in approved_diseases:
                if fuzz.partial_ratio(disease, normalized_text) > 90:
                    disease_found = True
                    logger.debug(f"Matched disease: {disease}")
                    break
            logger.debug(f"Hospital found: {hospital_found}, Disease found: {disease_found}")

            images = pdf_to_images(pdf_path)
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

            if hospital_found and disease_found and stamp_matched:
                result = 'Your document has been "ACCEPTED"'
                reason = 'All requirements have been successfully met and verified.'
            else:
                result = 'Your document has been "REJECTED"'
                reason = []
                if not hospital_found:
                    reason.append('This Hospital is not among the officially authorized hospitals to issue medical support letters')
                if not disease_found:
                    reason.append('The submitted disease type is not recognized as one of the eligible critical conditions for medical support.')
                if not stamp_matched:
                    reason.append("This doctor is not recognized as an authorized approver for medical support.")
                reason = ', '.join(reason)

        except Exception as e:
            result = 'Error'
            reason = f'Processing failed: {str(e)}'
            logger.error(f"Validation error: {str(e)}")
        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

        return Response({'result': result, 'reason': reason})