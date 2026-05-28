import json
import time
from kafka import KafkaProducer

def main():
    producer = KafkaProducer(
        bootstrap_servers="localhost:9092",
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8")
    )
    
    print("🚀 Bắt đầu stream dữ liệu Facebook Comment vào Kafka...")
    
    with open("data/facebook_comments.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            # Đẩy nguyên dòng text thô vào Kafka
            payload = {"raw_comment": line}
            producer.send("facebook_orders_stream", payload)
            producer.flush()
            
            print(f"Đã gửi: {line}")
            time.sleep(2) # Giả lập 2 giây có 1 comment mới

if __name__ == "__main__":
    main()