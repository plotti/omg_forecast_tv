import streamlit as st
import numpy as np
import pandas as pd
from fbprophet import Prophet
import datetime as dt
import base64
import matplotlib.pyplot as plt


def main():
	st.markdown("# Reichweitenkurven-Vorraussagen-Tool")
	st.markdown("## Schritt 1")
	st.text("Bitte wählen Sie die Excel file mit den GRP / Reichweitendaten aus. Siehe Beispiel unten:")
	st.image("example.png",width =300)
	uploaded_file = st.file_uploader("Bitte wählen Sie die Excel file mit den GRP / Reichweitendaten aus.", type="xlsx")

	if uploaded_file is not None:
		df = pd.read_excel(uploaded_file)
		df.columns = ["GRP","RW"]

		st.markdown("## Schritt 2")
		existing_grps = int(df["GRP"].max())
		limit_grps = 1200
		half_way = int(existing_grps + (limit_grps-existing_grps)/2)
		grps = st.slider('Für bis zu vielen GRPs möchten sie vorraussagen?', existing_grps, limit_grps, half_way)
		max_reach = st.slider('Was ist die maximal mögliche Reichweite?', 0, 100, 80)
		

		if st.button('Berechnung beginnen'):
			st.write('Berechne Forecast mit Grps %s und Max Reach %s' % (grps,max_reach))
			result = predict(df,existing_grps,grps,max_reach)
			st.balloons()
			st.markdown("## Schritt 3: Ergebniss")
			plot_result(result)
			st.dataframe(result)
			result = result.to_csv(index=False)						
			st.markdown("### Donwload ")
			b64 = base64.b64encode(result.encode()).decode()  # some strings <-> bytes conversions necessary here
			href = f'<a href="data:file/csv;base64,{b64}" download="export.csv">Excel Datei herunterladen</a>'
			st.markdown(href, unsafe_allow_html=True)
		else:
			st.write('')


	# st.text("Schritt 1: Excel Hochladen")
	df = pd.read_excel('testkurve.xlsx')

def predict(df,existing_grps,max_grps,max_reach):
	df = df[1:]
	start = dt.datetime(1970,1,1)
	df['date'] = df["GRP"].apply(lambda x: start + dt.timedelta(x))
	df.columns = ["GRP","y", "ds"]
	df["cap"] = max_reach
	periods = max_grps - existing_grps

	m = Prophet(mcmc_samples=50,seasonality_mode='multiplicative',growth='logistic').fit(df);
	future = m.make_future_dataframe(periods=periods,freq='d')
	future["cap"] = max_reach #whats the max RW we can reach
	forecast = m.predict(future)
	forecast = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

	forecast["GRP"] = forecast["ds"].apply(lambda x: date_to_grps(x))
	result = pd.merge(df,forecast,on="GRP",how="right")[["GRP","y","yhat",'yhat_lower', 'yhat_upper',]]
	result["error"] = result["y"]-result["yhat"]
	result.columns = ["GRP","RW","RW_forecast","Min","Max","Fehler"]
	return result

def plot_result(result):
	result.index = result["GRP"]
	ax = result["RW"].plot(style='k.',figsize=(20,10))	
	ax = result["RW_forecast"].plot()
	ax.set_ylabel(ylabel="RW",fontsize=18)
	ax.set_xlabel(xlabel="GRP",fontsize=18)
	ax.set_title(label="Vorraussage Reichweite",fontsize=22)
	ax.fill_between(result.index, result["Min"], result["Max"],facecolor='green', alpha=0.2, interpolate=True)
	plt.tight_layout()
	st.pyplot()


def date_to_grps(time):
    start = dt.datetime(1970,1,1)
    return (time - start).days

if __name__ == "__main__":
    main()