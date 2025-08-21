from __future__ import annotations
import csv
import os
import json
from datetime import datetime, date, timedelta
from typing import List, Tuple, Optional, Dict

from PyQt6.QtCore import Qt, QTimer, QDate
from PyQt6.QtGui import QAction, QPalette, QColor, QFont
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QMessageBox, QComboBox, QScrollArea, QFrame,
    QFileDialog, QGridLayout, QDateEdit, QSplitter, QTextEdit, QDialog,
    QFormLayout, QTableWidget, QTableWidgetItem, QDoubleSpinBox
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

CSV_FILE = "comandas_estado.csv"
CAJA_FILE = "caja_movimientos.csv"
CONFIG_FILE = "config_caja.json"

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

CSV_HEADER = [
    "ID","Cliente","Número de Mesa","Productos","Total","Fecha y Hora","Estado","Comentarios",
    "MetodoPago","EfectivoIngresado","TarjetaIngresado","Cambio","Restante"
]

CAJA_HEADER = [
    "Timestamp","Tipo","OrderID","IngresoEfectivo","EgresoEfectivo","Nota","SaldoCaja"
]

def ensure_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE,"w",newline="",encoding="utf-8") as f:
            csv.writer(f).writerow(CSV_HEADER)
        return
    with open(CSV_FILE,"r",newline="",encoding="utf-8") as f:
        rows=list(csv.reader(f))
    if not rows:
        with open(CSV_FILE,"w",newline="",encoding="utf-8") as f:
            csv.writer(f).writerow(CSV_HEADER)
        return
    changed=rows[0]!=CSV_HEADER
    norm=[CSV_HEADER]
    for r in rows[1:]:
        if not r: continue
        if len(r)<len(CSV_HEADER): r=r+[""]*(len(CSV_HEADER)-len(r))
        elif len(r)>len(CSV_HEADER): r=r[:len(CSV_HEADER)]
        norm.append(r)
    if changed or len(norm)!=len(rows):
        with open(CSV_FILE,"w",newline="",encoding="utf-8") as f:
            csv.writer(f).writerows(norm)

def ensure_caja():
    if not os.path.exists(CAJA_FILE):
        with open(CAJA_FILE,"w",newline="",encoding="utf-8") as f:
            csv.writer(f).writerow(CAJA_HEADER)

def caja_saldo_actual() -> float:
    ensure_caja()
    saldo=0.0
    with open(CAJA_FILE,"r",newline="",encoding="utf-8") as f:
        rows=list(csv.reader(f))
        if len(rows)<=1: return 0.0
        try: saldo=float(rows[-1][-1])
        except: saldo=0.0
    return saldo

def apertura_existente(fecha_str:str) -> bool:
    ensure_caja()
    with open(CAJA_FILE,"r",newline="",encoding="utf-8") as f:
        rows=list(csv.reader(f))
    for r in rows[1:]:
        try:
            if r[1]=="FONDO_INICIAL" and r[0].split(" ")[0]==fecha_str:
                return True
        except:
            pass
    return False

def caja_registrar(tipo:str, order_id:str, ingreso_ef:float, egreso_ef:float, nota:str):
    ensure_caja()
    saldo=caja_saldo_actual()+ingreso_ef-egreso_ef
    with open(CAJA_FILE,"a",newline="",encoding="utf-8") as f:
        w=csv.writer(f)
        w.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"),tipo,order_id,f"{ingreso_ef:.2f}",f"{egreso_ef:.2f}",nota,f"{saldo:.2f}"])

def read_orders()->List[List[str]]:
    ensure_csv()
    with open(CSV_FILE,"r",newline="",encoding="utf-8") as f:
        return list(csv.reader(f))

def write_orders(all_rows:List[List[str]]):
    with open(CSV_FILE,"w",newline="",encoding="utf-8") as f:
        csv.writer(f).writerows(all_rows)

def next_order_id()->int:
    rows=read_orders()
    ids=[]
    for r in rows[1:]:
        try: ids.append(int(r[0]))
        except: pass
    return (max(ids)+1) if ids else 1

def parse_dt(s:str)->datetime:
    try: return datetime.strptime(s,"%Y-%m-%d %H:%M:%S")
    except: return datetime.min

def parse_products(items_str:str)->List[str]:
    return [s.strip() for s in items_str.split(",") if s.strip()]

def dark_palette(app:QApplication):
    pal=QPalette()
    pal.setColor(QPalette.ColorRole.Window,QColor(30,30,30))
    pal.setColor(QPalette.ColorRole.WindowText,Qt.GlobalColor.white)
    pal.setColor(QPalette.ColorRole.Base,QColor(18,18,18))
    pal.setColor(QPalette.ColorRole.AlternateBase,QColor(30,30,30))
    pal.setColor(QPalette.ColorRole.Text,Qt.GlobalColor.white)
    pal.setColor(QPalette.ColorRole.Button,QColor(45,45,45))
    pal.setColor(QPalette.ColorRole.ButtonText,Qt.GlobalColor.white)
    pal.setColor(QPalette.ColorRole.Highlight,QColor(0,120,215))
    pal.setColor(QPalette.ColorRole.HighlightedText,Qt.GlobalColor.white)
    app.setPalette(pal)

def light_palette(app:QApplication):
    app.setPalette(app.style().standardPalette())

class TicketWindow(QMainWindow):
    def __init__(self, row:List[str]):
        super().__init__()
        self.setWindowTitle(f"Ticket #{row[0]}")
        self.resize(520,680)
        central=QWidget(); self.setCentralWidget(central)
        root=QVBoxLayout(central)
        root.setContentsMargins(24,24,24,24); root.setSpacing(12)
        cont=QFrame(); cont.setObjectName("TicketCard")
        cont.setStyleSheet("QFrame#TicketCard { background: #111; border: 2px dashed #666; border-radius: 14px; } QLabel { color: #fff; }")
        v=QVBoxLayout(cont); v.setContentsMargins(18,18,18,18); v.setSpacing(10)
        h_title=QLabel(f"PEDIDO #{row[0]}  •  MESA {row[2]}")
        f_title=QFont(); f_title.setPointSize(20); f_title.setBold(True); h_title.setFont(f_title)
        cli=QLabel(f"Mesa: {row[2]}"); f_cli=QFont(); f_cli.setPointSize(18); cli.setFont(f_cli)
        prods=QLabel("Productos:\n"+row[3]); prods.setWordWrap(True); f_p=QFont(); f_p.setPointSize(18); prods.setFont(f_p)
        comentarios=QLabel("Comentarios: "+(row[7] if len(row)>7 and row[7].strip() else "(sin comentarios)"))
        comentarios.setWordWrap(True); comentarios.setFont(f_p)
        total=QLabel(f"TOTAL: ${row[4]}"); f_tot=QFont(); f_tot.setPointSize(22); f_tot.setBold(True); total.setFont(f_tot)
        foot=QLabel(f"{row[6]}  •  {row[5]}"); f_foot=QFont(); f_foot.setPointSize(16); foot.setFont(f_foot)
        v.addWidget(h_title); v.addWidget(cli); v.addWidget(prods); v.addWidget(comentarios); v.addWidget(total); v.addWidget(foot)
        root.addWidget(cont)
        btns=QHBoxLayout()
        btn_full=QPushButton("Pantalla completa"); btn_full.clicked.connect(self.showMaximized)
        btn_close=QPushButton("Cerrar"); btn_close.clicked.connect(self.close)
        for b in (btn_full,btn_close): _make_big(b)
        btns.addStretch(); btns.addWidget(btn_full); btns.addWidget(btn_close)
        root.addLayout(btns)

