import stripe
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.db_models import User

# Configurar Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Precios en céntimos (29,99 € = 2999)
PRICE_AMOUNT = 2999
CURRENCY = "eur"

def create_checkout_session(user_email: str, frontend_url: str) -> str:
    """
    Crea una sesión de pago en Stripe y devuelve la URL de checkout.
    """
    try:
        # Buscar o crear cliente en Stripe
        customers = stripe.Customer.list(email=user_email, limit=1)
        if customers.data:
            customer = customers.data[0]
        else:
            customer = stripe.Customer.create(
                email=user_email,
                metadata={"source": "nuvora"}
            )

        # Crear sesión de checkout (pago único)
        session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": CURRENCY,
                    "product_data": {
                        "name": "Nuvora - 12 meses de servicio",
                        "description": "Acceso completo a Nuvora durante 12 meses"
                    },
                    "unit_amount": PRICE_AMOUNT,
                },
                "quantity": 1,
            }],
            mode="payment",  # Pago único, no suscripción
            success_url=f"{frontend_url}/dashboard?payment=success",
            cancel_url=f"{frontend_url}/dashboard?payment=cancel",
            metadata={
                "user_email": user_email,
                "service": "nuvora",
                "duration_months": "12"
            }
        )
        return session.url

    except stripe.error.StripeError as e:
        print(f"Error de Stripe: {e}")
        raise Exception(f"Error al crear sesión de pago: {str(e)}")

def handle_webhook(payload: bytes, sig_header: str) -> dict:
    """
    Procesa un webhook de Stripe.
    Devuelve el evento procesado.
    """
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
        return event
    except ValueError as e:
        raise Exception(f"Payload inválido: {e}")
    except stripe.error.SignatureVerificationError as e:
        raise Exception(f"Firma inválida: {e}")

def activate_service(db: Session, user_email: str):
    """
    Activa el servicio de Nuvora para un usuario.
    - Establece service_status = "active"
    - Registra fecha de pago
    - Establece expiration_date = hoy + 365 días
    - Limpia los campos de trial
    """
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise Exception(f"Usuario no encontrado: {user_email}")

    now = datetime.utcnow()
    expiration = now + timedelta(days=365)

    user.service_status = "active"
    user.payment_date = now
    user.expiration_date = expiration
    user.trial_start = None
    user.trial_end = None

    db.commit()
    db.refresh(user)

    return {
        "user_email": user.email,
        "status": user.service_status,
        "payment_date": user.payment_date,
        "expiration_date": user.expiration_date
    }

def get_service_status(user: User) -> dict:
    """
    Devuelve el estado del servicio de un usuario.
    """
    now = datetime.utcnow()

    # Si está en trial
    if user.service_status == "trial" and user.trial_end:
        days_left = (user.trial_end - now).days
        if days_left < 0:
            # Trial expirado, cambiar a expired
            user.service_status = "expired"
            db = user._sa_instance_state.session
            if db:
                db.commit()
            days_left = 0
        return {
            "status": "trial",
            "trial_days_left": max(0, days_left),
            "days_left": None,
            "expiration_date": None,
            "payment_date": None
        }

    # Si está activo
    if user.service_status == "active" and user.expiration_date:
        days_left = (user.expiration_date - now).days
        if days_left < 0:
            # Servicio expirado
            user.service_status = "expired"
            db = user._sa_instance_state.session
            if db:
                db.commit()
            days_left = 0
        return {
            "status": "active",
            "trial_days_left": None,
            "days_left": max(0, days_left),
            "expiration_date": user.expiration_date,
            "payment_date": user.payment_date
        }

    # Estado por defecto
    return {
        "status": user.service_status,
        "trial_days_left": None,
        "days_left": None,
        "expiration_date": user.expiration_date,
        "payment_date": user.payment_date
    }
