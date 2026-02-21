import os
import secrets
import uuid
import shutil
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Request, Response, status
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from pydantic import BaseModel
import csv
import io
import codecs
import ipaddress 
from . import models, schemas, database

# Create DB tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="NetDoc API")

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# --- Authentication Configuration ---
ADMIN_USER = os.getenv("NETDOC_USER")
ADMIN_PASS = os.getenv("NETDOC_PASSWORD")
AUTH_ENABLED = bool(ADMIN_USER and ADMIN_PASS)
SESSION_TOKEN = secrets.token_hex(16) if AUTH_ENABLED else None

# --- Auto-Migration for Existing Users ---
@app.on_event("startup")
def perform_migrations():
    """Attempts to add new columns to existing DBs without full migration tool"""
    with database.engine.connect() as conn:
        try: conn.execute(text("ALTER TABLE devices ADD COLUMN dns_name VARCHAR")); conn.commit()
        except: pass
        try: conn.execute(text("ALTER TABLE devices ADD COLUMN serial_number VARCHAR")); conn.commit()
        except: pass
        try: conn.execute(text("ALTER TABLE devices ADD COLUMN mac_address VARCHAR")); conn.commit()
        except: pass
        try: conn.execute(text("ALTER TABLE devices ADD COLUMN flag_wireless BOOLEAN DEFAULT 0")); conn.commit()
        except: pass
        try: conn.execute(text("ALTER TABLE devices ADD COLUMN uplink_device VARCHAR")); conn.commit()
        except: pass
        try: conn.execute(text("ALTER TABLE devices ADD COLUMN uplink_notes VARCHAR")); conn.commit()
        except: pass
        try: conn.execute(text("ALTER TABLE devices ADD COLUMN flag_tailscale BOOLEAN DEFAULT 0")); conn.commit()
        except: pass

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def verify_auth(request: Request):
    if not AUTH_ENABLED: return True
    token = request.cookies.get("netdoc_session")
    if token != SESSION_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return True

class LoginRequest(BaseModel):
    username: str
    password: str

@app.get("/api/status")
def get_status(request: Request):
    is_logged_in = False
    if AUTH_ENABLED:
        token = request.cookies.get("netdoc_session")
        if token == SESSION_TOKEN: is_logged_in = True
    return { "auth_required": AUTH_ENABLED, "logged_in": is_logged_in or (not AUTH_ENABLED) }

@app.post("/api/login")
def login(creds: LoginRequest, response: Response):
    if not AUTH_ENABLED: return {"message": "Auth not enabled"}
    if creds.username == ADMIN_USER and creds.password == ADMIN_PASS:
        response.set_cookie(key="netdoc_session", value=SESSION_TOKEN, httponly=True, samesite="lax", max_age=86400 * 7)
        return {"message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/api/logout")
def logout(response: Response):
    response.delete_cookie("netdoc_session")
    return {"message": "Logged out"}

# --- CSV Import / Export ---

