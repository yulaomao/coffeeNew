#!/usr/bin/env python3
"""
Flask Web Application for Smart Coffee Machine
智能咖啡机Web应用
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_socketio import SocketIO, emit
import asyncio
import threading
import json
import base64
from pathlib import Path
from datetime import datetime
from loguru import logger
import sys

# Add device directory to path
device_dir = Path(__file__).parent.parent
sys.path.insert(0, str(device_dir))

from config import config
from agent.supervisor import agent_supervisor
from utils.sse import event_bus
from utils.i18n import i18n, t
from storage.models import Order

app = Flask(__name__)
app.secret_key = config.SECRET_KEY if hasattr(config, 'SECRET_KEY') else 'coffee-machine-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Global state
current_order = None
device_status = {"status": "idle", "temperature": 85, "cup_detected": False}

@app.route('/')
def index():
    """Main page - redirect to idle"""
    return redirect(url_for('idle'))

@app.route('/idle')
def idle():
    """Idle/Welcome page"""
    return render_template('idle.html', 
                         title=t("app_name", "智能咖啡机"),
                         device_id=config.DEVICE_ID)

@app.route('/menu')
def menu():
    """Menu page"""
    # Get available recipes from agent
    try:
        recipes = agent_supervisor.get_available_recipes()
    except AttributeError:
        # Fallback with mock data if method doesn't exist
        recipes = get_mock_recipes()
    
    return render_template('menu.html', 
                         recipes=recipes,
                         title=t("menu_title", "选择您的饮品"))

@app.route('/product/<product_id>')
def product_detail(product_id):
    """Product detail page"""
    # Get product details from agent
    try:
        product = agent_supervisor.get_product_details(product_id)
    except AttributeError:
        # Fallback with mock data
        product = get_mock_product(product_id)
    
    if not product:
        return redirect(url_for('menu'))
    
    return render_template('product_detail.html', 
                         product=product,
                         title=product.get('name', 'Product'))

@app.route('/confirm', methods=['POST'])
def confirm_order():
    """Confirm order page"""
    global current_order
    
    # Get form data
    product_id = request.form.get('product_id')
    options = request.form.to_dict()
    
    # Create order
    current_order = {
        'product_id': product_id,
        'options': options,
        'timestamp': datetime.now().isoformat(),
        'total_price': calculate_price(product_id, options)
    }
    
    return render_template('confirm.html', 
                         order=current_order,
                         title=t("confirm_title", "确认订单"))

@app.route('/payment')
def payment():
    """Payment page"""
    if not current_order:
        return redirect(url_for('menu'))
    
    return render_template('payment.html', 
                         order=current_order,
                         title=t("payment_title", "选择支付方式"))

@app.route('/qr/<payment_method>')
def qr_payment(payment_method):
    """QR code payment page"""
    if not current_order:
        return redirect(url_for('menu'))
    
    # Generate QR code
    qr_data = generate_payment_qr(payment_method, current_order)
    
    return render_template('qr.html', 
                         payment_method=payment_method,
                         qr_data=qr_data,
                         order=current_order,
                         title=t("qr_title", "扫码支付"))

@app.route('/brewing')
def brewing():
    """Brewing/Making page"""
    if not current_order:
        return redirect(url_for('menu'))
    
    return render_template('brewing.html', 
                         order=current_order,
                         title=t("brewing_title", "正在制作"))

@app.route('/done')
def done():
    """Order complete page"""
    return render_template('done.html', 
                         title=t("done_title", "制作完成"))

@app.route('/maintenance')
def maintenance():
    """Maintenance page"""
    # Check maintenance password
    if not session.get('maintenance_auth'):
        return render_template('maintenance_login.html')
    
    # Get system status
    try:
        status = agent_supervisor.get_system_status()
    except AttributeError:
        # Mock system status
        status = get_mock_system_status()
    
    return render_template('maintenance.html', 
                         status=status,
                         title=t("maintenance_title", "维护管理"))

@app.route('/api/status')
def api_status():
    """API endpoint for device status"""
    return jsonify(device_status)

@app.route('/api/start_order', methods=['POST'])
def api_start_order():
    """API endpoint to start new order"""
    global current_order
    current_order = None
    return jsonify({"success": True, "redirect": "/menu"})

@app.route('/api/payment/check/<payment_id>')
def api_check_payment(payment_id):
    """Check payment status"""
    # Simulate payment check (in real app, check with payment provider)
    # For demo, auto-complete after 3 seconds
    return jsonify({"status": "completed", "redirect": "/brewing"})

@app.route('/api/brewing/status')
def api_brewing_status():
    """Get brewing progress"""
    # Get brewing status from hardware abstraction layer
    try:
        progress = agent_supervisor.get_brewing_progress()
    except AttributeError:
        # Mock brewing progress
        progress = {"progress": 75, "step": 3, "estimated_time": 30}
    return jsonify(progress)

@app.route('/api/maintenance/auth', methods=['POST'])
def api_maintenance_auth():
    """Maintenance authentication"""
    password = request.json.get('password')
    if password == config.MAINTENANCE_PASSWORD:
        session['maintenance_auth'] = True
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Invalid password"})

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('status_update', device_status)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('request_status')
def handle_status_request():
    """Handle status request"""
    emit('status_update', device_status)

def calculate_price(product_id, options):
    """Calculate order price based on product and options"""
    base_price = 15.0  # Default price
    
    # Add pricing logic based on options
    total_price = base_price
    
    # Add extra charges for premium options
    if options.get('milk') == 'oat':
        total_price += 2.0
    
    # Add size pricing
    size = options.get('size', 'medium')
    if size == 'large':
        total_price += 3.0
    elif size == 'small':
        total_price -= 2.0
        
    return total_price

def generate_payment_qr(payment_method, order):
    """Generate payment QR code data"""
    # In real implementation, integrate with payment providers
    qr_content = f"{payment_method}://pay?amount={order['total_price']}&order_id={order.get('id', 'test')}"
    
    import qrcode
    import io
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_content)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    img_data = base64.b64encode(img_io.getvalue()).decode()
    return f"data:image/png;base64,{img_data}"

async def start_agent():
    """Start the device agent in background"""
    try:
        await agent_supervisor.start()
        logger.info("Device agent started successfully")
    except Exception as e:
        logger.error(f"Failed to start device agent: {e}")

def run_agent():
    """Run agent in separate thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_agent())
    
    # Keep the agent running
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Agent thread interrupted")
    finally:
        loop.close()

