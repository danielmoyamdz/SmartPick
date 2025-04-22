from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
import json
from bs4 import BeautifulSoup
from loguru import logger
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import random

class GSMArenaScraper:
    """Scraper for GSMArena website."""
    
    BASE_URL = "https://www.gsmarena.com"
    SEARCH_URL = f"{BASE_URL}/results.php3"
    CACHE_DIR = "cache"
    CACHE_DURATION = timedelta(hours=24)  # Cache duration of 24 hours
    
    def __init__(self):
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        
        # Initialize the Chrome driver
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        # Set up wait
        self.wait = WebDriverWait(self.driver, 10)
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(self.CACHE_DIR):
            os.makedirs(self.CACHE_DIR)
    
    def _get_cache_path(self, key: str) -> str:
        """Get the cache file path for a given key."""
        filename = str(hash(key)) + ".json"
        return os.path.join(self.CACHE_DIR, filename)
    
    async def _get_cached_data(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache if it exists and is not expired."""
        try:
            cache_path = self._get_cache_path(key)
            if not os.path.exists(cache_path):
                return None
            
            with open(cache_path, 'r') as f:
                cached_data = json.load(f)
            
            # Check if cache is expired
            cached_time = datetime.fromisoformat(cached_data['timestamp'])
            if datetime.now() - cached_time > self.CACHE_DURATION:
                return None
            
            return cached_data['data']
            
        except Exception as e:
            logger.error(f"Error reading from cache: {str(e)}")
            return None
    
    async def _save_to_cache(self, key: str, data: Dict[str, Any]):
        """Save data to cache."""
        try:
            cache_path = self._get_cache_path(key)
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f)
                
        except Exception as e:
            logger.error(f"Error saving to cache: {str(e)}")
    
    async def get_device_details(self, url: str) -> Dict[str, Any]:
        """Get detailed specifications for a device."""
        try:
            # Check cache first
            cached_data = await self._get_cached_data(url)
            if cached_data:
                logger.info(f"Using cached data for {url}")
                return cached_data
            
            # Fix URL formation
            if not url.startswith('http'):
                url = f"{self.BASE_URL}/{url}"
            if url.endswith('.php.php'):
                url = url[:-4]
            
            logger.info(f"Fetching device details from {url}")
            
            # Load the page
            self.driver.get(url)
            
            # Wait for the main content to load
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "specs-phone-name-title")))
            
            # Get the page source
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract basic device info
            device_info = {
                'name': soup.find('h1', class_='specs-phone-name-title').get_text(strip=True) if soup.find('h1', class_='specs-phone-name-title') else "Unknown",
                'brand': url.split('/')[-1].split('_')[0].capitalize(),
                'url': url
            }
            
            # Extract specifications
            specs = {}
            tables = soup.find_all(['table', 'div'], class_=['specs-list', 'specs-list2', 'specs-list3'])
            
            for table in tables:
                rows = table.find_all(['tr', 'div'], class_=['nfo', 'specs-list-row'])
                for row in rows:
                    cells = row.find_all(['td', 'div'], class_=['nfo', 'specs-list-cell'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        specs[key] = value
            
            # Extract key specifications
            key_specs = {
                'display': await self._extract_spec(specs, 'Display'),
                'processor': await self._extract_spec(specs, 'Chipset'),
                'ram': await self._extract_spec(specs, 'RAM'),
                'storage': await self._extract_spec(specs, 'Storage'),
                'camera': await self._extract_spec(specs, 'Main camera'),
                'battery': await self._extract_spec(specs, 'Battery'),
                'price': await self._extract_spec(specs, 'Price')
            }
            
            device_info.update(key_specs)
            
            # Save to cache
            await self._save_to_cache(url, device_info)
            
            logger.info(f"Successfully extracted details for {device_info['name']}")
            return device_info
            
        except Exception as e:
            logger.error(f"Error getting device details: {str(e)}")
            return {}
    
    async def _extract_spec(self, specs: Dict[str, str], spec_name: str) -> str:
        """Extract a specific specification from the specs dictionary with improved matching."""
        try:
            # Lista de posibles nombres para cada especificación
            spec_aliases = {
                'Display': ['Display', 'Screen', 'Display size', 'Size'],
                'Chipset': ['Chipset', 'CPU', 'Processor', 'SoC'],
                'RAM': ['RAM', 'Memory'],
                'Storage': ['Storage', 'Built-in Storage', 'Internal'],
                'Main camera': ['Main Camera', 'Camera', 'Rear Camera', 'Primary Camera'],
                'Battery': ['Battery', 'Battery capacity', 'Battery size'],
                'Price': ['Price', 'Retail Price', 'Launch Price']
            }
            
            # Intentar coincidencia exacta primero
            if spec_name in specs:
                return specs[spec_name]
            
            # Intentar con los alias
            if spec_name in spec_aliases:
                for alias in spec_aliases[spec_name]:
                    # Coincidencia exacta
                    if alias in specs:
                        return specs[alias]
                    
                    # Coincidencia insensible a mayúsculas/minúsculas
                    for key in specs:
                        if key.lower() == alias.lower():
                            return specs[key]
                    
                    # Coincidencia parcial
                    for key in specs:
                        if alias.lower() in key.lower():
                            return specs[key]
            
            logger.warning(f"Could not find specification '{spec_name}' using any method")
            return "N/A"
            
        except Exception as e:
            logger.error(f"Error extracting specification '{spec_name}': {str(e)}")
            return "N/A"
    
    async def search_devices(self, query: str, category: str = None) -> List[Dict[str, Any]]:
        """Search for devices on GSMArena."""
        try:
            # Si no hay query, buscar dispositivos populares
            if not query or not query.strip():
                return await self._get_popular_devices()
            
            # Clean the query
            query = query.strip()
            
            # Build the search URL
            search_url = f"{self.SEARCH_URL}?sQuickSearch=yes&sName={query}"
            
            logger.info(f"Searching devices with query: {query}")
            
            # Load the search page
            self.driver.get(search_url)
            
            # Wait for results to load
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "makers")))
            
            # Get the page source
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            results = []
            
            # Try to find the makers list
            makers_div = soup.find('div', {'class': ['makers', 'makers-list']})
            if makers_div:
                # Find all phone entries
                phones = makers_div.find_all(['li', 'div'], class_='makers')
                logger.info(f"Found {len(phones)} devices in search results")
                
                # Crear una lista de tareas para obtener detalles en paralelo
                tasks = []
                for phone in phones[:5]:  # Limitar a 5 dispositivos para mayor velocidad
                    try:
                        link = phone.find('a')
                        if not link or not link.get('href'):
                            continue
                            
                        name = link.get_text(strip=True)
                        if not name:
                            continue
                            
                        url = link['href']
                        if not url.startswith('http'):
                            url = f"{self.BASE_URL}/{url}"
                        
                        # Añadir tarea para obtener detalles
                        tasks.append(self.get_device_details(url))
                        
                    except Exception as e:
                        logger.error(f"Error processing phone entry: {str(e)}")
                        continue
                
                # Ejecutar todas las tareas en paralelo con un límite de concurrencia
                if tasks:
                    # Usar un semáforo para limitar la concurrencia
                    semaphore = asyncio.Semaphore(2)  # Máximo 2 solicitudes simultáneas
                    
                    async def get_details_with_semaphore(task):
                        async with semaphore:
                            return await task
                    
                    details_tasks = [get_details_with_semaphore(task) for task in tasks]
                    details_list = await asyncio.gather(*details_tasks, return_exceptions=True)
                    
                    for details in details_list:
                        if isinstance(details, Exception):
                            logger.error(f"Error getting device details: {str(details)}")
                            continue
                            
                        if details:
                            results.append(details)
            else:
                logger.warning("No search results found")
            
            return results
            
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            return []
    
    async def _get_popular_devices(self) -> List[Dict[str, Any]]:
        """Get popular devices from GSMArena homepage."""
        try:
            logger.info("Getting popular devices from homepage")
            
            # Load the homepage
            self.driver.get(self.BASE_URL)
            
            # Wait for the popular phones section to load
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "module-phones")))
            
            # Get the page source
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            results = []
            
            # Buscar en la sección de teléfonos populares
            popular_section = soup.find('div', class_='module-phones')
            if popular_section:
                phones = popular_section.find_all('a')
                logger.info(f"Found {len(phones)} popular devices")
                
                # Crear una lista de tareas para obtener detalles
                tasks = []
                for phone in phones[:10]:  # Limitar a 10 dispositivos
                    try:
                        href = phone.get('href')
                        if not href:
                            continue
                            
                        name = phone.get_text(strip=True)
                        if not name:
                            continue
                            
                        url = href
                        if not url.startswith('http'):
                            url = f"{self.BASE_URL}/{url}"
                        
                        tasks.append(self.get_device_details(url))
                        
                    except Exception as e:
                        logger.error(f"Error processing popular phone: {str(e)}")
                        continue
                
                # Ejecutar tareas con límite de concurrencia
                if tasks:
                    # Usar un semáforo para limitar la concurrencia
                    semaphore = asyncio.Semaphore(2)  # Máximo 2 solicitudes simultáneas
                    
                    async def get_details_with_semaphore(task):
                        async with semaphore:
                            return await task
                    
                    details_tasks = [get_details_with_semaphore(task) for task in tasks]
                    details_list = await asyncio.gather(*details_tasks, return_exceptions=True)
                    
                    for details in details_list:
                        if isinstance(details, Exception):
                            logger.error(f"Error getting device details: {str(details)}")
                            continue
                            
                        if details:
                            results.append(details)
                else:
                    logger.warning("No popular devices found to process")
            else:
                logger.warning("Popular devices section not found")
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting popular devices: {str(e)}")
            return []
    
    def __del__(self):
        """Clean up resources."""
        try:
            self.driver.quit()
        except:
            pass 