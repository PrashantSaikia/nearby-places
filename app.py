import dash
from dash.dependencies import Output, Input, State
import dash_core_components as dcc
import dash_html_components as html
import plotly
import random
import plotly.graph_objs as go
import requests, json
import pandas as pd
import sqlite3

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(external_stylesheets=external_stylesheets)
server = app.server

colors = {'background': '#ffffff', 'text': '#33B5FF'}

blank_fig = {'data': [],
             'layout': go.Layout(
                xaxis={
                    'showticklabels': False,
                    'ticks': '',
                    'showgrid': False,
                    'zeroline': False
                },
                yaxis={
                    'showticklabels': False,
                    'ticks': '',
                    'showgrid': False,
                    'zeroline': False
                }
            )
        }

app.layout = html.Div(style={'backgroundColor': colors['background'], 'color': colors['text'], 'height':'100vh', 'width':'100%', 'height':'100%', 'top':'0px', 'left':'0px'}, 
	children=[
		html.H1(children='Nearby - The app that helps you discover places of interest near you.'),
		html.H3(children="Please input the GPS coordinates (i.e., latitude and longitude), radius of search (in metres), location type and keyword (option) to search for interesting places nearby. If you don't know the GPS coordinates, please enter the name of the location, and we'll help you find it.", style={'height':'8vh'}),
		html.Div([
			dcc.Input(id='input_loc_name', placeholder='Enter location name (like, Mountain View, CA)', type='text', style={'width': '20%', 'display': 'inline-block'}),
			html.Button('Submit', id='submit_loc_name'),
			html.H6(id='coordinates_display', style={'height':'6vh', 'font-size':'1.15em'}),
		]),
		html.H4(children="Some examples of location types are airport, bank, restaurant, hospital, etc. You can choose to fine tune the search by entering the optional keyword parameter. For example, if you want to search for Thai restaurants, you can enter 'restaurant' in location type and 'Thai' in keyword. If you don't provide any keyword, you will get results of all restaurants. A maximum of 20 places will be displayed. Therefore, although techinically you can give a high radius of search, a more reasonable search radius (typically around 500-2500 metres) is advised to get more meaningful results.", style={'font-size':'1.15em'}),
		html.Div([
			dcc.Input(id='input_lat', placeholder='Enter a latitude', type='text', style={'width': '10%', 'display': 'inline-block'}),
			dcc.Input(id='input_lon', placeholder='Enter a longitude', type='text', style={'width': '10%', 'display': 'inline-block'}),
			dcc.Input(id='input_radius', placeholder='Enter radius (in metres)', type='text', style={'width': '10%', 'display': 'inline-block'}),
			dcc.Input(id='input_type', placeholder='Enter type of location', type='text', style={'width': '10%', 'display': 'inline-block'}),
			dcc.Input(id='input_key', placeholder='Enter keyword (optional)', type='text', style={'width': '10%', 'display': 'inline-block'}),
		]),
		html.Button('Submit', id='submit_button'),
		html.Div([
			html.H3(id='output_text', style={'color': colors['text'], 'backgroundColor': colors['background']}),
			html.Div([
				html.Div([dcc.Graph(id='output_graph',figure=blank_fig, 
				            		style={'color': colors['text'], 'backgroundColor': colors['background'], 'display': 'inline-block'})
			    ]),
				html.H4(children="As we all know, the Wuhan coronavirus is spreading to many places across the world. So, for people looking to travel to a city, its imperative to get a qualitative assessment of how safe it is to travel to that city. With the ubiquity of Twitter, a reasonable proxy of knowing if the virus has infected anyone in any location is to check coronovirus related tweets tagging the location. Below are the latest tweets (max 20 displayed) and their average positive and negative sentiments about coronavirus in the City in which the inputted location is present. If no coronovirus related tweets are found with the city's name tagged, then its reasonable to assume that its probably safe to travel to that city. In that case, coronavirus related tweets from the country of the inputted location are displayed. If no coronovirus related tweets are found even with the country's name in the tweet, then the latest tweets (max 20) among all coronavirus related tweets are displayed."),
				dcc.Graph(id='sentiment_pie', figure=blank_fig, animate=False,
						  style={'backgroundColor': colors['background'], 'width': '50%', 'display': 'inline-block'}),
				html.Div(id='recent-tweets-table', style={'color': colors['text'], 'width': '100%'})
			])
		])
	])

