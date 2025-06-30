from pdf2image import PdfToImageConverter
from ocr_cert import OCRCertInfoExtractor
from io import BytesIO

def pdf_urls_to_ocr_results(pdf_urls: list, scale_factor: float = 2.0, workers: int = 2):
    """
    从 PDF URL 列表获取 OCR 识别结果
    
    :param pdf_urls: PDF 文件 URL 列表
    :param scale_factor: 缩放倍数，默认为初始化时的设置
    :param workers: 并行工作线程数，默认为初始化时的设置
    :return: OCR 识别结果的字典列表
    """
    # 初始化 PDF 转图片转换器
    pdf_converter = PdfToImageConverter(scale_factor=scale_factor, workers=workers)
    # 初始化 OCR 信息提取器
    ocr_extractor = OCRCertInfoExtractor()

    # 将 PDF URL 列表转换为图片文件流列表
    image_streams = pdf_converter.urls_to_image_streams(pdf_urls, scale_factor, workers)

    ocr_results = []
    # 对每个图片文件流进行 OCR 识别
    for image_stream in image_streams:
        try:
            # 将字节流转换为文件流对象
            with BytesIO(image_stream) as img_buffer:
                # 进行 OCR 识别
                result = ocr_extractor.from_file(img_buffer)
            ocr_results.append(result)
        except Exception as e:
            print(f"OCR 识别出错: {str(e)}")

    return ocr_results

# 测试代码
if __name__ == "__main__":
    test_pdf_urls = [
        "https://xuntian-pv.tcl.com/group1/M00/2C/72/rBAAOGdzuwGATMSIAAJAsZYWXKI601.pdf",
        "https://xuntian-pv.tcl.com/group1/M00/2C/64/rBAAOGdzkjmAeKrxAAJAsZYWXKI702.pdf"
    ]
    results = pdf_urls_to_ocr_results(test_pdf_urls)
    print("OCR 识别结果:", results)