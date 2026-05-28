import os
import json
os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 pyspark-shell'

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

# Create Spark Session
spark = SparkSession.builder \
    .appName("KTX Food Real-time Analytics") \
    .master("local[*]") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

# Define schema matching app.py STANDARD_COLUMNS JSON payload
schema = StructType([
    StructField("store_name", StringType()),
    StructField("uid", StringType()),
    StructField("thoi_gian", StringType()),
    StructField("mon_an", StringType()),
    StructField("so_luong", IntegerType()),
    StructField("don_gia", IntegerType()),
    StructField("doanh_thu", IntegerType()),
    StructField("dia_chi", StringType()),
    StructField("sdt", StringType()),
    StructField("ghi_chu", StringType()),
    StructField("raw_comment", StringType())
])

# Read from Kafka topic 'shipped_orders_stream'
df_raw = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "shipped_orders_stream") \
    .option("startingOffsets", "earliest") \
    .load()

# Convert Kafka binary -> string -> parse JSON -> extract data
df_json = df_raw.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")) \
    .select("data.*")

# Analytics: total revenue and orders per store
revenue_df = df_json.groupBy("store_name").agg(
    sum("doanh_thu").alias("total_revenue"),
    count("*").alias("total_orders")
)

# Thư mục và file lưu kết quả
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
SUMMARY_FILE = os.path.join(OUTPUT_DIR, "spark_summary.json")

def process_batch(df, epoch_id):
    """
    Hàm này sẽ được gọi mỗi khi có dữ liệu stream mới (batch).
    Nó sẽ chuyển đổi Dataframe của Spark thành Pandas và lưu vào file JSON
    để Streamlit (app.py) đọc được lập tức.
    """
    try:
        # Lấy dataframe aggregate hiện tại
        pdf = df.toPandas()
        
        # Nếu có dữ liệu, ghi đè file spark_summary.json
        if not pdf.empty:
            records = pdf.to_dict(orient="records")
            with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=4)
            print(f"[{epoch_id}] Đã cập nhật spark_summary.json: {len(records)} chi nhánh.")
        else:
            print(f"[{epoch_id}] Chưa có dữ liệu giao hàng mới.")
            
    except Exception as e:
        print(f"Lỗi khi lưu batch {epoch_id}: {e}")

print("⏳ PySpark đang chờ dữ liệu đơn hàng ĐÃ GIAO từ Streamlit...")

# Output to console AND file via foreachBatch
query = revenue_df.writeStream \
    .outputMode("complete") \
    .foreachBatch(process_batch) \
    .start()

query.awaitTermination()