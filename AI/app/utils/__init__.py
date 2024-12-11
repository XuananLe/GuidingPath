from ast import List
import re
import openai
from openai import OpenAI
import os
import logging
from fpdf import FPDF
import asyncio
from config import config

def segment_text_by_sentence(text):
    sentence_boundaries = re.finditer(r'(?<=[.!?])\s+', text)
    boundaries_indices = [boundary.start() for boundary in sentence_boundaries]
    
    segments = []
    start = 0
    for boundary_index in boundaries_indices:
        segments.append(text[start:boundary_index + 1].strip())
        start = boundary_index + 1
    segments.append(text[start:].strip())

    return segments


def create_pdf(text: str, output_path: str):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("FreeSerif",fname="FreeSerif.ttf", uni=True)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("FreeSerif", size=12)
    pdf.multi_cell(0, 10, text)
    pdf.output(output_path)

async def create_pdf_async(text: str, pdf_path: str):
    await asyncio.to_thread(create_pdf, text, pdf_path)
    

def format_response_distance_estimate_with_openai(response, trascribe ,base64_image):
    try:
        if response == None or len(response) == 0:
            return "Hiện tại không có vật thể nào được phát hiện"
            
        if not config.OPENAI_API_KEY:
            logging.error("OpenAI API key is missing")
            return str(response)

        logging.info(f"Processing response: {response}")

        openai.api_key = config.OPENAI_API_KEY
        client = OpenAI()

        system_prompt = """
            Nhiệm vụ của bạn là chuyển đổi dữ liệu phát hiện đối tượng thành báo cáo chi tiết và dễ hiểu bằng tiếng Việt, bao gồm các yếu tố sau:
            
        """

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {
                        "type" : "text",
                        "text" : str(response)
                    }, 
                    {
                        "type": "text",
                        "text": trascribe
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]}
            ],
            max_tokens=300,
            temperature=0.7,
            top_p=0.9,
        )

        formatted_response = completion.choices[0].message.content.strip()
        
        logging.info(f"Formatted response: {formatted_response}")

        return formatted_response

    except openai.OpenAIError as openai_error:
        logging.error(f"OpenAI API Error: {openai_error}")
        return f"Lỗi xử lý: {str(openai_error)}"

    except Exception as e:
        # Catch-all for any other unexpected errors
        logging.error(f"Unexpected error in distance estimation: {e}")
        return str(response)
    

def format_product_information_with_openai(response):
    try:
        if not config.OPENAI_API_KEY:
            logging.error("OpenAI API key is missing")
            return response
        openai.api_key = config.OPENAI_API_KEY
        client = OpenAI()

        system_prompt = """
        Nhiệm vụ của bạn là chuyển đổi thông tin sản phẩm thành một đoạn văn mô tả chi tiết, dễ hiểu và hấp dẫn bằng tiếng Việt.

        Yêu cầu chi tiết:
        - Cung cấp mô tả đầy đủ về sản phẩm
        - Giải thích các thông số dinh dưỡng một cách dễ hiểu
        - Đánh giá giá trị dinh dưỡng và tiềm năng sử dụng
        - Sử dụng ngôn ngữ thân thiện, chuyên nghiệp

        Định dạng mẫu:
        "[Tên sản phẩm] của thương hiệu [Tên thương hiệu] - Một trải nghiệm ẩm thực độc đáo!

        Chi tiết sản phẩm:
        - Loại sản phẩm: [Mô tả chi tiết]
        - Khối lượng: [Khối lượng]
        - Danh mục: [Các danh mục phù hợp]

        Giá trị dinh dưỡng (Phân tích chuyên sâu):
        [Phân tích chi tiết về năng lượng, chất béo, carbohydrate, đạm]
        """

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": str(response)}
            ],
            max_tokens=300,
            temperature=0.7,
            top_p=0.9,
        )

        formatted_description = completion.choices[0].message.content.strip()
        
        return formatted_description

    except openai.OpenAIError as openai_error:
        logging.error(f"OpenAI API Error: {openai_error}")
        return f"Lỗi xử lý thông tin sản phẩm: {str(openai_error)}"

    except Exception as e:
        logging.error(f"Unexpected error in product information processing: {e}")
        return str(response)