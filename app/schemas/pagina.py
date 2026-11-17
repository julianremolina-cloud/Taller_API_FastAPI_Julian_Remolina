from pydantic import BaseModel


class Pagina[T](BaseModel):
    items: list[T]
    total: int
    skip: int
    limit: int
