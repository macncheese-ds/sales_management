# comandos: pip install PyQt6 matplotlib
from __future__ import annotations
import csv
import os
from datetime import datetime, date, timedelta
from typing import List, Tuple, Optional, Dict

from PyQt6.QtCore import Qt, QTimer, QDate
from PyQt6.QtGui import QAction, QPalette, QColor, QFont
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QMessageBox, QComboBox, QScrollArea, QFrame,
    QFileDialog, QGridLayout, QDateEdit, QSplitter, QTextEdit, QDialog,
    QFormLayout, QPlainTextEdit, QTableWidget, QTableWidgetItem
)

# --- Matplotlib embebido para gráficas ---
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# --------- Configuración y datos ---------
CSV_FILE = "comandas_estado.csv"

PRODUCTS = {
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
    "Tostada de Ceviche de Pescado": 45.0,
    "Hazla Cochi": 20.0,
}

# CSV con columna extra "Comentarios"
CSV_HEADER = ["ID", "Cliente", "Número de Mesa", "Productos", "Total", "Fecha y Hora", "Estado", "Comentarios"]

def ensure_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(CSV_HEADER)
        return
    with open(CSV_FILE, "r", newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    if not rows:
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(CSV_HEADER)
        return
    changed = rows[0] != CSV_HEADER
    norm = [CSV_HEADER]
    for r in rows[1:]:
        if not r:
            continue
        if len(r) < 8: r = r + [""] * (8 - len(r))
        elif len(r) > 8: r = r[:8]
        norm.append(r)
    if changed or len(norm) != len(rows):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(norm)

def read_orders() -> List[List[str]]:
    ensure_csv()
    with open(CSV_FILE, "r", newline="", encoding="utf-8") as f:
        return list(csv.reader(f))

def write_orders(all_rows: List[List[str]]):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(all_rows)

def next_order_id() -> int:
    rows = read_orders()
    ids = []
    for r in rows[1:]:
        try:
            ids.append(int(r[0]))
        except:
            pass
    return (max(ids) + 1) if ids else 1

def parse_dt(s: str) -> datetime:
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except:
        return datetime.min

def parse_products(items_str: str) -> List[str]:
    return [s.strip() for s in items_str.split(",") if s.strip()]

def dark_palette(app: QApplication):
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
    pal.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    pal.setColor(QPalette.ColorRole.Base, QColor(18, 18, 18))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor(30, 30, 30))
    pal.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    pal.setColor(QPalette.ColorRole.Button, QColor(45, 45, 45))
    pal.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    pal.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
    pal.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
    app.setPalette(pal)

