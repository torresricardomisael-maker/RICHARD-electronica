"""
RICHARD Electronica - App de Ordenes de Trabajo (OT) a domicilio.
Genera PDF con firma del cliente y registro de retiro de equipo.
"""
import os
import sqlite3
from datetime import datetime

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line
from kivy.properties import StringProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

APP_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(APP_DIR, "logo.png")
EMPRESA_NOMBRE = "RICHARD ELECTRONICA"
EMPRESA_RUBRO = "Servicio Tecnico: TV - Audio - Microondas"
EMPRESA_DIRECCION = "Laprida 602 esquina Caseros - Capital"
EMPRESA_TELEFONO = "Celular: 264 564 1950"
DATA_DIR = os.path.join(APP_DIR, "richard_data")
PDF_DIR = os.path.join(DATA_DIR, "pdf")
FIRMA_DIR = os.path.join(DATA_DIR, "firmas")
FOTO_DIR = os.path.join(DATA_DIR, "fotos")
DB_PATH = os.path.join(DATA_DIR, "ordenes.db")

for d in (DATA_DIR, PDF_DIR, FIRMA_DIR, FOTO_DIR):
    os.makedirs(d, exist_ok=True)

CLAUSULA_TEXTO = (
    "El cliente declara recibir conforme el equipo detallado en esta orden de "
    "trabajo, aceptando el diagnostico y/o reparacion realizada por RICHARD "
    "ELECTRONICA. La garantia cubre unicamente la falla reparada, por el plazo "
    "indicado, y no cubre danos por mal uso, humedad, golpes o manipulacion de "
    "terceros. Equipos no retirados dentro de 30 dias no generan responsabilidad "
    "de custodia para el taller. Con su firma, el cliente confirma la entrega y "
    "recepcion del equipo en las condiciones aqui descritas."
)

CLAUSULA_RETIRO_TEXTO = (
    "El cliente autoriza a RICHARD ELECTRONICA a retirar de su domicilio el "
    "equipo detallado en este remito para su evaluacion en el taller." 
    "Este remito no implica diagnostico, reparacion ni garantia, "
    "unicamente constancia del retiro del equipo y su estado fisico declarado. "
    "Con su firma, el cliente confirma la entrega del equipo para su traslado."
    "RICHARD electronica no se responsabiliza por roturas en el equipo en el traslado"
    "hacia el taller, como roturas, trizaduras, o cualquier daño ocasionado accidentalmente"
    "El cliente entiende y acepta estas condiciones."
)


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ordenes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_ot TEXT,
            fecha TEXT,
            cliente_nombre TEXT,
            cliente_direccion TEXT,
            cliente_telefono TEXT,
            cliente_email TEXT,
            equipo_tipo TEXT,
            equipo_marca_modelo TEXT,
            equipo_serie TEXT,
            accesorios TEXT,
            estado_fisico TEXT,
            falla_reportada TEXT,
            diagnostico TEXT,
            trabajo_realizado TEXT,
            repuestos TEXT,
            costo_total TEXT,
            tecnico TEXT,
            garantia_dias TEXT,
            observaciones TEXT,
            foto_path TEXT,
            firma_path TEXT,
            pdf_path TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS retiros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_retiro TEXT,
            fecha TEXT,
            cliente_nombre TEXT,
            cliente_direccion TEXT,
            cliente_telefono TEXT,
            cliente_email TEXT,
            equipo_tipo TEXT,
            equipo_marca_modelo TEXT,
            equipo_serie TEXT,
            accesorios TEXT,
            estado_fisico TEXT,
            motivo_retiro TEXT,
            observaciones TEXT,
            tecnico TEXT,
            firma_path TEXT,
            pdf_path TEXT
        )
        """
    )
    conn.commit()
    return conn


def siguiente_numero_ot():
    conn = get_connection()
    cur = conn.execute("SELECT COUNT(*) FROM ordenes")
    total = cur.fetchone()[0]
    conn.close()
    return f"OT-{total + 1:04d}"


def siguiente_numero_retiro():
    conn = get_connection()
    cur = conn.execute("SELECT COUNT(*) FROM retiros")
    total = cur.fetchone()[0]
    conn.close()
    return f"RE-{total + 1:04d}"


KV = """
ScreenManager:
    MenuScreen:
    FormScreen:
    SignatureScreen:
    RetiroFormScreen:
    RetiroSignatureScreen:

