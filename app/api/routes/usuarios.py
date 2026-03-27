from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user, require_role
from app.services.usuario import UsuarioService
from app.schemas.schemas import UsuarioCreate, UsuarioResponse, UsuarioUpdate
from app.models.enums import UserRole

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])
service = UsuarioService()


@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def create_usuario(payload: UsuarioCreate, db: Session = Depends(get_db)):
    try:
        return service.create(db, payload.dict())
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/", response_model=list[UsuarioResponse])
def list_usuarios(db: Session = Depends(get_db), current_user = Depends(require_role([UserRole.ADMIN]))):
    return service.get_all(db)


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def get_usuario(usuario_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    try:
        return service.get_by_id(db, usuario_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.put("/{usuario_id}", response_model=UsuarioResponse)
def update_usuario(usuario_id: int, payload: UsuarioUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    try:
        return service.update(db, usuario_id, payload.dict(exclude_unset=True), current_user.rol)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/{usuario_id}")
def delete_usuario(usuario_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    try:
        return service.delete(db, usuario_id, current_user.rol)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
