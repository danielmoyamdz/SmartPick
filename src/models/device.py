from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any

@dataclass
class Device:
    """Base model for all electronic devices."""
    id: str
    name: str
    brand: str
    category: str
    release_date: Optional[datetime]
    price: Optional[float]
    specifications: Dict[str, Any]
    reviews: List[Dict[str, Any]]
    source: str
    source_url: str
    currency: str = "USD"
    last_updated: datetime = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert device to dictionary format."""
        return {
            "id": self.id,
            "name": self.name,
            "brand": self.brand,
            "category": self.category,
            "release_date": self.release_date.isoformat() if self.release_date else None,
            "price": self.price,
            "currency": self.currency,
            "specifications": self.specifications,
            "reviews": self.reviews,
            "source": self.source,
            "source_url": self.source_url,
            "last_updated": self.last_updated.isoformat()
        }

@dataclass
class PhoneSpecifications:
    """Specific specifications for smartphones."""
    screen_size: float
    resolution: str
    processor: str
    ram: int
    storage: int
    battery_capacity: int
    camera_main: float
    camera_front: float
    os: str
    os_version: str

@dataclass
class TabletSpecifications:
    """Specific specifications for tablets."""
    screen_size: float
    resolution: str
    processor: str
    ram: int
    storage: int
    battery_capacity: int
    camera_main: float
    camera_front: float
    os: str
    os_version: str
    cellular: bool

@dataclass
class SmartwatchSpecifications:
    """Specific specifications for smartwatches."""
    screen_size: float
    resolution: str
    processor: str
    ram: int
    storage: int
    battery_capacity: int
    os: str
    os_version: str
    water_resistance: str
    heart_rate_monitor: bool
    gps: bool 