# --------- Ventanas auxiliares ---------
class OrderDetailDialog(QDialog):
    """Detalle y edición rápida de un pedido."""
    def __init__(self, row: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Detalle del Pedido #{row[0]}")
        self.setMinimumWidth(520)
        self.row = row

        layout = QVBoxLayout(self)
        form = QFormLayout()
        f_big = QFont(); f_big.setPointSize(12); f_big.setBold(True)

        self.lbl_id = QLabel(row[0]); self.lbl_id.setFont(f_big)
        self.lbl_cliente = QLabel(row[1])
        self.lbl_mesa = QLabel(row[2])
        self.txt_prod = QPlainTextEdit(row[3]); self.txt_prod.setReadOnly(True); self.txt_prod.setFixedHeight(90)
        self.lbl_total = QLabel(f"${row[4]}")
        self.lbl_fecha = QLabel(row[5])

        self.cmb_estado = QComboBox(); self.cmb_estado.addItems(["Pendiente", "Entregado"])
        self.cmb_estado.setCurrentText(row[6] if row[6] in ["Pendiente", "Entregado"] else "Pendiente")

        self.txt_coment = QPlainTextEdit(row[7] if len(row) > 7 else ""); self.txt_coment.setFixedHeight(90)

        form.addRow("ID:", self.lbl_id)
        form.addRow("Cliente:", self.lbl_cliente)
        form.addRow("Mesa:", self.lbl_mesa)
        form.addRow("Productos:", self.txt_prod)
        form.addRow("Total:", self.lbl_total)
        form.addRow("Fecha/Hora:", self.lbl_fecha)
        form.addRow("Estado:", self.cmb_estado)
        form.addRow("Comentarios:", self.txt_coment)
        layout.addLayout(form)

        btns = QHBoxLayout()
        self.btn_save = QPushButton("Guardar cambios")
        self.btn_close = QPushButton("Cerrar")
        btns.addWidget(self.btn_save); btns.addStretch(); btns.addWidget(self.btn_close)
        layout.addLayout(btns)

        self.btn_save.clicked.connect(self.save_changes)
        self.btn_close.clicked.connect(self.accept)

    def save_changes(self):
        oid = int(self.row[0])
        rows = read_orders()
        for i, r in enumerate(rows):
            if i == 0: continue
            try:
                if int(r[0]) == oid:
                    rows[i][6] = self.cmb_estado.currentText()
                    rows[i][7] = self.txt_coment.toPlainText().strip()
                    break
            except:
                pass
        write_orders(rows)
        QMessageBox.information(self, "Guardado", f"Pedido {oid} actualizado.")
        self.accept()

class TicketWindow(QMainWindow):
    """Vista de UNA sola comanda estilo ‘ticket’ (se abre desde Cocina)."""
    def __init__(self, row: List[str]):
        super().__init__()
        self.setWindowTitle(f"Ticket #{row[0]}")
        self.resize(520, 680)

        central = QWidget(); self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(24, 24, 24, 24); root.setSpacing(12)

        cont = QFrame(); cont.setObjectName("TicketCard")
        cont.setStyleSheet("""
            QFrame#TicketCard { background: #111; border: 2px dashed #666; border-radius: 14px; }
            QLabel { color: #fff; }
        """)
        v = QVBoxLayout(cont); v.setContentsMargins(18, 18, 18, 18); v.setSpacing(10)

        h_title = QLabel(f"PEDIDO #{row[0]}  •  MESA {row[2]}")
        f_title = QFont(); f_title.setPointSize(20); f_title.setBold(True); h_title.setFont(f_title)
        cli = QLabel(f"Cliente: {row[1]}"); f_cli = QFont(); f_cli.setPointSize(18); cli.setFont(f_cli)

        prods = QLabel("Productos:\n" + row[3]); prods.setWordWrap(True); f_p = QFont(); f_p.setPointSize(18); prods.setFont(f_p)

        comentarios = QLabel("Comentarios: " + (row[7] if len(row) > 7 and row[7].strip() else "(sin comentarios)"))
        comentarios.setWordWrap(True); comentarios.setFont(f_p)

        total = QLabel(f"TOTAL: ${row[4]}"); f_tot = QFont(); f_tot.setPointSize(22); f_tot.setBold(True); total.setFont(f_tot)

        foot = QLabel(f"{row[6]}  •  {row[5]}"); f_foot = QFont(); f_foot.setPointSize(16); foot.setFont(f_foot)

        v.addWidget(h_title); v.addWidget(cli); v.addWidget(prods); v.addWidget(comentarios); v.addWidget(total); v.addWidget(foot)
        root.addWidget(cont)

        btns = QHBoxLayout()
        btn_full = QPushButton("Pantalla completa"); btn_full.clicked.connect(self.showMaximized)
        btn_close = QPushButton("Cerrar"); btn_close.clicked.connect(self.close)
        btns.addStretch(); btns.addWidget(btn_full); btns.addWidget(btn_close)
        root.addLayout(btns)

# ---------- Helpers de analítica ----------
def iso_week_range(d: date) -> tuple[date, date]:
    """Devuelve (lunes, domingo) de la semana ISO a la que pertenece d."""
    monday = d - timedelta(days=d.weekday())  # weekday(): 0=lunes ... 6=domingo
    sunday = monday + timedelta(days=6)
    return monday, sunday

def annotate_bars(ax, bars):
    """Escribe el valor encima de cada barra."""
    for rect in bars:
        height = rect.get_height()
        ax.annotate(f"{int(height)}",
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9)

class AnalyticsWindow(QDialog):
    """Analítica: tabla + gráficas (barras y donut) con modos General/Diario/Semanal."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Analítica de ventas por producto")
        self.resize(1000, 700)

        root = QVBoxLayout(self)

        # Controles
        ctrl = QHBoxLayout()
        self.mode = QComboBox(); self.mode.addItems(["General", "Diario", "Semanal"])
        ctrl.addWidget(QLabel("Modo:")); ctrl.addWidget(self.mode)
        self.date_pick = QDateEdit(); self.date_pick.setCalendarPopup(True); self.date_pick.setDate(QDate.currentDate())
        ctrl.addWidget(QLabel("Fecha base:")); ctrl.addWidget(self.date_pick)
        self.btn_calc = QPushButton("Calcular")
        self.btn_export = QPushButton("Exportar CSV…")
        ctrl.addStretch(); ctrl.addWidget(self.btn_calc); ctrl.addWidget(self.btn_export)
        root.addLayout(ctrl)

        # Tabla
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Producto", "Cantidad", "Importe", "Tickets distintos"])
        self.table.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self.table, 3)

        # Gráficas (barras + donut)
        charts_row = QHBoxLayout()
        self.fig_bar = Figure(figsize=(4, 3), dpi=100); self.canvas_bar = FigureCanvas(self.fig_bar); charts_row.addWidget(self.canvas_bar, 1)
        self.fig_pie = Figure(figsize=(4, 3), dpi=100); self.canvas_pie = FigureCanvas(self.fig_pie); charts_row.addWidget(self.canvas_pie, 1)
        root.addLayout(charts_row, 4)

        # Eventos
        self.btn_calc.clicked.connect(self.compute)
        self.btn_export.clicked.connect(self.export_csv)
        self.mode.currentIndexChanged.connect(self.compute)
        self.date_pick.dateChanged.connect(self.compute)

        self.compute()

    def _in_day(self, dt: datetime, day: date) -> bool:
        return dt.date() == day

    def _in_iso_week(self, dt: datetime, base_day: date) -> bool:
        y1, w1, _ = dt.date().isocalendar()
        y2, w2, _ = base_day.isocalendar()
        return (y1, w1) == (y2, w2)

    def _title_suffix(self, mode: str, base_day: date) -> str:
        if mode == "Diario":
            return base_day.strftime(" — %Y-%m-%d")
        if mode == "Semanal":
            start, end = iso_week_range(base_day)
            return f" — Semana ISO ({start.strftime('%Y-%m-%d')} a {end.strftime('%Y-%m-%d')})"
        return ""

    def compute(self):
        """Recalcula tabla + gráficas en función del modo/fecha."""
        rows = read_orders()
        data = rows[1:]

        mode = self.mode.currentText()
        base_qd = self.date_pick.date()
        base_day = date(base_qd.year(), base_qd.month(), base_qd.day())

        # Agregación
        counts: Dict[str, int] = {}
        totals: Dict[str, float] = {}
        tickets_by_product: Dict[str, set] = {}

        for r in data:
            dt = parse_dt(r[5])
            if mode == "Diario" and not self._in_day(dt, base_day):
                continue
            if mode == "Semanal" and not self._in_iso_week(dt, base_day):
                continue

            items = parse_products(r[3])
            ticket_id = r[0]
            for it in items:
                name = it
                counts[name] = counts.get(name, 0) + 1
                price = PRODUCTS.get(name, 0.0)
                totals[name] = totals.get(name, 0.0) + (price or 0.0)
                tickets_by_product.setdefault(name, set()).add(ticket_id)

        # Orden por cantidad desc
        items_sorted = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)

        # --- Tabla ---
        self.table.setRowCount(len(items_sorted))
        for i, (name, qty) in enumerate(items_sorted):
            self.table.setItem(i, 0, QTableWidgetItem(name))
            self.table.setItem(i, 1, QTableWidgetItem(str(qty)))
            self.table.setItem(i, 2, QTableWidgetItem(f"${totals.get(name, 0.0):.2f}"))
            self.table.setItem(i, 3, QTableWidgetItem(str(len(tickets_by_product.get(name, set())))))

        # --- Barras bonitas ---
        self.fig_bar.clear()
        axb = self.fig_bar.add_subplot(111)
        axb.grid(axis='y', linestyle='--', alpha=0.4)
        axb.set_axisbelow(True)

        title_suf = self._title_suffix(mode, base_day)
        axb.set_title("Top productos por cantidad" + title_suf)

        if items_sorted:
            # Top dinámico (hasta 12)
            labels = [n for n, _ in items_sorted[:12]]
            values = [counts[n] for n in labels]
            bars = axb.bar(range(len(labels)), values)
            axb.set_xticks(range(len(labels)))
            axb.set_xticklabels(labels, rotation=35, ha='right')
            axb.set_ylabel("Cantidad")
            annotate_bars(axb, bars)
        else:
            axb.text(0.5, 0.5, "Sin datos", ha='center', va='center', transform=axb.transAxes)

        self.fig_bar.tight_layout()
        self.canvas_bar.draw()
        self.canvas_bar.repaint()

        # --- Donut (pastel con hueco) ---
        self.fig_pie.clear()
        axp = self.fig_pie.add_subplot(111)
        axp.set_title("Distribución de ventas" + title_suf)

        if items_sorted:
            labels = [n for n, _ in items_sorted[:8]]
            values = [counts[n] for n in labels]
            wedges, texts, autotexts = axp.pie(
                values,
                labels=labels,
                autopct="%1.0f%%",
                startangle=90,
                wedgeprops={"width": 0.45, "edgecolor": "white"}  # donut
            )
            # Centrar donut
            axp.axis('equal')
        else:
            axp.text(0.5, 0.5, "Sin datos", ha='center', va='center', transform=axp.transAxes)

        self.fig_pie.tight_layout()
        self.canvas_pie.draw()
        self.canvas_pie.repaint()

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exportar CSV", "reporte_ventas.csv", "CSV (*.csv)")
        if not path:
            return
        out = []
        for r in range(self.table.rowCount()):
            out.append([
                self.table.item(r, 0).text() if self.table.item(r, 0) else "",
                self.table.item(r, 1).text() if self.table.item(r, 1) else "",
                self.table.item(r, 2).text() if self.table.item(r, 2) else "",
                self.table.item(r, 3).text() if self.table.item(r, 3) else "",
            ])
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["Producto", "Cantidad", "Importe", "Tickets distintos"]); w.writerows(out)
        QMessageBox.information(self, "Exportado", f"Archivo guardado en {path}")

# --------- Tarjeta de pedido (boleta) ---------
class OrderCard(QFrame):
    def __init__(self, row: List[str], on_mark_delivered, on_view_detail, on_view_ticket):
        super().__init__()
        self.setObjectName("OrderCard")
        self.setFrameShape(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame#OrderCard { background-color: #222; border: 2px solid #444; border-radius: 16px; }
            QLabel { color: #fff; }
            QPushButton { padding: 10px 14px; border-radius: 10px; background: #2e7d32; color: white; font-weight: 600; }
            QPushButton#Secondary { background: #616161; }
        """)
        layout = QVBoxLayout(self); layout.setContentsMargins(16, 16, 16, 16); layout.setSpacing(10)

        title_font = QFont(); title_font.setPointSize(18); title_font.setBold(True)
        body_font = QFont(); body_font.setPointSize(16)
        small_font = QFont(); small_font.setPointSize(14)

        top = QLabel(f"ID #{row[0]}  |  Mesa {row[2]}"); top.setFont(title_font)
        cliente = QLabel(f"Cliente: {row[1]}"); cliente.setFont(body_font)
        prods = QLabel(f"Productos:\n{row[3]}"); prods.setWordWrap(True); prods.setFont(body_font)
        prods.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        comentarios = QLabel(f"Comentarios: {(row[7] if len(row) > 7 and row[7].strip() else '(sin comentarios)')}"); comentarios.setWordWrap(True); comentarios.setFont(body_font)
        footer = QLabel(f"Total: ${row[4]}   •   {row[6]}   •   {row[5]}"); footer.setFont(small_font)

        btns = QHBoxLayout()
        deliver_btn = QPushButton("Entregado"); deliver_btn.clicked.connect(lambda: on_mark_delivered(int(row[0])))
        view_btn = QPushButton("Ver"); view_btn.setObjectName("Secondary"); view_btn.clicked.connect(lambda: on_view_detail(row))
        ticket_btn = QPushButton("Ticket"); ticket_btn.setObjectName("Secondary"); ticket_btn.clicked.connect(lambda: on_view_ticket(row))
        copy_btn = QPushButton("Copiar"); copy_btn.setObjectName("Secondary"); copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(row[3]))

        layout.addWidget(top); layout.addWidget(cliente); layout.addWidget(prods); layout.addWidget(comentarios); layout.addWidget(footer)
        for b in (deliver_btn, view_btn, ticket_btn, copy_btn): btns.addWidget(b)
        layout.addLayout(btns)

