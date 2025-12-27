from typing import Optional, List, Dict, Any, Type, Union
from drf_spectacular.utils import (
    extend_schema as drf_extend_schema,
    OpenApiParameter,
    OpenApiResponse,
    inline_serializer
)
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers
from rest_framework.relations import RelatedField


def custom_extend_schema(
    title: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    request_serializer: Optional[Type[serializers.Serializer]] = None,
    response_serializer: Optional[Type[serializers.Serializer]] = None,
    responses: Optional[Dict[int, Any]] = None,
    parameters: Optional[List[Union[OpenApiParameter, Type[serializers.Serializer]]]] = None,
    query_serializer: Optional[Type[serializers.Serializer]] = None,
    path_serializer: Optional[Type[serializers.Serializer]] = None,
    status_codes: Optional[List[Union[int, str]]] = None,
    summary: Optional[str] = None,
    deprecated: bool = False,
    operation_id: Optional[str] = None,
    resource_name: Optional[str] = None,
    **kwargs
):
    """
    Custom extend_schema decorator for DRF Spectacular.
    
    This decorator provides a simplified interface for extending API schemas
    with common parameters, responses, and metadata. Supports both serializer-based
    and manual parameter definitions, as well as status_codes for response mapping.
    
    Args:
        title: Operation title
        description: Detailed operation description
        tags: List of tags for grouping endpoints
        request_serializer: Serializer class for request body (POST/PUT/PATCH)
        response_serializer: Serializer class for successful response (200)
        responses: Dictionary mapping status codes to response schemas
            Example: {200: ResponseSerializer, 400: ErrorSerializer, 404: NotFoundSerializer}
        parameters: List of OpenApiParameter objects or Serializer classes for query/path parameters
        query_serializer: Serializer class for query parameters (alternative to parameters)
        path_serializer: Serializer class for path parameters (alternative to parameters)
        status_codes: List of status codes (int or string like "200-all", "200-paginated")
            Automatically maps to appropriate response serializers
        summary: Short summary of the operation
        deprecated: Whether this endpoint is deprecated
        operation_id: Unique operation identifier
        resource_name: Resource name for the operation
        **kwargs: Additional arguments passed to drf_spectacular's extend_schema
        
    Returns:
        Decorator function
        
    Example with status_codes:
        @custom_extend_schema(
            resource_name="ProductList",
            parameters=[ProductQuerySerializer, PaginationQuerySerializer],
            response_serializer=ProductListSerializer,
            status_codes=[
                ResponseStatusCodes.OK_PAGINATED,
                ResponseStatusCodes.BAD_REQUEST,
                ResponseStatusCodes.NOT_FOUND,
            ],
            summary="Get all products",
            description="Get all products with pagination and filtering",
        )
        def get(self, request):
            ...
    """
    from apps.core.api.status_code_mapper import map_status_codes_to_responses
    
    schema_kwargs = {}
    
    if resource_name:
        schema_kwargs['operation_id'] = resource_name
    if title:
        schema_kwargs['summary'] = title
    if summary:
        schema_kwargs['summary'] = summary
    if description:
        schema_kwargs['description'] = description
    if tags:
        schema_kwargs['tags'] = tags
    if deprecated:
        schema_kwargs['deprecated'] = True
    if operation_id:
        schema_kwargs['operation_id'] = operation_id
    
    if request_serializer:
        schema_kwargs['request'] = request_serializer
    
    if status_codes:
        from apps.core.api.status_code_mapper import map_status_codes_to_responses
        custom_mappings = kwargs.pop('custom_mappings', None)
        status_responses = map_status_codes_to_responses(
            status_codes=status_codes,
            response_serializer=response_serializer,
            custom_mappings=custom_mappings
        )
        if schema_kwargs.get('responses'):
            schema_kwargs['responses'].update(status_responses)
        else:
            schema_kwargs['responses'] = status_responses
    elif response_serializer:
        schema_kwargs['responses'] = {200: response_serializer}
    
    if responses:
        if schema_kwargs.get('responses'):
            schema_kwargs['responses'].update(responses)
        else:
            schema_kwargs['responses'] = responses
    
    params_list = []
    
    if query_serializer:
        query_params = _serializer_to_parameters(query_serializer, OpenApiParameter.QUERY)
        params_list.extend(query_params)
    
    if path_serializer:
        path_params = _serializer_to_parameters(path_serializer, OpenApiParameter.PATH)
        params_list.extend(path_params)
    
    if parameters:
        for param in parameters:
            if isinstance(param, type) and issubclass(param, serializers.Serializer):
                serializer_params = _serializer_to_parameters(param, OpenApiParameter.QUERY)
                params_list.extend(serializer_params)
            else:
                params_list.append(param)
    
    if params_list:
        schema_kwargs['parameters'] = params_list
    
    schema_kwargs.update(kwargs)
    
    return drf_extend_schema(**schema_kwargs)


