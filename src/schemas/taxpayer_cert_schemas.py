from pydantic import BaseModel, Field
from typing import Optional
from .response_schema import SuccessResponse

class TaxpayerCertRequest(BaseModel):
    url: str = Field(..., description="图片URL", example="https://xuntian-cloud-prod.obs.cn-south-1.myhuaweicloud.com/7/taxpayer/esigntest%E6%83%A0%E5%B7%9ETCL%E5%85%89%E4%BC%8F%E7%A7%91%E6%8A%80%E6%9C%89%E9%99%90%E5%85%AC%E5%8F%B8PAAB.png")

class TaxpayerCertResult(BaseModel):
    credit_code: str = Field(..., alias="creditCode", description="统一社会信用代码")
    company_name: str = Field(..., alias="companyName", description="公司名称")
    taxpayer_type: str = Field(..., alias="taxpayerType", description="纳税人类型")

    class Config:
        populate_by_name = True

class TaxpayerCertResponse(SuccessResponse):
    data: TaxpayerCertResult | None = None