from kafka import KafkaProducer
import json
import random
import time
from datetime import datetime

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

stores = [
    {
        "store_id": "KTX_A",
        "store_name": "KTX Khu A"
    },
    {
        "store_id": "KTX_B",
        "store_name": "KTX Khu B"
    },
    {
        "store_id": "KTX_C",
        "store_name": "KTX Khu C"
    }
]

foods = [
    ("Com ga", 35000),
    ("Com suon", 40000),
    ("Bun bo", 45000),
    ("Pho bo", 50000),
    ("Mi xao", 30000),
    ("Hu tieu", 32000),
]

customers = [
    "An",
    "Binh",
    "Cuong",
    "Dung",
    "Huy",
    "Khanh",
    "Linh",
    "Minh",
    "Trang"
]

sentiments = [
    "positive",
    "neutral",
    "negative"
]

print("Streaming fake realtime data to Kafka...")

while True:

    store = random.choice(stores)

    food_name, food_price = random.choice(foods)

    quantity = random.randint(1, 5)

    data = {
        "store_id": store["store_id"],
        "store_name": store["store_name"],
        "customer": random.choice(customers),
        "item": food_name,
        "quantity": quantity,
        "price": food_price,
        "total_amount": quantity * food_price,
        "sentiment": random.choice(sentiments),
        "timestamp": datetime.now().isoformat()
    }

    producer.send("fb_comments", value=data)

    print(f"Sent: {data}")

    time.sleep(random.uniform(1, 3))