# --------- Ventana de Cocina ---------
class KitchenWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cocina - Pedidos")
        self.resize(1100, 750)

        central = QWidget(); self.setCentralWidget(central)
        root = QVBoxLayout(central); root.setContentsMargins(12, 12, 12, 12); root.setSpacing(10)

        ctrl_row = QHBoxLayout(); root.addLayout(ctrl_row)
        ctrl_row.addWidget(QLabel("Fecha:"))
        self.date_picker = QDateEdit(); self.date_picker.setCalendarPopup(True); self.date_picker.setDate(QDate.currentDate())
        ctrl_row.addWidget(self.date_picker)
        ctrl_row.addWidget(QLabel("Estado:"))
        self.filter_combo = QComboBox(); self.filter_combo.addItems(["Pendiente", "Todos", "Entregado"])
        ctrl_row.addWidget(self.filter_combo)
        self.columns_combo = QComboBox(); self.columns_combo.addItems(["2 columnas", "3 columnas"])
        ctrl_row.addWidget(self.columns_combo)
        self.refresh_btn = QPushButton("Refrescar"); ctrl_row.addWidget(self.refresh_btn); ctrl_row.addStretch()

        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True); root.addWidget(self.scroll)
        self.grid_host = QWidget(); self.scroll.setWidget(self.grid_host)
        self.grid = QGridLayout(self.grid_host); self.grid.setContentsMargins(4, 4, 4, 4)
        self.grid.setHorizontalSpacing(12); self.grid.setVerticalSpacing(12)

        self.refresh_btn.clicked.connect(self.refresh)
        self.filter_combo.currentIndexChanged.connect(self.refresh)
        self.columns_combo.currentIndexChanged.connect(self.refresh)
        self.date_picker.dateChanged.connect(self.refresh)

        self.timer = QTimer(self); self.timer.setInterval(10_000)
        self.timer.timeout.connect(self.refresh); self.timer.start()

        self.refresh()

    def current_columns(self) -> int:
        return 3 if self.columns_combo.currentIndex() == 1 else 2

    def clear_grid(self):
        while self.grid.count():
            it = self.grid.takeAt(0)
            w = it.widget()
            if w:
                w.setParent(None); w.deleteLater()

    def refresh(self):
        rows = read_orders()
        data = rows[1:]
        data.sort(key=lambda r: parse_dt(r[5]))

        qd = self.date_picker.date()
        selected_day = date(qd.year(), qd.month(), qd.day())
        data = [r for r in data if parse_dt(r[5]).date() == selected_day]

        st = self.filter_combo.currentText()
        if st != "Todos":
            data = [r for r in data if r[6] == st]

        self.clear_grid()
        cols = self.current_columns()
        ri = ci = 0
        for r in data:
            card = OrderCard(r, self.mark_delivered, self.open_detail, self.open_ticket)
            card.setMinimumSize(340, 240)
            self.grid.addWidget(card, ri, ci)
            ci += 1
            if ci >= cols:
                ci = 0; ri += 1

        if not data:
            lbl = QLabel("Sin pedidos para mostrar en ese día.")
            f = QFont(); f.setPointSize(18); f.setBold(True)
            lbl.setFont(f); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid.addWidget(lbl, 0, 0, 1, cols)

    def mark_delivered(self, order_id: int):
        rows = read_orders()
        for i, r in enumerate(rows):
            if i == 0: continue
            try:
                if int(r[0]) == order_id:
                    rows[i][6] = "Entregado"; break
            except:
                pass
        write_orders(rows); self.refresh()
        QMessageBox.information(self, "OK", f"Pedido {order_id} marcado como Entregado.")

    def open_detail(self, row: List[str]):
        dlg = OrderDetailDialog(row, self)
        dlg.exec(); self.refresh()

    def open_ticket(self, row: List[str]):
        win = TicketWindow(row)
        win.showMaximized()
        # guarda referencia para evitar GC
        self._ticket_win = win

