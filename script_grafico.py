import matplotlib.pyplot as plt
import pandas as pd

# Referencia al archivo suministro
df = pd.read_excel("datos_prueba.xlsx")

# Se separan los conteos de estudiantes bloqueados y no bloqueados
data = {
    "y_activos" : df[df['causa_bloqueo'].isna()]['matriculas'].value_counts(),
    "y_bloqueados" : df[df['causa_bloqueo'].notna()]['matriculas'].value_counts(),
}

# Número de matrículas con estudiantes activos como eje X
x_data = df["matriculas"].unique()

df = pd.DataFrame(data, index = x_data)

df_sorted = df.sort_index()

plt.style.use('bmh')

ax = df_sorted.plot(kind="bar", figsize=(10, 5))

plt.xlabel("Matricula", fontsize=12)
plt.ylabel("Número de Estudiantes", fontsize=12)
plt.grid("False")

plt.savefig('grafico_discusion.png', dpi=300, bbox_inches='tight')

plt.show()