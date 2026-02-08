from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import subprocess
import paho.mqtt.client as mqtt
import json
import asyncio
import logging
from typing import Set

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/hardware",
    tags=["Hardware"],
)

# Store active WebSocket connections
active_connections: Set[WebSocket] = set()

@router.post("/restart/")
def restart_application():
    """
    Restart the hardware application.
    """
    # Run 'sudo systemctl restart bindicator-hardware.service'
    subprocess.call(['sudo', 'systemctl', 'restart', 'bindicator-hardware.service'])


@router.websocket("/subscribe-to-gpio")
async def subscribe_to_gpio(websocket: WebSocket):
    """
    WebSocket endpoint that subscribes to MQTT GPIO events and streams them to the client.
    """
    await websocket.accept()
    active_connections.add(websocket)

    mqtt_connected = False
    mqtt_client = None

    # Queue to receive MQTT messages in async context
    message_queue = asyncio.Queue()

    # Get the event loop for this async context
    loop = asyncio.get_running_loop()

    def on_connect(client, userdata, flags, reason_code, properties):
        nonlocal mqtt_connected
        if reason_code == 0:
            mqtt_connected = True
            client.subscribe("bindicator/events/gpio")
            logger.info("WebSocket client connected to MQTT and subscribed to bindicator/events/gpio")
        else:
            logger.error(f"MQTT connection failed with code {reason_code}")
            mqtt_connected = False

    def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
        nonlocal mqtt_connected
        mqtt_connected = False
        logger.info("MQTT client disconnected")

    def on_message(client, userdata, msg):
        try:
            # Parse the MQTT message
            payload = json.loads(msg.payload.decode())
            logger.debug(f"Received MQTT message: {payload}")
            # Put it in the async queue using the correct event loop
            asyncio.run_coroutine_threadsafe(message_queue.put(payload), loop)
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    try:
        # Set up MQTT client
        mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        mqtt_client.on_connect = on_connect
        mqtt_client.on_disconnect = on_disconnect
        mqtt_client.on_message = on_message

        # Try to connect to MQTT broker
        try:
            mqtt_client.connect("localhost", 1883, keepalive=60)
            mqtt_client.loop_start()

            # Wait briefly for connection
            await asyncio.sleep(1)

            if not mqtt_connected:
                # Send offline status
                await websocket.send_json({
                    "status": "offline",
                    "message": "MQTT broker is not available"
                })
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            await websocket.send_json({
                "status": "offline",
                "message": f"Failed to connect to MQTT broker: {str(e)}"
            })

        # Send initial connection status
        if mqtt_connected:
            await websocket.send_json({
                "status": "connected",
                "message": "Connected to GPIO event stream"
            })

        # Main loop: forward MQTT messages to WebSocket
        while True:
            try:
                # Check for messages with timeout
                message = await asyncio.wait_for(message_queue.get(), timeout=30.0)
                await websocket.send_json(message)
            except asyncio.TimeoutError:
                # Send keepalive ping
                try:
                    await websocket.send_json({"type": "ping"})
                except:
                    break
            except Exception as e:
                logger.error(f"Error in WebSocket message loop: {e}")
                break

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Cleanup
        if mqtt_client:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()

        active_connections.discard(websocket)
        logger.info("WebSocket connection closed and cleaned up")


