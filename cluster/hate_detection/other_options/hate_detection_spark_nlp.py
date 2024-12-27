'''
This script detects whether hate speech is present in the comments or not using a spark nlp pretrained model(roberta_classifier_hate_speech_dynabench_r4_target). 

possible outcomes:
hate, nothate

To locally run the script use the command:
spark-submit --packages com.johnsnowlabs.nlp:spark-nlp_2.12:5.5.1 hate_detection_spark_nlp.py input-parquet-path output-parquet-path
'''


import sys
assert sys.version_info >= (3, 5) # Make sure we have Python 3.5+
from pyspark.sql import SparkSession, functions, types, Row 
import sparknlp
from sparknlp.base import *
from sparknlp.annotator import *
from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.sql.functions import col

# Constants
MAX_SEQ_LENGTH = 128        # maximum sequence length for the pretrained model 
COMMENT_TXT_FIELD = 'body' 
PARTY_LABEL_FIELD = 'label'
PARTY_LABELS = ['conservative', 'liberal']
HATE_SPEECH_LABEL_FIELD = 'hate_speech'
PARTITION_BY_FIELDS = ['subreddit','year','month','day']


def main(input, output):
    # Read data from files
    comments_df = spark.read.parquet(input)

    # Convert the text column of the dataframe into the acceptable input for the model 
    doc_assembler = DocumentAssembler() \
    .setInputCol('truncated_comment') \
    .setOutputCol('document')

    tokenizer = Tokenizer() \
        .setInputCols('document') \
        .setOutputCol('token')

    emotion_classifier = RoBertaForSequenceClassification.pretrained("roberta_classifier_hate_speech_dynabench_r4_target","en") \
        .setInputCols(['document', 'token']) \
        .setOutputCol('class')
    
    # Build the pipeline from all the stages
    pipeline = Pipeline().setStages([doc_assembler, tokenizer, emotion_classifier])

    # Fit and transform the data
    comments_df = comments_df.withColumn(
        'truncated_comment', 
        functions.substring(comments_df[COMMENT_TXT_FIELD], 0, MAX_SEQ_LENGTH)
    )
    model = pipeline.fit(comments_df)
    classified_df = model.transform(comments_df)

    # Keep the prevalent emotion and discard rest
    result_df = classified_df \
        .withColumn(HATE_SPEECH_LABEL_FIELD, classified_df['class.result'].getItem(0)) \
        .drop('document', 'token', 'class', 'truncated_comment')

    # Write the result to a Parquet file
    result_df.write\
        .partitionBy(PARTITION_BY_FIELDS)\
        .parquet(output, mode='overwrite')


if __name__ == '__main__':
    # Reading the  command line arguments
    input = sys.argv[1] 
    output = sys.argv[2]        

    # Initializing sparksession with necessary packages (Alternatively use spark = sparknlp.start())
    spark = SparkSession.Builder() \
        .appName('Hate Speech Detection Spark NLP') \
        .config('spark.jars.packages', 'com.johnsnowlabs.nlp:spark-nlp_2.12:5.5.1') \
        .getOrCreate()
    assert spark.version >= '3.0' # Make sure we have Spark 3.0+
    spark.sparkContext.setLogLevel('WARN')
    sc = spark.sparkContext

    main(input, output)