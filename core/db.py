from pymongo import MongoClient
from config import trace_logger, passive_logger

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "jarvis_ai"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

trace_logger.info("MongoDB connected")
passive_logger.info(f"MongoDB connected | uri={MONGO_URI} | db={DB_NAME} | collection=passive_memory")

passive_memory_collection = db.passive_memory

# Ensure unique index to prevent duplicate facts (normalized key)
try:
	passive_memory_collection.create_index(
		[("fact_key", 1)],
		unique=True,
		sparse=True,
		name="uniq_fact_key"
	)
	passive_logger.info("MongoDB index ensured | name=uniq_fact_key | key=fact_key | unique=true | sparse=true")
except Exception as e:
	passive_logger.error(f"MongoDB index ensure failed | index=uniq_fact_key | error={e}")