import importlib
import sys
import types

app_module = types.ModuleType("app")
app_module.__path__ = []
sys.modules["app"] = app_module

for name in ["core", "models", "routers", "schemas", "services", "repositories"]:
    module = importlib.import_module(name)
    setattr(app_module, name, module)
    sys.modules[f"app.{name}"] = module

for module_name in [
    "core.config",
    "core.security",
    "core.exceptions",
    "core.rate_limit",
    "services.auth_service",
    "services.user_service",
    "services.collection_point",
    "services.sms_service",
    "routers.auth",
    "routers.users",
    "routers.collection_point",
    "main",
]:
    module = importlib.import_module(module_name)
    sys.modules[f"app.{module_name}"] = module
    parent_name, _, leaf = module_name.rpartition(".")
    if parent_name:
        parent = sys.modules.get(parent_name)
        if parent is not None:
            setattr(parent, leaf, module)
            setattr(app_module, leaf, module)
