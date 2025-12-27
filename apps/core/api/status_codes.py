from rest_framework import status


class ResponseStatusCodes:
    """
    HTTP status codes and custom status strings used for response schemas.
    Supports DRF status codes as well as special cases for paginated/unpaginated responses.
    """
    OK_ALL = f"{status.HTTP_200_OK}-all"
    OK_PAGINATED = f"{status.HTTP_200_OK}-paginated"
    OK = status.HTTP_200_OK
    CREATED = status.HTTP_201_CREATED
    NO_CONTENT = status.HTTP_204_NO_CONTENT
    BAD_REQUEST = status.HTTP_400_BAD_REQUEST
    UNAUTHORIZED = status.HTTP_401_UNAUTHORIZED
    FORBIDDEN = status.HTTP_403_FORBIDDEN
    NOT_FOUND = status.HTTP_404_NOT_FOUND
    CONFLICT = status.HTTP_409_CONFLICT
    SERVER_ERROR = status.HTTP_500_INTERNAL_SERVER_ERROR
    SERVICE_UNAVAILABLE = status.HTTP_503_SERVICE_UNAVAILABLE

