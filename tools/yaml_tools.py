# tools/yaml_tools.py
import yaml
import json
from pathlib import Path
from typing import Any, Dict, Optional
from crewai.tools import BaseTool

def _coerce_to_dict_or_list(value: Any):
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        # try JSON first
        try:
            return json.loads(value)
        except Exception:
            # if it's plain text YAML, try to parse YAML → dict/list
            try:
                parsed = yaml.safe_load(value)
                return parsed
            except Exception:
                # fall back: return as raw text
                return value
    return value

class SaveYAMLTool(BaseTool):
    name: str = "Save YAML Report"
    description: str = (
        "Save analysis results to a YAML file. "
        "Args: file_path (default 'schema_analysis.yaml'). "
        "You can pass a single 'data' object (JSON/YAML string or dict), "
        "or separate parts like 'schema', 'row_counts', 'foreign_keys', 'fk_distributions' "
        "(each can be JSON/YAML string or dict)."
    )

    def _run(
        self,
        file_path: str = "schema_analysis.yaml",
        data: Optional[Any] = None,
        schema: Optional[Any] = None,
        row_counts: Optional[Any] = None,
        foreign_keys: Optional[Any] = None,
        fk_distributions: Optional[Any] = None,
        notes: Optional[str] = None
    ) -> str:
        payload: Dict[str, Any] = {}

        if data is not None:
            coerced = _coerce_to_dict_or_list(data)
            if isinstance(coerced, (dict, list)):
                payload = coerced
            else:
                # raw text fallback
                payload = {"raw": coerced}

        # Merge parts (parts override keys if provided)
        parts = {
            "schema": _coerce_to_dict_or_list(schema),
            "row_counts": _coerce_to_dict_or_list(row_counts),
            "foreign_keys": _coerce_to_dict_or_list(foreign_keys),
            "fk_distributions": _coerce_to_dict_or_list(fk_distributions),
        }
        for k, v in parts.items():
            if v is not None:
                payload[k] = v

        if notes:
            payload["notes"] = notes

        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(payload, f, sort_keys=False, allow_unicode=True)

        return f"📝 YAML saved to {path.resolve()}"
