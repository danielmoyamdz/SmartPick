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
        devices = await gsmarena_scraper.search_devices(query, category)
        return devices
    except Exception as e:
        st.error(f"Error searching devices: {str(e)}")
        return []

def display_device_card(device: Dict[str, Any]):
    """Display a device card with its details."""
    st.markdown(f"""
        <div class="device-card">
            <h3>{device['name']}</h3>
            <p><strong>Brand:</strong> {device['brand']}</p>
            <p><strong>Source:</strong> <a href="{device['source_url']}" target="_blank">GSMArena</a></p>
        </div>
    """, unsafe_allow_html=True)

def main():
    st.title("📱 SmartPick - Comparador de Dispositivos")
    st.markdown("""
    SmartPick te ayuda a encontrar el dispositivo perfecto comparando especificaciones, precios y reseñas de múltiples fuentes.
    """)
    
    # Sidebar filters
    st.sidebar.header("🔍 Filtros de Búsqueda")
    
    # Búsqueda
    search_query = st.text_input("Buscar dispositivo", placeholder="Ej: iPhone 14, Samsung S23...")
    
    # Filtros
    st.subheader("Filtros")
    
    # Rango de precios
    min_price, max_price = st.slider(
        "Rango de precios ($)",
        min_value=0,
        max_value=2000,
        value=(0, 2000),
        step=100
    )
    
    # Marcas
    brands = st.multiselect(
        "Marcas",
        ["Apple", "Samsung", "Google", "OnePlus", "Xiaomi", "Huawei", "Otras"],
        default=[]
    )
    
    # Año de lanzamiento
    current_year = datetime.now().year
    min_year, max_year = st.slider(
        "Año de lanzamiento",
        min_value=2018,
        max_value=current_year,
        value=(2018, current_year)
    )
    
    # Características específicas
    st.subheader("Características")
    
    # RAM
    ram_options = st.multiselect(
        "RAM",
        ["4GB", "6GB", "8GB", "12GB", "16GB"],
        default=[]
    )
    
    # Almacenamiento
    storage_options = st.multiselect(
        "Almacenamiento",
        ["64GB", "128GB", "256GB", "512GB", "1TB"],
        default=[]
    )
    
    # Tamaño de pantalla
    screen_sizes = st.multiselect(
        "Tamaño de pantalla",
        ["< 6 pulgadas", "6-6.5 pulgadas", "6.5-7 pulgadas", "> 7 pulgadas"],
        default=[]
    )
    
    # Botón de búsqueda
    search_button = st.button("🔍 Buscar Dispositivos")

    # Contenedor principal
    main_container = st.container()

    # Función para mostrar métricas
    def show_metrics(device: Device):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">{}</div>
                <div class="metric-label">Precio</div>
            </div>
            """.format(f"${device.price:,.2f}" if device.price else "N/A"), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">{}</div>
                <div class="metric-label">RAM</div>
            </div>
            """.format(device.specifications.ram if device.specifications.ram else "N/A"), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">{}</div>
                <div class="metric-label">Almacenamiento</div>
            </div>
            """.format(device.specifications.storage if device.specifications.storage else "N/A"), unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">{}</div>
                <div class="metric-label">Pantalla</div>
            </div>
            """.format(device.specifications.display if device.specifications.display else "N/A"), unsafe_allow_html=True)

    # Función para mostrar especificaciones
    def show_specifications(device: Device):
        st.markdown("### 📋 Especificaciones Técnicas")
        
        specs = {
            "General": {
                "Marca": device.brand,
                "Modelo": device.name,
                "Fecha de lanzamiento": device.release_date.strftime("%B %Y") if device.release_date else "N/A",
                "Precio": f"${device.price:,.2f}" if device.price else "N/A"
            },
            "Pantalla": {
                "Tamaño": device.specifications.display,
                "Resolución": device.specifications.resolution,
                "Tipo": device.specifications.display_type
            },
            "Hardware": {
                "Procesador": device.specifications.cpu,
                "RAM": device.specifications.ram,
                "Almacenamiento": device.specifications.storage,
                "GPU": device.specifications.gpu
            },
            "Cámara": {
                "Principal": device.specifications.camera,
                "Frontal": device.specifications.front_camera,
                "Video": device.specifications.video
            },
            "Batería": {
                "Capacidad": device.specifications.battery,
                "Carga rápida": device.specifications.charging
            }
        }
        
        for category, items in specs.items():
            st.markdown(f"#### {category}")
            for key, value in items.items():
                if value and value != "N/A":
                    st.markdown(f"**{key}:** {value}")

    # Función para mostrar gráficos de comparación
    def show_comparison_charts(devices: List[Device]):
        if len(devices) < 2:
            return
        
        st.markdown("### 📊 Comparación de Dispositivos")
        
        # Preparar datos para los gráficos
        data = []
        for device in devices:
            if device.price and device.specifications.ram and device.specifications.storage:
                data.append({
                    "Dispositivo": device.name,
                    "Precio": device.price,
                    "RAM": device.specifications.ram,
                    "Almacenamiento": device.specifications.storage
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
        fig_specs.add_trace(go.Bar(name="Almacenamiento", x=df["Dispositivo"], y=df["Almacenamiento"]))
        fig_specs.update_layout(title="Comparación de Especificaciones", barmode="group")
        st.plotly_chart(fig_specs, use_container_width=True)

    # Función para aplicar filtros
    def apply_filters(device: Device) -> bool:
        # Filtro de precio
        if device.price:
            if not (min_price <= device.price <= max_price):
                return False
        
        # Filtro de marca
        if brands and device.brand not in brands:
            return False
        
        # Filtro de año
        if device.release_date:
            if not (min_year <= device.release_date.year <= max_year):
                return False
        
        # Filtro de RAM
        if ram_options and device.specifications.ram:
            if device.specifications.ram not in ram_options:
                return False
        
        # Filtro de almacenamiento
        if storage_options and device.specifications.storage:
            if device.specifications.storage not in storage_options:
                return False
        
        # Filtro de tamaño de pantalla
        if screen_sizes and device.specifications.display:
            screen_size = device.specifications.display.split()[0]
            try:
                size = float(screen_size)
                if size < 6 and "< 6 pulgadas" not in screen_sizes:
                    return False
                elif 6 <= size < 6.5 and "6-6.5 pulgadas" not in screen_sizes:
                    return False
                elif 6.5 <= size < 7 and "6.5-7 pulgadas" not in screen_sizes:
                    return False
                elif size >= 7 and "> 7 pulgadas" not in screen_sizes:
                    return False
            except ValueError:
                pass
        
        return True

    # Procesar búsqueda
    if search_button and search_query:
        with main_container:
            st.markdown("### 🔍 Resultados de la búsqueda")
            
            # Mostrar spinner durante la búsqueda
            with st.spinner("Buscando dispositivos..."):
                # Realizar búsqueda
                devices = asyncio.run(gsmarena_scraper.search_devices(search_query))
                
                # Aplicar filtros
                filtered_devices = [device for device in devices if apply_filters(device)]
                
                if not filtered_devices:
                    st.warning("No se encontraron dispositivos que coincidan con los criterios de búsqueda.")
                else:
                    st.success(f"Se encontraron {len(filtered_devices)} dispositivos.")
                    
                    # Mostrar dispositivos
                    for device in filtered_devices:
                        with st.expander(f"📱 {device['name']} ({device['brand']})"):
                            show_metrics(device)
                            show_specifications(device)
                            
                            # Botones de acción
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("➕ Añadir a comparación", key=f"compare_{device['id']}"):
                                    if "comparison" not in st.session_state:
                                        st.session_state.comparison = []
                                    if device not in st.session_state.comparison:
                                        st.session_state.comparison.append(device)
                                        st.success("Dispositivo añadido a la comparación")
                                    else:
                                        st.warning("Este dispositivo ya está en la comparación")
                            
                            with col2:
                                if st.button("🔗 Ver en GSMArena", key=f"link_{device['id']}"):
                                    st.markdown(f"[Abrir en GSMArena]({device['source_url']})")
                    
                    # Mostrar comparación si hay dispositivos seleccionados
                    if "comparison" in st.session_state and st.session_state.comparison:
                        show_comparison_charts(st.session_state.comparison)
                        
                        # Botón para limpiar comparación
                        if st.button("🗑️ Limpiar comparación"):
                            st.session_state.comparison = []
                            st.experimental_rerun()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center'>
        <p>Desarrollado con ❤️ por SmartPick Team</p>
        <p>Datos proporcionados por GSMArena</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 