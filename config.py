import logging

# ---------- Intent logger (existing) ----------
logging.basicConfig(
    filename="nova_intents.log",
    level=logging.INFO,
    format="%(asctime)s | %(message)s"
)

logger = logging.getLogger("NOVA_INTENT")


# ---------- Trace logger (NEW) ----------
trace_logger = logging.getLogger("NOVA_TRACE")
trace_logger.setLevel(logging.INFO)

trace_handler = logging.FileHandler("nova_trace.log")
trace_formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s"
)
trace_handler.setFormatter(trace_formatter)

trace_logger.addHandler(trace_handler)
trace_logger.propagate = False

# ---------- Passive memory logger (NEW) ----------
passive_logger = logging.getLogger("NOVA_PASSIVE")
passive_logger.setLevel(logging.INFO)

passive_handler = logging.FileHandler("passive_memory.log")
passive_formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s"
)
passive_handler.setFormatter(passive_formatter)

passive_logger.addHandler(passive_handler)
passive_logger.propagate = False
