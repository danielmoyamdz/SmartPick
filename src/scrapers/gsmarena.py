from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
from loguru import logger
import re
import asyncio
from ..models.device import Device, PhoneSpecifications
import random
import time

class GSMArenaScraper:
    """Scraper for GSMArena website."""
    
    BASE_URL = "https://www.gsmarena.com"
    SEARCH_URL = f"{BASE_URL}/results.php3"
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0",
                "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "Referer": "https://www.gsmarena.com/"
            },
            follow_redirects=True,
            timeout=30.0
        )
        self.last_request_time = 0
        self.min_request_interval = 5  # Mínimo tiempo entre solicitudes en segundos
    
    async def _make_request(self, url: str, params: Dict[str, str] = None) -> httpx.Response:
        """Make a request with a delay to avoid being blocked."""
        try:
            # Calcular el tiempo desde la última solicitud
            current_time = time.time()
            time_since_last_request = current_time - self.last_request_time
            
            # Si no ha pasado suficiente tiempo, esperar
            if time_since_last_request < self.min_request_interval:
                wait_time = self.min_request_interval - time_since_last_request
                logger.info(f"Esperando {wait_time:.2f} segundos antes de hacer la siguiente solicitud")
                await asyncio.sleep(wait_time)
            
            # Añadir un pequeño delay aleatorio adicional (1-3 segundos)
            additional_delay = 1 + random.random() * 2
            await asyncio.sleep(additional_delay)
            
            # Actualizar el tiempo de la última solicitud
            self.last_request_time = time.time()
            
            # Añadir common query parameters
            if params is None:
                params = {}
            
            # Intentar la solicitud con reintentos
            max_retries = 3
            retry_count = 0
            last_error = None
            
            while retry_count < max_retries:
                try:
                    response = await self.client.get(
                        url,
                        params=params,
                        headers={
                            **self.client.headers,
                            "Referer": self.BASE_URL
                        }
                    )
                    response.raise_for_status()
                    
                    # Log response details for debugging
                    logger.debug(f"Request URL: {response.url}")
                    logger.debug(f"Response status: {response.status_code}")
                    logger.debug(f"Response headers: {dict(response.headers)}")
                    
                    return response
                    
                except httpx.HTTPStatusError as e:
                    last_error = e
                    if e.response.status_code == 429:  # Too Many Requests
                        retry_count += 1
                        if retry_count < max_retries:
                            # Esperar más tiempo entre reintentos
                            wait_time = self.min_request_interval * (2 ** retry_count)
                            logger.warning(f"Recibido error 429. Reintentando en {wait_time} segundos...")
                            await asyncio.sleep(wait_time)
                        else:
                            logger.error("Se alcanzó el número máximo de reintentos")
                            raise
                    else:
                        raise
                        
        except Exception as e:
            logger.error(f"Error making request to {url}: {str(e)}")
            raise
    
    async def search_devices(self, query: str, category: str = None) -> List[Dict[str, Any]]:
        """Search for devices on GSMArena."""
        logger.info(f"Searching for devices with query: {query}")
        
        if not query or not query.strip():
            logger.warning("Empty search query provided")
            return []
            
        # Clean the query
        query = query.strip()
        
        try:
            # Use the search results page directly
            search_params = {
                "sQuickSearch": "yes",
                "sName": query
            }
            
            logger.info(f"Searching with params: {search_params}")
            response = await self._make_request(self.SEARCH_URL, search_params)
            
            if response.status_code != 200:
                logger.error(f"Search page returned status code: {response.status_code}")
                return []
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Log the full HTML for debugging
            logger.debug(f"Full response HTML: {soup.prettify()}")
            
            # Find the main results container
            results = []
            
            # Try to find the makers list
            makers_div = soup.find('div', {'class': ['makers', 'makers-list']})
            if makers_div:
                # Find all phone entries
                phones = makers_div.find_all(['li', 'div'], class_='makers')
                
                for phone in phones:
                    try:
                        # Find the link
                        link = phone.find('a')
                        if not link:
                            continue
                            
                        href = link.get('href')
                        if not href:
                            continue
                            
                        # Get the device name
                        name = link.get_text(strip=True)
                        if not name:
                            continue
                            
                        # Get the brand (usually the first word in the name)
                        brand = name.split()[0]
                        
                        # Get the full URL
                        url = f"{self.BASE_URL}/{href}" if not href.startswith('http') else href
                        
                        logger.info(f"Found device: {name} ({brand})")
                        
                        # Get device details
                        details = await self._get_device_details(url)
                        if details:
                            results.append({
                                "name": name,
                                "brand": brand,
                                "source_url": url,
                                "specifications": details
                            })
                            logger.info(f"Added device details for: {name}")
                            
                            # Si encontramos resultados en el primer contenedor, retornamos inmediatamente
                            if len(results) >= 5:  # Limitamos a 5 resultados para evitar demasiadas solicitudes
                                logger.info(f"Found {len(results)} devices in makers list")
                                return results
                                
                    except Exception as e:
                        logger.error(f"Error processing phone entry: {str(e)}")
                        continue
            
            logger.info(f"Total devices found: {len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            return []
    
    async def _get_device_details(self, url: str) -> Dict[str, Any]:
        """Get detailed specifications for a device."""
        try:
            logger.info(f"Getting device details from: {url}")
            response = await self._make_request(url)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            specs = {}
            
            # Try different selectors for the specs table
            table_selectors = [
                "table.specs",
                "table#specs-list",
                "div.specs table",
                "table.specs-list",
                "div.specs-list table",
                "div.specs-list",
                "div#specs-list table",
                "div#specs-list"
            ]
            
            logger.info("Searching for specifications table...")
            for selector in table_selectors:
                logger.info(f"Trying table selector: {selector}")
                tables = soup.select(selector)
                logger.info(f"Found {len(tables)} tables with selector {selector}")
                
                for table in tables:
                    # Try to find all rows, including those in nested tables
                    rows = table.select("tr")
                    logger.info(f"Found {len(rows)} rows in table")
                    
                    for row in rows:
                        # Get category
                        category_cell = row.select_one("th")
                        if not category_cell:
                            continue
                            
                        category = category_cell.text.strip()
                        if category not in specs:
                            specs[category] = {}
                        
                        # Get specifications in this category
                        for cell in row.select("td"):
                            # Try different selectors for label and value
                            label = (
                                cell.select_one("span.specs-label") or
                                cell.select_one("td.ttl") or
                                cell.select_one("td:first-child") or
                                cell.select_one("td.nfo")
                            )
                            value = (
                                cell.select_one("span.specs-value") or
                                cell.select_one("td.nfo") or
                                cell.select_one("td:last-child") or
                                cell.select_one("td.ttl")
                            )
                            
                            if label and value:
                                label_text = label.text.strip()
                                value_text = value.text.strip()
                                if label_text and value_text:
                                    specs[category][label_text] = value_text
                                    logger.debug(f"Found spec: {category} - {label_text}: {value_text}")
            
            # Extract key specifications with fallbacks
            result = {
                "display": (
                    self._extract_spec(specs, "Display", "Size") or
                    self._extract_spec(specs, "Display", "Screen size") or
                    self._extract_spec(specs, "Display", "Physical size") or
                    "N/A"
                ),
                "resolution": (
                    self._extract_spec(specs, "Display", "Resolution") or
                    self._extract_spec(specs, "Display", "Screen resolution") or
                    self._extract_spec(specs, "Display", "Pixel density") or
                    "N/A"
                ),
                "display_type": (
                    self._extract_spec(specs, "Display", "Type") or
                    self._extract_spec(specs, "Display", "Display type") or
                    self._extract_spec(specs, "Display", "Technology") or
                    "N/A"
                ),
                "cpu": (
                    self._extract_spec(specs, "Hardware", "CPU") or
                    self._extract_spec(specs, "Hardware", "Processor") or
                    self._extract_spec(specs, "Hardware", "Chipset") or
                    "N/A"
                ),
                "ram": (
                    self._extract_spec(specs, "Hardware", "RAM") or
                    self._extract_spec(specs, "Memory", "RAM") or
                    self._extract_spec(specs, "Hardware", "Memory") or
                    "N/A"
                ),
                "storage": (
                    self._extract_spec(specs, "Hardware", "Storage") or
                    self._extract_spec(specs, "Memory", "Storage") or
                    self._extract_spec(specs, "Hardware", "Card slot") or
                    "N/A"
                ),
                "gpu": (
                    self._extract_spec(specs, "Hardware", "GPU") or
                    self._extract_spec(specs, "Hardware", "Graphics") or
                    self._extract_spec(specs, "Hardware", "Graphics processor") or
                    "N/A"
                ),
                "camera": (
                    self._extract_spec(specs, "Camera", "Main camera") or
                    self._extract_spec(specs, "Camera", "Primary camera") or
                    self._extract_spec(specs, "Camera", "Camera") or
                    "N/A"
                ),
                "front_camera": (
                    self._extract_spec(specs, "Camera", "Selfie camera") or
                    self._extract_spec(specs, "Camera", "Front camera") or
                    self._extract_spec(specs, "Camera", "Selfie") or
                    "N/A"
                ),
                "video": (
                    self._extract_spec(specs, "Camera", "Video") or
                    self._extract_spec(specs, "Camera", "Video recording") or
                    self._extract_spec(specs, "Camera", "Video capture") or
                    "N/A"
                ),
                "battery": (
                    self._extract_spec(specs, "Battery", "Capacity") or
                    self._extract_spec(specs, "Battery", "Battery capacity") or
                    self._extract_spec(specs, "Battery", "Battery") or
                    "N/A"
                ),
                "charging": (
                    self._extract_spec(specs, "Battery", "Charging") or
                    self._extract_spec(specs, "Battery", "Fast charging") or
                    self._extract_spec(specs, "Battery", "Charger") or
                    "N/A"
                )
            }
            
            logger.info(f"Successfully extracted specifications: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting device details: {str(e)}")
            return {}
    
    def _extract_spec(self, specs: Dict[str, Dict[str, str]], category: str, field: str) -> str:
        """Extract a specific specification from the specs dictionary."""
        try:
            logger.debug(f"Extracting spec: {category}/{field}")
            if category in specs:
                # Try exact match first
                if field in specs[category]:
                    value = specs[category][field]
                    logger.debug(f"Found exact match for {category}/{field}: {value}")
                    return value
                
                # Try case-insensitive match
                for key, value in specs[category].items():
                    if key.lower() == field.lower():
                        logger.debug(f"Found case-insensitive match for {category}/{field}: {value}")
                        return value
                
                # Try partial match
                for key, value in specs[category].items():
                    if field.lower() in key.lower():
                        logger.debug(f"Found partial match for {category}/{field}: {value}")
                        return value
            
            logger.debug(f"No match found for {category}/{field}")
            return None
        except Exception as e:
            logger.error(f"Error extracting spec {category}/{field}: {str(e)}")
            return None
    
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