def _serializer_to_parameters(
    serializer_class: Type[serializers.Serializer],
    location: str
) -> List[OpenApiParameter]:
    """
    Convert serializer fields to OpenApiParameter list.
    
    Args:
        serializer_class: Serializer class with fields
        location: Parameter location (QUERY or PATH)
        
    Returns:
        List of OpenApiParameter objects
    """
    params = []
    serializer = serializer_class()
    
    for field_name, field in serializer.fields.items():
        param_type = _get_openapi_type(field)
        description = getattr(field, 'help_text', None) or getattr(field, 'label', None)
        required = field.required if location == OpenApiParameter.PATH else field.required
        
        enum = None
        if not isinstance(field, RelatedField) and hasattr(field, 'choices'):
            try:
                choices = field.choices
                if choices:
                    enum = list(choices.keys()) if isinstance(choices, dict) else list(choices)
            except Exception:
                pass
        
        default = getattr(field, 'default', None)
        if default == serializers.empty:
            default = None
        
        param = OpenApiParameter(
            name=field_name,
            type=param_type,
            location=location,
            description=description,
            required=required,
            enum=enum,
            default=default
        )
        params.append(param)
    
    return params


def _get_openapi_type(field: serializers.Field) -> Any:
    """
    Map DRF serializer field to OpenAPI type.
    
    Args:
        field: DRF serializer field
        
    Returns:
        OpenAPI type
    """
    from rest_framework import fields
    
    field_type_mapping = {
        fields.CharField: OpenApiTypes.STR,
        fields.IntegerField: OpenApiTypes.INT,
        fields.FloatField: OpenApiTypes.FLOAT,
        fields.DecimalField: OpenApiTypes.DECIMAL,
        fields.BooleanField: OpenApiTypes.BOOL,
        fields.DateField: OpenApiTypes.DATE,
        fields.DateTimeField: OpenApiTypes.DATETIME,
        fields.EmailField: OpenApiTypes.EMAIL,
        fields.URLField: OpenApiTypes.URI,
        fields.UUIDField: OpenApiTypes.UUID,
        fields.ChoiceField: OpenApiTypes.STR,
    }
    
    field_type = type(field)
    
    for drf_field, openapi_type in field_type_mapping.items():
        if issubclass(field_type, drf_field):
            return openapi_type
    
    return OpenApiTypes.STR


def create_query_parameter(
    name: str,
    param_type: Any = OpenApiTypes.STR,
    description: Optional[str] = None,
    required: bool = False,
    enum: Optional[List] = None,
    default: Any = None
) -> OpenApiParameter:
    """
    Helper function to create query parameters.
    
    Args:
        name: Parameter name
        param_type: Parameter type (OpenApiTypes.STR, OpenApiTypes.INT, etc.)
        description: Parameter description
        required: Whether parameter is required
        enum: List of allowed values
        default: Default value
        
    Returns:
        OpenApiParameter: Configured parameter object
    """
    return OpenApiParameter(
        name=name,
        type=param_type,
        location=OpenApiParameter.QUERY,
        description=description,
        required=required,
        enum=enum,
        default=default
    )


def create_path_parameter(
    name: str,
    param_type: Any = OpenApiTypes.INT,
    description: Optional[str] = None
) -> OpenApiParameter:
    """
    Helper function to create path parameters.
    
    Args:
        name: Parameter name
        param_type: Parameter type (OpenApiTypes.INT, OpenApiTypes.STR, etc.)
        description: Parameter description
        
    Returns:
        OpenApiParameter: Configured parameter object
    """
    return OpenApiParameter(
        name=name,
        type=param_type,
        location=OpenApiParameter.PATH,
        description=description,
        required=True
    )


def create_error_response(
    status_code: int,
    description: str,
    serializer: Optional[Type[serializers.Serializer]] = None
) -> Dict[int, Any]:
    """
    Helper function to create error response schemas.
    
    Args:
        status_code: HTTP status code
        description: Error description
        serializer: Optional serializer for error response
        
    Returns:
        Dictionary with status code and response schema
    """
    if serializer:
        return {status_code: OpenApiResponse(response=serializer, description=description)}
    return {status_code: OpenApiResponse(description=description)}


def create_list_response(
    serializer: Type[serializers.Serializer],
    description: str = "List of items"
) -> Dict[int, Any]:
    """
    Helper function to create list response schema.
    
    Args:
        serializer: Serializer class for list items
        description: Response description
        
    Returns:
        Dictionary with 200 status code and list response schema
    """
    return {
        200: serializer(many=True),
        'description': description
    }

