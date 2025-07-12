from fastapi import APIRouter, Body
from src.schemas.taxpayer_cert_schemas import TaxpayerCertResponse, TaxpayerCertRequest
from src.services.taxpayer_cert_service import TaxpayerCertService

router = APIRouter(prefix="/api/taxpayer-cert", tags=["纳税人证明识别接口"])

@router.post("/recognize-cert", response_model=TaxpayerCertResponse)
async def recognize_taxpayer_cert(request: TaxpayerCertRequest = Body(..., description="纳税人证明图片URL请求体")):
    """纳税人证明识别接口（POST请求）"""
    service = TaxpayerCertService()
    result = await service.recognize_taxpayer_cert(request.url)
    return TaxpayerCertResponse(data=result)