def iso_week_range(d:date)->tuple[date,date]:
    monday=d-timedelta(days=d.weekday())
    sunday=monday+timedelta(days=6)
    return monday,sunday

def annotate_bars(ax,bars):
    for rect in bars:
        h=rect.get_height()
        ax.annotate(f"{int(h)}",xy=(rect.get_x()+rect.get_width()/2,h),xytext=(0,3),textcoords="offset points",ha="center",va="bottom",fontsize=9)

class AnalyticsWindow(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowTitle("Analítica de ventas por producto")
        self.resize(1000,700)
        root=QVBoxLayout(self)
        ctrl=QHBoxLayout()
        self.mode=QComboBox(); self.mode.addItems(["General","Diario","Semanal"])
        ctrl.addWidget(QLabel("Modo:")); ctrl.addWidget(self.mode)
        self.date_pick=QDateEdit(); self.date_pick.setCalendarPopup(True); self.date_pick.setDate(QDate.currentDate())
        ctrl.addWidget(QLabel("Fecha base:")); ctrl.addWidget(self.date_pick)
        self.btn_calc=QPushButton("Calcular")
        self.btn_export=QPushButton("Exportar CSV…")
        for b in (self.btn_calc,self.btn_export): _make_big(b)
        ctrl.addStretch(); ctrl.addWidget(self.btn_calc); ctrl.addWidget(self.btn_export)
        root.addLayout(ctrl)
        self.table=QTableWidget(0,4)
        self.table.setHorizontalHeaderLabels(["Producto","Cantidad","Importe","Tickets distintos"])
        self.table.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self.table,3)
        charts_row=QHBoxLayout()
        self.fig_bar=Figure(figsize=(4,3),dpi=100); self.canvas_bar=FigureCanvas(self.fig_bar); charts_row.addWidget(self.canvas_bar,1)
        self.fig_pie=Figure(figsize=(4,3),dpi=100); self.canvas_pie=FigureCanvas(self.fig_pie); charts_row.addWidget(self.canvas_pie,1)
        root.addLayout(charts_row,4)
        self.btn_calc.clicked.connect(self.compute)
        self.btn_export.clicked.connect(self.export_csv)
        self.mode.currentIndexChanged.connect(self.compute)
        self.date_pick.dateChanged.connect(self.compute)
        self.compute()

    def _in_day(self,dt:datetime,day:date)->bool:
        return dt.date()==day

    def _in_iso_week(self,dt:datetime,base_day:date)->bool:
        y1,w1,_=dt.date().isocalendar()
        y2,w2,_=base_day.isocalendar()
        return (y1,w1)==(y2,w2)

    def _title_suffix(self,mode:str,base_day:date)->str:
        if mode=="Diario":
            return base_day.strftime(" — %Y-%m-%d")
        if mode=="Semanal":
            start,end=iso_week_range(base_day)
            return f" — Semana ISO ({start.strftime('%Y-%m-%d')} a {end.strftime('%Y-%m-%d')})"
        return ""

    def compute(self):
        rows=read_orders()
        data=rows[1:]
        mode=self.mode.currentText()
        base_qd=self.date_pick.date()
        base_day=date(base_qd.year(),base_qd.month(),base_qd.day())
        counts:Dict[str,int]={}
        totals:Dict[str,float]={}
        tickets_by_product:Dict[str,set]={}
        for r in data:
            dt=parse_dt(r[5])
            if mode=="Diario" and not self._in_day(dt,base_day): continue
            if mode=="Semanal" and not self._in_iso_week(dt,base_day): continue
            items=parse_products(r[3])
            ticket_id=r[0]
            for it in items:
                counts[it]=counts.get(it,0)+1
                price=PRODUCTS.get(it,0.0)
                totals[it]=totals.get(it,0.0)+(price or 0.0)
                tickets_by_product.setdefault(it,set()).add(ticket_id)
        items_sorted=sorted(counts.items(),key=lambda kv:kv[1],reverse=True)
        self.table.setRowCount(len(items_sorted))
        for i,(name,qty) in enumerate(items_sorted):
            self.table.setItem(i,0,QTableWidgetItem(name))
            self.table.setItem(i,1,QTableWidgetItem(str(qty)))
            self.table.setItem(i,2,QTableWidgetItem(f"${totals.get(name,0.0):.2f}"))
            self.table.setItem(i,3,QTableWidgetItem(str(len(tickets_by_product.get(name,set())))))
        self.fig_bar.clear()
        axb=self.fig_bar.add_subplot(111)
        axb.grid(axis="y",linestyle="--",alpha=0.4)
        axb.set_axisbelow(True)
        title_suf=self._title_suffix(mode,base_day)
        axb.set_title("Top productos por cantidad"+title_suf)
        if items_sorted:
            labels=[n for n,_ in items_sorted[:12]]
            values=[counts[n] for n in labels]
            bars=axb.bar(range(len(labels)),values)
            axb.set_xticks(range(len(labels)))
            axb.set_xticklabels(labels,rotation=35,ha="right")
            axb.set_ylabel("Cantidad")
            annotate_bars(axb,bars)
        else:
            axb.text(0.5,0.5,"Sin datos",ha="center",va="center",transform=axb.transAxes)
        self.fig_bar.tight_layout(); self.canvas_bar.draw(); self.canvas_bar.repaint()
        self.fig_pie.clear()
        axp=self.fig_pie.add_subplot(111)
        axp.set_title("Distribución de ventas"+title_suf)
        if items_sorted:
            labels=[n for n,_ in items_sorted[:8]]
            values=[counts[n] for n in labels]
            axp.pie(values,labels=labels,autopct="%1.0f%%",startangle=90,wedgeprops={"width":0.45,"edgecolor":"white"})
            axp.axis("equal")
        else:
            axp.text(0.5,0.5,"Sin datos",ha="center",va="center",transform=axb.transAxes)
        self.fig_pie.tight_layout(); self.canvas_pie.draw(); self.canvas_pie.repaint()

    def export_csv(self):
        path,_=QFileDialog.getSaveFileName(self,"Exportar CSV","reporte_ventas.csv","CSV (*.csv)")
        if not path: return
        out=[]
        for r in range(self.table.rowCount()):
            out.append([
                self.table.item(r,0).text() if self.table.item(r,0) else "",
                self.table.item(r,1).text() if self.table.item(r,1) else "",
                self.table.item(r,2).text() if self.table.item(r,2) else "",
                self.table.item(r,3).text() if self.table.item(r,3) else "",
            ])
        with open(path,"w",newline="",encoding="utf-8") as f:
            w=csv.writer(f); w.writerow(["Producto","Cantidad","Importe","Tickets distintos"]); w.writerows(out)
        QMessageBox.information(self,"Exportado",f"Archivo guardado en {path}")

