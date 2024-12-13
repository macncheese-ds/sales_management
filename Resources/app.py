import tkinter as tk
from tkinter import messagebox
import csv
import os
from datetime import datetime
# Nombre del archivo CSV para almacenar las comandas con estado
csv_file = "comandas_estado.csv"
# Crear el archivo CSV si no existe y agregar el encabezado
if not os.path.exists(csv_file):
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Cliente", "Número de Mesa", "Productos", "Total", "Fecha y Hora", "Estado"])
# Definición de los productos y precios basados en el menú proporcionado
products = {
    "Torta de Carne Asada": 110.0,
    "Torta de Cochinita Pibil": 90.0,
    "Torta Mixta": 125.0,
    "Tacos Carne Asada (5)": 110.0,
    "Tacos Cochinita Pibil (5)": 110.0,
    "Extra de Queso o Aguacate": 15.0,
    "Chile Chilaca Relleno": 75.0,
    "Cochichilaca": 110.0,
    "Volcán de Cochinita": 90.0,
    "Volcán de Carne Asada": 90.0,
    "Volcán Mixto": 90.0,
    "Tostada de Ceviche de Pescado": 45.0
}
# Variables globales
current_order = []  # Almacena el pedido actual
current_order_id = None  # Almacena el ID del pedido en edición
# Crear la ventana principal
root = tk.Tk()
root.title("Sistema de Comandas con Gestión de Pedidos")
# Variables de entrada de datos
customer_name_var = tk.StringVar()
table_number_var = tk.StringVar()
ticket_number_var = tk.StringVar()  # Para consultar un ticket específico
status_var = tk.StringVar(value="Pendiente")  # Estado inicial del pedido
# Función para agregar un producto a la lista
def add_product(product_name, price):
    """Agrega un producto a la lista de la comanda."""
    current_order.append((product_name, price))
    update_order_display()
# Función para eliminar un producto de la lista
def remove_product(index):
    """Elimina un producto de la lista de la comanda."""
    if index < len(current_order):
        del current_order[index]
        update_order_display()
# Función para actualizar la visualización de la comanda en la lista
def update_order_display():
    """Actualiza la lista de productos seleccionados."""
    order_list.delete(0, tk.END)
    total_price = 0
    for idx, (product, price) in enumerate(current_order):
        order_list.insert(tk.END, f"{product} - ${price:.2f}")
        total_price += price
    
    # Mostrar el total al final de la lista
    order_list.insert(tk.END, f"TOTAL: ${total_price:.2f}")
# Función para registrar la comanda en el CSV
def save_order():
    """Guarda la comanda actual en el archivo CSV."""
    customer_name = customer_name_var.get()
    table_number = table_number_var.get()
    if not customer_name or not table_number or not current_order:
        messagebox.showerror("Error", "Por favor, completa todos los campos y selecciona al menos un producto.")
        return
    # Calcular el total de la comanda
    total_price = sum([price for _, price in current_order])
    items_str = ", ".join([f"{product}" for product, _ in current_order])
    # Obtener la fecha y hora actual
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Si estamos editando un pedido existente
    if current_order_id is not None:
        update_order_in_csv(current_order_id, customer_name, table_number, items_str, total_price, timestamp, status_var.get())
        messagebox.showinfo("Éxito", f"Pedido {current_order_id} actualizado exitosamente. Total: ${total_price:.2f}")
    else:
        # Calcular el ID automáticamente basado en el número de filas en el archivo CSV
        with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)
            order_id = len(rows)
        # Registrar la comanda en el archivo CSV con estado inicial "Pendiente"
        with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([order_id, customer_name, table_number, items_str, total_price, timestamp, "Pendiente"])
        messagebox.showinfo("Éxito", f"Comanda registrada exitosamente. Número de Pedido: {order_id}, Total: ${total_price:.2f}")
    
    clear_order()
    load_all_orders()
# Función para actualizar un pedido en el archivo CSV
def update_order_in_csv(order_id, customer_name, table_number, items_str, total_price, timestamp, status):
    """Actualiza un pedido existente en el CSV."""
    orders = []
    with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        orders = list(reader)
    for i, order in enumerate(orders):
        if order[0].isdigit() and int(order[0]) == order_id:
            orders[i] = [order_id, customer_name, table_number, items_str, total_price, timestamp, status]
            break
    # Guardar las órdenes actualizadas en el archivo CSV
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(orders)
# Función para cargar un pedido existente para editarlo
def load_order():
    """Carga un pedido existente para editarlo según el número de pedido ingresado."""
    global current_order_id
    ticket_id = ticket_number_var.get()
    if not ticket_id.isdigit():
        messagebox.showerror("Error", "Por favor, ingresa un número de pedido válido.")
        return
    ticket_id = int(ticket_id)
    with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        orders = list(reader)[1:]  # Omitir encabezado
    for order in orders:
        if int(order[0]) == ticket_id:
            # Cargar los detalles del pedido
            current_order_id = ticket_id
            customer_name_var.set(order[1])
            table_number_var.set(order[2])
            status_var.set(order[6])
            items = order[3].split(", ")
            current_order.clear()
            for item in items:
                for product, price in products.items():
                    if product in item:
                        current_order.append((product, price))
            update_order_display()
            return
    # Si no se encuentra el pedido
    messagebox.showerror("Error", f"El pedido con el ID {ticket_id} no existe.")
