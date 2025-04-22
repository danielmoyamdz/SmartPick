# SmartPick

SmartPick is a web application that helps users find smartphones based on their budget range. It scrapes device information from GSMArena and provides a user-friendly interface to search and compare devices.

## Features

- Search devices by budget range
- View detailed specifications including display, processor, RAM, storage, camera, and battery
- Browse popular devices
- Real-time data scraping from GSMArena

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/SmartPick.git
cd SmartPick
```

2. Create and activate a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the Streamlit application:
```bash
streamlit run app.py
```

2. To test the scraper independently:
```bash
python main.py
```

## Project Structure

- `app.py`: Main Streamlit application
- `src/scrapers/gsmarena.py`: GSMArena scraper implementation
- `main.py`: Scraper testing script

## Notes

- The application uses Selenium for web scraping, which requires a compatible web driver
- Internet connection is required for the application to function
- Some websites may have anti-scraping measures in place, which could affect the application's performance

## Contributing

Feel free to submit issues and enhancement requests! 