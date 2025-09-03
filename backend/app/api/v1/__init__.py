from flask import Blueprint

bp = Blueprint('api_v1', __name__)

# Import all API modules to register routes
from . import auth, dashboard, devices, orders, materials, recipes, packages, commands, alarms, tasks, audit