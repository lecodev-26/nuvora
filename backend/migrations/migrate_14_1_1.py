"""
Migración 14.1.1 — Nuvora Core Universal
==========================================
Objetivo:
- Rellenar bot.user_id a partir de bot.owner_email (JOIN con users)
- Rellenar bot.business_name a partir de bot.restaurant_name
- Rellenar bot.nicho_id = "otro" si está vacío
- Rellenar bot.is_active = True si está vacío
- Rellenar bot.is_published = False si está vacío
- Rellenar bot.answer_mode = "strict" si está vacío
- Marcar memories existentes como is_confirmed = True y source = "manual"
- Rellenar conversations existentes con channel = "widget"

IMPORTANTE: NO elimina campos antiguos.
Es idempotente: se puede ejecutar varias veces sin efectos secundarios.
"""

import sys
import os

# Añadir el directorio raíz al path para importar los modelos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.config import SessionLocal, engine, Base
from app.models.db_models import Bot, Memory, User, Conversation


def migrate():
    print("=" * 60)
    print("🚀 Migración 14.1.1 — Nuvora Core Universal")
    print("=" * 60)

    db = SessionLocal()
    try:
        # ------------------------------------------------------------
        # 1. Rellenar bot.user_id desde owner_email
        # ------------------------------------------------------------
        print("\n📌 Paso 1: Migrando owner_email → user_id...")
        bots_without_user = db.query(Bot).filter(Bot.user_id.is_(None)).all()
        migrated_user = 0
        for bot in bots_without_user:
            if bot.owner_email:
                user = db.query(User).filter(User.email == bot.owner_email).first()
                if user:
                    bot.user_id = user.id
                    migrated_user += 1
                else:
                    print(f"   ⚠️  Bot {bot.id}: no se encontró user con email {bot.owner_email}")
            else:
                print(f"   ⚠️  Bot {bot.id}: sin owner_email")
        db.commit()
        print(f"   ✅ {migrated_user} bots actualizados con user_id")

        # ------------------------------------------------------------
        # 2. Rellenar bot.business_name desde restaurant_name
        # ------------------------------------------------------------
        print("\n📌 Paso 2: Migrando restaurant_name → business_name...")
        bots_without_business = db.query(Bot).filter(Bot.business_name.is_(None)).all()
        migrated_business = 0
        for bot in bots_without_business:
            if bot.restaurant_name:
                bot.business_name = bot.restaurant_name
                migrated_business += 1
        db.commit()
        print(f"   ✅ {migrated_business} bots actualizados con business_name")

        # ------------------------------------------------------------
        # 3. Rellenar nicho_id = "otro" si vacío
        # ------------------------------------------------------------
        print("\n📌 Paso 3: Rellenando nicho_id por defecto...")
        bots_without_nicho = db.query(Bot).filter(
            (Bot.nicho_id.is_(None)) | (Bot.nicho_id == "")
        ).all()
        for bot in bots_without_nicho:
            bot.nicho_id = "otro"
        db.commit()
        print(f"   ✅ {len(bots_without_nicho)} bots actualizados con nicho_id")

        # ------------------------------------------------------------
        # 4. Rellenar is_active = True si vacío
        # ------------------------------------------------------------
        print("\n📌 Paso 4: Rellenando is_active...")
        bots_without_active = db.query(Bot).filter(Bot.is_active.is_(None)).all()
        for bot in bots_without_active:
            bot.is_active = True
        db.commit()
        print(f"   ✅ {len(bots_without_active)} bots actualizados con is_active")

        # ------------------------------------------------------------
        # 5. Rellenar is_published = False si vacío
        # ------------------------------------------------------------
        print("\n📌 Paso 5: Rellenando is_published...")
        bots_without_published = db.query(Bot).filter(Bot.is_published.is_(None)).all()
        for bot in bots_without_published:
            bot.is_published = False
        db.commit()
        print(f"   ✅ {len(bots_without_published)} bots actualizados con is_published")

        # ------------------------------------------------------------
        # 6. Rellenar answer_mode = "strict" si vacío
        # ------------------------------------------------------------
        print("\n📌 Paso 6: Rellenando answer_mode...")
        bots_without_mode = db.query(Bot).filter(
            (Bot.answer_mode.is_(None)) | (Bot.answer_mode == "")
        ).all()
        for bot in bots_without_mode:
            bot.answer_mode = "strict"
        db.commit()
        print(f"   ✅ {len(bots_without_mode)} bots actualizados con answer_mode")

        # ------------------------------------------------------------
        # 7. Marcar memories como confirmadas y source=manual
        # ------------------------------------------------------------
        print("\n📌 Paso 7: Confirmando memorias existentes...")
        memories_to_update = db.query(Memory).filter(Memory.is_confirmed.is_(None)).all()
        for mem in memories_to_update:
            mem.is_confirmed = True
            if not mem.source:
                mem.source = "manual"
        db.commit()
        print(f"   ✅ {len(memories_to_update)} memorias confirmadas")

        # ------------------------------------------------------------
        # 8. Rellenar channel = "widget" en conversaciones
        # ------------------------------------------------------------
        print("\n📌 Paso 8: Rellenando channel en conversaciones...")
        convs_to_update = db.query(Conversation).filter(
            (Conversation.channel.is_(None)) | (Conversation.channel == "")
        ).all()
        for conv in convs_to_update:
            conv.channel = "widget"
        db.commit()
        print(f"   ✅ {len(convs_to_update)} conversaciones actualizadas con channel")

        print("\n" + "=" * 60)
        print("🎉 Migración 14.1.1 completada correctamente")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error durante la migración: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Primero, crear las nuevas columnas si no existen (SQLite)
    print("🔧 Actualizando esquema de la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("✅ Esquema actualizado")

    # Ejecutar la migración de datos
    migrate()