<MenuScreen>:
    name: "menu"
    BoxLayout:
        orientation: "vertical"
        padding: dp(24)
        spacing: dp(16)

        BoxLayout:
            size_hint_y: None
            height: dp(70)
            spacing: dp(10)
            Image:
                source: app.logo_path
                size_hint_x: None
                width: dp(70)
                allow_stretch: True
            BoxLayout:
                orientation: "vertical"
                Label:
                    text: "RICHARD ELECTRONICA"
                    bold: True
                    font_size: "18sp"
                    halign: "left"
                    valign: "middle"
                    text_size: self.width, None
                Label:
                    text: "Servicio Tecnico: TV - Audio - Microondas"
                    font_size: "12sp"
                    halign: "left"
                    valign: "middle"
                    text_size: self.width, None
                Label:
                    text: "Laprida 602 esquina Caseros - Capital  |  Cel: 264 564 1950"
                    font_size: "12sp"
                    halign: "left"
                    valign: "middle"
                    text_size: self.width, None

        Widget:

        Button:
            text: "Retiro de equipo a domicilio"
            font_size: "16sp"
            size_hint_y: None
            height: dp(64)
            on_release: root.manager.current = "retiro_form"

        Button:
            text: "Entrega de equipo (Orden de Trabajo)"
            font_size: "16sp"
            size_hint_y: None
            height: dp(64)
            on_release: root.manager.current = "form"

        Widget:

