from datetime import datetime, time
import pandas as pd

# Definiciones
hora_inicio_jornada = time(8, 30)
hora_fin_jornada = time(17, 0)
feriados_mexico = []  # Puedes llenar esta lista con fechas de feriados

def jornada_valida(entrada, salida):
    if isinstance(entrada, time) and isinstance(salida, time):
        total_horas = (datetime.combine(datetime.today(), salida) - datetime.combine(datetime.today(), entrada)).total_seconds() / 3600
        return total_horas >= 5 and entrada <= hora_fin_jornada and salida >= hora_inicio_jornada
    return False

def procesar_asistencias(df):
    usuarios = df['ID de Usuario'].unique()
    resultados = []

    for uid in usuarios:
        bloque = []
        sub = df[df['ID de Usuario'] == uid].copy()
        nombre = sub['Nombre'].iloc[0]
        fechas_completas = pd.date_range(start=sub['Fecha'].min(), end=sub['Fecha'].max(), freq='D')

        for fecha in fechas_completas:
            dia = fecha.date()
            dia_semana = fecha.weekday()
            registros_dia = sub[sub['Fecha'] == dia].sort_values(by="Tiempo").reset_index(drop=True)

            # Eliminar duplicados por estado con diferencia menor a 3 minutos
            filtrados = []
            for idx, row in registros_dia.iterrows():
                if not filtrados:
                    filtrados.append(row.to_dict())
                else:
                    last = filtrados[-1]
                    diff = abs((row["Tiempo"] - last["Tiempo"]).total_seconds())
                    if row["Estado"] != last["Estado"] or diff > 180:
                        filtrados.append(row.to_dict())

            registros = pd.DataFrame(filtrados)

            if registros.empty:
                if dia_semana < 6 and dia not in feriados_mexico:
                    bloque.append([uid, nombre, dia, "", "FALTA", 0, 0])
                continue

            pares = []
            stack = []

            for _, row in registros.iterrows():
                if row['Estado'] == "Entrada":
                    stack.append(row['Tiempo'])
                elif row['Estado'] == "Salida":
                    if stack:
                        entrada = stack.pop(0)
                        salida = row['Tiempo']
                        pares.append((entrada, salida))
                    else:
                        pares.append(("NO SE REGISTRO ENTRADA", row['Tiempo']))

            for entrada in stack:
                pares.append((entrada, "NO SE REGISTRO SALIDA"))

            jornada_contada = False

            for ent, sal in pares:
                entrada_hora = ent.time() if not isinstance(ent, str) else None
                salida_hora = sal.time() if not isinstance(sal, str) else None

                if isinstance(ent, str) or isinstance(sal, str):
                    if isinstance(ent, datetime) and ent.time() <= hora_fin_jornada and not jornada_contada:
                        jornada_contada = True
                        bloque.append([
                            uid, nombre, dia,
                            ent.time(), sal if isinstance(sal, str) else sal.time(),
                            1, 0
                        ])
                    else:
                        bloque.append([
                            uid, nombre, dia,
                            ent if isinstance(ent, str) else ent.time(),
                            sal if isinstance(sal, str) else sal.time(),
                            0, 0
                        ])
                    continue

                horas_trabajadas = (sal - ent).total_seconds() / 3600
                es_valida = jornada_valida(entrada_hora, salida_hora)

                if es_valida and not jornada_contada:
                    jornada_contada = True
                    dia_trabajado = 1
                    horas_extra = horas_trabajadas - 8.5 if horas_trabajadas > 8.5 else 0
                else:
                    dia_trabajado = 0
                    horas_extra = 0

                bloque.append([
                    uid, nombre, dia,
                    entrada_hora, salida_hora,
                    dia_trabajado,
                    round(horas_extra, 2)
                ])

        bloque_df = pd.DataFrame(bloque, columns=[
            "Id de usuario", "Nombre", "Fecha", "Entrada", "Salida",
            "Día trabajado", "Horas Extras"
        ])
        bloque_df[["Día trabajado", "Horas Extras"]] = bloque_df[[
            "Día trabajado", "Horas Extras"
        ]].apply(pd.to_numeric, errors='coerce').fillna(0)

        total_horas = bloque_df["Horas Extras"].sum()
        dec = total_horas % 1
        if dec < 0.5:
            total_redondeado = int(total_horas)
        elif 0.5 <= dec < 0.9:
            total_redondeado = int(total_horas) + 0.5
        else:
            total_redondeado = int(total_horas) + 1.0

        total_fila = pd.DataFrame([[
            uid, nombre, "", "", "TOTAL",
            bloque_df["Día trabajado"].sum(),
            total_redondeado
        ]], columns=bloque_df.columns)

        resultados.append(bloque_df)
        resultados.append(total_fila)
        resultados.append(pd.DataFrame([[""] * len(bloque_df.columns)] * 2, columns=bloque_df.columns))

    df_final = pd.concat(resultados, ignore_index=True)
    return df_final
