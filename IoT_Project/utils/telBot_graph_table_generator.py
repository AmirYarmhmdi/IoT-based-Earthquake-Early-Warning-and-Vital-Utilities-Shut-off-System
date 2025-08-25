import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
from datetime import datetime
import pytz

def generate_graph_image(chart_data: dict, device_id: str) -> io.BytesIO:
    """
    Generates a graph for sensor data and returns it as a bytes buffer.
    
    Args:
        chart_data: Dictionary containing timestamps, x_axis, and y_axis values.
        device_id: The ID of the device.

    Returns:
        A BytesIO buffer containing the graph image.
    """
    timestamps = [datetime.fromtimestamp(ts, tz=pytz.timezone('Europe/Rome')) for ts in chart_data['data']['timestamps']]
    x_values = chart_data['data']['x_axis']['values']
    y_values = chart_data['data']['y_axis']['values']
    sensor_type = chart_data['sensor_type']
    unit = "Gal" if sensor_type == "acceleration" else "cm/s"

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(timestamps, x_values, label=f"X-Axis {sensor_type.capitalize()}", color='blue')
    ax.plot(timestamps, y_values, label=f"Y-Axis {sensor_type.capitalize()}", color='red')
    
    ax.set_title(f"{sensor_type.capitalize()} Data for {device_id}")
    ax.set_xlabel("Time")
    ax.set_ylabel(f"Value ({unit})")
    ax.legend()
    ax.grid(True)
    ax.yaxis.set_label_position("left")
    ax.yaxis.tick_left()
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    plt.close(fig)
    
    return img_buffer

def generate_table_image(header: list, rows: list) -> io.BytesIO:
    """
    Generates an image of a table and returns it as a bytes buffer.
    
    Args:
        header: The list of column headers.
        rows: A list of lists representing the table rows.

    Returns:
        A BytesIO buffer containing the table image.
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.axis("tight")
    ax.axis("off")
    ax.table(cellText=rows, colLabels=header, loc="center")

    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format="png", bbox_inches="tight")
    img_buffer.seek(0)
    plt.close(fig)
    
    return img_buffer