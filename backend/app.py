from flask import Flask  , jsonify ,request 
import requests 
from flask_cors import CORS
from flaskext.mysql import MySQL
import pymysql
from flask_bcrypt import Bcrypt 

#database configuuration
mysql =MySQL()
app = Flask(__name__, template_folder='templates')

app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_DB'] = 'weatherTime'
app.config['MYSQL_DATABASE_PASSWORD'] = '******'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)
#feedback submission
@app.route('/feedback', methods=['POST'])
def insert_feedback():
  try:
    data = request.json
    feedback_text = data.get('feedback_text')
    time=data.get('time')
    date=data.get('date')
    email = data.get("email")   
    connection = mysql.connect()
    cursor = connection.cursor()
    query_user = "SELECT user_id FROM users WHERE email = %s"
    cursor.execute(query_user, (email,))
    user_id = cursor.fetchone()[0]
    query = "INSERT INTO feedback (user_id, feedback_text,feedback_time,feedback_date) VALUES (%s, %s,%s, %s)"
    cursor.execute(query, (user_id, feedback_text,time,date))
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({'message': 'Feedback submitted successfully', 'status': 'success'}), 200
  except Exception as e:
        print("Error:", e)
        return jsonify({'message': 'An error occurred', 'status': 'error', 'error': str(e)}), 500    
API_KEY = ''

CORS(app)



# a function to transform the temperature from kelvin to Celsus
def minus(x):
    return round(x - 273.15)

# get weather data from open weather api 
@app.route('/weather', methods=['GET'])
def get_weather():
    city = request.args.get('city')
    if not city:
        return jsonify({'error': 'City parameter is required'}), 400

    url = f'https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}'
    response = requests.get(url)
    print(url)
    if response.status_code == 200:
        data = response.json()
        forecast_data = []
        for item in data['list']:
            forecast_entry = {
            'datetime': item['dt_txt'],
            'temperature': minus(item['main']['temp']),
            'description': item['weather'][0]['description'],
            'humidity': item['main']['humidity'],
            'wind_speed': item['wind']['speed']
            }
            forecast_data.append(forecast_entry)
        return jsonify({
        'city': data['city']['name'],
        'country': data['city']['country'],
        'forecast': forecast_data  # List of forecast entries
        })
    else:
        return jsonify({'error': 'Failed to get weather data. Check city name or try again later.'}), 400


#a function used to generate hashed passwords
bcrypt = Bcrypt(app) 
def hashing(password):
    hashed_password = bcrypt.generate_password_hash (password).decode('utf-8')
    return hashed_password

#a function to return if an account exist or not by connecting to the database by fetching the entered email
def account(email): 
            conn = mysql.connect()
            cur = conn.cursor(pymysql.cursors.DictCursor) #request many requests in the same time 
            cur.execute(" SELECT * FROM users WHERE email = %s ",(email,)) 
            accounts = cur.fetchone()
            return(accounts)
#print(account_data)  



#a route used to make sign up of user based on username  , email , password chosen
@app.route('/signup',methods=['POST'])
def signup():
     data=request.json
     username=data.get('username')
     email=data.get('email')
     password=data.get('password')
     if account(email):
        return jsonify({'message': 'Email already used . Please enter another email', 'status': 'fail'}), 400
     else :
        password_hash=hashing(password)
        connection = mysql.connect()
        cursor = connection.cursor()
        query = "INSERT INTO users (email,username,password_hash) VALUES (%s, %s,%s)"
        cursor.execute(query, (email,username,password_hash))
        connection.commit()
        cursor.close()
        connection.close()
        return jsonify({'message': 'User registered successfully', 'status': 'success'})
         
 
# a route used to log in the user based on the email and password 
@app.route('/login',methods=["POST"])
def login():
    data=request.json
    email=data.get("email")
    data_password=data.get("password")
    if account(email):
        account_entered=account(email)
        if bcrypt.check_password_hash(account_entered["password_hash"],data_password):
                return jsonify({"message": "Login successful", "status": "success"}), 200
        else :
            return jsonify({"message": "Invalid email or password", "status": "fail"}), 401
    else :
         return ("account not found")


# a route used to get the facts stored in the database and return them in a json file
@app.route('/facts',methods=["GET"])
def facts():
    connection = mysql.connect()
    cursor = connection.cursor()
    query = "SELECT category, title, description FROM weather_facts"
    cursor.execute(query)
    facts = cursor.fetchall()
    facts_data = [{'category': row[0], 'title': row[1], 'description': row[2]} for row in facts]

    return jsonify(facts_data)
    


   
if __name__ == '__main__':
    app.run(debug=True)



