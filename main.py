import asyncio
from loguru import logger
from src.scrapers.gsmarena import GSMArenaScraper

async def main():
    logger.info("Starting GSMArena scraper test")
    
    try:
        scraper = GSMArenaScraper()
        
        # Test searching for a specific device
        logger.info("Testing device search...")
        search_results = await scraper.search_devices("iPhone 15")
        logger.info(f"Found {len(search_results)} devices in search")
        
        # Print details of found devices
        for device in search_results:
            logger.info(f"Device: {device.get('name', 'Unknown')}")
            logger.info(f"Price: {device.get('price', 'N/A')}")
            logger.info(f"Display: {device.get('display', 'N/A')}")
            logger.info(f"Processor: {device.get('processor', 'N/A')}")
            logger.info(f"RAM: {device.get('ram', 'N/A')}")
            logger.info(f"Storage: {device.get('storage', 'N/A')}")
            logger.info(f"Camera: {device.get('camera', 'N/A')}")
            logger.info(f"Battery: {device.get('battery', 'N/A')}")
            logger.info("-" * 50)
        
        # Test getting popular devices
        logger.info("\nTesting popular devices...")
        popular_devices = await scraper.search_devices("")
        logger.info(f"Found {len(popular_devices)} popular devices")
        
        # Print details of popular devices
        for device in popular_devices:
            logger.info(f"Device: {device.get('name', 'Unknown')}")
            logger.info(f"Price: {device.get('price', 'N/A')}")
            logger.info(f"Display: {device.get('display', 'N/A')}")
            logger.info(f"Processor: {device.get('processor', 'N/A')}")
            logger.info(f"RAM: {device.get('ram', 'N/A')}")
            logger.info(f"Storage: {device.get('storage', 'N/A')}")
            logger.info(f"Camera: {device.get('camera', 'N/A')}")
            logger.info(f"Battery: {device.get('battery', 'N/A')}")
            logger.info("-" * 50)
            
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
    finally:
        # Clean up resources
        if 'scraper' in locals():
            try:
                del scraper
            except:
                pass

if __name__ == "__main__":
    asyncio.run(main()) 