import os
import requests

# Create images directory if it doesn't exist
os.makedirs('static/images', exist_ok=True)

# Download male profile images
for i in range(1, 7):
    url = f"https://randomuser.me/api/portraits/men/{i+10}.jpg"
    response = requests.get(url)
    with open(f"static/images/m{i}.jpg", 'wb') as f:
        f.write(response.content)
    print(f"Downloaded m{i}.jpg")

# Download female profile images
for i in range(1, 7):
    url = f"https://randomuser.me/api/portraits/women/{i+10}.jpg"
    response = requests.get(url)
    with open(f"static/images/f{i}.jpg", 'wb') as f:
        f.write(response.content)
    print(f"Downloaded f{i}.jpg")

print("All images downloaded successfully!")
