from app.core.database import SessionLocal
from app.schemas.component import ComponentCreate
from app.services.component_service import ComponentService

SEED = [
    ComponentCreate(
        name="AMD Ryzen 5 5600", category="cpu", brand="AMD", price=899.00,
        specs={"cores": 6, "threads": 12, "socket": "AM4", "tdp": "65W"},
    ),
    ComponentCreate(
        name="Intel Core i5-12400F", category="cpu", brand="Intel", price=899.00,
        specs={"cores": 6, "threads": 12, "socket": "LGA1700", "tdp": "65W"},
    ),
    ComponentCreate(
        name="AMD Ryzen 7 7800X3D", category="cpu", brand="AMD", price=2499.00,
        specs={"cores": 8, "threads": 16, "socket": "AM5", "tdp": "120W"},
    ),
    ComponentCreate(
        name="NVIDIA GeForce RTX 4060", category="gpu", brand="NVIDIA", price=1999.00,
        specs={"vram": "8GB GDDR6", "interface": "PCIe 4.0"},
    ),
    ComponentCreate(
        name="AMD Radeon RX 7600", category="gpu", brand="AMD", price=1799.00,
        specs={"vram": "8GB GDDR6", "interface": "PCIe 4.0"},
    ),
    ComponentCreate(
        name="NVIDIA GeForce RTX 4070 Super", category="gpu", brand="NVIDIA", price=4599.00,
        specs={"vram": "12GB GDDR6X", "interface": "PCIe 4.0"},
    ),
    ComponentCreate(
        name="Corsair Vengeance 16GB DDR5", category="ram", brand="Corsair", price=399.00,
        specs={"capacity": "16GB", "type": "DDR5", "kit": "2x8GB", "speed": "6000MHz"},
    ),
    ComponentCreate(
        name="Kingston Fury 32GB DDR4", category="ram", brand="Kingston", price=549.00,
        specs={"capacity": "32GB", "type": "DDR4", "kit": "2x16GB", "speed": "3200MHz"},
    ),
    ComponentCreate(
        name="Samsung 980 Pro 1TB NVMe", category="storage", brand="Samsung", price=649.00,
        specs={"capacity": "1TB", "interface": "NVMe M.2", "form_factor": "2280"},
    ),
    ComponentCreate(
        name="WD Blue 1TB SATA", category="storage", brand="Western Digital", price=299.00,
        specs={"capacity": "1TB", "interface": "SATA III", "form_factor": "3.5\""},
    ),
]


def seed() -> None:
    db = SessionLocal()
    try:
        service = ComponentService(db)
        if service.list():
            print("Catálogo já populado. Nada a fazer.")
            return
        for component in SEED:
            service.create(component)
        print(f"Seed concluído: {len(SEED)} componentes inseridos.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()