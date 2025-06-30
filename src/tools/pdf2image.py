import fitz  # PyMuPDF
import requests
import os
from pathlib import Path
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
import tempfile
from typing import List, Union, Optional, Dict, Any, Callable
import logging

# 配置日志
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class PdfToImageConverter:
    """PDF转图片转换器，支持本地PDF和网络PDF转换为图片"""
    
    def __init__(
        self,
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        scale_factor: float = 2.0,
        workers: int = 4,
        timeout: int = 15,
        temp_dir: str = None
    ):
        """
        初始化PDF转图片转换器
        
        Args:
            user_agent: HTTP请求的User-Agent
            scale_factor: 图片缩放因子
            workers: 并行处理的线程数
            timeout: 网络请求超时时间(秒)
            temp_dir: 临时文件存储目录
        """
        self.user_agent = user_agent
        self.scale_factor = scale_factor
        self.workers = workers
        self.timeout = timeout
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.common_headers = {"User-Agent": self.user_agent}
        
        # 初始化临时目录
        self._init_temp_dir()
    
    def _init_temp_dir(self) -> None:
        """初始化临时目录"""
        try:
            Path(self.temp_dir).mkdir(parents=True, exist_ok=True)
            logger.info(f"临时目录已初始化: {self.temp_dir}")
        except Exception as e:
            logger.error(f"初始化临时目录失败: {str(e)}")
            self.temp_dir = tempfile.gettempdir()
            logger.warning(f"使用默认临时目录: {self.temp_dir}")
    
    def _download_pdf(self, pdf_url: str) -> bytes:
        """下载PDF内容，统一处理网络请求和错误"""
        try:
            logger.info(f"开始下载: {pdf_url}")
            response = requests.get(
                pdf_url, 
                headers=self.common_headers, 
                stream=True, 
                timeout=self.timeout
            )
            response.raise_for_status()
            logger.info(f"下载成功: {pdf_url}，大小: {len(response.content)} bytes")
            return response.content
        except requests.exceptions.ConnectionError as e:
            logger.error(f"连接失败: {pdf_url}, 错误: {str(e)}")
        except requests.exceptions.Timeout as e:
            logger.error(f"请求超时: {pdf_url}, 错误: {str(e)}")
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP错误 ({response.status_code}): {pdf_url}, 错误: {str(e)}")
        except Exception as e:
            logger.error(f"下载失败: {pdf_url}, 错误: {str(e)}")
        return b""
    
    def _pdf_to_images(
        self, 
        pdf_content: bytes, 
        output_dir: Optional[str] = None, 
        scale_factor: float = None
    ) -> Union[List[str], List[bytes]]:
        """
        将PDF内容转换为图片
        
        Args:
            pdf_content: PDF文件内容字节流
            output_dir: 输出目录，如果为None则返回图片字节流
            scale_factor: 缩放因子，默认为初始化时的设置
        
        Returns:
            如果指定了输出目录，返回图片路径列表；否则返回图片字节流列表
        """
        results = []
        scale = scale_factor or self.scale_factor
        
        try:
            with fitz.open(stream=pdf_content, filetype="pdf") as doc:
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    matrix = fitz.Matrix(scale, scale)
                    pix = page.get_pixmap(matrix=matrix)
                    
                    if output_dir:
                        # 保存到文件
                        image_path = os.path.join(output_dir, f"page_{page_num+1}.png")
                        pix.save(image_path)
                        results.append(image_path)
                    else:
                        # 保存到内存
                        with BytesIO() as img_buffer:
                            img_buffer.write(pix.tobytes(output="png"))
                            results.append(img_buffer.getvalue())
            logger.info(f"PDF转换完成，共生成{len(results)}张图片")
            return results
        except Exception as e:
            logger.error(f"PDF转换失败: {str(e)}")
            return results
    
    def local_pdf_to_images(
        self, 
        pdf_path: str, 
        output_dir: str = "output", 
        scale_factor: float = None
    ) -> List[str]:
        """
        本地PDF文件转图片
        
        Args:
            pdf_path: 本地PDF文件路径
            output_dir: 输出图片目录
            scale_factor: 缩放倍数，默认为初始化时的设置
        
        Returns:
            生成的图片路径列表
        """
        if not os.path.exists(pdf_path):
            logger.error(f"PDF文件不存在: {pdf_path}")
            return []
        
        output_dir = os.path.abspath(output_dir)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"开始转换本地PDF: {pdf_path} 到目录: {output_dir}")
        
        try:
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            return self._pdf_to_images(pdf_content, output_dir, scale_factor)
        except Exception as e:
            logger.error(f"处理本地PDF时出错: {str(e)}")
            return []
    
    def url_to_images(
        self, 
        pdf_url: str, 
        output_dir: str = "output", 
        scale_factor: float = None
    ) -> List[str]:
        """
        PDF URL转图片
        
        Args:
            pdf_url: PDF文件URL
            output_dir: 输出图片目录
            scale_factor: 缩放倍数，默认为初始化时的设置
        
        Returns:
            生成的图片路径列表
        """
        logger.info(f"开始处理URL: {pdf_url}")
        pdf_content = self._download_pdf(pdf_url)
        
        if not pdf_content:
            logger.error(f"未获取到PDF内容: {pdf_url}")
            return []
        
        output_dir = os.path.abspath(output_dir)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        return self._pdf_to_images(pdf_content, output_dir, scale_factor)
    
    def urls_to_images(
        self, 
        pdf_urls: List[str], 
        output_dir: str = "output", 
        workers: int = None,
        parallel: bool = True
    ) -> List[str]:
        """
        批量处理多个PDF URL转图片
        
        Args:
            pdf_urls: PDF文件URL列表
            output_dir: 输出图片根目录
            workers: 并行工作线程数，默认为初始化时的设置
            parallel: 是否并行处理
        
        Returns:
            生成的所有图片路径列表
        """
        if not pdf_urls:
            logger.warning("PDF URL列表为空，无法处理")
            return []
        
        all_image_paths = []
        use_workers = workers or self.workers
        logger.info(f"开始批量处理{len(pdf_urls)}个PDF URL，输出目录: {output_dir}")
        
        def process_url(url, idx):
            url_output_dir = os.path.join(output_dir, f"pdf_{idx+1}")
            Path(url_output_dir).mkdir(parents=True, exist_ok=True)
            try:
                return self.url_to_images(url, url_output_dir)
            except Exception as e:
                logger.error(f"处理URL {url} 时出错: {str(e)}")
                return []
        
        if parallel and len(pdf_urls) > 1:
            with ThreadPoolExecutor(max_workers=use_workers) as executor:
                futures = [executor.submit(process_url, url, idx) for idx, url in enumerate(pdf_urls)]
                for future in futures:
                    all_image_paths.extend(future.result())
            logger.info(f"并行处理完成，共生成{len(all_image_paths)}张图片")
        else:
            for idx, url in enumerate(pdf_urls):
                all_image_paths.extend(process_url(url, idx))
            logger.info(f"顺序处理完成，共生成{len(all_image_paths)}张图片")
        
        return all_image_paths
    
    def url_to_image_streams(
        self, 
        pdf_url: str, 
        scale_factor: float = None
    ) -> List[bytes]:
        """
        PDF URL转图片文件流
        
        Args:
            pdf_url: PDF文件URL
            scale_factor: 缩放倍数，默认为初始化时的设置
        
        Returns:
            图片文件流列表
        """
        logger.info(f"开始转换URL为图片流: {pdf_url}")
        pdf_content = self._download_pdf(pdf_url)
        
        if not pdf_content:
            logger.error(f"未获取到PDF内容: {pdf_url}")
            return []
        
        return self._pdf_to_images(pdf_content, None, scale_factor)
    
    def urls_to_image_streams(
        self, 
        pdf_urls: List[str], 
        scale_factor: float = None, 
        workers: int = None
    ) -> List[bytes]:
        """
        批量处理多个PDF URL转图片文件流
        
        Args:
            pdf_urls: PDF文件URL列表
            scale_factor: 缩放倍数，默认为初始化时的设置
            workers: 并行工作线程数，默认为初始化时的设置
        
        Returns:
            生成的所有图片文件流列表
        """
        if not pdf_urls:
            logger.warning("PDF URL列表为空，无法处理")
            return []
        
        all_image_streams = []
        use_workers = workers or self.workers
        logger.info(f"开始批量转换{len(pdf_urls)}个PDF URL为图片流")
        
        def process_single_url(url):
            try:
                return self.url_to_image_streams(url, scale_factor)
            except Exception as e:
                logger.error(f"处理URL {url} 时出错: {str(e)}")
                return []
        
        with ThreadPoolExecutor(max_workers=use_workers) as executor:
            results = executor.map(process_single_url, pdf_urls)
            for result in results:
                all_image_streams.extend(result)
        
        logger.info(f"批量转换完成，共生成{len(all_image_streams)}个图片流")
        return all_image_streams


