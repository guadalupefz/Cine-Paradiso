from flask import Blueprint, request, jsonify
from src.validators.auth_validator import validar_datos_registro
from src.services.auth_service import registrar_usuario

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/auth/registro', methods=['POST'])
def registro():
    try:
        data = request.get_json(silent=True)

        if data is None:
            return jsonify({
                'errors': [{
                    'code': 'JSON_INVALIDO',
                    'message': 'El cuerpo de la petición debe ser un JSON válido.',
                    'level': 'error'
                }]
            }), 400

        errores_val = validar_datos_registro(data)
        if errores_val:
            return jsonify({'errors': errores_val}), 400
    
        usuario, errores_srv = registrar_usuario(
            nombre=data.get('nombre', '').strip(),
            apellido=data.get('apellido', '').strip(),
            email=data.get('email', '').strip().lower(),
            password=data.get('password', '')
        )

        if errores_srv:
            return jsonify({'errors': errores_srv}), 409
    
        return jsonify({
            'message': 'Usuario registrado exitosamente.',
            'usuario': usuario
        }), 201

    except Exception as e:
        return (
            jsonify({
                'errors': [{
                    'code': 'ERROR_SERVIDOR',
                    'message': 'Ocurrió un error interno en el servidor.',
                    'level': 'error',
                    'description': str(e),
                }] 
            }), 
            500,
        )
