from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
from loguru import logger
import re
import asyncio
from ..models.device import Device, PhoneSpecifications

class GSMArenaScraper:
    """Scraper for GSMArena website."""
    
    BASE_URL = "https://www.gsmarena.com"  # Usar la versión desktop
    SEARCH_URL = f"{BASE_URL}/results.php3"
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0"
            },
            follow_redirects=True,
            timeout=30.0
        )
    
    async def search_devices(self, query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for devices on GSMArena."""
        try:
            params = {
                "sQuickSearch": "yes",
                "sName": query
            }
            logger.info(f"Searching for devices with query: {query}")
            response = await self.client.get(self.SEARCH_URL, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            devices = []
            
            # Buscar resultados en la lista de dispositivos
            for item in soup.select(".makers ul li"):
                try:
                    link = item.find("a")
                    if not link:
                        continue
                        
                    href = link.get("href", "")
                    if not href or not href.endswith(".php"):
                        continue
                        
                    # Extraer el ID y la URL completa del dispositivo
                    device_url = f"{self.BASE_URL}/{href}"
                    device_id = href.replace(".php", "")
                    
                    # Obtener el nombre y la imagen del dispositivo
                    name = link.text.strip()
                    if not name:
                        continue
                        
                    # Obtener la marca del nombre
                    brand = name.split()[0] if len(name.split()) > 1 else "Unknown"
                    
                    # Obtener la imagen si está disponible
                    img = item.find("img")
                    image_url = img["src"] if img and "src" in img.attrs else None
                    
                    device = {
                        "id": device_id,
                        "name": name,
                        "brand": brand,
                        "image_url": image_url,
                        "url": device_url,
                        "source": "gsmarena",
                        "source_url": device_url
                    }
                    
                    # Evitar duplicados
                    if not any(d["id"] == device["id"] for d in devices):
                        devices.append(device)
                        logger.info(f"Added device: {name} ({brand})")
                        
                except Exception as e:
                    logger.error(f"Error processing search result: {str(e)}")
                    continue
            
            logger.info(f"Total devices found: {len(devices)}")
            return devices
            
        except Exception as e:
            logger.error(f"Failed to search GSMArena devices: {str(e)}")
            return []
    
    async def get_device_details(self, device_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific device."""
        try:
            url = f"{self.BASE_URL}/{device_id}.php"
            logger.info(f"Fetching device details from: {url}")
            
            async with httpx.AsyncClient(
                headers=self.client.headers,
                follow_redirects=True,
                timeout=30.0
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, "html.parser")
                specs = self._parse_specifications(soup)
                
                # Obtener el nombre del dispositivo
                name_elem = soup.select_one("h1.specs-phone-name-title")
                name = name_elem.text.strip() if name_elem else "Unknown Device"
                
                # Obtener la marca del nombre
                brand = name.split()[0] if len(name.split()) > 1 else "Unknown"
                
                # Obtener la imagen del dispositivo
                img = soup.select_one("div.specs-photo-main img")
                image_url = img["src"] if img and "src" in img.attrs else None
                
                # Obtener la fecha de lanzamiento
                release_date = self._extract_release_date(specs)
                
                # Obtener el precio si está disponible
                price = None
                price_elem = soup.select_one(".price")
                if price_elem:
                    price_text = price_elem.text.strip()
                    try:
                        # Extraer el precio numérico
                        price_match = re.search(r'[\d,.]+', price_text)
                        if price_match:
                            price = float(price_match.group().replace(',', ''))
                    except ValueError:
                        pass
                
                logger.info(f"Found device details: {name} ({brand})")
                
                return {
                    "id": device_id,
                    "name": name,
                    "brand": brand,
                    "image_url": image_url,
                    "specifications": specs,
                    "release_date": release_date.isoformat() if release_date else None,
                    "price": price,
                    "source": "gsmarena",
                    "source_url": url
                }
        except Exception as e:
            logger.error(f"Failed to get GSMArena device details: {str(e)}")
            return {}
    
    def _parse_specifications(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parse device specifications from GSMArena page."""
        specs = {}
        
        # Extraer especificaciones de la tabla de specs
        for section in soup.select("#specs-list table"):
            try:
                category = section.find_previous("tr", class_="head")
                if not category:
                    continue
                    
                category_name = category.text.strip().lower()
                category_specs = {}
                
                for row in section.select("tr:not(.head)"):
                    try:
                        name = row.select_one("td.ttl")
                        value = row.select_one("td.nfo")
                        
                        if name and value:
                            name = name.text.strip().lower()
                            value = value.text.strip()
                            category_specs[name] = value
                    except Exception as e:
                        logger.error(f"Error parsing specification row: {str(e)}")
                        continue
                
                if category_specs:
                    specs[category_name] = category_specs
            except Exception as e:
                logger.error(f"Error parsing specification section: {str(e)}")
                continue
        
        return specs
    
    def _extract_release_date(self, specs: Dict[str, Any]) -> Optional[datetime]:
        """Extract release date from specifications."""
        try:
            if "launch" in specs:
                date_str = specs["launch"].get("announced", "")
                if date_str:
                    # Try different date formats
                    formats = ["%Y, %B %d", "%Y, %B", "%B %Y", "%Y"]
                    for fmt in formats:
                        try:
                            return datetime.strptime(date_str, fmt)
                        except ValueError:
                            continue
        except Exception as e:
            logger.error(f"Error extracting release date: {str(e)}")
        return None
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        asyncio.run(self.close()) 