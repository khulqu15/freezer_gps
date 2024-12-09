from datetime import datetime, timedelta
import random
import json

# Define the base timestamp and interval
base_timestamp = datetime.strptime("28/11/2024 00:00", "%d/%m/%Y %H:%M")
interval = timedelta(minutes=5)

# Generate realistic dummy data
realistic_dummy_data = {}

for i in range(100):
    current_timestamp = base_timestamp + i * interval
    load_cell = random.randint(50, 300)  # Bird food weight in grams
    water_level = random.randint(5, 20)  # Water level in cm

    data_point = {
        "load_cell": load_cell,
        "timestamp": current_timestamp.strftime("%d/%m/%Y %H:%M"),
        "water_level": water_level
    }
    realistic_dummy_data[f"-OADnbhEf{i:05d}"] = data_point

# Display the generated data
formatted_realistic_data = json.dumps(realistic_dummy_data, indent=2)
print(formatted_realistic_data)
