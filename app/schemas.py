from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime

class DeviceImage(BaseModel):
    id: int
    device_id: int
    filename: str
    uploaded_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CustomField(BaseModel):
    label: str
    value: str

class DeviceBase(BaseModel):
    name: str
    device_type: str
    location: str
    network: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    
    ip_address: Optional[str] = None
    subnet_mask: Optional[str] = None
    default_gateway: Optional[str] = None
    primary_dns: Optional[str] = None
    secondary_dns: Optional[str] = None
    dns_name: Optional[str] = None
    mac_address: Optional[str] = None

    os: Optional[str] = None
    virtual_host: Optional[str] = None
    guest_name: Optional[str] = None
    
    # New Linking Fields
    uplink_device: Optional[str] = None
    uplink_notes: Optional[str] = None

    flag_dhcp: bool = False
    flag_public_ip: bool = False
    flag_oob: bool = False
    flag_wireless: bool = False
    flag_tailscale: bool = False
    custom_fields: List[CustomField] = []
    location_manual_override: bool = False

class DeviceCreate(DeviceBase):
    pass

class Device(DeviceBase):
    id: int
    images: List[DeviceImage] = []
    class Config:
        from_attributes = True

class LocationNetworkBase(BaseModel):
    location: str
    subnet: str
    description: Optional[str] = None

class LocationNetworkCreate(LocationNetworkBase):
    pass

class LocationNetwork(LocationNetworkBase):
    id: int
    class Config:
        from_attributes = True