<FormScreen>:
    name: "form"
    BoxLayout:
        orientation: "vertical"
        ScrollView:
            bar_width: dp(10)
            bar_color: 0.3, 0.3, 0.3, 0.9
            bar_inactive_color: 0.6, 0.6, 0.6, 0.5
            scroll_type: ["bars", "content"]
            GridLayout:
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                padding: dp(12)
                spacing: dp(6)

                BoxLayout:
                    size_hint_y: None
                    height: dp(70)
                    spacing: dp(10)
                    Image:
                        source: app.logo_path
                        size_hint_x: None
                        width: dp(70)
                        allow_stretch: True
                    BoxLayout:
                        orientation: "vertical"
                        Label:
                            text: "RICHARD ELECTRONICA"
                            bold: True
                            font_size: "18sp"
                            halign: "left"
                            valign: "middle"
                            text_size: self.width, None
                        Label:
                            text: "Servicio Tecnico: TV - Audio - Microondas"
                            font_size: "12sp"
                            halign: "left"
                            valign: "middle"
                            text_size: self.width, None
                        Label:
                            text: "Laprida 602 esquina Caseros - Capital  |  Cel: 264 564 1950"
                            font_size: "12sp"
                            halign: "left"
                            valign: "middle"
                            text_size: self.width, None

                Label:
                    text: "Datos del cliente"
                    bold: True
                    size_hint_y: None
                    height: dp(28)
                TextInput:
                    id: cliente_nombre
                    hint_text: "Nombre completo"
                    size_hint_y: None
                    height: dp(44)
                    multiline: False
                TextInput:
                    id: cliente_direccion
                    hint_text: "Direccion (domicilio)"
                    size_hint_y: None
                    height: dp(44)
                    multiline: False
                TextInput:
                    id: cliente_telefono
                    hint_text: "Telefono / WhatsApp"
                    size_hint_y: None
                    height: dp(44)
                    multiline: False
                TextInput:
                    id: cliente_email
                    hint_text: "Email (opcional)"
                    size_hint_y: None
                    height: dp(44)
                    multiline: False

                Label:
                    text: "Datos del equipo"
                    bold: True
                    size_hint_y: None
                    height: dp(28)
                TextInput:
                    id: equipo_tipo
                    hint_text: "Tipo de equipo (TV, radio, amplificador...)"
                    size_hint_y: None
                    height: dp(44)
                    multiline: False
                TextInput:
                    id: equipo_marca_modelo
                    hint_text: "Marca / Modelo"
                    size_hint_y: None
                    height: dp(44)
                    multiline: False
                TextInput:
                    id: equipo_serie
                    hint_text: "Numero de serie (opcional)"
                    size_hint_y: None
                    height: dp(44)
                    multiline: False
                TextInput:
                    id: accesorios
                    hint_text: "Accesorios entregados"
                    size_hint_y: None
                    height: dp(44)
                    multiline: False
                TextInput:
                    id: estado_fisico
                    hint_text: "Estado fisico al recibir"
                    size_hint_y: None
                    height: dp(60)

                Label:
                    text: "Foto del equipo (opcional)"
                    bold: True
                    size_hint_y: None
                    height: dp(28)
                BoxLayout:
                    size_hint_y: None
                    height: dp(44)
                    spacing: dp(6)
                    Button:
                        text: "Tomar foto"
                        on_release: root.tomar_foto()
                    Label:
                        id: foto_estado
                        text: "Sin foto"

                Label:
                    text: "Servicio"
                    bold: True
                    size_hint_y: None
                    height: dp(28)
                TextInput:
                    id: falla_reportada
                    hint_text: "Falla reportada por el cliente"
                    size_hint_y: None
                    height: dp(60)
                TextInput:
                    id: diagnostico
                    hint_text: "Diagnostico tecnico"
                    size_hint_y: None
                    height: dp(60)
                TextInput:
                    id: trabajo_realizado
                    hint_text: "Trabajo realizado"
                    size_hint_y: None
                    height: dp(60)
                TextInput:
                    id: repuestos
                    hint_text: "Repuestos usados"
                    size_hint_y: None
                    height: dp(44)
                    multiline: False
                TextInput:
                    id: costo_total
                    hint_text: "Costo total"
                    size_hint_y: None
                    height: dp(44)
                    multiline: False
                TextInput:
                    id: tecnico
                    hint_text: "Tecnico responsable"
                    size_hint_y: None
                    height: dp(44)
                    multiline: False
                TextInput:
                    id: garantia_dias
                    hint_text: "Garantia (dias)"
                    size_hint_y: None
                    height: dp(44)
                    multiline: False
                TextInput:
                    id: observaciones
                    hint_text: "Observaciones finales"
                    size_hint_y: None
                    height: dp(60)

        BoxLayout:
            size_hint_y: None
            height: dp(52)
            spacing: dp(8)
            Button:
                text: "Volver al menu"
                on_release: root.manager.current = "menu"
            Button:
                text: "Continuar a firma y entrega"
                on_release: root.ir_a_firma()

<SignatureScreen>:
    name: "signature"
    BoxLayout:
        orientation: "vertical"
        padding: dp(12)
        spacing: dp(8)

        Label:
            text: "Confirmacion de entrega al cliente"
            bold: True
            font_size: "18sp"
            size_hint_y: None
            height: dp(32)

        ScrollView:
            size_hint_y: 0.3
            Label:
                text: root.clausula
                size_hint_y: None
                height: self.texture_size[1]
                text_size: self.width, None
                padding: dp(6), dp(6)

        Label:
            text: "Firme dentro del recuadro para confirmar la entrega:"
            size_hint_y: None
            height: dp(24)

        SignaturePad:
            id: signature_pad
            size_hint_y: 0.4
            canvas.before:
                Color:
                    rgba: 1, 1, 1, 1
                Rectangle:
                    pos: self.pos
                    size: self.size

        BoxLayout:
            size_hint_y: None
            height: dp(52)
            spacing: dp(8)
            Button:
                text: "Limpiar firma"
                on_release: signature_pad.limpiar()
            Button:
                text: "Volver"
                on_release: root.manager.current = "form"
            Button:
                text: "Confirmar y generar PDF"
                on_release: root.confirmar(signature_pad)