# 测试用例部分
if __name__ == "__main__":
    # 创建转换器实例
    converter = PdfToImageConverter(
        scale_factor=2.0,
        workers=2,
        timeout=20
    )
    
    # 测试用例1: 本地PDF转换
    def test_local_pdf_conversion():
        print("\n=== 测试用例1: 本地PDF转换 ===")
        local_pdf_path = "test.pdf"  # 替换为实际本地PDF路径
        if os.path.exists(local_pdf_path):
            try:
                images = converter.local_pdf_to_images(local_pdf_path, "local_output")
                print(f"生成{len(images)}张图片，保存至local_output目录")
                for img in images[:2]:  # 打印前2个路径
                    print(f"- {os.path.basename(img)}")
            except Exception as e:
                print(f"测试过程中出错: {str(e)}")
        else:
            print("跳过测试: 未找到本地测试PDF文件")

    # 测试用例2: 单URL PDF转换
    def test_single_url_conversion():
        print("\n=== 测试用例2: 单URL PDF转换 ===")
        test_url = "https://xuntian-pv.tcl.com/group1/M00/5E/1B/rBAAOGg4P6SABizqAAXiFV_wwKU981.pdf"
        try:
            images = converter.url_to_images(test_url, "url_output")
            print(f"生成{len(images)}张图片，保存至url_output目录")
        except Exception as e:
            print(f"测试过程中出错: {str(e)}")

    # 测试用例3: 批量URL顺序转换
    def test_batch_urls_sequential():
        print("\n=== 测试用例3: 批量URL顺序转换 ===")
        test_urls = [
            "https://xuntian-pv.tcl.com/group1/M00/2C/72/rBAAOGdzuwGATMSIAAJAsZYWXKI601.pdf",
            "https://xuntian-pv.tcl.com/group1/M00/2C/64/rBAAOGdzkjmAeKrxAAJAsZYWXKI702.pdf"
        ]
        try:
            images = converter.urls_to_images(test_urls, "batch_sequential", parallel=False)
            print(f"共生成{len(images)}张图片，保存至batch_sequential目录")
        except Exception as e:
            print(f"测试过程中出错: {str(e)}")

    # 测试用例4: 批量URL并行转换
    def test_batch_urls_parallel():
        print("\n=== 测试用例4: 批量URL并行转换 ===")
        test_urls = [
            "https://xuntian-pv.tcl.com/group1/M00/2C/72/rBAAOGdzuwGATMSIAAJAsZYWXKI601.pdf",
            "https://xuntian-pv.tcl.com/group1/M00/2C/64/rBAAOGdzkjmAeKrxAAJAsZYWXKI702.pdf"
        ]
        try:
            images = converter.urls_to_images(test_urls, "batch_parallel", workers=2)
            print(f"共生成{len(images)}张图片，保存至batch_parallel目录")
        except Exception as e:
            print(f"测试过程中出错: {str(e)}")

    # 测试用例5: 单URL转文件流
    def test_url_to_image_streams():
        print("\n=== 测试用例5: 单URL转文件流 ===")
        test_url = "https://xuntian-pv.tcl.com/group1/M00/5E/1B/rBAAOGg4P6SABizqAAXiFV_wwKU981.pdf"
        try:
            streams = converter.url_to_image_streams(test_url)
            print(f"生成{len(streams)}个图片流，第一个流大小: {len(streams[0])} bytes")
        except Exception as e:
            print(f"测试过程中出错: {str(e)}")

    # 测试用例6: 批量URL转文件流
    def test_batch_urls_to_image_streams():
        print("\n=== 测试用例6: 批量URL转文件流 ===")
        test_urls = [
            "https://xuntian-pv.tcl.com/group1/M00/2C/72/rBAAOGdzuwGATMSIAAJAsZYWXKI601.pdf",
            "https://xuntian-pv.tcl.com/group1/M00/2C/64/rBAAOGdzkjmAeKrxAAJAsZYWXKI702.pdf"
        ]
        try:
            streams = converter.urls_to_image_streams(test_urls, workers=2)
            print(f"共生成{len(streams)}个图片流")
        except Exception as e:
            print(f"测试过程中出错: {str(e)}")

    # 执行所有测试用例
    test_local_pdf_conversion()
    test_single_url_conversion()
    test_batch_urls_sequential()
    test_batch_urls_parallel()
    test_url_to_image_streams()
    test_batch_urls_to_image_streams()