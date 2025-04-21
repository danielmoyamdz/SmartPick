import pytest
from src.api.bestbuy import BestBuyAPIClient
from src.scrapers.gsmarena import GSMArenaScraper
import os
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture
def bestbuy_client():
    return BestBuyAPIClient()

@pytest.fixture
def gsmarena_scraper():
    return GSMArenaScraper()

def test_bestbuy_search(bestbuy_client):
    """Test Best Buy device search."""
    devices = bestbuy_client.search_devices("iPhone 13", "smartphone")
    assert isinstance(devices, list)
    if devices:  # If API key is configured
        assert all(isinstance(d, dict) for d in devices)
        assert all("id" in d for d in devices)
        assert all("name" in d for d in devices)

def test_bestbuy_device_details(bestbuy_client):
    """Test Best Buy device details retrieval."""
    # First search for a device
    devices = bestbuy_client.search_devices("iPhone 13", "smartphone")
    if devices:  # If API key is configured
        device_id = devices[0]["id"]
        details = bestbuy_client.get_device_details(device_id)
        assert isinstance(details, dict)
        assert "id" in details
        assert "name" in details
        assert "specifications" in details

@pytest.mark.asyncio
async def test_gsmarena_search(gsmarena_scraper):
    """Test GSMArena device search."""
    devices = await gsmarena_scraper.search_devices("iPhone 13")
    assert isinstance(devices, list)
    assert all(isinstance(d, dict) for d in devices)
    assert all("id" in d for d in devices)
    assert all("name" in d for d in devices)

@pytest.mark.asyncio
async def test_gsmarena_device_details(gsmarena_scraper):
    """Test GSMArena device details retrieval."""
    # First search for a device
    devices = await gsmarena_scraper.search_devices("iPhone 13")
    if devices:
        device_id = devices[0]["id"]
        details = await gsmarena_scraper.get_device_details(device_id)
        assert isinstance(details, dict)
        assert "id" in details
        assert "name" in details
        assert "specifications" in details 