@router.websocket("/control")
async def control_hardware(websocket: WebSocket):
    """
    WebSocket endpoint for remote hardware control.
    Accepts commands from frontend and publishes them to MQTT.
    """
    await websocket.accept()
    active_connections.add(websocket)

    mqtt_connected = False
    mqtt_client = None

    # Queue to receive MQTT messages in async context
    message_queue = asyncio.Queue()

    # Get the event loop for this async context
    loop = asyncio.get_running_loop()

    def on_connect(client, userdata, flags, reason_code, properties):
        nonlocal mqtt_connected
        if reason_code == 0:
            mqtt_connected = True
            # Subscribe to both command responses and status updates
            client.subscribe("bindicator/remote_control/status")
            logger.info("Hardware control: Connected to MQTT broker and subscribed to status")
        else:
            logger.error(f"Hardware control: MQTT connection failed with code {reason_code}")
            mqtt_connected = False

    def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
        nonlocal mqtt_connected
        mqtt_connected = False
        logger.info("Hardware control: MQTT client disconnected")

    def on_message(client, userdata, msg):
        """Handle status messages from hardware."""
        try:
            # Check if this is a status message
            if msg.topic == "bindicator/remote_control/status":
                asyncio.run_coroutine_threadsafe(message_queue.put(msg), loop)
        except Exception as e:
            logger.error(f"Hardware control: Error processing MQTT message: {e}")

    try:
        # Set up MQTT client
        mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        mqtt_client.on_connect = on_connect
        mqtt_client.on_disconnect = on_disconnect
        mqtt_client.on_message = on_message

        # Try to connect to MQTT broker
        try:
            mqtt_client.connect("localhost", 1883, keepalive=60)
            mqtt_client.loop_start()

            # Wait briefly for connection
            await asyncio.sleep(1)

            if not mqtt_connected:
                await websocket.send_json({
                    "status": "error",
                    "message": "MQTT broker is not available"
                })
                return
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            await websocket.send_json({
                "status": "error",
                "message": f"Failed to connect to MQTT broker: {str(e)}"
            })
            return

        # Send success status
        await websocket.send_json({
            "status": "connected",
            "message": "Connected to hardware control"
        })

        # Check for retained status message
        await asyncio.sleep(0.5)
        try:
            msg = message_queue.get_nowait()
            if msg.payload:
                payload = json.loads(msg.payload.decode())
                await websocket.send_json({
                    "status": "hardware_ready",
                    "message": "Hardware is ready for remote control"
                })
            else:
                await websocket.send_json({
                    "status": "hardware_not_ready",
                    "message": "Please navigate to Settings > Remote Control on the hardware device"
                })
        except asyncio.QueueEmpty:
            await websocket.send_json({
                "status": "hardware_not_ready",
                "message": "Please navigate to Settings > Remote Control on the hardware device"
            })

        # Main loop: receive commands from WebSocket and publish to MQTT
        while True:
            try:
                # Check for status messages with a short timeout
                try:
                    msg = await asyncio.wait_for(message_queue.get(), timeout=0.1)
                    if msg.payload:
                        payload = json.loads(msg.payload.decode())
                        await websocket.send_json({
                            "status": "hardware_ready",
                            "message": "Hardware is ready for remote control"
                        })
                    else:
                        # Empty payload means hardware left remote control mode
                        await websocket.send_json({
                            "status": "hardware_not_ready",
                            "message": "Hardware left remote control mode"
                        })
                except asyncio.TimeoutError:
                    pass  # No status updates, continue

                # Wait for command from client with timeout
                try:
                    data = await asyncio.wait_for(websocket.receive_json(), timeout=0.1)
                except asyncio.TimeoutError:
                    continue  # No command, loop back to check status

                command_type = data.get('type')
                logger.debug(f"Hardware control: Received command {command_type}: {data}")

                # Validate and publish command to MQTT
                if command_type in ['lcd_display', 'light_control', 'disconnect']:
                    result = mqtt_client.publish(
                        "bindicator/commands",
                        json.dumps(data),
                        qos=0
                    )

                    if result.rc == mqtt.MQTT_ERR_SUCCESS:
                        await websocket.send_json({
                            "status": "success",
                            "message": f"Command {command_type} sent"
                        })
                        logger.debug(f"Hardware control: Published command {command_type}")

                        # If disconnect command, close the connection
                        if command_type == 'disconnect':
                            break
                    else:
                        await websocket.send_json({
                            "status": "error",
                            "message": "Failed to publish command"
                        })
                else:
                    await websocket.send_json({
                        "status": "error",
                        "message": f"Unknown command type: {command_type}"
                    })

            except WebSocketDisconnect:
                logger.info("Hardware control: WebSocket client disconnected")
                break
            except Exception as e:
                logger.error(f"Hardware control: Error in WebSocket loop: {e}")
                break

    except Exception as e:
        logger.error(f"Hardware control: WebSocket error: {e}")
    finally:
        # Cleanup
        if mqtt_client:
            # Send disconnect command if connection was established
            if mqtt_connected:
                try:
                    mqtt_client.publish(
                        "bindicator/commands",
                        json.dumps({"type": "disconnect"}),
                        qos=0
                    )
                except:
                    pass

            mqtt_client.loop_stop()
            mqtt_client.disconnect()

        active_connections.discard(websocket)
        logger.info("Hardware control: Connection closed and cleaned up")

