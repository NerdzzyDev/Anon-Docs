from __future__ import annotations

from pydantic import BaseModel


class AnonymizeOptions(BaseModel):
    fio: bool = True
    passport: bool = True
    birthdate: bool = True
    snils_inn: bool = True
    phone: bool = True
    banking: bool = True
