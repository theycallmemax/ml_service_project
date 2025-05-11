from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

# u0422u0438u043fu044b u0442u0440u0430u043du0437u0430u043au0446u0438u0439
class TransactionType(str, Enum):
    CREDIT = "credit"  # u043fu043eu043fu043eu043bu043du0435u043du0438u0435
    DEBIT = "debit"    # u0441u043fu0438u0441u0430u043du0438u0435

# u0411u0430u0437u043eu0432u0430u044f u0441u0445u0435u043cu0430 u0442u0440u0430u043du0437u0430u043au0446u0438u0438
class TransactionBase(BaseModel):
    amount: float = Field(..., gt=0)  # u0421u0443u043cu043cu0430 u0432u0441u0435u0433u0434u0430 u043fu043eu043bu043eu0436u0438u0442u0435u043bu044cu043du0430u044f
    transaction_type: TransactionType
    description: Optional[str] = None

# u0421u0445u0435u043cu0430 u0434u043bu044f u0441u043eu0437u0434u0430u043du0438u044f u0442u0440u0430u043du0437u0430u043au0446u0438u0438
class TransactionCreate(TransactionBase):
    pass

# u0421u0445u0435u043cu0430 u0434u043bu044f u043fu043eu043fu043eu043bu043du0435u043du0438u044f u0431u0430u043bu0430u043du0441u0430
class TopUpBalance(BaseModel):
    amount: float = Field(..., gt=0)  # u0421u0443u043cu043cu0430 u0434u043eu043bu0436u043du0430 u0431u044bu0442u044c u043fu043eu043bu043eu0436u0438u0442u0435u043bu044cu043du043eu0439

# u0421u0445u0435u043cu0430 u0434u043bu044f u043eu0442u043eu0431u0440u0430u0436u0435u043du0438u044f u0442u0440u0430u043du0437u0430u043au0446u0438u0438
class Transaction(TransactionBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True  # u0417u0430u043cu0435u043du0435u043du043e u0441 orm_mode
