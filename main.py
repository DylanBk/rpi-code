import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
from sense_hat import SenseHat
from time import sleep
from twilio.rest import Client


sense = SenseHat()
sense.color.gain = 64
sense.color.integration_cycles = 64

load_dotenv()
supabase_url = os.environ.get("DATABASE_URL")
supabase_key = os.environ.get("DATABASE_KEY")

supabase = create_client(supabase_url, supabase_key)


# def init_sensor():
#     data = supabase.table("sensors").insert({}).execute()

def get_sensor_data(id):
    data = supabase.table("sensors").select("*").eq("id", id).execute()
    sensor_data = data.data[0]

    return sensor_data

def get_user_data(user_id):
    phone_num = supabase.table("users").select("phone_number").eq("id", user_id).execute()

    return user_id, phone_num.data[0]['phone_number']

def get_plant_data(plant_id):
    data = supabase.table("plant_data").select("*").eq("id", plant_id).execute()
    plant_data = {
        'plant_id': data.data[0]['id'],
        'name': data.data[0]['name'],
        'temp': data.data[0]['Temperature'],
        'hum': data.data[0]['Humidity']
    }

    return plant_data

def update_sensor_data(id, temp, hum, light, plant_id, user_id):
    supabase.table("sensors").upsert({
        "id": id,
        "temperature": temp,
        "humidity": hum,
        "light": light,
        "plant_id": plant_id,
        "user_id": user_id
    }).execute()

def set_rules(plant_data):
    temp = plant_data['temp']
    hum = plant_data['hum']

    temp_min = temp - 3
    temp_max = temp + 3

    hum_min = hum - (hum / 100 * 10)
    hum_max = hum + (hum / 100 * 10)

    temp_rules = [temp_min, temp, temp_max]
    hum_rules = [hum_min, hum, hum_max]

    return temp_rules, hum_rules

def monitor_plant():
    temp = sense.get_temperature()
    hum = sense.get_humidity()
    r, g, b, clear = sense.colour.colour
    light = clear

    return temp, hum, light

def draw_data(temp, hum, temp_rules, hum_rules): # define colour for text and icons based on params
    if temp < temp_rules[0]:
        temp_colour = (0, 0, 255) # blue
    elif temp < temp_rules[1]:
        temp_colour = (173, 216, 230) # lightblue
    elif temp == temp_rules[1]:
        temp_colour = (0, 255, 0) # green        
    elif temp < temp_rules[2]:
        temp_colour = (255, 255, 0) # yellow
    else:
        temp_colour = (255, 0, 0) # red

    if hum < hum_rules[0]:
        hum_colour = (255, 0, 0)  # Red
    elif hum < hum_rules[1]:
        hum_colour = (255, 255, 0)  # Yellow
    elif hum == hum_rules[1]:
        hum_colour = (0, 255, 0)  # Green
    elif hum < hum_rules[2]:
        hum_colour = (173, 216, 230)  # Light Blue
    else:
        hum_colour = (0, 0, 255)  # Blue

    sense.show_message(f"{str(round(temp, 1))}C", scroll_speed=0.1, text_colour=temp_colour) # outputs temperature rounded to 1 dec pts on LED grid
    sense.show_message(f"{str(round(hum, 1))}%", scroll_speed=0.1, text_colour=hum_colour) # outsputs humidity rounded to 1 dec pts on LED grid

def draw_icon(icon):
    black = (0, 0, 0)

    match icon:
        case "moon":
            white = (255, 255, 255)
            pattern = [
                black, white, white, white, black, black, black, black,
                black, black, white, white, white, black, black, black,
                black, black, black, white, white, white, black, black,
                black, black, black, white, white, white, black, black,
                black, black, black, white, white, white, black, black,
                black, black, black, white, white, white, black, black,
                black, black, white, white, white, black, black, black,
                black, white, white, white, black, black, black, black,
            ]

            sense.set_pixels(pattern)
        case "sun":
            yellow = (255, 255, 0)
            pattern = [
                black, black, yellow, yellow, yellow, yellow, black, black,
                black, yellow, yellow, yellow, yellow, yellow, yellow, black,
                yellow, yellow, yellow, yellow, yellow, yellow, yellow, yellow,
                yellow, yellow, yellow, yellow, yellow, yellow, yellow, yellow,
                yellow, yellow, yellow, yellow, yellow, yellow, yellow, yellow,
                yellow, yellow, yellow, yellow, yellow, yellow, yellow, yellow,
                black, yellow, yellow, yellow, yellow, yellow, yellow, black,
                black, black, yellow, yellow, yellow, yellow, black, black,
            ]

            sense.set_pixels(pattern)

def send_alert(phone_num, alert_type, plant_name):
    match alert_type:
       # case "High Temperature":
           # message_body = f"The temperature is too high for the {plant_name}."
        case "Low Temperature":
            message_body = f"The temperature is too low for the {plant_name}."
        case "Sensor Blocked":
            message_body = f"The sensor for the cabbage is blocked."

#     time = datetime.now().strftime("%H:%M:%S")

# #     if time >= "07:00:00" or time <= "18:00:00": # check if appropriate time to send alert
    try:
        

        client = Client(account_sid, auth_token)

        message = client.messages.create(
              # Your Twilio sandbox WhatsApp number
            body=message_body
        )
    except Exception as e:
        print(f"Error sending alert message: {e}")

    # Print the SID of each sent message to confirm
    print(f'Message sent to {phone_num} from {message.account_sid}, body = {message.body}')


# monitor data every 60 seconds
def main(sensor_id):
    phone_num = "whatsapp:+447484872459"
    user_id = 1
    while True:
        sense.clear()
        sensor_data = get_sensor_data(sensor_id)

#         user_id, phone_num = get_user_data(1)

        plant_id = sensor_data['plant_id']
        plant_data = get_plant_data(plant_id)

        temp_rules, hum_rules = set_rules(plant_data)
        temp, hum, light = monitor_plant()

        update_sensor_data(sensor_id, temp, hum, light, plant_id, 1)

#         time = datetime.now().strftime("%H:%M:%S")

        if light < 50:
            print("something blocking sensor")
            draw_icon("moon")
            send_alert(phone_num, "Sensor Blocked", plant_data['name'])
        else:
            draw_icon("sun")
        sleep(3)
#         if light < 85 and time > "07:00:00" and time < "19:00:00": # send alert if its dark during daylight hours
#             send_alert(phone_num, "Light Sensor", f"Something is blocking the light sensor")
#             print("something blocking sensor")

        if temp < temp_rules[0]:
            print("cold")
            send_alert(phone_num, "Low Temperature", plant_data['name'])
#         elif temp > temp_rules[2]:
#             print("hot")
#             send_alert(phone_num, "High Temperature", plant_data['name'])

        sense.set_rotation(180) # can be removed/changed, depends how we align the pi
        draw_data(temp, hum, temp_rules, hum_rules)

        sleep(10)

if __name__ == "__main__":
    sensor_id = 1
    main(sensor_id)