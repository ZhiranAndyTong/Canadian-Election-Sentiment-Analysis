# -*- coding: utf-8 -*-
"""Untitled1.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1JJaE0nHGHzBiYUsEMOS-I1VLvTobB7BC
"""

import sys
assert sys.version_info >= (3, 5) # Make sure we have Python 3.5+
from pyspark.sql import functions, types, Row
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, count

def aggregate_sentiment_data(input_path, output_path):
    # Initialize Spark session
    spark = SparkSession.builder.appName("SentimentAnalysisAggregation").getOrCreate()

    # Read the data from parquet files
    df = spark.read.parquet(input_path)

    # Group by the specified fields
    grouped_df = df.groupBy(
        'subreddit', 'year', 'month', 'label', 'sentiment', 'emotion', 'hate_speech'
    ).agg(
        # Aggregate sentiment_score (average), count of comments, and average srage score
        avg('sentiment_score').alias('average_sentiment_score'),
        count('sentiment').alias('comment_count'),  # You can replace 'sentiment' with another column if needed
        avg('score').alias('average_score')
    )

    # Write the result to CSV
    grouped_df.write.csv(output_path, header=True)


if __name__ == "__main__":
    input_path = sys.argv[1]  # Replace with actual input path
    output_path = sys.argv[2]   # Replace with actual output path
    aggregate_sentiment_data(input_path, output_path)