# Función para cambiar el estado de un pedido
def change_order_status(new_status):
    """Cambia el estado del pedido seleccionado."""
    selected = order_management_list.curselection()
    if not selected:
        messagebox.showwarning("Advertencia", "Por favor, selecciona un pedido para cambiar su estado.")
        return
    # Obtener el ID del pedido seleccionado
    selected_order = order_management_list.get(selected[0])
    try:
        order_id = int(selected_order.split("|")[0].split(":")[1].strip())
    except ValueError:
        return  # Ignorar si el valor no es un número válido
    # Actualizar el estado en el CSV
    orders = []
    with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        orders = list(reader)
    for i, order in enumerate(orders):
        if order[0].isdigit() and int(order[0]) == order_id:
            orders[i][6] = new_status
            break
    # Guardar los cambios en el archivo CSV
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(orders)
    load_all_orders()
    messagebox.showinfo("Información", f"El pedido con ID {order_id} ha sido marcado como {new_status}.")
# Función para cargar todos los pedidos en la lista de gestión
def load_all_orders():
    """Carga todos los pedidos en la lista de gestión de pedidos."""
    order_management_list.delete(0, tk.END)
    with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        orders = list(reader)[1:]  # Omitir la primera fila (encabezado)
    for order in orders:
        order_management_list.insert(tk.END, f"ID: {order[0]} | Cliente: {order[1]} | Mesa: {order[2]} | Total: ${order[4]} | Estado: {order[6]}")
# Función para limpiar la lista de pedidos
def clear_order():
    """Limpia la lista de la comanda actual."""
    global current_order_id
    customer_name_var.set("")
    table_number_var.set("")
    status_var.set("Pendiente")
    current_order.clear()
    current_order_id = None
    update_order_display()
# Crear la interfaz gráfica para la selección de productos y la lista de la comanda
frame_left = tk.Frame(root, padx=20, pady=20)
frame_left.grid(row=0, column=0)
frame_right = tk.Frame(root, padx=20, pady=20)
frame_right.grid(row=0, column=1)
frame_bottom = tk.Frame(root, padx=20, pady=20)
frame_bottom.grid(row=1, column=0, columnspan=2)
frame_management = tk.Frame(root, padx=20, pady=20)
frame_management.grid(row=0, column=2)
# Panel Izquierdo para registrar comandas
tk.Label(frame_left, text="Nombre del Cliente:").pack(anchor="w")
tk.Entry(frame_left, textvariable=customer_name_var).pack(anchor="w")
tk.Label(frame_left, text="Número de Mesa:").pack(anchor="w")
tk.Entry(frame_left, textvariable=table_number_var).pack(anchor="w")
tk.Label(frame_left, text="Selecciona los Productos:").pack(anchor="w")
for product, price in products.items():
    tk.Button(frame_left, text=f"{product} - ${price:.2f}", width=40, command=lambda p=product, pr=price: add_product(p, pr)).pack(anchor="w")
# Botón adicional para la opción "Hazla Cochi"
tk.Button(frame_left, text="Hazla Cochi ($20)", width=40, command=lambda: add_product("Hazla Cochi", 20)).pack(anchor="w", pady=10)
# Panel derecho para mostrar la lista de pedidos
tk.Label(frame_right, text="Lista de Productos Seleccionados:").pack(anchor="w")
order_list = tk.Listbox(frame_right, width=50, height=15)
order_list.pack()
# Botón para eliminar un producto seleccionado
tk.Button(frame_right, text="Eliminar Producto Seleccionado", command=lambda: remove_product(order_list.curselection()[0])).pack(pady=10)
# Botón para registrar o actualizar la comanda
tk.Button(frame_right, text="Guardar/Actualizar Comanda", bg="lightgreen", command=save_order).pack(pady=10)
# Botón para limpiar la lista
tk.Button(frame_right, text="Limpiar Lista", bg="lightcoral", command=clear_order).pack(pady=10)
# Sección Inferior para consultar y editar tickets
tk.Label(frame_bottom, text="Consultar/Modificar Pedido por Número de Ticket:").grid(row=0, column=0)
tk.Entry(frame_bottom, textvariable=ticket_number_var).grid(row=0, column=1)
tk.Button(frame_bottom, text="Cargar Pedido", command=load_order).grid(row=0, column=2, padx=10)
# Sección de gestión de pedidos
tk.Label(frame_management, text="Gestión de Pedidos:").pack(anchor="w")
order_management_list = tk.Listbox(frame_management, width=60, height=20)
order_management_list.pack()
# Botones para cambiar el estado del pedido
tk.Button(frame_management, text="Marcar como Entregado", bg="lightblue", command=lambda: change_order_status("Entregado")).pack(pady=10)
tk.Button(frame_management, text="Marcar como Pendiente", bg="lightyellow", command=lambda: change_order_status("Pendiente")).pack(pady=10)
# Cargar todos los pedidos al inicio
load_all_orders()
if __name__ == '__main__':
    root.mainloop()