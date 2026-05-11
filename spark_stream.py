from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

# Create Spark Session
spark = SparkSession.builder \
    .appName("KTX Food Streaming Analytics") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

# Schema for Kafka JSON data
schema = StructType([
    StructField("store_id", StringType()),
    StructField("store_name", StringType()),
    StructField("customer", StringType()),
    StructField("item", StringType()),
    StructField("quantity", IntegerType()),
    StructField("price", IntegerType()),
    StructField("total_amount", IntegerType()),
    StructField("sentiment", StringType()),
    StructField("timestamp", StringType())
])

# Read stream from Kafka
df_raw = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "fb_comments") \
    .load()

# Convert Kafka binary -> string
df_string = df_raw.selectExpr("CAST(value AS STRING)")

# Parse JSON
df_json = df_string.select(
    from_json(col("value"), schema).alias("data")
)

# Flatten data
df = df_json.select("data.*")

# Analytics: revenue per store
revenue_df = df.groupBy("store_name").agg(
    sum("total_amount").alias("total_revenue"),
    count("*").alias("total_orders")
)

# Output to console
query = revenue_df.writeStream \
    .outputMode("complete") \
    .format("console") \
    .option("truncate", False) \
    .start()

query.awaitTermination()