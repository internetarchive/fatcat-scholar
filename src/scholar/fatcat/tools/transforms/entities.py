from typing import Any, Dict, List

from fatcat_openapi_client import ApiClient
import toml


def entity_to_dict(entity: Any,
                   api_client: ApiClient|None = None,
) -> Dict[str, Any]:
    """
    Hack to take advantage of the code-generated serialization code.

    Initializing/destroying ApiClient objects is surprisingly expensive
    (because it involves a threadpool), so we allow passing an existing
    instance. If you already have a full-on API connection `api`, you can
    access the ApiClient object as `api.api_client`. This is such a speed-up
    that this argument may become mandatory.
    """
    if not api_client:
        api_client = ApiClient()
    return api_client.sanitize_for_serialization(entity)

def entity_to_toml(entity: Any,
                   api_client: ApiClient|None = None,
                   pop_fields: List[str]|None = None
) -> str:
    """
    pop_fields parameter can be used to strip out some fields from the resulting
    TOML. Eg, for fields which should not be edited, like the ident.
    """
    obj = entity_to_dict(entity, api_client=api_client)
    pop_fields = pop_fields or []
    for k in pop_fields:
        obj.pop(k, None)
    return toml.dumps(obj)

