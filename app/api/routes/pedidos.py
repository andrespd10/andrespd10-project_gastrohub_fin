from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user, require_role
from app.services.pedido import PedidoService
from app.schemas.schemas import PedidoCreate, PedidoResponse, PedidoUpdate, DetallePedidoCreate, PagoResponse
from app.models.enums import UserRole

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])
service = PedidoService()


@router.post("/", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
def create_pedido(payload: PedidoCreate, db: Session = Depends(get_db), current_user = Depends(require_role([UserRole.MESERO, UserRole.ADMIN]))):
    try:
        return service.create(db, payload.dict())
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/", response_model=list[PedidoResponse])
def list_pedidos(db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    return service.get_all(db)


@router.get("/{pedido_id}", response_model=PedidoResponse)
def get_pedido(pedido_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    try:
        return service.get_by_id(db, pedido_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.put("/{pedido_id}", response_model=PedidoResponse)
def update_pedido(pedido_id: int, payload: PedidoUpdate, db: Session = Depends(get_db), current_user = Depends(require_role([UserRole.MESERO, UserRole.ADMIN]))):
    try:
        return service.update(db, pedido_id, payload.dict(exclude_unset=True))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/{pedido_id}")
def delete_pedido(pedido_id: int, db: Session = Depends(get_db), current_user = Depends(require_role([UserRole.ADMIN]))):
    try:
        return service.delete(db, pedido_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{pedido_id}/detalles", response_model=DetallePedidoCreate, status_code=status.HTTP_201_CREATED)
def add_detalle(pedido_id: int, payload: DetallePedidoCreate, db: Session = Depends(get_db), current_user = Depends(require_role([UserRole.MESERO]))):
    try:
        return service.add_detalle(db, pedido_id, payload.dict())
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.patch("/detalles/{detalle_id}", response_model=DetallePedidoCreate)
def update_detalle(detalle_id: int, payload: DetallePedidoCreate, db: Session = Depends(get_db), current_user = Depends(require_role([UserRole.COCINA, UserRole.MESERO]))):
    try:
        return service.update_detalle(db, detalle_id, payload.dict(exclude_unset=True))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{pedido_id}/cerrar", response_model=PedidoResponse)
def cerrar_pedido(pedido_id: int, db: Session = Depends(get_db), current_user = Depends(require_role([UserRole.MESERO, UserRole.ADMIN]))):
    try:
        return service.cerrar_pedido(db, pedido_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{pedido_id}/pago", response_model=PagoResponse)
def create_pago(pedido_id: int, db: Session = Depends(get_db), current_user = Depends(require_role([UserRole.ADMIN]))):
    try:
        return service.create_pago(db, pedido_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{pedido_id}/total")
def get_total(pedido_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    return {"total": service.calculate_pago_total(db, pedido_id)}
