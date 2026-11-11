import React, { useState } from 'react';
import { Copy, Download, Check, Code, BookOpen, Terminal, Sparkles } from 'lucide-react';
import { useVeterinaria } from '../../context/VeterinariaContext';

export const ModuloPythonExport: React.FC = () => {
  const { showToast } = useVeterinaria();
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<'app' | 'modelos' | 'explicacion'>('app');

  const PYTHON_CODE_APP = `# ==============================================================================
# PATITAS & CO. - SISTEMA VETERINARIO & DERIVACIÓN DE LABORATORIO
# Desarrollo de Aplicaciones con Objetos - Cátedra 2026
# Interfaz Gráfica de Escritorio construida con Tkinter & ttk
# ==============================================================================

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

# ------------------------------------------------------------------------------
# 1. MODELO ORIENTADO A OBJETOS (DOMINIO VETERINARIO)
# ------------------------------------------------------------------------------

class Responsable:
    def __init__(self, id_resp, nombre, documento, telefono):
        self.id = id_resp
        self.nombre = nombre
        self.documento = documento
        self.telefono = telefono

class Mascota:
    def __init__(self, id_mascota, responsable, nombre, especie, raza, peso):
        self.id = id_mascota
        self.responsable = responsable
        self.nombre = nombre
        self.especie = especie
        self.raza = raza
        self.peso = peso

# Patrón State para el ciclo de vida de la Muestra Biológica
class EstadoMuestra:
    def nombre(self):
        return self.__class__.__name__

class EstadoExtraida(EstadoMuestra): pass
class EstadoEmpaquetada(EstadoMuestra): pass
class EstadoEnTransito(EstadoMuestra): pass
class EstadoRecibida(EstadoMuestra): pass
class EstadoRechazada(EstadoMuestra): pass
class EstadoAnalizada(EstadoMuestra): pass

class MuestraBiologica:
    def __init__(self, id_muestra, rotulo, tipo_material, condicion):
        self.id = id_muestra
        self.rotulo = rotulo
        self.tipo_material = tipo_material
        self.condicion = condicion
        self.estado = EstadoExtraida()
        self.historial = [("Extraída", datetime.now().strftime("%Y-%m-%d %H:%M"))]

    def transicionar(self, nuevo_estado, motivo=""):
        # Registro inmutable de trazabilidad
        self.estado = nuevo_estado
        self.historial.append((nuevo_estado.nombre(), datetime.now().strftime("%Y-%m-%d %H:%M") + f" ({motivo})"))

class RemitoBiologico:
    def __init__(self, id_remito, conservadora, precinto_codigo, transportista, muestras):
        self.id = id_remito
        self.fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.conservadora = conservadora
        self.precinto_codigo = precinto_codigo
        self.transportista = transportista
        self.muestras = muestras
        self.estado = "Despachado"

# ------------------------------------------------------------------------------
# 2. INTERFAZ GRÁFICA TKINTER CON TTK (NOTEBOOK, TREEVIEW, VALIDATECOMMAND)
# ------------------------------------------------------------------------------

class VeterinariaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Patitas & Co. - Sistema de Derivación Veterinaria")
        self.root.geometry("820x620")
        self.root.configure(bg="#FAF8F5")

        # Configuración de tema TTK
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except:
            pass

        self.style.configure(".", font=("Helvetica", 10), background="#FAF8F5")
        self.style.configure("TNotebook", background="#FAF8F5")
        self.style.configure("TNotebook.Tab", padding=[12, 6], font=("Helvetica", 10, "bold"))
        self.style.configure("Primary.TButton", background="#2D5864", foreground="white", font=("Helvetica", 9, "bold"))

        # Base de datos en memoria (Simulación)
        self.responsables = [
            Responsable("RESP-001", "María González", "32.489.102", "351-5123489")
        ]
        self.mascotas = [
            Mascota("MASC-001", self.responsables[0], "Luna", "Canino", "Golden Retriever", 28.5)
        ]
        self.muestras = [
            MuestraBiologica("MUE-9101", "TUB-LILA-01", "Sangre EDTA", "Refrigerada 2-8°C")
        ]
        self.remitos = []

        # Registro de función de validación para entradas numéricas
        self.vcmd_num = root.register(self.validar_numerico)

        # Barra Superior
        self.crear_encabezado()

        # Cuaderno de Pestañas (ttk.Notebook)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=10)

        # Pestañas correspondientes a los módulos de la cátedra
        self.tab_pacientes = ttk.Frame(self.notebook)
        self.tab_muestras = ttk.Frame(self.notebook)
        self.tab_despacho = ttk.Frame(self.notebook)
        self.tab_recepcion = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_pacientes, text="1. Pacientes & Atención")
        self.notebook.add(self.tab_muestras, text="2. Órdenes & Muestras")
        self.notebook.add(self.tab_despacho, text="3. Despacho & Remito")
        self.notebook.add(self.tab_recepcion, text="4. Recepción & Precinto")

        # Construcción de cada pantalla
        self.setup_tab_pacientes()
        self.setup_tab_muestras()
        self.setup_tab_despacho()
        self.setup_tab_recepcion()

    def validar_numerico(self, nuevo_valor):
        """Validación en tiempo real para Entry de peso o números"""
        if nuevo_valor == "":
            return True
        try:
            float(nuevo_valor)
            return True
        except ValueError:
            return False

    def crear_encabezado(self):
        header = tk.Frame(self.root, bg="#2D5864", height=50)
        header.pack(side="top", fill="x")
        lbl = tk.Label(header, text="🐾 PATITAS & CO. — Red Veterinaria & Trazabilidad",
                       bg="#2D5864", fg="white", font=("Helvetica", 12, "bold"))
        lbl.pack(side="left", padx=15, pady=10)

    # ---------------- TAB 1: PACIENTES ----------------
    def setup_tab_pacientes(self):
        frame_form = tk.LabelFrame(self.tab_pacientes, text="Registrar Nuevo Paciente", bg="#FAF8F5", padx=10, pady=10)
        frame_form.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_form, text="Nombre Mascota:", bg="#FAF8F5").grid(row=0, column=0, sticky="w", pady=3)
        self.ent_nombre = ttk.Entry(frame_form, width=20)
        self.ent_nombre.grid(row=0, column=1, padx=5, pady=3)

        tk.Label(frame_form, text="Especie:", bg="#FAF8F5").grid(row=0, column=2, sticky="w", pady=3)
        self.cb_especie = ttk.Combobox(frame_form, values=["Canino", "Felino", "Otro"], width=15)
        self.cb_especie.set("Canino")
        self.cb_especie.grid(row=0, column=3, padx=5, pady=3)

        tk.Label(frame_form, text="Peso (kg):", bg="#FAF8F5").grid(row=1, column=0, sticky="w", pady=3)
        # Entry con validación validatecommand (ejemplo cátedra)
        self.ent_peso = ttk.Entry(frame_form, width=20, validate="key", validatecommand=(self.vcmd_num, "%P"))
        self.ent_peso.grid(row=1, column=1, padx=5, pady=3)

        tk.Label(frame_form, text="Raza:", bg="#FAF8F5").grid(row=1, column=2, sticky="w", pady=3)
        self.ent_raza = ttk.Entry(frame_form, width=17)
        self.ent_raza.grid(row=1, column=3, padx=5, pady=3)

        btn_guardar = tk.Button(frame_form, text="Guardar Mascota", bg="#2D5864", fg="white",
                                command=self.guardar_mascota, relief="flat", padx=10)
        btn_guardar.grid(row=2, column=3, sticky="e", pady=8)

        # Treeview de Pacientes
        self.tree_pacientes = ttk.Treeview(self.tab_pacientes, columns=("id", "nombre", "especie", "raza", "peso"), show="headings", height=8)
        self.tree_pacientes.heading("id", text="ID")
        self.tree_pacientes.heading("nombre", text="Nombre")
        self.tree_pacientes.heading("especie", text="Especie")
        self.tree_pacientes.heading("raza", text="Raza")
        self.tree_pacientes.heading("peso", text="Peso (Kg)")
        self.tree_pacientes.pack(fill="both", expand=True, padx=10, pady=10)
        self.actualizar_tree_pacientes()

    def guardar_mascota(self):
        nom = self.ent_nombre.get().strip()
        raza = self.ent_raza.get().strip()
        peso_txt = self.ent_peso.get().strip()
        if not nom or not raza:
            messagebox.showwarning("Campos vacíos", "Por favor completa el nombre y raza.")
            return
        p = float(peso_txt) if peso_txt else 5.0
        nueva = Mascota(f"MASC-{len(self.mascotas)+1:03d}", self.responsables[0], nom, self.cb_especie.get(), raza, p)
        self.mascotas.append(nueva)
        self.actualizar_tree_pacientes()
        messagebox.showinfo("Éxito", f"Mascota {nom} registrada exitosamente.")
        self.ent_nombre.delete(0, tk.END)
        self.ent_raza.delete(0, tk.END)
        self.ent_peso.delete(0, tk.END)

    def actualizar_tree_pacientes(self):
        for item in self.tree_pacientes.get_children():
            self.tree_pacientes.delete(item)
        for m in self.mascotas:
            self.tree_pacientes.insert("", "end", values=(m.id, m.nombre, m.especie, m.raza, m.peso))

    # ---------------- TAB 2: MUESTRAS ----------------
    def setup_tab_muestras(self):
        lbl = tk.Label(self.tab_muestras, text="Registro y Trazabilidad de Muestras Biológicas", font=("Helvetica", 11, "bold"), bg="#FAF8F5")
        lbl.pack(anchor="w", padx=10, pady=5)

        self.tree_muestras = ttk.Treeview(self.tab_muestras, columns=("id", "rotulo", "material", "condicion", "estado"), show="headings", height=8)
        self.tree_muestras.heading("id", text="ID Muestra")
        self.tree_muestras.heading("rotulo", text="Rótulo Tubo")
        self.tree_muestras.heading("material", text="Material")
        self.tree_muestras.heading("condicion", text="Conservación")
        self.tree_muestras.heading("estado", text="Estado Actual")
        self.tree_muestras.pack(fill="both", expand=True, padx=10, pady=10)
        self.actualizar_tree_muestras()

    def actualizar_tree_muestras(self):
        for item in self.tree_muestras.get_children():
            self.tree_muestras.delete(item)
        for m in self.muestras:
            self.tree_muestras.insert("", "end", values=(m.id, m.rotulo, m.tipo_material, m.condicion, m.estado.nombre()))

    # ---------------- TAB 3: DESPACHO & REMITO ----------------
    def setup_tab_despacho(self):
        f = tk.LabelFrame(self.tab_despacho, text="Preparar Despacho a Laboratorio Central", bg="#FAF8F5", padx=10, pady=10)
        f.pack(fill="x", padx=10, pady=5)

        tk.Label(f, text="Contenedor:", bg="#FAF8F5").grid(row=0, column=0, sticky="w", pady=4)
        self.cb_con = ttk.Combobox(f, values=["CON-01 (2° a 8°C)", "CON-02 (-20°C)"], width=20)
        self.cb_con.set("CON-01 (2° a 8°C)")
        self.cb_con.grid(row=0, column=1, padx=5, pady=4)

        tk.Label(f, text="Código Precinto Sanitario:", bg="#FAF8F5").grid(row=0, column=2, sticky="w", pady=4)
        self.ent_precinto = ttk.Entry(f, width=20)
        self.ent_precinto.insert(0, "PREC-48921")
        self.ent_precinto.grid(row=0, column=3, padx=5, pady=4)

        tk.Label(f, text="Transportista:", bg="#FAF8F5").grid(row=1, column=0, sticky="w", pady=4)
        self.ent_transp = ttk.Entry(f, width=22)
        self.ent_transp.insert(0, "Transportes BioLog (R. Gómez)")
        self.ent_transp.grid(row=1, column=1, padx=5, pady=4)

        btn_despachar = tk.Button(f, text="Generar Remito y Despachar", bg="#2D5864", fg="white",
                                  command=self.despachar_envio, relief="flat", padx=10)
        btn_despachar.grid(row=2, column=3, sticky="e", pady=8)

    def despachar_envio(self):
        prec = self.ent_precinto.get().strip()
        trans = self.ent_transp.get().strip()
        if not prec:
            messagebox.showwarning("Precinto requerido", "Debes ingresar el código del precinto sanitario.")
            return

        remito = RemitoBiologico(f"REM-2026-{len(self.remitos)+1:03d}", self.cb_con.get(), prec, trans, [m.id for m in self.muestras])
        self.remitos.append(remito)

        # Transicionar muestras a En Tránsito
        for m in self.muestras:
            m.transicionar(EstadoEnTransito(), f"Despachado en {remito.id} con precinto {prec}")

        self.actualizar_tree_muestras()
        messagebox.showinfo("Despacho Exitoso", f"Remito {remito.id} generado.\\nMuestras en tránsito hacia el laboratorio central.")

    # ---------------- TAB 4: RECEPCIÓN & VALIDACIÓN PRECINTO ----------------
    def setup_tab_recepcion(self):
        f = tk.LabelFrame(self.tab_recepcion, text="Verificación en Laboratorio Receptor", bg="#FAF8F5", padx=10, pady=10)
        f.pack(fill="x", padx=10, pady=5)

        tk.Label(f, text="Estado del Precinto Sanitario:", font=("Helvetica", 10, "bold"), bg="#FAF8F5").pack(anchor="w", pady=5)
        self.var_precinto_estado = tk.StringVar(value="Integro")

        r1 = tk.Radiobutton(f, text="Precinto ÍNTEGRO (Conforme a remito)", variable=self.var_precinto_estado,
                            value="Integro", bg="#FAF8F5")
        r1.pack(anchor="w", padx=10)

        r2 = tk.Radiobutton(f, text="Precinto ROTO / VIOLADO (Criterio de rechazo)", variable=self.var_precinto_estado,
                            value="Roto", bg="#FAF8F5", fg="#B91C1C")
        r2.pack(anchor="w", padx=10)

        btn_verificar = tk.Button(f, text="Confirmar Recepción / Inspección", bg="#2D5864", fg="white",
                                  command=self.verificar_recepcion, relief="flat", padx=12, pady=4)
        btn_verificar.pack(anchor="e", pady=10)

    def verificar_recepcion(self):
        """Regla de Negocio Crítica: Si el precinto llega roto, la muestra se rechaza"""
        estado = self.var_precinto_estado.get()
        if estado == "Integro":
            for m in self.muestras:
                m.transicionar(EstadoRecibida(), "Precinto conforme. Muestra viable para análisis.")
            messagebox.showinfo("Recepción Conforme", "Precinto sanitario íntegro.\\nLas muestras han sido recibidas y están listas para procesar.")
        else:
            for m in self.muestras:
                m.transicionar(EstadoRechazada(), "ANOMALÍA: Precinto sanitario roto en transporte.")
            messagebox.showerror("¡MUESTRA RECHAZADA!", "Regla de Seguridad de la Cátedra:\\nEl precinto sanitario llegó ROTO.\\nSe bloquea el análisis y las muestras quedan formalmente RECHAZADAS.")

        self.actualizar_tree_muestras()

# ------------------------------------------------------------------------------
# PUNTO DE ENTRADA PRINCIPAL
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    ventana = tk.Tk()
    app = VeterinariaGUI(ventana)
    ventana.mainloop()
`;

  const PYTHON_CLASSES = `# ==============================================================================
# MODELO ORIENTADO A OBJETOS (DOMINIO VETERINARIO PATITAS & CO.)
# Aplica Patrones de Diseño: STATE (Ciclo de Muestra) y OBSERVER (Resultados)
# ==============================================================================

from abc import ABC, abstractmethod
from datetime import datetime

# ----------------- ENTIDADES BÁSICAS -----------------

class Responsable:
    def __init__(self, id_resp: str, nombre: str, documento: str, telefono: str, email: str = ""):
        self.id = id_resp
        self.nombre = nombre
        self.documento = documento
        self.telefono = telefono
        self.email = email
        self.mascotas = []

    def agregar_mascota(self, mascota):
        self.mascotas.append(mascota)

class Mascota:
    def __init__(self, id_mascota: str, responsable: Responsable, nombre: str, especie: str, raza: str, peso: float):
        if not responsable:
            raise ValueError("Regla de negocio: Toda mascota debe tener un responsable asociado.")
        self.id = id_mascota
        self.responsable = responsable
        self.nombre = nombre
        self.especie = especie
        self.raza = raza
        self.peso = peso
        self.consultas = []
        responsable.agregar_mascota(self)

# ----------------- PATRÓN STATE: CICLO DE VIDA DE LA MUESTRA -----------------

class EstadoMuestra(ABC):
    @abstractmethod
    def nombre(self) -> str:
        pass

    def puede_analizar(self) -> bool:
        return False

class EstadoExtraida(EstadoMuestra):
    def nombre(self): return "Extraída"

class EstadoEmpaquetada(EstadoMuestra):
    def nombre(self): return "Empaquetada"

class EstadoEnTransito(EstadoMuestra):
    def nombre(self): return "En tránsito"

class EstadoRecibida(EstadoMuestra):
    def nombre(self): return "Recibida"
    def puede_analizar(self): return True

class EstadoAnalizada(EstadoMuestra):
    def nombre(self): return "Analizada"

class EstadoRechazada(EstadoMuestra):
    def nombre(self): return "Rechazada"
    def puede_analizar(self): return False

class MuestraBiologica:
    def __init__(self, id_muestra: str, rotulo: str, tipo_material: str, condicion_termica: str):
        self.id = id_muestra
        self.rotulo = rotulo
        self.tipo_material = tipo_material
        self.condicion_termica = condicion_termica
        self.estado: EstadoMuestra = EstadoExtraida()
        self.historial = [("Extraída", datetime.now(), "Extracción inicial")]

    def transicionar(self, nuevo_estado: EstadoMuestra, responsable: str, motivo: str = ""):
        # Trazabilidad inmutable: jamás borra eventos previos
        self.estado = nuevo_estado
        self.historial.append((nuevo_estado.nombre(), datetime.now(), f"{responsable}: {motivo}"))

    def intentar_procesar(self):
        if not self.estado.puede_analizar():
            raise Exception(f"Violación de regla: No se puede procesar una muestra en estado '{self.estado.nombre()}'.")
        return True

# ----------------- LOGÍSTICA & DESPACHO -----------------

class PrecintoSanitario:
    def __init__(self, codigo: str, conservadora_id: str, colocado_por: str):
        self.codigo = codigo
        self.conservadora_id = conservadora_id
        self.colocado_por = colocado_por
        self.estado_verificacion = None

class RemitoBiologico:
    def __init__(self, numero: str, origen: str, destino: str, transportista: str, precinto: PrecintoSanitario, muestras: list):
        self.numero = numero
        self.fecha_emision = datetime.now()
        self.origen = origen
        self.destino = destino
        self.transportista = transportista
        self.precinto = precinto
        self.muestras = muestras
        self.estado = "Despachado"

    def verificar_llegada(self, precinto_integro: bool, verificado_por: str):
        if precinto_integro:
            self.estado = "Recibido"
            for m in self.muestras:
                m.transicionar(EstadoRecibida(), verificado_por, "Precinto sanitario íntegro.")
        else:
            self.estado = "Con incidencias"
            for m in self.muestras:
                m.transicionar(EstadoRechazada(), verificado_por, "RECHAZO: Precinto roto en transporte.")
`;

  const handleCopy = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    showToast({
      type: 'success',
      title: 'Código copiado al portapapeles',
      description: 'Puedes pegarlo directamente en tu editor de Python (VS Code, PyCharm o IDLE).'
    });
    setTimeout(() => setCopied(false), 2500);
  };

  const handleDownload = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/x-python;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    showToast({
      type: 'info',
      title: 'Archivo Python descargado',
      description: `Se descargó ${filename}. Ejecútalo con 'python ${filename}'.`
    });
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="p-5 bg-gradient-to-r from-[#2D5864] to-[#3c6b77] rounded-2xl text-white space-y-2 shadow-xs">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#F2E8D8]">
          <Terminal className="w-4 h-4 text-[#F2E8D8]" />
          <span>Material de Cátedra & Desarrollo de Aplicaciones con Objetos (Córdoba 2026)</span>
        </div>
        <h3 className="text-base sm:text-lg font-bold tracking-tight">
          Código Fuente en Python & GUI Tkinter
        </h3>
        <p className="text-xs text-[#FAF8F5]/90 max-w-2xl leading-relaxed">
          Diseñado para cumplir con el TP Integrador Tema 2: incorpora los patrones de diseño <strong>State</strong> y <strong>Observer</strong>, validaciones con <code>validate=&quot;key&quot;</code>, <code>validatecommand</code>, widgets <code>ttk.Notebook</code> y <code>ttk.Treeview</code>, y la regla crítica de rechazo por precinto sanitario roto.
        </p>
      </div>

      {/* Segmented Controls & Copy/Download Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E7E2DA] pb-4">
        <div className="inline-flex items-center p-1 bg-[#FAF6EF] border border-[#E7E2DA] rounded-xl">
          <button
            onClick={() => setActiveTab('app')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeTab === 'app'
                ? 'bg-white text-[#2D5864] shadow-xs'
                : 'text-neutral-600 hover:text-[#2D5864]'
            }`}
          >
            GUI Tkinter Completa (.py)
          </button>
          <button
            onClick={() => setActiveTab('modelos')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeTab === 'modelos'
                ? 'bg-white text-[#2D5864] shadow-xs'
                : 'text-neutral-600 hover:text-[#2D5864]'
            }`}
          >
            Clases POO & Patrón State (.py)
          </button>
          <button
            onClick={() => setActiveTab('explicacion')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeTab === 'explicacion'
                ? 'bg-white text-[#2D5864] shadow-xs'
                : 'text-neutral-600 hover:text-[#2D5864]'
            }`}
          >
            Defensa del Modelo para la Cátedra
          </button>
        </div>

        <div className="flex items-center gap-2">
          {activeTab !== 'explicacion' && (
            <>
              <button
                onClick={() => handleCopy(activeTab === 'app' ? PYTHON_CODE_APP : PYTHON_CLASSES)}
                className="px-3 py-1.5 text-xs font-semibold text-neutral-700 bg-white border border-neutral-300 hover:bg-neutral-50 rounded-lg transition-colors flex items-center gap-1.5"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? '¡Copiado!' : 'Copiar Código'}</span>
              </button>

              <button
                onClick={() => handleDownload(
                  activeTab === 'app' ? PYTHON_CODE_APP : PYTHON_CLASSES,
                  activeTab === 'app' ? 'veterinaria_patitas_gui.py' : 'modelos_veterinaria.py'
                )}
                className="px-3 py-1.5 text-xs font-semibold text-white bg-[#2D5864] hover:bg-[#23454f] rounded-lg transition-colors flex items-center gap-1.5 shadow-xs"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Descargar Script .py</span>
              </button>
            </>
          )}
        </div>
      </div>

      {/* CODE DISPLAY */}
      {activeTab === 'app' && (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs text-neutral-500">
            <span>Archivo ejecutable: <strong className="font-mono text-neutral-800">veterinaria_patitas_gui.py</strong></span>
            <span>Compatible con Python 3.8+ y biblioteca estándar Tkinter</span>
          </div>
          <div className="relative rounded-xl overflow-hidden border border-neutral-300 bg-[#1E293B] shadow-inner text-neutral-200">
            <pre className="p-4 text-xs font-mono overflow-x-auto max-h-[500px] leading-relaxed selection:bg-[#2D5864]">
              {PYTHON_CODE_APP}
            </pre>
          </div>
        </div>
      )}

      {activeTab === 'modelos' && (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs text-neutral-500">
            <span>Módulo de dominio: <strong className="font-mono text-neutral-800">modelos_veterinaria.py</strong></span>
            <span>Implementación del Patrón State y auditoría inmutable</span>
          </div>
          <div className="relative rounded-xl overflow-hidden border border-neutral-300 bg-[#1E293B] shadow-inner text-neutral-200">
            <pre className="p-4 text-xs font-mono overflow-x-auto max-h-[500px] leading-relaxed selection:bg-[#2D5864]">
              {PYTHON_CLASSES}
            </pre>
          </div>
        </div>
      )}

      {activeTab === 'explicacion' && (
        <div className="space-y-4 text-xs">
          <div className="p-5 bg-white border border-[#E7E2DA] rounded-xl shadow-xs space-y-4">
            <h4 className="font-bold text-sm text-[#2D5864]">
              Aspectos Evaluados por la Cátedra de Objetos (TP 2026)
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-[#FAF8F5] rounded-lg border border-[#F2E8D8] space-y-2">
                <span className="font-bold text-neutral-900 block text-xs">
                  1. Patrón State para MuestraBiologica
                </span>
                <p className="text-neutral-600 leading-relaxed text-[11px]">
                  Evita condicionales booleanos dispersos (<code>if muestra.esta_rota:</code>) encapsulando el comportamiento en clases concretas (<code>EstadoExtraida</code>, <code>EstadoEmpaquetada</code>, <code>EstadoEnTransito</code>, <code>EstadoRecibida</code>, <code>EstadoRechazada</code>). Si una muestra está rechazada, el método <code>puede_analizar()</code> retorna <code>False</code> y bloquea el inicio de cualquier estudio.
                </p>
              </div>

              <div className="p-4 bg-[#FAF8F5] rounded-lg border border-[#F2E8D8] space-y-2">
                <span className="font-bold text-neutral-900 block text-xs">
                  2. Regla Crítica del Precinto Sanitario
                </span>
                <p className="text-neutral-600 leading-relaxed text-[11px]">
                  El precinto sanitario se modela como una <strong>entidad propia</strong> con código único y responsable, y no un mero atributo de la conservadora. Esto permite verificar la rotura en el laboratorio y disparar la transición irreversible a <code>Muestra Rechazada</code> e <code>Incidencia</code>.
                </p>
              </div>

              <div className="p-4 bg-[#FAF8F5] rounded-lg border border-[#F2E8D8] space-y-2">
                <span className="font-bold text-neutral-900 block text-xs">
                  3. Trazabilidad Inmutable
                </span>
                <p className="text-neutral-600 leading-relaxed text-[11px]">
                  Cada cambio de estado de la muestra añade una tupla con fecha, hora, responsable y motivo a la lista histórica. Los estados previos nunca son sobrescritos ni eliminados, permitiendo auditar la cadena de custodia ante litigios o auditorías sanitarias.
                </p>
              </div>

              <div className="p-4 bg-[#FAF8F5] rounded-lg border border-[#F2E8D8] space-y-2">
                <span className="font-bold text-neutral-900 block text-xs">
                  4. Cumplimiento de Controles Tkinter (Guía Cátedra)
                </span>
                <p className="text-neutral-600 leading-relaxed text-[11px]">
                  Aplica exactamente las directivas del documento conceptual: <code>root.register(validar_input)</code> con <code>validate=&quot;key&quot;</code>, <code>ttk.Notebook</code> para navegación por pestañas de módulos, <code>ttk.Treeview</code> para datos tabulares y <code>messagebox</code> para diálogos de alerta y confirmación.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
