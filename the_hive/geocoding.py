import requests  # type: ignore
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def geocode_address(request):
    """
    Convert address to coordinates using Nominatim (OpenStreetMap) geocoding service
    """
    address = request.data.get('address', '').strip()
    
    if not address:
        return Response(
            {"error": "Address is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': address,
            'format': 'json',
            'addressdetails': 1,
            'limit': 1,
            'extratags': 1
        }
        
        headers = {
            'User-Agent': 'TheHive-Community-Platform/1.0'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data:
            return Response(
                {"error": "Address not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        result = data[0]
        
        return Response({
            "address": result.get('display_name', address),
            "latitude": float(result['lat']),
            "longitude": float(result['lon']),
            "formatted_address": result.get('display_name', address)
        })
        
    except requests.exceptions.Timeout:
        return Response(
            {"error": "Geocoding service timeout"}, 
            status=status.HTTP_408_REQUEST_TIMEOUT
        )
    except requests.exceptions.RequestException as e:
        return Response(
            {"error": f"Geocoding service error: {str(e)}"}, 
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except Exception as e:
        return Response(
            {"error": f"Unexpected error: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )