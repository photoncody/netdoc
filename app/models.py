from sqlalchemy import Column, Integer, String, Boolean, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class DeviceImage(Base):
    __tablename__ = "device_images"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    filename = Column(String)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    device = relationship("Device", back_populates="images")

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    device_type = Column(String)
    location = Column(String)
    network = Column(String, nullable=True)
    manufacturer = Column(String, nullable=True)
    model = Column(String, nullable=True)
    serial_number = Column(String, nullable=True)
    
    ip_address = Column(String, nullable=True)
    subnet_mask = Column(String, nullable=True)
    default_gateway = Column(String, nullable=True)
    primary_dns = Column(String, nullable=True)
    secondary_dns = Column(String, nullable=True)
    dns_name = Column(String, nullable=True)
    mac_address = Column(String, nullable=True)

    os = Column(String, nullable=True)
    virtual_host = Column(String, nullable=True)
    guest_name = Column(String, nullable=True)
    
    # New Linking Fields
    uplink_device = Column(String, nullable=True) # Stores the NAME of the connected device
    uplink_notes = Column(String, nullable=True)  # Stores port info e.g. "Port 1 to Port 24"

    # Flags
    flag_dhcp = Column(Boolean, default=False)
    flag_public_ip = Column(Boolean, default=False)
    flag_oob = Column(Boolean, default=False)
    flag_wireless = Column(Boolean, default=False)
    flag_tailscale = Column(Boolean, default=False)

    # Custom Fields
    custom_fields = Column(JSON, default=list)
    location_manual_override = Column(Boolean, default=False)

    images = relationship("DeviceImage", back_populates="device", cascade="all, delete-orphan")
class LocationNetwork(Base):
    __tablename__ = "location_networks"

    id = Column(Integer, primary_key=True, index=True)
    location = Column(String, index=True)
    subnet = Column(String)
    description = Column(String, nullable=True)
