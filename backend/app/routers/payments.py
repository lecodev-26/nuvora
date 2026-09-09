from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database.config import get_db
from app.models.db_models import User
from app.services.auth import get_current_user
from app.services.stripe_service import (
    create_checkout_session,
    handle_webhook,
    activate_service,
    get_service_status
)
import os

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("/create-checkout-session")
def create_session(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crea una sesión de pago en Stripe.
    Devuelve la URL de checkout.
    """
    try:
        frontend_url = os.getenv("FRONTEND_URL", "https://nuvora-chi.vercel.app")
        session_url = create_checkout_session(current_user.email, frontend_url)
        return {"url": session_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Webhook de Stripe para confirmar pagos.
    Solo escucha checkout.session.completed.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Falta firma de Stripe")

    try:
        event = handle_webhook(payload, sig_header)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Procesar solo eventos de pago completado
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_email = session.get("metadata", {}).get("user_email")

        if not user_email:
            raise HTTPException(status_code=400, detail="Email no encontrado en metadata")

        # Activar servicio para el usuario
        try:
            result = activate_service(db, user_email)
            print(f"✅ Servicio activado para {user_email}")
            return {"status": "success", "message": "Servicio activado"}
        except Exception as e:
            print(f"❌ Error al activar servicio: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return {"status": "ignored"}

@router.get("/status")
def get_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Devuelve el estado del servicio del usuario actual.
    """
    status_info = get_service_status(current_user)
    return status_info
