import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import asyncio
from src.scrapers.gsmarena import GSMArenaScraper
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
from src.models.device import Device
import plotly.express as px
import plotly.graph_objects as go
import json
import logging

# Load environment variables
load_dotenv()

# Initialize GSMArena scraper
gsmarena_scraper = GSMArenaScraper()

# Page config
st.set_page_config(
    page_title="SmartPick - Comparador de Dispositivos",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .device-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 16px;
        margin: 8px 0;
        background-color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .specs-table {
        width: 100%;
        border-collapse: collapse;
    }
    .specs-table th, .specs-table td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }
    .specs-table th {
        background-color: #f5f5f5;
    }
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .price {
        font-size: 1.2em;
        font-weight: bold;
        color: #4CAF50;
    }
    .brand-badge {
        background-color: #e0e0e0;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        margin-right: 8px;
    }
    .filter-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .comparison-section {
        background-color: #fff;
        padding: 1rem;
        border-radius: 10px;
        margin-top: 1rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 0.5rem;
    }
    .metric-value {
        font-size: 1.5em;
        font-weight: bold;
        color: #2196F3;
    }
    .metric-label {
        font-size: 0.9em;
        color: #666;
    }
    </style>
""", unsafe_allow_html=True)

async def search_devices(query: str, category: str) -> List[Dict[str, Any]]:
    """Search for devices using GSMArena."""
    try:
        if not query or not query.strip():
            st.warning("Por favor ingresa un término de búsqueda.")
            return []
            
        st.info(f"Buscando dispositivos con el término: {query}")
        devices = await gsmarena_scraper.search_devices(query, category)
        
        if not devices:
            st.warning("No se encontraron dispositivos que coincidan con tu búsqueda.")
            return []
            
        return devices
    except Exception as e:
        st.error(f"Error al buscar dispositivos: {str(e)}")
        logger.error(f"Error searching devices: {str(e)}")
        return []

async def search_devices_by_price(min_price: float, max_price: float) -> List[Dict[str, Any]]:
    """Search for devices within a price range."""
    try:
        # Obtener todos los dispositivos populares (usando búsqueda vacía)
        devices = await gsmarena_scraper.search_devices("", None)
        
        # Filtrar dispositivos por rango de precio
        filtered_devices = []
        for device in devices:
            price = device.get('price')
            if price is not None and min_price <= price <= max_price:
                filtered_devices.append(device)
        
        # Ordenar por precio
        filtered_devices.sort(key=lambda x: x.get('price', float('inf')))
        
        return filtered_devices
    except Exception as e:
        st.error(f"Error al buscar dispositivos: {str(e)}")
        logging.error(f"Error searching devices by price: {str(e)}")
        return []

def display_device_card(device: Dict[str, Any]):
    """Display a device card with its specifications."""
    st.subheader(f"{device['brand']} {device['name']}")
    
    # Create columns for specifications
    col1, col2 = st.columns(2)
    
    # Filter out specifications with value "N/A"
    filtered_specs = {k: v for k, v in device['specifications'].items() if v != "N/A"}
    
    # Display specifications in columns
    for i, (spec, value) in enumerate(filtered_specs.items()):
        if i % 2 == 0:
            col1.write(f"**{spec}:** {value}")
        else:
            col2.write(f"**{spec}:** {value}")
    
    # Add a link to the source
    st.write(f"[Ver en GSMArena]({device['source_url']})")
    st.markdown("---")

def main():
    st.title("📱 SmartPick - Comparador de Dispositivos")
    st.markdown("""
    SmartPick te ayuda a encontrar el dispositivo perfecto comparando especificaciones, precios y reseñas de múltiples fuentes.
    """)
    
    # Sección de filtros de precio
    st.markdown("### 💰 Rango de Presupuesto")
    col1, col2 = st.columns(2)
    
    with col1:
        min_price = st.number_input(
            "Precio mínimo (€)",
            min_value=0,
            max_value=2000,
            value=0,
            step=50
        )
    
    with col2:
        max_price = st.number_input(
            "Precio máximo (€)",
            min_value=0,
            max_value=2000,
            value=1000,
            step=50
        )
    
    # Validación del rango de precios
    if min_price > max_price:
        st.error("El precio mínimo no puede ser mayor que el precio máximo")
        return
    
    # Botón de búsqueda
    search_button = st.button("🔍 Buscar Dispositivos")

    # Contenedor principal
    main_container = st.container()

    # Función para mostrar métricas
    def show_metrics(device: Dict[str, Any]):
        """Show device metrics in a grid layout."""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">{}</div>
                <div class="metric-label">Precio</div>
            </div>
            """.format(f"${device.get('price', 'N/A'):,.2f}" if device.get('price') else "N/A"), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">{}</div>
                <div class="metric-label">RAM</div>
            </div>
            """.format(device.get('specifications', {}).get('ram', 'N/A')), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">{}</div>
                <div class="metric-label">Almacenamiento</div>
            </div>
            """.format(device.get('specifications', {}).get('storage', 'N/A')), unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">{}</div>
                <div class="metric-label">Pantalla</div>
            </div>
            """.format(device.get('specifications', {}).get('display', 'N/A')), unsafe_allow_html=True)

    # Función para mostrar especificaciones
    def show_specifications(device: Dict[str, Any]):
        """Show device specifications in a table format."""
        st.markdown("### 📋 Especificaciones Técnicas")
        
        specs = {
            "General": {
                "Marca": device.get('brand', 'N/A'),
                "Modelo": device.get('name', 'N/A'),
                "Fecha de lanzamiento": device.get('release_date', 'N/A'),
                "Precio": f"${device.get('price', 'N/A'):,.2f}" if device.get('price') else "N/A"
            },
            "Pantalla": {
                "Tamaño": device.get('specifications', {}).get('display', 'N/A'),
                "Resolución": device.get('specifications', {}).get('resolution', 'N/A'),
                "Tipo": device.get('specifications', {}).get('display_type', 'N/A')
            },
            "Hardware": {
                "Procesador": device.get('specifications', {}).get('cpu', 'N/A'),
                "RAM": device.get('specifications', {}).get('ram', 'N/A'),
                "Almacenamiento": device.get('specifications', {}).get('storage', 'N/A'),
                "GPU": device.get('specifications', {}).get('gpu', 'N/A')
            },
            "Cámara": {
                "Principal": device.get('specifications', {}).get('camera', 'N/A'),
                "Frontal": device.get('specifications', {}).get('front_camera', 'N/A'),
                "Video": device.get('specifications', {}).get('video', 'N/A')
            },
            "Batería": {
                "Capacidad": device.get('specifications', {}).get('battery', 'N/A'),
                "Carga rápida": device.get('specifications', {}).get('charging', 'N/A')
            }
        }
        
        for category, items in specs.items():
            st.markdown(f"#### {category}")
            for key, value in items.items():
                if value and value != "N/A":
                    st.markdown(f"**{key}:** {value}")

    # Función para mostrar gráficos de comparación
    def show_comparison_charts(devices: List[Dict[str, Any]]):
        """Show comparison charts for selected devices."""
        if len(devices) < 2:
            return
        
        st.markdown("### 📊 Comparación de Dispositivos")
        
        # Preparar datos para los gráficos
        data = []
        for device in devices:
            if device.get('price') and device.get('specifications', {}).get('ram') and device.get('specifications', {}).get('storage'):
                data.append({
                    "Dispositivo": device['name'],
                    "Precio": device['price'],
                    "RAM": device['specifications']['ram'],
                    "Almacenamiento": device['specifications']['storage']
                })
        
        if not data:
            return
        
        df = pd.DataFrame(data)
        
        # Gráfico de precios
        fig_price = px.bar(df, x="Dispositivo", y="Precio", title="Comparación de Precios")
        st.plotly_chart(fig_price, use_container_width=True)
        
        # Gráfico de especificaciones
        fig_specs = go.Figure()
        fig_specs.add_trace(go.Bar(name="RAM", x=df["Dispositivo"], y=df["RAM"]))
        fig_specs.add_trace(go.Bar(name="Almacenamiento", x=df["Dispositivo"], y=df["Storage"]))
        fig_specs.update_layout(title="Comparación de Especificaciones", barmode="group")
        st.plotly_chart(fig_specs, use_container_width=True)

    if search_button:
        with main_container:
            st.info(f"Buscando dispositivos entre {min_price}€ y {max_price}€")
            # Realizar búsqueda asíncrona
            devices = asyncio.run(search_devices_by_price(min_price, max_price))
            
            if not devices:
                st.warning("No se encontraron dispositivos en ese rango de precios.")
            else:
                st.success(f"Se encontraron {len(devices)} dispositivos")
                for device in devices:
                    with st.expander(f"{device['brand']} {device['name']} - {device.get('price', 'N/A')}€"):
                        show_metrics(device)
                        show_specifications(device)
                        display_device_card(device)
                
                # Mostrar sección de comparación si hay dispositivos seleccionados
                if st.session_state.devices_to_compare:
                    st.markdown("---")
                    st.subheader("📊 Comparación de Dispositivos")
                    
                    # Mostrar gráficos de comparación
                    show_comparison_charts(st.session_state.devices_to_compare)
                    
                    # Mostrar tabla de comparación
                    st.markdown("### 📋 Tabla de Comparación")
                    
                    # Preparar datos para la tabla
                    comparison_data = []
                    for device in st.session_state.devices_to_compare:
                        specs = device.get('specifications', {})
                        comparison_data.append({
                            "Dispositivo": f"{device['brand']} {device['name']}",
                            "Precio": f"${device.get('price', 'N/A'):,.2f}" if device.get('price') else "N/A",
                            "Pantalla": specs.get('display', 'N/A'),
                            "Resolución": specs.get('resolution', 'N/A'),
                            "Procesador": specs.get('cpu', 'N/A'),
                            "RAM": specs.get('ram', 'N/A'),
                            "Almacenamiento": specs.get('storage', 'N/A'),
                            "Cámara Principal": specs.get('camera', 'N/A'),
                            "Cámara Frontal": specs.get('front_camera', 'N/A'),
                            "Batería": specs.get('battery', 'N/A'),
                            "Carga Rápida": specs.get('charging', 'N/A')
                        })
                    
                    # Mostrar tabla
                    df = pd.DataFrame(comparison_data)
                    st.dataframe(df, use_container_width=True)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center'>
        <p>Datos proporcionados por GSMArena</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 