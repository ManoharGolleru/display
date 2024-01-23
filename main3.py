from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Store active WebSocket connections
active_websockets = set()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_address = websocket.client.host + ":" + str(websocket.client.port)
    await websocket.accept()
    active_websockets.add(websocket)
    logging.info(f"WebSocket connection accepted from {client_address}")

    try:
        while True:
            data = await websocket.receive_text()
            logging.info(f"Received data from {client_address}: {data}")
            data_json = json.loads(data)
            state = data_json.get("state", {})
            text = state.get("$socket2", "")
            logging.info(f"Parsed JSON data from {client_address}: {data_json}, State: {state}, Text: {text}")

            disconnected_sockets = set()
            for ws in active_websockets:
                try:
                    await ws.send_text(json.dumps({"message": text}))
                    logging.info(f"Sent data to {ws.client.host}:{ws.client.port}")
                except RuntimeError as e:
                    logging.error(f"Runtime error sending to {ws.client.host}:{ws.client.port}: {e}")
                    disconnected_sockets.add(ws)
                except Exception as e:
                    logging.error(f"Exception sending to {ws.client.host}:{ws.client.port}: {e}")
            
            active_websockets.difference_update(disconnected_sockets)

    except WebSocketDisconnect as e:
        logging.warning(f"WebSocket disconnected with code: {e.code} from {client_address}")
    finally:
        active_websockets.remove(websocket)
        logging.info(f"WebSocket connection closed with {client_address}")
