# Debug endpoint for testing Logística API integration
from fastapi import APIRouter, HTTPException
from app.crud import shipping_client

router = APIRouter(
    prefix="/api/debug",
    tags=["Debug"],
)


@router.post("/test-logistica-shipping")
def test_logistica_shipping():
    """
    Test endpoint to debug Logística API shipping creation.
    Calls crear_envio directly with test data.
    """
    print("[DEBUG] Testing Logística API shipping creation...")
    
    # Test data
    test_payload = {
        "order_id": 999,
        "user_id": 12345,
        "delivery_address": {
            "street": "Av. Test",
            "number": 123,
            "postal_code": "5000",
            "locality_name": "Test City"
        },
        "transport_type": "road",
        "products": [
            {"id": 3, "quantity": 2}
        ]
    }
    
    print(f"[DEBUG] Test payload: {test_payload}")
    
    try:
        response = shipping_client.crear_envio(
            order_id=test_payload["order_id"],
            user_id=test_payload["user_id"],
            delivery_address=test_payload["delivery_address"],
            transport_type=test_payload["transport_type"],
            products=test_payload["products"]
        )
        
        print(f"[DEBUG] Success! Response: {response}")
        return {
            "status": "success",
            "response": response
        }
        
    except HTTPException as e:
        print(f"[DEBUG] HTTPException: {e.status_code} - {e.detail}")
        return {
            "status": "error",
            "status_code": e.status_code,
            "detail": e.detail
        }
    except Exception as e:
        print(f"[DEBUG] Exception: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/test-logistica-token")
def test_logistica_token():
    """Test getting Logística API token"""
    try:
        from app.crud.shipping_client import _get_shipping_access_token
        token = _get_shipping_access_token("envios:write productos:read")
        return {
            "status": "success",
            "token_preview": token[:20] + "..." if len(token) > 20 else token
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