class PaymentDialog(QDialog):
    def __init__(self,total:float,parent=None,preset:Optional[Dict[str,float|str]]=None):
        super().__init__(parent)
        self.setWindowTitle("Método de pago")
        self.setMinimumWidth(420)
        self.total=total
        self.method="Efectivo"
        self.cash=0.0
        self.card=0.0
        self.change=0.0
        self.remaining=total
        root=QVBoxLayout(self)
        form=QFormLayout()
        self.cmb_method=QComboBox(); self.cmb_method.addItems(["Efectivo","Tarjeta","Combinado"])
        form.addRow("Método:",self.cmb_method)
        self.spn_cash=QDoubleSpinBox(); self.spn_cash.setDecimals(2); self.spn_cash.setMaximum(10_000_000); self.spn_cash.setPrefix("$ "); self.spn_cash.setSingleStep(10.0)
        self.spn_card=QDoubleSpinBox(); self.spn_card.setDecimals(2); self.spn_card.setMaximum(10_000_000); self.spn_card.setPrefix("$ "); self.spn_card.setSingleStep(10.0)
        form.addRow("Efectivo:",self.spn_cash)
        form.addRow("Tarjeta:",self.spn_card)
        self.lbl_total=QLabel(f"$ {total:,.2f}")
        self.lbl_change=QLabel("$ 0.00")
        self.lbl_remaining=QLabel(f"$ {total:,.2f}")
        form.addRow("Total:",self.lbl_total)
        form.addRow("Cambio:",self.lbl_change)
        form.addRow("Restante:",self.lbl_remaining)
        root.addLayout(form)
        btns=QHBoxLayout()
        self.btn_ok=QPushButton("Aceptar")
        self.btn_cancel=QPushButton("Cancelar")
        for b in (self.btn_ok,self.btn_cancel): _make_big(b)
        btns.addStretch(); btns.addWidget(self.btn_ok); btns.addWidget(self.btn_cancel)
        root.addLayout(btns)
        self.cmb_method.currentIndexChanged.connect(self.on_method_change)
        self.spn_cash.valueChanged.connect(self.recalc)
        self.spn_card.valueChanged.connect(self.recalc)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        if preset:
            m=preset.get("MetodoPago")
            if isinstance(m,str) and m in ["Efectivo","Tarjeta","Combinado"]:
                self.cmb_method.setCurrentText(m)
            try: self.spn_cash.setValue(float(preset.get("EfectivoIngresado",0) or 0))
            except: pass
            try: self.spn_card.setValue(float(preset.get("TarjetaIngresado",0) or 0))
            except: pass
        self.on_method_change(); self.recalc()

    def on_method_change(self):
        m=self.cmb_method.currentText()
        if m=="Efectivo":
            self.spn_cash.setEnabled(True)
            self.spn_card.setEnabled(False); self.spn_card.setValue(0.0)
        elif m=="Tarjeta":
            self.spn_cash.setEnabled(False); self.spn_cash.setValue(0.0)
            self.spn_card.setEnabled(True)
        else:
            self.spn_cash.setEnabled(True); self.spn_card.setEnabled(True)
        self.recalc()

    def recalc(self):
        m=self.cmb_method.currentText()
        cash=float(self.spn_cash.value())
        card=float(self.spn_card.value())
        total=self.total
        change=0.0
        remaining=0.0
        if m=="Efectivo":
            change=cash-total if cash>total else 0.0
            remaining=total-cash if cash<total else 0.0
        elif m=="Tarjeta":
            change=0.0
            remaining=total-card if card<total else 0.0
        else:
            paid=cash+card
            need_from_cash=max(total-card,0.0)
            change=cash-need_from_cash if cash>need_from_cash else 0.0
            remaining=total-paid if paid<total else 0.0
        self.method=m
        self.cash=cash
        self.card=card
        self.change=round(max(change,0.0),2)
        self.remaining=round(max(remaining,0.0),2)
        self.lbl_change.setText(f"$ {self.change:,.2f}")
        self.lbl_remaining.setText(f"$ {self.remaining:,.2f}")

    def get_values(self)->Dict[str,str]:
        return {
            "MetodoPago":self.method,
            "EfectivoIngresado":f"{self.cash:.2f}",
            "TarjetaIngresado":f"{self.card:.2f}",
            "Cambio":f"{self.change:.2f}",
            "Restante":f"{self.remaining:.2f}",
        }