google_API_key = "AIzaSyCM0ZcGcuQsIQIhaBDIHaTeK-RUc9Y7hpo"
mapbox_access_token = 'pk.eyJ1Ijoia3Jpc3RhZGE2NzMiLCJhIjoiY2syZmpkdzU5MGtyMzNjcDA5NHhoNTRobiJ9.0UfXv_kWgfcerji8znePxA'

def geocoder(lat, lon, radius, loc_type, keyword, API_key=google_API_key):
	if keyword:
		req = requests.get("https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=" + str(lat) + "," + str(lon) + "&radius=" + str(radius)+"&type=" + loc_type + "&keyword=" + keyword + "&key=" + API_key)
	else:
		req = requests.get("https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=" + str(lat) + "," + str(lon) + "&radius=" + str(radius)+"&type=" + loc_type + "&key=" + API_key)
	return  json.loads(req.text)

def return_lat_lon_city_country(location_name):
	req = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address='+location_name+'&key='+google_API_key)
	res = req.json()
	result = res['results'][0]
	lat = result['geometry']['location']['lat']
	lon = result['geometry']['location']['lng']
	city = ''
	country = ''
	for i in range(len(res['results'][0]['address_components'])):
	    if res['results'][0]['address_components'][i]['types'][0]=='administrative_area_level_2':
	        city = res['results'][0]['address_components'][i]['long_name']

	for i in range(len(res['results'][0]['address_components'])):
	    if res['results'][0]['address_components'][i]['types'][0]=='country':
	        country = res['results'][0]['address_components'][i]['long_name']
	        	        
	return lat, lon, city, country

def generate_table(dataframe, max_rows=21):
	return html.Table(
		# Header
		[html.Tr([html.Th(col) for col in dataframe.columns])] +

		# Body
		[html.Tr([
			html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
		]) for i in range(min(len(dataframe), max_rows))]
	)

@app.callback(
	[Output('coordinates_display', 'children'),
	Output('input_lat', 'value'),
	Output('input_lon', 'value')],
	[Input('submit_loc_name', 'n_clicks')],
	[State('input_loc_name', 'value')])
def display_gps_coordinatates(n_clicks, input_loc_name):
	if n_clicks:
		if input_loc_name:
			lat, lon, _, _ = return_lat_lon_city_country(input_loc_name)
			output_str = "The GPS coordinates (latitude, longitude) of '{}' are: {}, {}".format(input_loc_name, lat, lon)
			return output_str,lat,lon
	else:
		return dash.no_update, dash.no_update, dash.no_update

@app.callback(
	[Output('output_text', 'children'),
	Output('output_graph', 'figure'),
	Output('sentiment_pie', 'figure'),
	Output('recent-tweets-table', 'children')],
	[Input('submit_button', 'n_clicks')],
	[State('input_lat', 'value'),
	State('input_lon', 'value'),
	State('input_radius', 'value'),
	State('input_type', 'value'),
	State('input_key', 'value')])
