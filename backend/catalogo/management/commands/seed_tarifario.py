from decimal import Decimal

from django.core.management.base import BaseCommand

from catalogo.models import Examen, Paquete, TarifarioExamen, TarifarioPaquete, Zona

EXAMENES = [
    ("HB", "Hemoglobina", "sangre", "numerico", "g/dL", False, "", ""),
    ("HT", "Hematocrito", "sangre", "numerico", "%", False, "", ""),
    ("Cl", "Cloro", "sangre", "numerico", "mmol/L", False, "", ""),
    ("Na", "Sodio", "sangre", "numerico", "mmol/L", False, "", ""),
    ("K", "Potasio", "sangre", "numerico", "mmol/L", False, "", ""),
    ("P", "Fosforo inorganico (fosfato)", "sangre", "numerico", "mg/dL", False, "", ""),
    ("Ca", "Calcio total", "sangre", "numerico", "mg/dL", False, "", ""),
    ("NNU", "Nitrogeno ureico cuantitativo (Pre y Post)", "sangre", "numerico", "mg/dL", True, "", ""),
    ("AST", "Aspartato aminotransferasa (AST/SGOT)", "sangre", "numerico", "U/L", False, "", ""),
    ("ALT", "Alanina aminotransferasa (ALT/SGPT)", "sangre", "numerico", "U/L", False, "", ""),
    ("PTH", "Dosaje de Paratohormona (PTH)", "sangre", "numerico", "pg/mL", False, "", ""),
    ("FE", "Dosaje de Hierro", "sangre", "numerico", "ug/dL", False, "", ""),
    ("FERR", "Dosaje de Ferritina", "sangre", "numerico", "ng/mL", False, "", ""),
    ("TRF", "Dosaje de Transferrina", "sangre", "numerico", "mg/dL", False, "", ""),
    ("HIV", "Anticuerpos HIV-1 y HIV-2 (analisis unico)", "sangre", "texto", "", False, "", "No reactivo"),
    ("RPR", "Prueba de sifilis (anticuerpo no treponemico, cualitativo)", "sangre", "texto", "", False, "", "No reactivo"),
    ("HBsAg", "Antigeno de superficie hepatitis B (HBsAg)", "sangre", "texto", "", False, "", "No reactivo"),
    ("HBsAb", "Anticuerpo contra antigeno de superficie hepatitis B (HBsAb)", "sangre", "texto", "", False, "", "No reactivo"),
    ("HBcAb", "Anticuerpo contra antigeno nucleocapside hepatitis B (HBcAb) total", "sangre", "texto", "", False, "", "No reactivo"),
    ("HCV", "Anticuerpo contra hepatitis C", "sangre", "texto", "", False, "", "No reactivo"),
    ("HTLV", "Anticuerpo para HTLV-1", "sangre", "texto", "", False, "", "No reactivo"),
    ("AG-MIC", "Analisis microbiologico de Aguas de Dialisis", "aguas", "texto", "", False, "", ""),
    ("AG-QUIM", "Contaminantes quimicos y electrolitos de Dialisis", "aguas", "texto", "", False, "", ""),
    ("AG-END", "Analisis de Endotoxinas", "aguas", "texto", "", False, "", ""),
]

PAQUETES = [
    ("Control Mensual", "mensual", "30.00", ["NNU", "HB", "HT", "Cl", "Na", "K", "P", "Ca"]),
    (
        "Control Bimestral",
        "bimestral",
        "38.00",
        ["NNU", "HB", "HT", "Cl", "Na", "K", "P", "Ca", "AST", "ALT"],
    ),
    (
        "Control Trimestral",
        "trimestral",
        "70.00",
        ["NNU", "HB", "HT", "Cl", "Na", "K", "P", "Ca", "PTH", "FE", "FERR", "TRF"],
    ),
    (
        "Control Semestral",
        "semestral",
        "153.00",
        [
            "NNU", "HB", "HT", "Cl", "Na", "K", "P", "Ca",
            "AST", "ALT", "PTH", "FE", "FERR", "TRF",
            "HIV", "RPR", "HBsAg", "HBsAb", "HBcAb", "HCV", "HTLV",
        ],
    ),
]

AGUAS_PRECIOS = {"AG-MIC": "100.00", "AG-QUIM": "200.00", "AG-END": "200.00"}


class Command(BaseCommand):
    help = "Carga catálogo de exámenes, paquetes y tarifarios base (idempotente)."

    def handle(self, *args, **options):
        Zona.objects.get_or_create(nombre="Lima")
        Zona.objects.get_or_create(nombre="Provincia")

        for codigo, nombre, area, rtipo, unidad, pre_post, metodo, ref in EXAMENES:
            Examen.objects.get_or_create(
                codigo=codigo,
                defaults={
                    "nombre": nombre,
                    "area": area,
                    "resultado_tipo": rtipo,
                    "unidad": unidad,
                    "mide_pre_post": pre_post,
                    "metodo": metodo,
                    "ref_texto": ref,
                },
            )

        for nombre, frecuencia, precio, codigos in PAQUETES:
            paquete, _ = Paquete.objects.get_or_create(nombre=nombre, defaults={"frecuencia": frecuencia})
            for posicion, codigo in enumerate(codigos, start=1):
                examen = Examen.objects.get(codigo=codigo)
                paquete.examenes_compuestos.get_or_create(examen=examen, defaults={"orden": posicion})
            TarifarioPaquete.objects.get_or_create(
                paquete=paquete, zona=None, cliente=None, defaults={"precio": Decimal(precio)}
            )

        for codigo, precio in AGUAS_PRECIOS.items():
            examen = Examen.objects.get(codigo=codigo)
            TarifarioExamen.objects.get_or_create(
                examen=examen, zona=None, cliente=None, defaults={"precio": Decimal(precio)}
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Catálogo listo: {Examen.objects.count()} exámenes, "
                f"{Paquete.objects.count()} paquetes y tarifas generales aplicadas."
            )
        )
        self.stdout.write(
            self.style.WARNING(
                "Recordatorio: definir en el admin los valores de referencia numéricos "
                "y las tarifas por cliente."
            )
        )