class AjusteDialog(QDialog):
    def __init__(self,diferencia:float,parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajuste por diferencia")
        self.setMinimumWidth(440)
        self.diferencia=diferencia
        root=QVBoxLayout(self)
        form=QFormLayout()
        self.lbl_info=QLabel("Diferencia: $ {:.2f}".format(diferencia))
        form.addRow("Monto:",self.lbl_info)
        self.cmb_accion=QComboBox()
        if diferencia>0:
            self.cmb_accion.addItems(["Cobrar en efectivo","Cobrar con tarjeta","Cobrar combinado"])
        else:
            self.cmb_accion.addItems(["Devolver en efectivo","Devolver en tarjeta"])
        form.addRow("Acción:",self.cmb_accion)
        self.spn_cash=QDoubleSpinBox(); self.spn_cash.setDecimals(2); self.spn_cash.setMaximum(10_000_000); self.spn_cash.setPrefix("$ "); self.spn_cash.setValue(abs(diferencia) if diferencia<0 else 0.0)
        self.spn_card=QDoubleSpinBox(); self.spn_card.setDecimals(2); self.spn_card.setMaximum(10_000_000); self.spn_card.setPrefix("$ ")
        form.addRow("Efectivo:",self.spn_cash)
        form.addRow("Tarjeta:",self.spn_card)
        root.addLayout(form)
        btns=QHBoxLayout()
        okb=QPushButton("Aceptar"); cb=QPushButton("Cancelar")
        for b in (okb,cb): _make_big(b)
        btns.addStretch(); btns.addWidget(okb); btns.addWidget(cb)
        root.addLayout(btns)
        self.cmb_accion.currentIndexChanged.connect(self._mode)
        okb.clicked.connect(self.accept); cb.clicked.connect(self.reject)
        self._mode()

    def _mode(self):
        a=self.cmb_accion.currentText()
        if a=="Devolver en efectivo":
            self.spn_card.setEnabled(False); self.spn_card.setValue(0.0)
            self.spn_cash.setEnabled(True); self.spn_cash.setValue(abs(self.diferencia))
        elif a=="Devolver en tarjeta":
            self.spn_cash.setEnabled(False); self.spn_cash.setValue(0.0)
            self.spn_card.setEnabled(True); self.spn_card.setValue(abs(self.diferencia))
        elif a=="Cobrar en efectivo":
            self.spn_cash.setEnabled(True); self.spn_card.setEnabled(False); self.spn_card.setValue(0.0)
            self.spn_cash.setValue(self.diferencia if self.diferencia>0 else 0.0)
        elif a=="Cobrar con tarjeta":
            self.spn_cash.setEnabled(False); self.spn_cash.setValue(0.0); self.spn_card.setEnabled(True); self.spn_card.setValue(self.diferencia)
        else:
            self.spn_cash.setEnabled(True); self.spn_card.setEnabled(True)

    def valores(self)->Dict[str,float|str]:
        return {"cash":float(self.spn_cash.value()),"card":float(self.spn_card.value()),"accion":self.cmb_accion.currentText()}

class CorteDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowTitle("Corte del día")
        self.setMinimumWidth(460)
        root=QVBoxLayout(self)
        row=QHBoxLayout()
        row.addWidget(QLabel("Fecha:"))
        self.date=QDateEdit(); self.date.setCalendarPopup(True); self.date.setDate(QDate.currentDate())
        row.addWidget(self.date); row.addStretch()
        root.addLayout(row)
        self.fondo_lbl=QLabel("$ 0.00")
        self.efectivo_lbl=QLabel("$ 0.00")
        self.tarjeta_lbl=QLabel("$ 0.00")
        self.dev_ef_lbl=QLabel("$ 0.00")
        self.dev_tj_lbl=QLabel("$ 0.00")
        self.saldo_lbl=QLabel("$ 0.00")
        form=QFormLayout()
        form.addRow("Fondo inicial:",self.fondo_lbl)
        form.addRow("Ventas en efectivo:",self.efectivo_lbl)
        form.addRow("Ventas con tarjeta:",self.tarjeta_lbl)
        form.addRow("Devolución en efectivo:",self.dev_ef_lbl)
        form.addRow("Devolución en tarjeta:",self.dev_tj_lbl)
        form.addRow("Saldo final del día (caja):",self.saldo_lbl)
        root.addLayout(form)
        btn=QPushButton("Cerrar"); _make_big(btn)
        root.addWidget(btn,alignment=Qt.AlignmentFlag.AlignRight)
        self.date.dateChanged.connect(self.recalc)
        btn.clicked.connect(self.accept)
        self.recalc()

    def recalc(self):
        d=self.date.date()
        d_str=f"{d.year():04d}-{d.month():02d}-{d.day():02d}"
        fondo=self._fondo_dia(d_str)
        efectivo=self._ventas_efectivo_dia(d_str)
        tarjeta=self._ventas_tarjeta_dia(d_str)
        dev_ef,dev_tj=self._devoluciones_dia(d_str)
        saldo=self._saldo_final_dia(d_str)
        self.fondo_lbl.setText(f"$ {fondo:,.2f}")
        self.efectivo_lbl.setText(f"$ {efectivo:,.2f}")
        self.tarjeta_lbl.setText(f"$ {tarjeta:,.2f}")
        self.dev_ef_lbl.setText(f"$ {dev_ef:,.2f}")
        self.dev_tj_lbl.setText(f"$ {dev_tj:,.2f}")
        self.saldo_lbl.setText(f"$ {saldo:,.2f}")

    def _fondo_dia(self,fecha:str)->float:
        ensure_caja()
        with open(CAJA_FILE,"r",newline="",encoding="utf-8") as f:
            rows=list(csv.reader(f))
        for r in rows[1:]:
            try:
                if r[1]=="FONDO_INICIAL" and r[0].split(" ")[0]==fecha:
                    return float(r[3])
            except: pass
        return 0.0

    def _ventas_efectivo_dia(self,fecha:str)->float:
        rows=read_orders()
        total=0.0
        for r in rows[1:]:
            try:
                if r[5].split(" ")[0]==fecha:
                    ef=float(r[9] or 0.0); cam=float(r[11] or 0.0)
                    total+=max(ef-cam,0.0)
            except: pass
        return round(total,2)

    def _ventas_tarjeta_dia(self,fecha:str)->float:
        rows=read_orders()
        total=0.0
        for r in rows[1:]:
            try:
                if r[5].split(" ")[0]==fecha:
                    tj=float(r[10] or 0.0)
                    total+=tj
            except: pass
        return round(total,2)

    def _devoluciones_dia(self,fecha:str)->Tuple[float,float]:
        ensure_caja()
        dev_ef=0.0; dev_tj=0.0
        with open(CAJA_FILE,"r",newline="",encoding="utf-8") as f:
            rows=list(csv.reader(f))
        for r in rows[1:]:
            try:
                if r[0].split(" ")[0]==fecha:
                    tipo=r[1]
                    eg=float(r[4] or 0.0)
                    if "DEVOLUCION" in tipo and "TARJETA" not in tipo:
                        dev_ef+=eg
                    if "DEVOLUCION_TARJETA" in tipo:
                        nota=r[5] or ""
                        if "TJ=" in nota:
                            try:
                                dev_tj+=float(nota.split("TJ=")[1].split()[0])
                            except:
                                pass
            except: pass
        return round(dev_ef,2),round(dev_tj,2)

    def _saldo_final_dia(self,fecha:str)->float:
        ensure_caja()
        ingreso=0.0; egreso=0.0
        with open(CAJA_FILE,"r",newline="",encoding="utf-8") as f:
            rows=list(csv.reader(f))
        for r in rows[1:]:
            try:
                if r[0].split(" ")[0]==fecha:
                    ingreso+=float(r[3] or 0.0)
                    egreso+=float(r[4] or 0.0)
            except: pass
        return round(ingreso-egreso,2)

class OrderCard(QFrame):
    def __init__(self,row:List[str],on_mark_delivered,on_view_ticket):
        super().__init__()
        self.setObjectName("OrderCard")
        self.setFrameShape(QFrame.Shape.Box)
        self.setStyleSheet("QFrame#OrderCard { background-color: #222; border: 2px solid #444; border-radius: 16px; } QLabel { color: #fff; } QPushButton { padding: 12px 16px; border-radius: 12px; background: #2e7d32; color: white; font-weight: 600; font-size: 14px;} QPushButton#Secondary { background: #616161; }")
        layout=QVBoxLayout(self); layout.setContentsMargins(16,16,16,16); layout.setSpacing(10)
        title_font=QFont(); title_font.setPointSize(18); title_font.setBold(True)
        body_font=QFont(); body_font.setPointSize(16)
        small_font=QFont(); small_font.setPointSize(14)
        top=QLabel(f"ID #{row[0]}  |  Mesa {row[2]}"); top.setFont(title_font)
        cliente=QLabel(f"Mesa: {row[2]}"); cliente.setFont(body_font)
        prods=QLabel(f"Productos:\n{row[3]}"); prods.setWordWrap(True); prods.setFont(body_font)
        prods.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        comentarios=QLabel(f"Comentarios: {(row[7] if len(row)>7 and row[7].strip() else '(sin comentarios)')}"); comentarios.setWordWrap(True); comentarios.setFont(body_font)
        pago_info=""
        if len(row)>=13:
            pago_info=f"Método: {row[8] or '-'} • Efectivo: ${row[9] or '0'} • Tarjeta: ${row[10] or '0'} • Cambio: ${row[11] or '0'} • Restante: ${row[12] or '0'}"
        footer=QLabel(f"Total: ${row[4]}   •   {row[6]}   •   {row[5]}"); footer.setFont(small_font)
        pago_lbl=QLabel(pago_info); pago_lbl.setFont(small_font)
        btns=QHBoxLayout()
        deliver_btn=QPushButton("Entregado"); _make_big(deliver_btn); deliver_btn.clicked.connect(lambda: on_mark_delivered(int(row[0])))
        ticket_btn=QPushButton("Ticket"); _make_big(ticket_btn); ticket_btn.setObjectName("Secondary"); ticket_btn.clicked.connect(lambda: on_view_ticket(row))
        copy_btn=QPushButton("Copiar"); _make_big(copy_btn); copy_btn.setObjectName("Secondary"); copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(row[3]))
        layout.addWidget(top); layout.addWidget(cliente); layout.addWidget(prods); layout.addWidget(comentarios)
        if pago_info: layout.addWidget(pago_lbl)
        layout.addWidget(footer)
        for b in (deliver_btn, ticket_btn, copy_btn): btns.addWidget(b)
        layout.addLayout(btns)

class KitchenWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cocina - Pedidos")
        self.resize(1100,750)
        central=QWidget(); self.setCentralWidget(central)
        root=QVBoxLayout(central); root.setContentsMargins(12,12,12,12); root.setSpacing(10)
        ctrl_row=QHBoxLayout(); root.addLayout(ctrl_row)
        ctrl_row.addWidget(QLabel("Fecha:"))
        self.date_picker=QDateEdit(); self.date_picker.setCalendarPopup(True); self.date_picker.setDate(QDate.currentDate())
        ctrl_row.addWidget(self.date_picker)
        ctrl_row.addWidget(QLabel("Estado:"))
        self.filter_combo=QComboBox(); self.filter_combo.addItems(["Pendiente","Todos","Entregado"])
        ctrl_row.addWidget(self.filter_combo)
        self.columns_combo=QComboBox(); self.columns_combo.addItems(["2 columnas","3 columnas"])
        ctrl_row.addWidget(self.columns_combo)
        self.refresh_btn=QPushButton("Refrescar"); _make_big(self.refresh_btn); ctrl_row.addWidget(self.refresh_btn); ctrl_row.addStretch()
        self.scroll=QScrollArea(); self.scroll.setWidgetResizable(True); root.addWidget(self.scroll)
        self.grid_host=QWidget(); self.scroll.setWidget(self.grid_host)
        self.grid=QGridLayout(self.grid_host); self.grid.setContentsMargins(4,4,4,4)
        self.grid.setHorizontalSpacing(12); self.grid.setVerticalSpacing(12)
        self.refresh_btn.clicked.connect(self.refresh)
        self.filter_combo.currentIndexChanged.connect(self.refresh)
        self.columns_combo.currentIndexChanged.connect(self.refresh)
        self.date_picker.dateChanged.connect(self.refresh)
        self.timer=QTimer(self); self.timer.setInterval(10_000)
        self.timer.timeout.connect(self.refresh); self.timer.start()
        self.refresh()

    def current_columns(self)->int:
        return 3 if self.columns_combo.currentIndex()==1 else 2

    def clear_grid(self):
        while self.grid.count():
            it=self.grid.takeAt(0)
            w=it.widget()
            if w:
                w.setParent(None); w.deleteLater()

    def refresh(self):
        rows=read_orders()
        data=rows[1:]
        data.sort(key=lambda r: parse_dt(r[5]))
        qd=self.date_picker.date()
        selected_day=date(qd.year(),qd.month(),qd.day())
        data=[r for r in data if parse_dt(r[5]).date()==selected_day]
        st=self.filter_combo.currentText()
        if st!="Todos":
            data=[r for r in data if r[6]==st]
        self.clear_grid()
        cols=self.current_columns()
        ri=ci=0
        for r in data:
            card=OrderCard(r,self.mark_delivered,self.open_ticket)
            card.setMinimumSize(360,260)
            self.grid.addWidget(card,ri,ci)
            ci+=1
            if ci>=cols:
                ci=0; ri+=1
        if not data:
            lbl=QLabel("Sin pedidos para mostrar en ese día.")
            f=QFont(); f.setPointSize(18); f.setBold(True)
            lbl.setFont(f); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid.addWidget(lbl,0,0,1,cols)

    def mark_delivered(self,order_id:int):
        rows=read_orders()
        for i,r in enumerate(rows):
            if i==0: continue
            try:
                if int(r[0])==order_id:
                    rows[i][6]="Entregado"; break
            except: pass
        write_orders(rows); self.refresh()
        QMessageBox.information(self,"OK",f"Pedido {order_id} marcado como Entregado.")

    def open_ticket(self,row:List[str]):
        win=TicketWindow(row)
        win.showMaximized()
        self._ticket_win=win

class FondoCajaDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fondo inicial de caja")
        self.setMinimumWidth(360)
        root=QVBoxLayout(self)
        form=QFormLayout()
        self.spn=QDoubleSpinBox(); self.spn.setDecimals(2); self.spn.setMaximum(10_000_000); self.spn.setPrefix("$ "); self.spn.setValue(0.0)
        form.addRow("Fondo en efectivo:",self.spn)
        root.addLayout(form)
        btns=QHBoxLayout()
        ok=QPushButton("Guardar"); ca=QPushButton("Cancelar")
        for b in (ok,ca): _make_big(b)
        btns.addStretch(); btns.addWidget(ok); btns.addWidget(ca)
        root.addLayout(btns)
        ok.clicked.connect(self.accept); ca.clicked.connect(self.reject)

    def valor(self)->float:
        return float(self.spn.value())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Comandas con Gestión de Pedidos - PyQt6")
        self.resize(1300,800)
        self.current_order:List[Tuple[str,float]]=[]
        self.current_order_id:Optional[int]=None
        self.current_payment:Dict[str,str]={}
        self.is_dark=True
        self._init_caja()
        kitchen_action=QAction("Abrir pantalla de cocina",self)
        kitchen_action.triggered.connect(self.open_kitchen)
        open_csv_action=QAction("Abrir CSV…",self)
        open_csv_action.triggered.connect(self.open_csv_folder)
        analytics_action=QAction("Analítica de ventas",self)
        analytics_action.triggered.connect(self.open_analytics)
        corte_action=QAction("Corte del día",self)
        corte_action.triggered.connect(self.abrir_corte)
        theme_action=QAction("Cambiar a modo claro",self)
        theme_action.triggered.connect(self.toggle_theme)
        menu=self.menuBar().addMenu("Ventanas"); menu.addAction(kitchen_action)
        tools=self.menuBar().addMenu("Herramientas"); tools.addAction(open_csv_action); tools.addAction(analytics_action); tools.addAction(corte_action)
        appearance=self.menuBar().addMenu("Apariencia"); appearance.addAction(theme_action)
        self.theme_action=theme_action
        central=QWidget(); self.setCentralWidget(central)
        root=QHBoxLayout(central)
        left=QVBoxLayout(); root.addLayout(left,1)
        left.addWidget(QLabel("Número de Mesa:")); self.table_number=QLineEdit(); left.addWidget(self.table_number)
        left.addWidget(QLabel("Comentarios (nota):"))
        self.comments_edit=QTextEdit(); self.comments_edit.setPlaceholderText("Ej.: sin cebolla, sin picante, partir a la mitad, etc.")
        self.comments_edit.setFixedHeight(80); left.addWidget(self.comments_edit)
        left.addWidget(QLabel("Selecciona los Productos:"))
        scroll=QScrollArea(); scroll.setWidgetResizable(True); left.addWidget(scroll)
        prod_container=QWidget(); scroll.setWidget(prod_container)
        prod_layout=QVBoxLayout(prod_container)
        for name,price in PRODUCTS.items():
            btn=QPushButton(f"{name} - ${price:.2f}")
            btn.clicked.connect(lambda _,n=name,p=price:self.add_product(n,p))
            btn.setMinimumHeight(44); _set_btn_font(btn,14)
            prod_layout.addWidget(btn)
        prod_layout.addStretch()
        right=QVBoxLayout(); root.addLayout(right,1)
        right.addWidget(QLabel("Productos en la Comanda:"))
        self.order_list=QListWidget(); self.order_list.setMinimumHeight(260); right.addWidget(self.order_list)
        del_btn=QPushButton("Eliminar Producto Seleccionado"); _make_big(del_btn); del_btn.clicked.connect(self.remove_selected_product); right.addWidget(del_btn)
        pay_btn=QPushButton("Cobrar / Método de pago"); _make_big(pay_btn); pay_btn.clicked.connect(self.set_payment_and_save); right.addWidget(pay_btn)
        save_btn=QPushButton("Actualizar Comanda"); _make_big(save_btn); save_btn.clicked.connect(self.update_order_after_change); right.addWidget(save_btn)
        clear_btn=QPushButton("Limpiar Lista"); _make_big(clear_btn); clear_btn.clicked.connect(self.clear_order); right.addWidget(clear_btn)
        bottom=QHBoxLayout(); right.addLayout(bottom)
        bottom.addWidget(QLabel("Cargar por ID:"))
        self.ticket_edit=QLineEdit(); bottom.addWidget(self.ticket_edit)
        load_btn=QPushButton("Cargar Pedido"); _make_big(load_btn); load_btn.clicked.connect(self.load_order); bottom.addWidget(load_btn)
        manage_box=QVBoxLayout(); root.addLayout(manage_box,1)
        header_row=QHBoxLayout(); manage_box.addLayout(header_row)
        header_row.addWidget(QLabel("Gestión de Pedidos por día:")); header_row.addStretch()
        header_row.addWidget(QLabel("Fecha:"))
        self.date_picker=QDateEdit(); self.date_picker.setCalendarPopup(True); self.date_picker.setDate(QDate.currentDate())
        header_row.addWidget(self.date_picker)
        splitter=QSplitter(Qt.Orientation.Horizontal)
        manage_box.addWidget(splitter,1)
        pending_panel=QWidget(); pending_layout=QVBoxLayout(pending_panel)
        lbl_pend=QLabel("Pendientes"); f1=QFont(); f1.setPointSize(12); f1.setBold(True); lbl_pend.setFont(f1)
        pending_layout.addWidget(lbl_pend)
        self.manage_list_pending=QListWidget(); pending_layout.addWidget(self.manage_list_pending,1)
        splitter.addWidget(pending_panel)
        delivered_panel=QWidget(); delivered_layout=QVBoxLayout(delivered_panel)
        lbl_ent=QLabel("Entregados"); f2=QFont(); f2.setPointSize(12); f2.setBold(True); lbl_ent.setFont(f2)
        delivered_layout.addWidget(lbl_ent)
        self.manage_list_delivered=QListWidget(); delivered_layout.addWidget(self.manage_list_delivered,1)
        splitter.addWidget(delivered_panel)
        actions_row=QHBoxLayout(); manage_box.addLayout(actions_row)
        mark_delivered=QPushButton("Marcar como Entregado"); _make_big(mark_delivered); mark_delivered.clicked.connect(lambda: self.change_order_status("Entregado"))
        actions_row.addWidget(mark_delivered)
        mark_pending=QPushButton("Marcar como Pendiente"); _make_big(mark_pending); mark_pending.clicked.connect(lambda: self.change_order_status("Pendiente"))
        actions_row.addWidget(mark_pending)
        actions_row.addStretch()
        self.manage_list_pending.itemDoubleClicked.connect(lambda *_: None)
        self.manage_list_delivered.itemDoubleClicked.connect(lambda *_: None)
        self.date_picker.dateChanged.connect(self.load_all_orders_for_day)
        self.load_all_orders_for_day()
        self.update_order_display()

    def toggle_theme(self):
        app=QApplication.instance()
        if self.is_dark:
            light_palette(app)
            self.is_dark=False
            self.theme_action.setText("Cambiar a modo oscuro")
            app.setStyleSheet("QPushButton{min-height:40px; font-size:14px;}")
        else:
            dark_palette(app)
            self.is_dark=True
            self.theme_action.setText("Cambiar a modo claro")
            app.setStyleSheet("QPushButton{min-height:40px; font-size:14px;}")

    def _init_caja(self):
        ensure_caja()
        hoy=datetime.now().strftime("%Y-%m-%d")
        ya_apertura=apertura_existente(hoy)
        cfg={}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE,"r",encoding="utf-8") as f:
                    cfg=json.load(f)
            except:
                cfg={}
        if cfg.get("fecha")==hoy and ya_apertura:
            return
        if not ya_apertura:
            dlg=FondoCajaDialog(self)
            if dlg.exec()==QDialog.DialogCode.Accepted:
                fondo=dlg.valor()
                caja_registrar("FONDO_INICIAL","-",fondo,0.0,"Fondo apertura")
                with open(CONFIG_FILE,"w",encoding="utf-8") as g:
                    json.dump({"fecha":hoy,"fondo":fondo},g)

    def abrir_corte(self):
        dlg=CorteDialog(self)
        dlg.exec()

    def open_kitchen(self):
        self.kitchen=KitchenWindow()
        self.kitchen.showMaximized()

    def open_csv_folder(self):
        path=os.path.abspath(CSV_FILE)
        folder=os.path.dirname(path)
        QFileDialog.getOpenFileName(self,"Abrir CSV",folder,"CSV (*.csv)")

    def open_analytics(self):
        dlg=AnalyticsWindow(self)
        dlg.exec()

    def add_product(self,name:str,price:float):
        self.current_order.append((name,price))
        self.update_order_display()

    def remove_selected_product(self):
        idx=self.order_list.currentRow()
        if 0<=idx<len(self.current_order):
            self.current_order.pop(idx); self.update_order_display()

    def update_order_display(self):
        self.order_list.clear()
        total=0.0
        for item,price in self.current_order:
            self.order_list.addItem(f"{item} - ${price:.2f}")
            total+=price
        self.order_list.addItem(f"TOTAL: ${total:.2f}")

    def set_payment_and_save(self):
        table=self.table_number.text().strip()
        comments=self.comments_edit.toPlainText().strip()
        if not table or not self.current_order:
            QMessageBox.critical(self,"Error","Completa el número de mesa y agrega al menos un producto.")
            return
        total=sum(p for _,p in self.current_order)
        items_str=", ".join([n for n,_ in self.current_order])
        ts=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        preset=self.current_payment if self.current_payment else None
        dlg=PaymentDialog(total,self,preset=preset)
        if dlg.exec()!=QDialog.DialogCode.Accepted:
            return
        self.current_payment=dlg.get_values()
        pay=self.current_payment
        if self.current_order_id is None:
            oid=next_order_id()
            rows=read_orders()
            new_row=[
                str(oid),"",table,items_str,f"{total:.2f}",ts,"Pendiente",comments,
                pay.get("MetodoPago",""),pay.get("EfectivoIngresado","0"),pay.get("TarjetaIngresado","0"),
                pay.get("Cambio","0"),pay.get("Restante","0")
            ]
            rows.append(new_row); write_orders(rows)
            ingreso_ef=max(float(pay["EfectivoIngresado"])-float(pay["Cambio"]),0.0)
            if ingreso_ef>0: caja_registrar("VENTA",str(oid),ingreso_ef,0.0,"Venta registrada")
            if float(pay["Cambio"])>0: caja_registrar("CAMBIO",str(oid),0.0,float(pay["Cambio"]),"Cambio entregado")
            QMessageBox.information(self,"Éxito",f"Comanda registrada y cobrada. ID: {oid}  Total: ${total:.2f}")
            self.clear_order(); self.load_all_orders_for_day()
        else:
            rows=read_orders()
            found_idx=None; old_row=None
            for i,r in enumerate(rows):
                if i==0: continue
                try:
                    if int(r[0])==self.current_order_id:
                        found_idx=i; old_row=r; break
                except: pass
            if found_idx is None:
                QMessageBox.critical(self,"Error","No se encontró el pedido para actualizar.")
                return
            old_total=float(old_row[4])
            nueva=[
                str(self.current_order_id),"",table,items_str,f"{total:.2f}",ts,old_row[6] if len(old_row)>6 and old_row[6] else "Pendiente",comments,
                pay.get("MetodoPago",""),pay.get("EfectivoIngresado","0"),pay.get("TarjetaIngresado","0"),
                pay.get("Cambio","0"),pay.get("Restante","0")
            ]
            rows[found_idx]=nueva; write_orders(rows)
            diff=round(total-old_total,2)
            if diff!=0:
                if diff>0:
                    adj=AjusteDialog(diff,self)
                    if adj.exec()==QDialog.DialogCode.Accepted:
                        v=adj.valores()
                        if "efectivo" in v["accion"].lower() and v["cash"]>0:
                            caja_registrar("AJUSTE_COBRO",str(self.current_order_id),v["cash"],0.0,"Cobro extra por actualización")
                else:
                    devolver=abs(diff)
                    adj=AjusteDialog(-devolver,self)
                    if adj.exec()==QDialog.DialogCode.Accepted:
                        v=adj.valores()
                        if v["accion"]=="Devolver en efectivo" and v["cash"]>0:
                            caja_registrar("AJUSTE_DEVOLUCION",str(self.current_order_id),0.0,v["cash"],"Devolución en efectivo")
                        elif v["accion"]=="Devolver en tarjeta" and v["card"]>0:
                            caja_registrar("AJUSTE_DEVOLUCION_TARJETA",str(self.current_order_id),0.0,0.0,f"TJ={v['card']:.2f}")
            ingreso_ef=max(float(pay["EfectivoIngresado"])-float(pay["Cambio"]),0.0)
            if ingreso_ef>0: caja_registrar("VENTA_ACT",str(self.current_order_id),ingreso_ef,0.0,"Actualización de cobro")
            if float(pay["Cambio"])>0: caja_registrar("CAMBIO_ACT",str(self.current_order_id),0.0,float(pay["Cambio"]),"Cambio entregado (actualización)")
            QMessageBox.information(self,"Actualizado",f"Pedido {self.current_order_id} actualizado y cobrado. Total: ${total:.2f}")
            self.clear_order(); self.load_all_orders_for_day()

    def update_order_after_change(self):
        if self.current_order_id is None:
            QMessageBox.information(self,"Aviso","No hay pedido cargado para actualizar. Usa Cobrar para registrar uno nuevo.")
            return
        table=self.table_number.text().strip()
        comments=self.comments_edit.toPlainText().strip()
        if not table or not self.current_order:
            QMessageBox.critical(self,"Error","Completa el número de mesa y agrega al menos un producto.")
            return
        rows=read_orders()
        found_idx=None; old_row=None
        for i,r in enumerate(rows):
            if i==0: continue
            try:
                if int(r[0])==self.current_order_id:
                    found_idx=i; old_row=r; break
            except: pass
        if found_idx is None:
            QMessageBox.critical(self,"Error","No se encontró el pedido para actualizar.")
            return
        old_total=float(old_row[4])
        new_total=sum(p for _,p in self.current_order)
        items_str=", ".join([n for n,_ in self.current_order])
        ts=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rows[found_idx]=[
            str(self.current_order_id),"",table,items_str,f"{new_total:.2f}",ts,old_row[6] if len(old_row)>6 and old_row[6] else "Pendiente",comments,
            old_row[8] if len(old_row)>8 else "", old_row[9] if len(old_row)>9 else "0", old_row[10] if len(old_row)>10 else "0",
            old_row[11] if len(old_row)>11 else "0", old_row[12] if len(old_row)>12 else "0"
        ]
        write_orders(rows)
        diff=round(new_total-old_total,2)
        if diff!=0:
            if diff>0:
                adj=AjusteDialog(diff,self)
                if adj.exec()==QDialog.DialogCode.Accepted:
                    v=adj.valores()
                    if "efectivo" in v["accion"].lower() and v["cash"]>0:
                        caja_registrar("AJUSTE_COBRO",str(self.current_order_id),v["cash"],0.0,"Cobro extra por actualización")
            else:
                devolver=abs(diff)
                adj=AjusteDialog(-devolver,self)
                if adj.exec()==QDialog.DialogCode.Accepted:
                    v=adj.valores()
                    if v["accion"]=="Devolver en efectivo" and v["cash"]>0:
                        caja_registrar("AJUSTE_DEVOLUCION",str(self.current_order_id),0.0,v["cash"],"Devolución en efectivo")
                    elif v["accion"]=="Devolver en tarjeta" and v["card"]>0:
                        caja_registrar("AJUSTE_DEVOLUCION_TARJETA",str(self.current_order_id),0.0,0.0,f"TJ={v['card']:.2f}")
        QMessageBox.information(self,"Actualizado",f"Pedido {self.current_order_id} actualizado. Diferencia: ${diff:.2f}")
        self.clear_order(); self.load_all_orders_for_day()

    def load_order(self):
        text=self.ticket_edit.text().strip()
        if not text.isdigit():
            QMessageBox.critical(self,"Error","Ingresa un ID numérico válido."); return
        oid=int(text)
        rows=read_orders()
        found=None
        for r in rows[1:]:
            try:
                if int(r[0])==oid:
                    found=r; break
            except: pass
        if not found:
            QMessageBox.critical(self,"Error",f"No existe el pedido con ID {oid}."); return
        self.current_order_id=oid
        self.table_number.setText(found[2])
        self.comments_edit.setPlainText(found[7] if len(found)>7 else "")
        self.current_order.clear()
        for it in parse_products(found[3]):
            self.current_order.append((it,PRODUCTS.get(it,0.0)))
        self.current_payment={
            "MetodoPago":found[8] if len(found)>8 else "",
            "EfectivoIngresado":found[9] if len(found)>9 else "0",
            "TarjetaIngresado":found[10] if len(found)>10 else "0",
            "Cambio":found[11] if len(found)>11 else "0",
            "Restante":found[12] if len(found)>12 else "0",
        }
        self.update_order_display()

    def change_order_status(self,new_status:str):
        oid=self._selected_order_id_from_lists()
        if oid is None:
            QMessageBox.warning(self,"Aviso","Selecciona un pedido en alguna de las listas."); return
        rows=read_orders()
        for i,r in enumerate(rows):
            if i==0: continue
            try:
                if int(r[0])==oid:
                    rows[i][6]=new_status; break
            except: pass
        write_orders(rows); self.load_all_orders_for_day()
        QMessageBox.information(self,"OK",f"Pedido {oid} marcado como {new_status}.")

    def _selected_order_id_from_lists(self)->Optional[int]:
        def parse_from(text:str)->Optional[int]:
            try: return int(text.split("|")[0].split(":")[1].strip())
            except: return None
        it=self.manage_list_pending.currentItem()
        if it:
            oid=parse_from(it.text())
            if oid is not None: return oid
        it=self.manage_list_delivered.currentItem()
        if it:
            oid=parse_from(it.text())
            if oid is not None: return oid
        return None

    def load_all_orders_for_day(self):
        self.manage_list_pending.clear(); self.manage_list_delivered.clear()
        rows=read_orders(); data=rows[1:]
        qd=self.date_picker.date()
        selected_day=date(qd.year(),qd.month(),qd.day())
        filtered=[r for r in data if parse_dt(r[5]).date()==selected_day]
        filtered.sort(key=lambda r: parse_dt(r[5]))
        for r in filtered:
            has_note=" • Nota" if (len(r)>7 and r[7].strip()) else ""
            line=f"ID: {r[0]} | Mesa: {r[2]} | Total: ${r[4]} | Estado: {r[6]} | {r[5]}{has_note}"
            if r[6]=="Entregado": self.manage_list_delivered.addItem(line)
            else: self.manage_list_pending.addItem(line)

    def clear_order(self):
        self.current_order_id=None
        self.table_number.clear(); self.comments_edit.clear()
        self.current_order.clear(); self.current_payment={}
        self.update_order_display()

def _make_big(btn:QPushButton):
    btn.setMinimumHeight(44)
    _set_btn_font(btn,14)

def _set_btn_font(widget, size:int):
    f=widget.font()
    f.setPointSize(size)
    widget.setFont(f)

def main():
    import sys
    ensure_csv(); ensure_caja()
    app=QApplication(sys.argv)
    dark_palette(app)
    app.setStyleSheet("QPushButton{min-height:40px; font-size:14px;}")
    w=MainWindow(); w.show()
    sys.exit(app.exec())

if __name__=="__main__":
    main()
