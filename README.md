# SmartPick - Device Comparison Tool

SmartPick is a powerful device comparison tool that helps users make informed decisions when purchasing electronic devices. It currently uses GSMArena as its primary data source to provide comprehensive device specifications and comparisons.

## Features

- Device search and comparison using GSMArena data
- Detailed specifications for smartphones, tablets, and smartwatches
- User-friendly interface built with Streamlit
- Comprehensive device specifications
- Easy-to-use search and filtering

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/SmartPick.git
cd SmartPick
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the Streamlit application:
```bash
streamlit run app.py
```

2. Open your browser and navigate to `http://localhost:8501`

3. Use the interface to:
   - Select device categories (smartphone, tablet, smartwatch)
   - Search for specific devices
   - View detailed specifications
   - Compare devices side by side

## Project Structure

```
SmartPick/
├── app.py                 # Main Streamlit application
├── src/
│   ├── scrapers/         # Web scraping modules
│   ├── models/           # Data models and schemas
│   └── utils/            # Utility functions
├── tests/                # Test suite
├── requirements.txt      # Project dependencies
└── README.md            # Project documentation
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- GSMArena for providing comprehensive device specifications 