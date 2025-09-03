#!/usr/bin/env python3
"""
Simple Flask test for Smart Coffee Machine
"""

import sys
from pathlib import Path

# Add device directory to path
device_dir = Path(__file__).parent
sys.path.insert(0, str(device_dir))

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_socketio import SocketIO, emit
import json
import base64
from datetime import datetime
from loguru import logger

app = Flask(__name__, 
           template_folder='web/templates',
           static_folder='web/static')
app.secret_key = 'coffee-machine-secret'
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
                         title="智能咖啡机",
                         device_id="D001")

@app.route('/menu')
def menu():
    """Menu page"""
    recipes = get_mock_recipes()
    return render_template('menu.html', 
                         recipes=recipes,
                         title="选择您的饮品")

@app.route('/product/<product_id>')
def product_detail(product_id):
    """Product detail page"""
    product = get_mock_product(product_id)
    if not product:
        return redirect(url_for('menu'))
    
    return render_template('product_detail.html', 
                         product=product,
                         title=product.get('name', 'Product'))

@app.route('/confirm', methods=['GET', 'POST'])
def confirm_order():
    """Confirm order page"""
    global current_order
    
    if request.method == 'POST':
        # Get form data
        product_id = request.form.get('product_id')
        options = request.form.to_dict()
        
        # Get product details
        product = get_mock_product(product_id)
        
        # Create order
        current_order = {
            'product_id': product_id,
            'product_name': product['name'] if product else '咖啡饮品',
            'options': options,
            'timestamp': datetime.now().isoformat(),
            'total_price': calculate_price(product_id, options)
        }
    
    if not current_order:
        return redirect(url_for('menu'))
    
    return render_template('confirm.html', 
                         order=current_order,
                         title="确认订单")

@app.route('/payment')
def payment():
    """Payment page"""
    if not current_order:
        return redirect(url_for('menu'))
    
    return render_template('payment.html', 
                         order=current_order,
                         title="选择支付方式")

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
                         title="扫码支付")

@app.route('/brewing')
def brewing():
    """Brewing/Making page"""
    if not current_order:
        return redirect(url_for('menu'))
    
    return render_template('brewing.html', 
                         order=current_order,
                         title="正在制作")

@app.route('/done')
def done():
    """Order complete page"""
    return render_template('done.html', 
                         title="制作完成")

@app.route('/maintenance')
def maintenance():
    """Maintenance page"""
    # Check maintenance password
    if not session.get('maintenance_auth'):
        return render_template('maintenance_login.html')
    
    # Get system status
    status = get_mock_system_status()
    return render_template('maintenance.html', 
                         status=status,
                         title="维护管理")

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
    return jsonify({"status": "completed", "redirect": "/brewing"})

@app.route('/api/brewing/status')
def api_brewing_status():
    """Get brewing progress"""
    progress = {"progress": 75, "step": 3, "estimated_time": 30}
    return jsonify(progress)

@app.route('/api/maintenance/auth', methods=['POST'])
def api_maintenance_auth():
    """Maintenance authentication"""
    password = request.json.get('password')
    if password == "0000":  # Default maintenance password
        session['maintenance_auth'] = True
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Invalid password"})

@app.route('/api/rating', methods=['POST'])
def api_rating():
    """Submit rating"""
    rating = request.json.get('rating')
    logger.info(f"Received rating: {rating} stars")
    return jsonify({"success": True})

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
    product = get_mock_product(product_id)
    base_price = product['price'] if product else 15.0
    
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
    logger.info("Starting Flask Coffee Machine Web Application...")
    logger.info("Web UI will be available at:")
    logger.info("  - Local: http://localhost:5000")
    logger.info("  - Network: http://0.0.0.0:5000")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)