<RetiroFormScreen>:
    name: "retiro_form"
    BoxLayout:
        orientation: "vertical"
        ScrollView:
            bar_width: dp(10)
            bar_color: 0.3, 0.3, 0.3, 0.9
            bar_inactive_color: 0.6, 0.6, 0.6, 0.5
            scroll_type: ["bars", "content"]
            GridLayout:
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                padding: dp(12)
                spacing: dp(6)

                BoxLayout:
                    size_hint_y: None
                    height: dp(70)
                    spacing: dp(10)
                    Image:
                        source: app.logo_path
                        size_hint_x: None
                        width: dp(70)
                        allow_stretch: True
                    BoxLayout:
                        orientation: "vertical"
                        Label:
                            text: "RICHARD ELECTRONICA"
                            bold: True
                            font_size: "18sp"
                            halign: "left"
                            valign: "middle"
                            text_size: self.width, None
                        Label:
                            text: "Remito de retiro de equipo a domicilio"
                            font_size: "12sp"
                            halign: "left"
                            valign: "middle"
                            text_size: self.width, None
                        Label:
                            text: "Laprida 602 esquina Caseros - Capital  |  Cel: 264 564 1950"
                            font_size: "12sp"
                            halign: "left"
                            valign: "middle"
                            text_size: self.width, None

                Label:
                    text: "Datos del cliente"
                    bold: True
                    size_hint_y: None
                    height: dp(28)
                TextInput:
                    id: r_cliente_nombre
                    hint_text: "Nombre completo"
                    size_hint_y: None
                    height: dp(44)
                    multiline: False
                TextInput:
                    id: r_cliente_direccion
                    hint_text: "Direccion (domicilio)"
                    size_hint_y: None
                    height: dp(44)
                    multiline: False
                TextInput:
                    id: r_cliente_telefono
                    hint_text: "Telefono / WhatsApp"
                    size_hint_y: None
                    height: dp(44)
                    multiline: False
                TextInput:
                    id: r_cliente_email
                    hint_text: "Email (opcional)"
                    size_hint_y: None
                    height: dp(44)
                    multiline: False

                Label:
                    text: "Datos del equipo"
                    bold: True
                    size_hint_y: None
                    height: dp(28)
                TextInput:
                    id: r_equipo_tipo
                    hint_text: "Tipo de equipo (TV, radio, amplificador...)"
                    size_hint_y: None
                    height: dp(44)
                    multiline: False
                TextInput:
                    id: r_equipo_marca_modelo
                    hint_text: "Marca / Modelo"
                    size_hint_y: None
                    height: dp(44)
                    multiline: False
                TextInput:
                    id: r_equipo_serie
                    hint_text: "Numero de serie (opcional)"
                    size_hint_y: None
                    height: dp(44)
                    multiline: False
                TextInput:
                    id: r_accesorios
                    hint_text: "Accesorios que se llevan"
                    size_hint_y: None
                    height: dp(44)
                    multiline: False
                TextInput:
                    id: r_estado_fisico
                    hint_text: "Estado fisico al retirar"
                    size_hint_y: None
                    height: dp(60)

                Label:
                    text: "Motivo del retiro"
                    bold: True
                    size_hint_y: None
                    height: dp(28)
                TextInput:
                    id: r_motivo_retiro
                    hint_text: "Falla informada por el cliente"
                    size_hint_y: None
                    height: dp(60)
                TextInput:
                    id: r_tecnico
                    hint_text: "Tecnico que retira"
                    size_hint_y: None
                    height: dp(44)
                    multiline: False
                TextInput:
                    id: r_observaciones
                    hint_text: "Observaciones"
                    size_hint_y: None
                    height: dp(60)

        BoxLayout:
            size_hint_y: None
            height: dp(52)
            spacing: dp(8)
            Button:
                text: "Volver al menu"
                on_release: root.manager.current = "menu"
            Button:
                text: "Continuar a firma de retiro"
                on_release: root.ir_a_firma()

