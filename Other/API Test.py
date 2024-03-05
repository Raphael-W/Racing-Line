import requests, json

# api-endpoint
URL = "https://api.auto-data.net/?code=ab0535f73cf5d3fcd5e06732c7d70e7e"

dataFormat = "json"
PARAMS = {"format":dataFormat}

r = requests.get(url = URL, params = PARAMS)

# extracting data in json format
data = r.json()
brands_data = data["brands"]["brand"]

# Iterate through the brands data and print the brand name and its associated models
for brand_data in brands_data:
    brand_name = brand_data["name"]
    models_data = brand_data["models"]["model"]
    for model_data in models_data:
        model_name = model_data["name"]
        generations_data = model_data["generations"]["generation"]
        for generation_data in generations_data:
            acceleration = "N/A"
            braking = "N/A"
            wheel_base = "N/A"
            turning_radius = "N/A"
            top_speed = "N/A"
            modifications_data = generation_data.get("modifications", {}).get("modification", [])
            for modification_data in modifications_data:
                acceleration = modification_data.get("acceleration", "N/A")
                braking = modification_data.get("deceleration", "N/A")
                wheel_base = modification_data.get("wheelbase", "N/A")
                turning_radius = modification_data.get("turningCircle", "N/A")
                top_speed = modification_data.get("maxspeed", "N/A")
            
            # Print details for each model
            print(f"{brand_name} {model_name}:")
            print(f"Acceleration: {acceleration}")
            print(f"Braking: {braking}")
            print(f"Wheel Base: {wheel_base}")
            print(f"Turning Radius: {turning_radius}")
            print(f"Top Speed: {top_speed}\n{'-' * 40}")

#For my program, I'll need to be able to save a file for each vehicle
def saveData():
    for brand_data in brands_data:
        brand_name = brand_data["name"]
        models_data = brand_data["models"]["model"]
        for model_data in models_data:
            model_name = model_data["name"]
            generations_data = model_data["generations"]["generation"]
            for generation_data in generations_data:
                acceleration = "N/A"
                braking = "N/A"
                wheel_base = "N/A"
                turning_radius = "N/A"
                top_speed = "N/A"
                modifications_data = generation_data.get("modifications", {}).get("modification", [])
                for modification_data in modifications_data:
                    acceleration = modification_data.get("acceleration", "N/A")
                    braking = modification_data.get("deceleration", "N/A")
                    wheel_base = modification_data.get("wheelbase", "N/A")
                    turning_radius = modification_data.get("turningCircle", "N/A")
                    top_speed = modification_data.get("maxspeed", "N/A")

                carData = {"Brand": brand_name,
                        "Model": model_name,
                        "Top Speed": top_speed,
                        "Acceleration": acceleration,
                        "Braking": braking,
                        "Wheel-Base": wheel_base,
                        "Turning Radius": turning_radius}

                with open("Car Data/" + brand_name + " " + model_name + ".json", "w") as carFile:
                    json.dump(carData, carFile)
saveData()
