from polygon import WebSocketClient
from polygon.websocket.models import WebSocketMessage, EquityTrade
from confluent_kafka import Producer
from typing import List
import os
from dotenv import load_dotenv 
import pandas as pd
import logging
import json
import sys

def get_subsciptions(file_path:str):
    df = pd.read_csv(file_path)
    data = df.values.tolist()
    subscriptions = [item for sublist in data for item in sublist]
    # print(subscriptions)
    return subscriptions

def read_ccloud_config(config_file):
    conf = {}
    with open(config_file) as fh:
        for line in fh:
            print(line)
            line = line.strip()
            if len(line) != 0 and line[0] != "#":
                parameter, value = line.strip().split('=', 1)
                conf[parameter] = value.strip()
    return conf

def delivery_callback(err, msg):
    if err:
        sys.stderr.write('%% Message failed delivery: %s\n' % err)
    else:
        sys.stderr.write('%% Message delivered to %s [%d] @ %d\n' %
                            (msg.topic(), msg.partition(), msg.offset()))


def handle_msg(msg: List[WebSocketMessage]):
    for m in msg:
        #Create an item dictionary with the relevant fields from the WebSocket message
        item = {
            "event_type": m.event_type,  # Event type (AM)
            "symbol": m.symbol,  # Ticker symbol (e.g., 'AAPL')
            "volume": m.volume,  # Volume
            "accumulated_volume": m.accumulated_volume,  # Accumulated volume
            "official_open_price": m.official_open_price,  # Official opening price
            "vwap": m.vwap,  # VWAP
            "open_price": m.open,  # Opening tick price
            "close_price": m.close,  # Closing tick price
            "high": m.high,  # Highest tick price
            "low": m.low,  # Lowest tick price
            "aggregate_vwap": m.aggregate_vwap,  # Aggregate VWAP
            "average_size": m.average_size,  # Average trade size
            "start_timestamp": m.start_timestamp,  # Start timestamp
            "end_timestamp": m.end_timestamp,  # End timestamp
            "otc": m.otc  # OTC flag
        }
        # Produce the message to Kafka topic "aggregates"
        producer.produce(
            topic=os.environ.get('CONFLUENT_TOPIC'),
            key=json.dumps({"symbol": m.symbol}).encode('utf-8'),  # Use symbol as key
            value=json.dumps(item).encode('utf-8'),  # Serialize item to JSON
            callback=delivery_callback
        )
        # Poll to handle delivery callback
        producer.poll(0)
    producer.flush()


if __name__=='__main__':
    # load environment variables
    load_dotenv()
    api_key=os.environ.get('api_key')
    data_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
    client_properties_path = os.path.join(data_dir,"client.properties")
    producer = Producer(read_ccloud_config(client_properties_path))

    logging.basicConfig(level=logging.DEBUG)
    
    subscription_csv_path = os.path.join(data_dir, "data", "subscriptions.csv")
    #print(subscription_csv_path)
    
    # Modify WebSocket initialization
    try:
        ws = WebSocketClient(
        api_key=api_key,
        feed='delayed.polygon.io',
        market='stocks',
        subscriptions=get_subsciptions(subscription_csv_path),
        verbose=True,  # Enable verbose logging
    )
    except Exception as e:
        print(f"WebSocket initialization error: {e}")
    
    # Run web socket client
    ws.run(handle_msg=handle_msg)