def get_mock_recipes():
    """Get mock recipes for demonstration"""
    return [
        {
            "id": "espresso",
            "name": "浓缩咖啡",
            "description": "经典意式浓缩，香浓醇厚",
            "price": 12.0,
            "image": None,
            "available": True,
            "sizes": [
                {"id": "single", "name": "单份", "extra_price": 0},
                {"id": "double", "name": "双份", "extra_price": 3.0}
            ],
            "allow_milk": False
        },
        {
            "id": "americano", 
            "name": "美式咖啡",
            "description": "浓缩咖啡配热水，口感清爽",
            "price": 15.0,
            "image": None,
            "available": True,
            "sizes": [
                {"id": "medium", "name": "中杯", "extra_price": 0},
                {"id": "large", "name": "大杯", "extra_price": 3.0}
            ],
            "allow_milk": True
        },
        {
            "id": "latte",
            "name": "拿铁咖啡", 
            "description": "浓缩咖啡配蒸汽牛奶，奶香浓郁",
            "price": 18.0,
            "image": None,
            "available": True,
            "sizes": [
                {"id": "medium", "name": "中杯", "extra_price": 0},
                {"id": "large", "name": "大杯", "extra_price": 3.0}
            ],
            "allow_milk": True
        },
        {
            "id": "cappuccino",
            "name": "卡布奇诺",
            "description": "浓缩咖啡、蒸汽牛奶和奶泡的完美结合",
            "price": 18.0,
            "image": None,
            "available": True,
            "sizes": [
                {"id": "medium", "name": "中杯", "extra_price": 0},
                {"id": "large", "name": "大杯", "extra_price": 3.0}
            ],
            "allow_milk": True
        },
        {
            "id": "mocha",
            "name": "摩卡咖啡",
            "description": "巧克力与咖啡的甜美邂逅",
            "price": 20.0,
            "image": None,
            "available": True,
            "sizes": [
                {"id": "medium", "name": "中杯", "extra_price": 0},
                {"id": "large", "name": "大杯", "extra_price": 3.0}
            ],
            "allow_milk": True
        },
        {
            "id": "macchiato",
            "name": "玛奇朵",
            "description": "浓缩咖啡配一勺奶泡",
            "price": 16.0,
            "image": None,
            "available": False,  # Out of stock example
            "sizes": [
                {"id": "single", "name": "单份", "extra_price": 0}
            ],
            "allow_milk": False
        }
    ]

def get_mock_product(product_id):
    """Get mock product details"""
    recipes = get_mock_recipes()
    return next((r for r in recipes if r["id"] == product_id), None)

def get_mock_system_status():
    """Get mock system status"""
    return {
        "device_status": "正常运行",
        "temperature": 85,
        "water_level": "充足",
        "cup_detected": False,
        "coffee_beans": "75%",
        "milk": "60%", 
        "syrup": "90%",
        "cups": "充足",
        "last_update": "2小时前",
        "network_connected": True,
        "uptime": "48小时"
    }

if __name__ == '__main__':
    # Start agent in background thread
    agent_thread = threading.Thread(target=run_agent, daemon=True)
    agent_thread.start()
    
    # Run Flask app
    logger.info(f"Starting Flask app on {config.WEB_HOST}:{config.WEB_PORT}")
    socketio.run(app, 
                host=getattr(config, 'WEB_HOST', '0.0.0.0'), 
                port=getattr(config, 'WEB_PORT', 5000),
                debug=getattr(config, 'DEBUG', False))