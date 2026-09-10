"""
Auditoría de seguridad — Migración 14.1.1
==========================================
Este script NO modifica la base de datos.
Solo analiza y reporta posibles problemas.

Ejecutar ANTES de la migración real.
"""

import sys
import os
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.config import SessionLocal
from app.models.db_models import Bot, User


def audit():
    print("=" * 70)
    print("🔍 Auditoría de seguridad — Migración 14.1.1")
    print("=" * 70)

    db = SessionLocal()
    try:
        # ------------------------------------------------------------
        # Totales actuales
        # ------------------------------------------------------------
        total_bots = db.query(Bot).count()
        total_users = db.query(User).count()
        print(f"\n📊 Estado actual:")
        print(f"   Total usuarios: {total_users}")
        print(f"   Total bots:     {total_bots}")

        if total_bots == 0:
            print("\n✅ No hay bots que migrar. Migración trivial.")
            print("=" * 70)
            return

        # ------------------------------------------------------------
        # 1. Bots sin owner_email
        # ------------------------------------------------------------
        bots_sin_email = db.query(Bot).filter(
            (Bot.owner_email.is_(None)) | (Bot.owner_email == "")
        ).all()
        print(f"\n📌 Caso 1: Bots sin owner_email:")
        print(f"   Cantidad: {len(bots_sin_email)}")
        for b in bots_sin_email:
            print(f"   - Bot id={b.id} name='{b.name}'")

        # ------------------------------------------------------------
        # 2. Bots con owner_email que no existe en users
        # ------------------------------------------------------------
        bots_huerfanos = []
        for bot in db.query(Bot).filter(
            Bot.owner_email.isnot(None),
            Bot.owner_email != ""
        ).all():
            email_normalizado = bot.owner_email.strip().lower()
            user = db.query(User).filter(
                text("LOWER(TRIM(email)) = :e")
            ).params(e=email_normalizado).first()
            if not user:
                bots_huerfanos.append((bot.id, bot.name, bot.owner_email))

        print(f"\n📌 Caso 2: Bots con owner_email sin usuario correspondiente:")
        print(f"   Cantidad: {len(bots_huerfanos)}")
        for bot_id, name, email in bots_huerfanos:
            print(f"   - Bot id={bot_id} name='{name}' email='{email}'")

        # ------------------------------------------------------------
        # 3. Emails duplicados en users
        # ------------------------------------------------------------
        try:
            dup_query = text("""
                SELECT LOWER(TRIM(email)) AS email_norm, COUNT(*) AS cnt
                FROM users
                GROUP BY LOWER(TRIM(email))
                HAVING COUNT(*) > 1
            """)
            duplicados = db.execute(dup_query).fetchall()
        except Exception as e:
            print(f"\n⚠️  No se pudo ejecutar la query de duplicados: {e}")
            duplicados = []

        print(f"\n📌 Caso 3: Emails duplicados en tabla users:")
        print(f"   Cantidad de emails duplicados: {len(duplicados)}")
        for row in duplicados:
            print(f"   - email='{row.email_norm}' aparece {row.cnt} veces")

        # ------------------------------------------------------------
        # 4. Bots con user_id ya asignado
        # ------------------------------------------------------------
        bots_con_user_id = db.query(Bot).filter(Bot.user_id.isnot(None)).count()
        print(f"\n📌 Caso 4: Bots que YA tienen user_id asignado:")
        print(f"   Cantidad: {bots_con_user_id}")
        print(f"   (Estos no se tocarán durante la migración)")

        # ------------------------------------------------------------
        # 5. Bots que quedarían con user_id = NULL tras migración
        # ------------------------------------------------------------
        bots_quedarian_null = []
        for bot in db.query(Bot).filter(Bot.user_id.is_(None)).all():
            if not bot.owner_email:
                bots_quedarian_null.append((bot.id, bot.name, "sin owner_email"))
                continue
            email_normalizado = bot.owner_email.strip().lower()
            user = db.query(User).filter(
                text("LOWER(TRIM(email)) = :e")
            ).params(e=email_normalizado).first()
            if not user:
                bots_quedarian_null.append((bot.id, bot.name, "email sin usuario"))

        print(f"\n📌 Caso 5: Bots que quedarían con user_id = NULL:")
        print(f"   Cantidad: {len(bots_quedarian_null)}")
        for bot_id, name, motivo in bots_quedarian_null:
            print(f"   - Bot id={bot_id} name='{name}' motivo='{motivo}'")

        # ------------------------------------------------------------
        # 6. Verificar integridad de FKs existentes
        # ------------------------------------------------------------
        try:
            bots_fk_rota = db.execute(text("""
                SELECT b.id, b.user_id
                FROM bots b
                LEFT JOIN users u ON u.id = b.user_id
                WHERE b.user_id IS NOT NULL AND u.id IS NULL
            """)).fetchall()
        except Exception:
            bots_fk_rota = []

        print(f"\n📌 Caso 6: Bots con user_id apuntando a user inexistente (FK rota):")
        print(f"   Cantidad: {len(bots_fk_rota)}")
        for row in bots_fk_rota:
            print(f"   - Bot id={row.id} user_id={row.user_id}")

        # ------------------------------------------------------------
        # RESUMEN FINAL
        # ------------------------------------------------------------
        print("\n" + "=" * 70)
        print("📋 RESUMEN DE LA AUDITORÍA")
        print("=" * 70)
        print(f"   Bots totales:                              {total_bots}")
        print(f"   Bots sin owner_email:                      {len(bots_sin_email)}")
        print(f"   Bots con email huérfano:                   {len(bots_huerfanos)}")
        print(f"   Emails duplicados en users:                {len(duplicados)}")
        print(f"   Bots que quedarían con user_id=NULL:       {len(bots_quedarian_null)}")
        print(f"   Bots con FK rota:                          {len(bots_fk_rota)}")

        # ------------------------------------------------------------
        # DECISIÓN
        # ------------------------------------------------------------
        print("\n" + "=" * 70)
        if len(duplicados) > 0:
            print("🛑 ABORTAR: Hay emails duplicados en 'users'.")
            print("   La migración asignaría user_id de forma ambigua.")
            print("   → Resolver duplicados antes de migrar.")
        elif len(bots_fk_rota) > 0:
            print("🛑 ABORTAR: Hay bots con FK rota (user_id inexistente).")
            print("   → Reparar FKs antes de migrar.")
        elif len(bots_quedarian_null) > 0:
            print("⚠️  ADVERTENCIA: Algunos bots quedarían con user_id = NULL.")
            print("   La migración puede continuar, pero esos bots quedarán")
            print("   sin dueño válido hasta que se resuelva manualmente.")
        else:
            print("✅ SEGURO: Todos los bots pueden migrarse correctamente.")
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    audit()