@app.get("/api/devices/export", dependencies=[Depends(verify_auth)])
def export_devices(db: Session = Depends(get_db)):
    devices = db.query(models.Device).all()
    output = io.StringIO()
    writer = csv.writer(output)
    
    headers = [
        "name", "device_type", "location", "manufacturer", "model", "serial_number", "os",
        "ip_address", "mac_address", "dns_name", "subnet_mask", "default_gateway", 
        "primary_dns", "secondary_dns", "virtual_host", "guest_name", 
        "uplink_device", "uplink_notes",
        "flag_dhcp", "flag_public_ip", "flag_oob", "flag_wireless", "flag_tailscale"
    ]
    writer.writerow(headers)
    
    for d in devices:
        writer.writerow([
            d.name, d.device_type, d.location, d.manufacturer, d.model, d.serial_number, d.os,
            d.ip_address, d.mac_address, d.dns_name, d.subnet_mask, d.default_gateway, 
            d.primary_dns, d.secondary_dns, d.virtual_host, d.guest_name,
            d.uplink_device, d.uplink_notes,
            d.flag_dhcp, d.flag_public_ip, d.flag_oob, d.flag_wireless, d.flag_tailscale
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=netdoc_export.csv"}
    )

@app.post("/api/devices/import", dependencies=[Depends(verify_auth)])
async def import_devices(file: UploadFile = File(...), db: Session = Depends(get_db)):
    reader = csv.DictReader(codecs.iterdecode(file.file, 'utf-8'))
    imported_count = 0
    updated_count = 0

    for row in reader:
        if not row.get("name"): continue
        def parse_bool(val): return str(val).lower() in ('true', '1', 'yes')

        db_device = db.query(models.Device).filter(models.Device.name == row["name"]).first()
        
        device_data = {
            "name": row.get("name"),
            "device_type": row.get("device_type", "Router"),
            "location": row.get("location", ""),
            "manufacturer": row.get("manufacturer"),
            "model": row.get("model"),
            "serial_number": row.get("serial_number"),
            "os": row.get("os"),
            "ip_address": row.get("ip_address"),
            "mac_address": row.get("mac_address"),
            "dns_name": row.get("dns_name"),
            "subnet_mask": row.get("subnet_mask"),
            "default_gateway": row.get("default_gateway"),
            "primary_dns": row.get("primary_dns"),
            "secondary_dns": row.get("secondary_dns"),
            "virtual_host": row.get("virtual_host"),
            "guest_name": row.get("guest_name"),
            "uplink_device": row.get("uplink_device"),
            "uplink_notes": row.get("uplink_notes"),
            "flag_dhcp": parse_bool(row.get("flag_dhcp")),
            "flag_public_ip": parse_bool(row.get("flag_public_ip")),
            "flag_oob": parse_bool(row.get("flag_oob")),
            "flag_wireless": parse_bool(row.get("flag_wireless")),
            "flag_tailscale": parse_bool(row.get("flag_tailscale"))
        }

        if db_device:
            for key, value in device_data.items(): setattr(db_device, key, value)
            updated_count += 1
        else:
            new_device = models.Device(**device_data)
            db.add(new_device)
            imported_count += 1
            
    db.commit()
    return {"message": f"Import successful. Created {imported_count}, Updated {updated_count}"}

# --- NEW SUBNET TOOL ENDPOINT ---
@app.get("/api/tools/subnet", dependencies=[Depends(verify_auth)])
def scan_subnet(cidr: str, db: Session = Depends(get_db)):
    try:
        # strict=False allows "192.168.1.50/24" to be treated as "192.168.1.0/24"
        network = ipaddress.ip_network(cidr, strict=False)
        
        # Limit to prevent browser crash (max /20)
        if network.num_addresses > 4096:
            raise HTTPException(status_code=400, detail="Range too large (Max /20 or 4096 IPs)")
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid CIDR format (e.g., 192.168.1.0/24)")

    devices = db.query(models.Device).filter(models.Device.ip_address.isnot(None)).all()
    # Normalize IP map keys and skip devices with empty IP addresses
    ip_map = {d.ip_address.strip(): d for d in devices if d.ip_address and d.ip_address.strip()}

    results = []
    
    # Identify Network and Broadcast Addresses
    net_addr = network.network_address
    broadcast_addr = network.broadcast_address

    for ip in network:
        ip_str = str(ip)
        device = ip_map.get(ip_str)
        
        status_val = "Free"
        if ip == net_addr: status_val = "Network"
        elif ip == broadcast_addr: status_val = "Broadcast"
        elif device: 
            if device.device_type == "Reserved":
                status_val = "Reserved"
            else:
                status_val = "Used"

        results.append({
            "ip": ip_str,
            "status": status_val,
            "device_name": device.name if device else None,
            "device_id": device.id if device else None,
            "type": device.device_type if device else None
        })
        
    return results

# --- CRUD Operations ---

@app.get("/api/devices", response_model=List[schemas.Device], dependencies=[Depends(verify_auth)])
def read_devices(skip: int = 0, limit: int = 1000, db: Session = Depends(get_db)):
    devices = db.query(models.Device).all()
    return devices

@app.post("/api/devices", response_model=schemas.Device, dependencies=[Depends(verify_auth)])
def create_device(device: schemas.DeviceCreate, db: Session = Depends(get_db)):
    db_device = models.Device(**device.dict())
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device

@app.put("/api/devices/{device_id}", response_model=schemas.Device, dependencies=[Depends(verify_auth)])
def update_device(device_id: int, device: schemas.DeviceCreate, db: Session = Depends(get_db)):
    db_device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if not db_device: raise HTTPException(status_code=404, detail="Device not found")
    for key, value in device.dict().items(): setattr(db_device, key, value)
    db.commit()
    db.refresh(db_device)
    return db_device

@app.delete("/api/devices/{device_id}", dependencies=[Depends(verify_auth)])
def delete_device(device_id: int, db: Session = Depends(get_db)):
    db_device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if not db_device: raise HTTPException(status_code=404, detail="Device not found")
    db.delete(db_device)
    db.commit()
    return {"ok": True}

# --- Image Upload Endpoints ---

UPLOAD_DIR = os.getenv("NETDOC_UPLOAD_DIR", "/data/uploads")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

@app.post("/api/devices/{device_id}/images", response_model=schemas.DeviceImage, dependencies=[Depends(verify_auth)])
def upload_device_image(device_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    db_device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if not db_device: raise HTTPException(status_code=404, detail="Device not found")

    # Validate extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file type. Allowed: jpg, jpeg, png, gif, webp")

    # Generate unique filename
    filename = f"{uuid.uuid4()}{file_ext}"

    # Ensure directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    db_image = models.DeviceImage(device_id=device_id, filename=filename)
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image

@app.get("/api/devices/{device_id}/images", response_model=List[schemas.DeviceImage], dependencies=[Depends(verify_auth)])
def list_device_images(device_id: int, db: Session = Depends(get_db)):
    db_device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if not db_device: raise HTTPException(status_code=404, detail="Device not found")
    return db_device.images

@app.delete("/api/images/{image_id}", dependencies=[Depends(verify_auth)])
def delete_device_image(image_id: int, db: Session = Depends(get_db)):
    db_image = db.query(models.DeviceImage).filter(models.DeviceImage.id == image_id).first()
    if not db_image: raise HTTPException(status_code=404, detail="Image not found")

    # Delete file from filesystem
    filepath = os.path.join(UPLOAD_DIR, db_image.filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    db.delete(db_image)
    db.commit()
    return {"ok": True}

# Ensure upload directory exists on startup
if not os.path.exists(UPLOAD_DIR):
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
    except OSError:
        print(f"Warning: Could not create upload directory {UPLOAD_DIR}")

# Mount uploads directory - MUST be before root mount
if os.path.exists(UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.mount("/", StaticFiles(directory="app/static", html=True), name="static")