<RetiroSignatureScreen>:
    name: "retiro_signature"
    BoxLayout:
        orientation: "vertical"
        padding: dp(12)
        spacing: dp(8)

        Label:
            text: "Confirmacion de retiro para evaluacion"
            bold: True
            font_size: "18sp"
            size_hint_y: None
            height: dp(32)

        ScrollView:
            size_hint_y: 0.3
            Label:
                text: root.clausula
                size_hint_y: None
                height: self.texture_size[1]
                text_size: self.width, None
                padding: dp(6), dp(6)

        Label:
            text: "Firme dentro del recuadro para confirmar el retiro:"
            size_hint_y: None
            height: dp(24)

        SignaturePad:
            id: retiro_signature_pad
            size_hint_y: 0.4
            canvas.before:
                Color:
                    rgba: 1, 1, 1, 1
                Rectangle:
                    pos: self.pos
                    size: self.size

        BoxLayout:
            size_hint_y: None
            height: dp(52)
            spacing: dp(8)
            Button:
                text: "Limpiar firma"
                on_release: retiro_signature_pad.limpiar()
            Button:
                text: "Volver"
                on_release: root.manager.current = "retiro_form"
            Button:
                text: "Confirmar y generar PDF"
                on_release: root.confirmar(retiro_signature_pad)
