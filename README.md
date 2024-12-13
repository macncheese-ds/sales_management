# README

## Sistema de Comandas con Gestión de Pedidos

Este es un sistema desarrollado en Python utilizando `Tkinter` para la creación de una interfaz gráfica que permite registrar, modificar y gestionar pedidos en un restaurante. Los pedidos se almacenan en un archivo CSV, que incluye la información de los productos seleccionados, el cliente, la mesa, el total y el estado del pedido.

### Funcionalidades principales:

- **Registro de pedidos**: Los usuarios pueden ingresar los detalles del cliente (nombre, número de mesa) y seleccionar productos del menú para agregar a la comanda. El sistema calcula el total de la comanda automáticamente.
  
- **Actualización de pedidos**: Es posible editar un pedido existente a través de su número de ticket. Los cambios se reflejan tanto en la interfaz como en el archivo CSV.
  
- **Gestión de estado de pedidos**: Los usuarios pueden cambiar el estado de un pedido (Pendiente, Entregado) directamente desde la interfaz.
  
- **Lista de productos**: Los productos disponibles se muestran en un listado con su nombre y precio. Los usuarios pueden agregar o eliminar productos a medida que construyen su comanda.

- **Archivo CSV**: Los pedidos se almacenan en un archivo CSV (`comandas_estado.csv`). Si el archivo no existe, se crea automáticamente al iniciar el programa.

### Requisitos:

- Python 3.x
- Tkinter (para la interfaz gráfica)
- Librerías estándar de Python (os, csv, datetime)

### Instalación:

1. Clona este repositorio o descarga el archivo `main.py` en tu máquina local.
2. Asegúrate de tener instalada la versión adecuada de Python (Python 3.x).
3. Si no tienes Tkinter instalado, puedes instalarlo utilizando el siguiente comando:
   ```bash
   pip install tk
   ```
4. Ejecuta el script:
   ```bash
   python main.py
   ```

### Estructura del archivo CSV:

El archivo `comandas_estado.csv` contiene las siguientes columnas:

1. **ID**: Identificador único para cada pedido.
2. **Cliente**: Nombre del cliente que realiza el pedido.
3. **Número de Mesa**: El número de mesa asociado al pedido.
4. **Productos**: Los productos seleccionados en el pedido, separados por comas.
5. **Total**: El total del pedido calculado sumando los precios de los productos.
6. **Fecha y Hora**: La fecha y hora en que se registró el pedido.
7. **Estado**: El estado actual del pedido (Pendiente o Entregado).

### Uso de la interfaz:

- **Panel izquierdo**:
  - Ingrese el nombre del cliente y el número de mesa.
  - Seleccione los productos del menú haciendo clic en los botones correspondientes.
  - Use el botón "Hazla Cochi" para agregar un extra al pedido.
  
- **Panel derecho**:
  - Muestra la lista de productos seleccionados.
  - Permite eliminar un producto de la lista.
  - Permite guardar o actualizar un pedido.
  - Permite limpiar la lista de la comanda.

- **Sección inferior**:
  - Permite consultar y cargar un pedido existente ingresando el número de ticket.

- **Gestión de Pedidos**:
  - Visualiza todos los pedidos registrados.
  - Permite cambiar el estado de un pedido a "Entregado" o "Pendiente".

### Autor:

- **Desarrollado por**: Marcelo Morales
