from flask import Blueprint, Response, request, stream_template
import json
import time
from datetime import datetime, timezone

sse_bp = Blueprint('sse', __name__, url_prefix='/sse')


class SSEManager:
    def __init__(self):
        self.clients = {}
    
    def add_client(self, channel, client_id):
        if channel not in self.clients:
            self.clients[channel] = set()
        self.clients[channel].add(client_id)
    
    def remove_client(self, channel, client_id):
        if channel in self.clients:
            self.clients[channel].discard(client_id)
            if not self.clients[channel]:
                del self.clients[channel]
    
    def broadcast(self, channel, event, data):
        # In a real implementation, you'd use Redis pub/sub or similar
        # For now, this is a simple in-memory implementation
        pass


sse_manager = SSEManager()


def event_stream(channel):
    """Generate SSE events for a specific channel"""
    def generate():
        client_id = f"{channel}_{int(time.time())}"
        sse_manager.add_client(channel, client_id)
        
        try:
            # Send initial connection event
            yield f"event: connected\n"
            yield f"data: {json.dumps({'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"
            
            # In a real implementation, you'd listen to Redis pub/sub or similar
            # For demo purposes, send periodic heartbeats
            counter = 0
            while True:
                time.sleep(5)  # Send heartbeat every 5 seconds
                counter += 1
                yield f"event: heartbeat\n"
                yield f"data: {json.dumps({'count': counter, 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"
                
                # In practice, you'd yield actual events here based on channel subscriptions
                
        except GeneratorExit:
            sse_manager.remove_client(channel, client_id)
    
    return generate()


@sse_bp.route('/dispatch/<batch_id>')
def dispatch_events(batch_id):
    """SSE endpoint for dispatch batch updates"""
    return Response(
        event_stream(f"dispatch_{batch_id}"),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*'
        }
    )


@sse_bp.route('/alarms')
def alarm_events():
    """SSE endpoint for alarm updates"""
    return Response(
        event_stream("alarms"),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*'
        }
    )


def send_sse_event(channel, event_type, data):
    """Send SSE event to a specific channel"""
    # In a real implementation, this would publish to Redis
    # and the event_stream would listen for these events
    sse_manager.broadcast(channel, event_type, data)