def update_output(n_clicks, lat_, lon_, radius, loc_type, keyword):
	if n_clicks:					 
		try:
			assert float(lat_)>=-90 and float(lat_)<=90
		except:
			return "Please enter a numeric value for Latitude between -90 and 90.", {}, {}, []
		try:
			assert float(lon_)>=-180 and float(lon_)<=180
		except:
			return "Please enter a numeric value for Longitude between -180 and 180.", {}, {}, []
		try:
			assert float(radius)>=0 and float(radius)<=10000000
		except:
			return "Please enter a numeric value for radius (under 1 million).", {}, {}, []
		try:
			assert isinstance(loc_type, str)
		except:
			return "Please enter a string value for Location Type.", {}, {}, []

		res = geocoder(lat_, lon_, radius, loc_type, keyword, google_API_key)

		# Output the text line
		if keyword:
			assert isinstance(loc_type, str), "Please enter a string value for Keyword."
			t = "There are a total of {} {} {}s within a radius of {}m of latitude {} and longitude {}. You can hover over the locations to find additional information about them. You can also zoom in or out of the map by pinching in or out, respectively.".format(len(res['results']), str(keyword).title(), ' '.join(loc_type.split('_')).title(), str(radius), lat_, lon_)
		else:
			t = "There are a total of {} {}s within a radius of {}m of latitude {} and longitude {}. You can hover over the locations to find additional information about them. You can also zoom in or out of the map by pinching in or out, respectively.".format(len(res['results']), ' '.join(loc_type.split('_')).title(), str(radius), lat_, lon_)

		# Output the map
		lat = []
		lon = []
		name = []
		price_level = []
		rating = []
		num_ratings = []
		landmark = []
		open_hours = []

		for i in range(len(res['results'])):
			lat.append(res['results'][i]['geometry']['location']['lat'])
			lon.append(res['results'][i]['geometry']['location']['lng'])
			name.append(res['results'][i]['name'])
			try:
				price_level.append(res['results'][i]['price_level'])
			except:
				price_level.append('N/A')
			try:
				rating.append(res['results'][i]['rating'])
			except:
				rating.append('N/A')
			try:
				num_ratings.append(res['results'][i]['user_ratings_total'])
			except:
				num_ratings.append('N/A')
			try:
				landmark.append(res['results'][i]['vicinity'])
			except:
				landmark.append('N/A')
			try:
				if res['results'][i]['opening_hours']:
					open_hours.append('Yes')
				else:
					open_hours.append('Closed')
			except:
				open_hours.append('N/A')
				
		df = pd.DataFrame({'Name':name, 'Lat':lat, 'Lon':lon, 'Price Level':price_level, 'Avg. Rating':rating, 
						   'No. of Ratings':num_ratings, 'Landmark':landmark, 'Open':open_hours})

		df['text'] = 'Name: ' + df['Name'] + '<br>' + 'Price Level: ' + df['Price Level'].astype(str) + '<br>' + 'Avg. Rating: ' + df['Avg. Rating'].astype(str) + '<br>' + 'No. of Ratings: ' + df['No. of Ratings'].astype(str) + '<br>' + 'Open Now: ' + df['Open']

		datamap = go.Data([])
		datamap.append(go.Scattermapbox(
							lat=df['Lat'],
							lon=df['Lon'],
							mode='markers',
							marker=go.scattermapbox.Marker(
								size=25,
								opacity=0.7,
								color='rgb(255, 0, 0)'
							),
							text=df['text'],
							name='',
							showlegend=True
						)
					)
		datamap.append(go.Scattermapbox(
							lat=[float(lat_)],
							lon=[float(lon_)],
							mode='markers',
							marker=go.scattermapbox.Marker(
								size=25,
								opacity=1,
								color='rgb(0, 0, 255)',
								symbol='star'
							),
							text='Origin',
							name='',
							showlegend=True
						)
					)
		layoutmap = go.Layout(
			margin ={'t':50},
			autosize=True,
			hovermode='closest',
			width=700, 
			height=700,
			showlegend=False,
			paper_bgcolor='rgba(0,0,0,0)',
			mapbox=go.layout.Mapbox(
				accesstoken=mapbox_access_token,
				bearing=0,
				center=go.layout.mapbox.Center(
					lat=float(lat_),
					lon=float(lon_)
				),
				style="streets", # basic, streets, outdoors, light, dark, satellite, satellite-streets
				pitch=0,
				zoom=13,
			),
		)

		fig = dict( data=datamap, layout=layoutmap )

		

		# Output the sentiments pie chart
		try:
			conn = sqlite3.connect('twitter.db')
			c = conn.cursor()
				
			_, _, city, country = return_lat_lon_city_country(res['results'][0]['vicinity'])

			df = pd.read_sql("SELECT * FROM sentiment WHERE tweet LIKE '%coronavirus%' AND tweet LIKE ? ORDER BY unix DESC LIMIT 100", conn, params=('%'+format(city)+'%',))

			if len(df)==0: # if coronavirus related news with the City name taaged are not present
				df = pd.read_sql("SELECT * FROM sentiment WHERE tweet LIKE '%coronavirus%' AND tweet LIKE ? ORDER BY unix DESC LIMIT 100", conn, params=('%'+format(country)+'%',))
				if len(df)==0: # if coronavirus related news with the Country name taaged are not present
					df = pd.read_sql("SELECT * FROM sentiment WHERE tweet LIKE '%coronavirus%' ORDER BY unix DESC LIMIT 100", conn)

			df.sort_values('unix', inplace=True)
			df['sentiment_smoothed'] = df['sentiment'].rolling(int(len(df)/2)).mean()

			df['date'] = pd.to_datetime(df['unix'],unit='ms')
			df.set_index('date', inplace=True)
			df.dropna(inplace=True)
			X = df.index
			Y = df.sentiment_smoothed

			threshold = min(Y)+(max(Y)-min(Y))/2
			pos = Y[Y>=threshold]
			neg = Y[Y<threshold]
			color = ['#DC143C', '#1E90FF']
			trace = go.Pie(labels=['Positive', 'Negative'], values=[len(pos), len(neg)],
						   hoverinfo='label+percent', textinfo='value', 
						   textfont=dict(size=20),
						   marker=dict(colors=color, line=dict(color='#FFFFFF', width=2)))

			if city!='':
				sent_out = {'data':[trace],
									'layout': {
										'title':'Sentiment pie chart of Coronovirus related tweets with {} in the tweet'.format(city),
										'plot_bgcolor': colors['background'],
										'paper_bgcolor': colors['background'],
										'font': {'color': colors['text']}
									}
							}
			elif city=='' and country!='':
				sent_out = {'data':[trace],
									'layout': {
										'title':'Sentiment pie chart of Coronovirus related tweets with {} in the tweet'.format(country),
										'plot_bgcolor': colors['background'],
										'paper_bgcolor': colors['background'],
										'font': {'color': colors['text']}
									}
							}
			elif city=='' and country=='':
				sent_out = {'data':[trace],
									'layout': {
										'title':'Sentiment pie chart of Coronovirus related tweets in general.',
										'plot_bgcolor': colors['background'],
										'paper_bgcolor': colors['background'],
										'font': {'color': colors['text']}
									}
							}

		except Exception as e:
			with open('errors.txt','a') as f:
				f.write(str(e))
				f.write('\n')

		# Output the Tweets table
		df.columns = ['Date', 'Tweet', 'Sentiment', 'Sentiment Smoothed']
		df = df[['Date', 'Tweet', 'Sentiment']]
		df['Date'] = pd.to_datetime(df['Date'],unit='ms').apply(lambda x: x.replace(microsecond=0))
		df['Time'] = [d.time() for d in df['Date']]
		df['Date'] = [d.date() for d in df['Date']]
		df = df[['Date', 'Time', 'Tweet', 'Sentiment']]

		return t, go.Figure(fig), sent_out, generate_table(df)

	else:
  		return dash.no_update, dash.no_update, dash.no_update, dash.no_update
		
if __name__ == '__main__':
	app.run_server(debug=True)