# --------- Ventana Principal ---------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Comandas con Gestión de Pedidos - PyQt6")
        self.resize(1300, 800)

        self.current_order: List[Tuple[str, float]] = []
        self.current_order_id: Optional[int] = None

        # Menús
        kitchen_action = QAction("Abrir pantalla de cocina", self)
        kitchen_action.triggered.connect(self.open_kitchen)
        open_csv_action = QAction("Abrir CSV…", self)
        open_csv_action.triggered.connect(self.open_csv_folder)
        analytics_action = QAction("Analítica de ventas", self)
        analytics_action.triggered.connect(self.open_analytics)

        menu = self.menuBar().addMenu("Ventanas"); menu.addAction(kitchen_action)
        tools = self.menuBar().addMenu("Herramientas"); tools.addAction(open_csv_action); tools.addAction(analytics_action)

        # Layout principal
        central = QWidget(); self.setCentralWidget(central)
        root = QHBoxLayout(central)

        # ---- Panel izquierdo (datos + productos) ----
        left = QVBoxLayout(); root.addLayout(left, 1)
        left.addWidget(QLabel("Nombre del Cliente:")); self.customer_name = QLineEdit(); left.addWidget(self.customer_name)
        left.addWidget(QLabel("Número de Mesa:")); self.table_number = QLineEdit(); left.addWidget(self.table_number)
        left.addWidget(QLabel("Comentarios (nota):"))
        self.comments_edit = QTextEdit(); self.comments_edit.setPlaceholderText("Ej.: sin cebolla, sin picante, partir a la mitad, etc.")
        self.comments_edit.setFixedHeight(80); left.addWidget(self.comments_edit)
        left.addWidget(QLabel("Selecciona los Productos:"))
        scroll = QScrollArea(); scroll.setWidgetResizable(True); left.addWidget(scroll)
        prod_container = QWidget(); scroll.setWidget(prod_container)
        prod_layout = QVBoxLayout(prod_container)
        for name, price in PRODUCTS.items():
            btn = QPushButton(f"{name} - ${price:.2f}")
            btn.clicked.connect(lambda _, n=name, p=price: self.add_product(n, p))
            btn.setMinimumHeight(34); prod_layout.addWidget(btn)
        prod_layout.addStretch()

        # ---- Panel medio (lista y acciones) ----
        right = QVBoxLayout(); root.addLayout(right, 1)
        right.addWidget(QLabel("Productos en la Comanda:"))
        self.order_list = QListWidget(); self.order_list.setMinimumHeight(260); right.addWidget(self.order_list)
        del_btn = QPushButton("Eliminar Producto Seleccionado"); del_btn.clicked.connect(self.remove_selected_product); right.addWidget(del_btn)
        save_btn = QPushButton("Guardar / Actualizar Comanda"); save_btn.clicked.connect(self.save_order); right.addWidget(save_btn)
        clear_btn = QPushButton("Limpiar Lista"); clear_btn.clicked.connect(self.clear_order); right.addWidget(clear_btn)
        bottom = QHBoxLayout(); right.addLayout(bottom)
        bottom.addWidget(QLabel("Consultar/Modificar por ID:"))
        self.ticket_edit = QLineEdit(); bottom.addWidget(self.ticket_edit)
        load_btn = QPushButton("Cargar Pedido"); load_btn.clicked.connect(self.load_order); bottom.addWidget(load_btn)

        # ---- Gestión por día con dos listas ----
        manage_box = QVBoxLayout(); root.addLayout(manage_box, 1)
        header_row = QHBoxLayout(); manage_box.addLayout(header_row)
        header_row.addWidget(QLabel("Gestión de Pedidos por día:")); header_row.addStretch()
        header_row.addWidget(QLabel("Fecha:"))
        self.date_picker = QDateEdit(); self.date_picker.setCalendarPopup(True); self.date_picker.setDate(QDate.currentDate())
        header_row.addWidget(self.date_picker)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        manage_box.addWidget(splitter, 1)

        pending_panel = QWidget(); pending_layout = QVBoxLayout(pending_panel)
        lbl_pend = QLabel("Pendientes"); f1 = QFont(); f1.setPointSize(12); f1.setBold(True); lbl_pend.setFont(f1)
        pending_layout.addWidget(lbl_pend)
        self.manage_list_pending = QListWidget(); pending_layout.addWidget(self.manage_list_pending, 1)
        splitter.addWidget(pending_panel)

        delivered_panel = QWidget(); delivered_layout = QVBoxLayout(delivered_panel)
        lbl_ent = QLabel("Entregados"); f2 = QFont(); f2.setPointSize(12); f2.setBold(True); lbl_ent.setFont(f2)
        delivered_layout.addWidget(lbl_ent)
        self.manage_list_delivered = QListWidget(); delivered_layout.addWidget(self.manage_list_delivered, 1)
        splitter.addWidget(delivered_panel)

        actions_row = QHBoxLayout(); manage_box.addLayout(actions_row)
        mark_delivered = QPushButton("Marcar como Entregado"); mark_delivered.clicked.connect(lambda: self.change_order_status("Entregado"))
        actions_row.addWidget(mark_delivered)
        mark_pending = QPushButton("Marcar como Pendiente"); mark_pending.clicked.connect(lambda: self.change_order_status("Pendiente"))
        actions_row.addWidget(mark_pending)
        actions_row.addStretch()

        self.btn_detail = QPushButton("Ver detalle del pedido seleccionado")
        self.btn_detail.clicked.connect(self.open_detail_from_list)
        manage_box.addWidget(self.btn_detail)

        # Doble clic abre detalle
        self.manage_list_pending.itemDoubleClicked.connect(self.open_detail_from_list)
        self.manage_list_delivered.itemDoubleClicked.connect(self.open_detail_from_list)

        self.date_picker.dateChanged.connect(self.load_all_orders_for_day)

        # Init
        self.load_all_orders_for_day()
        self.update_order_display()

    # --------- Utilidades UI ---------
    def open_kitchen(self):
        self.kitchen = KitchenWindow()
        self.kitchen.showMaximized()

    def open_csv_folder(self):
        path = os.path.abspath(CSV_FILE)
        folder = os.path.dirname(path)
        QFileDialog.getOpenFileName(self, "Abrir CSV", folder, "CSV (*.csv)")

    def open_analytics(self):
        dlg = AnalyticsWindow(self)
        dlg.exec()

    # --------- Lógica de comanda ---------
    def add_product(self, name: str, price: float):
        self.current_order.append((name, price))
        self.update_order_display()

    def remove_selected_product(self):
        idx = self.order_list.currentRow()
        if 0 <= idx < len(self.current_order):
            self.current_order.pop(idx); self.update_order_display()

    def update_order_display(self):
        self.order_list.clear()
        total = 0.0
        for item, price in self.current_order:
            self.order_list.addItem(f"{item} - ${price:.2f}")
            total += price
        self.order_list.addItem(f"TOTAL: ${total:.2f}")

    def save_order(self):
        name = self.customer_name.text().strip()
        table = self.table_number.text().strip()
        comments = self.comments_edit.toPlainText().strip()
        if not name or not table or not self.current_order:
            QMessageBox.critical(self, "Error", "Completa nombre, mesa y agrega al menos un producto.")
            return
        total = sum(p for _, p in self.current_order)
        items_str = ", ".join([n for n, _ in self.current_order])
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if self.current_order_id is not None:
            rows = read_orders()
            for i, r in enumerate(rows):
                if i == 0: continue
                try:
                    if int(r[0]) == self.current_order_id:
                        estado = r[6] if len(r) > 6 and r[6] else "Pendiente"
                        rows[i] = [str(self.current_order_id), name, table, items_str, f"{total}", ts, estado, comments]
                        break
                except:
                    pass
            write_orders(rows)
            QMessageBox.information(self, "Éxito", f"Pedido {self.current_order_id} actualizado. Total: ${total:.2f}")
        else:
            oid = next_order_id()
            rows = read_orders()
            rows.append([str(oid), name, table, items_str, f"{total}", ts, "Pendiente", comments])
            write_orders(rows)
            QMessageBox.information(self, "Éxito", f"Comanda registrada. ID: {oid}  Total: ${total:.2f}")

        self.clear_order(); self.load_all_orders_for_day()

    def load_order(self):
        text = self.ticket_edit.text().strip()
        if not text.isdigit():
            QMessageBox.critical(self, "Error", "Ingresa un ID numérico válido."); return
        oid = int(text)
        rows = read_orders()
        found = None
        for r in rows[1:]:
            try:
                if int(r[0]) == oid:
                    found = r; break
            except:
                pass
        if not found:
            QMessageBox.critical(self, "Error", f"No existe el pedido con ID {oid}."); return

        self.current_order_id = oid
        self.customer_name.setText(found[1]); self.table_number.setText(found[2])
        self.comments_edit.setPlainText(found[7] if len(found) > 7 else "")
        self.current_order.clear()
        for it in parse_products(found[3]):
            self.current_order.append((it, PRODUCTS.get(it, 0.0)))
        self.update_order_display()

    def change_order_status(self, new_status: str):
        oid = self._selected_order_id_from_lists()
        if oid is None:
            QMessageBox.warning(self, "Aviso", "Selecciona un pedido en alguna de las listas."); return
        rows = read_orders()
        for i, r in enumerate(rows):
            if i == 0: continue
            try:
                if int(r[0]) == oid:
                    rows[i][6] = new_status; break
            except:
                pass
        write_orders(rows); self.load_all_orders_for_day()
        QMessageBox.information(self, "OK", f"Pedido {oid} marcado como {new_status}.")

    def _selected_order_id_from_lists(self) -> Optional[int]:
        def parse_from(text: str) -> Optional[int]:
            try: return int(text.split("|")[0].split(":")[1].strip())
            except: return None
        it = self.manage_list_pending.currentItem()
        if it:
            oid = parse_from(it.text())
            if oid is not None: return oid
        it = self.manage_list_delivered.currentItem()
        if it:
            oid = parse_from(it.text())
            if oid is not None: return oid
        return None

    def load_all_orders_for_day(self):
        self.manage_list_pending.clear(); self.manage_list_delivered.clear()
        rows = read_orders(); data = rows[1:]
        qd = self.date_picker.date()
        selected_day = date(qd.year(), qd.month(), qd.day())
        filtered = [r for r in data if parse_dt(r[5]).date() == selected_day]
        filtered.sort(key=lambda r: parse_dt(r[5]))
        for r in filtered:
            has_note = " • Nota" if (len(r) > 7 and r[7].strip()) else ""
            line = f"ID: {r[0]} | Cliente: {r[1]} | Mesa: {r[2]} | Total: ${r[4]} | Estado: {r[6]} | {r[5]}{has_note}"
            if r[6] == "Entregado": self.manage_list_delivered.addItem(line)
            else: self.manage_list_pending.addItem(line)

    def open_detail_from_list(self, *_):
        oid = self._selected_order_id_from_lists()
        if oid is None:
            QMessageBox.warning(self, "Aviso", "Selecciona un pedido para ver detalle."); return
        rows = read_orders(); found = None
        for r in rows[1:]:
            try:
                if int(r[0]) == oid:
                    found = r; break
            except:
                pass
        if not found:
            QMessageBox.critical(self, "Error", f"No se encontró el pedido {oid}."); return
        dlg = OrderDetailDialog(found, self); dlg.exec()
        self.load_all_orders_for_day()

    def clear_order(self):
        self.current_order_id = None
        self.customer_name.clear(); self.table_number.clear(); self.comments_edit.clear()
        self.current_order.clear(); self.update_order_display()

# --------- Main ---------
def main():
    import sys
    app = QApplication(sys.argv)
    dark_palette(app)
    w = MainWindow(); w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    ensure_csv()
    main()