"""


class MenuScreen(Screen):
    pass


class SignaturePad(Widget):
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            with self.canvas:
                Color(0, 0, 0, 1)
                touch.ud["line"] = Line(points=(touch.x, touch.y), width=2)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if "line" in touch.ud and self.collide_point(*touch.pos):
            touch.ud["line"].points += (touch.x, touch.y)
            return True
        return super().on_touch_move(touch)

    def limpiar(self):
        self.canvas.clear()

    def tiene_firma(self):
        return len(self.canvas.children) > 2

    def exportar_png(self, path):
        self.export_to_png(path)


class FormScreen(Screen):
    foto_path = StringProperty("")

    def tomar_foto(self):
        try:
            from plyer import camera
            destino = os.path.join(FOTO_DIR, f"foto_{datetime.now():%Y%m%d_%H%M%S}.jpg")
            camera.take_picture(filename=destino, on_complete=self._foto_lista(destino))
        except Exception as exc:
            self._mostrar_mensaje(f"No se pudo abrir la camara: {exc}")

    def _foto_lista(self, destino):
        def callback(*args):
            if os.path.exists(destino):
                self.foto_path = destino
                self.ids.foto_estado.text = "Foto adjuntada"
        return callback

    def _mostrar_mensaje(self, texto):
        Popup(title="Aviso", content=Label(text=texto), size_hint=(0.8, 0.4)).open()

    def datos_formulario(self):
        campos = [
            "cliente_nombre", "cliente_direccion", "cliente_telefono", "cliente_email",
            "equipo_tipo", "equipo_marca_modelo", "equipo_serie", "accesorios",
            "estado_fisico", "falla_reportada", "diagnostico", "trabajo_realizado",
            "repuestos", "costo_total", "tecnico", "garantia_dias", "observaciones",
        ]
        return {c: self.ids[c].text.strip() for c in campos}

    def ir_a_firma(self):
        datos = self.datos_formulario()
        if not datos["cliente_nombre"] or not datos["equipo_tipo"]:
            self._mostrar_mensaje("Completa al menos el nombre del cliente y el tipo de equipo.")
            return
        self.manager.current = "signature"


class SignatureScreen(Screen):
    clausula = StringProperty(CLAUSULA_TEXTO)

    def confirmar(self, pad):
        if not pad.tiene_firma():
            self._mostrar_mensaje("El cliente debe firmar antes de continuar.")
            return

        form_screen = self.manager.get_screen("form")
        datos = form_screen.datos_formulario()
        numero_ot = siguiente_numero_ot()
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")

        firma_path = os.path.join(FIRMA_DIR, f"{numero_ot}_firma.png")
        pad.exportar_png(firma_path)

        pdf_path = os.path.join(PDF_DIR, f"{numero_ot}.pdf")
        generar_pdf(numero_ot, fecha, datos, form_screen.foto_path, firma_path, pdf_path)
        guardar_en_bd(numero_ot, fecha, datos, form_screen.foto_path, firma_path, pdf_path)

        pad.limpiar()
        self.manager.current = "form"
        mostrar_popup_pdf(pdf_path, f"Orden {numero_ot} generada correctamente.")

    def _mostrar_mensaje(self, texto):
        Popup(title="Aviso", content=Label(text=texto), size_hint=(0.8, 0.4)).open()


class RetiroFormScreen(Screen):
    def datos_formulario(self):
        campos = [
            "r_cliente_nombre", "r_cliente_direccion", "r_cliente_telefono", "r_cliente_email",
            "r_equipo_tipo", "r_equipo_marca_modelo", "r_equipo_serie", "r_accesorios",
            "r_estado_fisico", "r_motivo_retiro", "r_tecnico", "r_observaciones",
        ]
        return {c[2:]: self.ids[c].text.strip() for c in campos}

    def ir_a_firma(self):
        datos = self.datos_formulario()
        if not datos["cliente_nombre"] or not datos["equipo_tipo"]:
            self._mostrar_mensaje("Completa al menos el nombre del cliente y el tipo de equipo.")
            return
        self.manager.current = "retiro_signature"

    def _mostrar_mensaje(self, texto):
        Popup(title="Aviso", content=Label(text=texto), size_hint=(0.8, 0.4)).open()


class RetiroSignatureScreen(Screen):
    clausula = StringProperty(CLAUSULA_RETIRO_TEXTO)

    def confirmar(self, pad):
        if not pad.tiene_firma():
            self._mostrar_mensaje("El cliente debe firmar antes de continuar.")
            return

        form_screen = self.manager.get_screen("retiro_form")
        datos = form_screen.datos_formulario()
        numero_retiro = siguiente_numero_retiro()
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")

        firma_path = os.path.join(FIRMA_DIR, f"{numero_retiro}_firma.png")
        pad.exportar_png(firma_path)

        pdf_path = os.path.join(PDF_DIR, f"{numero_retiro}.pdf")
        generar_pdf_retiro(numero_retiro, fecha, datos, firma_path, pdf_path)
        guardar_retiro_bd(numero_retiro, fecha, datos, firma_path, pdf_path)

        pad.limpiar()
        self.manager.current = "menu"
        mostrar_popup_pdf(pdf_path, f"Remito {numero_retiro} generado correctamente.")

    def _mostrar_mensaje(self, texto):
        Popup(title="Aviso", content=Label(text=texto), size_hint=(0.8, 0.4)).open()


def generar_pdf(numero_ot, fecha, datos, foto_path, firma_path, pdf_path):
    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle("titulo", parent=styles["Title"], fontSize=16)
    normal = styles["Normal"]

    doc = SimpleDocTemplate(pdf_path, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm)

    encabezado_texto = Paragraph(
        f"<b>{EMPRESA_NOMBRE}</b><br/>{EMPRESA_RUBRO}<br/>{EMPRESA_DIRECCION}<br/>{EMPRESA_TELEFONO}",
        normal,
    )
    if os.path.exists(LOGO_PATH):
        encabezado = Table(
            [[RLImage(LOGO_PATH, width=2.2 * cm, height=2.2 * cm), encabezado_texto]],
            colWidths=[2.6 * cm, 13.4 * cm],
        )
        encabezado.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        elementos = [encabezado, Spacer(1, 10)]
    else:
        elementos = [encabezado_texto, Spacer(1, 10)]

    elementos += [
        Paragraph("Orden de Trabajo", titulo_style),
        Paragraph(f"N&deg; {numero_ot} &nbsp;&nbsp; Fecha: {fecha}", normal),
        Spacer(1, 12),
    ]

    def tabla(titulo, filas):
        elementos.append(Paragraph(titulo, styles["Heading3"]))
        t = Table(filas, colWidths=[5 * cm, 11 * cm])
        t.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        elementos.append(t)
        elementos.append(Spacer(1, 10))

    tabla("Datos del cliente", [
        ["Nombre", datos["cliente_nombre"]],
        ["Direccion", datos["cliente_direccion"]],
        ["Telefono", datos["cliente_telefono"]],
        ["Email", datos["cliente_email"]],
    ])

    tabla("Datos del equipo", [
        ["Tipo", datos["equipo_tipo"]],
        ["Marca / Modelo", datos["equipo_marca_modelo"]],
        ["N. Serie", datos["equipo_serie"]],
        ["Accesorios", datos["accesorios"]],
        ["Estado fisico", datos["estado_fisico"]],
    ])

    tabla("Servicio realizado", [
        ["Falla reportada", datos["falla_reportada"]],
        ["Diagnostico", datos["diagnostico"]],
        ["Trabajo realizado", datos["trabajo_realizado"]],
        ["Repuestos", datos["repuestos"]],
        ["Costo total", datos["costo_total"]],
        ["Tecnico", datos["tecnico"]],
        ["Garantia (dias)", datos["garantia_dias"]],
        ["Observaciones", datos["observaciones"]],
    ])

    if foto_path and os.path.exists(foto_path):
        elementos.append(Paragraph("Foto del equipo", styles["Heading3"]))
        elementos.append(RLImage(foto_path, width=8 * cm, height=6 * cm))
        elementos.append(Spacer(1, 10))

    elementos.append(Paragraph("Clausulas de entrega y retiro", styles["Heading3"]))
    elementos.append(Paragraph(CLAUSULA_TEXTO, normal))
    elementos.append(Spacer(1, 10))

    elementos.append(Paragraph("Firma del cliente (aceptacion de retiro)", styles["Heading3"]))
    if os.path.exists(firma_path):
        elementos.append(RLImage(firma_path, width=8 * cm, height=3 * cm))

    doc.build(elementos)


def guardar_en_bd(numero_ot, fecha, datos, foto_path, firma_path, pdf_path):
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO ordenes (
            numero_ot, fecha, cliente_nombre, cliente_direccion, cliente_telefono,
            cliente_email, equipo_tipo, equipo_marca_modelo, equipo_serie, accesorios,
            estado_fisico, falla_reportada, diagnostico, trabajo_realizado, repuestos,
            costo_total, tecnico, garantia_dias, observaciones, foto_path, firma_path, pdf_path
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            numero_ot, fecha, datos["cliente_nombre"], datos["cliente_direccion"],
            datos["cliente_telefono"], datos["cliente_email"], datos["equipo_tipo"],
            datos["equipo_marca_modelo"], datos["equipo_serie"], datos["accesorios"],
            datos["estado_fisico"], datos["falla_reportada"], datos["diagnostico"],
            datos["trabajo_realizado"], datos["repuestos"], datos["costo_total"],
            datos["tecnico"], datos["garantia_dias"], datos["observaciones"],
            foto_path, firma_path, pdf_path,
        ),
    )
    conn.commit()
    conn.close()


def generar_pdf_retiro(numero_retiro, fecha, datos, firma_path, pdf_path):
    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle("titulo", parent=styles["Title"], fontSize=16)
    normal = styles["Normal"]

    doc = SimpleDocTemplate(pdf_path, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm)

    encabezado_texto = Paragraph(
        f"<b>{EMPRESA_NOMBRE}</b><br/>{EMPRESA_RUBRO}<br/>{EMPRESA_DIRECCION}<br/>{EMPRESA_TELEFONO}",
        normal,
    )
    if os.path.exists(LOGO_PATH):
        encabezado = Table(
            [[RLImage(LOGO_PATH, width=2.2 * cm, height=2.2 * cm), encabezado_texto]],
            colWidths=[2.6 * cm, 13.4 * cm],
        )
        encabezado.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        elementos = [encabezado, Spacer(1, 10)]
    else:
        elementos = [encabezado_texto, Spacer(1, 10)]

    elementos += [
        Paragraph("Remito de Retiro de Equipo", titulo_style),
        Paragraph(f"N&deg; {numero_retiro} &nbsp;&nbsp; Fecha: {fecha}", normal),
        Spacer(1, 12),
    ]

    def tabla(titulo, filas):
        elementos.append(Paragraph(titulo, styles["Heading3"]))
        t = Table(filas, colWidths=[5 * cm, 11 * cm])
        t.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        elementos.append(t)
        elementos.append(Spacer(1, 10))

    tabla("Datos del cliente", [
        ["Nombre", datos["cliente_nombre"]],
        ["Direccion", datos["cliente_direccion"]],
        ["Telefono", datos["cliente_telefono"]],
        ["Email", datos["cliente_email"]],
    ])

    tabla("Datos del equipo retirado", [
        ["Tipo", datos["equipo_tipo"]],
        ["Marca / Modelo", datos["equipo_marca_modelo"]],
        ["N. Serie", datos["equipo_serie"]],
        ["Accesorios", datos["accesorios"]],
        ["Estado fisico al retirar", datos["estado_fisico"]],
    ])

    tabla("Motivo del retiro", [
        ["Falla informada", datos["motivo_retiro"]],
        ["Tecnico que retira", datos["tecnico"]],
        ["Observaciones", datos["observaciones"]],
    ])

    elementos.append(Paragraph("Clausulas del retiro", styles["Heading3"]))
    elementos.append(Paragraph(CLAUSULA_RETIRO_TEXTO, normal))
    elementos.append(Spacer(1, 10))

    elementos.append(Paragraph("Firma del cliente (autorizacion de retiro)", styles["Heading3"]))
    if os.path.exists(firma_path):
        elementos.append(RLImage(firma_path, width=8 * cm, height=3 * cm))

    doc.build(elementos)


def guardar_retiro_bd(numero_retiro, fecha, datos, firma_path, pdf_path):
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO retiros (
            numero_retiro, fecha, cliente_nombre, cliente_direccion, cliente_telefono,
            cliente_email, equipo_tipo, equipo_marca_modelo, equipo_serie, accesorios,
            estado_fisico, motivo_retiro, observaciones, tecnico, firma_path, pdf_path
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            numero_retiro, fecha, datos["cliente_nombre"], datos["cliente_direccion"],
            datos["cliente_telefono"], datos["cliente_email"], datos["equipo_tipo"],
            datos["equipo_marca_modelo"], datos["equipo_serie"], datos["accesorios"],
            datos["estado_fisico"], datos["motivo_retiro"], datos["observaciones"],
            datos["tecnico"], firma_path, pdf_path,
        ),
    )
    conn.commit()
    conn.close()


def compartir_pdf(pdf_path):
    try:
        from plyer import share
        share.share(title="Orden de trabajo", text="Adjunto su orden de trabajo", filepath=pdf_path)
    except Exception:
        pass


def mostrar_popup_pdf(pdf_path, mensaje):
    contenido = BoxLayout(orientation="vertical", spacing=10, padding=10)
    contenido.add_widget(Label(text=f"{mensaje}\n\n{os.path.basename(pdf_path)}"))

    boton_compartir = Button(text="Compartir PDF", size_hint_y=None, height=48)
    boton_cerrar = Button(text="Cerrar", size_hint_y=None, height=48)
    contenido.add_widget(boton_compartir)
    contenido.add_widget(boton_cerrar)

    popup = Popup(title="PDF listo", content=contenido, size_hint=(0.85, 0.5))
    boton_compartir.bind(on_release=lambda *_: compartir_pdf(pdf_path))
    boton_cerrar.bind(on_release=popup.dismiss)
    popup.open()


class RichardApkApp(App):
    logo_path = StringProperty(LOGO_PATH if os.path.exists(LOGO_PATH) else "")

    def build(self):
        return Builder.load_string(KV)


if __name__ == "__main__":
    RichardApkApp().run()
